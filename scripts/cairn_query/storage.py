"""kuzudb wrapper, snapshot LRU cache, and source-mtime change detection.

Exposes:
- KuzuStorage: initialize / upsert / lookup / search / path_bindings / cypher
- SnapshotLRU: in-process LRU(8) keyed by git SHA
- sources_changed_since: mtime fingerprint comparison
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

import kuzu

from .models import (
    Decision,
    Feature,
    Invariant,
    Lesson,
    OpRule,
    PathAnchor,
    Slice,
    SpecSection,
)
from .schema import bootstrap_schema

# entity_type label → kuzu node-table name + pydantic model class
_ENTITY_TYPE_TO_TABLE: dict[str, tuple[str, type]] = {
    "invariant": ("Invariant", Invariant),
    "decision": ("Decision", Decision),
    "lesson": ("Lesson", Lesson),
    "spec_section": ("SpecSection", SpecSection),
    "op_rule": ("OpRule", OpRule),
    "feature": ("Feature", Feature),
    "slice": ("Slice", Slice),
}


class KuzuStorage:
    """Thin wrapper around kuzu.Database providing typed upsert/lookup/search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db = bootstrap_schema(db_path)
        self.conn = kuzu.Connection(self.db)

    def upsert_node(self, entity: Any) -> None:
        table_name, _ = _ENTITY_TYPE_TO_TABLE[entity.entity_type]
        params = self._entity_to_params(entity)
        # Exclude primary key from SET clauses — kuzu forbids setting pk in MERGE SET
        non_pk = {k: v for k, v in params.items() if k != "id"}
        set_clauses = ", ".join(f"n.{k} = $p_{k}" for k in non_pk)
        flat_params = {f"p_{k}": v for k, v in non_pk.items()}
        flat_params["_id"] = entity.id
        if set_clauses:
            self.conn.execute(
                f"MERGE (n:{table_name} {{id: $_id}}) ON MATCH SET {set_clauses} ON CREATE SET {set_clauses}",
                flat_params,
            )
        else:
            self.conn.execute(
                f"MERGE (n:{table_name} {{id: $_id}})",
                flat_params,
            )

    def upsert_edge(
        self,
        predicate: str,
        *,
        from_path: str | None = None,
        from_node_type: str | None = None,
        from_id: str | None = None,
        to_node_type: str,
        to_id: str,
    ) -> None:
        """Insert one typed edge."""
        if from_path is not None:
            self.conn.execute(
                "MERGE (p:Path {value: $v})",
                {"v": from_path},
            )
            self.conn.execute(
                f"MATCH (p:Path {{value: $from_path}}), (n:{to_node_type} {{id: $to_id}}) "
                f"MERGE (p)-[:{predicate}]->(n)",
                {"from_path": from_path, "to_id": to_id},
            )
        else:
            assert from_node_type is not None and from_id is not None
            self.conn.execute(
                f"MATCH (a:{from_node_type} {{id: $from_id}}), (b:{to_node_type} {{id: $to_id}}) "
                f"MERGE (a)-[:{predicate}]->(b)",
                {"from_id": from_id, "to_id": to_id},
            )

    def lookup(self, entity_type: str, id: str) -> Any:
        table_name, model_cls = _ENTITY_TYPE_TO_TABLE[entity_type]
        result = self.conn.execute(
            f"MATCH (n:{table_name} {{id: $id}}) RETURN n",
            {"id": id},
        )
        if not result.has_next():
            raise KeyError(f"{entity_type}:{id} not found")
        row = result.get_next()
        return self._row_to_entity(entity_type, row[0])

    def search(self, entity_type: str, filters: dict | None = None) -> list[Any]:
        table_name, _ = _ENTITY_TYPE_TO_TABLE[entity_type]
        where = ""
        params: dict = {}
        if filters:
            clauses = []
            for k, v in filters.items():
                clauses.append(f"n.{k} = ${k}")
                params[k] = v
            where = "WHERE " + " AND ".join(clauses)
        result = self.conn.execute(
            f"MATCH (n:{table_name}) {where} RETURN n",
            params,
        )
        out: list[Any] = []
        while result.has_next():
            row = result.get_next()
            out.append(self._row_to_entity(entity_type, row[0]))
        return out

    def path_bindings(self, path: str) -> list[Any]:
        results: list[Any] = []
        for entity_type, (table_name, _) in _ENTITY_TYPE_TO_TABLE.items():
            res = self.conn.execute(
                f"MATCH (p:Path {{value: $path}})-[:BINDS]->(n:{table_name}) RETURN n",
                {"path": path},
            )
            while res.has_next():
                row = res.get_next()
                results.append(self._row_to_entity(entity_type, row[0]))
        return results

    def cypher(self, query: str, params: dict | None = None) -> list[dict]:
        result = self.conn.execute(query, params or {})
        column_names = result.get_column_names()
        rows: list[dict] = []
        while result.has_next():
            row_vals = result.get_next()
            rows.append(dict(zip(column_names, row_vals)))
        return rows

    def count(self, table_name: str) -> int:
        result = self.conn.execute(f"MATCH (n:{table_name}) RETURN COUNT(n)")
        row = result.get_next()
        return row[0]

    def _entity_to_params(self, entity: Any) -> dict:
        """Flatten pydantic model to kuzu-compatible param dict."""
        d = entity.model_dump(mode="python")
        flat: dict[str, Any] = {}
        for k, v in d.items():
            if k == "entity_type":
                continue
            if isinstance(v, dict) and "path" in v:
                if k == "target":
                    flat["target_path"] = v["path"]
                    flat["target_line"] = v.get("line")
                elif k == "architecture_anchor":
                    flat["anchor_path"] = v["path"]
                    flat["anchor_line"] = v.get("line")
                elif k == "body_anchor":
                    flat["body_path"] = v["path"]
                    flat["body_line"] = v.get("line")
                # skip other PathAnchor-shaped dicts
            elif isinstance(v, list):
                continue  # lists go to edge tables, not node properties
            elif isinstance(v, date):
                flat[k] = v
            else:
                flat[k] = v
        return flat

    def _row_to_entity(self, entity_type: str, node_dict: dict) -> Any:
        """Inflate kuzu node row back into pydantic model."""
        _, model_cls = _ENTITY_TYPE_TO_TABLE[entity_type]
        kwargs: dict[str, Any] = dict(node_dict)
        kwargs["entity_type"] = entity_type
        if "target_path" in kwargs:
            kwargs["target"] = PathAnchor(
                path=kwargs.pop("target_path"),
                line=kwargs.pop("target_line", None),
            )
        if "anchor_path" in kwargs:
            kwargs["architecture_anchor"] = PathAnchor(
                path=kwargs.pop("anchor_path"),
                line=kwargs.pop("anchor_line", None),
            )
        if "body_path" in kwargs:
            kwargs["body_anchor"] = PathAnchor(
                path=kwargs.pop("body_path"),
                line=kwargs.pop("body_line", None),
            )
        # Lists come from edge queries — populate empty for direct lookups
        for f in [
            "invariants_touched",
            "supersedes",
            "instances",
            "anti_patterns",
            "adrs_referenced",
            "adrs_created",
            "envelope_paths",
            "envelope_out_of_scope",
            "slice_ids",
            "decision_points",
        ]:
            kwargs.setdefault(f, [])
        return model_cls.model_validate(kwargs)


class SnapshotLRU:
    """In-process LRU keyed by git SHA → arbitrary value (typically a KuzuStorage).

    Capacity 8 covers 4 phases × 2 in-flight slices (per design doc §4 / D12).
    """

    def __init__(self, maxsize: int = 8):
        self.maxsize = maxsize
        self._data: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)


def sources_changed_since(manifest: dict[str, float], sources: list[Path]) -> bool:
    """Return True if any source's mtime differs from the manifest, or if any source is missing."""
    for src in sources:
        if not src.exists():
            return True
        recorded = manifest.get(str(src))
        if recorded is None or src.stat().st_mtime != recorded:
            return True
    return False

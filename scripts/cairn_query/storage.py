"""kuzudb wrapper, snapshot LRU cache, and source-mtime change detection.

Exposes:
- KuzuStorage: initialize / upsert / lookup / search / path_bindings / cypher
- SnapshotLRU: in-process LRU keyed by git SHA
- sources_changed_since: mtime fingerprint comparison
"""

from __future__ import annotations

from collections import OrderedDict
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

# entity_type label -> (kuzu table name, pydantic model class)
_ENTITY_MAP: dict[str, tuple[str, type]] = {
    "invariant": ("Invariant", Invariant),
    "decision": ("Decision", Decision),
    "lesson": ("Lesson", Lesson),
    "spec_section": ("SpecSection", SpecSection),
    "op_rule": ("OpRule", OpRule),
    "feature": ("Feature", Feature),
    "slice": ("Slice", Slice),
}


def _node_props(node_dict: dict) -> dict:
    """Strip kuzu internal fields (_id, _label) from a node dict."""
    return {k: v for k, v in node_dict.items() if not k.startswith("_")}


def _entity_to_flat(entity: Any) -> dict:
    """Flatten a pydantic entity to a kuzu-compatible param dict.

    PathAnchor fields are flattened to <prefix>_path / <prefix>_line.
    List fields are omitted (stored as edges, not node properties).
    """
    flat: dict[str, Any] = {}
    et = entity.entity_type  # e.g. "invariant"

    if et == "invariant":
        flat = {
            "id": entity.id,
            "statement": entity.statement,
            "target_path": entity.target.path,
            "target_line": entity.target.line,
            "grep": entity.grep,
            "anchor_path": entity.architecture_anchor.path,
            "anchor_line": entity.architecture_anchor.line,
        }
    elif et == "decision":
        flat = {
            "id": entity.id,
            "name": entity.name,
            "status": entity.status,
            "firmness": entity.firmness,
            "topic": entity.topic,
            "date": entity.date,
            "body_path": entity.body_anchor.path,
            "superseded_by": entity.superseded_by,
        }
    elif et == "lesson":
        flat = {
            "id": entity.id,
            "title": entity.title,
            "discovered": entity.discovered,
            "pattern": entity.pattern,
            "rule": entity.rule,
            "body_path": entity.body_anchor.path,
        }
    elif et == "spec_section":
        flat = {
            "id": entity.id,
            "title": entity.title,
            "body_path": entity.body_anchor.path,
        }
    elif et == "op_rule":
        flat = {
            "id": entity.id,
            "statement": entity.statement,
            "scope": entity.scope,
            "body_path": entity.body_anchor.path,
            "body_line": entity.body_anchor.line,
        }
    elif et == "feature":
        flat = {
            "id": entity.id,
            "name": entity.name,
            "intent": entity.intent,
            "shaped_from": entity.shaped_from,
        }
    elif et == "slice":
        flat = {
            "id": entity.id,
            "name": entity.name,
            "feature_id": entity.feature_id,
            "status": entity.status,
            "started": entity.started,
            "completed": entity.completed,
            "close_commit": entity.close_commit,
        }
    return flat


def _flat_to_entity(entity_type: str, props: dict) -> Any:
    """Reconstruct a pydantic entity from flat kuzu node properties."""
    _, model_cls = _ENTITY_MAP[entity_type]
    kwargs: dict[str, Any] = dict(props)
    kwargs["entity_type"] = entity_type

    if entity_type == "invariant":
        kwargs["target"] = PathAnchor(
            path=kwargs.pop("target_path", "") or "",
            line=kwargs.pop("target_line", None),
        )
        kwargs["architecture_anchor"] = PathAnchor(
            path=kwargs.pop("anchor_path", "") or "",
            line=kwargs.pop("anchor_line", None),
        )
        kwargs.setdefault("grep", "")

    elif entity_type == "decision":
        kwargs["body_anchor"] = PathAnchor(path=kwargs.pop("body_path", "") or "")
        # List fields not stored as node props
        for f in ("invariants_touched", "supersedes", "decision_points"):
            kwargs.setdefault(f, [])

    elif entity_type == "lesson":
        kwargs["body_anchor"] = PathAnchor(path=kwargs.pop("body_path", "") or "")
        for f in ("instances", "anti_patterns"):
            kwargs.setdefault(f, [])

    elif entity_type == "spec_section":
        kwargs["body_anchor"] = PathAnchor(path=kwargs.pop("body_path", "") or "")

    elif entity_type == "op_rule":
        line = kwargs.pop("body_line", None)
        kwargs["body_anchor"] = PathAnchor(
            path=kwargs.pop("body_path", "") or "",
            line=line,
        )

    elif entity_type == "feature":
        kwargs.setdefault("slice_ids", [])

    elif entity_type == "slice":
        for f in (
            "invariants_touched",
            "adrs_referenced",
            "adrs_created",
            "envelope_paths",
            "envelope_out_of_scope",
        ):
            kwargs.setdefault(f, [])

    return model_cls.model_validate(kwargs)


def _build_upsert(table_name: str, params: dict) -> str:
    """Build a MERGE ... ON CREATE SET ... ON MATCH SET ... query.

    The primary key is always 'id'; all other params go into SET clauses.
    """
    non_pk = [k for k in params if k != "id"]
    if not non_pk:
        return f"MERGE (n:{table_name} {{id: $id}})"
    set_parts = ", ".join(f"n.{k} = ${k}" for k in non_pk)
    return (
        f"MERGE (n:{table_name} {{id: $id}}) "
        f"ON CREATE SET {set_parts} "
        f"ON MATCH SET {set_parts}"
    )


class KuzuStorage:
    """Thin wrapper around kuzu.Database providing typed upsert/lookup/search."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db = bootstrap_schema(self.db_path)
        self.conn = kuzu.Connection(self.db)

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def upsert_node(self, entity: Any) -> None:
        """Upsert (insert or update) a pydantic entity into kuzu."""
        table_name, _ = _ENTITY_MAP[entity.entity_type]
        params = _entity_to_flat(entity)
        query = _build_upsert(table_name, params)
        self.conn.execute(query, params)

    def lookup(self, entity_type: str, id: str) -> Any:
        """Return a single entity by type+id; raises KeyError if missing."""
        table_name, _ = _ENTITY_MAP[entity_type]
        result = self.conn.execute(
            f"MATCH (n:{table_name} {{id: $id}}) RETURN n",
            {"id": id},
        )
        if not result.has_next():
            raise KeyError(f"{entity_type}:{id} not found")
        row = result.get_next()
        props = _node_props(row[0])
        return _flat_to_entity(entity_type, props)

    def search(self, entity_type: str, filters: dict | None = None) -> list[Any]:
        """Return all entities of a type, optionally filtered."""
        table_name, _ = _ENTITY_MAP[entity_type]
        where = ""
        params: dict = {}
        if filters:
            clauses = [f"n.{k} = ${k}" for k in filters]
            where = "WHERE " + " AND ".join(clauses)
            params = dict(filters)
        result = self.conn.execute(
            f"MATCH (n:{table_name}) {where} RETURN n",
            params,
        )
        out: list[Any] = []
        while result.has_next():
            row = result.get_next()
            props = _node_props(row[0])
            out.append(_flat_to_entity(entity_type, props))
        return out

    def count(self, table_name: str) -> int:
        """Count nodes in a table by table name (e.g. 'Invariant')."""
        result = self.conn.execute(f"MATCH (n:{table_name}) RETURN COUNT(n)")
        row = result.get_next()
        return row[0]

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

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
        """Insert one typed edge.

        BINDS-style (path → entity): supply from_path.
        Node-to-node: supply from_node_type + from_id.
        """
        if from_path is not None:
            # Ensure Path node exists
            self.conn.execute(
                "MERGE (p:Path {value: $v})",
                {"v": from_path},
            )
            self.conn.execute(
                f"MATCH (p:Path {{value: $fp}}), (n:{to_node_type} {{id: $tid}}) "
                f"MERGE (p)-[:{predicate}]->(n)",
                {"fp": from_path, "tid": to_id},
            )
        else:
            assert from_node_type is not None and from_id is not None
            self.conn.execute(
                f"MATCH (a:{from_node_type} {{id: $fid}}), (b:{to_node_type} {{id: $tid}}) "
                f"MERGE (a)-[:{predicate}]->(b)",
                {"fid": from_id, "tid": to_id},
            )

    # ------------------------------------------------------------------
    # Path binding query
    # ------------------------------------------------------------------

    def path_bindings(self, path: str) -> list[Any]:
        """Return all entities bound to the given path via BINDS edges."""
        results: list[Any] = []
        for entity_type, (table_name, _) in _ENTITY_MAP.items():
            res = self.conn.execute(
                f"MATCH (p:Path {{value: $path}})-[:BINDS]->(n:{table_name}) RETURN n",
                {"path": path},
            )
            while res.has_next():
                row = res.get_next()
                props = _node_props(row[0])
                results.append(_flat_to_entity(entity_type, props))
        return results

    # ------------------------------------------------------------------
    # Raw Cypher escape hatch
    # ------------------------------------------------------------------

    def cypher(self, query: str, params: dict | None = None) -> list[dict]:
        """Execute a raw Cypher query and return rows as list of dicts."""
        result = self.conn.execute(query, params or {})
        col_names = result.get_column_names()
        rows: list[dict] = []
        while result.has_next():
            row_vals = result.get_next()
            rows.append(dict(zip(col_names, row_vals)))
        return rows


# ---------------------------------------------------------------------------
# Snapshot LRU
# ---------------------------------------------------------------------------


class SnapshotLRU:
    """In-process LRU keyed by git SHA → arbitrary value (typically a KuzuStorage).

    Capacity 8 covers 4 phases × 2 in-flight slices (per design doc §4 / D12).
    """

    def __init__(self, maxsize: int = 8) -> None:
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


# ---------------------------------------------------------------------------
# Source mtime fingerprint
# ---------------------------------------------------------------------------


def sources_changed_since(manifest: dict[str, float], sources: list[Path]) -> bool:
    """Return True if any source's mtime differs from the manifest or is missing."""
    for src in sources:
        if not src.exists():
            return True
        recorded = manifest.get(str(src))
        if recorded is None or src.stat().st_mtime != recorded:
            return True
    return False

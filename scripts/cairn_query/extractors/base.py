"""Extractor protocol — every per-entity-type extractor implements this.

Returns (nodes, edges) tuple. Nodes are pydantic-validated entities; edges are
typed predicates emitted by the extractor at extraction time. The extraction
runner upserts both into the KuzuStorage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from cairn_query.models import Entity


@dataclass
class ExtractedNode:
    entity: Entity


@dataclass
class ExtractedEdge:
    predicate: str
    to_node_type: str
    to_id: str
    # Either from_path (BINDS-style) OR (from_node_type + from_id) (node-to-node)
    from_path: str | None = None
    from_node_type: str | None = None
    from_id: str | None = None


@runtime_checkable
class Extractor(Protocol):
    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]: ...

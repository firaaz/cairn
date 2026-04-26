"""Cairn knowledge substrate — typed query layer over the markdown corpus.

Public API: rebuild_from_sources, lookup, search, path_bindings, cypher.
See docs/plans/2026-04-25-knowledge-substrate-design.md.
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    Decision,
    Entity,
    EntityType,
    Feature,
    Invariant,
    Lesson,
    OpRule,
    Slice,
    SpecSection,
)
from .storage import KuzuStorage

DEFAULT_DB_PATH = Path(".claude/cairn_query/index.kz")


def rebuild_from_sources(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    snapshot_id: str | None = None,
) -> KuzuStorage:
    """Run all extractors and populate the kuzudb at db_path. Idempotent."""
    # Lazy imports so the package is usable before all extractors are implemented.
    from .extractors.decision import DecisionExtractor
    from .extractors.feature import FeatureExtractor
    from .extractors.invariant import InvariantExtractor
    from .extractors.lesson import LessonExtractor
    from .extractors.op_rule import OpRuleExtractor
    from .extractors.slice import SliceExtractor
    from .extractors.spec_section import SpecSectionExtractor

    storage = KuzuStorage(db_path=db_path)
    extractors = [
        InvariantExtractor(architecture_path=Path("docs/ARCHITECTURE.md")),
        DecisionExtractor(adr_dir=Path("docs/adr")),
        LessonExtractor(lessons_path=Path("docs/lessons.md")),
        SpecSectionExtractor(spec_path=Path("docs/spec-v1.md")),
        OpRuleExtractor(op_ref_path=Path("docs/operational-reference.md")),
        FeatureExtractor(features_dir=Path(".claude/features")),
        SliceExtractor(),
    ]
    for ex in extractors:
        nodes, edges = ex.extract(snapshot_id=snapshot_id)
        for n in nodes:
            storage.upsert_node(n.entity)
        for e in edges:
            storage.upsert_edge(
                e.predicate,
                from_path=e.from_path,
                from_node_type=e.from_node_type,
                from_id=e.from_id,
                to_node_type=e.to_node_type,
                to_id=e.to_id,
            )
    return storage


def lookup(storage: KuzuStorage, entity_type: str, id: str) -> Entity:
    """Look up a single entity by type and id. Raises KeyError if missing."""
    return storage.lookup(entity_type, id)


def search(
    storage: KuzuStorage,
    entity_type: str,
    filters: dict | None = None,
) -> list[Entity]:
    """Return all entities of entity_type matching optional filters."""
    return storage.search(entity_type, filters)


def path_bindings(storage: KuzuStorage, path: str) -> list[Entity]:
    """Return all entities bound to path via a BINDS edge."""
    return storage.path_bindings(path)


def cypher(
    storage: KuzuStorage,
    query: str,
    params: dict | None = None,
) -> list[dict]:
    """Execute a raw Cypher query. Returns list of row dicts."""
    return storage.cypher(query, params)

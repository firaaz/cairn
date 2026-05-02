"""Cairn knowledge substrate — typed query layer over the markdown corpus.

Public API: rebuild_from_sources, lookup, search, path_bindings, cypher.
See docs/plans/2026-04-25-knowledge-substrate-design.md.
"""

from __future__ import annotations

from pathlib import Path

from _root import package_root as _package_root
from _root import project_root as _project_root

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

DEFAULT_DB_PATH = _project_root() / ".claude" / "cairn_query" / "index.kz"

__all__ = [
    "rebuild_from_sources",
    "lookup",
    "search",
    "path_bindings",
    "cypher",
    "DEFAULT_DB_PATH",
    "KuzuStorage",
    "Decision",
    "Entity",
    "EntityType",
    "Feature",
    "Invariant",
    "Lesson",
    "OpRule",
    "Slice",
    "SpecSection",
]


def rebuild_from_sources(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    snapshot_id: str | None = None,
) -> KuzuStorage:
    """Run all extractors and populate the kuzudb at db_path. Idempotent.

    If db_path is corrupted (RuntimeError from kuzu on open), the file is
    removed and a fresh database is created — self-healing for stale/truncated
    index files.
    """
    # Lazy imports so the package is usable before all extractors are implemented.
    from .extractors.decision import DecisionExtractor
    from .extractors.feature import FeatureExtractor
    from .extractors.invariant import InvariantExtractor
    from .extractors.lesson import LessonExtractor
    from .extractors.op_rule import OpRuleExtractor
    from .extractors.slice import SliceExtractor
    from .extractors.spec_section import SpecSectionExtractor

    db_path = Path(db_path)
    try:
        storage = KuzuStorage(db_path=db_path)
    except RuntimeError:
        # Corrupted or truncated database — remove and start fresh.
        if db_path.exists():
            db_path.unlink()
        storage = KuzuStorage(db_path=db_path)

    # Corpus paths anchor at package_root() — these read cairn's own ADRs,
    # lessons, spec, and INV docs, which the MCP server serves to all consumers
    # regardless of which consumer launched it. Using project_root() here would
    # point at the consumer's docs/, which is the L-017 leak.
    # Feature paths anchor at project_root() — features are project-local
    # (each consumer has its own .claude/features/) and not part of the cairn
    # methodology corpus.
    _pkg = _package_root()
    extractors = [
        InvariantExtractor(architecture_path=_pkg / "docs" / "ARCHITECTURE.md"),
        DecisionExtractor(adr_dir=_pkg / "docs" / "adr"),
        LessonExtractor(lessons_path=_pkg / "docs" / "lessons.md"),
        SpecSectionExtractor(spec_path=_pkg / "docs" / "spec-v1.md"),
        OpRuleExtractor(op_ref_path=_pkg / "docs" / "operational-reference.md"),
        FeatureExtractor(features_dir=_project_root() / ".claude" / "features"),
        SliceExtractor(),
    ]
    for ex in extractors:
        nodes, edges = ex.extract(snapshot_id=snapshot_id)
        for n in nodes:
            storage.upsert_node(n.entity)
        for e in edges:
            storage.upsert_edge(
                e.predicate,
                from_path=_relativize_corpus_path(e.from_path, _pkg),
                from_node_type=e.from_node_type,
                from_id=e.from_id,
                to_node_type=e.to_node_type,
                to_id=e.to_id,
            )
    return storage


def _relativize_corpus_path(raw: str | None, pkg: Path) -> str | None:
    """Normalize a corpus-rooted absolute path back to its package-relative form.

    Extractors now receive package-anchored absolute paths and emit
    ``from_path=str(self.path)``. Stored binding identities must stay stable
    across machines — so reduce ``/abs/path/to/cairn/docs/ARCHITECTURE.md`` to
    ``docs/ARCHITECTURE.md``. Paths outside the cairn package (project-local
    feature yaml, slice yaml) pass through unchanged.
    """
    if raw is None:
        return None
    try:
        return str(Path(raw).relative_to(pkg))
    except ValueError:
        return raw


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

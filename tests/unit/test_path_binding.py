"""RED integration tests — public Python API over a live-corpus rebuild.

Validates the workhorse path-binding query against the three known paths
declared in slice-close criteria §4-§6:

- docs/ARCHITECTURE.md → ≥9 Invariants
- scripts/slice_orchestrator/lifecycle.py → INV-008
- docs/lessons.md → L-001 (and L-002)

Plus lookup, search, and the cypher escape hatch.
"""

from __future__ import annotations

import pytest

from cairn_query import (
    cypher,
    lookup,
    path_bindings,
    rebuild_from_sources,
    search,
)


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("idx") / "index.kz"
    return rebuild_from_sources(db_path=db_path, snapshot_id=None)


def test_path_bindings_for_lifecycle_py(index):
    """scripts/slice_orchestrator/lifecycle.py is bound by INV-008."""
    results = path_bindings(index, "scripts/slice_orchestrator/lifecycle.py")
    inv_ids = {r.id for r in results if r.entity_type == "invariant"}
    assert "INV-008" in inv_ids


def test_path_bindings_for_architecture_md(index):
    """docs/ARCHITECTURE.md is bound by every Invariant (≥9)."""
    results = path_bindings(index, "docs/ARCHITECTURE.md")
    inv_results = [r for r in results if r.entity_type == "invariant"]
    assert len(inv_results) >= 9


def test_path_bindings_for_lessons_md(index):
    """docs/lessons.md is bound by L-001 and L-002."""
    results = path_bindings(index, "docs/lessons.md")
    lesson_ids = {r.id for r in results if r.entity_type == "lesson"}
    assert "L-001" in lesson_ids
    assert "L-002" in lesson_ids


def test_lookup_invariant(index):
    inv = lookup(index, "invariant", "INV-008")
    assert inv.id == "INV-008"


def test_lookup_missing_raises(index):
    with pytest.raises(KeyError):
        lookup(index, "invariant", "INV-999")


def test_search_invariants_returns_all(index):
    results = search(index, "invariant")
    assert len(results) >= 9


def test_cypher_supersedes_chain(index):
    """Multi-hop query: identifier-scheme supersedes semantic-identity."""
    rows = cypher(
        index,
        "MATCH (d:Decision)<-[:SUPERSEDES]-(d2:Decision) RETURN d.id, d2.id",
    )
    pairs = {(r["d.id"], r["d2.id"]) for r in rows}
    assert ("semantic-identity", "identifier-scheme") in pairs

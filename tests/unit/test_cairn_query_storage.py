"""RED tests — KuzuStorage upsert / lookup / search / path_bindings / cypher.

Asserts: typed upsert is idempotent and updates-in-place; missing lookups
raise KeyError; search returns all nodes of a type; path_bindings returns
entities anchored to a Path; cypher is the raw escape hatch.
"""

from __future__ import annotations

import pytest

from cairn_query.models import Invariant, PathAnchor
from cairn_query.storage import KuzuStorage


@pytest.fixture
def storage(tmp_path):
    return KuzuStorage(db_path=tmp_path / "test.kz")


def test_storage_initializes_empty(storage):
    assert storage.count("Invariant") == 0
    assert storage.count("Decision") == 0


def test_upsert_invariant_round_trip(storage):
    inv = Invariant(
        id="INV-008",
        statement="close_slice contract",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep=r"def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    storage.upsert_node(inv)
    assert storage.count("Invariant") == 1
    fetched = storage.lookup("invariant", "INV-008")
    assert fetched.id == "INV-008"
    assert fetched.statement == "close_slice contract"


def test_upsert_idempotent(storage):
    inv = Invariant(
        id="INV-008",
        statement="x",
        target=PathAnchor(path="x"),
        grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    storage.upsert_node(inv)
    storage.upsert_node(inv)
    assert storage.count("Invariant") == 1


def test_upsert_updates_existing(storage):
    inv1 = Invariant(
        id="INV-008",
        statement="original",
        target=PathAnchor(path="x"),
        grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    inv2 = inv1.model_copy(update={"statement": "updated"})
    storage.upsert_node(inv1)
    storage.upsert_node(inv2)
    fetched = storage.lookup("invariant", "INV-008")
    assert fetched.statement == "updated"


def test_lookup_missing_raises(storage):
    with pytest.raises(KeyError):
        storage.lookup("invariant", "INV-999")


def test_search_returns_filtered_list(storage):
    for i, sid in enumerate(["INV-001", "INV-002", "INV-003"]):
        storage.upsert_node(
            Invariant(
                id=sid,
                statement=f"s{i}",
                target=PathAnchor(path="x"),
                grep="x",
                architecture_anchor=PathAnchor(path="x"),
            )
        )
    results = storage.search("invariant")
    assert len(results) == 3
    assert {r.id for r in results} == {"INV-001", "INV-002", "INV-003"}


def test_path_bindings_returns_anchored_entities(storage):
    inv = Invariant(
        id="INV-008",
        statement="x",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep="def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    storage.upsert_node(inv)
    storage.upsert_edge(
        "BINDS",
        from_path="docs/ARCHITECTURE.md",
        to_node_type="Invariant",
        to_id="INV-008",
    )
    results = storage.path_bindings("docs/ARCHITECTURE.md")
    assert len(results) == 1
    assert results[0].id == "INV-008"


def test_cypher_escape_hatch(storage):
    """cypher() returns raw dicts; advanced queries unburdened by typed return."""
    inv = Invariant(
        id="INV-008",
        statement="x",
        target=PathAnchor(path="x"),
        grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    storage.upsert_node(inv)
    rows = storage.cypher("MATCH (i:Invariant) RETURN i.id AS id")
    assert any(r["id"] == "INV-008" for r in rows)

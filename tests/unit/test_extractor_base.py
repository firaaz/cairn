"""RED tests — Extractor protocol + ExtractedNode/ExtractedEdge dataclasses."""

from __future__ import annotations

from cairn_query.extractors.base import (
    ExtractedEdge,
    ExtractedNode,
    Extractor,
)


def test_extractor_protocol_requires_extract_method():
    """A class missing extract() should fail isinstance(Extractor) check."""

    class NotAnExtractor:
        pass

    assert not isinstance(NotAnExtractor(), Extractor)


def test_extractor_protocol_satisfied_by_extract_method():
    class GoodExtractor:
        def extract(self, snapshot_id: str | None = None):
            return ([], [])

    assert isinstance(GoodExtractor(), Extractor)


def test_extracted_node_carries_pydantic_entity():
    """ExtractedNode wraps a pydantic Entity for upsert."""
    from cairn_query.models import Invariant, PathAnchor

    inv = Invariant(
        id="INV-001",
        statement="x",
        target=PathAnchor(path="x"),
        grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    node = ExtractedNode(entity=inv)
    assert node.entity.id == "INV-001"


def test_extracted_edge_holds_typed_predicate():
    e = ExtractedEdge(
        predicate="BINDS",
        from_path="docs/ARCHITECTURE.md",
        to_node_type="Invariant",
        to_id="INV-008",
    )
    assert e.predicate == "BINDS"
    assert e.from_path == "docs/ARCHITECTURE.md"
    assert e.to_node_type == "Invariant"
    assert e.to_id == "INV-008"
    assert e.from_node_type is None
    assert e.from_id is None

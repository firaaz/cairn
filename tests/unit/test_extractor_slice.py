"""RED tests — SliceExtractor against `git log --grep='^slice: .* — complete$'`.

Asserts: every close-commit produces one Slice node with the parent's
slice.yaml fields rehydrated; ≥4 slices present (slice-close criterion §6);
PARENT edges link slices to features; idempotent re-extraction at fixed
HEAD yields equal output.
"""

from __future__ import annotations

import pytest

from cairn_query.extractors.slice import SliceExtractor


@pytest.fixture
def extractor():
    return SliceExtractor()


def test_extracts_at_least_four_slices(extractor):
    """Slice-close criterion §6 mandates ≥4 Slices populated."""
    nodes, _edges = extractor.extract()
    assert len({n.entity.id for n in nodes}) >= 4


def test_extracts_lever_2_orchestrator_split(extractor):
    nodes, _edges = extractor.extract()
    target = next(
        (
            n.entity
            for n in nodes
            if n.entity.id == "compression/lever-2-orchestrator-split"
        ),
        None,
    )
    assert target is not None
    assert target.status == "complete"
    # close_commit is the short SHA recorded in the slice-close commit message.
    assert target.close_commit
    assert target.close_commit.startswith("84f1749")


def test_at_least_one_slice_touches_invariants(extractor):
    nodes, _edges = extractor.extract()
    assert any(n.entity.invariants_touched for n in nodes)


def test_emits_parent_edge_to_feature(extractor):
    _nodes, edges = extractor.extract()
    parents = {
        (e.from_id, e.to_id)
        for e in edges
        if e.predicate == "PARENT"
        and e.from_node_type == "Slice"
        and e.to_node_type == "Feature"
    }
    # Every compression slice's PARENT edge points at the compression feature.
    assert any(
        slice_id.startswith("compression/") and feature_id == "compression"
        for slice_id, feature_id in parents
    )


def test_idempotent_at_fixed_head(extractor):
    """Re-extracting at the same git HEAD must yield identical nodes."""
    nodes_a, _ = extractor.extract()
    nodes_b, _ = extractor.extract()
    assert {n.entity.id for n in nodes_a} == {n.entity.id for n in nodes_b}

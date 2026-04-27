"""RED tests — InvariantExtractor against docs/ARCHITECTURE.md.

Asserts the extractor surfaces ≥9 INV-NNN entries currently codified in
ARCHITECTURE.md (per the closed compression/lever-2 slice), wires INV-008
to scripts/slice_orchestrator/lifecycle.py, emits BINDS edges from the
architecture path, and degrades gracefully when the source file is absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.invariant import InvariantExtractor


@pytest.fixture
def extractor():
    return InvariantExtractor(architecture_path=Path("docs/ARCHITECTURE.md"))


def test_extracts_known_invariant_inv_008(extractor):
    """INV-008 (close_slice as sole producer) exists in current ARCHITECTURE.md."""
    nodes, _edges = extractor.extract()
    inv_008 = next((n.entity for n in nodes if n.entity.id == "INV-008"), None)
    assert inv_008 is not None
    assert "close_slice" in inv_008.grep or "close_slice" in inv_008.statement
    assert inv_008.target.path == "scripts/slice_orchestrator/lifecycle.py"


def test_extracts_all_nine_current_invariants(extractor):
    """At slice compression/lever-2-orchestrator-split close, 9 invariants exist."""
    nodes, _edges = extractor.extract()
    ids = {n.entity.id for n in nodes}
    expected = {f"INV-00{i}" for i in range(1, 10)}
    assert expected.issubset(ids)


def test_extractor_emits_binds_edge_per_invariant(extractor):
    nodes, edges = extractor.extract()
    binds = [
        e for e in edges if e.predicate == "BINDS" and e.to_node_type == "Invariant"
    ]
    paths = {e.from_path for e in binds}
    assert "docs/ARCHITECTURE.md" in paths
    # Every Invariant node should have at least one BINDS edge to it.
    bound_ids = {e.to_id for e in binds}
    assert {n.entity.id for n in nodes}.issubset(bound_ids)


def test_extractor_handles_missing_architecture_file(tmp_path):
    extractor = InvariantExtractor(architecture_path=tmp_path / "nope.md")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []

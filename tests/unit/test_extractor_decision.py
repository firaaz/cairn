"""RED tests — DecisionExtractor against docs/adr/*.md.

Asserts: every ADR file (excluding index.md) becomes one Decision node;
frontmatter fields (id, name, status, firmness, topic, date) populate;
SUPERSEDES edges encode supersession links recorded in frontmatter; BINDS
edges emit from each ADR's body path.

Concrete corpus probes:
- `parallelism-v1` is present and accepted.
- `identifier-scheme` SUPERSEDES `semantic-identity` (per cairn ADR corpus).
- The 16+ ADRs currently in docs/adr (minus index.md) are all extracted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.decision import DecisionExtractor


@pytest.fixture
def extractor():
    return DecisionExtractor(adr_dir=Path("docs/adr"))


def test_extracts_known_decision_parallelism_v1(extractor):
    nodes, _edges = extractor.extract()
    parallelism = next(
        (n.entity for n in nodes if n.entity.id == "parallelism-v1"), None
    )
    assert parallelism is not None
    assert parallelism.entity_type == "decision"
    # frontmatter-derived fields populated
    assert parallelism.name
    assert parallelism.status in {"accepted", "superseded", "deferred", "draft"}
    assert parallelism.firmness in {"firm", "provisional"}


def test_extracts_at_least_sixteen_decisions(extractor):
    """Slice-close criterion §6 mandates ≥16 Decisions populated."""
    nodes, _edges = extractor.extract()
    assert len({n.entity.id for n in nodes}) >= 16


def test_skips_index_md(extractor):
    nodes, _edges = extractor.extract()
    assert all(n.entity.id != "index" for n in nodes)


def test_supersedes_edge_for_identifier_scheme(extractor):
    """identifier-scheme supersedes semantic-identity per the cairn ADR corpus."""
    _nodes, edges = extractor.extract()
    superseded = {
        (e.from_id, e.to_id)
        for e in edges
        if e.predicate == "SUPERSEDES"
        and e.from_node_type == "Decision"
        and e.to_node_type == "Decision"
    }
    assert ("identifier-scheme", "semantic-identity") in superseded


def test_emits_binds_edges_from_adr_path(extractor):
    nodes, edges = extractor.extract()
    binds = {
        (e.from_path, e.to_id)
        for e in edges
        if e.predicate == "BINDS" and e.to_node_type == "Decision"
    }
    # parallelism-v1's BINDS edge must include its ADR file path.
    assert any(
        path.endswith("docs/adr/parallelism-v1.md") and to_id == "parallelism-v1"
        for path, to_id in binds
    )


def test_handles_missing_adr_dir(tmp_path):
    extractor = DecisionExtractor(adr_dir=tmp_path / "nope")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []

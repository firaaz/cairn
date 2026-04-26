"""RED tests — OpRuleExtractor against docs/operational-reference.md.

v1 minimum scope (per Task 11): the four Phase Skill Guide rows surface as
OpRule entities `phase-skill-guide/phase-{1,2,3,4}` with BINDS edges from
the operational-reference path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.op_rule import OpRuleExtractor


@pytest.fixture
def extractor():
    return OpRuleExtractor(op_ref_path=Path("docs/operational-reference.md"))


def test_extracts_four_phase_skill_guide_rows(extractor):
    nodes, _edges = extractor.extract()
    ids = {n.entity.id for n in nodes}
    expected = {f"phase-skill-guide/phase-{i}" for i in (1, 2, 3, 4)}
    assert expected.issubset(ids)


def test_phase_skill_guide_entries_have_statement(extractor):
    nodes, _edges = extractor.extract()
    for n in nodes:
        if n.entity.id.startswith("phase-skill-guide/"):
            assert n.entity.statement


def test_emits_binds_from_op_ref_path(extractor):
    _nodes, edges = extractor.extract()
    paths = {
        e.from_path
        for e in edges
        if e.predicate == "BINDS" and e.to_node_type == "OpRule"
    }
    assert any(p and p.endswith("docs/operational-reference.md") for p in paths)


def test_handles_missing_op_ref_file(tmp_path):
    extractor = OpRuleExtractor(op_ref_path=tmp_path / "nope.md")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []

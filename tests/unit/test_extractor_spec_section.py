"""RED tests — SpecSectionExtractor against docs/spec-v1.md.

Asserts each `## §N` / `### §N.M` heading produces a SpecSection node, the
id captures the section marker, and BINDS edges emit from the spec path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.spec_section import SpecSectionExtractor


@pytest.fixture
def extractor():
    return SpecSectionExtractor(spec_path=Path("docs/spec-v1.md"))


def test_extracts_at_least_one_section(extractor):
    nodes, _edges = extractor.extract()
    assert len(nodes) >= 1


def test_section_ids_use_section_sign(extractor):
    nodes, _edges = extractor.extract()
    assert all(n.entity.id.startswith("§") for n in nodes)


def test_each_section_has_title(extractor):
    nodes, _edges = extractor.extract()
    assert all(n.entity.title for n in nodes)


def test_emits_binds_from_spec_path(extractor):
    nodes, edges = extractor.extract()
    if not nodes:
        pytest.skip("no spec sections present in current corpus")
    paths = {
        e.from_path
        for e in edges
        if e.predicate == "BINDS" and e.to_node_type == "SpecSection"
    }
    assert any(p and p.endswith("docs/spec-v1.md") for p in paths)


def test_handles_missing_spec_file(tmp_path):
    extractor = SpecSectionExtractor(spec_path=tmp_path / "nope.md")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []

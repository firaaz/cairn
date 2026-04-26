"""RED tests — LessonExtractor against docs/lessons.md.

Asserts L-001 and L-002 surface, body fields populate (pattern, rule,
anti_patterns), instances list non-empty for L-001, and BINDS edges
emit from the lessons file path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.lesson import LessonExtractor


@pytest.fixture
def extractor():
    return LessonExtractor(lessons_path=Path("docs/lessons.md"))


def test_extracts_l_001_and_l_002(extractor):
    nodes, _edges = extractor.extract()
    ids = {n.entity.id for n in nodes}
    assert "L-001" in ids
    assert "L-002" in ids


def test_l_001_body_populated(extractor):
    nodes, _edges = extractor.extract()
    l_001 = next(n.entity for n in nodes if n.entity.id == "L-001")
    assert l_001.title
    assert l_001.pattern
    assert l_001.rule
    assert l_001.anti_patterns  # non-empty list


def test_l_001_instances_include_known_commit(extractor):
    nodes, _edges = extractor.extract()
    l_001 = next(n.entity for n in nodes if n.entity.id == "L-001")
    # f531087 is the canonical instance commit recorded in the lesson.
    assert any("f531087" in inst for inst in l_001.instances)


def test_emits_binds_edge_from_lessons_path(extractor):
    _nodes, edges = extractor.extract()
    binds = [
        e
        for e in edges
        if e.predicate == "BINDS"
        and e.to_node_type == "Lesson"
        and e.from_path
        and e.from_path.endswith("docs/lessons.md")
    ]
    assert binds  # non-empty


def test_handles_missing_lessons_file(tmp_path):
    extractor = LessonExtractor(lessons_path=tmp_path / "nope.md")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []

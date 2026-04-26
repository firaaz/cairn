"""RED tests — pydantic entity models for the cairn knowledge substrate.

Asserts: PathAnchor + EntityType enum + 7 typed entities round-trip via
pydantic v2's model_dump/model_validate, and pattern-validators reject
malformed ids (INV-NNN, hierarchical slice ids, L-NNN).

Module under test does not yet exist; test file fails at collection until
Phase 3 ships scripts/cairn_query/models.py.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from cairn_query.models import (
    Decision,
    EntityType,
    Feature,
    Invariant,
    Lesson,
    OpRule,
    PathAnchor,
    Slice,
    SpecSection,
)


def test_path_anchor_constructs():
    p = PathAnchor(path="docs/ARCHITECTURE.md", line=80)
    assert p.path == "docs/ARCHITECTURE.md"
    assert p.line == 80


def test_path_anchor_line_optional():
    p = PathAnchor(path="docs/spec-v1.md")
    assert p.line is None


def test_entity_type_enum_values():
    assert EntityType.INVARIANT.value == "invariant"
    assert EntityType.DECISION.value == "decision"
    assert EntityType.LESSON.value == "lesson"
    assert EntityType.SPEC_SECTION.value == "spec_section"
    assert EntityType.OP_RULE.value == "op_rule"
    assert EntityType.FEATURE.value == "feature"
    assert EntityType.SLICE.value == "slice"


def test_invariant_round_trip():
    inv = Invariant(
        entity_type="invariant",
        id="INV-008",
        statement="close_slice is the sole producer of the slice-complete commit.",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep=r"def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    dumped = inv.model_dump(mode="json")
    loaded = Invariant.model_validate(dumped)
    assert loaded == inv


def test_invariant_id_format_validation():
    with pytest.raises(ValidationError):
        Invariant(
            entity_type="invariant",
            id="bad-id-format",
            statement="x",
            target=PathAnchor(path="x"),
            grep="x",
            architecture_anchor=PathAnchor(path="x"),
        )


def test_decision_round_trip():
    d = Decision(
        entity_type="decision",
        id="parallelism-v1",
        name="Parallelism v1",
        status="accepted",
        firmness="firm",
        topic="execution",
        date=date(2026, 4, 15),
        invariants_touched=["INV-005"],
        supersedes=[],
        superseded_by=None,
        body_anchor=PathAnchor(path="docs/adr/parallelism-v1.md"),
        decision_points=[],
    )
    dumped = d.model_dump(mode="json")
    loaded = Decision.model_validate(dumped)
    assert loaded == d


def test_lesson_round_trip():
    lesson = Lesson(
        entity_type="lesson",
        id="L-001",
        title="Pipeline-bypass temptation",
        discovered=date(2026, 4, 11),
        pattern="A bug surfaces mid-session…",
        instances=["f531087"],
        rule="Open a slice, run /decision, or write nothing.",
        anti_patterns=["it's just docs", "only three lines"],
        body_anchor=PathAnchor(path="docs/lessons.md"),
    )
    assert Lesson.model_validate(lesson.model_dump(mode="json")) == lesson


def test_lesson_id_format_validation():
    with pytest.raises(ValidationError):
        Lesson(
            entity_type="lesson",
            id="not-a-lesson-id",
            title="x",
            discovered=date(2026, 1, 1),
            pattern="x",
            rule="x",
            body_anchor=PathAnchor(path="x"),
        )


def test_spec_section_round_trip():
    s = SpecSection(
        entity_type="spec_section",
        id="§13",
        title="Failure modes",
        body_anchor=PathAnchor(path="docs/spec-v1.md"),
    )
    assert SpecSection.model_validate(s.model_dump(mode="json")) == s


def test_op_rule_round_trip():
    o = OpRule(
        entity_type="op_rule",
        id="phase-skill-guide/phase-4",
        statement="Auditor produces pass/fail verdict on declared invariants.",
        scope="docs/operational-reference.md § Phase Skill Guide",
        body_anchor=PathAnchor(path="docs/operational-reference.md", line=85),
    )
    assert OpRule.model_validate(o.model_dump(mode="json")) == o


def test_feature_round_trip():
    f = Feature(
        entity_type="feature",
        id="compression",
        name="Slice compression",
        intent="Ship compression protocol.",
        shaped_from="docs/plans/2026-04-18-slice-compression-protocol-design.md",
        slice_ids=["compression/doc-cleanup-tail", "compression/infrastructure"],
    )
    assert Feature.model_validate(f.model_dump(mode="json")) == f


def test_slice_round_trip():
    s = Slice(
        entity_type="slice",
        id="compression/lever-2-orchestrator-split",
        name="Compression Lever 2 — orchestrator package split",
        feature_id="compression",
        status="complete",
        started=date(2026, 4, 25),
        completed=date(2026, 4, 25),
        invariants_touched=["INV-003", "INV-004", "INV-008", "INV-009"],
        adrs_referenced=[],
        adrs_created=[],
        envelope_paths=["scripts/slice_orchestrator/**"],
        envelope_out_of_scope=["any test-file edit"],
        close_commit="84f1749",
    )
    assert Slice.model_validate(s.model_dump(mode="json")) == s


def test_slice_id_format_validation():
    with pytest.raises(ValidationError):
        Slice(
            entity_type="slice",
            id="not-hierarchical",
            name="x",
            feature_id="x",
            status="complete",
            started=date(2026, 4, 25),
            close_commit="abc1234",
        )

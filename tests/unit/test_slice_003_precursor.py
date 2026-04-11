"""SLICE-003-precursor Phase 2 validation suite.

Verifies the three textual mechanisms ADR-004 commits to via intent.md S1-S6:
  - `docs/operational-reference.md § Phase Skill Guide` section (S1)
  - `/catchup` phase-entry surfacing (S2)
  - `/start-slice` phase-entry surfacing + D3 adrs-referenced gate (S3, S4)

Tests V1-V6 map one-to-one to intent.md's structural assertions. They are
designed to fail RED at Phase 2 commit time because the production code does
not yet exist, and to flip GREEN at Phase 3 Builder's implementation commit.
This is the direct TDD RED+Verify RED adaptation ADR-004 D4 names as the
Skeptic's primary skill, bisected by the Phase 2 -> Phase 3 session boundary.

The INV-003 phase-order canary is the intentional exception: it is GREEN
from the start and exists as a regression check against future rename drift
against ADR-004 D1's load-bearing phase and role names.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OPREF = REPO / "docs" / "operational-reference.md"
CATCHUP = REPO / "commands" / "claude-code" / "catchup.md"
STARTSLICE = REPO / "commands" / "claude-code" / "start-slice.md"
ARCH = REPO / "docs" / "ARCHITECTURE.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _extract_section(body: str, heading: str) -> str | None:
    """Extract a Markdown section from `heading` to the next same-or-higher heading."""
    lines = body.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return None
    level = len(heading) - len(heading.lstrip("#"))
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            this_level = len(stripped) - len(stripped.lstrip("#"))
            if this_level <= level:
                return "\n".join(lines[start:i])
    return "\n".join(lines[start:])


def _extract_region(body: str, start_marker: str, end_marker: str) -> str | None:
    start = body.find(start_marker)
    if start == -1:
        return None
    end = body.find(end_marker, start + len(start_marker))
    return body[start:end] if end != -1 else body[start:]


def test_v1_phase_skill_guide_section_exists() -> None:
    """V1: exactly one `## Phase Skill Guide` heading in operational-reference.md (S1)."""
    body = _read(OPREF)
    count = len(re.findall(r"(?m)^## Phase Skill Guide\s*$", body))
    assert count == 1, (
        f"Expected exactly 1 '## Phase Skill Guide' heading in "
        f"{OPREF.relative_to(REPO)}, found {count}. (intent.md V1)"
    )


def test_v2_phase_skill_guide_content() -> None:
    """V2 + A5 gap-fix: 4 phases x 4 roles, >=1 skill, S1.b exclusion list landed."""
    body = _read(OPREF)
    section = _extract_section(body, "## Phase Skill Guide")
    assert section is not None, (
        f"Phase Skill Guide section not found in {OPREF.relative_to(REPO)}. (V2)"
    )
    for phase in ("Intent", "Validation", "Implementation", "Integration"):
        assert phase in section, (
            f"Phase name {phase!r} missing from Phase Skill Guide. (V2)"
        )
    for role in ("Reader", "Skeptic", "Builder", "Auditor"):
        assert role in section, (
            f"Role name {role!r} missing from Phase Skill Guide. (V2)"
        )
    primary_skills = (
        "test-driven-development",
        "verification-before-completion",
        "brainstorming",
    )
    assert any(s in section for s in primary_skills), (
        f"No primary superpowers skill found in Phase Skill Guide; "
        f"expected >=1 of {primary_skills} per ADR-004 D4 table rows 2-4. (V2)"
    )
    phase1_ok = ("no primary fit" in section.lower()) or ("—" in section)
    assert phase1_ok, (
        "Phase 1 row must carry 'no primary fit' note or an em-dash per "
        "ADR-004 D4 Phase 1 row semantics. (V2)"
    )
    # A5 sub-check: S1.b explicit-exclusions list landed (>=1 excluded skill name)
    excluded = (
        "dispatching-parallel-agents",
        "executing-plans",
        "finishing-a-development-branch",
        "using-git-worktrees",
        "writing-skills",
        "writing-plans",
    )
    assert any(s in section for s in excluded), (
        f"S1.b exclusion list missing from Phase Skill Guide; "
        f"expected >=1 of {excluded}. (V2 sub-check for A5 gap)"
    )


def test_v3_living_registry_and_adr_citation() -> None:
    """V3: S1.c 'living registry' note AND S1.d ADR-004 citation."""
    body = _read(OPREF)
    section = _extract_section(body, "## Phase Skill Guide")
    assert section is not None, "Phase Skill Guide section not found. (V3)"
    assert "living registry" in section.lower(), (
        "S1.c: Phase Skill Guide must state it is a living registry. (V3)"
    )
    assert "ADR-004" in section, (
        "S1.d: Phase Skill Guide must cite ADR-004 as authoritative source. (V3)"
    )


def test_v4_catchup_references_phase_skill_guide() -> None:
    """V4: /catchup Mode A region references Phase Skill Guide."""
    body = _read(CATCHUP)
    mode_a = _extract_region(body, "### Mode A", "### Mode B")
    assert mode_a is not None, (
        f"Mode A region not found in {CATCHUP.relative_to(REPO)}. (V4)"
    )
    assert "Phase Skill Guide" in mode_a, (
        "S2: /catchup Mode A must reference 'Phase Skill Guide' at phase entry. (V4)"
    )


def test_v5_startslice_references_phase_skill_guide() -> None:
    """V5: /start-slice references Phase Skill Guide at Step 3 or Step 5 (phase-entry moments)."""
    body = _read(STARTSLICE)
    step3 = _extract_region(body, "## Step 3", "## Step 4") or ""
    step5 = _extract_region(body, "## Step 5", "## Step 6") or ""
    in_step3 = "Phase Skill Guide" in step3
    in_step5 = "Phase Skill Guide" in step5
    assert in_step3 or in_step5, (
        "S3: /start-slice must reference 'Phase Skill Guide' at a phase-entry moment "
        "(Step 3 gate-pass or Step 5 intent guidance). (V5)"
    )


def test_v6_startslice_step3_d3_gate() -> None:
    """V6: Step 3 gate table contains D3 adrs-referenced check, empty-trivial semantics, missing-slug message."""
    body = _read(STARTSLICE)
    step3 = _extract_region(body, "## Step 3", "## Step 4")
    assert step3 is not None, (
        f"Step 3 region not found in {STARTSLICE.relative_to(REPO)}. (V6)"
    )
    assert "adrs-referenced" in step3, (
        "S4.a: Step 3 gate table Phase 2 row must check 'adrs-referenced' field. (V6)"
    )
    step3_lower = step3.lower()
    empty_semantics = "empty" in step3_lower and (
        "trivial" in step3_lower or "pass" in step3_lower
    )
    assert empty_semantics, (
        "S4.b: Step 3 must explain empty-adrs-referenced-passes-trivially semantics. (V6)"
    )
    assert re.search(r"missing\s+adr", step3, re.IGNORECASE), (
        "S4.c: Step 3 failure path must name missing ADR slug(s). (V6)"
    )


def test_inv_003_four_phase_order_and_role_names() -> None:
    """INV-003 sub-claim (1) regression canary: four phases in canonical order + four role names.

    This test is GREEN from the start. It exists as a regression canary against
    future rename drift. INV-003 sub-claims (2), (3), (4) are covered by V1, V4+V5,
    and V6 respectively; this canary covers sub-claim (1) — the load-bearing
    phase/role name lock per ADR-004 D1.
    """
    body = _read(ARCH)
    inv_idx = body.find("INV-003")
    assert inv_idx != -1, "INV-003 not found in ARCHITECTURE.md"
    inv_block = body[inv_idx : inv_idx + 1500]
    phases = ("Intent", "Validation", "Implementation", "Integration")
    last = -1
    for phase in phases:
        idx = inv_block.find(phase)
        assert idx > last, (
            f"Phase {phase!r} out of canonical order in INV-003 block "
            f"(expected order: {phases}). INV-003 canary."
        )
        last = idx
    for role in ("Reader", "Skeptic", "Builder", "Auditor"):
        assert role in inv_block, (
            f"Role {role!r} missing from INV-003 block. INV-003 canary."
        )

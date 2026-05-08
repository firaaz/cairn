"""F2 consumer-doc surface tests.

Covers, per ``docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface.md``:

- ``test_claude_md_cross_cutting_sections_carry_both_tag`` (F2.1 Step 1, FLI-1
  scaffolding)
- ``test_consumer_md_anchors_resolve_into_claude_md`` (F2.1 Step 4, FLI-1)
- ``test_phase_skill_mapping_doc_exists`` (F2.4 Step 1)
- ``test_phase_skill_mapping_doc_preserves_validator_regex_anchors`` (Risk
  Surface coverage — intent.md lines 40-42, FLI-3 lines 48)
- ``test_operational_reference_phase_skill_guide_is_a_pointer`` (F2.4 Step 1,
  FLI-4 line 49)
- ``test_adoptable_disciplines_lists_four_disciplines`` (F2.5 Step 1)
- ``test_consumer_md_word_count_within_budget`` (FLI-6 line 51)

These tests are intentionally RED at Phase 2: the files they assert against
have not been authored yet. Phase 3 lands the artefacts; Phase 4 audits.
"""

from __future__ import annotations

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent

CLAUDE_MD = CAIRN_ROOT / "CLAUDE.md"
CONSUMER_MD = CAIRN_ROOT / "CONSUMER.md"
OPS_REF = CAIRN_ROOT / "docs" / "operational-reference.md"
PHASE_SKILL_MAPPING = CAIRN_ROOT / "docs" / "phase-skill-mapping.md"
ADOPTABLE = CAIRN_ROOT / "docs" / "adoptable-disciplines.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(heading_text: str) -> str:
    """Approximate GitHub-flavoured slugify per FLI-1 line 46.

    Lowercase; spaces and ``[``/``]`` -> ``-``; strip non-alphanumeric except
    ``-``.
    """
    s = heading_text.lower()
    s = s.replace("[", "-").replace("]", "-")
    s = s.replace(" ", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    # collapse multiple dashes (cosmetic — anchors typically squash these too)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _extract_heading_anchors(md_text: str) -> set[str]:
    """Return the set of slugified heading anchors that appear in ``md_text``.

    Both ATX headings (``## Foo``) and bold-lead callouts written in CLAUDE.md
    style (``**Operator envelope** (...)``) are surfaces a CONSUMER.md anchor
    might target. We collect both.
    """
    anchors: set[str] = set()
    for line in md_text.splitlines():
        stripped = line.strip()
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if m:
            anchors.add(_slugify(m.group(2)))
            continue
        # Bold-lead callouts: lines that begin with **...** form pseudo-anchors
        # in many markdown renderers. Capture the bolded label.
        b = re.match(r"^\*\*(.+?)\*\*", stripped)
        if b:
            anchors.add(_slugify(b.group(1)))
    return anchors


# ---------------------------------------------------------------------------
# T1 — CLAUDE.md cross-cutting sections carry [both]/[maintainer] (F2.1 Step 1)
# ---------------------------------------------------------------------------


def test_claude_md_cross_cutting_sections_carry_both_tag() -> None:
    """Each cross-cutting section in CLAUDE.md must carry a ``[both]`` or
    ``[maintainer]`` audience tag per intent.md line 23 (T1 audience model).

    The ``.slice-system`` rule and the symlink-recursion hazard are
    maintainer-only per plan F2.1 Step 2; the rest must be ``[both]``.
    """
    text = CLAUDE_MD.read_text()
    lines = text.splitlines()

    # Map: scan-anchor (substring uniquely identifying the line) -> required tag set.
    expectations: list[tuple[str, set[str]]] = [
        ("## Identifier scheme", {"[both]"}),
        ("Edit canonical paths only, never via", {"[maintainer]"}),
        ("Hook dependencies.", {"[both]"}),
        ("Symlink recursion hazard.", {"[maintainer]"}),
        ("ADRs are append-only.", {"[both]"}),
        ("Force-push policy.", {"[both]"}),
        ("Operator envelope", {"[both]"}),
    ]

    missing: list[str] = []
    for needle, allowed in expectations:
        found_idx = None
        for i, line in enumerate(lines):
            if needle in line:
                found_idx = i
                break
        if found_idx is None:
            missing.append(f"line containing {needle!r} not found in CLAUDE.md")
            continue
        # Tag must appear on the same line or the line directly above.
        candidates = []
        if found_idx - 1 >= 0:
            candidates.append(lines[found_idx - 1])
        candidates.append(lines[found_idx])
        joined = "\n".join(candidates)
        if not any(tag in joined for tag in allowed):
            missing.append(
                f"line containing {needle!r} missing required tag {allowed} "
                f"(scanned line and its predecessor)"
            )

    assert not missing, "CLAUDE.md audience-tag failures:\n  - " + "\n  - ".join(
        missing
    )


# ---------------------------------------------------------------------------
# FLI-1 — CONSUMER.md anchors resolve into CLAUDE.md (F2.1 Step 4)
# ---------------------------------------------------------------------------


def test_consumer_md_anchors_resolve_into_claude_md() -> None:
    """Every ``CLAUDE.md#<anchor>`` link in CONSUMER.md must resolve to a real
    CLAUDE.md heading under the slugify approximation per FLI-1 line 46.
    """
    consumer_text = CONSUMER_MD.read_text()
    claude_text = CLAUDE_MD.read_text()

    # Match markdown links of the form (CLAUDE.md#anchor) or (./CLAUDE.md#anchor).
    pattern = re.compile(r"\(\.{0,2}/?CLAUDE\.md#([A-Za-z0-9_\-]+)\)")
    referenced = set(pattern.findall(consumer_text))

    assert referenced, (
        "CONSUMER.md must contain at least one anchor link into CLAUDE.md "
        "per plan F2.1 Step 3 / Step 5; found none."
    )

    available = _extract_heading_anchors(claude_text)
    unresolved = sorted(a for a in referenced if a not in available)
    assert not unresolved, (
        f"CONSUMER.md anchors that do not resolve to a CLAUDE.md heading "
        f"under the FLI-1 slugify approximation: {unresolved}\n"
        f"Available CLAUDE.md anchors (sample): "
        f"{sorted(available)[:10]}..."
    )


# ---------------------------------------------------------------------------
# FLI-6 — CONSUMER.md ≤ 1500 words (intent.md line 51)
# ---------------------------------------------------------------------------


def test_consumer_md_word_count_within_budget() -> None:
    """CONSUMER.md is a navigation surface, not an alternative spec; cap is
    1500 words per FLI-6 line 51.
    """
    text = CONSUMER_MD.read_text()
    word_count = len(text.split())
    assert word_count <= 1500, (
        f"CONSUMER.md word count {word_count} exceeds the 1500-word budget "
        f"established by FLI-6 (intent.md line 51)."
    )


# ---------------------------------------------------------------------------
# F2.4 — phase-skill-mapping promotion (existence)
# ---------------------------------------------------------------------------


def test_phase_skill_mapping_doc_exists() -> None:
    """``docs/phase-skill-mapping.md`` exists and names the four agent slugs,
    the four role names, and the literal ``Superpowers`` token per plan F2.4
    Step 1 / intent.md Verification line 35.
    """
    text = PHASE_SKILL_MAPPING.read_text()
    required_tokens = [
        "phase-1-tdd",
        "phase-2-tdd",
        "phase-3-tdd",
        "phase-4-tdd",
        "Reader",
        "Skeptic",
        "Builder",
        "Auditor",
        "Superpowers",
    ]
    missing = [tok for tok in required_tokens if tok not in text]
    assert not missing, (
        f"docs/phase-skill-mapping.md missing required tokens: {missing}"
    )


# ---------------------------------------------------------------------------
# Risk Surface coverage — INV-003 binding preserved on relocation
# (intent.md lines 40-42, FLI-3 line 48)
# ---------------------------------------------------------------------------


def test_phase_skill_mapping_doc_preserves_validator_regex_anchors() -> None:
    """RISK SURFACE COVERAGE TEST.

    intent.md lines 40-42 flag the T4 relocation as the F2 risk: the new
    ``docs/phase-skill-mapping.md`` becomes the binding surface
    ``scripts/validate_architecture.py``'s ``validate_phase_topology`` regex
    extracts from. Per FLI-3 line 48, the relocated doc MUST preserve the
    four canonical agent slugs, the four role names, and the literal
    ``Superpowers`` token — these are the regex anchors INV-003 keys on.

    This test goes beyond ``test_phase_skill_mapping_doc_exists`` (which
    only requires the tokens appear once); here we additionally require the
    role names appear in the *same* row-like context as the agent slugs, so
    the binding-surface table structure is preserved end-to-end.
    """
    text = PHASE_SKILL_MAPPING.read_text()

    # 1. Four canonical agent slugs.
    for slug in ("phase-1-tdd", "phase-2-tdd", "phase-3-tdd", "phase-4-tdd"):
        assert slug in text, (
            f"{slug!r} missing from docs/phase-skill-mapping.md — "
            f"INV-003 validate_phase_topology regex anchor would break per "
            f"intent.md Risk Surface lines 40-42."
        )

    # 2. Four role names.
    for role in ("Reader", "Skeptic", "Builder", "Auditor"):
        assert role in text, (
            f"Role name {role!r} missing from docs/phase-skill-mapping.md — "
            f"INV-003 binding surface would break per FLI-3 line 48."
        )

    # 3. Literal ``Superpowers`` token (intent.md line 35 enumerates it as
    #    required; the role-to-skill mapping table relies on it).
    assert "Superpowers" in text, (
        "Literal 'Superpowers' token missing from docs/phase-skill-mapping.md "
        "— required by FLI-3 line 48 / intent.md Verification line 35."
    )

    # 4. Structural co-occurrence: each role name must appear on a line that
    #    also names its phase or appear in the same paragraph as its phase
    #    slug. We require co-occurrence in a 4-line sliding window so the
    #    table-row binding pattern the validator relies on is preserved.
    role_phase_pairs = [
        ("phase-1-tdd", "Reader"),
        ("phase-2-tdd", "Skeptic"),
        ("phase-3-tdd", "Builder"),
        ("phase-4-tdd", "Auditor"),
    ]
    lines = text.splitlines()
    for slug, role in role_phase_pairs:
        co_occurs = False
        for i, line in enumerate(lines):
            if slug in line:
                window = "\n".join(lines[max(0, i - 4) : i + 5])
                if role in window:
                    co_occurs = True
                    break
            if role in line:
                window = "\n".join(lines[max(0, i - 4) : i + 5])
                if slug in window:
                    co_occurs = True
                    break
        assert co_occurs, (
            f"{slug!r} and {role!r} must co-occur within a 4-line window in "
            f"docs/phase-skill-mapping.md to preserve the validator's "
            f"row-extraction binding (intent.md Risk Surface lines 40-42)."
        )


# ---------------------------------------------------------------------------
# FLI-4 — operational-reference Phase Skill Guide is a pointer (F2.4 Step 1)
# ---------------------------------------------------------------------------


def test_operational_reference_phase_skill_guide_is_a_pointer() -> None:
    """After F2.4, ``docs/operational-reference.md``'s ``## Phase Skill Guide``
    section must contain a literal link to ``docs/phase-skill-mapping.md``
    and have body ≤ 5 lines per FLI-4 line 49 / plan F2.4 Step 1.
    """
    text = OPS_REF.read_text()
    lines = text.splitlines()

    section_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Phase Skill Guide":
            section_idx = i
            break
    assert section_idx is not None, (
        "## Phase Skill Guide heading not found in docs/operational-reference.md"
    )

    # Find next heading at the same depth or shallower to bound the section body.
    end_idx = len(lines)
    for j in range(section_idx + 1, len(lines)):
        if re.match(r"^#{1,2}\s", lines[j]):
            end_idx = j
            break

    body = lines[section_idx + 1 : end_idx]
    # Trim leading/trailing blanks for a "lines of content" measure.
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()

    body_text = "\n".join(body)

    assert "docs/phase-skill-mapping.md" in body_text, (
        "Phase Skill Guide section in operational-reference.md must link to "
        "docs/phase-skill-mapping.md (FLI-4 line 49)."
    )

    non_empty_lines = [ln for ln in body if ln.strip()]
    assert len(non_empty_lines) <= 5, (
        f"Phase Skill Guide pointer body has {len(non_empty_lines)} non-empty "
        f"lines, exceeds the ≤5 cap from FLI-4 line 49.\nBody:\n{body_text}"
    )


# ---------------------------------------------------------------------------
# F2.5 — adoptable-disciplines lists four disciplines
# ---------------------------------------------------------------------------


def test_adoptable_disciplines_lists_four_disciplines() -> None:
    """``docs/adoptable-disciplines.md`` exists and contains a section per
    discipline with a literal heading naming each, plus an ``Integration cost``
    line per entry per plan F2.5 Step 1.
    """
    text = ADOPTABLE.read_text()

    # Discipline name keywords that must each appear as a heading anchor.
    disciplines = [
        "Handoff",  # handoff-as-pointer
        "hooks",  # the three hooks
        "validator",  # architecture validator
        "phase-skill-mapping",  # phase-skill-mapping table
    ]
    missing_disciplines = [d for d in disciplines if d.lower() not in text.lower()]
    assert not missing_disciplines, (
        f"docs/adoptable-disciplines.md missing discipline references: "
        f"{missing_disciplines}"
    )

    # Each discipline section must carry an "Integration cost" line.
    integration_cost_count = len(
        re.findall(r"Integration[- ]cost", text, flags=re.IGNORECASE)
    )
    assert integration_cost_count >= 4, (
        f"docs/adoptable-disciplines.md must have ≥4 'Integration cost' lines "
        f"(one per discipline) per plan F2.5 Step 1; found "
        f"{integration_cost_count}."
    )

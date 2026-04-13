"""SLICE-006 Phase 2 validation suite.

Verifies the phase-pipeline evaluation ADR produced by SLICE-006.
Tests V1–V5 map to intent.md's verification items. RED at Phase 2
(ADR not written yet); GREEN after Phase 3 writes the ADR.

Ambiguity resolutions: .claude/current-slice/validation/approach.md
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ADR_DIR = REPO / "docs" / "adr"

# Files/fields that string-match on phase names per ARCHITECTURE.md:36
PHASE_NAME_REFERENCES = [
    "commands/claude-code/catchup.md",
    "commands/claude-code/start-slice.md",
    "checks/scope-guard.sh",
    "checks/reality-check.sh",
    "docs/operational-reference.md",
    "slice.yaml",
]

COMPLETED_SLICES = {"SLICE-001", "SLICE-002", "SLICE-003", "SLICE-004", "SLICE-005"}


def _find_phase_adr() -> Path | None:
    """Find the SLICE-006 output ADR matching docs/adr/*-phase-*.md, excluding ADR-004."""
    matches = sorted(ADR_DIR.glob("*-phase-*.md"))
    return next((p for p in matches if not p.name.startswith("004-")), None)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter delimited by --- markers."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None


def _extract_section(body: str, heading: str) -> str | None:
    """Extract a Markdown section from heading to next same-or-higher heading."""
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


def _adr_supersedes_004(fm: dict) -> bool:
    """Check if ADR supersedes ADR-004 (fully or by section)."""
    supersedes = fm.get("supersedes", []) or []
    supersedes_sections = fm.get("supersedes-sections", []) or []
    all_refs = [str(s) for s in supersedes + supersedes_sections]
    return any("ADR-004" in ref or "004" in ref for ref in all_refs)


# ---------------------------------------------------------------------------
# V1: ADR addresses all four specification items
# ---------------------------------------------------------------------------


class TestV1FourSpecItems:
    """V1: The output ADR explicitly addresses all four specification items."""

    def _get_adr_text(self) -> str:
        path = _find_phase_adr()
        assert path is not None, (
            "No ADR matching docs/adr/*-phase-*.md (excluding 004-*) found. "
            "Phase 3 must write this file. (V1)"
        )
        return _read(path)

    def test_v1a_addresses_phase_count(self):
        """V1a: ADR addresses phase count and names."""
        text = self._get_adr_text()
        count_patterns = [
            r"phase count",
            r"four phases",
            r"three phases",
            r"five phases",
            r"number of phases",
            r"phase.{1,20}names?",
        ]
        found = any(re.search(p, text, re.IGNORECASE) for p in count_patterns)
        assert found, (
            "ADR must address phase count and names. None of the expected "
            "patterns found. (V1a)"
        )

    def test_v1b_addresses_role_flexibility(self):
        """V1b: ADR addresses role flexibility."""
        text = self._get_adr_text()
        has_roles = bool(re.search(r"Reader|Skeptic|Builder|Auditor", text))
        has_flex = bool(
            re.search(
                r"flexib|vacu|work.+types?|non-code|categories|all.+work",
                text,
                re.IGNORECASE,
            )
        )
        assert has_roles and has_flex, (
            f"ADR must address role flexibility. "
            f"Roles mentioned: {has_roles}, flexibility discussed: {has_flex}. (V1b)"
        )

    def test_v1c_addresses_ceremony_calibration(self):
        """V1c: ADR addresses ceremony calibration."""
        text = self._get_adr_text()
        ceremony_patterns = [
            r"ceremony",
            r"lightweight",
            r"skip\w*\s+phase",
            r"phase.{1,20}weight",
            r"calibrat",
        ]
        found = any(re.search(p, text, re.IGNORECASE) for p in ceremony_patterns)
        assert found, (
            "ADR must address ceremony calibration. None of the expected "
            "patterns found. (V1c)"
        )

    def test_v1d_addresses_protocol_extraction(self):
        """V1d: ADR addresses protocol extraction readiness."""
        text = self._get_adr_text()
        extraction_patterns = [
            r"protocol.{1,20}extract",
            r"extract.{1,20}protocol",
            r"roadmap.{1,20}item.{1,5}2",
            r"protocols?/phase",
            r"extraction.{1,20}read",
        ]
        found = any(re.search(p, text, re.IGNORECASE) for p in extraction_patterns)
        assert found, (
            "ADR must address protocol extraction readiness. None of the "
            "expected patterns found. (V1d)"
        )


# ---------------------------------------------------------------------------
# V2: ADR cites at least 3 completed slices with evidence
# ---------------------------------------------------------------------------


def test_v2_cites_three_slices():
    """V2: ADR cites ≥3 of SLICE-001..005 with substantive context per citation."""
    path = _find_phase_adr()
    assert path is not None, "Phase ADR not found. (V2 pre-req)"
    text = _read(path)

    cited = set()
    for slice_id in COMPLETED_SLICES:
        if slice_id not in text:
            continue
        # Require at least one line with the slice ID that has substantive
        # surrounding context (more than just a bare reference in a list)
        lines_with_ref = [
            line
            for line in text.splitlines()
            if slice_id in line and len(line.strip()) > len(slice_id) + 10
        ]
        if lines_with_ref:
            cited.add(slice_id)

    assert len(cited) >= 3, (
        f"ADR must cite ≥3 completed slices with substantive context. "
        f"Found {len(cited)} ({', '.join(sorted(cited)) or 'none'}). (V2)"
    )


# ---------------------------------------------------------------------------
# V3: If superseding — Consequences names phase-name files + migration
# ---------------------------------------------------------------------------


def test_v3_supersession_file_enumeration():
    """V3: If superseding ADR-004, Consequences names every phase-name-matching
    file and declares a migration path for each."""
    path = _find_phase_adr()
    assert path is not None, "Phase ADR not found. (V3 pre-req)"
    text = _read(path)
    fm = _parse_frontmatter(text)
    assert fm is not None, "Phase ADR has no valid frontmatter. (V3 pre-req)"

    if not _adr_supersedes_004(fm):
        return  # V3 conditional on supersession

    consequences = _extract_section(text, "## Consequences")
    assert consequences is not None, (
        "Superseding ADR must have a ## Consequences section. (V3)"
    )

    missing = []
    for filepath in PHASE_NAME_REFERENCES:
        filename = Path(filepath).name
        stem = Path(filepath).stem
        if not (
            filename in consequences or stem in consequences or filepath in consequences
        ):
            missing.append(filepath)

    assert not missing, (
        f"Superseding ADR's Consequences must name every file that string-matches "
        f"on phase names. Missing: {missing}. (V3)"
    )

    migration_patterns = [r"migrat", r"updat", r"renam", r"adapt", r"propagat"]
    has_migration = any(
        re.search(p, consequences, re.IGNORECASE) for p in migration_patterns
    )
    assert has_migration, (
        "Superseding ADR's Consequences must declare migration path for "
        "each phase-name file. No migration-related language found. (V3)"
    )


# ---------------------------------------------------------------------------
# V4: If confirming — explains what changed to justify re-confirmation
# ---------------------------------------------------------------------------


def test_v4_confirmation_justification():
    """V4: If confirming ADR-004, the ADR explains what changed since the
    original decision to justify re-confirmation (not just 'it still works')."""
    path = _find_phase_adr()
    assert path is not None, "Phase ADR not found. (V4 pre-req)"
    text = _read(path)
    fm = _parse_frontmatter(text)
    assert fm is not None, "Phase ADR has no valid frontmatter. (V4 pre-req)"

    if _adr_supersedes_004(fm):
        return  # V4 conditional on confirmation

    change_patterns = [
        r"since.{1,30}ADR.?004",
        r"new evidence",
        r"additional.{1,20}slice",
        r"experience.{1,20}since",
        r"slices?.{1,20}shipped",
        r"changed.{1,20}since",
        r"evidence.{1,20}from.{1,30}slice",
        r"five.{1,20}slices?",
        r"SLICE.00[1-5].{1,100}(show|demonstrat|confirm|reveal)",
    ]
    found = any(re.search(p, text, re.IGNORECASE) for p in change_patterns)
    assert found, (
        "Confirming ADR must explain what changed since the original "
        "ADR-004 decision to justify re-confirmation — not just "
        "'it still works'. (V4)"
    )


# ---------------------------------------------------------------------------
# V5: A2 tripwire evaluated with finding
# ---------------------------------------------------------------------------


def test_v5_a2_tripwire_evaluation():
    """V5: The A2 tripwire status (ADR-004 Risk Register) is evaluated
    against available evidence and the finding is recorded."""
    path = _find_phase_adr()
    assert path is not None, "Phase ADR not found. (V5 pre-req)"
    text = _read(path)

    assert "A2" in text, (
        "ADR must evaluate the A2 tripwire status from ADR-004's "
        "Risk Register. No 'A2' reference found. (V5)"
    )

    a2_patterns = [
        r"A2.{0,200}(tripwire|canary)",
        r"(tripwire|canary).{0,200}A2",
        r"A2.{0,200}(evaluat|finding|evidence|status|fired|not fired)",
    ]
    has_evaluation = any(
        re.search(p, text, re.IGNORECASE | re.DOTALL) for p in a2_patterns
    )
    assert has_evaluation, (
        "ADR must evaluate A2 tripwire status with a finding. Found 'A2' but "
        "no evaluation/finding language near it. (V5)"
    )

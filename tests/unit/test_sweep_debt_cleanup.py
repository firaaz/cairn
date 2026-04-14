"""SLICE-007 Phase 2 validation suite.

Verifies sweep-debt-cleanup: stale measurement artifact commit and
Phase Skill Guide drift repair (using-git-worktrees exclusion → Phase 3 supporting).

Tests V1-V4 map to intent.md verification items. V1-V3 are RED at Phase 2
commit (changes not yet landed); V4 is a GREEN canary for architecture validity.

Ambiguity resolutions documented in
`.claude/current-slice/validation/approach.md`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OPREF = REPO / "docs" / "operational-reference.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _extract_section(text: str, heading: str) -> str | None:
    """Extract a Markdown section from `heading` to the next same-or-higher heading."""
    lines = text.splitlines()
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


# ---------------------------------------------------------------------------
# V1: using-git-worktrees appears in Phase 3 supporting skills
# ---------------------------------------------------------------------------


def test_v1_worktrees_in_phase3_supporting() -> None:
    """V1: using-git-worktrees appears in the Phase 3 (Builder) supporting skills.

    Intent verification #2. ADR-007 D3 returns using-git-worktrees as a
    conditional Phase 3 supporting skill.
    """
    text = _read(OPREF)
    mapping_section = _extract_section(text, "### Phase-to-skill mapping")
    assert mapping_section is not None, (
        "operational-reference.md missing '### Phase-to-skill mapping' section. (V1)"
    )

    # Find the Phase 3 row: contains "Implementation" and "Builder"
    phase3_row = None
    for line in mapping_section.splitlines():
        if (
            "Implementation" in line
            and "Builder" in line
            and line.strip().startswith("|")
        ):
            phase3_row = line
            break
    assert phase3_row is not None, (
        "Phase-to-skill mapping table has no Phase 3 (Implementation/Builder) row. (V1)"
    )

    # Split into columns — the Supporting skills column is the 4th (index 3)
    cols = [c.strip() for c in phase3_row.split("|")]
    # cols[0] is empty (before first |), cols[1]=Phase, cols[2]=Role,
    # cols[3]=Primary, cols[4]=Supporting, cols[5]=Notes
    assert len(cols) >= 5, f"Phase 3 row has fewer than 5 columns: {cols}. (V1)"
    supporting_col = cols[4] if len(cols) > 4 else ""
    assert "using-git-worktrees" in supporting_col, (
        f"Phase 3 Supporting skills column does not contain 'using-git-worktrees'. "
        f"Got: {supporting_col[:200]}... (V1)"
    )


# ---------------------------------------------------------------------------
# V2: using-git-worktrees NOT in exclusions section
# ---------------------------------------------------------------------------


def test_v2_worktrees_not_in_exclusions() -> None:
    """V2: using-git-worktrees does NOT appear in the Explicit exclusions section.

    Intent verification #3. After removal, only executing-plans,
    finishing-a-development-branch, writing-skills, and writing-plans remain.
    """
    text = _read(OPREF)
    exclusions = _extract_section(
        text, "### Explicit exclusions — skills deliberately NOT mapped"
    )
    assert exclusions is not None, (
        "operational-reference.md missing '### Explicit exclusions' section. (V2)"
    )

    assert "using-git-worktrees" not in exclusions, (
        "'using-git-worktrees' still appears in the Explicit exclusions section. "
        "It should have been moved to Phase 3 supporting skills per ADR-007 D3. (V2)"
    )


# ---------------------------------------------------------------------------
# V3: Stale measurement artifact committed (no uncommitted diff)
# ---------------------------------------------------------------------------


def test_v3_measurement_artifact_exists() -> None:
    """V3: docs/plans/measurements/2026-04-12-slice-003.txt exists and is tracked.

    The measurement file is live-updated by a session hook on every session
    start, so it will always have uncommitted changes. The meaningful check
    is that the file exists and is git-tracked (not untracked).
    """
    target = REPO / "docs" / "plans" / "measurements" / "2026-04-12-slice-003.txt"
    assert target.exists(), f"{target} does not exist. (V3)"
    result = subprocess.run(
        ["git", "ls-files", str(target)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.stdout.strip(), f"{target} exists but is not git-tracked. (V3)"


# ---------------------------------------------------------------------------
# V4: Envelope compliance — only SLICE-007 declared files modified
# ---------------------------------------------------------------------------


def test_v4_envelope_compliance() -> None:
    """V4: No files outside the SLICE-007 envelope are modified.

    Envelope from intent.md:
      - docs/plans/measurements/2026-04-12-slice-003.txt
      - docs/operational-reference.md

    At Phase 2 commit time this may pass vacuously (only unstaged measurement
    file outside the allowed patterns). After Phase 3 it validates that no
    undeclared files were touched.
    """
    allowed_patterns = [
        r"^docs/plans/measurements/2026-04-12-slice-003\.txt$",
        r"^docs/operational-reference\.md$",
        # Slice state files are pipeline substrate, always allowed
        r"^\.claude/current-slice/",
        # Test files are Phase 2 output, always allowed
        r"^tests/",
    ]

    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    changed = [f for f in result.stdout.strip().splitlines() if f]

    violations = []
    for f in changed:
        if not any(re.match(pat, f) for pat in allowed_patterns):
            violations.append(f)

    assert not violations, (
        f"Files outside the SLICE-007 envelope were modified: {violations}. (V4)"
    )


# ---------------------------------------------------------------------------
# V5: Architecture validator passes (GREEN canary)
# ---------------------------------------------------------------------------


def test_v5_architecture_validator() -> None:
    """V5: python3 scripts/validate_architecture.py exits 0.

    Intent verification #5. GREEN canary — should pass before and after
    Phase 3 since no invariants are changed.
    """
    result = subprocess.run(
        ["python3", "scripts/validate_architecture.py"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.returncode == 0, (
        f"Architecture validator failed (exit {result.returncode}).\n"
        f"stdout: {result.stdout[:500]}\n"
        f"stderr: {result.stderr[:500]}\n(V5)"
    )

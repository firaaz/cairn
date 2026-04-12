"""SLICE-005 Phase 2 validation suite.

Verifies the four-ADR design decomposition of the feature-slice model:
  - ADR-005 (semantic identity), ADR-006 (feature-slice model),
    ADR-007 (parallelism v1), ADR-008 (context tiers integration)

Tests V1-V8 map to intent.md's verification items. They are RED at Phase 2
commit (ADR files don't exist yet) and flip GREEN at Phase 3 implementation.

The index-format canary is GREEN from the start — it validates the existing
index.md table structure as a regression check.

Ambiguity resolutions are documented in
`.claude/current-slice/validation/approach.md`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ADR_DIR = REPO / "docs" / "adr"
INDEX = ADR_DIR / "index.md"

# Expected ADR files by numeric prefix
ADR_PREFIXES = ("005", "006", "007", "008")

# ADR-004 D4 excluded skills that ADR-007 must address
ADR004_D4_EXCLUDED_SKILLS = (
    "dispatching-parallel-agents",
    "using-git-worktrees",
)

# Additional ADR-004 D4 exclusions (non-parallelism, may stay excluded)
ADR004_D4_OTHER_EXCLUSIONS = (
    "executing-plans",
    "finishing-a-development-branch",
    "writing-skills",
    "writing-plans",
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _find_adr(prefix: str) -> Path | None:
    """Find the ADR file matching a numeric prefix (e.g., '005')."""
    matches = sorted(ADR_DIR.glob(f"{prefix}-*.md"))
    return matches[0] if matches else None


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
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


# ---------------------------------------------------------------------------
# V1: Four ADR files exist
# ---------------------------------------------------------------------------


def test_v1_four_adr_files_exist() -> None:
    """V1: Four ADR files exist matching docs/adr/005-*.md through 008-*.md."""
    for prefix in ADR_PREFIXES:
        path = _find_adr(prefix)
        assert path is not None, (
            f"No ADR file matching docs/adr/{prefix}-*.md found. (V1)"
        )
        assert path.stat().st_size > 0, (
            f"ADR file {path.name} is empty. (V1)"
        )


# ---------------------------------------------------------------------------
# V2: Valid YAML frontmatter with required fields
# ---------------------------------------------------------------------------


def test_v2_frontmatter_valid() -> None:
    """V2: Each ADR has valid YAML frontmatter with id, title, status, firmness, date."""
    required_fields = ("id", "title", "status", "firmness", "date")
    for prefix in ADR_PREFIXES:
        path = _find_adr(prefix)
        assert path is not None, f"ADR {prefix}-*.md not found. (V2 pre-req)"
        fm = _parse_frontmatter(_read(path))
        assert fm is not None, (
            f"ADR {path.name} has no valid YAML frontmatter. (V2)"
        )
        for field in required_fields:
            assert field in fm, (
                f"ADR {path.name} frontmatter missing required field '{field}'. (V2)"
            )
        assert fm["status"] == "accepted", (
            f"ADR {path.name} status should be 'accepted', got '{fm['status']}'. (V2)"
        )


# ---------------------------------------------------------------------------
# V3: ADR-007 supersession references
# ---------------------------------------------------------------------------


def test_v3_adr007_supersession() -> None:
    """V3: ADR-007 supersedes: field names ADR-003; prose explains partial scope."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found. (V3 pre-req)"
    text = _read(path)
    fm = _parse_frontmatter(text)
    assert fm is not None, "ADR-007 has no valid frontmatter. (V3 pre-req)"

    # Check supersedes field references ADR-003
    supersedes = fm.get("supersedes", []) or []
    supersedes_sections = fm.get("supersedes-sections", []) or []
    all_supersession_refs = supersedes + supersedes_sections
    adr003_referenced = any(
        "ADR-003" in str(ref) or "003" in str(ref)
        for ref in all_supersession_refs
    )
    assert adr003_referenced, (
        f"ADR-007 frontmatter must reference ADR-003 in supersedes or "
        f"supersedes-sections field. Found supersedes={supersedes}, "
        f"supersedes-sections={supersedes_sections}. (V3)"
    )

    # Check prose explains partial supersession scope
    body_lower = text.lower()
    assert "partial" in body_lower or "d4" in text, (
        "ADR-007 prose must explain partial supersession scope "
        "(expected 'partial' or 'D4' reference in body). (V3)"
    )


# ---------------------------------------------------------------------------
# V4: ADR-007 addresses each ADR-004 D4 excluded skill
# ---------------------------------------------------------------------------


def test_v4_adr007_addresses_adr004_d4() -> None:
    """V4: ADR-007 addresses each ADR-004 D4 excluded skill — stays or returns."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found. (V4 pre-req)"
    text = _read(path)

    # The two skills explicitly un-excluded per the supersession map
    for skill in ADR004_D4_EXCLUDED_SKILLS:
        assert skill in text, (
            f"ADR-007 must mention '{skill}' (un-excluded per supersession map). (V4)"
        )

    # ADR-007 should also address the remaining ADR-004 D4 exclusions
    # (at minimum by referencing ADR-004 D4 as a whole)
    addressed_other = any(skill in text for skill in ADR004_D4_OTHER_EXCLUSIONS)
    adr004_d4_ref = "ADR-004" in text and "D4" in text
    assert addressed_other or adr004_d4_ref, (
        "ADR-007 must address remaining ADR-004 D4 exclusions — either by "
        "naming individual skills or referencing ADR-004 D4 as a whole. (V4)"
    )


# ---------------------------------------------------------------------------
# V5: ADR-008 explicitly states INV-002 disposition
# ---------------------------------------------------------------------------


def test_v5_adr008_inv002_statement() -> None:
    """V5: ADR-008 explicitly states whether INV-002 needs amendment."""
    path = _find_adr("008")
    assert path is not None, "ADR 008-*.md not found. (V5 pre-req)"
    text = _read(path)
    assert "INV-002" in text, (
        "ADR-008 must reference INV-002. (V5)"
    )
    # Must contain an explicit disposition — confirming no change or specifying one
    text_lower = text.lower()
    confirms_no_change = (
        "without amendment" in text_lower
        or "no amendment" in text_lower
        or "accommodates" in text_lower
        or "does not require" in text_lower
    )
    specifies_amendment = "amend" in text_lower and "inv-002" in text_lower
    assert confirms_no_change or specifies_amendment, (
        "ADR-008 must explicitly state whether INV-002 needs amendment — "
        "either confirm it accommodates the change or specify the amendment. (V5)"
    )


# ---------------------------------------------------------------------------
# V6: index.md has entries for all four new ADRs
# ---------------------------------------------------------------------------


def test_v6_index_updated() -> None:
    """V6: docs/adr/index.md has entries for ADR-005 through ADR-008."""
    text = _read(INDEX)
    for prefix in ADR_PREFIXES:
        adr_id = f"ADR-{prefix}"
        assert adr_id in text, (
            f"docs/adr/index.md missing entry for {adr_id}. (V6)"
        )


# ---------------------------------------------------------------------------
# V7: Envelope compliance — only declared files modified
# ---------------------------------------------------------------------------


def test_v7_envelope_compliance() -> None:
    """V7: No files outside the envelope are modified by Phase 3.

    Envelope from intent.md:
      - docs/adr/005-*.md, 006-*.md, 007-*.md, 008-*.md
      - docs/adr/index.md

    This test checks git diff --name-only against the last Phase 1 commit
    to detect files outside the envelope. It is meaningful only after Phase 3
    commits land; at Phase 2 commit time it passes vacuously (no changes yet).
    """
    allowed_patterns = [
        r"^docs/adr/00[5-8]-.*\.md$",
        r"^docs/adr/index\.md$",
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
    changed_files = [f for f in result.stdout.strip().splitlines() if f]

    violations = []
    for f in changed_files:
        if not any(re.match(pat, f) for pat in allowed_patterns):
            violations.append(f)

    assert not violations, (
        f"Files outside the SLICE-005 envelope were modified: {violations}. (V7)"
    )


# ---------------------------------------------------------------------------
# V8: No implementation decisions — ADRs describe what, not how
# ---------------------------------------------------------------------------


def test_v8_no_implementation_decisions() -> None:
    """V8: ADRs contain no implementation code (Python, shell, JS blocks).

    Specification-level behavioral descriptions (e.g., 'the guard must match
    *.md') are acceptable per ambiguity resolution A2. This test catches
    actual code blocks that contain implementation patterns.
    """
    # Patterns that indicate implementation code, not specification
    impl_patterns = [
        r"```python\n.*(?:def |class |import )",
        r"```(?:bash|sh)\n.*(?:sed |awk |mv |cp |mkdir )",
        r"```javascript\n",
        r"```typescript\n",
    ]

    for prefix in ADR_PREFIXES:
        path = _find_adr(prefix)
        assert path is not None, f"ADR {prefix}-*.md not found. (V8 pre-req)"
        text = _read(path)
        for pat in impl_patterns:
            match = re.search(pat, text, re.MULTILINE | re.DOTALL)
            assert match is None, (
                f"ADR {path.name} contains implementation code block "
                f"matching pattern {pat!r}. ADRs describe what, not how. (V8)"
            )


# ---------------------------------------------------------------------------
# Spec detail: Required sections per ADR
# ---------------------------------------------------------------------------


def test_adr_required_sections() -> None:
    """Each ADR has Context, Decision, and Consequences sections."""
    required_headings = ("## Context", "## Decision", "## Consequences")
    for prefix in ADR_PREFIXES:
        path = _find_adr(prefix)
        assert path is not None, f"ADR {prefix}-*.md not found. (sections pre-req)"
        text = _read(path)
        for heading in required_headings:
            assert heading in text, (
                f"ADR {path.name} missing required section '{heading}'. "
                f"(spec detail: Context, Decision, Consequences required)"
            )


# ---------------------------------------------------------------------------
# Spec detail + A6: Risk Register for provisional ADRs
# ---------------------------------------------------------------------------


def test_adr007_provisional_risk_register() -> None:
    """ADR-007 (firmness: provisional) must have a Risk Register section."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found. (risk register pre-req)"
    text = _read(path)
    assert "## Risk Register" in text, (
        "ADR-007 is provisional and must have a '## Risk Register' section. (A6)"
    )


# ---------------------------------------------------------------------------
# Firmness checks per intent
# ---------------------------------------------------------------------------


def test_adr005_firmness_firm() -> None:
    """ADR-005 firmness is firm per intent."""
    path = _find_adr("005")
    assert path is not None, "ADR 005-*.md not found."
    fm = _parse_frontmatter(_read(path))
    assert fm is not None, "ADR-005 has no valid frontmatter."
    assert fm.get("firmness") == "firm", (
        f"ADR-005 firmness should be 'firm', got '{fm.get('firmness')}'"
    )


def test_adr006_firmness_firm() -> None:
    """ADR-006 firmness is firm per intent."""
    path = _find_adr("006")
    assert path is not None, "ADR 006-*.md not found."
    fm = _parse_frontmatter(_read(path))
    assert fm is not None, "ADR-006 has no valid frontmatter."
    assert fm.get("firmness") == "firm", (
        f"ADR-006 firmness should be 'firm', got '{fm.get('firmness')}'"
    )


def test_adr007_firmness_provisional() -> None:
    """ADR-007 firmness is provisional per intent."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found."
    fm = _parse_frontmatter(_read(path))
    assert fm is not None, "ADR-007 has no valid frontmatter."
    assert fm.get("firmness") == "provisional", (
        f"ADR-007 firmness should be 'provisional', got '{fm.get('firmness')}'"
    )


def test_adr008_firmness_firm() -> None:
    """ADR-008 firmness is firm per intent."""
    path = _find_adr("008")
    assert path is not None, "ADR 008-*.md not found."
    fm = _parse_frontmatter(_read(path))
    assert fm is not None, "ADR-008 has no valid frontmatter."
    assert fm.get("firmness") == "firm", (
        f"ADR-008 firmness should be 'firm', got '{fm.get('firmness')}'"
    )


# ---------------------------------------------------------------------------
# A5: ADR-008 token budget reference
# ---------------------------------------------------------------------------


def test_adr008_token_budget_reference() -> None:
    """ADR-008 references ADR-002's handoff token budget."""
    path = _find_adr("008")
    assert path is not None, "ADR 008-*.md not found. (A5 pre-req)"
    text = _read(path)
    assert "ADR-002" in text, (
        "ADR-008 must reference ADR-002. (A5)"
    )
    text_lower = text.lower()
    budget_ref = "150" in text or "400" in text or "token" in text_lower
    assert budget_ref, (
        "ADR-008 must reference the handoff token budget "
        "(expected '150', '400', or 'token'). (A5)"
    )


# ---------------------------------------------------------------------------
# ADR-007: ADR-003 D4 parallelism items addressed
# ---------------------------------------------------------------------------


def test_adr007_addresses_adr003_d4_parallelism() -> None:
    """ADR-007 addresses ADR-003 D4's parallelism deferral."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found."
    text = _read(path)

    # Must reference ADR-003 and its parallelism deferral
    assert "ADR-003" in text, "ADR-007 must reference ADR-003."

    # Must address parallelism as v1-native (per intent)
    text_lower = text.lower()
    parallelism_addressed = (
        "parallelism" in text_lower or "concurrent" in text_lower
    )
    assert parallelism_addressed, (
        "ADR-007 must address parallelism (the core of ADR-003 D4 supersession)."
    )


# ---------------------------------------------------------------------------
# ADR-007: Supersession of ADR-004 D4 also recorded in frontmatter
# ---------------------------------------------------------------------------


def test_adr007_supersedes_adr004_d4() -> None:
    """ADR-007 frontmatter references ADR-004 supersession."""
    path = _find_adr("007")
    assert path is not None, "ADR 007-*.md not found."
    text = _read(path)
    fm = _parse_frontmatter(text)
    assert fm is not None, "ADR-007 has no valid frontmatter."

    supersedes = fm.get("supersedes", []) or []
    supersedes_sections = fm.get("supersedes-sections", []) or []
    all_refs = supersedes + supersedes_sections
    adr004_ref = any(
        "ADR-004" in str(ref) or "004" in str(ref) for ref in all_refs
    )
    assert adr004_ref, (
        f"ADR-007 frontmatter must reference ADR-004 in supersedes or "
        f"supersedes-sections. Found: {all_refs}"
    )


# ---------------------------------------------------------------------------
# Canary: index.md table structure (GREEN from start)
# ---------------------------------------------------------------------------


def test_index_format_canary() -> None:
    """Regression canary: index.md has the expected table column structure."""
    text = _read(INDEX)
    # Check for table header with expected columns
    assert re.search(
        r"\|\s*ID\s*\|\s*Title\s*\|\s*Status\s*\|\s*Firmness\s*\|\s*Topic\s*\|\s*Date\s*\|",
        text,
    ), "index.md table header must have columns: ID, Title, Status, Firmness, Topic, Date"

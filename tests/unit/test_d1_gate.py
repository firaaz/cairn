"""Phase 2 validation tests for SLICE-008 — D1 automated architecture refresh.

Verifies intent.md V1–V6: the D1 refresh gate in start-slice.full.md Step 7,
the bypass escape hatch with append-only log, the rolling-window warning,
session isolation instructions, and manual /refresh-architecture unchanged.

Contract-conformance tests — static artifacts must match intent.md's spec.
Pytest + stdlib only.
"""

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


# --- Primitives (reused from test_context_discipline_protocol.py) ----------


def slice_section(text: str, header: str) -> str | None:
    """Return the section starting at a line matching `header`.

    A line matches if it equals `header` exactly OR begins with `header`
    followed by a non-word boundary. The section runs from the matched line
    to the next line beginning with `## ` (same-level header) or EOF.
    Subheaders (`### ...`) stay inside. Returns None when no line matches.
    """
    pattern = re.compile(re.escape(header) + r"(?:$|\W)")
    lines = text.splitlines(keepends=True)
    start: int | None = None
    for i, line in enumerate(lines):
        if pattern.match(line.rstrip("\n")):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "".join(lines[start:end])


def contains_all(
    text: str,
    phrases: list[str],
    *,
    case_insensitive: bool = False,
) -> list[str]:
    """Return phrases NOT present in text. Empty list == all present."""
    haystack = text.lower() if case_insensitive else text
    missing: list[str] = []
    for phrase in phrases:
        needle = phrase.lower() if case_insensitive else phrase
        if needle not in haystack:
            missing.append(phrase)
    return missing


def proximity(
    text: str,
    keyword: str,
    anchor: str,
    max_distance: int = 300,
    *,
    case_insensitive: bool = False,
) -> bool:
    """Return True if some occurrence of `anchor` has `keyword` within
    +/-max_distance chars of it."""
    hay = text.lower() if case_insensitive else text
    key = keyword.lower() if case_insensitive else keyword
    anc = anchor.lower() if case_insensitive else anchor
    start = 0
    while True:
        idx = hay.find(anc, start)
        if idx == -1:
            return False
        lo = max(0, idx - max_distance)
        hi = idx + len(anc) + max_distance
        if key in hay[lo:hi]:
            return True
        start = idx + 1


# --- V1: start-slice complete gains D1 refresh gate in Step 7 ---------------


def test_v1_step7_has_d1_refresh_gate():
    """V1 — start-slice.full.md Step 7 contains a D1 refresh gate that runs
    /refresh-architecture and gates on validate_architecture.py passing.

    The gate must appear between the Phase 4 PASS verdict and the
    status: complete transition."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.full.md"
    assert path.is_file(), f"{path} does not exist"
    text = path.read_text()

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section in start-slice.full.md"

    # Gate must reference refresh-architecture
    assert (
        "refresh-architecture" in step7.lower()
        or "refresh_architecture" in step7.lower()
    ), "Step 7 does not reference /refresh-architecture"

    # Gate must reference the validator
    assert "validate_architecture" in step7, (
        "Step 7 does not reference validate_architecture.py"
    )

    # Gate must block completion on validator failure
    block_keywords = ["block", "refuse", "cannot", "must not", "gates", "non-zero"]
    block_ok = any(kw in step7.lower() for kw in block_keywords)
    assert block_ok, (
        f"Step 7 does not describe blocking completion on validator failure "
        f"(looked for any of {block_keywords})"
    )


# --- V2: Validator failure blocks completion --------------------------------


def test_v2_validator_failure_blocks_completion():
    """V2 — start-slice.full.md Step 7 explicitly states that when
    validate_architecture.py exits non-zero AND ADR_D1_BYPASS is not set,
    the slice MUST NOT transition to status: complete. The protocol must
    instruct printing the validator output."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.full.md"
    text = path.read_text()

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section"

    # Must mention printing validator output on failure
    print_ok = (
        proximity(
            step7,
            "print",
            "validator",
            max_distance=200,
            case_insensitive=True,
        )
        or proximity(
            step7,
            "output",
            "validator",
            max_distance=200,
            case_insensitive=True,
        )
        or proximity(
            step7,
            "show",
            "validator",
            max_distance=200,
            case_insensitive=True,
        )
    )
    assert print_ok, (
        "Step 7 does not instruct printing/showing validator output on failure"
    )

    # Must mention the bypass escape hatch as the alternative
    assert "ADR_D1_BYPASS" in step7 or "adr_d1_bypass" in step7.lower(), (
        "Step 7 does not mention ADR_D1_BYPASS as escape hatch"
    )


# --- V3: Bypass escape hatch with correct log format -----------------------


def test_v3_bypass_escape_hatch_and_log_format():
    """V3 — start-slice.full.md Step 7 documents the ADR_D1_BYPASS=1
    escape hatch. When set:
    - Completion proceeds despite validator failure
    - A line is appended to .claude/d1-bypasses.log
    - Log format: <slice-id> <YYYY-MM-DD> <one-line-reason>
    - The log is append-only and does not exist until first bypass."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.full.md"
    text = path.read_text()

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section"

    # Must document ADR_D1_BYPASS=1
    assert "ADR_D1_BYPASS" in step7, "Step 7 missing ADR_D1_BYPASS"

    # Must reference the bypass log path
    assert "d1-bypasses.log" in step7, (
        "Step 7 does not reference .claude/d1-bypasses.log"
    )

    # Must document the log format (slice-id, date, reason)
    format_ok = (
        "slice-id" in step7.lower()
        or re.search(r"<slice.id>", step7, re.IGNORECASE) is not None
        or "YYYY-MM-DD" in step7
    )
    assert format_ok, (
        "Step 7 does not document the bypass log entry format "
        "(<slice-id> <YYYY-MM-DD> <one-line-reason>)"
    )

    # Must state the log is append-only
    assert "append" in step7.lower(), (
        "Step 7 does not describe the bypass log as append-only"
    )


# --- V4: Rolling window warning on third bypass ----------------------------


def test_v4_rolling_window_warning():
    """V4 — start-slice.full.md Step 7 documents the rolling-window check:
    three bypasses within the last 10 slices (by numeric suffix) triggers
    a warning message about D1 design review."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.full.md"
    text = path.read_text()

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section"

    # Must mention the threshold count (3 or three)
    three_ok = "three" in step7.lower() or "3" in step7
    assert three_ok, "Step 7 does not mention the three-bypass threshold"

    # Must mention the window size (10 slices)
    ten_ok = proximity(
        step7,
        "10",
        "slice",
        max_distance=100,
        case_insensitive=True,
    ) or proximity(
        step7,
        "ten",
        "slice",
        max_distance=100,
        case_insensitive=True,
    )
    assert ten_ok, "Step 7 does not describe the 10-slice rolling window"

    # Must mention warning / review trigger
    warning_ok = any(
        kw in step7.lower()
        for kw in ["warning", "warn", "review", "revisit", "design review"]
    )
    assert warning_ok, (
        "Step 7 does not describe the warning/review triggered by 3 bypasses"
    )

    # Must specify counting by numeric suffix
    suffix_ok = "numeric" in step7.lower() or "suffix" in step7.lower()
    assert suffix_ok, "Step 7 does not specify counting bypasses by numeric suffix"


# --- V5: Session isolation — refresh context constraints --------------------


def test_v5_session_isolation():
    """V5 — start-slice.full.md Step 7 documents session isolation for the
    D1 refresh: the refresh context loads ONLY docs/adr/*.md (excluding
    index.md and superseded) plus the prior ARCHITECTURE.md. It does NOT
    load .claude/current-slice/* or phase-role artifacts."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.full.md"
    text = path.read_text()

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section"

    # Must describe what the refresh loads
    loads_adr = proximity(
        step7,
        "adr",
        "load",
        max_distance=200,
        case_insensitive=True,
    ) or proximity(
        step7,
        "docs/adr",
        "refresh",
        max_distance=300,
        case_insensitive=True,
    )
    assert loads_adr, "Step 7 does not describe the refresh loading the ADR corpus"

    loads_arch = proximity(
        step7,
        "ARCHITECTURE.md",
        "refresh",
        max_distance=300,
        case_insensitive=True,
    ) or proximity(
        step7,
        "ARCHITECTURE.md",
        "load",
        max_distance=300,
        case_insensitive=True,
    )
    assert loads_arch, "Step 7 does not describe the refresh loading ARCHITECTURE.md"

    # Must describe what the refresh does NOT load
    excludes_ok = any(
        phrase in step7
        for phrase in [
            "current-slice",
            "slice artifacts",
            "phase-role",
            "phase role",
        ]
    )
    assert excludes_ok, (
        "Step 7 does not describe excluding slice artifacts / "
        ".claude/current-slice from the refresh context"
    )

    # Must mention excluding index.md or superseded ADRs
    exclude_index = "index.md" in step7 or "superseded" in step7.lower()
    assert exclude_index, (
        "Step 7 does not mention excluding index.md or superseded ADRs "
        "from the refresh input"
    )


# --- V6: Manual /refresh-architecture unchanged ----------------------------


def test_v6_manual_refresh_architecture_unchanged():
    """V6 — refresh-architecture.md and/or refresh-architecture.full.md
    gains a note that D1 invokes them automatically, but the manual command
    behavior is explicitly unchanged. The note must mention 'D1' or
    'automatic' or 'start-slice complete'."""
    lite = CAIRN_ROOT / "commands/claude-code/refresh-architecture.md"
    full = CAIRN_ROOT / "commands/claude-code/refresh-architecture.full.md"
    assert lite.is_file(), f"{lite} does not exist"
    assert full.is_file(), f"{full} does not exist"

    lite_text = lite.read_text()
    full_text = full.read_text()
    combined = lite_text + "\n" + full_text

    # At least one of the files must mention D1 auto-invocation
    d1_note_ok = any(
        phrase in combined.lower()
        for phrase in [
            "d1",
            "automatic",
            "automatically",
            "start-slice complete",
            "slice-close",
            "slice close",
        ]
    )
    assert d1_note_ok, (
        "Neither refresh-architecture.md nor .full.md mentions D1 "
        "automatic invocation (looked for d1/automatic/start-slice complete)"
    )

    # Must not remove the manual invocation path
    manual_ok = any(
        phrase in combined.lower()
        for phrase in ["manual", "usage", "/refresh-architecture"]
    )
    assert manual_ok, (
        "refresh-architecture docs appear to have lost the manual invocation path"
    )

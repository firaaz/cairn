"""Phase 2 validation tests for d3-bypasses.log schema (ADR d3-bypass-classification).

Schema-driven (not count-driven): tolerates append-only growth while pinning
migration anchors byte-identically.

- >=4 lines; migration anchors SLICE-012/014/016/017 are a permanent floor
- every line matches the classified `<slice> <date> <class>[ (<letter>)]: <reason>` regex
- first four lines are classified `pre-existing` (migration-anchor contract)
- id-suffixes and dates are both monotonically non-decreasing (chronological order)
- SLICE-012/014/016 reasons and SLICE-017 full line are byte-identical to pre-migration pins
- exactly one trailing newline

Pytest + stdlib only.
"""

import re
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
LOG = CAIRN_ROOT / ".claude" / "d3-bypasses.log"

CLASSIFIED_LINE_RE = re.compile(
    r"^(?:SLICE-\d+|[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*) \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive)(?: \([A-D]\))?: .+$"
)

SLICE_012_REASON = (
    "ruff lint (E741, E402) in test_feature_cross_index.py and "
    "test_invariant_assertions.py — outside envelope"
)
SLICE_014_REASON = (
    "fleet-coordinator-design.md drift from parallel session (designing "
    "the automation for multi-slice work this slice's gates are catching)"
)
SLICE_016_REASON = (
    "INV-004 turn-1 token budget failure — CC 2.1.107 → 2.1.110 drift, "
    "slice envelope does not load at session start; re-baseline queued "
    "as housekeeping"
)

SLICE_017_LINE = (
    "SLICE-017 2026-04-16 pre-existing: snapshot_diff flags "
    "docs/adr/d3-bypass-classification.md (new), docs/adr/index.md, "
    "docs/lessons.md — all last-touched before phase-1 commit d65e50c; "
    "baseline refresh deferred to next integration sweep"
)


def _read_log() -> str:
    return LOG.read_text(encoding="utf-8")


def _lines() -> list[str]:
    content = _read_log()
    if content.endswith("\n"):
        return content.rstrip("\n").split("\n")
    return content.split("\n")


def test_log_file_exists():
    assert LOG.exists(), f"{LOG} must exist"


def test_log_has_at_least_four_lines():
    lines = _lines()
    assert len(lines) >= 4, (
        f"expected >=4 lines (migration-anchor floor), got {len(lines)}"
    )


def test_every_line_matches_classified_regex():
    for i, line in enumerate(_lines()):
        assert CLASSIFIED_LINE_RE.match(line), (
            f"line {i + 1} does not match classified format: {line!r}"
        )


def test_first_four_lines_classified_pre_existing():
    lines = _lines()
    for i, line in enumerate(lines[:4]):
        m = CLASSIFIED_LINE_RE.match(line)
        assert m, f"migration-anchor line {i + 1} does not match regex: {line!r}"
        assert m.group(1) == "pre-existing", (
            f"migration-anchor line {i + 1} class is {m.group(1)!r}, expected 'pre-existing'"
        )


def test_line_order_is_chronological():
    lines = _lines()
    ids = [line.split(" ", 1)[0] for line in lines]
    assert ids[:4] == ["SLICE-012", "SLICE-014", "SLICE-016", "SLICE-017"], (
        f"first four ids must match migration anchors, got {ids[:4]}"
    )
    numeric_ids = [id_ for id_ in ids if id_.startswith("SLICE-")]
    suffixes = [int(id_.split("-")[1]) for id_ in numeric_ids]
    for i in range(len(suffixes) - 1):
        assert suffixes[i] <= suffixes[i + 1], (
            f"SLICE-NNN suffix not non-decreasing at position {i + 1}: {suffixes}"
        )
    dates = [line.split(" ")[1] for line in lines]
    for i in range(len(dates) - 1):
        assert dates[i] <= dates[i + 1], (
            f"date not non-decreasing at line {i + 2}: {dates}"
        )


def test_slice_012_reason_preserved():
    line = _lines()[0]
    assert line.startswith("SLICE-012 2026-04-14 pre-existing: ")
    reason = line[len("SLICE-012 2026-04-14 pre-existing: ") :]
    assert reason == SLICE_012_REASON


def test_slice_014_reason_preserved():
    line = _lines()[1]
    assert line.startswith("SLICE-014 2026-04-15 pre-existing: ")
    reason = line[len("SLICE-014 2026-04-15 pre-existing: ") :]
    assert reason == SLICE_014_REASON


def test_slice_016_reason_preserved():
    line = _lines()[2]
    assert line.startswith("SLICE-016 2026-04-16 pre-existing: ")
    reason = line[len("SLICE-016 2026-04-16 pre-existing: ") :]
    assert reason == SLICE_016_REASON


def test_slice_017_line_byte_identical():
    assert _lines()[3] == SLICE_017_LINE


def test_trailing_newline_exactly_one():
    content = _read_log()
    assert content.endswith("\n")
    assert not content.endswith("\n\n")


@pytest.mark.parametrize(
    "line,expected_match",
    [
        ("SLICE-020 2026-04-17 pre-existing: reason text", True),
        ("SLICE-018 2026-04-16 slice-caused (A): reason text", True),
        ("SLICE-018 2026-04-16 slice-caused(A): reason text", False),
        ("SLICE-018 2026-04-16 slice-caused (AC): reason text", False),
        ("SLICE-018 2026-04-16 bogus-class: reason text", False),
    ],
    ids=[
        "no-qualifier",
        "with-qualifier",
        "missing-space",
        "multi-letter",
        "bogus-class",
    ],
)
def test_classified_line_regex_schema(line: str, expected_match: bool):
    match = CLASSIFIED_LINE_RE.match(line)
    assert bool(match) == expected_match, (
        f"regex match={bool(match)} for line {line!r}, expected {expected_match}"
    )


SUBSTRATE_ORCHESTRATOR_PATHS_LINE_18 = (
    "substrate/orchestrator-paths 2026-04-30 pre-existing: "
    "integration_gate fails on 4 pre-existing kuzu MCP tests "
    "(issue #25 scope); invariant+ruff PASS"
)

SUBSTRATE_ORCHESTRATOR_PATHS_LINE_19 = (
    "substrate/orchestrator-paths 2026-04-30 pre-existing: "
    "snapshot baseline 2026-04-30T00:37 is many slices stale; "
    "reported new files are pre-existing housekeeping outside slice envelope"
)


def test_line_18_substrate_orchestrator_paths_pre_existing_pin():
    """Intent S1: line 18 backfilled with `pre-existing:` token, reason text byte-identical."""
    lines = _lines()
    assert len(lines) >= 18, f"expected >=18 lines, got {len(lines)}"
    assert lines[17] == SUBSTRATE_ORCHESTRATOR_PATHS_LINE_18, (
        f"line 18 mismatch:\n  expected: {SUBSTRATE_ORCHESTRATOR_PATHS_LINE_18!r}\n"
        f"  actual:   {lines[17]!r}"
    )


def test_line_19_substrate_orchestrator_paths_pre_existing_pin():
    """Intent S2: line 19 backfilled with `pre-existing:` token, reason text byte-identical."""
    lines = _lines()
    assert len(lines) >= 19, f"expected >=19 lines, got {len(lines)}"
    assert lines[18] == SUBSTRATE_ORCHESTRATOR_PATHS_LINE_19, (
        f"line 19 mismatch:\n  expected: {SUBSTRATE_ORCHESTRATOR_PATHS_LINE_19!r}\n"
        f"  actual:   {lines[18]!r}"
    )


def test_lines_18_and_19_classified_pre_existing_via_regex():
    """Intent S5: post-backfill, lines 18 and 19 carry the `pre-existing` class token explicitly.

    Parallel to test_first_four_lines_classified_pre_existing (migration-anchor pin)
    so silent reclassification of the substrate/orchestrator-paths entries
    (e.g. to `slice-caused` or `false-positive`) is caught by name, not just
    by the schema regex.
    """
    lines = _lines()
    assert len(lines) >= 19, f"expected >=19 lines, got {len(lines)}"
    for idx in (17, 18):
        line = lines[idx]
        m = CLASSIFIED_LINE_RE.match(line)
        assert m, f"line {idx + 1} does not match regex: {line!r}"
        assert line.startswith("substrate/orchestrator-paths 2026-04-30 "), (
            f"line {idx + 1} id/date prefix changed: {line!r}"
        )
        assert m.group(1) == "pre-existing", (
            f"line {idx + 1} class is {m.group(1)!r}, expected 'pre-existing'"
        )

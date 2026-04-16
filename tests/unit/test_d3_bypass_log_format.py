"""Phase 2 validation tests for SLICE-018 — d3-bypasses.log one-time
reclassification (ADR d3-bypass-classification, Decision 1).

Asserts the post-migration shape of .claude/d3-bypasses.log:
- 4 lines, chronological SLICE-012/014/016/017 order
- every line matches the classified <slice> <date> <class>: <reason> regex
- all four lines classified `pre-existing`
- the three migrated reason substrings are byte-identical to the pins
  in intent.md's Specification Detail table
- SLICE-017's line is byte-identical to its pre-migration content
- exactly one trailing newline

Pytest + stdlib only.
"""

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
LOG = CAIRN_ROOT / ".claude" / "d3-bypasses.log"

CLASSIFIED_LINE_RE = re.compile(
    r"^SLICE-\d+ \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive): .+$"
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


def test_log_has_exactly_four_lines():
    assert len(_lines()) == 4


def test_every_line_matches_classified_regex():
    for i, line in enumerate(_lines()):
        assert CLASSIFIED_LINE_RE.match(line), (
            f"line {i + 1} does not match classified format: {line!r}"
        )


def test_all_lines_classified_pre_existing():
    counts = {"slice-caused": 0, "pre-existing": 0, "false-positive": 0}
    for line in _lines():
        m = CLASSIFIED_LINE_RE.match(line)
        assert m, f"line does not match regex: {line!r}"
        counts[m.group(1)] += 1
    assert counts == {"slice-caused": 0, "pre-existing": 4, "false-positive": 0}


def test_line_order_is_chronological():
    ids = [line.split(" ", 1)[0] for line in _lines()]
    assert ids == ["SLICE-012", "SLICE-014", "SLICE-016", "SLICE-017"]


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

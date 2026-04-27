"""Phase 2 RED — V4 of compression/slice-1-foundation intent.md.

Asserts `_parse_structured_tail` accepts pretty-printed / multi-line JSON
objects at the end of child stdout. Scans backward from the last line's
closing brace, walks upward until braces balance, joins and parses
(intent.md:62).

Single-line fallback (current behavior) is retained.

RED at Phase 2: the current implementation is line-oriented and returns
None on multi-line tails (see scripts/slice_orchestrator.py _parse_structured_tail).
"""

from __future__ import annotations


def test_v4_multiline_pretty_printed_tail_parses():
    """intent.md:73 — newlines inside the tail object must not defeat the parser."""
    import slice_orchestrator as so

    stdout = (
        "some preamble\n"
        "more preamble\n"
        "{\n"
        '  "status": "OK",\n'
        '  "commit_hash": "abc1234",\n'
        '  "summary": "phase 1 done"\n'
        "}\n"
    )
    obj = so._parse_structured_tail(stdout)
    assert obj is not None, (
        "Multi-line JSON tail must parse; got None. "
        "Implementation must scan backward from closing `}` and walk until braces balance."
    )
    assert obj == {
        "status": "OK",
        "commit_hash": "abc1234",
        "summary": "phase 1 done",
    }


def test_v4_multiline_tail_with_trailing_blank_lines():
    """Trailing whitespace/blank lines after the closing brace must not confuse scan."""
    import slice_orchestrator as so

    stdout = (
        "log line\n"
        "{\n"
        '  "status": "RAISE_ISSUE",\n'
        '  "commit_hash": "deadbee",\n'
        '  "summary": "ambiguity in V1"\n'
        "}\n"
        "\n"
        "   \n"
    )
    obj = so._parse_structured_tail(stdout)
    assert obj is not None
    assert obj["status"] == "RAISE_ISSUE"
    assert obj["commit_hash"] == "deadbee"


def test_v4_multiline_tail_with_nested_object():
    """Balanced nested braces must still resolve to the outer object."""
    import slice_orchestrator as so

    stdout = (
        "noise\n"
        "{\n"
        '  "status": "OK",\n'
        '  "meta": {\n'
        '    "phase": 2,\n'
        '    "nested": {"k": "v"}\n'
        "  },\n"
        '  "summary": "done"\n'
        "}\n"
    )
    obj = so._parse_structured_tail(stdout)
    assert obj is not None
    assert obj["status"] == "OK"
    assert obj["meta"]["phase"] == 2
    assert obj["meta"]["nested"] == {"k": "v"}


def test_v4_single_line_fallback_preserved():
    """intent.md:62 — 'single-line fallback is preserved'."""
    import slice_orchestrator as so

    stdout = 'preamble\n{"status": "OK", "commit_hash": "abc", "summary": "x"}\n'
    obj = so._parse_structured_tail(stdout)
    assert obj == {"status": "OK", "commit_hash": "abc", "summary": "x"}


def test_v4_no_json_tail_returns_none():
    """Non-JSON trailing content must still return None (not raise)."""
    import slice_orchestrator as so

    assert so._parse_structured_tail("plain text\nno braces here\n") is None
    assert so._parse_structured_tail("") is None


def test_v4_malformed_multiline_brace_returns_none():
    """Unbalanced braces at EOF → None (no crash)."""
    import slice_orchestrator as so

    stdout = 'log\n{\n  "status": "OK",\n  "summary": "x"\n'  # missing closing brace
    assert so._parse_structured_tail(stdout) is None

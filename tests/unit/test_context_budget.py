"""Phase 2 validation tests for SLICE-003 — context budget (INV-004).

Live measurement: spawns a CC session with "hi" in cairn root, reads
turn-1 token count from session JSONL, asserts ≤30k. Records CC version
and measurement delta. Skips if `claude` CLI is not on PATH.

Pytest + stdlib only.
"""

import json
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
BUDGET_HARD = 30_000
BUDGET_ASPIRATIONAL = 25_000
D1_BASELINE = 27_314
MEASUREMENT_FILE = (
    CAIRN_ROOT / "docs" / "plans" / "measurements" / "2026-04-12-slice-003.txt"
)


def _claude_available() -> bool:
    try:
        subprocess.run(
            ["claude", "--version"], capture_output=True, timeout=10, check=True
        )
        return True
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
    ):
        return False


def _claude_version() -> str:
    r = subprocess.run(
        ["claude", "--version"], capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip()


def _run_and_measure() -> tuple[int, str]:
    """Run `claude -p "hi"` in cairn root, return (turn1_tokens, cc_version).

    Token formula per intent.md:
      input_tokens + cache_creation_input_tokens + cache_read_input_tokens
    from the first assistant response in session JSONL.
    """
    version = _claude_version()

    result = subprocess.run(
        ["claude", "-p", "hi", "--output-format", "stream-json"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(CAIRN_ROOT),
    )
    if result.returncode != 0:
        pytest.fail(
            f"claude -p hi failed (rc={result.returncode}): {result.stderr[:500]}"
        )

    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        usage = entry.get("usage")
        if not usage:
            usage = entry.get("result", {}).get("usage")
        if usage and "input_tokens" in usage:
            tokens = (
                usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
            )
            return tokens, version

    pytest.fail("No token usage found in claude JSONL output")


def _record_measurement(tokens: int, version: str) -> None:
    MEASUREMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    delta = tokens - D1_BASELINE
    pct = delta / D1_BASELINE * 100
    MEASUREMENT_FILE.write_text(
        f"CC version: {version}\n"
        f"Turn-1 tokens: {tokens}\n"
        f"D1 baseline: {D1_BASELINE}\n"
        f"Delta: {delta:+d} ({pct:+.1f}%)\n"
        f"Hard budget ({BUDGET_HARD}): {'PASS' if tokens <= BUDGET_HARD else 'FAIL'}\n"
        f"Aspirational ({BUDGET_ASPIRATIONAL}): "
        f"{'PASS' if tokens <= BUDGET_ASPIRATIONAL else 'MISS'}\n"
    )


@pytest.mark.skipif(not _claude_available(), reason="claude CLI not on PATH")
def test_inv004_turn1_token_budget():
    """INV-004 — turn-1 total context ≤30,000 tokens on a fresh 'hi' session."""
    tokens, version = _run_and_measure()
    _record_measurement(tokens, version)

    assert tokens <= BUDGET_HARD, (
        f"INV-004 FAIL: {tokens} tokens > {BUDGET_HARD} budget. "
        f"D1 baseline: {D1_BASELINE}, delta: {tokens - D1_BASELINE:+d}. "
        f"Aspirational ({BUDGET_ASPIRATIONAL}): "
        f"{'PASS' if tokens <= BUDGET_ASPIRATIONAL else 'MISS'}. "
        f"CC: {version}"
    )


def test_inv004_architecture_rebaselined():
    """INV-004 paragraph in ARCHITECTURE.md reflects the `housekeeping/inv004-rebaseline` re-baseline.

    Isolates the paragraph starting at ``**INV-004**`` and ending at the first
    subsequent blank line, then asserts the re-baselined ceiling and provenance
    citations are present while the stale ``≤22,000`` literal is gone.

    Independent of the ``claude`` CLI; runs unconditionally.
    """
    arch = (CAIRN_ROOT / "docs" / "ARCHITECTURE.md").read_text()
    lines = arch.splitlines()

    start = next(
        (i for i, line in enumerate(lines) if line.startswith("**INV-004**")),
        None,
    )
    assert start is not None, "INV-004 marker not found in docs/ARCHITECTURE.md"

    end = next(
        (
            i
            for i, line in enumerate(lines[start + 1 :], start=start + 1)
            if line.strip() == ""
        ),
        len(lines),
    )
    paragraph = "\n".join(lines[start:end])

    assert "≤30,000 total tokens" in paragraph, (
        f"INV-004 missing re-baselined ceiling '≤30,000 total tokens'.\n"
        f"Paragraph: {paragraph!r}"
    )
    assert "≤22,000" not in paragraph, (
        f"INV-004 still contains stale '≤22,000' literal.\nParagraph: {paragraph!r}"
    )
    assert "housekeeping/inv004-rebaseline" in paragraph, (
        f"INV-004 missing 'housekeeping/inv004-rebaseline' provenance citation.\nParagraph: {paragraph!r}"
    )
    assert "2.1.110" in paragraph, (
        f"INV-004 missing '2.1.110' provenance citation.\nParagraph: {paragraph!r}"
    )


def test_inv004_invariant_check_block_description_rebaselined():
    """INV-004 invariant-check block description points at the 30k budget.

    Isolates the fenced ``invariant-check INV-004`` block in ARCHITECTURE.md
    and asserts its body names the re-baselined ceiling ("30k token budget"),
    not the stale ("22k token budget"). Block-scoped so unrelated occurrences
    of "22k" elsewhere in ARCHITECTURE.md cannot mask drift here.
    """
    arch = (CAIRN_ROOT / "docs" / "ARCHITECTURE.md").read_text()
    lines = arch.splitlines()

    start = next(
        (
            i
            for i, line in enumerate(lines)
            if line.strip() == "```invariant-check INV-004"
        ),
        None,
    )
    assert start is not None, (
        "invariant-check INV-004 opening fence not found in docs/ARCHITECTURE.md"
    )

    end = next(
        (
            i
            for i, line in enumerate(lines[start + 1 :], start=start + 1)
            if line.strip() == "```"
        ),
        None,
    )
    assert end is not None, (
        "invariant-check INV-004 closing fence not found in docs/ARCHITECTURE.md"
    )
    block = "\n".join(lines[start : end + 1])

    assert "machine-checks the 30k token budget" in block, (
        "INV-004 invariant-check block missing re-baselined description "
        "'machine-checks the 30k token budget'.\n"
        f"Block: {block!r}"
    )
    assert "machine-checks the 22k token budget" not in block, (
        "INV-004 invariant-check block still contains stale description "
        "'machine-checks the 22k token budget'.\n"
        f"Block: {block!r}"
    )


def test_inv004_turn1_token_budget_docstring_rebaselined():
    """test_inv004_turn1_token_budget docstring reflects the 30,000 ceiling.

    Text-level scan of test_context_budget.py (not __doc__ attribute) to avoid
    importing the module, which would trigger the `claude` CLI skip fixture.
    Locates the ``def test_inv004_turn1_token_budget`` line and inspects the
    first non-blank line after it — that is, the function's docstring.
    """
    src = Path(__file__).read_text()
    lines = src.splitlines()

    def_index = next(
        (
            i
            for i, line in enumerate(lines)
            if line.lstrip().startswith("def test_inv004_turn1_token_budget(")
        ),
        None,
    )
    assert def_index is not None, (
        "def test_inv004_turn1_token_budget(...) not found in this file"
    )

    docstring_line = next(
        (line for line in lines[def_index + 1 :] if line.strip() != ""),
        None,
    )
    assert docstring_line is not None, (
        "no non-blank line after def test_inv004_turn1_token_budget"
    )

    assert "\u226430,000 tokens" in docstring_line, (
        "test_inv004_turn1_token_budget docstring missing re-baselined "
        "'\u226430,000 tokens' ceiling.\n"
        f"Docstring line: {docstring_line!r}"
    )
    assert "\u226422,000 tokens" not in docstring_line, (
        "test_inv004_turn1_token_budget docstring still contains stale "
        "'\u226422,000 tokens' literal.\n"
        f"Docstring line: {docstring_line!r}"
    )


def test_inv004_regression_guards_preserved():
    """Three regression-guard lines in test_inv004_architecture_rebaselined stay.

    These lines intentionally contain the stale ``\u226422,000`` literal as a
    regression assertion / failure-message / docstring clause. A future cleanup
    pass might remove them under the mistaken belief they are drift; this test
    pins them so that mistake breaks the suite loudly.

    Guardrail test — expected to pass today and keep passing. If it fails at
    slice entry, the slice's premise is wrong.
    """
    src = Path(__file__).read_text()

    required = [
        "the stale ``\u226422,000`` literal is gone",
        'assert "\u226422,000" not in paragraph',
        "INV-004 still contains stale '\u226422,000' literal",
    ]

    missing = [s for s in required if s not in src]
    assert not missing, (
        "Regression-guard substring(s) removed from test_inv004_architecture_"
        f"rebaselined: {missing!r}. These lines intentionally carry the stale "
        "'\u226422,000' literal to guard against its return to ARCHITECTURE.md — "
        "restore them verbatim."
    )

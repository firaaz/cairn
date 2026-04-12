"""Phase 2 validation tests for SLICE-003 — context budget (INV-004).

Live measurement: spawns a CC session with "hi" in cairn root, reads
turn-1 token count from session JSONL, asserts ≤22k. Records CC version
and measurement delta. Skips if `claude` CLI is not on PATH.

Pytest + stdlib only.
"""

import json
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
BUDGET_HARD = 22_000
BUDGET_ASPIRATIONAL = 20_000
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
    """INV-004 — turn-1 total context ≤22,000 tokens on a fresh 'hi' session."""
    tokens, version = _run_and_measure()
    _record_measurement(tokens, version)

    assert tokens <= BUDGET_HARD, (
        f"INV-004 FAIL: {tokens} tokens > {BUDGET_HARD} budget. "
        f"D1 baseline: {D1_BASELINE}, delta: {tokens - D1_BASELINE:+d}. "
        f"Aspirational ({BUDGET_ASPIRATIONAL}): "
        f"{'PASS' if tokens <= BUDGET_ASPIRATIONAL else 'MISS'}. "
        f"CC: {version}"
    )

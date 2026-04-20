"""Phase 2 RED — compression/slice-2-state-machine §B8.

FAILED classification + exponential backoff:

 - transient (returncode in {124}, OR stderr contains any of
   `rate limit`, `overloaded`, `429`, `503`, case-insensitive):
   retry up to CAIRN_FAILED_TRANSIENT_MAX_RETRIES (default 3) with
   `time.sleep(1 * 4**attempt)` → 1s, 4s, 16s (sum 21s).
 - malformed (_parse_structured_tail returned None): retry once.
 - logic (agent self-reported FAILED with parseable tail): retry once.

Each retry is logged with `{attempt, classification, backoff_s}`.

Expected at Phase 2: FAILS — no classification + backoff exists.
"""

from __future__ import annotations

import re


def _setup(monkeypatch, tmp_path):
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        'id: demo/b8\nname: "demo/b8"\nstatus: in-progress\n'
        'current_phase: 1\nbrief: "b"\n'
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/b8\nphase: 1-intent\nenvelope: []\n---\n"
    )
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    debug_dir = tmp_path / ".claude" / "orchestrator-debug"
    monkeypatch.setattr(so, "DEBUG_DIR", debug_dir, raising=False)
    return so, debug_dir


def test_b8_transient_rate_limit_triggers_three_exponential_retries(
    monkeypatch, tmp_path
):
    so, debug_dir = _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("CAIRN_FAILED_TRANSIENT_MAX_RETRIES", "3")

    sleeps: list[float] = []
    monkeypatch.setattr(so.time, "sleep", lambda s: sleeps.append(s))

    call_count = {"n": 0}

    def fake_dispatch_inner(*args, **kwargs):
        # Always returns a transient-flavoured FAILED.
        call_count["n"] += 1
        return {
            "status": "FAILED",
            "commit_hash": "",
            "summary": "rate limit exceeded",
            "stderr": "Error: rate limit exceeded (429)",
            "returncode": 1,
        }

    # Patch the internal single-attempt dispatch path. Two common names —
    # try them all; test will surface whichever the implementation uses.
    for name in (
        "_dispatch_phase_agent_once",
        "_dispatch_once",
        "_run_with_live_stderr",
    ):
        if hasattr(so, name):
            monkeypatch.setattr(so, name, fake_dispatch_inner)

    # Fallback: also stub the full dispatch_phase_agent *inner* mechanism by
    # patching Popen/run to emit rate-limit stderr. Implementation-specific;
    # Phase 3 is expected to route the stubbed inner through classification.

    # The top-level call must return FAILED after exhausting retries.
    result = so.dispatch_phase_agent(
        "phase-1-writer", {"phase": 1, "role": "phase-1-writer", "slice_id": "s"}
    )
    assert result.get("status") == "FAILED"

    # The sum of slept durations MUST equal 1+4+16 = 21s (with some tolerance).
    total = sum(sleeps)
    assert 21 <= total <= 30, (
        f"expected transient retry sleeps to sum to ~21s (1+4+16); "
        f"got {sleeps!r} total={total}"
    )
    assert len(sleeps) == 3, (
        f"expected exactly 3 backoff sleeps; got {len(sleeps)}: {sleeps!r}"
    )


def test_b8_retry_attempts_logged_with_classification(monkeypatch, tmp_path):
    so, debug_dir = _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("CAIRN_FAILED_TRANSIENT_MAX_RETRIES", "3")
    monkeypatch.setattr(so.time, "sleep", lambda s: None)

    def fake_inner(*args, **kwargs):
        return {
            "status": "FAILED",
            "commit_hash": "",
            "summary": "rate limit",
            "stderr": "429 Too Many Requests",
            "returncode": 1,
        }

    for name in (
        "_dispatch_phase_agent_once",
        "_dispatch_once",
        "_run_with_live_stderr",
    ):
        if hasattr(so, name):
            monkeypatch.setattr(so, name, fake_inner)

    so.dispatch_phase_agent(
        "phase-1-writer", {"phase": 1, "role": "phase-1-writer", "slice_id": "s"}
    )

    bodies = "\n".join(p.read_text() for p in debug_dir.glob("*.log"))
    assert "transient" in bodies, (
        f"failure log must record classification=transient; bodies={bodies!r}"
    )
    assert re.search(r"attempt.{0,6}[123]", bodies), (
        f"failure log must record each attempt number; bodies={bodies!r}"
    )


def test_b8_malformed_tail_retries_exactly_once(monkeypatch, tmp_path):
    so, _ = _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(so.time, "sleep", lambda s: None)

    # _parse_structured_tail returning None → malformed classification.
    monkeypatch.setattr(so, "_parse_structured_tail", lambda stdout: None)

    call_count = {"n": 0}

    def fake_inner(*args, **kwargs):
        call_count["n"] += 1
        return {
            "status": "FAILED",
            "commit_hash": "",
            "summary": "garbled",
            "stderr": "",
            "returncode": 0,
            "stdout": "not a valid tail",
        }

    for name in (
        "_dispatch_phase_agent_once",
        "_dispatch_once",
        "_run_with_live_stderr",
    ):
        if hasattr(so, name):
            monkeypatch.setattr(so, name, fake_inner)

    so.dispatch_phase_agent(
        "phase-1-writer", {"phase": 1, "role": "phase-1-writer", "slice_id": "s"}
    )
    # 1 initial + 1 retry = 2.
    assert call_count["n"] == 2, (
        f"malformed → exactly one retry (2 total invocations); got {call_count!r}"
    )

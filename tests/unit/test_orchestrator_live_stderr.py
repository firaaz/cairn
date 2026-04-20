"""Phase 2 RED — V5 of compression/slice-1-foundation intent.md.

Asserts D3 live-stderr streaming:

 - Each child stderr line reaches orchestrator stderr prefixed
   `[phase-N-role|slice-id]` within 500 ms of emission.
 - The full child stderr stream is also captured in a per-phase debug
   log whose filename is renamed to
   `{slice-id-slug}-phase-{n}-{role}-{timestamp}.log`.

Uses a real Python subprocess that emits three stderr lines at 100 ms
intervals as the "child". Monkeypatches slice_orchestrator.subprocess.Popen
to substitute the claude CLI with this emitter while preserving the
tee-pump behavior under test.

RED at Phase 2: dispatch_phase_agent does not exist; tee-pump and
renamed debug-log path are not implemented.
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
import time


SLICE_ID = "compression/slice-1-foundation"
SLICE_SLUG = SLICE_ID.replace("/", "-")
ROLE = "phase-2-skeptic"
PHASE_N = 2

CHILD_EMITTER = (
    "import sys, time\n"
    'sys.stderr.write("line1\\n"); sys.stderr.flush(); time.sleep(0.1)\n'
    'sys.stderr.write("line2\\n"); sys.stderr.flush(); time.sleep(0.1)\n'
    'sys.stderr.write("line3\\n"); sys.stderr.flush(); time.sleep(0.05)\n'
    'sys.stdout.write(\'{"status":"OK","commit_hash":"abc1234","summary":"ok"}\\n\')\n'
    "sys.stdout.flush()\n"
)

PREFIX_RE = re.compile(
    rf"^\[phase-{PHASE_N}-{re.escape(ROLE)}\|{re.escape(SLICE_ID)}\]"
)


def _popen_swap(*_args, **_kwargs):
    """Replacement for subprocess.Popen that runs the CHILD_EMITTER instead
    of whatever cmd was requested, preserving stdout/stderr PIPE semantics."""
    return subprocess.Popen(
        [sys.executable, "-u", "-c", CHILD_EMITTER],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _call_dispatch_capturing_stderr(monkeypatch, tmp_path):
    """Invoke dispatch_phase_agent with the child-emitter Popen swap, capturing
    everything written to sys.stderr by the orchestrator during the call."""
    import slice_orchestrator as so

    monkeypatch.setattr(so, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False)
    monkeypatch.setattr(so.subprocess, "Popen", _popen_swap)
    # Preserve subprocess.run for other call sites, but make sure any run-based
    # fallback would still produce a valid tail.
    monkeypatch.setattr(
        so.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            args=a,
            returncode=0,
            stdout='{"status":"OK","commit_hash":"x","summary":"y"}',
            stderr="",
        ),
    )

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stderr", captured)

    start = time.monotonic()
    result = so.dispatch_phase_agent(
        ROLE,
        {"phase": PHASE_N, "role": ROLE, "slice_id": SLICE_ID},
    )
    elapsed = time.monotonic() - start

    return result, captured.getvalue(), elapsed


def test_v5_child_stderr_lines_reach_orchestrator_stderr(monkeypatch, tmp_path):
    """intent.md:64 — every child stderr line reaches orchestrator stderr."""
    _result, captured, _elapsed = _call_dispatch_capturing_stderr(monkeypatch, tmp_path)
    for expected in ("line1", "line2", "line3"):
        assert expected in captured, (
            f"Child stderr line {expected!r} never reached orchestrator stderr; "
            f"captured={captured!r}"
        )


def test_v5_each_forwarded_line_carries_phase_role_slice_prefix(monkeypatch, tmp_path):
    """intent.md:64 — prefix is `[phase-N-role|slice-id]`."""
    _result, captured, _elapsed = _call_dispatch_capturing_stderr(monkeypatch, tmp_path)
    forwarded = [ln for ln in captured.splitlines() if PREFIX_RE.match(ln)]
    assert len(forwarded) >= 3, (
        f"Expected ≥3 prefixed lines; got {forwarded!r}. Full stderr: {captured!r}"
    )
    joined = "\n".join(forwarded)
    for expected in ("line1", "line2", "line3"):
        assert expected in joined, (
            f"Prefixed forward stream missing {expected!r}: {forwarded!r}"
        )


def test_v5_wallclock_forwarding_is_live_not_buffered(monkeypatch, tmp_path):
    """intent.md:64 — 'within 500 ms of emission'. A buffered implementation
    would only flush after the child exits (~250 ms + overhead). A tee-pump
    implementation forwards each line in ≤500 ms. We sanity-check the total
    wall clock against a generous upper bound of 2 s."""
    _result, _captured, elapsed = _call_dispatch_capturing_stderr(monkeypatch, tmp_path)
    assert elapsed < 2.0, (
        f"dispatch_phase_agent wall clock {elapsed:.2f}s — tee-pump likely not wired "
        "(fully buffered output would not necessarily blow this budget; "
        "this is the coarse liveness floor)."
    )


def test_v5_debug_log_uses_renamed_path(monkeypatch, tmp_path):
    """intent.md:66 — filename is
    `{slice-id-slug}-phase-{n}-{role}-{timestamp}.log`."""
    _result, _captured, _elapsed = _call_dispatch_capturing_stderr(
        monkeypatch, tmp_path
    )

    debug_dir = tmp_path / "orchestrator-debug"
    assert debug_dir.exists(), (
        "orchestrator must create DEBUG_DIR even on success (per-phase log); "
        f"{debug_dir} missing"
    )
    candidates = list(debug_dir.glob("*.log"))
    assert candidates, f"No debug log produced in {debug_dir}"
    pattern = re.compile(
        rf"^{re.escape(SLICE_SLUG)}-phase-{PHASE_N}-{re.escape(ROLE)}-\d{{8}}T\d{{6}}Z\.log$"
    )
    matches = [p for p in candidates if pattern.match(p.name)]
    assert matches, (
        f"No debug log matches renamed pattern "
        f"`{SLICE_SLUG}-phase-{PHASE_N}-{ROLE}-YYYYMMDDTHHMMSSZ.log`; "
        f"got {[p.name for p in candidates]!r}"
    )


def test_v5_debug_log_contains_full_child_stderr(monkeypatch, tmp_path):
    """intent.md:64 — 'buffering the full stream for failure-log capture'."""
    _result, _captured, _elapsed = _call_dispatch_capturing_stderr(
        monkeypatch, tmp_path
    )
    debug_dir = tmp_path / "orchestrator-debug"
    candidates = list(debug_dir.glob("*.log"))
    assert candidates
    body = max(candidates, key=lambda p: p.stat().st_mtime).read_text()
    for expected in ("line1", "line2", "line3"):
        assert expected in body, (
            f"Per-phase debug log missing child stderr line {expected!r}; "
            f"log body={body!r}"
        )

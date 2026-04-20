"""Phase 2 RED — atexit / signal terminal writer (Observability D6, spec-design §Data Flow).

Spec: intent.md §Artifact inventory (`main` gains `_init_state_dict` +
heartbeat start + `atexit.register` + resume-reconcile path) and design
§Exit paths (`_final_persist_and_md` is the single terminal writer, invoked
from either `atexit` or `_clean_shutdown`).

Invariant under test: regardless of the exit path, the `<slug>-result.json`
written by the orchestrator's single terminal writer exists, is valid JSON,
and carries a status consistent with the exit scenario:

  - normal return 0 → status == "OK"
  - return 1 (FAILED path)  → status == "FAILED"
  - SIGTERM (B13 handler → atexit) → status == "SIGNALED"

Mechanism. Each test spawns a short-lived Python subprocess that imports
`slice_orchestrator` from the repo's `scripts/` dir, calls `_init_state_dict`
+ `_register_atexit_terminal_writer` (name per design doc), mutates state to
the exit-specific terminal, and exits. The parent then reads
`.claude/orchestrator-debug/<slug>-result.json` out of the subprocess'
temp-dir cwd and asserts the terminal contract.

Expected at Phase 2: every test FAILS because none of
`_init_state_dict`, `_register_atexit_terminal_writer`, `_final_persist_and_md`,
or the SIGNALED-status hook exists yet.
"""

from __future__ import annotations

import json
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = CAIRN_ROOT / "scripts"
SLICE_ID = "demo/sig-obs"
SLUG = "demo-sig-obs"


def _driver(body: str) -> str:
    """Render a tiny Python driver that loads slice_orchestrator and runs `body`.

    The driver runs with cwd=tmp_path so every orchestrator path anchors under
    the temp directory. All Phase-3 terminal-writer symbols are required to
    exist by name; if they do not, the subprocess fails with AttributeError
    and the test's final JSON assertion fails RED.
    """
    return textwrap.dedent(
        f"""
        import os, sys, signal, time
        sys.path.insert(0, {str(SCRIPTS_DIR)!r})
        os.makedirs(".claude/orchestrator-debug", exist_ok=True)
        os.makedirs(".claude/current-slice", exist_ok=True)
        import slice_orchestrator as so
        so._init_state_dict(slice_id={SLICE_ID!r})
        so._register_atexit_terminal_writer()
        so._register_signal_handlers()
        {body}
        """
    )


def _result_json(tmp_path: Path) -> dict:
    p = tmp_path / ".claude" / "orchestrator-debug" / f"{SLUG}-result.json"
    assert p.exists(), (
        f"terminal writer must have produced {p}; dir has "
        f"{[x.name for x in (tmp_path / '.claude' / 'orchestrator-debug').iterdir()] if (tmp_path / '.claude' / 'orchestrator-debug').exists() else 'no dir'}"
    )
    return json.loads(p.read_text())


def test_atexit_writes_final_state_on_normal_exit(tmp_path):
    body = textwrap.dedent(
        """
        so._update_state(status="OK", exit_code=0, ended_at="2026-04-20T16:00:00+00:00")
        sys.exit(0)
        """
    )
    rc = subprocess.call(
        [sys.executable, "-c", _driver(body)],
        cwd=tmp_path,
    )
    assert rc == 0, "normal-exit driver must exit 0"
    data = _result_json(tmp_path)
    assert data["status"] == "OK"
    assert data["exit_code"] == 0
    assert data["schema_version"] == "1.0"


def test_atexit_writes_final_state_on_failed_exit(tmp_path):
    body = textwrap.dedent(
        """
        so._update_state(status="FAILED", exit_code=1, ended_at="2026-04-20T16:05:00+00:00")
        sys.exit(1)
        """
    )
    rc = subprocess.call(
        [sys.executable, "-c", _driver(body)],
        cwd=tmp_path,
    )
    assert rc == 1, "failed-exit driver must propagate exit 1"
    data = _result_json(tmp_path)
    assert data["status"] == "FAILED"
    assert data["exit_code"] == 1


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX signals only")
def test_sigterm_writes_signaled_status_via_atexit(tmp_path):
    body = textwrap.dedent(
        """
        # Park until signalled; _clean_shutdown -> sys.exit(143) -> atexit fires.
        while True:
            time.sleep(0.05)
        """
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", _driver(body)],
        cwd=tmp_path,
    )
    try:
        # Give the subprocess time to install handlers.
        deadline = time.time() + 3.0
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.05)
        assert proc.poll() is None, "driver must still be running before SIGTERM"
        proc.send_signal(signal.SIGTERM)
        rc = proc.wait(timeout=5.0)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2.0)

    assert rc != 0, "SIGTERM path must not report success"
    data = _result_json(tmp_path)
    assert data["status"] == "SIGNALED", (
        f"SIGTERM path must yield status=SIGNALED; got {data.get('status')!r}"
    )
    assert data.get("exit_code") in (143, 130, None), (
        f"SIGNALED exit_code must be the signal convention; got {data.get('exit_code')!r}"
    )

"""Phase 2 RED — compression/slice-2-state-machine §B13.

SIGINT/SIGTERM handler:

 - Orchestrator entry registers `signal.signal(SIGINT, _clean_shutdown)` and
   `signal.signal(SIGTERM, _clean_shutdown)`.
 - On SIGTERM the active child is SIGTERMed; after
   `CAIRN_SHUTDOWN_GRACE_S` (default 5 s) it is SIGKILLed; process exits 143
   (SIGINT → 130).
 - `slice.yaml` remains well-formed YAML after shutdown.

Expected at Phase 2: FAILS — no signal handler wired.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


HARNESS = r"""
import os, sys, time
sys.path.insert(0, {scripts!r})
import slice_orchestrator as so

# Ensure the orchestrator uses our tmp slice yaml.
so.SLICE_YAML = __import__('pathlib').Path({slice_yaml!r})
so.DEBUG_DIR = __import__('pathlib').Path({debug_dir!r})

def _sleep_forever(*args, **kwargs):
    # Simulate a very long-running child phase agent.
    time.sleep(9999)

so.dispatch_phase_agent = _sleep_forever
# Advance into the loop; handler must be registered before dispatch.
try:
    so.run_phase_loop()
except SystemExit as e:
    raise
"""


def _setup_project(tmp_path: Path) -> Path:
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        'id: demo/sig\nname: "demo/sig"\nstatus: in-progress\n'
        'current_phase: 1\nbrief: "b"\n'
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/sig\nphase: 1-intent\nenvelope: []\n---\n"
    )
    return slice_dir


@pytest.mark.parametrize(
    "sig,expected_rc", [(signal.SIGTERM, 143), (signal.SIGINT, 130)]
)
def test_b13_signal_exits_with_conventional_code(tmp_path, sig, expected_rc):
    slice_dir = _setup_project(tmp_path)
    # slice_orchestrator lives at repo-root/scripts/
    repo_root = Path(__file__).resolve().parent.parent.parent
    harness = HARNESS.format(
        scripts=str(repo_root / "scripts"),
        slice_yaml=str(slice_dir / "slice.yaml"),
        debug_dir=str(tmp_path / ".claude" / "orchestrator-debug"),
    )
    env = {**os.environ, "CAIRN_SHUTDOWN_GRACE_S": "2"}
    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", harness],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
        env=env,
    )
    # Give the orchestrator a moment to register handlers and enter dispatch.
    time.sleep(1.0)
    proc.send_signal(sig)
    try:
        rc = proc.wait(timeout=6)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise AssertionError(
            f"orchestrator did not exit within 6 s of {sig!r}; handler likely missing"
        )
    assert rc == expected_rc, (
        f"signal {sig!r}: expected exit {expected_rc}, got {rc}; "
        f"stderr={proc.stderr.read().decode()!r}"
    )


def test_b13_slice_yaml_still_parses_after_sigterm(tmp_path):
    slice_dir = _setup_project(tmp_path)
    repo_root = Path(__file__).resolve().parent.parent.parent
    harness = HARNESS.format(
        scripts=str(repo_root / "scripts"),
        slice_yaml=str(slice_dir / "slice.yaml"),
        debug_dir=str(tmp_path / ".claude" / "orchestrator-debug"),
    )
    env = {**os.environ, "CAIRN_SHUTDOWN_GRACE_S": "2"}
    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", harness],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
        env=env,
    )
    time.sleep(1.0)
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=6)

    import yaml  # PyYAML is an accepted dep per intent.md §Serialization

    loaded = yaml.safe_load((slice_dir / "slice.yaml").read_text())
    assert isinstance(loaded, dict), (
        f"slice.yaml must still parse as a dict after SIGTERM; got {loaded!r}"
    )

"""Phase 2 RED — compression/slice-2-state-machine §B9.

`_run_with_live_stderr` captures `pre_dispatch_head = git rev-parse HEAD`
before Popen.start. On `subprocess.TimeoutExpired`, after killing the child,
it captures `post_head`; if they differ the failure log MUST include
`partial_commit`, `pre_dispatch_head`, and `timeout_s` keys with SHA values.

Expected at Phase 2: FAILS — no reconciliation keys on current log.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path



def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "seed.txt").write_text("seed")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            "seed",
        ],
        cwd=tmp_path,
        check=True,
    )


def test_b9_failure_log_records_partial_commit_after_timeout(monkeypatch, tmp_path):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )

    # Replace Popen with a fake that (a) makes a real git commit (so HEAD
    # changes), then (b) raises TimeoutExpired from .wait().
    real_run = subprocess.run

    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.pid = os.getpid()
            (tmp_path / "child-artifact.txt").write_text("child wrote this")
            real_run(
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
                cwd=tmp_path,
                check=True,
            )
            real_run(
                [
                    "git",
                    "-c",
                    "user.email=t@t",
                    "-c",
                    "user.name=t",
                    "commit",
                    "-q",
                    "-m",
                    "child partial",
                ],
                cwd=tmp_path,
                check=True,
            )
            self.stdout = _DummyStream()
            self.stderr = _DummyStream()
            self.returncode = None

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)

        def poll(self):
            return None

        def kill(self):
            self.returncode = -9

        def terminate(self):
            self.returncode = -15

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 1)

    class _DummyStream:
        def readline(self):
            return ""

        def read(self):
            return ""

        def close(self):
            pass

    monkeypatch.setattr(so.subprocess, "Popen", FakePopen)

    # Invoke dispatch_phase_agent with a short timeout; it should return
    # FAILED and emit a per-phase failure log containing B9 reconciliation keys.
    monkeypatch.setattr(so, "_resolve_timeout", lambda role, override: 1)

    result = so.dispatch_phase_agent(
        "phase-1-writer", {"phase": 1, "role": "phase-1-writer", "slice_id": "s"}
    )

    logs = list((tmp_path / ".claude" / "orchestrator-debug").glob("*.log"))
    assert logs, "expected a per-phase failure log after timeout"
    # Concatenate body of all produced logs; any of them may carry the JSON.
    bodies = "\n".join(p.read_text() for p in logs)

    for key in ("partial_commit", "pre_dispatch_head", "timeout_s"):
        assert key in bodies, (
            f"failure log missing required B9 key {key!r}; bodies={bodies!r}"
        )

    sha_matches = re.findall(r"[0-9a-f]{7,40}", bodies)
    assert len(sha_matches) >= 2, (
        f"expected two SHA values (pre + partial); got {sha_matches!r}"
    )

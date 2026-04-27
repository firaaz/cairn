"""Phase 2 RED — compression/slice-2-state-machine §B11.

Every git call site routes through `_git(*args, **kwargs)` which wraps
`subprocess.run([...], check=True, capture_output=True, text=True)`. On
`CalledProcessError`, the original stderr is re-attached to the exception
message. `commit_phase_handoff` MUST propagate the exception — no silent
swallow.

Expected at Phase 2: FAILS — `_git` does not exist.
"""

from __future__ import annotations

import subprocess

import pytest


def test_b11_git_helper_exists_and_raises_with_stderr(monkeypatch):
    import slice_orchestrator as so

    assert hasattr(so, "_git"), "slice_orchestrator must expose a `_git` helper"

    def fake_run(cmd, *args, **kwargs):
        # Simulate `git commit` failure with meaningful stderr.
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr="permission denied"
        )

    # _git MUST pass check=True, which makes a returncode=1 trip CalledProcessError.
    # Simulate that by raising CalledProcessError directly on any git call.
    def fake_run_check(cmd, *args, **kwargs):
        if kwargs.get("check") or True:
            raise subprocess.CalledProcessError(
                returncode=1, cmd=cmd, output="", stderr="permission denied"
            )

    monkeypatch.setattr(so.subprocess, "run", fake_run_check)

    with pytest.raises(subprocess.CalledProcessError) as exc:
        so._git("commit", "-m", "x")
    # Either __str__ or the args must carry the original stderr.
    combined = f"{exc.value!s}|{exc.value.stderr!r}|{getattr(exc.value, 'args', ())!r}"
    assert "permission denied" in combined, (
        f"_git must re-attach original stderr; got {combined!r}"
    )


def test_b11_commit_phase_handoff_propagates_git_failure(monkeypatch):
    import slice_orchestrator as so

    def boom(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd=cmd, output="", stderr="permission denied"
        )

    monkeypatch.setattr(so.subprocess, "run", boom)

    with pytest.raises(subprocess.CalledProcessError):
        so.commit_phase_handoff(phase=1, summary="s", commit_hash="abc1234")

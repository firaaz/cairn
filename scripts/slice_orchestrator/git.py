"""Git wrappers and HEAD-introspection helpers.

Single chokepoint per B11: every orchestrator git operation flows through
``_git`` so no call site silently advances on a failed git op. ``_git_head_safe``
and ``_head_subject_safe`` wrap that further with try/except for the resume-
reconciliation paths that must tolerate a fresh / corrupted repo.
"""

from __future__ import annotations

import subprocess


def _git(*args, **kwargs):
    """Run a git subcommand with check=True and re-attach stderr on failure.

    B11: single choke-point so no orchestrator call site silently advances on
    a failed git operation.
    """
    cmd = ["git", *args]
    kwargs.setdefault("check", True)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as exc:
        orig = exc.stderr or ""
        if orig:
            exc.args = (f"{exc.args[0] if exc.args else exc}: {orig}",)
        raise


def _git_head_safe():
    """Best-effort HEAD capture; empty string if git unavailable or no commits."""
    try:
        return _git("rev-parse", "HEAD").stdout.strip()
    except Exception:
        return ""


def _head_subject_safe():
    """Return ``HEAD``'s commit subject, or ``""`` on any git error."""
    try:
        proc = _git("log", "-1", "--format=%s")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    return (proc.stdout or "").strip()

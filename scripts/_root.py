"""Canonical project-root resolver — single source of truth for all path construction.

Contract (slice substrate/root-resolver intent §Specification):
  1. CLAUDE_PROJECT_DIR env var if set and non-empty → Path(value).resolve()
  2. git rev-parse --show-toplevel from os.getcwd() → Path(stdout).resolve()
  3. Raise RuntimeError naming both mechanisms.

Banned: file-relative parent chains for root inference. The
.slice-system → . symlink canonicalizes wrong in downstream consumers
(L-017). Use env var or git.

Tests under tests/ are exempt from this module's constraints.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def project_root() -> Path:
    """Resolve the canonical project root.

    Precedence:
      1. CLAUDE_PROJECT_DIR env var (if set and non-empty) — resolves relative paths.
      2. git rev-parse --show-toplevel from the current working directory.
      3. RuntimeError with an actionable message naming both mechanisms.
    """
    val = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if val:
        return Path(val).resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Cannot determine project root. "
            "Set CLAUDE_PROJECT_DIR to the project root, "
            "or run from inside a git repository "
            "(git rev-parse --show-toplevel must succeed). "
            f"Underlying error: {exc}"
        ) from exc

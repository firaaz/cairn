"""Canonical root resolvers — single source of truth for path construction.

Two distinct roots; do not conflate them:

  * project_root()  — where the *project's* state lives (the consumer's
    `.claude/`, the consumer's git tree). Resolves via CLAUDE_PROJECT_DIR
    or git toplevel from cwd. Used for: slice state, cairn_query DB output,
    project-specific config.

  * package_root()  — where the *cairn package's code* lives on disk.
    Always cairn's checkout, regardless of where launched. Resolves via
    `Path(__file__).resolve().parent.parent` (this file is `scripts/_root.py`,
    so `parent.parent` = cairn checkout). Used for: `sys.path` injection in
    subprocess MCP servers; reading cairn's own corpus (ADRs, lessons,
    spec, INV docs) which the MCP server serves to consumers regardless
    of which consumer launched it.

Contract for project_root() (slice substrate/root-resolver intent §Specification):
  1. CLAUDE_PROJECT_DIR env var if set and non-empty → Path(value).resolve()
  2. git rev-parse --show-toplevel from os.getcwd() → Path(stdout).resolve()
  3. Raise RuntimeError naming both mechanisms.

For project_root() specifically: file-relative parent chains for *project-root*
inference are banned. The .slice-system → . symlink canonicalizes wrong in
downstream consumers (L-017). Use env var or git.

For package_root(): file-relative parent chains are *required* — that's
exactly what package-location inference means.

Tests under tests/ are exempt from these constraints where they need
fixture-specific behavior.
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


def package_root() -> Path:
    """Resolve the cairn package root — where the code physically lives.

    Always returns the cairn checkout regardless of cwd or env vars. Use for
    reading cairn's own corpus (the markdown the MCP server serves to all
    consumers) and for ``sys.path`` injection in subprocess MCP servers.

    Do NOT use as a project_root() substitute — it loses the consumer-vs-cairn
    distinction that L-017 names as the path-drift failure mode.
    """
    return Path(__file__).resolve().parent.parent

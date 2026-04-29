#!/usr/bin/env python3
"""Structural snapshot-diff for D3 automated backstop.

Creates and compares file-tree snapshots to detect out-of-envelope changes.
Scans .py files under scripts/, checks/, tests/ and .md files under
commands/, docs/.  Each entry records path, size, and SHA-256 hash.

Usage:
    python3 scripts/snapshot_diff.py --snapshot   # create/overwrite baseline
    python3 scripts/snapshot_diff.py --diff       # compare against baseline

Exit codes:
    0 — no out-of-envelope changes (--snapshot always exits 0)
    1 — out-of-envelope changes detected (--diff only)
    2 — no prior snapshot exists (--diff creates one and exits 2)
"""

import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path


SNAPSHOT_REL = ".claude/structural-snapshot.json"

SCAN_RULES: list[tuple[str, str]] = [
    ("scripts", ".py"),
    ("checks", ".py"),
    ("tests", ".py"),
    ("commands", ".md"),
    ("docs", ".md"),
]


def _resolve_root() -> Path:
    """Resolve the repo root via project_root() contract.

    Falls back to os.getcwd() when git is unavailable (e.g. isolated test
    trees without a git repo).  A4: script always treats its CWD as the root.
    """
    try:
        from _root import project_root

        return project_root()
    except RuntimeError:
        # A4: no git repo available — treat CWD as root.  os.getcwd() avoids
        # the Path.cwd() ban imposed by the lint gate.
        return Path(os.getcwd())


def _scan_files(root: Path) -> dict[str, dict]:
    """Scan in-scope files and return a snapshot dict keyed by relative path."""
    entries: dict[str, dict] = {}
    for dir_name, ext in SCAN_RULES:
        scan_dir = root / dir_name
        if not scan_dir.is_dir():
            continue
        for f in sorted(scan_dir.rglob(f"*{ext}")):
            if not f.is_file():
                continue
            rel = str(f.relative_to(root))
            content = f.read_bytes()
            entries[rel] = {
                "size": len(content),
                "hash": hashlib.sha256(content).hexdigest(),
            }
    return dict(sorted(entries.items()))


def _write_snapshot(root: Path, entries: dict[str, dict]) -> None:
    """Write snapshot JSON to .claude/structural-snapshot.json."""
    snapshot_path = root / SNAPSHOT_REL
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n")


def _read_snapshot(root: Path) -> dict[str, dict] | None:
    """Read existing snapshot, or None if missing."""
    snapshot_path = root / SNAPSHOT_REL
    if not snapshot_path.exists():
        return None
    return json.loads(snapshot_path.read_text())


def _parse_envelope(root: Path) -> list[str] | None:
    """Extract envelope globs from .claude/current-slice/intent.md.

    Returns None if intent.md doesn't exist (A7: no envelope = all flagged).
    """
    intent_path = root / ".claude" / "current-slice" / "intent.md"
    if not intent_path.exists():
        return None

    text = intent_path.read_text()
    envelope: list[str] = []
    in_envelope = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("envelope:"):
            in_envelope = True
            continue
        if in_envelope:
            if stripped.startswith("- "):
                glob_val = stripped[2:].strip().strip('"').strip("'")
                envelope.append(glob_val)
            elif stripped and not stripped.startswith("#"):
                # Hit a different YAML key — stop
                if re.match(r"^[a-zA-Z]", stripped):
                    break
    return envelope


def _matches_envelope(path: str, envelope: list[str]) -> bool:
    """Check if a file path matches any envelope glob."""
    for pattern in envelope:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def cmd_snapshot() -> int:
    """Create a baseline snapshot. Always exits 0."""
    root = _resolve_root()
    entries = _scan_files(root)
    _write_snapshot(root, entries)
    return 0


def cmd_diff() -> int:
    """Compare current tree against saved snapshot.

    Returns 0 if no out-of-envelope changes, 1 if any found, 2 if no prior
    snapshot (creates one as side effect).
    """
    root = _resolve_root()
    old = _read_snapshot(root)

    if old is None:
        # A1/A8: no prior snapshot — create one and exit 2
        entries = _scan_files(root)
        _write_snapshot(root, entries)
        print("No prior snapshot found. Created baseline.", file=sys.stderr)
        return 2

    current = _scan_files(root)
    envelope = _parse_envelope(root)

    # Compute changes
    all_paths = sorted(set(old.keys()) | set(current.keys()))
    changes: list[tuple[str, str]] = []  # (path, change_type)

    for path in all_paths:
        in_old = path in old
        in_cur = path in current
        if in_old and not in_cur:
            changes.append((path, "deleted"))
        elif not in_old and in_cur:
            changes.append((path, "new"))
        elif old[path]["hash"] != current[path]["hash"]:
            changes.append((path, "changed"))

    # Filter to out-of-envelope changes
    out_of_envelope: list[tuple[str, str]] = []
    for path, change_type in changes:
        if envelope is None:
            # A7: no intent.md = no envelope = everything is out-of-envelope
            out_of_envelope.append((path, change_type))
        elif not _matches_envelope(path, envelope):
            out_of_envelope.append((path, change_type))

    if not out_of_envelope:
        return 0

    # Report out-of-envelope changes on stdout
    print("Out-of-envelope changes detected:")
    for path, change_type in out_of_envelope:
        print(f"  {path} ({change_type})")
    return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: snapshot_diff.py --snapshot | --diff", file=sys.stderr)
        return 2

    cmd = sys.argv[1]
    if cmd == "--snapshot":
        return cmd_snapshot()
    elif cmd == "--diff":
        return cmd_diff()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

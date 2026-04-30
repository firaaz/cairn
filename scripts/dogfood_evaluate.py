#!/usr/bin/env python3
"""Evaluate dogfood instrumentation log against cliff-failure-mode-and-v1-defenses gate criteria.

Reads docs/dogfood-log.md and git history, evaluates:
  1. Catch-rate: >=1 confirmed automated catch where manual would not have caught
  2. False-positive: no defense has >=3 confirmed false positives (muting threshold)
  3. Gate status: pass/fail/insufficient-data based on post-cliff-failure-mode-and-v1-defenses slice count

The post-cliff slice count is derived from git history: the number of
`^slice: .* — complete$` commits between the commit that introduced
docs/adr/cliff-failure-mode-and-v1-defenses.md (exclusive) and HEAD.

Exit codes:
    0 — pass
    1 — fail (FP threshold breached, unresolved unclear entries, or 10+ slices no catch)
    2 — insufficient data (< 10 post-cliff slices, missing log, or baseline ADR introducing-commit unresolvable)
"""

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from _root import project_root

REQUIRED_FIELDS = frozenset(
    {
        "slice",
        "date",
        "defense",
        "type",
        "description",
        "would-manual-have-caught",
        "disposition",
    }
)

AUTOMATED_DEFENSES = frozenset({"D1", "D2", "D3"})

FP_THRESHOLD = 3

SLICE_THRESHOLD = 10

ADR_BASELINE_PATH = "docs/adr/cliff-failure-mode-and-v1-defenses.md"

SLICE_COMPLETE_SUBJECT_RE = re.compile(r"^slice: .* — complete$")


def _resolve_project_root() -> Path:
    """Locate the project root via the canonical resolver.

    Delegates to scripts/_root.project_root (CLAUDE_PROJECT_DIR → git
    rev-parse). Exits 2 on failure to preserve behavioral parity.
    """
    try:
        return project_root()
    except (RuntimeError, FileNotFoundError):
        diagnostic = [
            "ERROR: cannot identify project root for dogfood evaluation.",
            "Mechanisms attempted:",
            "  - CLAUDE_PROJECT_DIR (unset or empty)",
            "  - git rev-parse --show-toplevel (failed or git not installed)",
            "Set CLAUDE_PROJECT_DIR to the project root, "
            "or invoke from inside a git repository.",
        ]
        print("\n".join(diagnostic), file=sys.stderr)
        sys.exit(2)


def _parse_simple_yaml(text: str) -> dict[str, str]:
    """Parse simple single-level key: value YAML. Stdlib only."""
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([^:]+):\s*(.*)$", line)
        if match:
            result[match.group(1).strip()] = match.group(2).strip()
    return result


def _find_baseline_commit(root: Path) -> str | None:
    """Locate the commit that introduced the cliff-failure-mode-and-v1-defenses ADR.

    Uses `git log --diff-filter=A -- <path>`; returns the oldest add-commit
    SHA (last line of default newest-first ordering), or None if the file
    has never been added on HEAD's history.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--format=%H",
                "--",
                ADR_BASELINE_PATH,
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]


def _count_slices_since(root: Path, baseline_sha: str) -> int:
    """Count `^slice: .* — complete$` commit subjects in baseline..HEAD."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=%s", f"{baseline_sha}..HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return 0

    return sum(
        1
        for line in result.stdout.splitlines()
        if SLICE_COMPLETE_SUBJECT_RE.match(line)
    )


def _read_dogfood_log(root: Path) -> list[dict[str, str]]:
    """Read docs/dogfood-log.md and return its fenced-yaml entries.

    The log frontmatter is no longer consulted for baseline info — git
    history is authoritative (intent §9 disposition C). Any stale
    `adr-003-landed-at-slice:` key is silently ignored.
    """
    path = root / "docs" / "dogfood-log.md"
    if not path.exists():
        return []

    content = path.read_text()

    entries = []
    for block in re.finditer(r"```yaml\n(.*?)```", content, re.DOTALL):
        entry = _parse_simple_yaml(block.group(1))
        entries.append(entry)
    return entries


def _validate_entry(entry: dict[str, str], index: int) -> bool:
    """Return True if entry has all required fields. Warns on stderr if not."""
    missing = REQUIRED_FIELDS - set(entry.keys())
    if missing:
        print(
            f"WARNING: skipping entry {index + 1} — "
            f"missing fields: {', '.join(sorted(missing))}",
            file=sys.stderr,
        )
        return False
    return True


def _check_duplicates(entries: list[dict[str, str]]) -> None:
    """Warn on stderr about duplicate entries (same slice+defense+date)."""
    seen: Counter[tuple[str, str, str]] = Counter()
    for entry in entries:
        key = (
            entry.get("slice", ""),
            entry.get("defense", ""),
            entry.get("date", ""),
        )
        seen[key] += 1
    for key, count in seen.items():
        if count > 1:
            print(
                f"WARNING: duplicate entries — slice={key[0]}, "
                f"defense={key[1]}, date={key[2]} appears {count} times",
                file=sys.stderr,
            )


def _evaluate(entries: list[dict[str, str]], post_adr_slices: int) -> int:
    """Run evaluation. Returns exit code (0/1/2)."""
    valid: list[dict[str, str]] = []
    for i, entry in enumerate(entries):
        if _validate_entry(entry, i):
            valid.append(entry)

    _check_duplicates(valid)

    fp_counts: Counter[str] = Counter()
    for entry in valid:
        if (
            entry.get("type") == "false-positive"
            and entry.get("disposition") == "confirmed"
        ):
            fp_counts[entry["defense"]] += 1

    fp_breached = any(count >= FP_THRESHOLD for count in fp_counts.values())

    has_unclear = any(
        entry.get("would-manual-have-caught") == "unclear" for entry in valid
    )

    has_catch = any(
        entry.get("defense") in AUTOMATED_DEFENSES
        and entry.get("type") == "catch"
        and entry.get("would-manual-have-caught") == "no"
        and entry.get("disposition") == "confirmed"
        for entry in valid
    )

    print(
        f"Dogfood evaluation — {post_adr_slices} post-cliff-failure-mode-and-v1-defenses slices"
    )
    print(f"  Entries: {len(valid)} valid, {len(entries) - len(valid)} skipped")
    print(f"  Automated catches (would-manual=no): {'yes' if has_catch else 'none'}")
    for defense in sorted(fp_counts):
        label = " (THRESHOLD BREACHED)" if fp_counts[defense] >= FP_THRESHOLD else ""
        print(f"  FP {defense}: {fp_counts[defense]}{label}")
    if has_unclear:
        print("  Unclear entries: present — resolution required")

    if fp_breached:
        print("FAIL: false-positive threshold breached")
        return 1

    if has_unclear:
        print("FAIL: unresolved unclear entries")
        return 1

    if has_catch:
        print("PASS")
        return 0

    if post_adr_slices >= SLICE_THRESHOLD:
        print(
            "FAIL: 10+ post-cliff-failure-mode-and-v1-defenses slices with no confirmed automated catch"
        )
        return 1

    print("INSUFFICIENT DATA: awaiting more slices or entries")
    return 2


def main() -> None:
    root = _resolve_project_root()

    baseline_sha = _find_baseline_commit(root)
    if baseline_sha is None:
        print(
            f"WARNING: cannot resolve baseline — commit introducing "
            f"{ADR_BASELINE_PATH} not found in git history. Dogfood evaluator "
            "needs this to establish the cliff-failure-mode-and-v1-defenses baseline.",
            file=sys.stderr,
        )
        print("INSUFFICIENT DATA: baseline ADR introducing-commit unresolvable")
        sys.exit(2)

    post_adr_slices = _count_slices_since(root, baseline_sha)
    entries = _read_dogfood_log(root)

    code = _evaluate(entries, post_adr_slices)
    sys.exit(code)


if __name__ == "__main__":
    main()

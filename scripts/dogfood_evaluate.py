#!/usr/bin/env python3
"""Evaluate dogfood instrumentation log against cliff-failure-mode-and-v1-defenses gate criteria.

Reads docs/dogfood-log.md and .claude/sweep.yaml, evaluates:
  1. Catch-rate: >=1 confirmed automated catch where manual would not have caught
  2. False-positive: no defense has >=3 confirmed false positives (muting threshold)
  3. Gate status: pass/fail/insufficient-data based on post-cliff-failure-mode-and-v1-defenses slice count

Exit codes:
    0 — pass
    1 — fail (FP threshold breached, unresolved unclear entries, or 10+ slices no catch)
    2 — insufficient data (< 10 post-cliff-failure-mode-and-v1-defenses slices, missing files)
"""

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

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


def _resolve_project_root() -> Path:
    """Locate the project root.

    Tried in order:
      1. CLAUDE_PROJECT_DIR environment variable
      2. git rev-parse --show-toplevel from cwd

    On failure, write diagnostic to stderr and exit 2.
    """
    attempted: list[str] = []

    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        return Path(env_dir)
    attempted.append("CLAUDE_PROJECT_DIR (unset)")

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = result.stdout.strip()
        if top:
            return Path(top)
        attempted.append("git rev-parse --show-toplevel (empty output)")
    except FileNotFoundError:
        attempted.append("git rev-parse --show-toplevel (git not installed)")
    except subprocess.CalledProcessError:
        attempted.append("git rev-parse --show-toplevel (not a git repository)")

    diagnostic = [
        "ERROR: cannot identify project root for dogfood evaluation.",
        "Mechanisms attempted:",
    ]
    diagnostic.extend(f"  - {item}" for item in attempted)
    diagnostic.append(
        "Set CLAUDE_PROJECT_DIR to the project root, "
        "or invoke from inside a git repository."
    )
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


def _read_sweep_yaml(root: Path) -> int | None:
    """Read current-slice-number from .claude/sweep.yaml."""
    path = root / ".claude" / "sweep.yaml"
    if not path.exists():
        return None
    data = _parse_simple_yaml(path.read_text())
    val = data.get("current-slice-number")
    if val is not None:
        return int(val)
    return None


def _read_dogfood_log(
    root: Path,
) -> tuple[int | None, list[dict[str, str]]]:
    """Read docs/dogfood-log.md.

    Returns (baseline, entries) where baseline is adr-003-landed-at-slice
    from frontmatter, and entries is a list of parsed entry dicts.
    Returns (None, []) if file is missing.
    """
    path = root / "docs" / "dogfood-log.md"
    if not path.exists():
        return None, []

    content = path.read_text()

    # Parse frontmatter between --- markers
    baseline = None
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = _parse_simple_yaml(fm_match.group(1))
        val = fm.get("adr-003-landed-at-slice")
        if val is not None:
            baseline = int(val)

    # Parse fenced yaml entry blocks
    entries = []
    for block in re.finditer(r"```yaml\n(.*?)```", content, re.DOTALL):
        entry = _parse_simple_yaml(block.group(1))
        entries.append(entry)

    return baseline, entries


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


def _evaluate(
    entries: list[dict[str, str]],
    baseline: int,
    current_slice_number: int,
) -> int:
    """Run evaluation. Returns exit code (0/1/2)."""
    post_adr003_slices = current_slice_number - baseline

    # Validate entries, keep only well-formed ones
    valid: list[dict[str, str]] = []
    for i, entry in enumerate(entries):
        if _validate_entry(entry, i):
            valid.append(entry)

    _check_duplicates(valid)

    # False-positive counts per defense
    fp_counts: Counter[str] = Counter()
    for entry in valid:
        if (
            entry.get("type") == "false-positive"
            and entry.get("disposition") == "confirmed"
        ):
            fp_counts[entry["defense"]] += 1

    fp_breached = any(count >= FP_THRESHOLD for count in fp_counts.values())

    # Unclear entries
    has_unclear = any(
        entry.get("would-manual-have-caught") == "unclear" for entry in valid
    )

    # Catch criterion: automated defense, confirmed catch, manual would not have caught
    has_catch = any(
        entry.get("defense") in AUTOMATED_DEFENSES
        and entry.get("type") == "catch"
        and entry.get("would-manual-have-caught") == "no"
        and entry.get("disposition") == "confirmed"
        for entry in valid
    )

    # Report
    print(f"Dogfood evaluation — {post_adr003_slices} post-cliff-failure-mode-and-v1-defenses slices")
    print(f"  Entries: {len(valid)} valid, {len(entries) - len(valid)} skipped")
    print(f"  Automated catches (would-manual=no): {'yes' if has_catch else 'none'}")
    for defense in sorted(fp_counts):
        label = " (THRESHOLD BREACHED)" if fp_counts[defense] >= FP_THRESHOLD else ""
        print(f"  FP {defense}: {fp_counts[defense]}{label}")
    if has_unclear:
        print("  Unclear entries: present — resolution required")

    # Verdict — priority order
    if fp_breached:
        print("FAIL: false-positive threshold breached")
        return 1

    if has_unclear:
        print("FAIL: unresolved unclear entries")
        return 1

    if has_catch:
        print("PASS")
        return 0

    if post_adr003_slices >= SLICE_THRESHOLD:
        print("FAIL: 10+ post-cliff-failure-mode-and-v1-defenses slices with no confirmed automated catch")
        return 1

    print("INSUFFICIENT DATA: awaiting more slices or entries")
    return 2


def main() -> None:
    root = _resolve_project_root()

    current_slice_number = _read_sweep_yaml(root)
    if current_slice_number is None:
        print(
            "ERROR: cannot read .claude/sweep.yaml or current-slice-number",
            file=sys.stderr,
        )
        sys.exit(2)

    baseline, entries = _read_dogfood_log(root)
    if baseline is None:
        print("Dogfood evaluation — no log or missing baseline")
        print("INSUFFICIENT DATA")
        sys.exit(2)

    code = _evaluate(entries, baseline, current_slice_number)
    sys.exit(code)


if __name__ == "__main__":
    main()

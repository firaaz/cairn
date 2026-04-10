#!/usr/bin/env python3
"""Validate consistency between ARCHITECTURE.md and ADR corpus.

Checks:
  A) Every ARCHITECTURE.md invariant references a valid, non-superseded ADR
  B) Every accepted firm ADR has at least one invariant in ARCHITECTURE.md
  C) No invariant references a superseded/deprecated ADR

Usage:
    uv run python scripts/validate_architecture.py

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
    2 — missing required files
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_FILE = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"
ADR_DIR = PROJECT_ROOT / "docs" / "adr"


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from a markdown file.

    Parses the block between the first pair of '---' delimiters.
    Returns a dict of key-value pairs (simple scalar values only).
    """
    if not text.startswith("---"):
        return {}

    end = text.find("---", 3)
    if end == -1:
        return {}

    frontmatter = {}
    for line in text[3:end].strip().splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Handle YAML lists like [INV-001, INV-002]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            value = [item.strip() for item in items if item.strip()]
        elif value == "null":
            value = None

        frontmatter[key] = value
    return frontmatter


def parse_invariants(text: str) -> list[dict]:
    """Extract invariants from the ## Invariants section of ARCHITECTURE.md.

    Expected format: **INV-NNN** <statement> (ADR-NNN, ADR-NNN)
    """
    invariants = []
    in_section = False
    for line_num, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("## Invariants"):
            in_section = True
            continue
        if in_section and line.strip().startswith("## "):
            break
        if in_section:
            # Match **INV-NNN** ... (ADR-NNN, ADR-NNN)
            inv_match = re.match(r"\*\*INV-(\d+)\*\*\s+(.+)", line)
            if inv_match:
                inv_num = int(inv_match.group(1))
                rest = inv_match.group(2)
                # Extract all ADR references
                adr_refs = [int(m) for m in re.findall(r"ADR-(\d+)", rest)]
                invariants.append(
                    {
                        "inv_num": inv_num,
                        "statement": rest,
                        "adr_refs": adr_refs,
                        "line": line_num,
                    }
                )
    return invariants


def parse_adr(filepath: Path) -> dict | None:
    """Parse an ADR file. Extract metadata from frontmatter."""
    text = filepath.read_text()

    frontmatter = parse_frontmatter(text)
    if not frontmatter:
        return None

    # Number from frontmatter id field (ADR-001 -> 1)
    adr_id = frontmatter.get("id", "")
    num_match = re.search(r"(\d+)", str(adr_id))
    adr_num = int(num_match.group(1)) if num_match else None

    if adr_num is None:
        return None

    # Title from first heading after frontmatter
    body = text[text.find("---", 3) + 3 :].strip()
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filepath.stem

    return {
        "num": adr_num,
        "title": title,
        "status": frontmatter.get("status", "unknown"),
        "firmness": frontmatter.get("firmness", "unknown"),
        "invariants_touched": frontmatter.get("invariants-touched", []),
        "path": str(filepath),
    }


def validate() -> list[str]:
    """Run all validation checks. Returns list of failure messages."""
    failures = []

    if not ARCHITECTURE_FILE.exists():
        return [
            "ARCHITECTURE.md not found at docs/ARCHITECTURE.md — run /refresh-architecture"
        ]

    if not ADR_DIR.exists():
        return [f"ADR directory not found at {ADR_DIR}"]

    arch_text = ARCHITECTURE_FILE.read_text()
    invariants = parse_invariants(arch_text)

    if not invariants:
        failures.append("No invariants found in ARCHITECTURE.md ## Invariants section")

    # Load all ADRs
    adr_files = sorted(ADR_DIR.glob("[0-9]*.md"))
    adrs: dict[int, dict] = {}
    for f in adr_files:
        adr = parse_adr(f)
        if adr is None:
            failures.append(
                f"Warning: {f.name} has no valid YAML frontmatter — skipped by all checks"
            )
            continue
        if adr["num"] in adrs:
            failures.append(
                f"Check A: Duplicate ADR number ADR-{adr['num']:03d} "
                f"in {adrs[adr['num']]['path']} and {adr['path']}"
            )
        adrs[adr["num"]] = adr

    if not adrs:
        failures.append(f"No ADR files with frontmatter found in {ADR_DIR}")
        return failures

    # Classify ADRs (case-insensitive status/firmness comparison)
    active_adrs = {
        n: a for n, a in adrs.items() if a["status"].lower() in ("accepted", "proposed")
    }
    inactive_adrs = {
        n: a
        for n, a in adrs.items()
        if a["status"].lower() in ("superseded", "deprecated", "retired")
    }
    firm_active = {
        n: a for n, a in active_adrs.items() if a["firmness"].lower() == "firm"
    }

    # Track which ADRs are referenced by invariants
    referenced_adrs: set[int] = set()

    # Check A: every invariant references valid, existing, non-superseded ADRs
    for inv in invariants:
        if not inv["adr_refs"]:
            failures.append(
                f"Check A: INV-{inv['inv_num']:03d} on line {inv['line']} has no ADR references"
            )
            continue

        for adr_num in inv["adr_refs"]:
            referenced_adrs.add(adr_num)
            if adr_num not in adrs:
                failures.append(
                    f"Check A: INV-{inv['inv_num']:03d} (line {inv['line']}) references "
                    f"ADR-{adr_num:03d} which does not exist"
                )
            elif adr_num in inactive_adrs:
                failures.append(
                    f"Check C: INV-{inv['inv_num']:03d} (line {inv['line']}) references "
                    f"ADR-{adr_num:03d} which is {adrs[adr_num]['status']}"
                )

    # Check B: every accepted firm ADR has at least one invariant referencing it
    for n, adr in firm_active.items():
        if n not in referenced_adrs:
            failures.append(
                f"Check B: ADR-{n:03d} ({adr['title']}) is firm/accepted "
                f"but has no invariant in ARCHITECTURE.md"
            )

    return failures


def main() -> None:
    print("Validating ARCHITECTURE.md against ADR corpus...\n")

    failures = validate()

    if not failures:
        arch_text = ARCHITECTURE_FILE.read_text()
        invariants = parse_invariants(arch_text)
        adr_files = sorted(ADR_DIR.glob("[0-9]*.md"))
        print("ALL CHECKS PASSED")
        print(f"  Invariants verified: {len(invariants)}")
        print(f"  ADR files checked: {len(adr_files)}")
        sys.exit(0)
    else:
        print(f"FAILED — {len(failures)} issue(s):\n")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()

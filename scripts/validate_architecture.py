#!/usr/bin/env python3
"""Validate consistency between ARCHITECTURE.md and ADR corpus.

Checks:
  A) Every ARCHITECTURE.md invariant references a valid, non-superseded ADR
  B) Every accepted firm ADR has at least one invariant in ARCHITECTURE.md
  C) No invariant references a superseded/deprecated ADR
  D) Per-invariant assertion execution (invariant-check blocks)
  E) Warning for invariants lacking machine-checkable assertions

Checks D/E run after A/B/C. A failure in A/B/C short-circuits before D runs.

Usage:
    uv run python scripts/validate_architecture.py

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
    2 — missing required files, or project root could not be resolved
"""

import re
import sys
from pathlib import Path

from _root import project_root


def _resolve_project_root() -> Path:
    """Locate the consumer project's repo root via the canonical resolver.

    Delegates to scripts/_root.project_root (CLAUDE_PROJECT_DIR → git
    rev-parse). Exits 2 on failure to preserve behavioral parity.
    """
    try:
        return project_root()
    except (RuntimeError, FileNotFoundError):
        diagnostic_lines = [
            "ERROR: cannot identify project root for architecture validation.",
            "Mechanisms attempted:",
            "  - CLAUDE_PROJECT_DIR (unset or empty)",
            "  - git rev-parse --show-toplevel (failed or git not installed)",
            "Set CLAUDE_PROJECT_DIR to the project root, "
            "or invoke from inside a git repository.",
        ]
        print("\n".join(diagnostic_lines), file=sys.stderr)
        sys.exit(2)


PROJECT_ROOT = _resolve_project_root()
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

    Expected format: **INV-NNN** <statement> (<ref>; <ref>; ...).

    References accepted are legacy `ADR-NNN` tokens and flat-slug tokens
    matching an ADR's frontmatter `id:`.
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
            inv_match = re.match(r"\*\*INV-(\d+)\*\*\s+(.+)", line)
            if inv_match:
                inv_num = int(inv_match.group(1))
                rest = inv_match.group(2)
                invariants.append(
                    {
                        "inv_num": inv_num,
                        "statement": rest,
                        "adr_refs": _extract_refs(rest),
                        "line": line_num,
                    }
                )
    return invariants


def _extract_refs(text: str) -> list[str]:
    """Extract ADR reference tokens from an invariant's text.

    Legacy `ADR-NNN` tokens are recognized anywhere in the text (preserves
    current tolerance for commentary like `confirmed by phase-pipeline-evaluation`). Flat-slug
    tokens are recognized only as top-level `;`/`,`-separated fragments
    inside the trailing parenthetical.
    """
    refs: list[str] = []
    seen: set[str] = set()

    for m in re.finditer(r"ADR-(\d+)", text):
        key = f"ADR-{int(m.group(1)):03d}"
        if key not in seen:
            seen.add(key)
            refs.append(key)

    paren_match = re.search(r"\(([^()]*)\)\s*$", text)
    if paren_match:
        for fragment in re.split(r"[;,]", paren_match.group(1)):
            token = fragment.strip()
            if (
                re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)+", token)
                and token not in seen
            ):
                seen.add(token)
                refs.append(token)

    return refs


def parse_assertion_blocks(text: str) -> dict[str, dict]:
    """Extract invariant-check fenced blocks from ARCHITECTURE.md.

    Returns dict mapping inv_id (e.g. "INV-001") to assertion dict with
    keys: type, pattern, target, expect, description.
    """
    blocks: dict[str, dict] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^```invariant-check\s+(INV-\d+)", line)
        if m:
            inv_id = m.group(1)
            assertion: dict[str, str] = {}
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                field_line = lines[i].strip()
                if ":" in field_line:
                    key, _, value = field_line.partition(":")
                    key = key.strip()
                    value = value.strip().strip('"')
                    assertion[key] = value
                i += 1
            blocks[inv_id] = assertion
        i += 1
    return blocks


def _run_grep_assertion(project_root: Path, inv_id: str, assertion: dict) -> str | None:
    """Run a grep assertion. Returns failure message or None on pass."""
    pattern = assertion.get("pattern", "")
    target = assertion.get("target", "")
    expect = assertion.get("expect", "match")

    target_files = sorted(project_root.glob(target))
    if not target_files:
        if expect == "match":
            return f"Check D: {inv_id} FAIL — no files matching '{target}'"
        return None

    found = False
    for f in target_files:
        try:
            content = f.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if re.search(pattern, content):
            found = True
            break

    if expect == "match" and not found:
        return (
            f"Check D: {inv_id} FAIL — pattern not found in {target}"
            f" (no match for '{pattern}')"
        )
    if expect == "no-match" and found:
        return (
            f"Check D: {inv_id} FAIL — pattern found in {target}"
            f" (expected no match for '{pattern}')"
        )
    return None


def _run_file_exists_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a file-exists assertion. Returns failure message or None on pass."""
    target = assertion.get("target", "")
    target_files = sorted(project_root.glob(target))
    if not target_files:
        return f"Check D: {inv_id} FAIL — no files matching '{target}'"
    return None


def _run_test_ref_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a test-ref assertion. Returns failure message or None on pass."""
    test_path = assertion.get("pattern", "")
    full_path = project_root / test_path
    if not full_path.exists():
        return f"Check D: {inv_id} FAIL — test file not found: {test_path}"
    return None


_ROLE_SHORTHAND_TO_SLUG: dict[str, str] = {
    "reader": "phase-1-writer",
    "skeptic": "phase-2-skeptic",
    "builder": "phase-3-implementer",
    "auditor": "phase-4-integrator",
}


def _extract_role_for_phase(core_text: str) -> set[tuple[int, str]] | None:
    """Parse ROLE_FOR_PHASE dict from core.py text."""
    in_dict = False
    result: set[tuple[int, str]] = set()
    for line in core_text.splitlines():
        stripped = line.strip()
        if re.match(r"ROLE_FOR_PHASE\s*=\s*\{", stripped):
            in_dict = True
            continue
        if in_dict:
            if stripped.startswith("}"):
                break
            m = re.match(r"(\d+)\s*:\s*\"(phase-\d+-[a-z][a-z-]*)\"", stripped)
            if m:
                result.add((int(m.group(1)), m.group(2)))
    return result if result else None


def _extract_skill_guide_topology(
    opref_text: str,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Extract (phase, role_slug) pairs from the Phase Skill Guide tables.

    Uses shorthand-to-slug mapping for the two tables and additionally
    verifies each derived slug appears somewhere in the full document
    (catches slug renaming outside the Skill Guide section itself).
    """
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    section_m = re.search(
        r"## Phase Skill Guide\b(.*?)(?=\n## |\Z)", opref_text, re.DOTALL
    )
    if not section_m:
        failures.append(
            "INV-003: Cannot find '## Phase Skill Guide' section in "
            "docs/operational-reference.md"
        )
        return result, failures

    section_text = section_m.group(1)
    row_pat = re.compile(
        r"^\|\s*(\d+)\.\s+[^|]+\|\s+\*{0,2}(\w+)\*{0,2}\s*\|", re.MULTILINE
    )
    for m in row_pat.finditer(section_text):
        phase_num = int(m.group(1))
        shorthand = m.group(2).lower()
        slug = _ROLE_SHORTHAND_TO_SLUG.get(shorthand)
        if slug:
            result.add((phase_num, slug))

    # Verify each derived slug appears in the full document.
    to_remove: set[tuple[int, str]] = set()
    for pair in result:
        _, slug = pair
        if slug not in opref_text:
            failures.append(
                f"INV-003: role slug '{slug}' not found anywhere in "
                f"docs/operational-reference.md (Phase Skill Guide)"
            )
            to_remove.add(pair)
    result -= to_remove

    return result, failures


def _extract_agent_file_topology(
    project_root: Path,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Parse (phase, role_slug) pairs from .claude/agents/phase-N-*.md filenames."""
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    agents_dir = project_root / ".claude" / "agents"
    if not agents_dir.exists():
        failures.append("INV-003: .claude/agents/ directory not found")
        return result, failures

    for f in sorted(agents_dir.glob("phase-*.md")):
        m = re.match(r"phase-(\d+)-(.+)\.md$", f.name)
        if m:
            phase_num = int(m.group(1))
            slug = f"phase-{m.group(1)}-{m.group(2)}"
            result.add((phase_num, slug))

    return result, failures


def _extract_role_guard_topology(
    guard_text: str,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Extract (phase, role_slug) topology from ROLE_DENY_READ in role_guard.py.

    Uses ROLE_DENY_READ as the binding source (all four roles must appear there).
    This tolerates the option-(b) asymmetry: phase-3-implementer has no static
    ROLE_POLICIES entry but IS present in ROLE_DENY_READ.
    """
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    in_deny_read = False
    for line in guard_text.splitlines():
        stripped = line.strip()
        if re.match(r"ROLE_DENY_READ\s*=\s*\{", stripped):
            in_deny_read = True
            continue
        if in_deny_read:
            if stripped == "}":
                break
            m = re.search(r'"(phase-(\d+)-[a-z][a-z-]*)"', stripped)
            if m:
                slug = m.group(1)
                phase_num = int(m.group(2))
                result.add((phase_num, slug))

    if not result:
        failures.append(
            "INV-003: Cannot parse ROLE_DENY_READ from checks/role_guard.py"
        )

    return result, failures


def validate_phase_topology(project_root: Path) -> list[str]:
    """Four-way cross-reference: (phase_ordinal, role_slug) topology must agree.

    Canonical sources:
      1. scripts/slice_orchestrator/core.py — ROLE_FOR_PHASE (authoritative).
      2. docs/operational-reference.md — Phase Skill Guide tables.
      3. .claude/agents/phase-N-*.md — agent prompt filenames.
      4. checks/role_guard.py — ROLE_DENY_READ keys.

    Option-(b) asymmetry: phase-3-implementer has no static ROLE_POLICIES entry;
    write-path gate is AGENT_ENVELOPE-driven per compression-infrastructure-bootstrap.
    The binding tolerates this because phase-3-implementer IS in ROLE_DENY_READ.

    Returns list of failure messages; empty on full agreement.
    """
    failures: list[str] = []

    core_path = project_root / "scripts" / "slice_orchestrator" / "core.py"
    if not core_path.exists():
        return [f"INV-003: {core_path} not found"]
    authoritative = _extract_role_for_phase(core_path.read_text())
    if authoritative is None:
        return [
            "INV-003: Cannot parse ROLE_FOR_PHASE from "
            "scripts/slice_orchestrator/core.py"
        ]

    opref_path = project_root / "docs" / "operational-reference.md"
    if not opref_path.exists():
        failures.append(f"INV-003: {opref_path} not found")
        skill_guide_topology: set[tuple[int, str]] = set()
    else:
        skill_guide_topology, src2_failures = _extract_skill_guide_topology(
            opref_path.read_text()
        )
        failures.extend(src2_failures)

    agent_topology, src3_failures = _extract_agent_file_topology(project_root)
    failures.extend(src3_failures)

    guard_path = project_root / "checks" / "role_guard.py"
    if not guard_path.exists():
        failures.append(f"INV-003: {guard_path} not found")
        guard_topology: set[tuple[int, str]] = set()
    else:
        guard_topology, src4_failures = _extract_role_guard_topology(
            guard_path.read_text()
        )
        failures.extend(src4_failures)

    if failures:
        return failures

    sources = [
        ("operational-reference.md (Phase Skill Guide)", skill_guide_topology),
        (".claude/agents/ filenames", agent_topology),
        ("checks/role_guard.py ROLE_DENY_READ", guard_topology),
    ]
    for source_name, topology in sources:
        for pair in authoritative:
            if pair not in topology:
                phase, role = pair
                failures.append(
                    f"INV-003: {source_name} is missing ({phase}, '{role}') "
                    f"— phase-topology drift vs ROLE_FOR_PHASE"
                )
        for pair in topology:
            if pair not in authoritative:
                phase, role = pair
                failures.append(
                    f"INV-003: {source_name} has extra ({phase}, '{role}') "
                    f"— phase-topology drift vs ROLE_FOR_PHASE"
                )

    return failures


def _run_phase_topology_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a phase-topology assertion. Returns failure message or None on pass."""
    topo_failures = validate_phase_topology(project_root)
    if topo_failures:
        return f"Check D: {inv_id} FAIL — phase-topology drift:\n  " + "\n  ".join(
            topo_failures
        )
    return None


def _run_assertion(project_root: Path, inv_id: str, assertion: dict) -> str | None:
    """Dispatch assertion execution by type. Returns failure message or None."""
    atype = assertion.get("type", "")
    if atype == "grep":
        return _run_grep_assertion(project_root, inv_id, assertion)
    if atype == "file-exists":
        return _run_file_exists_assertion(project_root, inv_id, assertion)
    if atype == "test-ref":
        return _run_test_ref_assertion(project_root, inv_id, assertion)
    if atype == "phase-topology":
        return _run_phase_topology_assertion(project_root, inv_id, assertion)
    return None


def parse_adr(filepath: Path) -> dict | None:
    """Parse an ADR file. Extract metadata from frontmatter.

    The canonical reference key is derived as follows:
      - If frontmatter `id` is `ADR-NNN`, the key is that id, zero-padded.
      - Else if frontmatter `id` is a kebab slug, the key is that slug verbatim.
      - Else the filename's leading digits yield a legacy `ADR-NNN` key.
    Files that match none of the above are skipped.
    """
    text = filepath.read_text()

    frontmatter = parse_frontmatter(text)
    if not frontmatter:
        return None

    key = _derive_adr_key(frontmatter, filepath)
    if key is None:
        return None

    body = text[text.find("---", 3) + 3 :].strip()
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filepath.stem

    return {
        "key": key,
        "title": title,
        "status": frontmatter.get("status", "unknown"),
        "firmness": frontmatter.get("firmness", "unknown"),
        "superseded_by": frontmatter.get("superseded-by"),
        "invariants_touched": frontmatter.get("invariants-touched", []),
        "path": str(filepath),
    }


def _derive_adr_key(frontmatter: dict, filepath: Path) -> str | None:
    """Derive the canonical ADR key (ADR-NNN or flat slug) or None."""
    raw_id = str(frontmatter.get("id", "")).strip()
    if raw_id:
        numeric = re.fullmatch(r"ADR-(\d+)", raw_id)
        if numeric:
            return f"ADR-{int(numeric.group(1)):03d}"
        if re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)+", raw_id):
            return raw_id
    stem_digits = re.match(r"^(\d+)", filepath.stem)
    if stem_digits:
        return f"ADR-{int(stem_digits.group(1)):03d}"
    return None


def _is_superseded(adr: dict) -> bool:
    """Treat as superseded if `superseded-by` is set or status says so."""
    if adr.get("superseded_by"):
        return True
    return adr["status"].lower() in ("superseded", "deprecated", "retired")


def _is_active_firm(adr: dict) -> bool:
    """Firm ADR that still carries invariant-coverage weight."""
    if _is_superseded(adr):
        return False
    return (
        adr["status"].lower() in ("accepted", "proposed")
        and adr["firmness"].lower() == "firm"
    )


def _discover_adr_files(adr_dir: Path) -> list[Path]:
    """Discover ADR files under adr_dir, excluding the index."""
    return sorted(f for f in adr_dir.glob("*.md") if f.name != "index.md")


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
    adr_files = _discover_adr_files(ADR_DIR)
    adrs: dict[str, dict] = {}
    for f in adr_files:
        adr = parse_adr(f)
        if adr is None:
            failures.append(
                f"Warning: {f.name} has no valid YAML frontmatter — skipped by all checks"
            )
            continue
        key = adr["key"]
        if key in adrs:
            failures.append(
                f"Check A: Duplicate ADR key {key} "
                f"in {adrs[key]['path']} and {adr['path']}"
            )
        adrs[key] = adr

    if not adrs:
        failures.append(f"No ADR files with frontmatter found in {ADR_DIR}")
        return failures

    # Track which ADRs are referenced by invariants
    referenced_keys: set[str] = set()

    # Check A: every invariant references valid, existing, non-superseded ADRs
    for inv in invariants:
        if not inv["adr_refs"]:
            failures.append(
                f"Check A: INV-{inv['inv_num']:03d} on line {inv['line']} has no ADR references"
            )
            continue

        for ref in inv["adr_refs"]:
            referenced_keys.add(ref)
            if ref not in adrs:
                failures.append(
                    f"Check A: INV-{inv['inv_num']:03d} (line {inv['line']}) references "
                    f"{ref} which does not exist"
                )
            elif _is_superseded(adrs[ref]):
                failures.append(
                    f"Check C: INV-{inv['inv_num']:03d} (line {inv['line']}) references "
                    f"{ref} which is superseded"
                )

    # Check B: every accepted firm ADR has at least one invariant referencing it
    for key, adr in adrs.items():
        if not _is_active_firm(adr):
            continue
        if key not in referenced_keys:
            failures.append(
                f"Check B: {key} ({adr['title']}) is firm/accepted "
                f"but has no invariant in ARCHITECTURE.md"
            )

    # A/B/C failure short-circuits before check D/E
    if failures:
        return failures

    # Parse assertion blocks for checks D and E
    assertion_blocks = parse_assertion_blocks(arch_text)

    for inv in invariants:
        inv_id = f"INV-{inv['inv_num']:03d}"
        if inv_id in assertion_blocks:
            assertion = assertion_blocks[inv_id]
            atype = assertion.get("type", "")

            # V2 reserved types: skip with warning, not failure
            if atype in ("ast", "custom"):
                print(
                    f"Warning: {inv_id} assertion type '{atype}' is v2-reserved,"
                    f" skipping (Check D)",
                    file=sys.stderr,
                )
                continue

            # Check D: execute the assertion
            result = _run_assertion(PROJECT_ROOT, inv_id, assertion)
            if result:
                failures.append(result)
        else:
            # Check E: no assertion block — warning only, not failure
            print(
                f"Warning: {inv_id} has no machine-checkable assertion (Check E)",
                file=sys.stderr,
            )

    return failures


def main() -> None:
    print("Validating ARCHITECTURE.md against ADR corpus...\n")

    failures = validate()

    if not failures:
        arch_text = ARCHITECTURE_FILE.read_text()
        invariants = parse_invariants(arch_text)
        adr_files = _discover_adr_files(ADR_DIR)
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

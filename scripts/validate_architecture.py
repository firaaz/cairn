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
from lib.atomicity import check_clauses
from lib.premise_match import grounded


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

    Returns dict mapping inv_id (e.g. "INV-001") to a parsed YAML dict.

    The block body is parsed with PyYAML so nested dicts and lists arrive
    in their native Python form (lists become lists, nested objects become
    dicts). Pre-M3 this function did flat key:value parsing and silently
    dropped nested config — see docs/plans/2026-05-06-cairn-shrink-m3-
    bathwater-and-binding-fixes.md Task 3.
    """
    import yaml

    blocks: dict[str, dict] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^```invariant-check\s+(INV-\d+)", line)
        if m:
            inv_id = m.group(1)
            body_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body_lines.append(lines[i])
                i += 1
            body = "\n".join(body_lines)
            try:
                parsed = yaml.safe_load(body) or {}
            except yaml.YAMLError as exc:
                print(
                    f"validate_architecture: {inv_id} block YAML parse error: {exc}",
                    file=sys.stderr,
                )
                parsed = {}
            if not isinstance(parsed, dict):
                print(
                    f"validate_architecture: {inv_id} block did not parse to a dict "
                    f"(got {type(parsed).__name__}); skipping",
                    file=sys.stderr,
                )
                parsed = {}
            blocks[inv_id] = parsed
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
    """Run a test-ref assertion. Returns failure message or None on pass.

    Per ambiguity resolution A2: validates file existence only; function
    qualifiers after ``::`` are stripped before the path check.
    """
    test_path = assertion.get("pattern", "")
    # Strip ::function_name qualifier — file-existence check only (A2).
    file_path = test_path.split("::")[0]
    full_path = project_root / file_path
    if not full_path.exists():
        return f"Check D: {inv_id} FAIL — test file not found: {test_path}"
    return None


# Inline fallback authorised commit-subject prefixes. Used when the
# external registry file is absent (retired per pipeline-substrate-naming-superseded).
# Mirrors the prefix set from the last live registry (2026-05-07).
_FALLBACK_REGISTRY: dict[str, dict] = {
    k: {
        "prefix": k,
        "tool": "inline-fallback",
        "owner-adr": "pipeline-substrate-naming-superseded",
        "since": "2026-05-07",
    }
    for k in [
        "slice:",
        "handoff:",
        "sweep:",
        "bootstrap:",
        "feat:",
        "docs:",
        "fix:",
        "chore:",
        "test:",
        "design:",
        "plan:",
    ]
}


def _load_substrate_registry(project_root: Path) -> dict[str, dict]:
    """Load .claude/pipeline-substrate-registry.yaml as {prefix: entry}.

    Schema-checks: each entry has prefix, tool, owner-adr, since.
    Returns the inline fallback when the file is absent (registry retired per
    pipeline-substrate-naming-superseded; inline list preserves INV-001 mechanics).
    """
    import yaml

    path = project_root / ".claude" / "pipeline-substrate-registry.yaml"
    if not path.exists():
        return dict(_FALLBACK_REGISTRY)
    raw = yaml.safe_load(path.read_text()) or {}
    entries = raw.get("entries", [])
    out: dict[str, dict] = {}
    for entry in entries:
        prefix = entry.get("prefix", "")
        if not prefix:
            continue
        for required in ("prefix", "tool", "owner-adr", "since"):
            if required not in entry:
                raise ValueError(
                    f"INV-001 registry entry {prefix!r} missing {required}"
                )
        out[prefix] = entry
    return out


def _verify_pass_through(sha: str, files: list[str], parents: list[str]) -> str | None:
    return None


def _verify_sweep_commit(sha: str, files: list[str], parents: list[str]) -> str | None:
    has_results = any(f.startswith(".claude/sweep-results/") for f in files)
    has_yaml = ".claude/sweep.yaml" in files
    if not (has_results and has_yaml):
        missing = []
        if not has_results:
            missing.append(".claude/sweep-results/")
        if not has_yaml:
            missing.append(".claude/sweep.yaml")
        return f"sweep verifier: missing {' AND '.join(missing)} touch"
    return None


_SUBSTRATE_VERIFIERS: dict[str, object] = {
    "slice:": _verify_pass_through,
    "handoff:": _verify_pass_through,
    "sweep:": _verify_sweep_commit,
    "bootstrap:": _verify_pass_through,
    "feat:": _verify_pass_through,
    "docs:": _verify_pass_through,
    # fix: was sweep-constrained (touch only .claude/sweep-results/) while the
    # /integration-sweep machinery existed; that apparatus retired at M4 and
    # fix: is an ordinary defect-commit prefix (carrier-hierarchy-and-process-diet).
    "fix:": _verify_pass_through,
    "chore:": _verify_pass_through,
    "design:": _verify_pass_through,
    "plan:": _verify_pass_through,
    "test:": _verify_pass_through,
}

_PLACEHOLDER_SHA = "<pending-slice-close-sha>"


def _git_subjects_in_range(
    repo: Path, base_sha: str
) -> list[tuple[str, str, list[str]]]:
    """Return list of (sha, subject, files_changed) for base_sha..HEAD --no-merges."""
    import subprocess

    range_arg = f"{base_sha}..HEAD"
    out = subprocess.check_output(
        ["git", "log", range_arg, "--no-merges", "--format=%H%x09%s", "--name-only"],
        cwd=str(repo),
        text=True,
    )
    commits: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for line in out.split("\n"):
        if "\t" in line and len(line.split("\t", 1)[0]) == 40:
            if current:
                commits.append(current)
            sha, subject = line.split("\t", 1)
            current = (sha, subject, [])
        elif line and current is not None:
            current[2].append(line)
    if current:
        commits.append(current)
    return commits


def _run_git_log_walk_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Walk git log range, classify each commit, run per-prefix verifier.

    Conventional Commits routing:
    - Subject `<type>:` (bare) routes to the registered verifier for `<type>:`.
    - Subject `<type>(<scope>):` (scoped) routes to a pass-through verifier
      regardless of the registered tool's verifier — scoped CC is a developer
      commit (feature/slice level), not pipeline-substrate emission. Bare
      `fix:` and `sweep:` retain their constrained verifiers.
    - `<type>` not in the registry is reported as 'prefix not in registry'.
    """
    effective_from = assertion.get("binding-effective-from", "")
    if effective_from == _PLACEHOLDER_SHA or not effective_from:
        print(f"{inv_id}: binding pending effective-from set (placeholder present)")
        return None

    registry = _load_substrate_registry(project_root)
    if not registry:
        return f"Check D: {inv_id} FAIL — registry not found or empty"

    cc_re = re.compile(r"^([a-z]+)(\([^)]+\))?:")

    failures: list[str] = []
    for sha, subject, files in _git_subjects_in_range(project_root, effective_from):
        m = cc_re.match(subject)
        if m is None:
            failures.append(f"  {sha[:8]} {subject!r} — prefix not in registry")
            continue
        bare_type = m.group(1)
        is_scoped = m.group(2) is not None
        bare_prefix = f"{bare_type}:"
        if bare_prefix not in registry:
            failures.append(f"  {sha[:8]} {subject!r} — prefix not in registry")
            continue
        if is_scoped:
            verifier = _verify_pass_through
        else:
            verifier = _SUBSTRATE_VERIFIERS.get(bare_prefix)
            if verifier is None:
                failures.append(
                    f"  {sha[:8]} {subject!r} — prefix {bare_prefix!r} has no verifier"
                )
                continue
        err = verifier(sha, files, [])
        if err:
            failures.append(f"  {sha[:8]} {subject!r} — {err}")

    if failures:
        return f"Check D: {inv_id} FAIL — INV-001 violations:\n" + "\n".join(failures)
    return None


ROLE_TOPOLOGY_PATH = (
    Path(__file__).resolve().parent.parent / ".claude" / "agents" / "role-topology.yaml"
)

_ROLE_SHORTHAND_TO_SLUG: dict[str, str] = {
    "reader": "phase-1-tdd",
    "skeptic": "phase-2-tdd",
    "builder": "phase-3-tdd",
    "auditor": "phase-4-tdd",
}


def _extract_role_for_phase(_unused: str | None = None) -> set[tuple[int, str]] | None:
    """Read the canonical (phase, role-slug) topology from role-topology.yaml.

    The legacy signature accepted core.py text; M4 retires that source.
    The argument is preserved for back-compat but ignored.
    """
    import yaml

    try:
        data = yaml.safe_load(ROLE_TOPOLOGY_PATH.read_text())
    except (FileNotFoundError, yaml.YAMLError):
        return None
    phases = data.get("phases") if isinstance(data, dict) else None
    if not isinstance(phases, dict):
        return None
    result: set[tuple[int, str]] = set()
    for k, v in phases.items():
        if (
            isinstance(k, int)
            and isinstance(v, str)
            and re.match(r"^phase-\d+-[a-z][a-z-]*$", v)
        ):
            result.add((k, v))
    return result if result else None


def _extract_skill_guide_topology(
    phase_skill_mapping_text: str,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Extract (phase, role_slug) pairs from the Phase Skill Guide tables.

    Uses shorthand-to-slug mapping for the role-and-anti-behaviors and
    phase-to-skill-mapping tables; additionally verifies each derived
    slug appears somewhere in the full document (catches slug renaming
    outside those tables).
    """
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    title_m = re.search(
        r"^# Phase Skill Guide\b", phase_skill_mapping_text, re.MULTILINE
    )
    if not title_m:
        failures.append(
            "INV-003: Cannot find '# Phase Skill Guide' title in "
            "docs/phase-skill-mapping.md"
        )
        return result, failures

    row_pat = re.compile(
        r"^\|\s*(\d+)\.\s+[^|]+\|\s+\*{0,2}(\w+)\*{0,2}\s*\|", re.MULTILINE
    )
    for m in row_pat.finditer(phase_skill_mapping_text):
        phase_num = int(m.group(1))
        shorthand = m.group(2).lower()
        slug = _ROLE_SHORTHAND_TO_SLUG.get(shorthand)
        if slug:
            result.add((phase_num, slug))

    # Verify each derived slug appears in the full document.
    to_remove: set[tuple[int, str]] = set()
    for pair in result:
        _, slug = pair
        if slug not in phase_skill_mapping_text:
            failures.append(
                f"INV-003: role slug '{slug}' not found anywhere in "
                f"docs/phase-skill-mapping.md"
            )
            to_remove.add(pair)
    result -= to_remove

    return result, failures


def _extract_agent_file_topology(
    project_root: Path,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Parse (phase, role_slug) pairs from .claude/agents/phase-N-*.md filenames.

    Filters to the canonical role-slug set declared by role-topology.yaml. Sibling
    files matching phase-N-*.md but with non-canonical role slugs are tolerated;
    they are NOT reported as drift. A phase ordinal not in role-topology.yaml
    (e.g., phase-5-*.md) IS reported as drift.

    The canonical slug set is read from .claude/agents/role-topology.yaml
    (the authoritative source). If that file cannot be read, returns an error.
    """
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    agents_dir = project_root / ".claude" / "agents"
    if not agents_dir.exists():
        failures.append("INV-003: .claude/agents/ directory not found")
        return result, failures

    topo_path = project_root / ".claude" / "agents" / "role-topology.yaml"
    if not topo_path.exists():
        failures.append(f"INV-003: {topo_path} not found (canonical slug source)")
        return result, failures
    canonical = _extract_role_for_phase() or set()
    canonical_slugs = {slug for _, slug in canonical}
    canonical_phases = {phase for phase, _ in canonical}

    for f in sorted(agents_dir.glob("phase-*.md")):
        m = re.match(r"phase-(\d+)-(.+)\.md$", f.name)
        if not m:
            continue
        phase_num = int(m.group(1))
        slug = f"phase-{m.group(1)}-{m.group(2)}"
        if slug in canonical_slugs:
            result.add((phase_num, slug))
            continue
        if phase_num not in canonical_phases:
            result.add((phase_num, slug))

    return result, failures


def validate_phase_topology(project_root: Path) -> list[str]:
    """Three-way cross-reference: (phase_ordinal, role_slug) topology must agree.

    Canonical sources:
      1. .claude/agents/role-topology.yaml — authoritative phase→slug mapping.
      2. docs/phase-skill-mapping.md — Phase Skill Guide tables.
      3. .claude/agents/phase-N-*.md — agent prompt filenames.

    ROLE_DENY_READ leg dropped (read-class lockdown retired with the substrate;
    see INV-010 retirement in ARCHITECTURE.md).

    Returns list of failure messages; empty on full agreement.
    """
    failures: list[str] = []

    topo_path = project_root / ".claude" / "agents" / "role-topology.yaml"
    if not topo_path.exists():
        return [f"INV-003: {topo_path} not found"]
    authoritative = _extract_role_for_phase()
    if authoritative is None:
        return ["INV-003: Cannot parse phases from .claude/agents/role-topology.yaml"]

    phase_skill_mapping_path = project_root / "docs" / "phase-skill-mapping.md"
    if not phase_skill_mapping_path.exists():
        failures.append(f"INV-003: {phase_skill_mapping_path} not found")
        skill_guide_topology: set[tuple[int, str]] = set()
    else:
        skill_guide_topology, src2_failures = _extract_skill_guide_topology(
            phase_skill_mapping_path.read_text()
        )
        failures.extend(src2_failures)

    agent_topology, src3_failures = _extract_agent_file_topology(project_root)
    failures.extend(src3_failures)

    if failures:
        return failures

    sources = [
        ("phase-skill-mapping.md", skill_guide_topology),
        (".claude/agents/ filenames", agent_topology),
    ]
    for source_name, topology in sources:
        for pair in authoritative:
            if pair not in topology:
                phase, role = pair
                failures.append(
                    f"INV-003: {source_name} is missing ({phase}, '{role}') "
                    f"— phase-topology drift vs role-topology.yaml"
                )
        for pair in topology:
            if pair not in authoritative:
                phase, role = pair
                failures.append(
                    f"INV-003: {source_name} has extra ({phase}, '{role}') "
                    f"— phase-topology drift vs role-topology.yaml"
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


def _run_structural_parser_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a structural-parser assertion against a markdown file.

    Per ADR invariant-binding-strategy D4:
    - Placeholder binding-effective-from → no-op with notice.
    - Required sections missing → fail.
    - Forbidden literal/regex section headings → fail.
    - Forbidden content regex matches → fail.
    - Token budget: ceil(len(bytes)/4) vs warn-at/fail-at.
    """
    import math

    effective_from = assertion.get("binding-effective-from", "")
    if effective_from == "<pending-slice-close-sha>":
        print(
            f"[structural-parser] {inv_id}: binding pending — "
            "binding-effective-from is placeholder, skipping enforcement.",
            file=__import__("sys").stderr,
        )
        return None

    target = assertion.get("target", "")
    target_path = project_root / target
    if not target_path.exists():
        return f"Check D: {inv_id} FAIL — structural-parser target not found: {target}"

    raw = target_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    headings = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)

    required = assertion.get("required-sections", [])
    for section in required:
        if section not in headings:
            return (
                f"Check D: {inv_id} FAIL — structural-parser: "
                f"required section '{section}' missing from {target}"
            )

    forbidden_cfg = assertion.get("forbidden-sections", {})
    for literal in forbidden_cfg.get("literal", []):
        if literal in headings:
            return (
                f"Check D: {inv_id} FAIL — structural-parser: "
                f"forbidden section '{literal}' present in {target}"
            )
    for pattern in forbidden_cfg.get("regex", []):
        for heading in headings:
            heading_line = f"## {heading}"
            if re.search(pattern, heading_line):
                return (
                    f"Check D: {inv_id} FAIL — structural-parser: "
                    f"forbidden section heading '{heading}' matches regex "
                    f"'{pattern}' in {target}"
                )

    content_cfg = assertion.get("forbidden-content", {})
    for pattern in content_cfg.get("regex", []):
        if re.search(pattern, text):
            return (
                f"Check D: {inv_id} FAIL — structural-parser: "
                f"forbidden content pattern '{pattern}' found in {target}"
            )

    budget_cfg = assertion.get("token-budget", {})
    if budget_cfg:
        token_count = math.ceil(len(raw) / 4)
        fail_at = budget_cfg.get("fail-at", None)
        warn_at = budget_cfg.get("warn-at", None)
        if fail_at is not None and token_count > fail_at:
            return (
                f"Check D: {inv_id} FAIL — structural-parser: "
                f"token budget exceeded: {token_count} tokens "
                f"(fail-at {fail_at}) in {target}"
            )
        if warn_at is not None and token_count > warn_at:
            print(
                f"[structural-parser] {inv_id}: token budget warning: "
                f"{token_count} tokens (warn-at {warn_at}) in {target}",
                file=__import__("sys").stderr,
            )

    return None


def _run_premise_grounding_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a premise-grounding assertion: each cited premise must quote its source verbatim. Returns failure message or None."""
    for premise in assertion.get("premises", []):
        source = premise.get("source", "")
        quote = premise.get("quote", "")
        source_path = project_root / source
        if not source_path.exists():
            return (
                f"Check D: {inv_id} FAIL — premise-grounding: "
                f"cited source not found: {source}"
            )
        try:
            text = source_path.read_text()
        except (OSError, UnicodeDecodeError):
            return (
                f"Check D: {inv_id} FAIL — premise-grounding: "
                f"cited source unreadable: {source}"
            )
        if not grounded(text, quote, Path(source).suffix):
            return (
                f"Check D: {inv_id} FAIL — premise-grounding: premise no longer "
                f"grounded in {source} (quoted text absent — stale or fabricated): {quote!r}"
            )
    return None


def _run_scope_split_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Run a scope-split (atomicity) assertion. Returns a failure message or None."""
    must_satisfy = assertion.get("must-satisfy", [])
    if not isinstance(must_satisfy, list):
        return f"Check D: {inv_id} FAIL — scope-split: 'must-satisfy' is not a list"
    offences = check_clauses(must_satisfy)
    if offences:
        return f"Check D: {inv_id} FAIL — scope-split: " + "; ".join(offences)
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
    if atype == "git-log-walk":
        return _run_git_log_walk_assertion(project_root, inv_id, assertion)
    if atype == "structural-parser":
        return _run_structural_parser_assertion(project_root, inv_id, assertion)
    if atype == "premise-grounding":
        return _run_premise_grounding_assertion(project_root, inv_id, assertion)
    if atype == "scope-split":
        return _run_scope_split_assertion(project_root, inv_id, assertion)
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
        "has_contract": "contract" in frontmatter,
        "carrier": frontmatter.get("carrier"),
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


def check_adr_carrier(adrs: dict[str, dict]) -> list[str]:
    """Check F (INV-013 D5): non-superseded ADRs declare their carrier tier.

    A `contract:` frontmatter block (live constraint, names its level 1-4
    carrier) or `carrier: rationale-only` (history/rationale). Superseded
    ADRs are exempt — append-only stands.
    """
    failures = []
    for key, adr in adrs.items():
        if _is_superseded(adr):
            continue
        if adr.get("has_contract"):
            continue
        carrier = adr.get("carrier")
        if carrier == "rationale-only":
            continue
        if carrier is not None:
            failures.append(
                f"Check F: {key} has carrier: {carrier!r} — only "
                f"'rationale-only' or a contract: block is valid"
            )
            continue
        failures.append(
            f"Check F: {key} ({adr['title']}) is non-superseded but declares "
            f"no carrier tier — add a contract: block naming its mechanical "
            f"carrier, or carrier: rationale-only"
        )
    return failures


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

    # Check F (INV-013 D5): every non-superseded ADR declares its carrier tier
    failures.extend(check_adr_carrier(adrs))

    # A/B/C/F failure short-circuits before check D/E
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
            # Retirement markers intentionally carry no binding block.
            if re.match(r"^Retired\b", inv["statement"]):
                continue
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

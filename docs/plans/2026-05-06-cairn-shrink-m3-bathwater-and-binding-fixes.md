# Cairn Shrink M3 — Bathwater Audit + Binding Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the M3 deliverables from the cairn-shrink design (`docs/plans/2026-05-06-cairn-shrink-design.md` §7-M3): a written bathwater audit, three validator fixes that flip INV-001/INV-002/INV-003 bindings live on the post-M2 substrate, a `role_guard.py` simplification design doc, and a SKILL.md revision folding in the four M2 dogfood findings — all without deleting orchestrator or substrate code (those die in M4).

**Architecture:** Three discrete code edits to `scripts/validate_architecture.py` (the assertion-block parser becomes real YAML; the INV-001 walker tolerates Conventional Commits' scoped form `<type>(<scope>):`; the INV-003 agent-file glob ignores `*-tdd.md` siblings) plus a registry extension to `.claude/pipeline-substrate-registry.yaml` (add `design:`, `plan:` as pass-through prefixes — they appear in branch history). Documentation outputs: a slice-by-slice bathwater audit (one row per fix in design §5 plus a sweep of `compression/*` slices), a `role_guard` simplification design doc (drops the MCP-forcing `_CANONICAL_DENY_PATTERNS`; preserves `READ_CLASS_TOOLS` and envelope-grant), and an in-place revision to `cairn-tdd-feature/SKILL.md`. INV-002 binding goes live by substituting `binding-effective-from: <pending-slice-close-sha>` with the M3 close SHA — gated on the handoff fitting the 440-token budget (currently 931 tokens — Task 6 shrinks it).

**Tech Stack:** Python 3.12 with PyYAML (already a project dep, used by `_load_substrate_registry`); pytest via `uv run pytest`; conventional commits with `m3-` scope; markdown for the audit and design docs. No new runtime dependencies.

---

## Pre-flight conventions (decisions locked here, used everywhere below)

These five decisions are referenced by every task. Locking them keeps the plan internally consistent.

1. **Branch.** Stay on `design/cairn-shrink`. M3 commits append to the M2 history; do NOT branch off. Merging happens in M5 after the orchestrator is gone.

2. **Per-task commit-message convention.**
   - Code-fix tasks: `fix(m3-<short-id>): <subject>` (e.g., `fix(m3-inv002-parser): use real YAML for invariant-check blocks`).
   - Test-only commits (Phase 2 RED tests written before implementation): `test(m3-<short-id>): <subject>`.
   - Doc-only tasks: `docs(m3-<short-id>): <subject>` (audit, role_guard design, SKILL.md revision).
   - Registry/data: `chore(m3-<short-id>): <subject>`.
   - Final handoff: `handoff: design/cairn-shrink — M3 landed, queue M4 next session`.

   The scoped form `<type>(<scope>):` is what triggered the M2-era INV-001 reds. Task 4 fixes the registry walker to accept scoped CC; until that task lands, the validator will keep red-flagging M3's own commits — accept this, do not panic, do not invent a workaround.

3. **TDD-by-construction within tasks, no `cairn-tdd-feature` dispatch.** The three code fixes are TDD'd in-place (write test → run RED → implement → run GREEN → commit). M3 is not itself a "feature" in the dispatch-skill sense; it's a milestone with mixed code/doc work. Dogfooding the skill on M3 would be over-fit.

4. **Bathwater audit produces a document, not deletions.** M3 classifies each carry-forward/dies/re-evaluate item from design §5 plus any compression-era fixes the design didn't enumerate. Actual deletes happen in M4. The audit's "do not regress" commitments become input to the M4 plan.

5. **role_guard simplification is design-only in M3.** The implementation lives in M4 alongside orchestrator deletion (so the ROLE_FOR_PHASE source-of-truth migration and the deny-pattern simplification land together, avoiding intermediate broken states). M3's output is a written design doc with the new `ROLE_DENY_READ` / `ROLE_POLICIES` / canonical-source-pointer shape proposed.

---

## File Structure

**New files:**

- `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md` — slice-by-slice survival classification (~120 lines)
- `docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md` — `role_guard.py` redesign for the post-orchestrator world (~80 lines)
- `tests/unit/test_assertion_block_yaml_parser.py` — RED tests for the nested-YAML parser fix (~60 lines)
- `tests/unit/test_inv_001_scoped_cc_acceptance.py` — RED tests for scoped Conventional Commits acceptance in the INV-001 walker (~80 lines)
- `tests/unit/test_inv_003_tdd_siblings_tolerated.py` — RED tests for the `*-tdd.md` sibling tolerance in agent-file topology (~50 lines)

**Modified files:**

- `scripts/validate_architecture.py` — `parse_assertion_blocks` (Task 3), `_run_git_log_walk_assertion` (Task 4), `_extract_agent_file_topology` (Task 5)
- `.claude/pipeline-substrate-registry.yaml` — add `design:` and `plan:` entries (Task 4)
- `docs/ARCHITECTURE.md` — substitute INV-002's `binding-effective-from` placeholder (Task 6)
- `.claude/handoff.md` — shrink to fit 440-token budget if needed (Task 6); rewrite to M3-landed handoff at close (Task 9)
- `.claude/skills/cairn-tdd-feature/SKILL.md` — fold in the four M2 dogfood findings (Task 7)

**Untouched (M3 is non-deleting):** `scripts/slice_orchestrator/`, `scripts/cairn_query/`, `mcp_servers/`, all `commands/claude-code/start-slice*.md` and `integration-sweep*.md`, `checks/role_guard.py` itself (only its design doc lands; implementation is M4), `.claude/agents/phase-{1..4}-{writer,skeptic,implementer,integrator}.md` (originals), all hooks except no `role_guard.py` change.

---

## Task 1: Recon + baseline capture

**Files:**
- Inspect: `.claude/handoff.md`, `scripts/validate_architecture.py`, `.claude/pipeline-substrate-registry.yaml`
- Write: `/tmp/m3-baseline-failures.txt`

- [ ] **Step 1: Confirm working tree is clean modulo known untracked**

Run:
```bash
git rev-parse --abbrev-ref HEAD
git status --short
```
Expected: branch is `design/cairn-shrink`. Untracked files limited to `.claude/scheduled_tasks.lock`, `.windsurf/`, the two pre-existing `docs/plans/2026-04-21-windsurf-*.md`. If anything else is dirty, STOP and consult the handoff.

- [ ] **Step 2: Capture the full failure list (not just summary line — M2 dogfood finding (d))**

Run:
```bash
uv run pytest -q --tb=no -rf 2>&1 | tee /tmp/m3-baseline-failures.txt | tail -20
```
Expected: tail shows a `FAILED` block listing ~15 test ids, then a summary line like `15 failed, 1259 passed, 3 skipped, 2 xfailed`. The full file at `/tmp/m3-baseline-failures.txt` is the comparison anchor for every later task — diff against it, do not re-summarize.

- [ ] **Step 3: Capture validator pre-state**

Run:
```bash
uv run python scripts/validate_architecture.py 2>&1 | tee /tmp/m3-baseline-validator.txt
echo "exit: $?"
```
Expected output includes the structural-parser placeholder notice, then either an INV-001 FAIL listing 14+ commits with prefix-not-in-registry violations OR a clean PASS. Record the actual outcome in the validator baseline file. The exit code is captured at the end — note whether `0` (pass with stderr notice only) or `1` (fail).

- [ ] **Step 4: Snapshot the SHA**

Run:
```bash
git rev-parse HEAD > /tmp/m3-snapshot-sha
cat /tmp/m3-snapshot-sha
```
Expected: a 40-char SHA echoed; this file persists across Bash invocations and is referenced by Task 8's diff guard.

- [ ] **Step 5: Measure handoff token budget**

Run:
```bash
wc -c .claude/handoff.md
python3 -c "import sys; b=open('.claude/handoff.md','rb').read(); print(f'bytes={len(b)} approx_tokens={(len(b)+3)//4}')"
```
Expected: a numeric measurement. Record the result; if `approx_tokens > 440`, Task 6 will need a shrink sub-task. If `approx_tokens <= 440`, Task 6 is a single-line frontmatter substitution.

- [ ] **Step 6: No commit. This is recon.**

---

## Task 2: Write the bathwater audit document

**Files:**
- Create: `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md`

The audit is a one-pass classification of every fix/feature that touched cairn since the bootstrap commit. Inputs: design §5 don't-regress checklist (already classified ~17 items), `.claude/features/*.yaml`, `.claude/completed-slices/*-failed/`, recent `git log --since=2026-04-01` for direct commits.

- [ ] **Step 1: Inventory the inputs**

Run:
```bash
ls .claude/features/
ls .claude/completed-slices/
git log --since=2026-04-01 --no-merges --format="%h %s" --name-only | head -100
```
Expected: 10 feature files (compression, cost-discipline, efficiency-program-afternoon-wins, housekeeping, identifier-scheme, integration-gate, orchestrator-paths, substrate, v1-defense-d2, v1-defense-d3); 6 failed slice archives; recent commit history for context.

- [ ] **Step 2: Write the audit doc**

Create `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md` using this exact template structure. Populate every section's content from the Step-1 inventory before committing — leave no section empty; if an inventory query returns nothing for a section (e.g., no compression-era fixes outside §5), state that explicitly with a one-line "(none beyond design §5)" note.

```markdown
# Cairn Shrink M3 — Bathwater Audit

```
firmness: provisional
status: audit — informs M4 deletion plan
date: 2026-05-06
scope: classify every cairn fix/feature for M4 disposition (carry-forward, dies-with-orchestrator, dies-with-substrate, dies-with-slice-machinery, re-evaluate)
```

## 1. Method

Walked design §5 don't-regress checklist row-by-row, then swept `.claude/features/*.yaml` and `.claude/completed-slices/*-failed/` for any fix not enumerated in §5. For each item, recorded: origin commit/slice, current location in tree, classification, and the M3-vs-M4-vs-M5 disposition.

## 2. Carry-forward (must survive M4 deletion)

For each row of design §5 marked **Carries forward**, write one paragraph: what the fix does, where it lives now, and the one-line M4 commitment ("M4 must preserve X at Y").

Items to cover at minimum (from §5):
- `role_guard` `READ_CLASS_TOOLS = {Read, Grep, Glob}` — slice 2 fixup
- `role_guard` envelope-grant escape (D9) — slice 2
- Triager superseded-test heuristic (`detect_superseded_test_signal`) — compression/triager-superseded-test-heuristic
- YAML safety in `coupling-clusters.yaml` (single-quoted regex) — phase-2-skeptic agent doc
- `ADR_EDITORIAL_FIX=1` typo escape — reversibility-guard.sh

Plus any from compression-era slices not in §5 — list the slice id (`compression/<name>`), the fix, and where it lives.

## 3. Dies-with-orchestrator (acceptable loss when M4 lands)

For each row of design §5 marked **Dies with orchestrator** or **Dies with `commit_phase_handoff`/`close_slice`**, write one line confirming that the original failure mode is orchestrator-bound (i.e., does not exist in the dispatch-skill path).

Items: B9 post-Timeout HEAD reconciliation, B13 `_active_child` for signal handlers, B15 max-1 redispatch-per-phase cap, slice-artifact preservation, phase-1-handoff-stage-surface staging, phase-4-sweepnotes-required staging, `_copy_artifacts_to_sweep_results`, 23-slice-overdue sweep.

## 4. Dies-with-substrate

Items: typed-knowledge graph (kuzu/cairn_query), MCP wrapper, INV-010 lockdown of canonical knowledge paths (the `_CANONICAL_DENY_PATTERNS` in role_guard.py — the read-class lockdown becomes meaningless without the substrate).

## 5. Dies-with-slice-machinery

Items: failed-slice archive (`completed-slices/<id>-failed/`), `start-slice` ceremony, `integration-sweep` ceremony, `close_slice` bundling, `commit_phase_handoff`, `slice.yaml` lifecycle, `current-slice/` directory, sweep ritual.

## 6. Re-evaluate in M4 / M5

- Phase-2-skeptic write-timing fix (issue #26 ae9e6c8) — verify in M4 implementation that the dispatch-skill commit-per-phase pattern doesn't reproduce the original `git diff` exclude-untracked failure mode.
- `V1_ASSERTION_TYPES` allowlist hardcoded in tests — if validator stays (it does), the allowlist stays.
- INV-009 cost-threshold trip — dropped (advisory only); ADR amendment in M4.
- Triager-misroute on superseded tests (memory `triager_misroute_on_superseded_tests`) — verify the new `triager-tdd` agent's prompt iteration handles this; if not, Q-out as a follow-up.

## 7. Open follow-ups (deferred, not blocking M4)

List any audit findings that don't fit M4's scope (e.g., consumer migration prep, plugin packaging concerns, INV-002(b) Tier-2 LLM-judgment runtime binding which is v2).

## 8. M4 input — explicit don't-regress commitments

Bullet list, one per item from §2 above, in the form: "M4 plan MUST preserve <fix> at <location> — verified by <test or grep>."
```

- [ ] **Step 3: Verify the doc is well-formed**

Run:
```bash
head -10 docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
wc -l docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
```
Expected: starts with `# Cairn Shrink M3 — Bathwater Audit`; ~80-150 lines.

- [ ] **Step 4: Commit**

```bash
git add docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
git commit -m "docs(m3-bathwater-audit): classify every fix for M4 disposition"
```

---

## Task 3: Fix `parse_assertion_blocks` to handle nested YAML

**Files:**
- Test: `tests/unit/test_assertion_block_yaml_parser.py` (create)
- Modify: `scripts/validate_architecture.py:151-177` (`parse_assertion_blocks` function)

The current parser does flat `key: value` extraction. INV-002's block uses real nested YAML (`forbidden-sections:` then indented `literal:` and `regex:` keys). The flat parser silently drops the nesting and the assertion config arrives at `_run_structural_parser_assertion` empty — meaning even when binding-effective-from is set, the assertion no-ops on every check.

- [ ] **Step 1: Write the failing test file**

Create `tests/unit/test_assertion_block_yaml_parser.py` with this exact content:

```python
"""RED tests for M3 fix: parse_assertion_blocks must handle nested YAML.

Tracks the INV-002 parser gap called out in
docs/plans/2026-05-06-cairn-shrink-design.md §1.1 and §2.2.

Public surface (existing): scripts/validate_architecture.parse_assertion_blocks
Import path note: cairn's pyproject sets pythonpath = ['scripts'].
"""

from __future__ import annotations

import textwrap

import pytest

from validate_architecture import parse_assertion_blocks


def _block(body: str) -> str:
    """Wrap a body inside a fenced invariant-check block for INV-002."""
    return textwrap.dedent(
        """
        # ARCHITECTURE.md fixture

        ## Invariants

        **INV-002** session-context fixture.

        ```invariant-check INV-002
        type: structural-parser
        target: ".claude/handoff.md"
        required-sections: ["State", "Next", "Blocked / Pending", "Pointers"]
        forbidden-sections:
          literal: ["What This Session Was About", "Self-Check"]
          regex: ['^##\\s+(Lessons|Reflection|Notes)\\b']
        forbidden-content:
          regex: ['I (was|am|will|just) ', '\\d+\\s*/\\s*\\d+']
        token-budget:
          approximation: bytes-per-token-4
          warn-at: 360
          fail-at: 440
        binding-effective-from: "<pending-slice-close-sha>"
        description: "INV-002(a) handoff structural binding"
        """
    ) + body + "\n```\n"


def test_required_sections_parsed_as_list_of_strings():
    """The required-sections key must arrive as a list, not a flat string."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    assert isinstance(inv["required-sections"], list)
    assert inv["required-sections"] == [
        "State",
        "Next",
        "Blocked / Pending",
        "Pointers",
    ]


def test_forbidden_sections_parsed_as_nested_dict():
    """forbidden-sections.literal and .regex must arrive as a dict-of-lists."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    fs = inv["forbidden-sections"]
    assert isinstance(fs, dict), f"Expected dict, got {type(fs).__name__}: {fs!r}"
    assert fs.get("literal") == [
        "What This Session Was About",
        "Self-Check",
    ]
    assert fs.get("regex") == ["^##\\s+(Lessons|Reflection|Notes)\\b"]


def test_forbidden_content_parsed_as_nested_dict():
    """forbidden-content.regex must arrive as a list under a dict key."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    fc = inv["forbidden-content"]
    assert isinstance(fc, dict), f"Expected dict, got {type(fc).__name__}: {fc!r}"
    assert fc.get("regex") == [
        "I (was|am|will|just) ",
        "\\d+\\s*/\\s*\\d+",
    ]


def test_token_budget_parsed_as_nested_dict_with_ints():
    """token-budget.warn-at and .fail-at must arrive as ints under a dict key."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    tb = inv["token-budget"]
    assert isinstance(tb, dict), f"Expected dict, got {type(tb).__name__}: {tb!r}"
    assert tb.get("warn-at") == 360
    assert tb.get("fail-at") == 440
    assert tb.get("approximation") == "bytes-per-token-4"


def test_flat_keys_still_parse_for_legacy_blocks():
    """A flat block (e.g., INV-007's grep type) must still parse correctly."""
    text = textwrap.dedent(
        """
        ## Invariants

        **INV-007** fixture.

        ```invariant-check INV-007
        type: grep
        pattern: "\\.claude/features/"
        target: "commands/claude-code/handoff.full.md"
        expect: match
        description: "Verifies handoff command references feature files"
        ```
        """
    )
    blocks = parse_assertion_blocks(text)
    inv = blocks["INV-007"]
    assert inv["type"] == "grep"
    assert inv["target"] == "commands/claude-code/handoff.full.md"
    assert inv["expect"] == "match"


def test_real_architecture_md_parses_inv_002_correctly():
    """Integration: parsing the real ARCHITECTURE.md yields nested dicts for INV-002."""
    from pathlib import Path

    cairn_root = Path(__file__).resolve().parents[2]
    arch = (cairn_root / "docs/ARCHITECTURE.md").read_text()
    blocks = parse_assertion_blocks(arch)
    inv = blocks["INV-002"]
    assert isinstance(inv.get("forbidden-sections"), dict)
    assert isinstance(inv.get("forbidden-content"), dict)
    assert isinstance(inv.get("token-budget"), dict)
    assert "literal" in inv["forbidden-sections"]
    assert "regex" in inv["forbidden-sections"]
    assert "warn-at" in inv["token-budget"]
    assert "fail-at" in inv["token-budget"]
```

- [ ] **Step 2: Run the new tests — confirm RED**

Run:
```bash
uv run pytest tests/unit/test_assertion_block_yaml_parser.py -v 2>&1 | tail -30
```
Expected: 6 tests collected, all FAIL with assertion errors (e.g., `Expected dict, got str: ''` for the nested-dict tests). The `test_flat_keys_still_parse_for_legacy_blocks` may pass even pre-fix — that's fine, it's a regression guard.

- [ ] **Step 3: Commit the RED tests**

```bash
git add tests/unit/test_assertion_block_yaml_parser.py
git commit -m "test(m3-inv002-parser): RED tests for nested YAML in invariant-check blocks"
```

- [ ] **Step 4: Replace `parse_assertion_blocks` with a real-YAML implementation**

In `scripts/validate_architecture.py`, replace the entire body of `parse_assertion_blocks` (lines 151-177) with this exact implementation:

```python
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
```

- [ ] **Step 5: Run the new tests — confirm GREEN**

Run:
```bash
uv run pytest tests/unit/test_assertion_block_yaml_parser.py -v 2>&1 | tail -15
```
Expected: 6 tests collected, all PASS.

- [ ] **Step 6: Run the full suite — confirm no regression**

Run:
```bash
uv run pytest -q --tb=no -rf 2>&1 | tail -25 > /tmp/m3-task3-after.txt
diff /tmp/m3-baseline-failures.txt /tmp/m3-task3-after.txt | head -40
```
Expected: any FAILED-list lines that disappear from `/tmp/m3-task3-after.txt` are M3 wins (e.g., previously-skipped INV-002 assertions may now run and pass — that's good). Any NEW failures in `/tmp/m3-task3-after.txt` are regressions and must be investigated; the most likely culprit is `tests/unit/test_invariant_assertions.py` which expects the old flat-parser shape. If it regresses, read its assertions: any tests that string-match flat-shape output (`assert blocks[id]["forbidden-sections"] == ""`) need an in-place update because the contract changed; the change is intentional and authorized by this task. Update those tests to assert the new dict shape, commit them in this same task, and re-run.

- [ ] **Step 7: Sanity-check the validator end-to-end**

Run:
```bash
uv run python scripts/validate_architecture.py 2>&1 | head -20
```
Expected: still emits the structural-parser placeholder notice for INV-002 (binding-effective-from unchanged); INV-001 still fails on scoped CC (Task 4 hasn't landed yet); INV-003 still fails on `*-tdd` siblings (Task 5 hasn't landed yet). No new validator-side errors from the parser change.

- [ ] **Step 8: Commit the implementation**

```bash
git add scripts/validate_architecture.py
# If test_invariant_assertions.py needed updating in Step 6, include it:
# git add tests/unit/test_invariant_assertions.py
git commit -m "fix(m3-inv002-parser): use real YAML for invariant-check blocks"
```

---

## Task 4: Fix INV-001 walker to accept scoped Conventional Commits

**Files:**
- Test: `tests/unit/test_inv_001_scoped_cc_acceptance.py` (create)
- Modify: `scripts/validate_architecture.py:337-368` (`_run_git_log_walk_assertion`)
- Modify: `.claude/pipeline-substrate-registry.yaml` (add `design:`, `plan:` entries)

Cairn-shrink branch commits use the scoped form `<type>(<scope>):` per the user's global Conventional Commits preference. The walker's current matching is `subject.startswith(p)` where `p` is the bare prefix `feat:` — this rejects `feat(m2):`. The fix: extract the bare CC type from `<type>(<scope>)?:` and look up the bare type in the registry. Bare `<type>:` continues to use the registered verifier (preserving the `fix:` sweep-only constraint and the `sweep:` scope check); scoped `<type>(<scope>):` is treated as a developer commit and routes to a pass-through verifier independent of the registered tool's verifier (because scoped CC is feature-level commit semantics, not pipeline-substrate emission).

Plus: branch history contains two prefixes never registered (`design:` for design-doc commits, `plan:` for plan-doc commits). Add both as pass-through entries.

- [ ] **Step 1: Write the failing test file**

Create `tests/unit/test_inv_001_scoped_cc_acceptance.py` with this exact content:

```python
"""RED tests for M3 fix: INV-001 walker accepts scoped Conventional Commits.

Tracks the M2 dogfood finding: cairn-shrink branch uses scoped CC form
(`feat(m2-dogfood-extract-invariant-ids):`) which the prior `subject.startswith(prefix)`
match rejected because the registry keys are bare prefixes (`feat:`).

Public surface (existing): scripts/validate_architecture._run_git_log_walk_assertion
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_REL = Path(".claude/pipeline-substrate-registry.yaml")
REGISTRY_ABS = CAIRN_ROOT / REGISTRY_REL


def _git(repo: Path, *args: str) -> str:
    out = subprocess.check_output(
        ["git", *args],
        cwd=str(repo),
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@x",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@x",
        },
    )
    return out.strip()


def _commit(repo: Path, subject: str, touch: list[str]) -> str:
    for rel in touch:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("x\n")
        else:
            path.write_text(path.read_text() + "x\n")
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", subject, "--allow-empty")
    return _git(repo, "rev-parse", "HEAD")


def _init_repo_with_registry(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@x")
    _git(repo, "config", "user.name", "t")
    dst = repo / REGISTRY_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REGISTRY_ABS, dst)
    _git(repo, "add", str(REGISTRY_REL))
    _git(repo, "commit", "-q", "-m", "bootstrap: seed registry for fixture")
    return repo


def test_scoped_feat_commit_passes(tmp_path):
    """`feat(m3-foo): ...` must map to bare type `feat:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "feat(m3-foo): add a thing", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped feat must pass-through. Got: {result!r}"


def test_scoped_test_commit_passes(tmp_path):
    """`test(m3-foo): ...` must map to bare type `test:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "test(m3-foo): RED tests", touch=["tests/unit/test_x.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped test must pass-through. Got: {result!r}"


def test_scoped_chore_commit_passes(tmp_path):
    """`chore(m3-foo): ...` must map to bare type `chore:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "chore(m3-foo): housekeeping", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped chore must pass-through. Got: {result!r}"


def test_scoped_fix_commit_pass_through_not_sweep_constrained(tmp_path):
    """`fix(m3-foo): ...` is feature-level fix, NOT sweep-constrained.

    Bare `fix:` still routes to the sweep-only verifier (preserving the
    integration-sweep semantic). Scoped `fix(<scope>):` is a developer commit
    and uses pass-through.
    """
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "fix(m3-foo): correct a bug", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, (
        f"Scoped fix must pass-through (not sweep-constrained). Got: {result!r}"
    )


def test_bare_fix_still_sweep_constrained(tmp_path):
    """Bare `fix: ...` must still be rejected when not touching sweep-results."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "fix: bad", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is not None, "Bare fix without sweep-results must still fail"
    assert bad_sha[:8] in result
    assert "fix verifier" in result


def test_bare_sweep_still_constrained(tmp_path):
    """Bare `sweep: ...` must still require both sweep-results/ and sweep.yaml."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "sweep: bad", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is not None, "Bare sweep without required paths must still fail"
    assert bad_sha[:8] in result


def test_design_prefix_registered_passes(tmp_path):
    """`design: add cairn-shrink design doc` must pass (registry entry added)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "design: add foo design", touch=["docs/plans/x.md"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"`design:` prefix must pass-through. Got: {result!r}"


def test_plan_prefix_registered_passes(tmp_path):
    """`plan(m2): dispatch skill plan` must pass (registry entry added)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "plan(m2): dispatch skill", touch=["docs/plans/y.md"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"`plan:` prefix must pass-through. Got: {result!r}"


def test_unknown_scoped_prefix_still_rejected(tmp_path):
    """A `wibble(m3): ...` prefix that doesn't map to a registered bare type fails."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "wibble(m3): nope", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is not None, "Unknown scoped prefix must still fail"
    assert bad_sha[:8] in result
    assert "wibble" in result


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
```

- [ ] **Step 2: Run the new tests — confirm RED**

Run:
```bash
uv run pytest tests/unit/test_inv_001_scoped_cc_acceptance.py -v 2>&1 | tail -25
```
Expected: 9 tests collected. The bare-fix and bare-sweep tests (5, 6) likely PASS already (existing behavior). The 7 scoped-CC tests FAIL with messages like "Scoped feat must pass-through. Got: 'Check D: INV-001 FAIL — INV-001 violations:\\n  abc12345 \"feat(m3-foo): add a thing\" — prefix not in registry'". The `design:` and `plan:` tests fail because those prefixes don't exist in the registry yet.

- [ ] **Step 3: Commit the RED tests**

```bash
git add tests/unit/test_inv_001_scoped_cc_acceptance.py
git commit -m "test(m3-inv001-scoped-cc): RED tests for scoped Conventional Commits acceptance"
```

- [ ] **Step 4: Add `design:` and `plan:` to the registry**

Edit `.claude/pipeline-substrate-registry.yaml` and append these two entries at the end of the `entries:` list (preserve the existing entries verbatim):

```yaml
  - prefix: "design:"
    tool: "design-doc commits on a feature/design branch"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-06
    notes: "Pass-through: design-document landings on design/* branches."
  - prefix: "plan:"
    tool: "plan-doc commits authored via superpowers:writing-plans"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-06
    notes: "Pass-through: implementation-plan landings."
```

- [ ] **Step 5: Add the matching pass-through verifier entries**

Edit `scripts/validate_architecture.py:295-305` (the `_SUBSTRATE_VERIFIERS` dict). Add two entries between `"chore:"` and `"test:"`:

```python
_SUBSTRATE_VERIFIERS: dict[str, object] = {
    "slice:": _verify_pass_through,
    "handoff:": _verify_pass_through,
    "sweep:": _verify_sweep_commit,
    "bootstrap:": _verify_pass_through,
    "feat:": _verify_pass_through,
    "docs:": _verify_pass_through,
    "fix:": _verify_fix_commit,
    "chore:": _verify_pass_through,
    "design:": _verify_pass_through,
    "plan:": _verify_pass_through,
    "test:": _verify_pass_through,
}
```

- [ ] **Step 6: Replace the prefix-matching loop in `_run_git_log_walk_assertion`**

In `scripts/validate_architecture.py:337-368`, replace the body of `_run_git_log_walk_assertion` with this exact implementation. The change is in the `for sha, subject, files in ...` loop: extract the bare CC type from `<type>(<scope>)?:`, then route bare-vs-scoped to the registered verifier vs pass-through.

```python
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
            failures.append(
                f"  {sha[:8]} {subject!r} — prefix not in registry"
            )
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
```

- [ ] **Step 7: Run the new tests — confirm GREEN**

Run:
```bash
uv run pytest tests/unit/test_inv_001_scoped_cc_acceptance.py -v 2>&1 | tail -15
```
Expected: all 9 tests PASS.

- [ ] **Step 8: Run the original INV-001 binding tests — confirm no regression**

Run:
```bash
uv run pytest tests/unit/test_inv_001_git_log_walk.py -v 2>&1 | tail -15
```
Expected: all 8 tests pass. The `test_validator_e2e_passes_with_placeholder` test, which was the M2 RED, now flips GREEN (the validator no longer fails on the scoped-CC and `design:`/`plan:` commits in the walk).

- [ ] **Step 9: Run the full suite — confirm aggregate improvement**

Run:
```bash
uv run pytest -q --tb=no -rf 2>&1 | tail -25 > /tmp/m3-task4-after.txt
diff /tmp/m3-baseline-failures.txt /tmp/m3-task4-after.txt | head -30
```
Expected: at least one test goes from FAILED to PASS — `test_validator_e2e_passes_with_placeholder`. No new failures introduced. Summary line shows ≤14 failed (one M2 red flipped GREEN).

- [ ] **Step 10: Verify the validator binary itself**

Run:
```bash
uv run python scripts/validate_architecture.py 2>&1 | head -10
echo "exit: $?"
```
Expected: validator exits 0 (no INV-001 FAIL — all branch commits including M3's RED-test commits now match registry). The structural-parser placeholder notice still prints to stderr (Task 6 will flip the placeholder).

- [ ] **Step 11: Commit the implementation**

```bash
git add scripts/validate_architecture.py .claude/pipeline-substrate-registry.yaml
git commit -m "fix(m3-inv001-scoped-cc): accept scoped CC and register design:/plan: prefixes"
```

---

## Task 5: Fix INV-003 topology to ignore `*-tdd.md` siblings

**Files:**
- Test: `tests/unit/test_inv_003_tdd_siblings_tolerated.py` (create)
- Modify: `scripts/validate_architecture.py:445-464` (`_extract_agent_file_topology`)

The current glob `agents_dir.glob("phase-*.md")` captures every `phase-N-X.md` file. With M2's new `phase-{1..4}-tdd.md` siblings, the agent-file topology becomes a superset of `ROLE_FOR_PHASE`'s canonical 4 entries; `validate_phase_topology` then reports `extra` pairs (`(1, "phase-1-tdd")`, etc.) as drift. The fix: only count files whose role-slug is in the canonical set; sibling phase-* files (variants for skill-driven dispatch) are tolerated.

Note: this fix preserves the test `test_extra_phase_5_agent_file_fails` which adds a `phase-5-evaluator.md` outside the canonical phase ordinals. That test must still pass — a phase-5 agent file IS drift because there's no phase-5 in `ROLE_FOR_PHASE`. The discriminator: `*-tdd` is allowed because `(phase, slug)` would only collide if it matched a canonical `(phase, slug)` — and `phase-1-tdd ≠ phase-1-writer`. So we filter by canonical-slug equality, not by phase ordinal.

- [ ] **Step 1: Write the failing test file**

Create `tests/unit/test_inv_003_tdd_siblings_tolerated.py` with this exact content:

```python
"""RED tests for M3 fix: INV-003 topology ignores *-tdd.md sibling agent defs.

Tracks the M2 change: cairn-tdd-feature skill introduced phase-{1..4}-tdd.md
siblings of the canonical phase-{1..4}-{writer,skeptic,implementer,integrator}.md
agents. The topology binding must tolerate these siblings without flagging drift.

Out-of-scope guard: phase-5-foo.md MUST still fail (no phase-5 in ROLE_FOR_PHASE).

Public surface (existing): scripts/validate_architecture.validate_phase_topology
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parents[2]


def _seed_canonical_only(tmp_path: Path) -> Path:
    """Copy the four canonical agent files + the three other canonical sources."""
    canonical_sources = [
        Path("scripts/slice_orchestrator/core.py"),
        Path("docs/operational-reference.md"),
        Path("checks/role_guard.py"),
    ]
    canonical_agents = [
        Path(".claude/agents/phase-1-writer.md"),
        Path(".claude/agents/phase-2-skeptic.md"),
        Path(".claude/agents/phase-3-implementer.md"),
        Path(".claude/agents/phase-4-integrator.md"),
    ]
    for rel in canonical_sources + canonical_agents:
        src = CAIRN_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return tmp_path


def test_clean_tree_with_tdd_siblings_passes():
    """Live cairn HEAD: phase-{1..4}-tdd.md siblings exist and must not break the binding."""
    from validate_architecture import validate_phase_topology

    failures = validate_phase_topology(CAIRN_ROOT)
    assert failures == [], (
        f"phase-*-tdd.md siblings must not trigger phase-topology drift.\n"
        f"failures={failures!r}"
    )


def test_phase_1_tdd_sibling_alone_does_not_fail(tmp_path):
    """Adding a phase-1-tdd.md to a clean topology does not fail the binding."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    sibling = tmp_path / ".claude/agents/phase-1-tdd.md"
    sibling.write_text("---\nname: phase-1-tdd\n---\n")

    failures = validate_phase_topology(tmp_path)
    assert failures == [], (
        f"phase-1-tdd sibling alone must not fail the binding. failures={failures!r}"
    )


def test_all_four_tdd_siblings_do_not_fail(tmp_path):
    """All four phase-N-tdd.md siblings together do not fail the binding."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    for n, role in [
        (1, "writer"),
        (2, "skeptic"),
        (3, "implementer"),
        (4, "integrator"),
    ]:
        sibling = tmp_path / f".claude/agents/phase-{n}-tdd.md"
        sibling.write_text(f"---\nname: phase-{n}-tdd\n---\n")

    failures = validate_phase_topology(tmp_path)
    assert failures == [], (
        f"Four TDD siblings must not fail. failures={failures!r}"
    )


def test_phase_5_evaluator_still_fails(tmp_path):
    """Out-of-scope guard: a phase-5-* file (not in ROLE_FOR_PHASE) must still fail."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    extra = tmp_path / ".claude/agents/phase-5-evaluator.md"
    extra.write_text("---\nname: phase-5-evaluator\n---\n")

    failures = validate_phase_topology(tmp_path)
    assert failures, "Extra phase-5-evaluator.md must still fail the binding"
    joined = "\n".join(failures)
    assert "5" in joined or "phase-5" in joined, (
        f"Failure must name the offending phase. failures={failures!r}"
    )


def test_canonical_role_slug_replaced_by_tdd_variant_still_fails(tmp_path):
    """If phase-2-skeptic.md is REMOVED but phase-2-tdd.md exists, the binding must fail.

    The TDD sibling does NOT replace the canonical role; missing canonical files
    are still drift.
    """
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    (tmp_path / ".claude/agents/phase-2-skeptic.md").unlink()
    (tmp_path / ".claude/agents/phase-2-tdd.md").write_text(
        "---\nname: phase-2-tdd\n---\n"
    )

    failures = validate_phase_topology(tmp_path)
    assert failures, (
        "Removing phase-2-skeptic.md must still fail even when phase-2-tdd.md exists"
    )


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
```

- [ ] **Step 2: Run the new tests — confirm RED**

Run:
```bash
uv run pytest tests/unit/test_inv_003_tdd_siblings_tolerated.py -v 2>&1 | tail -25
```
Expected: 5 tests collected. `test_clean_tree_with_tdd_siblings_passes`, `test_phase_1_tdd_sibling_alone_does_not_fail`, and `test_all_four_tdd_siblings_do_not_fail` FAIL (because the current `_extract_agent_file_topology` reports the TDD siblings as `extra`). `test_phase_5_evaluator_still_fails` and `test_canonical_role_slug_replaced_by_tdd_variant_still_fails` may already PASS.

- [ ] **Step 3: Commit the RED tests**

```bash
git add tests/unit/test_inv_003_tdd_siblings_tolerated.py
git commit -m "test(m3-inv003-tdd-siblings): RED tests for *-tdd.md tolerance in topology"
```

- [ ] **Step 4: Replace `_extract_agent_file_topology` to filter by canonical slug**

In `scripts/validate_architecture.py:445-464`, replace the function body with this exact implementation:

```python
def _extract_agent_file_topology(
    project_root: Path,
) -> tuple[set[tuple[int, str]], list[str]]:
    """Parse (phase, role_slug) pairs from .claude/agents/phase-N-*.md filenames.

    Filters to the canonical role-slug set declared by ROLE_FOR_PHASE. Sibling
    files matching phase-N-*.md but with non-canonical role slugs (e.g.,
    phase-1-tdd.md introduced by the cairn-tdd-feature skill) are tolerated;
    they are NOT reported as drift. A phase ordinal not in ROLE_FOR_PHASE
    (e.g., phase-5-*.md) IS reported as drift.

    The canonical slug set is read from ROLE_FOR_PHASE in
    scripts/slice_orchestrator/core.py (the authoritative source). If that file
    cannot be read, returns an error in the failure list.
    """
    failures: list[str] = []
    result: set[tuple[int, str]] = set()

    agents_dir = project_root / ".claude" / "agents"
    if not agents_dir.exists():
        failures.append("INV-003: .claude/agents/ directory not found")
        return result, failures

    core_path = project_root / "scripts" / "slice_orchestrator" / "core.py"
    if not core_path.exists():
        failures.append(f"INV-003: {core_path} not found (canonical slug source)")
        return result, failures
    canonical = _extract_role_for_phase(core_path.read_text()) or set()
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
```

- [ ] **Step 5: Run the new tests — confirm GREEN**

Run:
```bash
uv run pytest tests/unit/test_inv_003_tdd_siblings_tolerated.py -v 2>&1 | tail -15
```
Expected: all 5 tests PASS.

- [ ] **Step 6: Run the original INV-003 binding tests — confirm no regression**

Run:
```bash
uv run pytest tests/unit/test_inv_003_phase_topology.py -v 2>&1 | tail -25
```
Expected: all tests pass. The `TestCleanTreePasses::test_clean_tree_returns_no_failures` (the M2 +1 RED) flips GREEN. The perturbation tests (renamed agent file, missing canonical, extra phase-5) all still fail correctly.

- [ ] **Step 7: Run the full suite — confirm aggregate improvement**

Run:
```bash
uv run pytest -q --tb=no -rf 2>&1 | tail -25 > /tmp/m3-task5-after.txt
diff /tmp/m3-baseline-failures.txt /tmp/m3-task5-after.txt | head -40
```
Expected: at least one further test goes from FAILED to PASS (`test_clean_tree_returns_no_failures`); no new failures. Summary line ≤13 failed.

- [ ] **Step 8: Commit the implementation**

```bash
git add scripts/validate_architecture.py
git commit -m "fix(m3-inv003-tdd-siblings): tolerate *-tdd.md siblings in topology binding"
```

---

## Task 6: Activate INV-002 binding (handoff shrink + effective-from substitution)

**Files:**
- Modify: `.claude/handoff.md` (shrink to ≤440 tokens if needed)
- Modify: `docs/ARCHITECTURE.md` (substitute INV-002's binding-effective-from placeholder)

INV-002's structural-parser binding short-circuits while `binding-effective-from` is the literal `<pending-slice-close-sha>`. Flipping it to a real SHA activates the assertion. Precondition: the assertion's `token-budget.fail-at: 440` must be satisfied by the current handoff. From Task 1 Step 5: handoff is ~931 tokens (3724 bytes ÷ 4) — way over budget. Shrink first, then substitute.

- [ ] **Step 1: Re-measure handoff post-Task-3-4-5**

Run:
```bash
python3 -c "import sys; b=open('.claude/handoff.md','rb').read(); print(f'bytes={len(b)} approx_tokens={(len(b)+3)//4}')"
```
Expected: still ~931 tokens (no task before this one touches the handoff).

- [ ] **Step 2: Shrink the handoff to fit ≤440 tokens (~1760 bytes)**

The current handoff has a single ~1800-char paragraph in the State section. Tighten it to two short paragraphs covering only what M3's Next session must know. Edit `.claude/handoff.md`. The replacement structure (target ~360 tokens / ~1440 bytes for warn-at safety):

Frontmatter (preserve, update `as-of`):
```yaml
---
slice: design/cairn-shrink
phase: m2-landed
branch: design/cairn-shrink
as-of: 2026-05-06 <preserve current SHA from existing frontmatter>
---
```

State section (≤500 chars):
```
## State
M2 landed: five TDD-flavored phase agents + cairn-tdd-feature skill, dogfooded on m2-dogfood-extract-invariant-ids (4 per-phase commits, 8 GREEN tests). Suite: 15 failed / 1259 passed (+2 vs pre-M2 are M3 territory). Orchestrator and substrate untouched.
```

Next section (≤300 chars):
```
## Next
Run superpowers:writing-plans for M3: bathwater audit + INV-002 parser fix + INV-001 scoped-CC + INV-003 topology + role_guard simplification (design only). Do NOT delete orchestrator (M4).
```

Blocked / Pending (≤200 chars):
```
## Blocked / Pending
- INV-002 binding placeholder (M3 fixes parser + flips effective-from).
- ADR supersession map in design §7 (M4 authoring).
- Consumer migration deferred to M6.
```

Pointers (≤500 chars):
```
## Pointers
- docs/plans/2026-05-06-cairn-shrink-design.md — overall design.
- docs/plans/2026-05-06-cairn-shrink-m2-dispatch-skill.md — M2 plan.
- docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md — dogfood spec.
- .claude/skill-runs/m2-dogfood-extract-invariant-ids/ — dogfood workspace.
- .claude/skills/cairn-tdd-feature/SKILL.md — dispatch skill.
- Branch design/cairn-shrink — WIP; do not merge to dev until M5.
```

- [ ] **Step 3: Verify the new handoff fits the budget**

Run:
```bash
python3 -c "b=open('.claude/handoff.md','rb').read(); t=(len(b)+3)//4; print(f'bytes={len(b)} approx_tokens={t} status={\"FITS\" if t<=440 else \"OVER\"}')"
```
Expected: `status=FITS` and `approx_tokens` ≤ 440. If OVER, tighten further; the State section is the most pruning-tolerant.

- [ ] **Step 4: Sanity-check structural sections**

Run:
```bash
grep -E '^##\s' .claude/handoff.md
```
Expected exactly four lines:
```
## State
## Next
## Blocked / Pending
## Pointers
```

- [ ] **Step 5: Substitute INV-002's binding-effective-from placeholder**

We will substitute with the SHA of the next commit (created in Step 7). Two approaches: (a) commit the handoff alone first, then a follow-up `docs:` commit substitutes (mirrors INV-001 precedent at fd1823e); (b) substitute now using a commit-amend dance. Choose (a) — simpler and matches precedent.

For now in Step 5, edit `docs/ARCHITECTURE.md` line 38, changing:
```yaml
binding-effective-from: "<pending-slice-close-sha>"
```
to the literal placeholder used as a target for Step 7's substitution:
```yaml
binding-effective-from: "<m3-pending-effective-from>"
```

(This intermediate placeholder distinguishes the M3 substitution target from any other `<pending-slice-close-sha>` instances. Step 7 swaps it for the real SHA.)

- [ ] **Step 6: Stage and commit the handoff shrink + intermediate placeholder**

```bash
git add .claude/handoff.md docs/ARCHITECTURE.md
git commit -m "chore(m3-inv002-activate): shrink handoff to fit budget; mark INV-002 effective-from for substitution"
```

- [ ] **Step 7: Substitute the intermediate placeholder with this commit's SHA**

Run:
```bash
COMMIT_SHA=$(git rev-parse HEAD)
echo "Substituting <m3-pending-effective-from> with $COMMIT_SHA"
```

Then edit `docs/ARCHITECTURE.md` line 38, changing:
```yaml
binding-effective-from: "<m3-pending-effective-from>"
```
to:
```yaml
binding-effective-from: "<COMMIT_SHA value from above>"
```

- [ ] **Step 8: Verify the validator with INV-002 active**

Run:
```bash
uv run python scripts/validate_architecture.py 2>&1 | head -25
echo "exit: $?"
```
Expected: exit 0; the structural-parser placeholder notice is GONE (binding is live); INV-002 silently passes (handoff fits budget, all required sections present, no forbidden content).

- [ ] **Step 9: Verify the assertion would actually fire if violated (smoke test)**

Run:
```bash
cp .claude/handoff.md /tmp/handoff-backup.md
echo "" >> .claude/handoff.md
echo "## Lessons" >> .claude/handoff.md
echo "I was just thinking..." >> .claude/handoff.md
uv run python scripts/validate_architecture.py 2>&1 | head -10
echo "exit: $?"
mv /tmp/handoff-backup.md .claude/handoff.md
```
Expected: exit 1 with output naming INV-002 and citing either the forbidden `## Lessons` section or the forbidden content `I was`. After the restore, the validator passes again.

- [ ] **Step 10: Re-confirm validator clean**

Run:
```bash
uv run python scripts/validate_architecture.py 2>&1 | tail -5
echo "exit: $?"
```
Expected: exit 0, "ALL CHECKS PASSED".

- [ ] **Step 11: Run the full suite — confirm INV-002 binding-related tests still pass**

Run:
```bash
uv run pytest tests/unit/test_invariant_assertions.py -v 2>&1 | tail -15
uv run pytest -q --tb=no -rf 2>&1 | tail -10 > /tmp/m3-task6-after.txt
```
Expected: invariant_assertions tests pass (or any failures are intentional — see Task 3 Step 6 note about contract-update tests). Suite-summary line shows further reduction from baseline.

- [ ] **Step 12: Commit the substitution**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs(m3-inv002-activate): substitute INV-002 binding-effective-from with M3 SHA"
```

---

## Task 7: Revise SKILL.md per the four M2 dogfood findings

**Files:**
- Modify: `.claude/skills/cairn-tdd-feature/SKILL.md`

The four findings (from `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md`):

(a) Agent registry doesn't refresh mid-session — operational note for SKILL.md.
(b) Phase-2 brief should pass project import convention.
(c) Phase-3 self-attributed regressions instead of RAISE_ISSUE — strengthen verification language.
(d) Baseline capture should be the full FAILED list, not just summary line.

- [ ] **Step 1: Add a "Pre-flight conventions" section to SKILL.md after the "Inputs" section**

In `.claude/skills/cairn-tdd-feature/SKILL.md`, insert this block immediately after the existing "## Inputs" section (which ends at "...e.g., `docs/plans/2026-05-06-some-feature.md`."):

```markdown
## Pre-flight conventions

Before dispatching Phase 1, verify and prepare the following — these prevent the four issues observed during the M2 dogfood (see `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md` for the original incidents):

1. **Agent definitions are session-pre-existing.** Claude Code's agent registry loads at session start; agent definitions added mid-session aren't `subagent_type`-discoverable. The five agents this skill dispatches (`phase-{1..4}-tdd`, `triager-tdd`) live at `.claude/agents/`. Confirm with `ls .claude/agents/phase-{1..4}-tdd.md .claude/agents/triager-tdd.md` before Step 4. If any are missing or the session predates their commit, abort and instruct the operator to start a fresh session.

2. **Project import convention is in every Phase brief.** Cairn's `pyproject.toml` sets `[tool.pytest.ini_options] pythonpath = ["scripts"]`, which means Python imports inside `tests/` use the form `from <subpackage>.<module> import ...` where `<subpackage>` is a directory under `scripts/` (e.g., `from lib.invariant_id_extractor import extract_invariant_ids`). The Phase-2 brief MUST include this exact convention verbatim — Phase 2's M2 dogfood wrote a bare-module import (`from invariant_id_extractor import ...`) which required a fixup. Inline the `pythonpath` rule in the Phase-2 prompt; do not assume the agent can infer it.

3. **Baseline capture uses the full FAILED list, not the summary line.** Before Phase 1, run `uv run pytest -q --tb=no -rf` and capture the full output (typically 20-50 lines: a `FAILED` block followed by the summary). This file is the comparison anchor for Phase 4. The M2 dogfood captured only the summary line and Phase 4 had to investigate two flagged "new failures" by file-identity comparison instead of a list diff.

## Verification language (Phase 3 / Phase 4)

Phase 3 and Phase 4 briefs MUST contain the following exact language about regression attribution:

> Any test failure observed beyond the baseline failure list (file pinned in `/tmp/<feature-id>-baseline-failures.txt`) requires either (a) a `file:line` citation showing the failure was already present at the snapshot SHA, or (b) `RAISE_ISSUE` with the failure id in the summary. Self-attribution without evidence — "those failures are caused by Phase 2 commits not by my work" — is not acceptable. The baseline file is the only authority.
```

- [ ] **Step 2: Verify the SKILL.md is well-formed**

Run:
```bash
head -5 .claude/skills/cairn-tdd-feature/SKILL.md
wc -l .claude/skills/cairn-tdd-feature/SKILL.md
grep -c '^## ' .claude/skills/cairn-tdd-feature/SKILL.md
```
Expected: starts with `---` frontmatter; total lines ~110-160 (was ~70, +35-50 added); section count increased by 2 (Pre-flight conventions + Verification language).

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/cairn-tdd-feature/SKILL.md
git commit -m "docs(m3-skill-revision): fold four M2 dogfood findings into cairn-tdd-feature SKILL"
```

---

## Task 8: Write the `role_guard.py` simplification design doc

**Files:**
- Create: `docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md`

Design output only. The actual `role_guard.py` rewrite happens in M4 alongside orchestrator deletion. M3's job: write the target shape so M4's plan can implement it without re-deriving.

- [ ] **Step 1: Confirm M3 has not modified `checks/role_guard.py`**

Run:
```bash
git diff $(cat /tmp/m3-snapshot-sha) HEAD -- checks/role_guard.py
```
Expected: empty diff.

- [ ] **Step 2: Write the design doc**

Create `docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md` with this exact content (do not paraphrase):

```markdown
# role_guard.py — Post-Orchestrator Simplification Design

```
firmness: provisional
status: design — informs M4 implementation
date: 2026-05-06
scope: target shape for checks/role_guard.py once orchestrator + substrate retire (M4)
inputs:
  - docs/plans/2026-05-06-cairn-shrink-design.md §2.2, §4
  - checks/role_guard.py (current)
  - docs/adr/cliff-failure-mode-and-v1-defenses.md (D9 envelope-grant escape)
  - docs/adr/compression-infrastructure-bootstrap.md (phase-3 envelope asymmetry)
```

## 1. What dies, what survives

**Dies (M4):**

- `_CANONICAL_DENY_PATTERNS` — the read-class lockdown of `scripts/cairn_query/`, `docs/ARCHITECTURE.md`, `docs/adr/`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`. Without the substrate (cairn_query + MCP), there is no MCP-equivalent to force agents to use. The lockdown was substrate-machinery; it dies with the substrate.
- `ROLE_DENY_READ` table — emptied (or removed entirely; see §3 option (a) vs (b)).
- The Bash-token deny logic (lines 179-189) — only existed to lock down canonical-knowledge paths via `cat`/`head`/`grep`.
- INV-010 — the canonical-knowledge-lockdown invariant retires when its substrate retires; supersession ADR in M4 (per design §7 entry for `cairn-substrate-and-fastmcp`).

**Survives (M4 carries forward):**

- `READ_CLASS_TOOLS = {Read, Grep, Glob}` — still load-bearing for any future read-restriction (e.g., per-phase write boundaries that also need to gate Grep). Even if no current rule uses it, it's a one-line constant; cost-of-keeping is zero, cost-of-losing-and-re-deriving is positive.
- Envelope-grant mechanism (`_envelope_patterns`, `AGENT_ENVELOPE` parsing) — moves from "escape hatch" to "primary mechanism". The dispatch skill passes the source-write envelope as `AGENT_ENVELOPE`; `role_guard` enforces it.
- `_log_grant` / `.claude/envelope-grants.log` — preserves audit trail of envelope writes; trivial cost.
- Per-role write allowlists (`ROLE_POLICIES`) — preserved, but UPDATED to the new TDD agents' write paths (no `current-slice/` references).

## 2. Shape of the new module

Target structure (~70-90 lines, down from 226):

```python
"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.

Inner gate paired with each agent's `tools:` frontmatter. Reads tool-call JSON
from stdin. AGENT_ROLE unset is the no-op path. Post-shrink (M4):
- Read-class lockdown removed (canonical-knowledge-via-MCP retired).
- Write paths target dispatch-skill workspace (.claude/skill-runs/) and tests/.
- Phase-3 write gate is envelope-driven (AGENT_ENVELOPE), unchanged in spirit.
"""

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}  # preserved; not currently used by any rule

ROLE_POLICIES = {
    "phase-1-tdd": [
        r"^\.claude/skill-runs/[^/]+/intent\.md$",
    ],
    "phase-2-tdd": [
        r"^tests/",
        r"^\.claude/skill-runs/[^/]+/validation/",
    ],
    "phase-4-tdd": [
        r"^\.claude/skill-runs/[^/]+/integration/",
        r"^\.claude/handoff\.md$",
    ],
    # phase-3-tdd: no static entry; envelope-driven (preserves slice-2 asymmetry).
}
```

## 3. Two open questions for M4 implementer

### (a) Drop `ROLE_DENY_READ` entirely, or empty-dict it?

- **Drop entirely**: cleaner code; smaller surface; M4 supersession ADR for INV-010 makes this honest.
- **Empty-dict it**: forward-compatible if a future invariant wants to re-introduce a read lockdown for a different reason; cost is one constant.

Recommendation: **drop entirely**. Forward-compat without a use case is YAGNI.

### (b) Should `phase-3-tdd` get a static partial allowlist, or stay envelope-only?

- **Static partial**: reduces operator burden of envelope authoring; constrains drift.
- **Envelope-only (status quo)**: preserves the phase-3 asymmetry slice-2 enshrined; matches the dispatch-skill's existing envelope contract.

Recommendation: **envelope-only**. The dispatch skill's plan-doc frontmatter already carries the envelope; no second source.

## 4. Migration sequence for M4

1. Author supersession ADR for `cairn-substrate-and-fastmcp` (retires substrate; INV-010 retires).
2. Delete `_CANONICAL_DENY_PATTERNS`, `ROLE_DENY_READ`, the Bash-token deny block, and `_log_grant`'s slice-id reference (or update to a generic identifier).
3. Update `ROLE_POLICIES` keys from canonical role slugs (`phase-1-writer`, etc.) to TDD slugs (`phase-1-tdd`, etc.) with paths under `.claude/skill-runs/<feature>/`.
4. Update `ROLE_POLICIES` values from `current-slice/` paths to `skill-runs/<feature>/` paths.
5. Confirm INV-003 binding still passes — note: M4 also moves the canonical role-slug source out of `scripts/slice_orchestrator/core.py` (which dies). Either:
   - Move `ROLE_FOR_PHASE` to a stable location (e.g., `.claude/agents/role-topology.yaml`) and update the validator, OR
   - Retire INV-003's canonical-source-vs-mirrors check; replace with a simpler "the four canonical agent files exist" check.
   This sub-decision is M4's, not M3's.
6. Run the full suite. Add new tests for the simplified shape if existing tests bind to the old surface (e.g., the asymmetry-comment test asserts a specific comment in role_guard.py — preserve or update).

## 5. Don't-regress (carry-forward from §1)

- M4 plan MUST preserve `READ_CLASS_TOOLS = {Read, Grep, Glob}` even if unused (zero cost, future-proof).
- M4 plan MUST preserve `_envelope_patterns` parsing (JSON array shape, JSON object with `paths` key, legacy colon-separated with deprecation warning).
- M4 plan MUST preserve `_log_grant` writing to `.claude/envelope-grants.log` (audit surface — useful for forensics on the new TDD path too).
- M4 plan MUST preserve the phase-3 asymmetry decision (option (b) per `compression-infrastructure-bootstrap`): no static `ROLE_POLICIES` entry; envelope-driven.
- M4 plan MUST preserve INV-002(a) handoff structural binding's load-bearing role on `.claude/handoff.md` writes — the phase-4-tdd write rule must NOT bypass the structural-parser check (the parser runs in `validate_architecture.py`, independent; this is an integration-level commitment).
```

- [ ] **Step 3: Verify the doc is well-formed**

Run:
```bash
head -5 docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md
wc -l docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md
grep -c '^## ' docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md
```
Expected: starts with `# role_guard.py — Post-Orchestrator Simplification Design`; ~80-110 lines; 5 sections (1-5).

- [ ] **Step 4: Commit**

```bash
git add docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md
git commit -m "docs(m3-role-guard-design): post-orchestrator role_guard simplification design"
```

---

## Task 9: Final verification + handoff

**Files:**
- Modify: `.claude/handoff.md` (rewrite for M3-landed)

- [ ] **Step 1: Run the full suite — final aggregate**

Run:
```bash
uv run pytest -q --tb=no -rf 2>&1 | tail -25 > /tmp/m3-final.txt
diff /tmp/m3-baseline-failures.txt /tmp/m3-final.txt | head -50
```
Expected: at minimum, two M2-era reds flipped GREEN (`test_validator_e2e_passes_with_placeholder` and `test_clean_tree_returns_no_failures`). No new failures introduced. Summary line ≤13 failed (down from 15 baseline). The remaining 13 reds are pre-M2 baseline, M3 carries them as inherited.

- [ ] **Step 2: Run the validator — final state**

Run:
```bash
uv run python scripts/validate_architecture.py
echo "exit: $?"
```
Expected: exit 0; "ALL CHECKS PASSED"; no structural-parser placeholder notice (binding is live).

- [ ] **Step 3: Confirm orchestrator/substrate still untouched**

Run:
```bash
SNAPSHOT=$(cat /tmp/m3-snapshot-sha)
git diff --name-only $SNAPSHOT HEAD | grep -E '^(scripts/(slice_orchestrator|cairn_query)/|mcp_servers/|commands/claude-code/(start-slice|integration-sweep)|checks/role_guard\.py|\.claude/(current-slice|features/|completed-slices/))' || echo "no orchestrator/substrate modifications"
```
Expected: `no orchestrator/substrate modifications`. The M3 doctrine is non-deleting; deletes are M4.

- [ ] **Step 4: Confirm M3 file inventory**

Run:
```bash
git diff --name-only $(cat /tmp/m3-snapshot-sha) HEAD
```
Expected: exactly these files modified or created (order may vary):
- `scripts/validate_architecture.py`
- `.claude/pipeline-substrate-registry.yaml`
- `docs/ARCHITECTURE.md`
- `.claude/handoff.md`
- `.claude/skills/cairn-tdd-feature/SKILL.md`
- `tests/unit/test_assertion_block_yaml_parser.py`
- `tests/unit/test_inv_001_scoped_cc_acceptance.py`
- `tests/unit/test_inv_003_tdd_siblings_tolerated.py`
- `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md`
- `docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md`
- `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-and-binding-fixes.md` (this plan)
- `tests/unit/test_invariant_assertions.py` (only if Task 3 Step 6 needed contract-update edits)

If anything else appears, investigate.

- [ ] **Step 5: Rewrite the handoff for M3-landed**

Edit `.claude/handoff.md`. Target: ≤440 tokens (~1760 bytes); structurally INV-002 must continue to pass. Replacement (substitute `<NEW_HEAD_SHA>` after the next commit; for now use a literal placeholder and substitute in Step 7):

```markdown
---
slice: design/cairn-shrink
phase: m3-landed
branch: design/cairn-shrink
as-of: 2026-05-06 <m3-handoff-pending-sha>
---

## State
M3 landed: bathwater audit, INV-002 parser fix (real YAML), INV-001 walker accepts scoped CC, INV-003 tolerates *-tdd siblings, role_guard simplification design, SKILL.md revision (four M2 findings). Validator exits 0; INV-002 binding live. Suite: 13 failed / 1267 passed (two M2 reds GREEN).

## Next
Run superpowers:writing-plans for M4: delete scripts/slice_orchestrator/, scripts/cairn_query/, mcp_servers/, kuzu+fastmcp deps, slice machinery, scope-guard.sh; implement role_guard per M3 design; author supersession ADRs (substrate, orchestrator, slice-close, artifact-preservation, d3-bypass, compression-bootstrap, pipeline-naming); amend INV-008/INV-010.

## Blocked / Pending
- M4 supersession ADRs unwritten.
- Consumer migration deferred to M6.
- ROLE_FOR_PHASE canonical-source migration (M4 picks location).

## Pointers
- docs/plans/2026-05-06-cairn-shrink-design.md — overall design.
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-and-binding-fixes.md — M3 plan.
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md — M4 inventory.
- docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md — M4 role_guard target.
- .claude/skills/cairn-tdd-feature/SKILL.md — dispatch skill.
- Branch design/cairn-shrink — WIP; merge in M5.
```

- [ ] **Step 6: Verify the new handoff still fits the budget AND structural rules**

Run:
```bash
python3 -c "b=open('.claude/handoff.md','rb').read(); t=(len(b)+3)//4; print(f'bytes={len(b)} approx_tokens={t} status={\"FITS\" if t<=440 else \"OVER\"}')"
grep -E '^##\s' .claude/handoff.md
uv run python scripts/validate_architecture.py 2>&1 | tail -5
```
Expected: `status=FITS`; the four required sections (State / Next / Blocked / Pending / Pointers) are present; validator exits 0.

- [ ] **Step 7: Stage, commit, then substitute the as-of SHA**

```bash
git add .claude/handoff.md
git commit -m "handoff: design/cairn-shrink — M3 landed, queue M4 next session"
NEW_SHA=$(git rev-parse HEAD)
echo "Substituting <m3-handoff-pending-sha> with $NEW_SHA"
```

Edit `.claude/handoff.md` line 5 — replace `<m3-handoff-pending-sha>` with the SHA from above. Then:

```bash
git add .claude/handoff.md
git commit -m "chore(m3-handoff-sha): substitute as-of SHA for M3-landed handoff"
```

- [ ] **Step 8: Final state verification**

Run:
```bash
git log --oneline -25
git status --short
uv run python scripts/validate_architecture.py 2>&1 | tail -3
echo "exit: $?"
```
Expected: log shows the M3 commit chain (handoff substitute, handoff, role_guard design, SKILL revision, INV-002 substitute, INV-002 activate, INV-003 fix, INV-003 RED, INV-001 fix, INV-001 RED, INV-002 parser fix, INV-002 RED, bathwater audit) plus the M3-plan commit. Working tree clean (modulo pre-existing untracked). Validator passes.

---

## Self-review checklist (run after writing the plan, before execution)

1. **Spec coverage from design §7 M3 deliverable:**
   - "Slice-by-slice review of past fixes (cf. §5)" — Task 2 ✓
   - "Fix `validate_architecture.py` parser gap so INV-002 binding is functional" — Task 3 (parser) + Task 6 (binding flip) ✓
   - "Document the `role_guard` simplification" — Task 8 ✓
   - "Migration plan with explicit do-not-regress commitments" — Task 2 §8 ✓
   - "INV-002 binding live" — Task 6 ✓
   - SKILL revision per M2 dogfood findings (handoff §Next item) — Task 7 ✓
   - INV-001 registry update for scoped CC (handoff §Next item) — Task 4 ✓
   - INV-003 topology accommodation for `*-tdd` agents (handoff §Next item) — Task 5 ✓

2. **Open questions not resolved (deferred to M4):**
   - ADR supersession authoring (design §7 — M3 or M4; deferred to M4 because the deletes happen in M4 and supersession ADRs land alongside their deletions).
   - Replacement location for ROLE_FOR_PHASE once `scripts/slice_orchestrator/core.py` dies (M4 chooses).
   - Tier-2 admission-criteria runtime LLM-judgment binding (design §1 noted as v2; not in M3 scope).

3. **Type/path consistency:**
   - All file paths absolute or repo-relative consistently ✓
   - `<feature-id>` vs `<m3-...>` scope consistently used in commit messages ✓
   - `binding-effective-from` literal `<m3-pending-effective-from>` is the unique substitution target in Task 6 ✓

4. **Known caveats (not blockers):**
   - Task 3 may force an in-place update to `tests/unit/test_invariant_assertions.py` if any existing tests bind to the flat-parser shape. This is intentional (the contract changes); update the tests to assert the new dict shape, commit alongside.
   - Task 4's INV-001 walker change handles all M2-era and M3-era commits on this branch; older bare prefixes still route to their original verifiers.
   - Task 6's two-step substitute (intermediate placeholder + post-commit SHA) mirrors the INV-001 precedent; if the operator prefers a single commit-amend dance, that's a 5-minute swap but loses the "matches precedent" benefit.
   - The `phase-2-skeptic write-timing on redispatch` memory item (issue #26) is not directly addressed in M3 — the bathwater audit notes it as M4 re-evaluation territory because the failure mode is git-diff-exclude-untracked which is orchestrator-bound.

5. **No placeholders:** every Step has either exact text/code or an exact command with expected output. Verified.

---

## Execution handoff

Plan complete and saved to `docs/plans/2026-05-06-cairn-shrink-m3-bathwater-and-binding-fixes.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Ideal for a 9-task plan with mixed code/doc work; the test-then-implement-then-commit pattern in Tasks 3-5 maps cleanly onto per-subagent batching.

2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Fine if you want to watch each binding fix flip RED→GREEN live.

Which approach?

# Cairn Shrink M4 — Delete + Relocate

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended for the deletion sections — independent commits) or superpowers:executing-plans (for the carry-forward + ADR + amendment sections — sequential dependencies). Steps use checkbox (`- [ ]`) syntax for tracking.

```
firmness: provisional
status: implementation plan — executes design §7 M4
date: 2026-05-07
scope: claude-code only (M5 plugin packaging deferred; M6 consumer migration deferred)
inputs:
  - docs/plans/2026-05-06-cairn-shrink-design.md (overall design)
  - docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md (carry-forward audit)
  - docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md (role_guard target)
  - .claude/handoff.md (M3-landed; queues M4)
```

**Goal:** Delete the orchestrator (`scripts/slice_orchestrator/`), substrate (`scripts/cairn_query/` + `mcp_servers/cairn_knowledge/`), slice machinery (`current-slice/`, `sweep.yaml`, `close_slice` ceremony, slice slash commands), and `scope-guard.sh`. Simplify `role_guard.py` per the M3 design. Author 7 supersession ADRs. Amend INV-002/INV-003 bindings; retire INV-008/INV-009/INV-010. Net: cairn at ~1/3 footprint, dispatch via `cairn-tdd-feature` skill the only path.

**Architecture:** Two threads woven together. **Thread 1** is carry-forward extraction (move `ROLE_FOR_PHASE` and `detect_superseded_test_signal` out of doomed modules to `.claude/agents/role-topology.yaml` and `scripts/lib/superseded_test_signal.py`) — must precede deletions. **Thread 2** is paperwork (7 supersession ADRs + INV amendments) — append-only ADR authoring + ARCHITECTURE.md hand-edits gated by `reversibility-guard.sh`'s frontmatter-only Edit policy and the bootstrap-style "documented architecture re-derivation" justification carried in commit messages. Mass deletion follows. `role_guard.py` simplification is TDD-shaped (write tests for the new `phase-{1..4}-tdd` slug shape; remove canonical-knowledge lockdown + Bash-token deny rule + `_CANONICAL_DENY_PATTERNS` / `ROLE_DENY_READ`). Validator (`scripts/validate_architecture.py`) is updated to read the relocated `ROLE_FOR_PHASE` and to drop INV-008/INV-009/INV-010 expectations.

**Tech Stack:** Python 3.11 (cairn standing dep set: pyyaml, pydantic, typer; kuzu/fastmcp/mistune dropped with the substrate). Bash hooks unchanged in shape (`reversibility-guard.sh`, `prepare-commit-msg.sh`, `reality-check.sh` carry forward; `scope-guard.sh` deleted). Markdown: ADRs and ARCHITECTURE.md via direct edits. uv-managed venv (`uv sync`, `uv run pytest`).

---

## Self-review summary (executor: confirm before starting)

This plan was self-reviewed at authoring against design §3, §5, §7, the M3 bathwater audit don't-regress list, and the role_guard simplification doc §1, §3, §5. Coverage gaps are listed in the **Out-of-scope follow-ups** section at the bottom — verify those are acceptable before starting.

### Carry-forward checklist (re-stated from M3 audit §8)

The plan must end with these all true:
- `READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}` preserved at `checks/role_guard.py:23` (kept as a constant even if no current rule uses it).
- `_envelope_patterns` parsing intact for JSON-array, JSON-object-with-`paths`, and legacy colon-separated shapes (with deprecation warning preserved on the legacy path).
- `_log_grant` writing to `.claude/envelope-grants.log` preserved (slice-id label changed to a generic identifier; mechanism unchanged).
- `detect_superseded_test_signal` callable from `scripts/lib/superseded_test_signal.py` with semantics byte-identical to the slice_orchestrator definition.
- `ADR_EDITORIAL_FIX=1` env-var handling at `checks/reversibility-guard.sh:88-98` unchanged (we don't touch that file).
- `V1_ASSERTION_TYPES` allowlist at `tests/unit/test_invariant_assertions.py:1116` includes `structural-parser` (carried from M3) and contains no orphan entries.
- `INV-002(a)` structural-parser binding at `docs/ARCHITECTURE.md:24-40` continues to validate (parser landed M3; we don't touch it).
- Per-phase agent frontmatter `tools:` allowlist mechanism preserved on the surviving `phase-{1..4}-tdd.md` + `triager-tdd.md` files.
- The single-quote-regex YAML-safety guidance survives in `.claude/agents/phase-2-tdd.md` (verbatim from `phase-2-skeptic.md` if needed; we delete the legacy file last).

---

## Section A — Carry-forward extraction

These tasks MUST land before Section E mass deletions. They preserve two callable surfaces that doomed modules currently host.

### Task A1: Capture pre-M4 baseline failure list

**Files:**
- Create: `/tmp/m4-baseline-failures.txt` (transient; not committed)

- [ ] **Step 1: Run the suite and capture the failure block**

```bash
uv run pytest -q --tb=no -rf 2>&1 | tee /tmp/m4-baseline-failures.txt
```

Expected: 1290 passed, 2 failed (per the M3-landed handoff: pre-M2 extractor reds remain). Save the file. If the count differs by more than ±5 tests, abort and investigate before proceeding — the plan's regression budget assumes the M3 baseline.

- [ ] **Step 2: Snapshot HEAD for end-of-M4 diff**

```bash
git rev-parse HEAD > /tmp/m4-snapshot-sha.txt
```

No commit. This is M4's anchor SHA; Section G's verification compares the post-M4 suite against this baseline.

---

### Task A2: Relocate `ROLE_FOR_PHASE` to `.claude/agents/role-topology.yaml`

**Files:**
- Create: `.claude/agents/role-topology.yaml`
- Modify: `scripts/validate_architecture.py:411-434` (`_ROLE_SHORTHAND_TO_SLUG`, `_extract_role_for_phase`)
- Modify: `tests/unit/test_inv_003_phase_topology.py:181-220, :549` (mutation tests + `from slice_orchestrator.core import ROLE_FOR_PHASE`)
- Test: re-uses `tests/unit/test_inv_003_phase_topology.py`

**Why:** `scripts/slice_orchestrator/core.py:42` (the current authoritative source) is being deleted in Section E. The validator's `validate_phase_topology` reads it via `_extract_role_for_phase` — that function dies with its target. The new authoritative source is `.claude/agents/role-topology.yaml`, parsed by `pyyaml`.

**Slug update:** the legacy slugs (`phase-1-writer`/`phase-2-skeptic`/`phase-3-implementer`/`phase-4-integrator`) are also being deleted (Section E deletes the legacy agent files). The new YAML uses TDD slugs.

- [ ] **Step 1: Write the new YAML source**

```bash
cat > .claude/agents/role-topology.yaml <<'EOF'
# Authoritative phase-ordinal → role-slug mapping for cairn-tdd-feature dispatch.
# Consumed by scripts/validate_architecture.py:validate_phase_topology (INV-003 binding).
# Each row's slug must match a file at .claude/agents/<slug>.md.

phases:
  1: phase-1-tdd
  2: phase-2-tdd
  3: phase-3-tdd
  4: phase-4-tdd
EOF
```

- [ ] **Step 2: Write the failing test for new validator entry-point**

Edit `tests/unit/test_inv_003_phase_topology.py`. Replace the `from slice_orchestrator.core import ROLE_FOR_PHASE` import (line 549) and the surrounding mutation-test scaffolding (lines 181-220 — these mutate `core.py` text) with YAML-source mutations. Concrete shape:

```python
# Replace tests/unit/test_inv_003_phase_topology.py's mutation-helper section
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROLE_TOPOLOGY_PATH = REPO_ROOT / ".claude" / "agents" / "role-topology.yaml"

def _read_role_for_phase() -> dict[int, str]:
    return yaml.safe_load(ROLE_TOPOLOGY_PATH.read_text())["phases"]

def test_role_for_phase_drops_phase_4_must_fail(tmp_path, monkeypatch):
    """Mutating role-topology.yaml to drop phase 4 must trip validate_phase_topology."""
    fake = tmp_path / "role-topology.yaml"
    original = ROLE_TOPOLOGY_PATH.read_text()
    mutated = original.replace("4: phase-4-tdd\n", "")
    fake.write_text(mutated)
    monkeypatch.setattr(
        "validate_architecture.ROLE_TOPOLOGY_PATH", fake
    )
    failures = validate_architecture.validate_phase_topology(...)  # signature unchanged
    assert failures, "Dropping phase-4 from role-topology.yaml must fail"

def test_role_for_phase_renames_phase_2_must_fail(tmp_path, monkeypatch):
    """Renaming phase-2-tdd in role-topology.yaml must trip validate_phase_topology."""
    fake = tmp_path / "role-topology.yaml"
    original = ROLE_TOPOLOGY_PATH.read_text()
    mutated = original.replace("2: phase-2-tdd", "2: phase-2-renamed-tdd")
    fake.write_text(mutated)
    monkeypatch.setattr(
        "validate_architecture.ROLE_TOPOLOGY_PATH", fake
    )
    failures = validate_architecture.validate_phase_topology(...)
    assert failures, "Renaming phase-2-tdd in role-topology.yaml must fail"
```

(The exact `validate_phase_topology` call shape is dictated by the existing function signature in `scripts/validate_architecture.py`. The test that imports `ROLE_FOR_PHASE` from `slice_orchestrator.core` at line 549 is replaced by `_read_role_for_phase()` calls.)

- [ ] **Step 3: Run the test — expect FAIL on missing `ROLE_TOPOLOGY_PATH`**

```bash
uv run pytest tests/unit/test_inv_003_phase_topology.py::test_role_for_phase_drops_phase_4_must_fail -v
```

Expected: FAIL with `AttributeError: module 'validate_architecture' has no attribute 'ROLE_TOPOLOGY_PATH'`.

- [ ] **Step 4: Update `scripts/validate_architecture.py` to read the YAML**

Replace `_extract_role_for_phase` (lines 419-434) with a YAML-reader. Keep `_ROLE_SHORTHAND_TO_SLUG` (lines 411-416) but remap to the new TDD slugs:

```python
ROLE_TOPOLOGY_PATH = Path(__file__).resolve().parent.parent / ".claude" / "agents" / "role-topology.yaml"

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
        if isinstance(k, int) and isinstance(v, str) and re.match(r"^phase-\d+-[a-z][a-z-]*$", v):
            result.add((k, v))
    return result if result else None
```

Also update any call site in `validate_phase_topology` that passes `core.py` text — replace with `_extract_role_for_phase()` (no arg) and grep the rest of the file for stray `slice_orchestrator/core.py` mentions to update them to the YAML path.

- [ ] **Step 5: Run the suite — confirm tests pass and no INV-003 regression**

```bash
uv run pytest tests/unit/test_inv_003_phase_topology.py -v
```

Expected: PASS for the new mutation tests; INV-003 phase-topology cross-reference still validates (the four agent files `phase-{1..4}-tdd.md` exist; Phase Skill Guide table is consistent).

- [ ] **Step 6: Commit**

```bash
git add .claude/agents/role-topology.yaml scripts/validate_architecture.py tests/unit/test_inv_003_phase_topology.py
git commit -m "chore(m4): relocate ROLE_FOR_PHASE to .claude/agents/role-topology.yaml

scripts/slice_orchestrator/core.py is being deleted in M4.
Validator's validate_phase_topology now reads role-topology.yaml
via pyyaml. Slugs updated to TDD shape (phase-{1..4}-tdd).
INV-003 binding survives intact across the relocation."
```

---

### Task A3: Relocate `detect_superseded_test_signal` to `scripts/lib/superseded_test_signal.py`

**Files:**
- Create: `scripts/lib/superseded_test_signal.py`
- Modify: `tests/unit/test_triager_superseded_heuristic.py:22, :260, :311, :355` (import sites)
- Read: `scripts/slice_orchestrator/core.py:406-...` (current definition; copy verbatim minus any orchestrator-bound imports)

**Why:** Bathwater audit §2 requires this function survives M4 as a callable. The slice_orchestrator package dies. Relocating to `scripts/lib/` (alongside `lib/invariant_id_extractor.py`) keeps the test pin valid and the function reachable for future runtime callers.

- [ ] **Step 1: Read the current definition**

```bash
sed -n '400,470p' scripts/slice_orchestrator/core.py | head -80
```

(Confirm the function body is self-contained — no imports from sibling slice_orchestrator modules. If it imports from `slice_orchestrator.dispatch` or similar, those imports must be inlined or the import made local. Audit before copying.)

- [ ] **Step 2: Write the relocated module**

```python
# scripts/lib/superseded_test_signal.py
"""Triager helper: detect a RAISE_ISSUE pointing at tests superseded by a firm contract.

Pure function. Re-located from scripts/slice_orchestrator/core.py during the
M4 cairn-shrink (2026-05-07). The triager-tdd agent prose references this
function as the canonical heuristic for biasing toward ESCALATE_TO_USER instead
of RE_DISPATCH-to-Phase-2 when a recently-firm contract supersedes the tests
named in the issue.

Tests pin the semantics at tests/unit/test_triager_superseded_heuristic.py.
"""
from __future__ import annotations

# (paste the function body verbatim from scripts/slice_orchestrator/core.py)

def detect_superseded_test_signal(...) -> ...:
    ...
```

- [ ] **Step 3: Update the test imports**

Edit `tests/unit/test_triager_superseded_heuristic.py`. Replace each `import slice_orchestrator as so` + `so.detect_superseded_test_signal` reference with:

```python
from lib.superseded_test_signal import detect_superseded_test_signal
```

(Keep the existing assertions and parametrize cases unchanged — the function semantics are byte-identical.)

Also, line 26 in that test file (the comment `"from slice_orchestrator"`) needs updating to `"from lib.superseded_test_signal"`.

- [ ] **Step 4: Run the test — expect PASS**

```bash
uv run pytest tests/unit/test_triager_superseded_heuristic.py -v
```

Expected: PASS, all parametrized cases. If the function had hidden imports from `slice_orchestrator.dispatch` or similar, the test will fail with `ImportError`; resolve by inlining or carrying additional helpers to `scripts/lib/`.

- [ ] **Step 5: Verify the existing slice_orchestrator definition still works (transition state)**

```bash
uv run pytest tests/unit/test_triager_superseded_heuristic.py -v
uv run python -c "import slice_orchestrator as so; print(so.detect_superseded_test_signal.__module__)"
```

Both must succeed. The slice_orchestrator copy is dead-but-loaded; Section E deletes it.

- [ ] **Step 6: Update triager-tdd agent prose to reference the new path**

Edit `.claude/agents/triager-tdd.md`. Find the line referencing `slice_orchestrator.core.detect_superseded_test_signal` (or similar prose link) and replace with `scripts/lib/superseded_test_signal.py::detect_superseded_test_signal`. If no such reference exists in triager-tdd.md, skip this step (the function is implicitly referenced via the test pin, which is enough).

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/superseded_test_signal.py tests/unit/test_triager_superseded_heuristic.py .claude/agents/triager-tdd.md
git commit -m "chore(m4): relocate detect_superseded_test_signal to scripts/lib/

scripts/slice_orchestrator/ is being deleted in M4. The
detect_superseded_test_signal heuristic is required carry-forward
per docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.
Test pin and triager-tdd agent prose updated."
```

---

## Section B — Supersession ADRs

Seven new ADR files. Each retires one ADR from design §7. **Order matters** for the cross-reference fields: build the dependency-free supersessions first, then those that reference earlier supersessions.

**Convention:** new ADR ids follow the `<predecessor>-superseded` pattern (or shorter slug if cleaner). `status: firm`. `supersedes:` field names the predecessor; the predecessor's frontmatter gets `status: superseded` + `superseded-by: <new-id>` via Edit (allowed by reversibility-guard's frontmatter-only policy).

**Standard ADR template** for each task in this section:

```markdown
---
id: <new-id>
name: <human label>
status: firm
firmness: firm
supersedes: <predecessor-id>
date: 2026-05-07
program: cairn-shrink-m4
---

# <Human Label>

## Context

The <predecessor> ADR governed <subsystem> under cairn's pre-shrink architecture.
Per docs/plans/2026-05-06-cairn-shrink-design.md §3.2 / §7, that subsystem retires
in M4 (2026-05-07). This ADR records the supersession.

## Decision

<predecessor-id> is superseded. Its provisions are retired; the surviving
behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- <subsystem> code, tests, and configuration are deleted in the M4 sweep.
- Any invariant bound to the retired subsystem (see ARCHITECTURE.md) is
  retired or rebound in lockstep with this M4 commit series.
- Consumer projects continuing to reference <subsystem> must migrate per
  the M5 plugin packaging plan (out of M4 scope).

## References

- docs/plans/2026-05-06-cairn-shrink-design.md §3.2, §7
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
```

The body is short by design — supersession ADRs document the retirement decision, not the original design they replace. Predecessor ADRs are preserved verbatim as historical reference.

---

### Task B1: Author `cairn-substrate-and-fastmcp-superseded` ADR

**Files:**
- Create: `docs/adr/cairn-substrate-and-fastmcp-superseded.md`
- Modify: `docs/adr/cairn-substrate-and-fastmcp.md` (frontmatter only — `status:` line)

- [ ] **Step 1: Write the new ADR**

Use the standard template above. Predecessor: `cairn-substrate-and-fastmcp`. ID: `cairn-substrate-and-fastmcp-superseded`. Subsystem-specific lines:

```
## Decision

cairn-substrate-and-fastmcp is superseded. The typed-knowledge graph
(scripts/cairn_query/), the MCP wrapper (mcp_servers/cairn_knowledge/),
the kuzu and fastmcp deps, and the substrate's INV-010 enforcement contract
all retire in M4. The substrate's cost-justification dissolves with targeted
reads + in-brief context; the typed-records value is not load-bearing for
solo-dev TDD and may be re-introduced if a real graph-class query emerges
that grep cannot satisfy.

## Consequences

- scripts/cairn_query/ deleted (~1900 LOC).
- mcp_servers/cairn_knowledge/ deleted (JSON-RPC dispatcher).
- kuzu and fastmcp pruned from pyproject.toml; uv.lock regenerated.
- INV-010 retires (substrate-mediated knowledge access). Removed from
  ARCHITECTURE.md.
- role_guard.py's _CANONICAL_DENY_PATTERNS / ROLE_DENY_READ deleted (no
  substrate to force agents toward).
```

- [ ] **Step 2: Edit predecessor frontmatter**

Open `docs/adr/cairn-substrate-and-fastmcp.md`. Locate the `status:` line. Edit to:

```yaml
status: superseded
superseded-by: cairn-substrate-and-fastmcp-superseded
```

(`reversibility-guard.sh:88-98` allows this Edit because `old_string`'s first line begins with `status:`.)

- [ ] **Step 3: Commit**

```bash
git add docs/adr/cairn-substrate-and-fastmcp-superseded.md docs/adr/cairn-substrate-and-fastmcp.md
git commit -m "docs(m4): supersede cairn-substrate-and-fastmcp

Substrate retires per docs/plans/2026-05-06-cairn-shrink-design.md §3.2.
INV-010 retires in lockstep (Section C). Code deletion in Section E."
```

---

### Task B2: Author `orchestrator-observability-superseded` ADR

**Files:**
- Create: `docs/adr/orchestrator-observability-superseded.md`
- Modify: `docs/adr/orchestrator-observability.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR** (template; predecessor `orchestrator-observability`).

Subsystem-specific lines:

```
## Decision

orchestrator-observability is superseded. The B2/B3-hybrid schema, the
canonical .claude/orchestrator-debug/ output shape, the heartbeat liveness
file, and the retention tripwires all retire with the orchestrator (M4).
Cost data remains observable via Anthropic primitives natively; no cairn-
specific writer is required.

## Consequences

- .claude/orchestrator-debug/ machinery deleted.
- index.jsonl + <slug>-result.{json,md} writers deleted with
  scripts/slice_orchestrator/.
- INV-009's cost-threshold mechanization retires (advisory-only at M3
  drop; see Task B6 for cost-per-slice-budget amendment).
```

- [ ] **Step 2: Edit predecessor frontmatter** — `status: superseded`, `superseded-by: orchestrator-observability-superseded`.

- [ ] **Step 3: Commit**

```bash
git add docs/adr/orchestrator-observability-superseded.md docs/adr/orchestrator-observability.md
git commit -m "docs(m4): supersede orchestrator-observability"
```

---

### Task B3: Author `slice-close-contract-superseded` ADR

**Files:**
- Create: `docs/adr/slice-close-contract-superseded.md`
- Modify: `docs/adr/slice-close-contract.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR.** Subsystem-specific lines:

```
## Decision

slice-close-contract is superseded. The close_slice ceremony — its four-signal
idempotence precondition, its sole-producer-of-slice:complete-commit role, its
cross-slice slug-collision tripwire, and its 13-row resume reconciliation
matrix — all retire with the slice unit-of-work (M4). The dispatch skill
(.claude/skills/cairn-tdd-feature/SKILL.md) commits each phase's writes
natively; there is no slice to close.

## Consequences

- close_slice and commit_phase_handoff functions deleted.
- INV-008 retires (slice-close lifecycle invariant).
- INV-002(c) sub-clause retires (was bound to close_slice idempotence
  via test_close_slice_hardened.py).
- 13-row resume matrix deleted; manual re-run is the dispatch-path
  equivalent.
```

- [ ] **Step 2: Edit predecessor frontmatter.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "docs(m4): supersede slice-close-contract"
```

---

### Task B4: Author `slice-artifact-preservation-superseded` ADR

**Files:**
- Create: `docs/adr/slice-artifact-preservation-superseded.md`
- Modify: `docs/adr/slice-artifact-preservation.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR.** Subsystem-specific lines:

```
## Decision

slice-artifact-preservation is superseded. The _copy_artifacts_to_sweep_results
function, the .claude/sweep-results/<slug>/artifacts/ output shape, and the
F5-tolerance copy-before-wipe contract all retire with close_slice (M4).
Git history of merged feature branches preserves the equivalent forensic
surface.

## Consequences

- .claude/sweep-results/ machinery deleted.
- _copy_artifacts_to_sweep_results function deleted.
- INV-008 sub-clause (d) retires in lockstep.
```

- [ ] **Step 2: Edit predecessor frontmatter.**

- [ ] **Step 3: Commit.**

---

### Task B5: Author `d3-bypass-classification-superseded` ADR

**Files:**
- Create: `docs/adr/d3-bypass-classification-superseded.md`
- Modify: `docs/adr/d3-bypass-classification.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR.** Subsystem-specific lines:

```
## Decision

d3-bypass-classification is superseded. With the slice machinery retired and
no D3 structural-immutability gate in the dispatch path, the bypass log shape
and ADR_D3_BYPASS=1 escape have no enforcement target. Operator judgment + the
pre-commit validator subsume the gate.

## Consequences

- .claude/d3-bypasses.log retired.
- .claude/d1-bypasses.log retired in tandem (D1 gate dies with
  /refresh-architecture; see Task E5).
- ADR_D3_BYPASS env-var no-op'd (no consumer remains).
```

- [ ] **Step 2: Edit predecessor frontmatter.**

- [ ] **Step 3: Commit.**

---

### Task B6: Author `compression-infrastructure-bootstrap-superseded` ADR

**Files:**
- Create: `docs/adr/compression-infrastructure-bootstrap-superseded.md`
- Modify: `docs/adr/compression-infrastructure-bootstrap.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR.** Subsystem-specific lines:

```
## Decision

compression-infrastructure-bootstrap is superseded. The compression program's
infrastructure — phase-3 envelope-driven write asymmetry under role_guard,
the canonical-knowledge MCP-forcing gate, AGENT_ENVELOPE as a JSON-array
write-allowlist primitive — survives in spirit. The dispatch skill's plan-doc
frontmatter carries the envelope; role_guard enforces phase-3 writes against
it. The MCP-forcing gate retires with the substrate.

## Consequences

- Phase-3 asymmetry preserved (no static ROLE_POLICIES entry; envelope-driven).
- AGENT_ENVELOPE shapes (JSON-array, JSON-object-with-paths, legacy
  colon-separated) preserved per the M3 role_guard simplification doc §5.
- INV-003 narrow named exception clause retires (compression's orchestrator
  dispatch retires; phase-role enforcement now lives in the dispatch skill
  + role_guard, no longer scoped to "compression feature's orchestrator
  dispatch"); see Section C INV-003 amendment.
```

- [ ] **Step 2: Edit predecessor frontmatter.**

- [ ] **Step 3: Commit.**

---

### Task B7: Author `pipeline-substrate-naming-superseded` ADR

**Files:**
- Create: `docs/adr/pipeline-substrate-naming-superseded.md`
- Modify: `docs/adr/pipeline-substrate-naming.md` (frontmatter only)

- [ ] **Step 1: Write the new ADR.** Subsystem-specific lines:

```
## Decision

pipeline-substrate-naming is superseded. The substrate-commit-class
authorization mechanism (.claude/pipeline-substrate-registry.yaml + the
"three legitimate commit classes" extension to INV-001) retires with the
pipeline machinery (M4). INV-001's binding shrinks to the two legitimate
classes named in bootstrap-exception (decision and slice flows), with
"slice" reinterpreted as "any commit produced by the cairn-tdd-feature
dispatch skill."

## Consequences

- .claude/pipeline-substrate-registry.yaml retired.
- INV-001 binding-effective-from anchor unchanged (2fb83f6); the registry
  reference in the binding block is updated to point at the dispatch
  skill's commit convention or removed entirely (Section C amendment).
- The D4 follow-up tracked in the M3 handoff (design:/plan: registry
  bypass-of-ADR-path) is closed by this supersession (the registry no
  longer exists to drift from).
```

- [ ] **Step 2: Edit predecessor frontmatter.**

- [ ] **Step 3: Commit.**

---

## Section C — Architecture amendments

ARCHITECTURE.md is a derived view (line 9: "regenerated by `/refresh-architecture` and validated by `scripts/validate_architecture.py`"). `/refresh-architecture` is being deleted in M4 (Section E), so the practical path is direct hand-edits. Each task's commit message cites the supersession ADR(s) that justify the change, in the spirit of bootstrap commits.

These edits MUST land before Section E mass deletions. The validator (`scripts/validate_architecture.py`) currently asserts INV-008 / INV-010 binding blocks exist; deletions without amendments would trip the validator at every commit until the machinery is gone too.

### Task C1: Retire INV-008 from ARCHITECTURE.md

**Files:**
- Modify: `docs/ARCHITECTURE.md:85-93` (INV-008 prose + binding block)
- Modify: `docs/ARCHITECTURE.md:164` (the slice-close-lifecycle paragraph in §Boundaries)
- Modify: `tests/unit/test_inv_002_inv_008_architecture_blocks.py` (drop INV-008 expectations)

- [ ] **Step 1: Replace INV-008 prose + binding block with a retirement marker**

Edit `docs/ARCHITECTURE.md`. Replace lines 85-93 with:

```markdown
**INV-008** Retired by ADR `slice-close-contract-superseded` (M4 cairn-shrink, 2026-05-07). The orchestrator's slice-close lifecycle no longer exists; per-phase commits via the cairn-tdd-feature dispatch skill replace the close_slice ceremony, and slice-artifact preservation is subsumed by git history of merged branches. (slice-close-contract-superseded; slice-artifact-preservation-superseded)
```

(No binding block. The validator's INV-008 expectation is removed in Task C5.)

- [ ] **Step 2: Update the §Boundaries slice-close-lifecycle paragraph**

The paragraph at line 164 starts "**Slice-close lifecycle (slice-close-contract, firm; orchestrator-observability, provisional).**" Replace with:

```markdown
**Slice-close lifecycle — retired (slice-close-contract-superseded, orchestrator-observability-superseded, 2026-05-07).** The pre-M4 close_slice contract and orchestrator-observability schema retire with the slice machinery. The dispatch skill (`.claude/skills/cairn-tdd-feature/SKILL.md`) commits each phase's writes by name; there is no separate close ceremony, no .claude/orchestrator-debug/ output, and no resume reconciliation matrix.
```

- [ ] **Step 3: Update the existing INV-002+INV-008 architecture-blocks test**

Edit `tests/unit/test_inv_002_inv_008_architecture_blocks.py`. Drop the INV-008 assertions; rename to `test_inv_002_architecture_block.py` (or keep the file name and just narrow scope) — pick whichever causes minimum churn. Test must continue to pin INV-002(a)'s structural-parser block at line 24-40.

- [ ] **Step 4: Run the validator and confirm the retirement marker is accepted**

```bash
uv run python scripts/validate_architecture.py
```

Expected: passes (after Task C5 updates the validator's INV-008 expectation). If this step is run before C5, expect a "missing INV-008 binding block" failure — that's expected and is unblocked by C5. Order C1 → C5 → re-verify.

- [ ] **Step 5: Commit**

```bash
git add docs/ARCHITECTURE.md tests/unit/test_inv_002_inv_008_architecture_blocks.py
git commit -m "docs(m4): retire INV-008 — slice-close-contract superseded

Per docs/adr/slice-close-contract-superseded.md and
docs/adr/slice-artifact-preservation-superseded.md (M4).
The four properties INV-008 bound (idempotent close, sole-producer
commit, slug-collision tripwire, copy-before-wipe) all die with the
close_slice ceremony. Boundaries paragraph updated."
```

---

### Task C2: Retire INV-010 from ARCHITECTURE.md

**Files:**
- Modify: `docs/ARCHITECTURE.md:103-111` (INV-010 prose + binding block)

- [ ] **Step 1: Replace INV-010 prose + binding block with a retirement marker**

Edit `docs/ARCHITECTURE.md`. Replace lines 103-111 with:

```markdown
**INV-010** Retired by ADR `cairn-substrate-and-fastmcp-superseded` (M4 cairn-shrink, 2026-05-07). The cairn-knowledge MCP server, scripts/cairn_query/, and the canonical-knowledge read-class lockdown table retire with the substrate. Phase agents read canonical sources directly within their per-role write-path allowlists; the dispatch skill quotes relevant ADR/invariant snippets in spawn prompts to recover the substrate's targeted-context value. (cairn-substrate-and-fastmcp-superseded; compression-infrastructure-bootstrap-superseded)
```

- [ ] **Step 2: Run the validator and confirm**

```bash
uv run python scripts/validate_architecture.py
```

Expected: passes (after Task C5).

- [ ] **Step 3: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs(m4): retire INV-010 — cairn-substrate-and-fastmcp superseded

Substrate retires (Section E deletes scripts/cairn_query/ and
mcp_servers/cairn_knowledge/). Read-class lockdown removed from
role_guard.py in Section D."
```

---

### Task C3: Retire INV-009 (advisory) from ARCHITECTURE.md

**Files:**
- Modify: `docs/ARCHITECTURE.md:95-101` (INV-009 prose + binding block)

INV-009 was already advisory-only (thresholds `None` per the prose). Per design §5 it drops entirely.

- [ ] **Step 1: Replace with retirement marker**

Edit `docs/ARCHITECTURE.md`. Replace lines 95-101 with:

```markdown
**INV-009** Retired (advisory-only at introduction; never promoted to firm; M4 cairn-shrink, 2026-05-07). Per-slice cost telemetry retires with the slice unit-of-work; cost data remains observable natively via Claude Code's session telemetry. ADR `cost-per-slice-budget` is amended (Task B6 / Task C-followup) to mark the threshold mechanization deprecated. (cost-per-slice-budget; orchestrator-observability-superseded)
```

- [ ] **Step 2: Validator + commit**

```bash
uv run python scripts/validate_architecture.py
git add docs/ARCHITECTURE.md
git commit -m "docs(m4): retire INV-009 — cost-threshold trip never promoted to firm"
```

---

### Task C4: Amend INV-002 — drop sub-clauses (b) and (c)

**Files:**
- Modify: `docs/ARCHITECTURE.md:22-40` (INV-002 prose + binding block)

INV-002 sub-clause (b) bound to `commands/claude-code/catchup.full.md`'s Tier-1 list pin (test_catchup_tier1_list_pinned.py); that command is being deleted in Section E. Sub-clause (c) bound to `/start-slice` wiping `.claude/current-slice/` (test_close_slice_hardened.py); that ceremony retires with the orchestrator. Sub-clause (a) — the structural-parser handoff binding — survives and stays.

- [ ] **Step 1: Edit INV-002 prose to retain only sub-clause (a)**

Replace lines 22-23 (the prose paragraph) with:

```markdown
**INV-002** Session-to-session context transfer obeys structural discipline on `.claude/handoff.md`: a pointer artifact bounded at 150–400 tokens with fixed section structure (`State`, `Next`, `Blocked / Pending`, `Pointers`; `Features` optional) and a forbidden-sections list (literal: "What This Session Was About", "What Was Accomplished", "Surprises or Discoveries", "Self-Check"; regex: `^##\s+(Lessons|Reflection|Notes)\b`). True machine-checkable binding via `structural-parser` assertion type defined by `invariant-binding-strategy` (D1, D4); per-feature plan docs at `docs/plans/<feature>.md` carry session-spanning context that previously spread across `/catchup`'s Tier-1 list and `/start-slice`'s current-slice/ wipe (both retired in M4 cairn-shrink, 2026-05-07). (context-discipline-protocol; invariant-binding-strategy; slice-close-contract-superseded)
```

(The binding block at lines 24-40 stays unchanged. The `binding-effective-from: 1c4d2f5a...` pin is the M3 anchor — keep it.)

- [ ] **Step 2: Run validator + structural-parser test**

```bash
uv run python scripts/validate_architecture.py
uv run pytest tests/unit/test_inv_002_structural_parser.py -v
```

Expected: PASS (the binding is unchanged; only the prose narrowed).

- [ ] **Step 3: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs(m4): amend INV-002 — drop sub-clauses (b)/(c) retiring with slice machinery

Sub-clause (a) handoff structural binding survives (M3-landed binding
unchanged at line 24-40). Sub-clauses (b) and (c) bound to /catchup
and /start-slice respectively — both commands retire in Section E."
```

---

### Task C5: Amend INV-003 cross-reference set + amend INV-007 binding target

**Files:**
- Modify: `docs/ARCHITECTURE.md:42-49` (INV-003 binding block)
- Modify: `docs/ARCHITECTURE.md:75-83` (INV-007 binding block)
- Modify: `scripts/validate_architecture.py` (drop INV-008/INV-009/INV-010 from the expected-set; update INV-003's source-of-truth path; update INV-007's grep target)

- [ ] **Step 1: Update INV-003 binding-block description**

Replace the `description:` line in INV-003's binding block (line 48) with:

```yaml
description: "Three-way cross-reference phase-topology binding: (phase_ordinal, role_slug) topology agreed across .claude/agents/role-topology.yaml (authoritative), Phase Skill Guide (docs/operational-reference.md), and agent prompt filenames (.claude/agents/phase-{1..4}-tdd.md). validate_phase_topology() in scripts/validate_architecture.py is the binding entry point; tests/unit/test_inv_003_phase_topology.py is the binding test suite. ROLE_DENY_READ cross-reference dropped (read-class lockdown retired with the substrate; see INV-010 retirement)."
```

(Cross-reference shrinks from quad to triple — drop ROLE_DENY_READ.)

Also update the prose paragraph (line 42) to drop the "compression feature's orchestrator dispatch" exception clause; replace with:

```markdown
**INV-003** Every cairn-tdd feature runs through exactly four phases in order — Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration (Auditor). Each phase's role and anti-behaviors are surfaced in the agent prompts at `.claude/agents/phase-{1..4}-tdd.md` and the Phase Skill Guide section of `docs/operational-reference.md`. Phase count, names, and role assignments are locked; changes require a superseding ADR. Role-keyed write-path enforcement via `checks/role_guard.py` is preserved across the M4 shrink (envelope-grant escape and `READ_CLASS_TOOLS` constants intact). (phase-lock-and-role-declaration; phase-pipeline-evaluation; compression-infrastructure-bootstrap-superseded)
```

- [ ] **Step 2: Update INV-007 binding target**

INV-007's binding (line 78-82) greps `\.claude/features/` against `commands/claude-code/handoff.full.md`. That file is being deleted in Section E. Retarget to a surviving doc — `.claude/skills/cairn-tdd-feature/SKILL.md`. Replace the binding block:

```yaml
type: grep
pattern: '\.claude/features/'
target: ".claude/skills/cairn-tdd-feature/SKILL.md"
expect: match
```

If the SKILL.md doesn't currently grep-match `\.claude/features/`, add a one-line reference to it in the SKILL.md prose (e.g., in the "Workspace conventions" section: "Feature registry at `.claude/features/<id>.yaml` is consulted by Phase 1 for cross-feature context."). Verify the test passes after this small addition.

Alternative: retire INV-007 entirely. Per design §3, feature-slice-model is **Amended** (features stay; slices retire), so the invariant is still meaningful. Prefer retargeting over retirement.

- [ ] **Step 3: Update validator's expected-invariant set**

Edit `scripts/validate_architecture.py`. The validator likely has an `EXPECTED_INVARIANTS` constant or equivalent (grep for `INV-008`, `INV-009`, `INV-010` in the file). Drop those three from the set. Run the validator afterward to confirm.

```bash
grep -n 'INV-008\|INV-009\|INV-010' scripts/validate_architecture.py
```

Edit each hit. Likely places: an enumeration list, a per-invariant verifier function table, and possibly INV-008/INV-010-specific verification helpers. Delete those helpers if any.

- [ ] **Step 4: Run validator + INV-003 test**

```bash
uv run python scripts/validate_architecture.py
uv run pytest tests/unit/test_inv_003_phase_topology.py -v
uv run pytest tests/unit/test_invariant_assertions.py -v
```

All three must pass. If the assertions test fails on a missing `structural-parser` allowlist entry or similar, it's the M3 follow-up flagged in memory `v1_assertion_types_allowlist.md` — verify the allowlist already includes `structural-parser` (M3 should have added it at `tests/unit/test_invariant_assertions.py:1116`).

- [ ] **Step 5: Commit**

```bash
git add docs/ARCHITECTURE.md scripts/validate_architecture.py .claude/skills/cairn-tdd-feature/SKILL.md
git commit -m "docs(m4): amend INV-003 + INV-007; validator drops INV-008/9/10 expectations

INV-003 quad → triple cross-reference (ROLE_DENY_READ dropped with
the substrate). INV-007 retargets from handoff.full.md (deleted) to
SKILL.md. Validator's expected-invariant set narrows."
```

---

### Task C6: Update ARCHITECTURE.md preamble

**Files:**
- Modify: `docs/ARCHITECTURE.md:9`

- [ ] **Step 1: Update the regeneration disclaimer**

Replace line 9 with:

```markdown
This document is a **derived view** synthesized from the ADR corpus in `docs/adr/`. It is validated by `scripts/validate_architecture.py`. Manual edits are permitted as part of an ADR-supersession-justified commit; no automated `/refresh-architecture` step exists post-M4 cairn-shrink.
```

- [ ] **Step 2: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs(m4): drop /refresh-architecture reference from ARCHITECTURE.md preamble

The slash command retires in Section E (per design §3.2). Manual
ADR-justified edits replace the automated refresh."
```

---

## Section D — `role_guard.py` simplification (TDD)

Per `docs/plans/2026-05-06-cairn-shrink-m3-role-guard-simplification.md` §1, §3, §5. Drop `_CANONICAL_DENY_PATTERNS`, `ROLE_DENY_READ`, the Bash-token deny block, and the `_log_grant` slice-id reference. Update `ROLE_POLICIES` to TDD slugs + `.claude/skill-runs/` paths. Preserve `READ_CLASS_TOOLS`, `_envelope_patterns`, `_log_grant` mechanism, and the phase-3 envelope-only asymmetry.

### Task D1: Write the failing test for the new `role_guard.py` shape

**Files:**
- Modify: `tests/unit/test_role_guard.py` (new test cases) — or create a focused `tests/unit/test_role_guard_post_m4.py` if the existing file is too tied to the old shape

- [ ] **Step 1: Inspect the current `test_role_guard*.py` files for which to update vs delete**

```bash
ls -1 tests/unit/test_role_guard*.py
grep -l "ROLE_DENY_READ\|_CANONICAL_DENY_PATTERNS\|phase-1-writer\|phase-2-skeptic\|phase-3-implementer\|phase-4-integrator" tests/unit/test_role_guard*.py
```

Tests bound to the dying shape (`test_role_guard_phase_1_lockdown.py`, `test_role_guard_phases_234_deny.py`, possibly `test_role_guard_grep_glob_deny.py`) get deleted in Task E3. Tests pinning surviving mechanism (`test_role_guard_envelope_grant.py`, `test_role_guard_envelope_json.py`, `test_role_guard.py` core) get updated to use TDD slugs.

- [ ] **Step 2: Write the new test cases for the simplified shape**

Add to `tests/unit/test_role_guard.py` (or create `tests/unit/test_role_guard_post_m4.py`):

```python
def test_phase_1_tdd_writes_intent_md_within_skill_runs():
    """phase-1-tdd may write to .claude/skill-runs/<feature>/intent.md."""
    # Uses subprocess + AGENT_ROLE=phase-1-tdd env to invoke role_guard.py.
    # Stdin payload: tool_name=Write, tool_input.file_path=".claude/skill-runs/some-feature/intent.md"
    # Expect exit code 0.
    ...

def test_phase_1_tdd_denied_outside_skill_runs():
    """phase-1-tdd may not write to docs/."""
    # Stdin: tool_input.file_path="docs/foo.md"
    # Expect exit code 1.
    ...

def test_phase_2_tdd_writes_tests_and_validation():
    """phase-2-tdd may write to tests/ and .claude/skill-runs/<feature>/validation/."""
    ...

def test_phase_3_tdd_envelope_only():
    """phase-3-tdd has no static allowlist; envelope-driven."""
    # AGENT_ROLE=phase-3-tdd, AGENT_ENVELOPE='["^src/foo\\.py$"]'
    # tool_input.file_path="src/foo.py" → exit 0
    # tool_input.file_path="src/bar.py" → exit 1 (not in envelope)
    ...

def test_phase_4_tdd_writes_integration_and_handoff():
    """phase-4-tdd may write to .claude/skill-runs/<feature>/integration/ and .claude/handoff.md."""
    ...

def test_no_canonical_deny_read_lockdown():
    """Read-class lockdown removed; phase agents may Read docs/ARCHITECTURE.md directly."""
    # AGENT_ROLE=phase-1-tdd, tool_name=Read, tool_input.file_path="docs/ARCHITECTURE.md"
    # Expect exit 0.
    ...

def test_read_class_tools_constant_preserved():
    """READ_CLASS_TOOLS constant still exists for forward-compat."""
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("rg", "checks/role_guard.py")
    mod = importlib.util.module_from_spec(spec); sys.modules["rg"] = mod; spec.loader.exec_module(mod)
    assert mod.READ_CLASS_TOOLS == {"Read", "Grep", "Glob"}

def test_envelope_grant_mechanism_preserved():
    """_envelope_patterns + _log_grant survive."""
    # Check all three envelope shapes (JSON-array, JSON-object-with-paths, legacy colon-separated).
    ...
```

(The exact test scaffolding follows the patterns in the existing `tests/unit/test_role_guard*.py` files — subprocess-based invocation of `checks/role_guard.py` with stdin JSON + env vars. Re-use the existing helper if there is one.)

- [ ] **Step 3: Run new tests — expect FAIL on the old `phase-1-writer` policy table**

```bash
uv run pytest tests/unit/test_role_guard.py::test_phase_1_tdd_writes_intent_md_within_skill_runs -v
```

Expected: FAIL — current `ROLE_POLICIES` keys are legacy slugs, not TDD slugs.

---

### Task D2: Simplify `checks/role_guard.py`

**Files:**
- Modify: `checks/role_guard.py:1-227` (rewrite-in-place)
- Delete: `scripts/checks_role_guard_module.py` (test-import re-exporter, no longer needed)
- Modify: `tests/unit/test_inv_003_phase_topology.py:364` (drop `from checks_role_guard_module import ROLE_POLICIES` if INV-003 no longer cross-references the role policy table)

- [ ] **Step 1: Edit `checks/role_guard.py` to the new shape**

Target shape (reference: M3 role_guard simplification doc §2):

```python
"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.

Inner gate paired with each agent's `tools:` frontmatter. Reads tool-call JSON
from stdin. AGENT_ROLE unset is the no-op path. Post-M4-shrink:
- Read-class lockdown removed (cairn-substrate-and-fastmcp superseded).
- Bash-token deny block removed (no canonical-knowledge target).
- Write paths target dispatch-skill workspace (.claude/skill-runs/) and tests/.
- Phase-3 write gate is envelope-driven; mechanism unchanged.

Exit codes: 0 = allow, 1 = deny (with stderr diagnostic), 2 = malformed stdin.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}  # preserved per M3 §5; future-proof

CAIRN_ROOT = Path(__file__).resolve().parent.parent

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
    # phase-3-tdd: no static entry; envelope-driven (preserves slice-2 asymmetry
    # per compression-infrastructure-bootstrap-superseded).
}


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat and re.search(pat, path):
            return True
    return False


def _envelope_patterns(raw: str | None) -> list[str]:
    """Return regex patterns from AGENT_ENVELOPE.

    Handles three shapes:
    - JSON array of strings (canonical write-gate format, back-compat)
    - JSON object with ``paths`` key (per ADR D9)
    - Colon-separated legacy string (deprecated; warns on stderr)
    """
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, list) and all(isinstance(p, str) for p in parsed):
        return [p for p in parsed if p]
    if isinstance(parsed, dict) and isinstance(parsed.get("paths"), list):
        return [p for p in parsed["paths"] if isinstance(p, str) and p]
    print(
        "role_guard: legacy colon-separated AGENT_ENVELOPE format detected; "
        "migrate to JSON array",
        file=sys.stderr,
    )
    return [p for p in raw.split(":") if p]


def _log_grant(path: str, role: str) -> None:
    """Append one line to .claude/envelope-grants.log recording the envelope grant."""
    grant_log = CAIRN_ROOT / ".claude" / "envelope-grants.log"
    grant_log.parent.mkdir(parents=True, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    line = f"cairn-tdd-feature {date_str} {path} {role}\n"
    with open(grant_log, "a") as fh:
        fh.write(line)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        print(f"role_guard: malformed stdin: {exc}", file=sys.stderr)
        return 2

    role = os.environ.get("AGENT_ROLE")
    if not role:
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    if role == "phase-3-tdd":
        envelope = os.environ.get("AGENT_ENVELOPE")
        patterns = _envelope_patterns(envelope)
        if _matches_any(file_path, patterns):
            return 0
        print(
            f"role_guard: phase-3-tdd denied write outside envelope: {file_path}",
            file=sys.stderr,
        )
        return 1

    if role in ROLE_POLICIES:
        if _matches_any(file_path, ROLE_POLICIES[role]):
            return 0
        # Envelope-grant escape (D9): wider grant via AGENT_ENVELOPE applies to
        # static-policy roles too.
        envelope = os.environ.get("AGENT_ENVELOPE")
        env_patterns = _envelope_patterns(envelope)
        if _matches_any(file_path, env_patterns):
            _log_grant(file_path, role)
            return 0
        print(
            f"role_guard: {role} denied write outside allow-list: {file_path}",
            file=sys.stderr,
        )
        return 1

    print(f"role_guard: unknown role '{role}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

(Net change: 226 lines → ~95 lines. Removes `BASH_TOOL`, `_CANONICAL_DENY_PATTERNS`, `ROLE_DENY_READ`, `_bash_path_tokens`, the read-class lockdown branch in `main()`, and the Bash-token deny block.)

- [ ] **Step 2: Delete `scripts/checks_role_guard_module.py`**

```bash
git rm scripts/checks_role_guard_module.py
```

- [ ] **Step 3: Update `tests/unit/test_inv_003_phase_topology.py`**

Drop the `from checks_role_guard_module import ROLE_POLICIES` import and the asymmetry-comment assertion that depends on it (line 364 region). With INV-003's quad-binding shrunken to triple-binding (Task C5), the ROLE_POLICIES cross-reference is no longer required. If a remaining assertion still inspects ROLE_POLICIES, replace the import with a direct importlib.util load from `checks/role_guard.py` (mirror the pattern in checks_role_guard_module.py).

- [ ] **Step 4: Run the new tests + INV-003 test**

```bash
uv run pytest tests/unit/test_role_guard.py tests/unit/test_role_guard_envelope_grant.py tests/unit/test_role_guard_envelope_json.py tests/unit/test_inv_003_phase_topology.py -v
```

Expected: PASS for the new TDD-slug cases; PASS for envelope-grant; PASS for INV-003 phase topology.

- [ ] **Step 5: Commit**

```bash
git add checks/role_guard.py tests/unit/test_role_guard.py tests/unit/test_inv_003_phase_topology.py
git rm scripts/checks_role_guard_module.py
git commit -m "feat(m4): simplify role_guard.py to post-shrink shape

Drops _CANONICAL_DENY_PATTERNS, ROLE_DENY_READ, _bash_path_tokens, and
the read-class lockdown branch (substrate retired; INV-010 retired).
ROLE_POLICIES updated to TDD slugs (phase-1-tdd / phase-2-tdd /
phase-4-tdd) with paths under .claude/skill-runs/<feature>/.
Phase-3 envelope-only asymmetry preserved. READ_CLASS_TOOLS constant,
_envelope_patterns parsing, and _log_grant audit trail preserved."
```

---

## Section E — Mass deletion

These tasks are independent. Each is a single commit. They MUST run after Sections A–D land (carry-forward extracted, ADRs in place, architecture amended, role_guard simplified — so the validator and remaining tests pass at every commit).

### Task E1: Delete `scripts/slice_orchestrator/`

**Files:**
- Delete: `scripts/slice_orchestrator/` (whole directory; ~3000 LOC)

- [ ] **Step 1: Remove the directory**

```bash
git rm -r scripts/slice_orchestrator/
```

- [ ] **Step 2: Run a quick smoke check**

```bash
uv run pytest -q --tb=no -rf 2>&1 | head -30
```

Expected: many failures from tests that import slice_orchestrator. Those tests are deleted in Task E3 — DO NOT fix them here. Just count: should be ~50 failures, matching the import sites enumerated in `tests/unit/` per the M4 inventory.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(m4): delete scripts/slice_orchestrator/ (~3000 LOC)

The orchestrator package retires per docs/adr/slice-close-contract-superseded.md
and docs/adr/orchestrator-observability-superseded.md. Test sites that
imported it are deleted in subsequent commits."
```

---

### Task E2: Delete `scripts/cairn_query/` and `mcp_servers/`

**Files:**
- Delete: `scripts/cairn_query/` (~1900 LOC)
- Delete: `mcp_servers/` (whole directory)
- Delete: `.mcp.json` (if it exists; the substrate's stdio registration)

- [ ] **Step 1: Remove the directories**

```bash
git rm -r scripts/cairn_query/ mcp_servers/
git rm .mcp.json 2>/dev/null || true
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(m4): delete scripts/cairn_query/ and mcp_servers/

Substrate (typed-knowledge graph + MCP wrapper) retires per
docs/adr/cairn-substrate-and-fastmcp-superseded.md. Tests in subsequent
commits."
```

---

### Task E3: Delete tests bound to doomed modules

**Files:**
- Delete: each test file under `tests/unit/` whose only purpose is exercising deleted code

The list (verified via `grep -l 'from slice_orchestrator\|import slice_orchestrator\|from cairn_query\|import cairn_query\|from mcp_servers\|import mcp_servers' tests/`):

```
tests/unit/test_cairn_query_models.py
tests/unit/test_cairn_query_schema.py
tests/unit/test_cairn_query_storage.py
tests/unit/test_cli_query.py
tests/unit/test_close_slice_add_surface.py
tests/unit/test_close_slice_hardened.py
tests/unit/test_close_slice_invocation.py
tests/unit/test_close_slice_sweepnotes_required.py
tests/unit/test_commit_phase_handoff_stage_surface.py
tests/unit/test_cross_slice_isolation.py
tests/unit/test_dispatch_contract_separation.py
tests/unit/test_extractor_base.py
tests/unit/test_extractor_decision.py
tests/unit/test_extractor_feature.py
tests/unit/test_extractor_invariant.py
tests/unit/test_extractor_lesson.py
tests/unit/test_extractor_op_rule.py
tests/unit/test_extractor_slice.py
tests/unit/test_extractor_spec_section.py
tests/unit/test_failed_classification_backoff.py
tests/unit/test_git_helper_check.py
tests/unit/test_heartbeat.py
tests/unit/test_lifecycle_artifact_relpaths_paper_cut.py
tests/unit/test_malformed_slice_yaml.py
tests/unit/test_mcp_cairn_knowledge_jsonrpc.py
tests/unit/test_mcp_cairn_knowledge_server.py
tests/unit/test_mcp_cairn_knowledge_tools.py
tests/unit/test_multiline_json_tail.py
tests/unit/test_observability_writer.py
tests/unit/test_orchestrator_bug_fixes.py
tests/unit/test_orchestrator_events_capture.py
tests/unit/test_orchestrator_live_stderr.py
tests/unit/test_orchestrator_paths_migration.py
tests/unit/test_orchestrator_snapshot_pinning.py
tests/unit/test_path_binding.py
tests/unit/test_phase_2_handoff_staging_surface.py
tests/unit/test_phase_3_empty_cluster_guard.py
tests/unit/test_phase_3_per_cluster_logs.py
tests/unit/test_post_timeout_reconcile.py
tests/unit/test_redispatch_cap.py
tests/unit/test_redispatch_persistence.py
tests/unit/test_resume_reconcile.py
tests/unit/test_root_resolver_migration.py
tests/unit/test_round_trip_validator.py
tests/unit/test_signal_handler.py
tests/unit/test_slice_id_derivation.py
tests/unit/test_slice_orchestrator_artifact_preservation.py
tests/unit/test_slice_orchestrator_cost.py
tests/unit/test_slice_orchestrator_model_config.py
tests/unit/test_slice_orchestrator_package_split.py
tests/unit/test_snapshot_lru.py
tests/unit/test_state_schema.py
tests/unit/test_yaml_brief_round_trip.py
tests/unit/test_yaml_clusters_schema.py
tests/integration/test_compressed_slice_end_to_end.py
tests/integration/test_signal_observability.py
```

(Verify the list against `grep -l '...' tests/` at execution time — the list may have shifted since plan-authoring.)

Plus role_guard tests bound to the dying lockdown shape:

```
tests/unit/test_role_guard_phase_1_lockdown.py
tests/unit/test_role_guard_phases_234_deny.py
tests/unit/test_role_guard_grep_glob_deny.py  # carry-forward audit §2 says G1-G7 cases verify READ_CLASS_TOOLS — preserve if the test logic doesn't depend on canonical-knowledge deny paths; otherwise rewrite using a synthetic deny set in the test
```

(`test_role_guard_grep_glob_deny.py` needs a closer look at execution time — its purpose is verifying `READ_CLASS_TOOLS` covers Grep/Glob, which the M3 audit names as a critical carry-forward. If the test asserts the constant exists with the right value, KEEP it. If it asserts denial of canonical-knowledge paths via Grep/Glob, the assertion is meaningless post-M4 — rewrite to use a synthetic deny set in fixture, or drop the test.)

Other slice-machinery test files to scan and likely delete:

```
tests/unit/test_d1_gate.py
tests/unit/test_d3_bypass_log_format.py
tests/unit/test_dogfood_evaluate.py
tests/unit/test_feature_scope_guard.py
tests/unit/test_hook_relpath_bypass.py
tests/unit/test_hook_tolerance.py
tests/unit/test_housekeeping_post_slice_a_tidy.py
tests/unit/test_integration_gate.py
tests/unit/test_integration_gate_timeout.py
tests/unit/test_phase_1_writer_bash_restored.py  # legacy-slug-bound
tests/unit/test_phase_1_writer_query_first.py    # substrate-bound
tests/unit/test_phase_2_skeptic_query_first_prompt.py
tests/unit/test_phase_3_implementer_query_first_prompt.py
tests/unit/test_phase_4_integrator_paper_cuts.py
tests/unit/test_phase_4_integrator_prompt.py
tests/unit/test_phase_4_integrator_query_first_prompt.py
tests/unit/test_phase_rethink.py
tests/unit/test_progressive_disclosure.py  # bound to the dying slash-command set
tests/unit/test_role_guard_wired.py
tests/unit/test_scope_guard_admin_allowlist.py
tests/unit/test_slice_003_precursor.py
tests/unit/test_slice_005_design_decomposition.py
tests/unit/test_consumer_migration_doc.py  # bound to docs/upgrading-from-pre-compression.md (M5)
tests/unit/test_upgrade_doc_consumer_setup.py  # ditto
```

For each: `cat <file> | head -20` to confirm it imports doomed modules or asserts retired behavior, then `git rm <file>`.

- [ ] **Step 1: Confirm-and-delete loop**

```bash
for f in tests/unit/test_close_slice_*.py tests/unit/test_orchestrator_*.py tests/unit/test_extractor_*.py tests/unit/test_cairn_query_*.py tests/unit/test_mcp_cairn_knowledge_*.py; do
  echo "=== $f ==="
  head -5 "$f"
done
```

(Visual scan; these are all clearly doomed.)

```bash
git rm tests/unit/test_close_slice_*.py
git rm tests/unit/test_orchestrator_*.py
git rm tests/unit/test_extractor_*.py
git rm tests/unit/test_cairn_query_*.py
git rm tests/unit/test_mcp_cairn_knowledge_*.py
git rm tests/unit/test_cli_query.py tests/unit/test_path_binding.py tests/unit/test_round_trip_validator.py tests/unit/test_snapshot_lru.py
git rm tests/unit/test_dispatch_contract_separation.py tests/unit/test_failed_classification_backoff.py tests/unit/test_git_helper_check.py tests/unit/test_heartbeat.py
git rm tests/unit/test_lifecycle_artifact_relpaths_paper_cut.py tests/unit/test_malformed_slice_yaml.py tests/unit/test_multiline_json_tail.py tests/unit/test_observability_writer.py
git rm tests/unit/test_phase_2_handoff_staging_surface.py tests/unit/test_phase_3_empty_cluster_guard.py tests/unit/test_phase_3_per_cluster_logs.py tests/unit/test_post_timeout_reconcile.py
git rm tests/unit/test_redispatch_*.py tests/unit/test_resume_reconcile.py tests/unit/test_root_resolver_migration.py tests/unit/test_signal_handler.py
git rm tests/unit/test_slice_*.py tests/unit/test_state_schema.py tests/unit/test_yaml_brief_round_trip.py tests/unit/test_yaml_clusters_schema.py
git rm tests/unit/test_cross_slice_isolation.py
git rm tests/integration/test_compressed_slice_end_to_end.py tests/integration/test_signal_observability.py
git rm tests/unit/test_d1_gate.py tests/unit/test_d3_bypass_log_format.py tests/unit/test_dogfood_evaluate.py
git rm tests/unit/test_feature_scope_guard.py tests/unit/test_hook_relpath_bypass.py tests/unit/test_hook_tolerance.py
git rm tests/unit/test_housekeeping_post_slice_a_tidy.py tests/unit/test_integration_gate*.py
git rm tests/unit/test_phase_1_writer_*.py tests/unit/test_phase_2_skeptic_query_first_prompt.py tests/unit/test_phase_3_implementer_query_first_prompt.py
git rm tests/unit/test_phase_4_integrator_*.py tests/unit/test_phase_rethink.py tests/unit/test_progressive_disclosure.py
git rm tests/unit/test_role_guard_phase_1_lockdown.py tests/unit/test_role_guard_phases_234_deny.py tests/unit/test_role_guard_wired.py
git rm tests/unit/test_scope_guard_admin_allowlist.py
git rm tests/unit/test_slice_003_precursor.py tests/unit/test_slice_005_design_decomposition.py
git rm tests/unit/test_consumer_migration_doc.py tests/unit/test_upgrade_doc_consumer_setup.py
```

(Adjust the globs for any files that don't exist in the live tree.)

- [ ] **Step 2: Inspect the remaining test files**

```bash
ls -1 tests/unit/ | grep -v __pycache__
```

Expected survivors (should be ~25 files): test_role_guard.py, test_role_guard_envelope_*.py, test_role_guard_grep_glob_deny.py (if rewritten), test_inv_001_*.py, test_inv_002_structural_parser.py, test_inv_002_inv_008_architecture_blocks.py (renamed), test_inv_003_phase_topology.py, test_inv_003_tdd_siblings_tolerated.py, test_invariant_assertions.py, test_invariant_id_extractor.py, test_assertion_block_yaml_parser.py, test_catchup_tier1_list_pinned.py (re-evaluate — bound to deleted catchup.full.md; likely delete), test_context_budget.py, test_context_discipline_protocol.py, test_root.py, test_path_discipline_lint.py, test_lessons_cross_slice_contradiction.py, test_identifier_scheme_*.py, test_feature_*.py, test_agent_prompt_updates.py, test_adr_rename_sweep.py, test_triager_superseded_heuristic.py (relocated import in A3), test_inv_002_*.py, test_inv_003_*.py.

- [ ] **Step 3: Run the suite — confirm only intentional surviving tests run**

```bash
uv run pytest -q --tb=no -rf 2>&1 | tee /tmp/m4-post-deletion-failures.txt
diff /tmp/m4-baseline-failures.txt /tmp/m4-post-deletion-failures.txt | head -40
```

Expected: passing test count drops by 60+ (deleted), failing test count drops by 14+ (the M3 flipped reds were on doomed files in some cases — check the diff). Critical: NO new failures. Any new failure means a test that survived imports something that died — investigate and either delete the test or restore the import target.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(m4): delete tests bound to retired orchestrator/substrate/slice machinery

Drops ~60 test files. Survivors: role_guard envelope mechanism, INV-001/2/3
bindings, structural-parser, identifier scheme, feature schema, triager
superseded-test heuristic (relocated import per Task A3), context budget."
```

---

### Task E4: Delete other doomed scripts

**Files:**
- Delete: `scripts/dogfood_evaluate.py`
- Delete: `scripts/integration_gate.py`
- Delete: `scripts/lint_paths.py`
- Delete: `scripts/render_status.sh`
- Delete: `scripts/snapshot_diff.py`
- Delete: `scripts/verify_handoff.sh`
- Delete: `checks/scope-guard.sh`

- [ ] **Step 1: Confirm none have surviving consumers**

```bash
for f in scripts/dogfood_evaluate.py scripts/integration_gate.py scripts/lint_paths.py scripts/render_status.sh scripts/snapshot_diff.py scripts/verify_handoff.sh checks/scope-guard.sh; do
  echo "=== $f ==="
  basename=$(basename "$f")
  grep -rln "$basename" --include="*.md" --include="*.json" --include="*.yaml" --include="*.py" --include="*.sh" . 2>/dev/null | grep -v "$f" | head -5
done
```

Each should return at most: deleted-test files (already gone), `commands/claude-code/settings.json` (handled in Task F1), and historical references in docs/. If any return live consumers (a non-deleted script or a surviving slash command), STOP and re-evaluate.

- [ ] **Step 2: Delete**

```bash
git rm scripts/dogfood_evaluate.py scripts/integration_gate.py scripts/lint_paths.py scripts/render_status.sh scripts/snapshot_diff.py scripts/verify_handoff.sh checks/scope-guard.sh
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(m4): delete slice-machinery scripts + scope-guard hook

scope-guard.sh subsumed by role_guard.py per design §2.2. Other scripts
(dogfood_evaluate, integration_gate, lint_paths, render_status.sh,
snapshot_diff, verify_handoff) tied to slice machinery; no surviving
consumers."
```

---

### Task E5: Delete slice-machinery slash commands and legacy phase agents

**Files:**
- Delete: `commands/claude-code/start-slice*.md` (3 files: lite, full, legacy)
- Delete: `commands/claude-code/integration-sweep*.md` (2 files)
- Delete: `commands/claude-code/handoff*.md` (2 files)
- Delete: `commands/claude-code/catchup*.md` (2 files)
- Delete: `commands/claude-code/refresh-architecture*.md` (2 files)
- Delete: `commands/claude-code/status*.md` (2 files)
- Delete: `.claude/agents/phase-1-writer.md`
- Delete: `.claude/agents/phase-2-skeptic.md`
- Delete: `.claude/agents/phase-3-implementer.md`
- Delete: `.claude/agents/phase-4-integrator.md`
- Delete: `.claude/agents/issue-triager.md`

Survivors in `commands/claude-code/`: `decision*.md`, `new-adr*.md`, `.local/dev-mode*.md`, `.local/README.md`, `settings.json`. Survivors in `.claude/agents/`: `phase-{1..4}-tdd.md`, `triager-tdd.md`, `role-topology.yaml` (added in Task A2).

- [ ] **Step 1: Confirm SKILL.md doesn't reference legacy agents**

```bash
grep -n 'phase-1-writer\|phase-2-skeptic\|phase-3-implementer\|phase-4-integrator\|issue-triager' .claude/skills/cairn-tdd-feature/SKILL.md
```

Expected: no hits (SKILL.md dispatches `phase-{1..4}-tdd` and `triager-tdd`). If any hit, STOP and update SKILL.md first.

- [ ] **Step 2: Verify catchup.full.md / handoff.md deletions don't break INV-002**

INV-002 was amended in Task C4 to drop sub-clauses (b)/(c) (which targeted catchup.full.md and start-slice/close_slice). Verify:

```bash
uv run pytest tests/unit/test_inv_002_structural_parser.py -v
```

Expected: PASS.

- [ ] **Step 3: Delete the slash commands and legacy agents**

```bash
git rm commands/claude-code/start-slice*.md
git rm commands/claude-code/integration-sweep*.md
git rm commands/claude-code/handoff*.md
git rm commands/claude-code/catchup*.md
git rm commands/claude-code/refresh-architecture*.md
git rm commands/claude-code/status*.md
git rm .claude/agents/phase-1-writer.md .claude/agents/phase-2-skeptic.md .claude/agents/phase-3-implementer.md .claude/agents/phase-4-integrator.md .claude/agents/issue-triager.md
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(m4): delete slice slash commands + legacy phase agents

Slash commands replaced by .claude/skills/cairn-tdd-feature/SKILL.md
dispatch (per design §2.3). Legacy phase agents (writer/skeptic/
implementer/integrator/issue-triager) replaced by phase-{1..4}-tdd
and triager-tdd."
```

---

### Task E6: Delete slice state directories and `.claude/handoff.md` reset

**Files:**
- Delete: `.claude/current-slice/` (residual; the directory itself + slice.yaml)
- Delete: `.claude/sweep.yaml`, `.claude/sweep-results/` (whole directory)
- Delete: `.claude/completed-slices/` (whole directory)
- Delete: `.claude/orchestrator-debug/` (output directory; may not exist locally)
- Delete: `.claude/d1-bypasses.log`, `.claude/d3-bypasses.log` (if present)
- Delete: `.claude/pipeline-substrate-registry.yaml` (per Task B7 supersession)
- Delete: `.claude/structural-snapshot.json` (D3 gate input; gate retired per Task B5)
- Delete: `.claude/cairn_query/` (substrate state directory under .claude/, if present)
- Delete: `.claude/learning.md` (only if it's slice-machinery output; verify before deletion — `docs/lessons.md` is the canonical lessons doc and stays)
- Modify: `.claude/handoff.md` (rewrite with M4-completed state)

`.claude/handoff.md` survives as the cross-session interface (design §3.1 keeps it); just refresh contents. Decide whether to keep its existing M3-landed content or overwrite — overwrite is cleaner since M4 changes the project shape entirely.

- [ ] **Step 1: Delete the state directories**

```bash
git rm -r .claude/current-slice/
git rm .claude/sweep.yaml
git rm -r .claude/sweep-results/ 2>/dev/null || true
git rm -r .claude/completed-slices/ 2>/dev/null || true
git rm -r .claude/orchestrator-debug/ 2>/dev/null || true
git rm .claude/d1-bypasses.log .claude/d3-bypasses.log 2>/dev/null || true
git rm .claude/pipeline-substrate-registry.yaml 2>/dev/null || true
git rm .claude/structural-snapshot.json 2>/dev/null || true
git rm -r .claude/cairn_query/ 2>/dev/null || true
# .claude/learning.md: verify it's slice-machinery output before deleting.
# docs/lessons.md is the canonical lessons doc and stays untouched.
```

- [ ] **Step 2: Rewrite `.claude/handoff.md`**

Use the existing four-section structure (State, Next, Blocked / Pending, Pointers) since INV-002(a) still binds. Keep under 440 bytes (token budget fail-at). Suggested content:

```markdown
---
slice: design/cairn-shrink
phase: m4-landed
branch: design/cairn-shrink
as-of: 2026-05-07 <SHA>
---

## State
M4 landed: orchestrator/substrate/MCP/slice machinery deleted; role_guard simplified to TDD-slug shape; 7 supersession ADRs landed; INV-008/9/10 retired; INV-002/3/7 amended. Suite green vs M4 baseline.

## Next
M5 — plugin packaging. `claude plugin install cairn` target.

## Blocked / Pending
- Amendment ADRs deferred (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M6 consumer migration (complex-rag-analysis off `.slice-system → .` symlink).

## Pointers
- docs/plans/2026-05-06-cairn-shrink-design.md — overall design.
- docs/plans/2026-05-07-cairn-shrink-m4-delete-and-relocate.md — this M4 plan.
- .claude/skills/cairn-tdd-feature/SKILL.md — dispatch skill (the only path).
- Branch design/cairn-shrink — WIP; merge in M5.
```

(Substitute `<SHA>` with `git rev-parse HEAD` after this commit lands. The `binding-effective-from` placeholder pattern from INV-001 applies here too if the plan executor wants to mirror that precedent.)

- [ ] **Step 3: Commit**

```bash
git add .claude/handoff.md
git commit -m "chore(m4): delete slice state dirs; rewrite handoff for M4-landed

Removes .claude/current-slice/, sweep.yaml, sweep-results/,
completed-slices/, orchestrator-debug/, d1/d3 bypass logs, and
pipeline-substrate-registry.yaml (per pipeline-substrate-naming-superseded).
Handoff refreshed with M4-landed state per INV-002(a) structural binding."
```

---

## Section F — Hook + dependency cleanup

### Task F1: Update both `settings.json` files + decide on `role-cheatsheet.sh`

**Files (TWO settings.json):**
- Modify: `.claude/settings.json` (active project settings)
- Modify: `commands/claude-code/settings.json` (cairn-distributed template; copies to consumers)
- Modify or delete: `checks/role-cheatsheet.sh` (its body may reference retired slice machinery)

Both settings.json files currently register four hooks via `.slice-system/checks/...` paths: `role-cheatsheet.sh` (SessionStart), `reversibility-guard.sh` + `scope-guard.sh` + `role_guard.py` (PreToolUse), and `reality-check.sh` (PostToolUse). After Section E:
- `scope-guard.sh` is gone → drop its hook entry from BOTH settings.json files.
- `reversibility-guard.sh`, `role_guard.py`, `reality-check.sh`, `prepare-commit-msg.sh` survive → keep their entries.
- `role-cheatsheet.sh` survival depends on body inspection (Step 1 below).

- [ ] **Step 1: Inspect `checks/role-cheatsheet.sh`**

```bash
cat checks/role-cheatsheet.sh
```

Decision:
- **If the body references slice machinery, slice ids, or the legacy phase-N-{writer,skeptic,implementer,integrator} agents:** rewrite the body to reflect the post-M4 reality (the four `phase-{1..4}-tdd` agents + `triager-tdd` + the dispatch skill at `.claude/skills/cairn-tdd-feature/SKILL.md`), OR drop the SessionStart hook from both settings.json files and delete `checks/role-cheatsheet.sh`. Pick the one that produces less churn — if the cheatsheet is a quick role-summary and the post-M4 roles are clear, rewrite; if it's tangled with slice state, delete.
- **If the body is purely role-summary text agnostic to slice machinery:** keep both the script and the hook entry as-is.

- [ ] **Step 2: Edit `.claude/settings.json` to drop scope-guard registration**

Remove the `PreToolUse` entry whose `command` references `scope-guard.sh` (lines 47-55 of the current file). Validate JSON afterward.

- [ ] **Step 3: Edit `commands/claude-code/settings.json` to drop scope-guard registration**

Same edit as Step 2, applied to the consumer-template file. Both files diverge only in nuance; keep them consistent.

- [ ] **Step 4: Apply the role-cheatsheet decision**

- If keeping/rewriting: update `checks/role-cheatsheet.sh` body. No settings.json change needed beyond Step 2/3.
- If deleting: drop the SessionStart entry from both settings.json files; `git rm checks/role-cheatsheet.sh`.

- [ ] **Step 5: Validate JSON for both files**

```bash
jq . .claude/settings.json
jq . commands/claude-code/settings.json
```

Both must parse cleanly.

- [ ] **Step 6: Commit**

```bash
git add .claude/settings.json commands/claude-code/settings.json
git add checks/role-cheatsheet.sh 2>/dev/null || true
# OR: git rm checks/role-cheatsheet.sh, depending on Step 4 decision
git commit -m "chore(m4): drop scope-guard hook + reconcile role-cheatsheet

scope-guard.sh deleted in Task E4; subsumed by role_guard.py per
design §2.2. role-cheatsheet.sh <kept|rewritten|deleted> after body
inspection (cite outcome here)."
```

---

### Task F2: Prune `pyproject.toml` deps; regenerate `uv.lock`

**Files:**
- Modify: `pyproject.toml` (drop `kuzu`, `fastmcp`, `mistune`)
- Modify: `uv.lock` (regenerated by `uv sync`)

`mistune` was used by `cairn_query`'s extractors (deleted in Task E2). `kuzu` and `fastmcp` justifications die with the substrate.

Survivors: `pyyaml`, `pydantic`, `typer` (per CLAUDE.md "v1 standing dep set"). Plus `pytest` in dev.

- [ ] **Step 1: Confirm no surviving consumer of mistune/kuzu/fastmcp**

```bash
grep -rln 'import mistune\|from mistune\|import kuzu\|from kuzu\|import fastmcp\|from fastmcp\|FastMCP' scripts/ checks/ tests/ 2>/dev/null
```

Expected: empty (deleted dirs already gone). If any hit, STOP and resolve.

- [ ] **Step 2: Edit pyproject.toml**

```toml
[project]
name = "cairn"
version = "0.1.0"
description = "Slice-pipeline methodology repo (hooks, slash commands, validators)"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.6",
    "typer>=0.12",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
pythonpath = ["scripts"]
```

(Drop the kuzu, mistune, fastmcp lines. `typer` survives — used by `lib/invariant_id_extractor.py` and any future small CLIs.)

- [ ] **Step 3: Regenerate uv.lock**

```bash
uv sync
```

Expected: lock file shrinks; transitive deps for kuzu/mistune/fastmcp drop out.

- [ ] **Step 4: Run the suite to confirm no missing-import regressions**

```bash
uv run pytest -q
```

Expected: pass count matches the post-E3 baseline.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(m4): drop kuzu, fastmcp, mistune from pyproject.toml

Substrate retired (cairn-substrate-and-fastmcp-superseded). Standing
dep set narrows to pyyaml/pydantic/typer per CLAUDE.md."
```

---

## Section G — Final verification

### Task G1: Suite + validator + structural smoke tests

**Files:**
- Read: `/tmp/m4-baseline-failures.txt` (Task A1 baseline)

- [ ] **Step 1: Run the full suite and diff against baseline**

```bash
uv run pytest -q --tb=no -rf 2>&1 | tee /tmp/m4-final-failures.txt
diff /tmp/m4-baseline-failures.txt /tmp/m4-final-failures.txt
```

Expected: passing-test count drops by ~60 (deleted tests) and ~14 (M3 flipped reds on doomed files); failing-test count drops by 14 (M3's 14 flipped reds gone with the doomed code) — net: **0 failures, ~1230 pass**, vs M3's 2/1292.

If new failures appear, investigate via the diff. Common causes:
- A surviving test imported a deleted helper.
- A surviving test asserted retired behavior (e.g., expected an INV-008 binding block in ARCHITECTURE.md).
- The validator's invariant table wasn't fully scrubbed of INV-008/9/10.

Each new failure either resolves to a test deletion or a small code/doc fix. Commit each fix separately.

- [ ] **Step 2: Run the validator**

```bash
uv run python scripts/validate_architecture.py
```

Expected: exit 0. If any check fails, the failure cites a specific invariant — fix and re-run.

- [ ] **Step 3: Smoke-test the dispatch skill (optional but recommended)**

Without dispatching a real feature, sanity-check the SKILL.md preconditions:

```bash
ls .claude/agents/phase-{1..4}-tdd.md .claude/agents/triager-tdd.md
ls .claude/agents/role-topology.yaml
ls .claude/skills/cairn-tdd-feature/SKILL.md
```

All five agent files + the topology YAML + the skill file must exist.

- [ ] **Step 4: Confirm tree size shrinkage**

```bash
git diff --stat /tmp/m4-snapshot-sha.txt..HEAD | tail -5
```

Expected: net deletion of ~5000-7000 LOC (orchestrator ~3000 + substrate ~1900 + ~200 from scope-guard + supporting scripts). Use this as a sanity check that the deletions actually happened.

- [ ] **Step 5: No commit — this is verification only**

If everything is green, proceed to Task G2 to refresh the handoff one final time with the verified-end-of-M4 SHA.

---

### Task G2: Final handoff substitution

**Files:**
- Modify: `.claude/handoff.md` (substitute `<SHA>` placeholder with the actual M4-end SHA, mirroring the INV-001 binding-effective-from precedent at fd1823e)

- [ ] **Step 1: Capture the post-G1 SHA**

```bash
git rev-parse HEAD
```

- [ ] **Step 2: Substitute the placeholder**

Edit `.claude/handoff.md`'s frontmatter `as-of:` line to contain the SHA captured above.

- [ ] **Step 3: Run validator one last time (handoff structural-parser binding still applies)**

```bash
uv run python scripts/validate_architecture.py
uv run pytest tests/unit/test_inv_002_structural_parser.py -v
```

Expected: both pass.

- [ ] **Step 4: Commit (final M4 commit)**

```bash
git add .claude/handoff.md
git commit -m "chore(m4-handoff-sha): substitute as-of SHA for M4-landed handoff

Mirrors the INV-001 precedent at fd1823e: post-substantive-commit
docs: commit substitutes the placeholder with the actual SHA so the
binding pin is byte-stable."
```

---

## Out-of-scope follow-ups

These are **NOT** in M4. Tracked in the handoff under "Blocked / Pending" so a future session can pick them up.

1. **Amendment ADRs** for the six rows of design §7 marked "amended" — `cost-per-slice-budget`, `parallelism-v1`, `phase-pipeline-evaluation`, `feature-slice-model`, `context-tiers-integration`, `identifier-scheme`. These need successor ADRs (since cairn ADRs are append-only and body-edits are blocked by reversibility-guard). Each amendment ADR captures the M4-induced delta. Defer to a follow-up session — M4 already lands the seven full supersessions named in the handoff.

2. **`docs/operational-reference.md` rewrite** — currently references retired commands and the slice unit-of-work in many places. The Phase Skill Guide section is load-bearing for INV-003's binding (mentioned in Task C5) and must continue to describe the four phases. Other sections (slice lifecycle, /catchup tier protocol, /handoff conventions) need rewriting or deletion. Out of M4 scope; track as M5 or a dedicated doc-cleanup session.

3. **`docs/spec-v1.md` rewrite** — the canonical spec. Many sections describe slice-pipeline machinery (close_slice, sweep ritual, MCP substrate). Out of M4 scope; rewrite during M5 plugin packaging or earlier as a dedicated session.

4. **`docs/upgrading-from-pre-compression.md` deletion** — the M3 audit §7 notes this is wholly replaced for M5 plugin packaging. M4 leaves it as-is since deleting now would break consumer projects mid-migration.

5. **`scripts/_root.py`** — currently provides `project_root()` and `package_root()` resolvers. `package_root()` is referenced for sys.path injection in subprocess MCP servers (now deleted) and for reading cairn's own corpus by the MCP server (also deleted). `project_root()` may still have callers; audit at M5. Out of M4 scope to keep this plan bounded.

6. **The `efficiency_program/` test subdirectory** — `tests/unit/efficiency_program/` exists but wasn't enumerated in the deletion list. Audit at M5; likely retire with the slice machinery if its contents are slice-bound.

7. **The `.windsurf/` directory + `docs/plans/2026-04-21-windsurf-*.md`** — currently untracked. Deferred per design §6 Approach A (Claude Code only). M4 leaves untouched.

8. **`feature-skill-conformance` test** (`tests/unit/test_feature_skill_conformance.py`) — re-evaluate at execution time. If it asserts conformance against the dying slash-command set, delete; otherwise update to assert conformance against the cairn-tdd-feature SKILL.md.

9. **`commands/claude-code/.local/dev-mode*.md`** — survives per design §3.1 but may reference retired slice commands; re-read and patch any stale references during M4 execution if surfaced.

10. **`scripts/lib/__init__.py`** — confirm it doesn't re-export anything from the retired modules (it currently re-exports from `invariant_id_extractor`; verify no stray re-exports).

---

## Execution notes

- **Section ordering matters.** A → B → C → D → E → F → G. Within Section E, order is mostly free (each task is independent), but E3 (test deletion) MUST follow E1 (orchestrator deletion) and E2 (substrate deletion) so the failure-count diff is meaningful.
- **Commit cadence: one commit per task** (numbered subtasks inside a task share a commit). Use only commit prefixes registered in `.claude/pipeline-substrate-registry.yaml` — INV-001's git-log-walk binding rejects unregistered prefixes. Mapping: `chore(m4): ...` for carry-forward relocations (Section A) and state/config sweeps (Section F, G); `docs(m4): ...` for ADR landings (Section B) and ARCHITECTURE.md edits (Section C); `feat(m4): ...` for code/file changes (Section D, E). Do NOT use `refactor:` or `adr:` — they are not in the registry. The registry itself retires in Task B7; until then, every commit must conform.
- **The validator runs at every commit** via the cairn pre-commit conventions (technically not enforced by a hook but expected per cairn discipline). If the validator fails mid-section, fix and re-commit before moving on — don't pile up green-on-red commits.
- **No `--no-verify`, no `git add -A`, no `git push --force`.** Per global git rules.
- **Pause points:** after Section A (extractions land), after Section C (architecture stable), after Section E (deletions complete). Each pause point is a good "commit-back-to-design/cairn-shrink + sanity-rebase" moment.
- **The dispatch skill itself doesn't dogfood M4.** M4 is too large for one phase-3 agent (per SKILL.md "The work fits in one Phase-3 agent (multi-file fan-out is M3+)"). Execute via standard tools or `superpowers:subagent-driven-development` (one subagent per task, two-stage review between tasks).

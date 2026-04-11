# ADR-003 → v1: Execution Plan

**Derived from:** `docs/adr/003-cliff-failure-mode-and-v1-defenses.md`
**Created:** 2026-04-11
**Status:** living plan; revise when a slice lands or a defense is superseded
**Read before:** starting any pre-v1 slice, running any `/decision` on v1 scope, or reviewing SLICE-002 resolve/supersede.

**Naming note:** cairn already has `docs/plans/2026-04-11-d1-*` files about the earlier **context-discipline D1** (CLAUDE.md floor cuts). This plan uses D0/D1/D2/D3/D4 in the **ADR-003** sense (target failure mode and three v1 defenses). The collision is unfortunate; disambiguation is by filename and context.

## Why this plan lives outside handoff.md

`.claude/handoff.md` is a 150–400 token pointer artifact per INV-002 / ADR-002. It cannot carry the ADR-003 execution plan without regressing that invariant. Attempting to cram the plan into handoffs either violates the token budget or loses state at the next role transition. This file is where the plan persists between sessions; handoff.md points here.

## The commitment (one-line recap)

Every pre-v1 slice must contribute to D1, D2, or D3, or declare non-v1-scope waiver in `intent.md`. Dogfood gate is 10 slices post-ADR-003 OR 2026-10-11 (whichever first). D1/D2/D3 are provisional — promote, amend, or reframe are all acceptable supersession outcomes.

## Current state (as of 2026-04-11, post-ADR-003 land)

- **SLICE-001**: shipped (bootstrap).
- **SLICE-002**: `status: stopped` at phase 2. Envelope (handoff.md / catchup.md rewrite for INV-002) must be reviewed against D1/D2/D3 contribution before resume. See Tier 0 below.
- **SLICE-003 and beyond**: not yet started.
- **ADR corpus**: ADR-001 (firm), ADR-002 (firm), ADR-003 (provisional).
- **Dogfood counter**: 0 of 10 post-ADR-003 slices.
- **Deadline counter**: 2026-10-11 (six months from ADR-003 land).

## Slice sequence (working plan, not committed order)

Candidate slices. Each slice's Phase 1 intent re-evaluates this sequencing against current state. The tier labels are priority bands, not strict ordering; overlap is permitted where dependencies allow.

### Tier 0 — prerequisites (unblock everything else)

**P0a. Phase rethink ADR** — NOT time-boxed; on v1 critical path per ADR-003 D4.

- Runs as a standalone `/decision`, not a slice.
- Output: one ADR locking phase count, boundaries, names, and role per phase.
- **Why first**: the phase shape is load-bearing for where D1/D2/D3 hook into the pipeline (intent.md, slice-close, post-phase-4, dedicated refresh session). If phases change mid-defense, D1/D2/D3 inherit churn cost.
- Corresponds to vision commitment #5 and `docs/roadmap.md` §Must-land-before-v1 item 1.
- Open question: can SLICE-003 be designed against the current 4-phase shape and refactored later, or must P0a land first? Default assumption: P0a first, to avoid churn.

**P0b. SLICE-002 resolve/supersede review** — review action, not a new slice.

- Per ADR-003 Consequences: SLICE-002's envelope must be reviewed against the D1/D2/D3 legibility criterion before resume.
- Two possible outcomes:
  1. **Amend and resume**: SLICE-002's envelope contributes to a defense (most plausibly D2 via INV-002 machine-checking). Record amendment rationale in `slice.yaml § stopped-reason` and resume.
  2. **Supersede**: envelope does not contribute or is substantively different from the amended path. Write a successor ADR amending ADR-002 and/or superseding SLICE-002 outright.
- SLICE-002's Phase 2 work on V2 resolution (shared-window) and Approach 1+ test design is preserved in `.claude/completed-slices/SLICE-002-stopped/validation/approach.md` — do not lose this on supersession.
- **Status (2026-04-11): on backburner.** SLICE-002 artifacts archived to `.claude/completed-slices/SLICE-002-stopped/` to free `.claude/current-slice/` for SLICE-003-precursor (pre-D1 D4 surfacing per ADR-004 Consequences). This is an **archive, not a supersession** — the resolve/amend-or-supersede decision is still owed, just deferred. Resume path: read the archived `slice.yaml § stopped-reason` and `validation/approach.md`, then re-run this P0b review before SLICE-003 (D1) start.

### Tier 1 — D1 automated architecture refresh

**SLICE-003 (D1 design + implementation)**

- **Inputs**: ADR-003 D1 paragraph, ADR-002 session-isolation contract, `docs/lessons.md` L-001 (pipeline-substrate commit precedent), `commands/claude-code/refresh-architecture.md` (existing manual command).
- **Phase 1 (intent)**: declare the dedicated-refresh-session spawn mechanism, `ADR_D1_BYPASS=1` escape hatch semantics, slice-close gating on `scripts/validate_architecture.py` pass, `.claude/d1-bypasses.log` format and rolling-window trigger.
- **Phase 2 (validation)**: tests for refresh-session isolation (no phase-role environment variables leak), bypass log format, validator-fail-blocks-close behavior, rolling-10-slice-window bypass-count trigger.
- **Phase 3 (implementation)**: post-slice hook, refresh session spawn, integration with `/start-slice` status transition, pipeline-substrate commit authoring.
- **Phase 4 (integration)**: explicit test verifying ADR-002 compliance per ADR-003 Risk Register item 9 ("the D1 design slice must explicitly verify ADR-002 compliance at Phase 4, with a named test that checks refresh-session isolation").

**SLICE-004 (D1 dogfood instrumentation)** — may fold into SLICE-003.

- Per ADR-003: "The D1 design slice is responsible for instrumenting the dogfood measurement; ADR-003 commits to the criterion, not the instrumentation."
- Dogfood measurement: catch-rate and false-positive-rate tracking, substrate for the 10-slice / 2026-10-11 evaluation.
- **Decision to defer to Phase 1 of SLICE-003**: one slice or two.

### Tier 2 — D2 code↔invariant binding

**SLICE-005 (D2 design)**

- **Depends on**: SLICE-003 (the refresh runner is D2's host).
- **Phase 1 decisions**:
  - Assertion-storage location: ADR frontmatter, separate `invariants.yaml`, or validator code.
  - Assertion language: Python callable, grep pattern, AST visitor, or a mix by invariant type.
  - Migration path for INV-001 (process-level — likely a commit-message / git-history audit, not a source-code audit) and INV-002 (three layers: token-bound grep + `wc`, literal-text grep for admission block, `ls .claude/current-slice/` on status transition).
- **Advisory-tier escape**: invariants without a machine-checkable form become `firmness: advisory` and do NOT count toward v1 defense satisfaction.

**SLICE-006 (D2 implementation)**

- Assertion runner integrated into `scripts/validate_architecture.py` or a successor.
- INV-001 and INV-002 assertions migrated from advisory to firm form.
- Per-invariant runtime budget and exception-count ceiling (ADR-003 Risk Register R3 mitigation).

### Tier 3 — D3 automated unknown-unknown backstop

**SLICE-007 (D3 design)**

- **Depends on**: SLICE-005/006 (D2 and D3 partially overlap on integration-sweep Step 3).
- **Phase 1 decisions**: structural-snapshot-diff check definition (per-file imports, type shapes, schema dependencies), snapshot storage format, comparison algorithm, envelope-aware filtering (files declared in `slice.yaml envelope` are exempt from diff flags).
- **Falsification test is a Phase 4 gate.** Per ADR-003: "D3's design slice must define a falsification test (a known case the check MUST catch). A D3 that cannot demonstrate catching a planted violation is rejected at design-slice Phase 4." This is the mitigation for Risk S6 (disarmed defense).

**SLICE-008 (D3 implementation)**

- Integration-sweep Step 3 and Step 4 promotion from manual to mechanical gate.
- Structural-snapshot-diff check wired.
- Planted-violation falsification test as committed evidence.

### Tier 4 — roadmap items folded into the defense slices

Existing `docs/roadmap.md` items that collapse into the D1/D2/D3 sequence:

- **Roadmap #2 (protocol extraction to plain markdown)** — plausibly part of P0a or a standalone pre-D1 cleanup slice. Not time-boxed.
- **Roadmap #3 (`state.json` + SHA-based catchup)** — re-evaluate after P0a. If phase rethink changes catchup's inputs, the state model may change.
- **Roadmap #10 (dogfood log infrastructure)** — folded into SLICE-003 / SLICE-004 as the dogfood measurement substrate. Required for ADR-003 supersession criterion.

### Time-boxed per ADR-003 D4 (v2+)

NOT on the v1 critical path. Any slice touching these requires explicit non-v1-scope waiver in `intent.md`:

- Vision commitment #1 (Windsurf portability, split-agent slices) → Roadmap #7, #8
- Vision commitment #2 (parallelism-native) → Roadmap #5, #6, #9
- Spec-v1 §9 three-track routing
- Vision commitment #6 mechanization (roles stay instructed, not hook-enforced)
- Retroactive invariant enforcement against existing code
- Slice pause/resume as a built-in command
- Cached-mind size management / `ARCHITECTURE.md` chunking
- Roadmap #4 (AGENTS.md migration) — unless justified as a D1/D2/D3 contributor

## Dogfood gate

Per ADR-003 supersession path:

- **Pass** iff D1/D2/D3 together catch ≥1 class of drift that integration-sweep Step 3's manual check would have missed in the same 10-slice window, AND no defense has a false-positive rate high enough to force muting.
- **Fail** iff either condition is violated.
- **Threshold-not-reached** (10 slices not reachable by 2026-10-11): itself the dogfood signal — the process is too heavy at the intended scale — triggers a lighter-reframing supersession.

Supersession outcomes, all three planned and acceptable:

- **Promote**: D1/D2/D3 demonstrably catch cliff-shape failures, false-positive rate acceptable. Successor ADR promotes ADR-003 to firm.
- **Amend**: a defense proves individually insufficient or wrong; successor ADR replaces/adds/removes specific defenses.
- **Reframe**: the cliff framing itself fails to match observed failures; successor ADR names a different primary target.

**Hard dependency freeze** until dogfood completes: no slice beyond D1/D2/D3's own design slices may take a hard dependency on the provisional defenses. Slices between dogfood start and dogfood completion are either D1/D2/D3 design slices themselves or non-v1-scope waiver slices.

## Open questions (revisit at each slice Phase 1)

- Does SLICE-003 carry dogfood instrumentation, or is it a separate SLICE-004?
- Minimum machine-checkable form of INV-001: process-level invariants grep against git history, not source. What substrate does D2 run that check on? (Candidate: pre-commit hook + periodic git-history audit.)
- P0a (phase rethink ADR) before SLICE-003, or can SLICE-003 be designed against current 4-phase shape and refactored later? Default: P0a first.
- Dogfood log format: absorbed into `.claude/learning.md` (ADR-002 reserved), a separate `docs/dogfood-log.md` (roadmap #10), or both?
- Does SLICE-002 resolve into an amendment (D2 contributor via INV-002 machine-checking) or a supersession?

## Where this plan lives and how it stays alive

- **This file** — the plan. Update in-place when a slice lands, a defense is amended, or dogfood signal arrives.
- **`docs/adr/003-cliff-failure-mode-and-v1-defenses.md`** — the immutable commitment. Any change to D0/D1/D2/D3/D4 is a new ADR superseding ADR-003, not an edit to this plan.
- **`docs/ARCHITECTURE.md § Current Phase Constraints`** — derived operational summary, regenerated by `/refresh-architecture`.
- **`.claude/handoff.md`** — pointer to this file in the `Pointers` section; never a copy.

**When this plan needs to change**, update it in the same slice that triggered the change. Do not let the drift live in handoff.md or in session memory.

---
id: ADR-007
title: Parallelism v1
status: accepted
firmness: provisional
supersedes:
  - "ADR-003 D4 (partial: parallelism deferral only)"
supersedes-sections:
  - "ADR-004 D4 (partial: skill exclusion list updates)"
superseded-by: null
topic: scope
invariants-touched: []
date: 2026-04-12
---

# ADR-007: Parallelism v1

## Status
Accepted

## Date
2026-04-12

## Context

ADR-003 D4 time-boxed parallelism to v2+: "Vision commitment #2 (parallelism-native) including the success criterion 'Two concurrent slices have completed on separate worktrees without interference.' v1 ships with single-slice discipline. v2 re-opens parallelism."

This deferral was appropriate when cairn had no feature grouping and no dependency model — running concurrent slices with only a global sequential counter and no dependency tracking would have been structurally unsafe. The feature-slice model (ADR-006) removes this blocker by introducing structured dependencies (`after` fields) and branch-local state (feature files on feature branches, slice.yaml on slice branches). Parallelism becomes a natural consequence of the model rather than an additional mechanism to design.

ADR-004 D4 excluded two Superpowers skills from the phase-to-skill mapping based on ADR-003 D4's single-slice discipline: `dispatching-parallel-agents` ("parallelism-native work violates v1 single-slice discipline per ADR-003 D4") and `using-git-worktrees` ("worktrees are for parallelism or isolation from shared state; v1 single-slice work does not need them"). With parallelism returning to v1, these exclusions no longer apply.

This ADR partially supersedes ADR-003 D4's parallelism deferral and partially supersedes ADR-004 D4's skill exclusion list. All other ADR-003 D4 time-boxed items and ADR-004 D4 exclusions are evaluated below and either confirmed as still deferred or returned to v1 scope.

## Decision

### D0 — Parallelism is v1-native

Cairn v1 supports concurrent slice execution. This supersedes ADR-003 D4's deferral of "Vision commitment #2 (parallelism-native)." The success criterion "Two concurrent slices have completed on separate worktrees without interference" returns to the v1 acceptance criteria.

### D1 — Concurrency rules

Slices without unmet `after` constraints in their feature file can run concurrently. Concurrency is available at two levels:

- **Feature-level parallelism.** Different features on different branches. No interaction unless features touch overlapping files (detected at integration).
- **Intra-feature parallelism.** Different slices within the same feature on separate branches. The `after` field in the feature file governs ordering; slices whose `after` dependencies are all complete can start.

### D2 — No global active-slice pointer

State is branch-local. There is no `.claude/active-slice` or equivalent global pointer that would serialize slice execution. Each branch carries its own `slice.yaml`; each feature branch carries its own feature file. `/catchup` on any branch reads that branch's state.

### D3 — ADR-004 D4 skill exclusion updates

ADR-004 D4 listed five Superpowers skills as explicitly excluded from the phase-to-skill mapping. This ADR updates the exclusion status of each:

**Returned to v1 scope (un-excluded):**

- `dispatching-parallel-agents` — returns as a supporting skill for Phase 3 (Builder). Within-slice parallel dispatch for independent tasks in the envelope is v1-legal. This was already noted as permitted in `docs/operational-reference.md` Phase Skill Guide but was formally excluded by ADR-004 D4's text. This ADR resolves the inconsistency.
- `using-git-worktrees` — returns as a conditional supporting skill for Phase 3 (Builder) when subagent-driven tasks require workspace isolation. Also available for cross-slice parallel work.

**Remaining excluded (unchanged from ADR-004 D4):**

- `executing-plans` — remains excluded. The parallel-session variant of `subagent-driven-development`; inside a Phase 3 session, same-session subagent dispatch is the right choice. Exclusion rationale is independent of parallelism.
- `finishing-a-development-branch` — remains excluded. Cairn's slice-close protocol (`/start-slice complete`) supersedes it for slice work. Exclusion rationale is independent of parallelism.
- `writing-skills` and `writing-plans` — remain excluded. Meta-skills that sit outside any slice phase. Exclusion rationale is independent of parallelism.

### D4 — Other ADR-003 D4 time-boxed items: disposition

ADR-003 D4 time-boxed several items beyond parallelism. Each is addressed:

- **Vision commitment #1 (full agent portability — Windsurf)**: remains deferred to v2+. Parallelism within Claude Code does not require Windsurf support.
- **Spec-v1 §9 (three-track routing)**: remains deferred. Work-type routing is orthogonal to parallelism.
- **Mechanized role assignment per phase**: remains deferred. Roles stay instructed in protocol text per ADR-004 D2.
- **Retroactive invariant enforcement against existing code**: remains deferred to v2+.
- **Slice pause/resume as a built-in command**: partially addressed by ADR-006 D6 (parked state protocol). The structured `parked: true` + `blocked-by` mechanism replaces the need for a dedicated pause/resume command. Remains deferred as a built-in command; the feature file mechanism is sufficient for v1.
- **Cached-mind size management / ARCHITECTURE.md chunking**: remains deferred to v2+.

## Consequences

- **ADR-003 D4 is partially superseded.** Only the parallelism deferral is lifted. D0/D1/D2/D3 of ADR-003 are unaffected. The `supersedes` field in this ADR's frontmatter records the partial scope.

- **ADR-004 D4's exclusion list is updated.** `dispatching-parallel-agents` and `using-git-worktrees` return to the Phase Skill Guide. The `docs/operational-reference.md` Phase Skill Guide is updated by the implementation slice that lands ADR-007's operational changes.

- **The Phase Skill Guide in `docs/operational-reference.md` requires update.** The current guide already notes within-slice parallel dispatch as permitted, but the formal exclusion text from ADR-004 D4 must be reconciled. The implementation slice updates the Explicit Exclusions section.

- **Worktree lifecycle is an implementation concern.** This ADR commits to parallelism being v1-legal but does not specify git branching strategy, worktree creation conventions, or merge ordering. These are implementation details for the slice that operationalizes parallelism.

- **Dogfood validation required.** This ADR is `firmness: provisional` because parallelism has not been operationally tested in cairn. The first concurrent-slice execution is the validation event. If concurrent slices produce merge conflicts, integration failures, or state corruption that the feature-file dependency model does not prevent, this ADR is superseded with tighter constraints or reverted to ADR-003 D4's deferral.

## Risk Register

- **Risk: Merge conflicts between concurrent slices touching overlapping files.** The feature-file dependency model (`after` fields) prevents known ordering violations, but cannot prevent two independent slices from modifying the same file if neither declares the other as a dependency. **Mitigation:** Phase 4 (Integration) catches file-level conflicts at merge time. The `/integration-sweep` protocol detects cross-slice interference. Persistent conflicts in a file are a signal to add an `after` dependency or split the file.

- **Risk: Stale handoff pointers when multiple slices complete between catchup sessions.** With single-slice discipline, handoff always reflects the most recent slice. With parallelism, multiple slices may complete and each updates handoff, potentially overwriting the other's pointers. **Mitigation:** `/handoff` updates are append-style (add pointer, not replace file). `/catchup` Tier 1 reads git log to detect completed slices that handoff may have missed. The cross-feature index in handoff provides a stable overview regardless of individual slice churn.

- **Risk: Within-slice subagent dispatch (dispatching-parallel-agents) produces race conditions on shared files.** Two subagents writing the same file simultaneously corrupt it. **Mitigation:** `dispatching-parallel-agents` skill documentation already requires independent tasks with non-overlapping file sets. The slice envelope declares the file set; subagents must partition it.

- **Risk: Provisional firmness means downstream slices built on parallelism face churn cost if this ADR is superseded.** **Mitigation:** The first implementation slice that exercises parallelism is the dogfood event. If it fails, supersession happens before further slices accumulate. The provisional framing keeps the revert path cheap.

- **Risk: Cognitive overload — tracking multiple active slices exceeds the developer's mental model capacity, recreating the cliff failure mode ADR-003 targets.** **Mitigation:** The feature file provides the decomposition artifact that replaces the mental model. `/catchup` Tier 1's cross-feature index provides the overview. The `after` field constrains which slices can run, bounding the active set. If cognitive load remains problematic, the maximum concurrent slice count can be constrained in a follow-up ADR.

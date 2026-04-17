---
id: feature-slice-model
title: Feature-Slice Model
status: accepted
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-04-12
---

# feature-slice-model: Feature-Slice Model

## Status
Accepted

## Date
2026-04-12

## Context

Dogfooding cairn in consumer projects revealed three structural problems in the current slice model:

1. **No feature grouping.** Related slices lack grouping metadata. Multi-slice work (e.g., a capability that requires ADR creation, hook updates, and test infrastructure) has no decomposition artifact. The human carries the decomposition in their head; the system cannot reason about it.

2. **Dependencies implicit in prose.** Slice-to-slice ordering lives in handoff prose ("do X before Y"), not in structured data. No tool can compute a dependency graph, detect blocked slices, or identify parallelizable work.

3. **Single-responsibility violations.** `handoff.md` currently carries both cross-session pointers (its context-discipline-protocol Layer 1 role) and implicit decomposition state (which slices exist, what order they run in). This dual role makes handoff fragile — a decomposition change forces a handoff rewrite even when the current session's state hasn't changed.

These problems share a root cause: the slice model doesn't represent decomposition. Work arrives as features (bugs, capabilities, experiments), gets decomposed into slices, and the decomposition evolves as slices complete. The model needs to capture this.

## Decision

### D0 — Features are the unit of intent; slices are the unit of execution

A **feature** is any reason you branch: a bug fix, a new capability, an experiment, a design/decision batch. Each feature has a semantic kebab-case ID (per semantic-identity).

A **slice** is a unit of execution within a feature. Each slice goes through the 4-phase cycle (Intent → Validation → Implementation → Integration, per phase-lock-and-role-declaration / INV-003). Each slice has its own semantic kebab-case ID. A simple feature has exactly one slice.

There is no type taxonomy for slices. Phase 3 produces the deliverable — code, ADRs, findings, whatever the intent specifies. The phase pipeline is type-agnostic.

### D1 — Single-responsibility file model

Each piece of state lives in exactly one file. No duplication, no sync burden.

| File | Lives on | Owns |
|------|----------|------|
| `handoff.md` | dev branch | Active feature/slice pointers, next steps, blockers, cross-feature index |
| `.claude/features/<id>.yaml` | Feature branch | Slice list, ordering (`after` fields), feature intent |
| `.claude/current-slice/slice.yaml` | Slice/feature branch | Current phase, invariants, ADR refs, parked state |

### D2 — Feature file structure

Feature files live at `.claude/features/<id>.yaml` and are created during brainstorming or design, before the first slice begins. A feature file is a planning artifact that evolves as decomposition changes at handoff checkpoints.

Required fields: `id`, `intent`, `created`. The `slices` list contains entries with `id` (required), `after` (optional dependency list), `added` (date the slice was added to the plan), and `status: dropped` with optional `reason` for slices that are abandoned.

Discipline rules:

- Dropped slices stay in the file with `status: dropped` and optional `reason` — append-only spirit, never deleted
- New slices get an `added` date for decomposition change visibility
- No narrative in the feature file — structured plan only
- Updated at handoff checkpoints when decomposition changes
- Changes committed for audit trail via git log
- Manual close — features don't auto-close (decomposition evolves)

### D3 — Always-create policy

Even single-slice features get a feature file. This eliminates the routing question "is this big enough to need a feature file?" and ensures every piece of work has a decomposition artifact, even if the decomposition is trivially one slice.

### D4 — Status derived from state, not stored

Slice status is derived from observable state, not duplicated in storage:

| Status | How determined |
|--------|---------------|
| Planned | Listed in feature file, no branch exists |
| Active | Branch exists, `parked` absent or false in slice.yaml |
| Parked | Branch exists, `parked: true` + `blocked-by` in slice.yaml |
| Complete | Branch merged |
| Dropped | `status: dropped` in feature file (the one stored exception — dead branches leave no trace) |

The only stored status is `dropped`, because a dropped slice's branch may never have existed or may have been deleted. All other statuses are observable from git and file state.

### D5 — Trigger-based updates

No background sync. Each event updates a specific, bounded set of files. Maximum 2 files per event.

| Event | Updates | Max files |
|-------|---------|-----------|
| Brainstorming complete | Feature file created | 1 |
| `/start-slice` | Handoff pointer + slice.yaml created | 2 |
| Phase transition | slice.yaml | 1 |
| `/handoff` (slice end) | Handoff pointer + branch merged | 2 |
| Decomposition change | Feature file | 1 |
| Feature done | Handoff pointer + feature branch merged | 2 |

Skills (`/start-slice`, `/handoff`, brainstorming) are the synchronizers. `/catchup` detects stale handoff pointers as a repair mechanism, not a sync mechanism.

### D6 — Parked state protocol

When a slice discovers a missing prerequisite mid-work:

1. Park the current slice: set `parked: true` and `blocked-by: [prerequisite-id]` in slice.yaml
2. Add the prerequisite as a new slice in the feature file
3. Update `after` fields to reflect the new dependency
4. Work on the prerequisite
5. Resume the parked slice when prerequisite completes

Branch and work-in-progress are preserved. Slice identity stays the same. The parked state is the structured replacement for the ad-hoc "stopped" state that SLICE-002 used.

### D7 — Mid-work discovery protocol

Three scenarios, all handled by existing mechanisms:

1. **Prerequisite found.** Park current slice. Add dependency slice to feature file. Update `after` fields.
2. **Scope too large.** Park or drop current slice. Re-decompose at the feature level — replace one slice with several in the feature file. Partial work on the original branch can be cherry-picked.
3. **Phase is just hard.** Continue. Phases don't have time limits.

All discoveries surface at handoff checkpoints. The `/handoff` skill prompts "Decomposition changes?" to trigger feature file updates.

## Consequences

- **Multi-slice work has a decomposition artifact.** The feature file replaces the implicit mental model with a structured plan that tools and agents can reason about.

- **Dependencies are machine-readable.** The `after` field in feature file slice entries enables dependency graph computation, blocked-slice detection, and parallelism identification (see parallelism-v1).

- **Handoff returns to single responsibility.** `handoff.md` carries cross-session pointers (context-discipline-protocol Layer 1) and a lightweight cross-feature index. Decomposition detail moves to the feature file.

- **Implementation slices required.** This ADR describes the information model; implementation slices will create the `.claude/features/` directory, update `/start-slice` and `/handoff` to read/write feature files, and update scope-guard for the new paths.

- **phase-lock-and-role-declaration INV-003 is unaffected.** The 4-phase pipeline applies to each slice within a feature. Features add a grouping layer above slices; they do not modify the phase pipeline.

- **Existing slices are not retroactively migrated.** Completed slices (SLICE-001 through current) retain their identities in git history. The feature file model applies to new work going forward.

# Feature-Slice Model Design

Date: 2026-04-12

## Context

Dogfooding cairn in consumer projects (complex-rag-analysis) revealed three structural problems in the current slice model:

1. **Sequential numbering blocks multi-dev.** Global counter (SLICE-001, SLICE-002...) prevents parallel slice creation without conflicts.
2. **No feature grouping.** Related slices lack grouping metadata. Multi-slice work has no decomposition artifact.
3. **Dependencies implicit in prose.** Slice-to-slice ordering lives in handoff prose, not structured data.

These problems share a root cause: the slice model doesn't represent decomposition. Work arrives as features (bugs, capabilities, experiments), gets decomposed into slices, and the decomposition evolves as slices complete. The model needs to capture this.

## Design

### Core Model

**Features** are the unit of intent. A feature is any reason you branch: a bug fix, a new capability, an experiment, a design/decision batch. Each feature has a semantic kebab-case ID (e.g., `context-discipline`, `token-refresh-fix`, `slice-model-redesign`).

**Slices** are the unit of execution within a feature. Each slice goes through the 4-phase cycle (Intent, Validation, Implementation, Integration — unchanged per ADR-004/INV-003). Each slice has a semantic kebab-case ID. A simple feature has exactly one slice.

**No types.** Phase 3 is "produce the deliverable" — code, ADRs, findings, whatever. There is no type taxonomy for slices.

**No sequential counters anywhere.** Slices, ADRs — all semantic kebab-case IDs. Collision avoidance: semantic names are naturally unique across concurrent work.

### Single-Responsibility File Model

Each piece of state lives in exactly one file. No duplication, no sync burden.

| File | Lives on | Owns |
|------|----------|------|
| `handoff.md` | dev | Active feature/slice pointers, next steps, blockers, cross-feature index |
| `.claude/features/<id>.yaml` | Feature branch | Slice list, ordering (`after` fields), feature intent |
| `.claude/current-slice/slice.yaml` | Slice/feature branch | Current phase, invariants, ADR refs, parked state |

**Status is derived, not stored:**

| Status | How determined |
|--------|---------------|
| Planned | In feature file, no branch exists |
| Active | Branch exists, `parked` absent or false in slice.yaml |
| Parked | Branch exists, `parked: true` + `blocked-by` in slice.yaml |
| Complete | Branch merged |
| Dropped | `status: dropped` in feature file (the one exception — dead branches leave no trace) |

### Feature File (planning artifact)

Created during brainstorming/design. Lives on the feature branch. Evolves as decomposition changes at handoff checkpoints.

```yaml
id: slice-model-redesign
intent: "Semantic IDs, feature grouping, dependency model, parallelism"
created: 2026-04-12
slices:
  - id: adr-rename
    added: 2026-04-12
  - id: identity-and-features
    after: [adr-rename]
    added: 2026-04-12
  - id: hook-updates
    after: [identity-and-features]
    added: 2026-04-12
```

**Discipline (from ADR/handoff learnings):**
- Dropped slices stay with `status: dropped` + optional `reason` (append-only spirit, never deleted)
- New slices get `added:` date (decomposition change visibility)
- No narrative in the feature file — structured plan only
- Updated at handoff checkpoints when decomposition changes ("Decomposition changes?" prompt)
- Changes committed for audit trail via git log
- Manual close — features don't auto-close (decomposition evolves)
- Always-create policy — even single-slice features get a feature file

### Trigger-Based Updates

No background sync. Each event has a specific, bounded set of writes. Max 2 files per event.

| Event | Updates | Max files |
|-------|---------|-----------|
| Brainstorming complete | Feature file created | 1 |
| `/start-slice` | Handoff pointer + slice.yaml created + branch created | 2 |
| Phase transition | slice.yaml | 1 |
| `/handoff` (slice end) | Handoff pointer + branch merged | 2 |
| Decomposition change | Feature file | 1 |
| Feature done | Handoff pointer + feature branch merged to dev | 2 |

Skills are the synchronizers (`/start-slice`, `/handoff`, brainstorming). `/catchup` detects stale handoff pointers as a repair mechanism.

### Slice Lifecycle

```
planned → active → [parked →] active → complete
                                     → dropped
```

**Parked state:** When a slice discovers a missing prerequisite mid-work:
1. Park the current slice (`parked: true`, `blocked-by: [prerequisite-id]` in slice.yaml)
2. Add the prerequisite as a new slice in the feature file
3. Update `after` fields to reflect the new dependency
4. Work on the prerequisite
5. Resume the parked slice when prerequisite completes

Branch and work-in-progress are preserved. Identity stays the same.

### Mid-Work Discovery Protocol

Three scenarios, all handled by existing mechanisms:

1. **Prerequisite found.** Park current slice. Add dependency slice to feature file. Update `after` fields.
2. **Scope too large.** Park or drop current slice. Re-decompose at the feature level — replace one slice with several in the feature file. Partial work on the original branch can be cherry-picked.
3. **Phase is just hard.** Continue. Phases don't have time limits.

All happen at handoff checkpoints.

### Parallelism (v1-native)

Parallelism is structural, not an edge case. ADR-003 D4 (parallelism deferral to v2) is superseded.

- Slices without unmet `after` constraints can run concurrently
- Feature-level parallelism: different features on different branches
- Intra-feature parallelism: different slices on separate branches within a feature
- No global "active slice" pointer — state is branch-local

### Context Tiers (ADR-002 compatibility)

The model preserves the three-tier context discipline:

- **Tier 1** (always loaded): `handoff.md` on dev has cross-feature index (one-liner per active feature). Stays within 150-400 token budget.
- **Tier 2** (on-demand): Feature file loaded when entering that feature's branch. Decomposition detail is here.
- **Tier 3** (working context): slice.yaml on active branch. Focused on current work.

Feature inventory for Tier 1 derived from handoff's feature index. Feature detail is Tier 2. No context budget regression.

### ADR Identity Change

All ADRs move from sequential to semantic IDs:
- `001-bootstrap-exception.md` → `bootstrap-exception.md`
- `002-context-discipline-protocol.md` → `context-discipline-protocol.md`
- `003-cliff-failure-mode-and-v1-defenses.md` → `cliff-failure-mode.md`
- `004-phase-lock-and-role-declaration.md` → `phase-lock-and-role-declaration.md`

Cross-references use filename stem: `adrs-referenced: [cliff-failure-mode]`

`reversibility-guard.sh` glob changes from `*/docs/adr/[0-9]*` to `*/docs/adr/*.md` with `index.md` excluded.

### Interactions with Existing ADRs and Roadmap

| Item | Impact |
|------|--------|
| ADR-003 D4 (parallelism deferral) | **Superseded.** Parallelism is v1. New ADR required. |
| ADR-004 D4 exclusions | `dispatching-parallel-agents` and `using-git-worktrees` no longer excluded |
| ADR-004 phases (INV-003) | **Unchanged.** 4-phase cycle still applies to each slice. |
| Roadmap 3 (state.json) | Orthogonal — SHA-based catchup can coexist with feature files |
| Roadmap 5 (branch-local state) | **Covered** by this design's branching model |
| Roadmap 6 (parallelism support) | **Covered** — this IS the parallelism design |
| Roadmap 9 (concurrent validation) | **Covered** — acceptance test for this design |
| Scope-guard Phase 3 | Allowlist broadened for non-code deliverables |

### Git Cycle

The branching strategy, merge conventions (squash merge for feature file changes, slice completions, feature completions), and worktree lifecycle are deferred to implementation planning. The design describes the information model; git workflow is an implementation detail.

### ADRs This Design Produces

- **Feature-slice model ADR** — formalizes this design
- **Semantic identity ADR** — covers slice and ADR naming; partially supersedes ADR-003 D4

### Migration Path

1. Rename existing ADRs (sequential → semantic) + update `reversibility-guard.sh` glob
2. Create `.claude/features/` directory structure + feature file template
3. Update `/start-slice` for semantic IDs + feature file context
4. Update `/handoff` for feature file decomposition prompts
5. Broaden scope-guard Phase 3 allowlist
6. Update ADR-004 D4 exclusions
7. Produce new ADRs (feature-slice model + semantic identity)
8. First new-model feature runs end-to-end as validation

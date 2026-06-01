# Phase 0 — Constraint Envelope (git-workflow-v1)

`feat/<feature-id>` off `dev` + `merge --no-ff`. `[V]` = operator's `--no-ff`/operator-owned-interim choice could violate.

## [git enforcement]
1. Force-push blocked; `--force-with-lease` allowed — `reversibility-guard.sh:24-26`. Rewriting `dev` is barred; `--no-ff` (additive) is safe.
2. `reset --hard`/`clean -fd`/`rm -rf` blocked — `reversibility-guard.sh:22-28`. Abandoned `feat/` branches drop via plain `git branch -d/-D` only.
3. ADRs append-only: Write on existing `docs/adr/*.md` denied; Edit only if `old_string` line 1 = `status:|superseded-by:|superseded_by:|firmness:` — `reversibility-guard.sh:59-106`. Supersession is frontmatter-Edit only; new `git-workflow-v1.md` Write is permitted.
4. `role_guard.py` does NOT strip `.slice-system/` (reversibility-guard does, `:48,76`) — edit canonical paths only.
5. Operator-session writes gated by `.claude/active-envelope.yaml` when `AGENT_ROLE` unset; fail-closed — `role_guard.py:142-165`. `[V]` operator-owned merge runs in operator session: if `mode: operator`, `paths:` must permit `docs/adr/` + hooks. Hook gates Write/Edit only, not Bash `git merge`.

## [commit/phase contract]
6. INV-001: every commit prefix in `_FALLBACK_REGISTRY`; `git-log-walk` since `2fb83f6` — `ARCHITECTURE.md:13-20`. The 4 phase prefixes are registered. `[V]` `merge --no-ff` default `Merge branch …` subject is unregistered — confirm the walk skips merge commits (first-parent) or give the merge a registered conventional subject.
7. INV-003: exactly 4 ordered phases, names/roles locked, supersession-only — `ARCHITECTURE.md:30-37,97-104`. Branch model adds no phase.
8. SKILL emits 4 phase commits to current HEAD, creates NO branch, NO merge — `SKILL.md:80,91,95`. D6 operator-owned-interim is consistent (skill stays branch-agnostic).
9. `SNAPSHOT_SHA = rev-parse HEAD` at start; Phase 4 baseline anchors on it + `/tmp/<id>-baseline-failures.txt` — `SKILL.md:56,30,36`. `[V]` rebase-onto-dev rewrites phase SHAs vs SNAPSHOT_SHA → D2's rebase rejection is load-bearing; `--no-ff` preserves SHAs. Capture SNAPSHOT_SHA after `feat/` checkout (HEAD identical).
10. L-011: phase-handoff commits are content-bearing; dirty tree across a boundary is the named failure — `lessons.md:206-223`. Merge only after all 4 phase commits land.

## [handoff/state placement]
11. INV-002: `.claude/handoff.md` contract-frontmatter + pointer body, lives on `dev` — `ARCHITECTURE.md:22-27`; `feature-slice-model.md:48-52`. `[V]` Phase 4 appends pointer on `feat/`; `--no-ff` carries it back, but concurrent features (deferred D4) conflict on `handoff.md` — flag for D4.
12. L-005: merge reconciliation cost is in pipeline-substrate files (handoff/feature/sweep), bounded ~5-10min, not code — `lessons.md:92-104`. Inherited only when concurrent.
13. Skill workspace `.claude/skill-runs/<id>/`, cleanup operator-discretion — `SKILL.md:40-44`. Rides `feat/`, merges with phase commits.

## [naming]
14. INV-005: immutable `id:` + mutable `name:`; ADR/feature ids flat slugs — `ARCHITECTURE.md:47`, `identifier-scheme.md:64-73`. `feat/<feature-id>` uses the flat slug — consistent.
15. identifier-scheme D4: slice branches `slice/<feature>/<slice>` — `identifier-scheme.md:89-97`. SUPERSEDE: D3 → `feat/<feature-id>`. `[V]` must explicitly supersede this D4 or two naming rules coexist.
16. identifier-scheme D2 "Slice" row asserts hierarchical slice id — `identifier-scheme.md:64-73`. Amend, don't delete.
17. Commit scope `<type>(<feature-id>): …` — context.md:57, matches INV-001 registry. Already feature-keyed.

## [distribution boundary]
18. dev → `release` → payload → `v0.x.y` (m5/INV-012) — `ARCHITECTURE.md:87`. `feat/` merges into `dev`, NOT `release`; new model sits upstream of release cadence.
19. INV-011: `.slice-system → .` self-symlink; recursion hazard — `ARCHITECTURE.md:79-85`. Any `feat/`-branch globbing must exclude `.slice-system`.

## [invariants — feature/slice model]
20. INV-006: one-file state; status DERIVED from branch existence + merge state + `parked`, except stored `dropped` — `ARCHITECTURE.md:55`, `feature-slice-model.md:74-85`. `[V]` "Complete = branch merged" must re-anchor on `feat/<feature-id>` merge into `dev`; the derivation table (`:76-85`) references slice branches → amend with D1/D4.
21. feature-slice-model D5 trigger table names retired `/start-slice`+`/handoff` and "branch merged" — `feature-slice-model.md:88-100`. SUPERSEDE: merge event re-homes to operator-owned `merge --no-ff`.
22. feature-slice-model D1: feature files on feature branch, slice.yaml on slice branch — `feature-slice-model.md:48-52`. SUPERSEDE: slice branches gone; `.claude/features/<id>.yaml` re-anchors to `feat/` or `dev`.
23. parallelism-v1 D1/D2: concurrent slices, branch-local state, no global pointer — `parallelism-v1.md:38-49`. Deferred D4 inherits; single-operator interim defers cleanly.
24. parallelism-v1 Consequences PUNT branching/worktree/merge-ordering to "the slice that operationalizes parallelism" (never shipped) — `parallelism-v1.md:85-87`. The open hole D4/D5 record as deferred; amend this concern here.

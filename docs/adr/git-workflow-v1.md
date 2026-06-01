---
id: git-workflow-v1
name: "Git workflow v1 — branch-per-feature, --no-ff integration, feature-level naming"
status: accepted
firmness: firm
supersedes: []
supersedes-sections:
  - "feature-slice-model D1 (state-file branch homes — slice.yaml / feature-file placement)"
  - "feature-slice-model D4 (status-from-branch-state derivation table)"
  - "feature-slice-model D5 (/start-slice + /handoff trigger events)"
  - "identifier-scheme D4 (slice/<feature>/<slice> branch naming)"
superseded-by: null
topic: process
adrs-referenced: [feature-slice-model, identifier-scheme, parallelism-v1, m5-plugin-distribution-and-symlink-retire, invariant-binding-strategy, phase-lock-and-role-declaration, slice-close-contract-superseded]
invariants-touched: [INV-001, INV-006]
date: 2026-05-31
---

# git-workflow-v1: Git workflow — branch-per-feature, --no-ff integration, feature-level naming

## Status
Accepted (firm). Falsification tripwire in "Load-bearing belief" below.

## Date
2026-05-31

## Context

The merge model was not merely undocumented — the firm ADRs that describe it
reference machinery retired at M4 (2026-05-07, `slice-close-contract-superseded`).

**Post-M4 reality (authoritative).** `.claude/skills/cairn-tdd-feature/SKILL.md`
is the dispatch primitive. It emits four phase commits — `feat(<id>): phase 1 — intent`,
`test(<id>): phase 2 — RED tests`, `feat(<id>): phase 3 — implementation`,
`chore(<id>): phase 4 — sweep + handoff` — to **whatever branch HEAD is on**. It
creates no branch and has no merge step (SKILL.md:91 "the git log is the durable
record; no slice.yaml"). It captures `SNAPSHOT_SHA = git rev-parse HEAD` at start
(SKILL.md:56) and anchors Phase-4 regression attribution on that snapshot. Work has
been landing directly on `dev`; `dev` history is currently linear.

**Firm ADRs that contradict reality.** `feature-slice-model` (firm) D1 homes state
files on slice/feature branches, D4 derives "Complete = branch merged", D5 drives
integration through `/start-slice` + `/handoff` skills — all retired with the
orchestrator. `identifier-scheme` (firm) D4 mandates `slice/<feature>/<slice>` branch
names; the sub-slice unit no longer exists as a branch. `parallelism-v1` (provisional)
assumes concurrent slice branches/worktrees but **explicitly punts** branching strategy,
worktree creation, and merge ordering to "the slice that operationalizes parallelism" —
which never shipped (the orchestrator was retired first).

**Already settled, out of scope.** `m5-plugin-distribution-and-symlink-retire` (firm)
decides dev → `release` → curated `dist/` → `v0.x.y` tags. This ADR governs the
`dev`-side working-branch/merge/naming model only and cross-references that boundary.

This ADR was reached through the full `/decision` protocol (Phases 0–5, artifacts under
`.claude/skill-runs/git-workflow-decision/`). Phase 5 independent fresh-context
verification converged on the same model and the same decisive justification (below),
which is the primary evidence against correlated error.

## Decision

Cairn commits to three properties of the `dev`-side git workflow. D4/D5/D6 are recorded
as deferred open questions (they answer concurrency needs the solo operator does not yet
have; deciding them now would be untested machinery).

### D1 — Branch-per-feature (prescribed workflow)

Every feature developed after this ADR runs on a `feat/<feature-id>` branch cut from
`dev`. The `<feature-id>` is the same identifier the dispatch skill derives (plan-doc
frontmatter `id:` or filename stem). The branch is cut at the point that becomes the
skill's `SNAPSHOT_SHA`.

This is a **prescribed-workflow rule, instructed and not hook-enforced** — consistent
with the INV-003 "instructed not enforced" posture (`phase-lock-and-role-declaration`).
It does **not** alter INV-001: operator-envelope-gated direct commits remain
prefix-valid (`docs/ARCHITECTURE.md:13`), so existing linear `dev` history stays
conformant and the rule applies prospectively. A direct-to-`dev` commit does not red the
validator; it is a workflow deviation, not an invariant violation. Mechanical
enforcement of the branch origin is deferred to D6.

### D2 — Integration via `git merge --no-ff`

A completed feature integrates into `dev` with `git merge --no-ff feat/<feature-id>`,
producing the four phase commits plus one merge commit on `dev`.

- **`--no-ff` is decisive, not aesthetic.** It preserves all four phase commits — the
  intent→RED→GREEN→audit trail that INV-001's per-prefix verifiers and the Phase-4
  audit both consume — while adding a single merge node per feature.
- **Merge-commit exemption (the `--no-merges` contract).** A `--no-ff` merge subject
  (`Merge branch 'feat/<id>'`) is an unregistered Conventional-Commits prefix. INV-001
  permits unregistered prefixes "except as recorded in a superseding ADR"
  (`docs/ARCHITECTURE.md:13`); **this ADR is that record.** The exemption is mechanically
  real because the INV-001 walk runs with `--no-merges`
  (`scripts/validate_architecture.py:367`), so merge commits are never classified. This
  is a **live contract, not future-proofing**: `dev` already carries merge commits the
  walk skips; removing `--no-merges` would red the walk today. `--no-merges` must not be
  removed without superseding this ADR.
- **Reject squash** — collapses the phase-commit prefixes and orphans `SNAPSHOT_SHA`,
  destroying the audit anchor.
- **Reject rebase-as-integration and forbid mid-feature rebase** — rebasing rewrites the
  four phase SHAs that `intent.md`, `sweep-notes.md`, and the handoff pointer cite against
  `SNAPSHOT_SHA`. If `dev` advances during feature work, the `--no-ff` merge's 3-way merge
  integrates it; no rebase is needed.
- **Merge ceremony.** `git merge --no-ff` only — never `-ff`, never `--squash`. This is
  instructed; no hook guards it (see Risk Register F5). The guard is deferred to D6.
- **Canonical history view.** `git log --first-parent dev` is the per-feature view (one
  node per feature); it is what `/catchup` and the M5 `release`/`dist/` cut should read to
  avoid per-feature phase-commit noise.

### D3 — Feature-level naming and branch taxonomy

The unit of work is the **feature**; there are no sub-slice branches. This supersedes
`identifier-scheme` D4 (`slice/<feature>/<slice>`) at the branch-naming level; the
`identifier-scheme` two-field `id:`/`name:` model (D1/D2/D3/D9) and INV-005 stand
unchanged.

Branch taxonomy:

| Prefix | Meaning |
|--------|---------|
| `feat/<feature-id>` | active feature under `cairn-tdd-feature` development |
| `plan/<slug>` | design / brainstorm / decision branches not yet a feature |
| `archive/<slug>` | frozen reference branches kept for provenance |
| `abort/<slug>` | abandoned work preserved with its trail |

`feat` is also the commit-*type* prefix (`feat(<id>): …`); the branch prefix `feat/` and
the commit prefix `feat(` are distinct namespaces and do not collide.

**State placement (supersedes `feature-slice-model` D1).** Phase 4 continues to append
`.claude/handoff.md` on the `feat/` branch; the `--no-ff` merge carries that append to
`dev`. The "handoff lives on `dev`" placement of `feature-slice-model` D1 is restated as
"handoff reaches `dev` via the feature merge." Concurrent-feature handoff-append collision
is the deferred D4 concern.

**Status derivation (supersedes `feature-slice-model` D4; touches INV-006).** A feature is
**Complete** when `feat/<feature-id>` is merged `--no-ff` into `dev` with a Phase-4 PASS.
INV-006's "feature contains one or more slices (unit of execution)" and its
branch-existence/merge-state derivation are re-anchored from slice branches to feature
branches; the always-create feature-file policy and `schema-amendment-threshold` clauses
of INV-006 are untouched.

### Deferred — recorded open questions (gated on the first real concurrent feature)

These take ownership of the lifecycle `parallelism-v1` left as "an implementation concern."
They are recorded, not decided.

- **D4 — Concurrent / out-of-order completion.** The rebase-or-re-merge rule for a trailing
  feature; the `.claude/handoff.md` append collision when two features merge (Risk Register
  F1); the per-feature `/tmp/<id>-baseline-failures.txt` clobber (F3).
- **D5 — Worktree lifecycle.** Optional worktree-per-feature create + cleanup, and the
  per-worktree copy of `.claude/active-envelope.yaml` (role_guard is worktree-scoped and
  fail-open when the envelope is absent). Live precedent: `.worktrees/feature-compression`.
- **D6 — Enforcement graduation.** (a) skill automation of branch create/merge versus the
  operator-owned interim; (b) a `reversibility-guard.sh` arm that denies `git merge --squash`
  and non-`--no-ff` merges of `feat/*` into `dev` (the F5 mitigation); (c) a branch-origin
  check that mechanizes D1. Graduate when the manual ceremony proves friction-worthy.

## Consequences

**Easier.**
- The four phase commits — the entire audit chain `intent.md`/`sweep-notes`/handoff anchor
  against `SNAPSHOT_SHA` — survive integration unchanged, with zero change to the dispatch
  skill.
- Features are isolated on branches, unblocking `parallelism-v1` execution without the
  retired orchestrator.
- The naming model finally matches the post-M4 feature unit; the three stale ADRs stop
  contradicting reality.
- `git log --first-parent dev` gives a clean one-node-per-feature history.

**Harder.**
- `dev` gains five commits per feature (four phase + one merge). Mitigated by the
  `--first-parent` view; raw `git log` is noisier.
- The merge step is instructed-not-enforced (F5): a single `--squash`/`-ff`/forgotten merge
  silently destroys the trail. No mechanical backstop until D6.
- The `--no-merges` exemption is a one-flag-fragile contract: dropping `--no-merges` from
  `validate_architecture.py:367` reds every merge. Pinned here; tested via the verification
  task.

**Invariant impact.**
- **INV-001** — this ADR is recorded as the superseding authority for merge commits on
  `dev` (the `--no-merges` exemption). The registered direct-commit set is unchanged;
  direct-to-`dev` work stays prefix-valid.
- **INV-006** — status derivation and the execution-unit re-anchor from slices to features.
  `/refresh-architecture` propagates the re-anchored text.
- **INV-003** — unchanged; D1's instructed posture is consistent with it, not an amendment.

**Distribution boundary.** Unchanged. The `release`/`dist/` cut
(`m5-plugin-distribution-and-symlink-retire`) reads `dev`; `--first-parent` keeps that cut
readable.

## Alternatives Considered

- **B — worktree-per-feature.** Stronger physical isolation, but it does not fix the F1
  handoff collision or the F3 baseline clobber (both features still merge to the same `dev`),
  worsens F5 by adding unguarded create/teardown, and forces the D5 worktree lifecycle
  `parallelism-v1` deferred plus per-worktree envelope copies. For a solo operator it solves
  a concurrency problem not yet present. Recorded as the D5 path, not adopted now.
- **C1 — direct-to-dev (status quo).** The cleanest INV-001 / force-push / `SNAPSHOT_SHA`
  story (no merge commits, no SHA rewrites) — but it has no merge to define and no isolation,
  so it cannot meet the goal (define merge + branch-per-feature + parallelism enablement). Its
  strengths are *matched* by A via the `--no-merges` pin and the `--first-parent` view, and it
  survives as the INV-001-legal fallback (D1).
- **C2 — rebase-stacked / linear.** Rejected outright: rebase makes SHA rewrite the
  integration mechanism, demolishing the phase-commit audit anchor that D2 exists to protect.
- **Squash-merge.** Rejected: destroys the per-phase prefixes INV-001 and Phase-4 both depend
  on, and orphans `SNAPSHOT_SHA`.

## Risk Register

Pre-mortem (`phase-1-pre-mortem.md`) and adversarial verification (`phase-3-adversarial.md`)
produced six scenarios; each verified against code.

| # | Scenario | Severity | Exposure | Disposition |
|---|----------|----------|----------|-------------|
| F1 | Phase 4 appends handoff on `feat/`; two concurrent merges collide the Pointers block → `test_handoff_contract.py:73-77` reds | catastrophic | deferred D4 (latent solo) | D3 restates handoff placement; collision owned by D4 |
| F2 | `--no-ff` merge subject is unregistered; dropping `--no-merges` reds the walk | graceful now | D2 solo | Pinned: `--no-merges` is a load-bearing contract (D2); verification task asserts it |
| F3 | `/tmp/<id>-baseline-failures.txt` + shared `SNAPSHOT_SHA` clobber on re-run/concurrency | graceful | deferred D4 | Owned by D4 |
| F4 | 5 commits/feature taxes `/catchup` and the release cut | graceful | D1/D2 solo | `git log --first-parent dev` (D2) |
| F5 | No hook gates `git merge`; `--squash`/`-ff`/forgotten merge destroys the trail | catastrophic | D6-interim solo | **Accepted interim risk.** Ceremony instructed (D2); guard deferred to D6 |
| F6 | Un-forbidden mid-feature rebase dangles phase SHAs vs `SNAPSHOT_SHA` | graceful | D1/D2 solo | Forbidden by D2 |

## Load-bearing belief and tripwire

This ADR rests on **the belief that `--no-ff` preserves the four phase SHAs and the
`--no-merges` walk keeps the merge commit invisible to INV-001, so the entire
`SNAPSHOT_SHA`-anchored audit chain survives integration unchanged.** Both Phase 3 (live
code at `validate_architecture.py:367`) and Phase 5 (independent fresh-context derivation)
support it; the first real `--no-ff` merge into `dev` is the confirmation event.

**Falsification tripwire.** The verification dogfood (a feature run on a `feat/` branch, then
`git merge --no-ff` into `dev`) is the first observation. If it reveals that
`validate_architecture.py` reds on the merge, that Phase-4 baseline attribution breaks across
the merge, or that the `--no-merges` exemption does not hold, this ADR is superseded with
tighter constraints. Any future merge scenario observed in the wild that breaks the audit-chain
preservation property is an A-falsification event and triggers supersession review.

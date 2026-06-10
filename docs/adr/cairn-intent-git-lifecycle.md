---
id: cairn-intent-git-lifecycle
name: "Cairn-intent git lifecycle — uniform branch-per-unit + --no-ff across both dispatch paths"
status: accepted
carrier: rationale-only
firmness: provisional
supersedes: []
supersedes-sections: []
amends: ["git-workflow-v1 D1 (scope: 'feature' generalised to 'unit of work, feature or intent')"]
superseded-by: null
topic: process
adrs-referenced: [git-workflow-v1, intent-management-loop, identifier-scheme, feature-slice-model]
invariants-touched: []
date: 2026-06-01
---

# cairn-intent-git-lifecycle: Uniform branch-per-unit + --no-ff across both dispatch paths

## Status
Accepted (provisional — contingent on `intent-management-loop` D7 Trial E; see Consequences).

## Date
2026-06-01

## Context

`git-workflow-v1` (firm) canonicalised branch-per-feature + `git merge --no-ff` for the
`cairn-tdd-feature` dispatch skill — its D1 ties `<feature-id>` to "the identifier the
dispatch skill derives." `intent-management-loop` (provisional) then introduced a *second*
repo-writing dispatch path, `cairn-intent` (a fluid intent-anchored loop:
`load-or-form-intent → intent-challenge → construct → close-review → close`, registry at
`workflows/cairn-intent.yaml`). Its git lifecycle was left unspecified — the seam.

By default `cairn-intent` work fell into `git-workflow-v1`'s *other* bucket
("operator-envelope-gated direct work stays INV-001-legal"), i.e. direct-to-`dev`. This ADR
decides whether and how it adopts the branch+merge model. Two properties resolve without a
choice, and are recorded here as the load-bearing reasoning:

- **`--no-ff` generalises.** Its justification is not "preserve the *four phase commits*"
  specifically — it is "preserve the unit's *construction commit history* as one attributable
  block on `dev` plus a single merge node." `cairn-intent`'s test-first red/green commits are
  equally audit-bearing, so `--no-ff`, no-squash, and no-mid-branch-rebase carry over
  unchanged. The `--no-merges` INV-001 exemption (`git-workflow-v1` D2,
  `scripts/validate_architecture.py:367`) is shape-agnostic and already covers any `--no-ff`
  merge on `dev`.
- **Branch point = the snapshot anchor.** The `feat/<id>` branch point off `dev` is to
  `cairn-intent`'s `close-review` diff what `SNAPSHOT_SHA` is to `cairn-tdd-feature`'s Phase-4
  baseline.

The genuine tension was ceremony: `git-workflow-v1`'s branch discipline versus
`intent-management-loop`'s daily-usability driver (thin intents, no per-unit ceremony). The
operator resolved it in favour of a single uniform git model.

## Decision

### D1 — Uniform unit-of-work model (amends `git-workflow-v1` D1)

`git-workflow-v1` D1's "feature" generalises to **any repo-writing unit of work** — a
`cairn-tdd-feature` feature *or* a `cairn-intent` intent. Every `cairn-intent` intent runs on
a `feat/<intent-id>` branch cut from `dev`; the branch point is the unit's snapshot anchor.
This amends `git-workflow-v1` D1's scope (per `identifier-scheme` D3, a decision is amended by
a later ADR without superseding the parent); `git-workflow-v1` stays firm and unedited.

### D2 — `--no-ff` integration, generalised

`cairn-intent`'s `close` node integrates the unit into `dev` with
`git merge --no-ff feat/<intent-id>`, preserving the construction commit history (whatever its
shape) as one block plus a single merge node. Squash and mid-branch rebase are rejected for
the same reason as `git-workflow-v1` D2 — they destroy the audit-bearing commit SHAs the
`close-review` diff and any premise/sweep artifacts anchor against. The merge commit is exempt
from INV-001 via the shared `--no-merges` walk; no new invariant interaction is introduced
(`git-workflow-v1`'s INV-001 provenance already covers every `--no-ff` merge on `dev`).

### D3 — Naming

`feat/<intent-id>`; `intent-id` shares the flat-slug `feature-id` namespace
(`identifier-scheme` D2). No new branch prefix is added to `git-workflow-v1`'s taxonomy — a
branched unit is a `feat/` unit regardless of which dispatch path built it.

### D4 — Scope and exemptions

The uniform rule covers **intent-bearing repo-writing units**, not every keystroke.
`intent-management-loop` D8's read-only / Q&A exemption stands (no write → nothing to govern),
and `git-workflow-v1` D1's INV-001-legal direct-to-`dev` path remains available for trivial
non-intent edits. Concurrent-intent merge ordering, worktree lifecycle, and the merge-step
guard are **not** re-decided here — they are `git-workflow-v1` D4/D5/D6, shared across both
dispatch paths.

## Consequences

**Easier.**
- One uniform git model across both dispatch paths — no bifurcated rules, no per-path special
  cases. A reader learns branch-per-unit + `--no-ff` once.
- `cairn-intent` inherits `git-workflow-v1`'s audit-preservation and its entire risk register
  (F1–F6) wholesale, rather than re-deriving them.

**Harder.**
- **Thin intents bear branch+merge ceremony**, partially undercutting
  `intent-management-loop`'s daily-usability driver — the operator's accepted tradeoff.
  Mitigated by (a) the ceremony being a cheap two-command wrap (`git checkout -b feat/<id>`;
  `git merge --no-ff`), (b) the D4 read-only/Q&A exemption, and (c) the trivial-non-intent
  direct path. If Trial E shows the ceremony returns the felt-cost that
  `intent-management-loop` set out to remove, that is a Trial-E finding feeding D7, not a
  defect of this ADR.
- Like its parent, the merge step is instructed-not-enforced (`git-workflow-v1` F5); the same
  D6 guard graduation applies.

**Contingency.** This ADR's lifecycle is bound to `cairn-intent` existing. If
`intent-management-loop` D7's Trial E fails and `cairn-intent` is dropped, this ADR is retired
alongside it (it governs a path that no longer ships). If `cairn-intent` graduates and
`cairn-tdd-feature` is retired (D7's pass path), the uniform model simply becomes the model.

## Alternatives Considered

- **Delta-keyed (material intent → branch; thin/resume → direct-to-`dev`).** Reuses
  `intent-management-loop`'s own material-change trigger and best preserves the anti-ceremony
  driver. Rejected by the operator in favour of a single uniform rule — the bifurcation (two
  git behaviours within one dispatch path, keyed on a delta classification) was judged more
  cognitive overhead than the ceremony it saved.
- **Intent-mode exempt (always direct-to-`dev`).** Maximal daily-usability, zero ceremony, but
  loses per-unit isolation and the `--no-ff` audit block, cannot run concurrent intents, and
  leaves `cairn-intent`'s git model permanently outside `git-workflow-v1`. Rejected: it
  re-creates the orphaned-git-model condition `git-workflow-v1` and lesson L-029 exist to
  prevent.
- **`intent/<intent-id>` prefix.** Makes the dispatch path greppable in the branch name, but
  adds a taxonomy entry for no governing difference — a branched unit obeys identical rules
  regardless of path. Rejected for `feat/<intent-id>` (one namespace).

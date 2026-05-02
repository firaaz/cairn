---
slice_id: substrate/phase-2-staging-untracked-enumeration
issue: 26
severity: S1
invariants-touched: [INV-008]
follow-up-to:
  - ae9e6c8 (scripts/slice_orchestrator/lifecycle.py — partial fix, diff-based)
  - af0b5e0 (tests/unit/test_phase_2_handoff_staging_surface.py — R1–R4 surface)
predecessor-archives:
  - .claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed-2/
phase-1-source:
  - .claude/handoff.md (Next)
  - memory: issue_26_untracked_blind_spot.md
  - docs/adr/slice-close-contract.md (DC-3, DC-4)
---

# substrate/phase-2-staging-untracked-enumeration — intent

## What

Close the untracked-file blind spot in the Phase-2 staging branch of
`commit_phase_handoff` (`scripts/slice_orchestrator/lifecycle.py:232-243`).
The fix already in tree at `ae9e6c8` discovers Phase-2 test writes via
`git diff --name-only <phase_1_boundary_sha> -- tests/unit/`. Because
`git diff` reports only tracked-tree differences, a brand-new test file
that the Phase-2 skeptic creates for the first time on a slice is
*untracked* at the moment the Phase-2 boundary commit is built — and so
escapes the diff. The original issue #26 leak therefore recurs for
greenfield test files.

This slice extends the same Phase-2 staging branch to additionally
enumerate untracked paths under `tests/unit/` via
`git ls-files --others --exclude-standard -- tests/unit/`, union the
result with the existing diff-derived set, and preserve the existing
`path.exists()` idempotency guard. No new commit, no subject change, no
new code path outside the existing `current_phase == 2` arm.

## Why

The whole point of staging Phase-2 RED tests at the Phase-2 boundary
commit is to anchor `git bisect`: the test that proves a regression
must live in the same commit as the behavioural change it covers.
Untracked first-time test files break that anchor identically to the
pre-`ae9e6c8` state — the fix only closed the *modified-tracked-file*
half of the leak. The skeptic's most common write — a brand-new RED
file — falls in the still-broken half.

`git diff` excludes untracked by design; the canonical Git idiom for
"all paths the working tree adds relative to HEAD" is
`git diff --name-only HEAD` *plus*
`git ls-files --others --exclude-standard`. Mirroring that idiom against
the Phase-1 boundary commit is the minimal, additive widening that
restores the bisect anchor for greenfield test files.

INV-008 is preserved by construction: the widening is *content* added
to the same single Phase-2 boundary commit (DC-4 holds), and the
union-then-`path.exists()` filter remains idempotent under re-invocation
on an empty working tree (DC-3 holds).

## Boundary

In scope:

- `scripts/slice_orchestrator/lifecycle.py` — extend the existing
  `current_phase == 2` staging block (lines 232–243) only. Union the
  diff-based set with `git ls-files --others --exclude-standard --
  tests/unit/`. Keep the `path.exists()` guard.
- One new RED case in
  `tests/unit/test_phase_2_handoff_staging_surface.py` covering an
  untracked test file at the Phase-1 boundary becoming staged at the
  Phase-2 boundary commit.
- Continued green of R1–R4 already in tree at `af0b5e0`.

Out of scope:

- Any phase other than Phase 2 (Phase 3 stages its own writes; Phase 4
  was patched at `a8d8f23`).
- Test paths outside `tests/unit/`.
- The Phase-1 boundary SHA discovery mechanism (read from existing
  orchestrator state; not redesigned here).
- Squash-merge handling (L-015 / substrate Slice 4).
- Pre-existing reds queued for the post-INV-008 housekeeping pass
  (`test_d3_bypass_log_format`, extractor XPASS-strict, etc.).
- Any change to commit *count* or commit *subject* at the Phase-2
  boundary.

## Specification

### Public-interface contract (`commit_phase_handoff`)

When `current_phase == 2`, the externally observable Phase-2 boundary
commit MUST contain:

1. The existing `handoff-phase-2.md` entry (unchanged).
2. The union of:
   - Every path under `tests/unit/` that `git diff --name-only
     <phase_1_boundary_sha> -- tests/unit/` reports (added or modified
     tracked paths) — already in tree at `ae9e6c8`.
   - Every path under `tests/unit/` that `git ls-files --others
     --exclude-standard -- tests/unit/` reports (untracked,
     non-gitignored paths) — added by this slice.
3. Filtered through the existing `path.exists()` guard so that paths
   removed between discovery and staging are silently dropped
   (idempotency precondition for DC-3).

The Phase-1 boundary SHA is read from existing orchestrator state. Its
discovery is unchanged.

### INV-008 preservation

- **DC-3 (idempotent close).** Preserved. The union is an additive,
  existence-guarded extension. On a tree with no Phase-2 `tests/unit/`
  changes (neither tracked-diff nor untracked), the union is empty; the
  staging extension is a no-op.
- **DC-4 (no extra commits at phase boundary).** Preserved. The
  extension widens the *content* of the existing Phase-2 boundary
  commit; it does not introduce a second commit at the Phase-2
  boundary. The drift-detector regex on `^handoff: phase [0-9]+
  complete$` is untouched.

### Discovery mechanism

Diff-only (current state at `ae9e6c8`) is rejected: untracked files are
silently dropped. Slug-glob is rejected for the same reasons recorded
in the predecessor archive (naming-fragile; R2 enforces non-slug
names). The chosen mechanism is the canonical Git idiom for
"working-tree contents not yet in a tree object": `git ls-files
--others --exclude-standard` unioned with the existing diff-based set.
Both queries are scoped to `-- tests/unit/`.

## Verification

### Test surface — `tests/unit/test_phase_2_handoff_staging_surface.py`

Existing cases (must remain green):

| Case | Setup                                                          | Expectation                                                          |
|------|----------------------------------------------------------------|----------------------------------------------------------------------|
| R1   | Phase-2 modified 1 tracked test file                           | Phase-2 boundary commit contains it                                  |
| R2   | Phase-2 modified 3 mixed-naming tracked test files             | All 3 staged in Phase-2 boundary commit                              |
| R3   | Phase-2 wrote 0 test files                                     | Phase-2 boundary commit shape unchanged: only `handoff-phase-2.md`   |
| R4   | Phase-2 modified 1 tracked test file AND `handoff-phase-2.md`  | Both staged in the same Phase-2 boundary commit                      |

New case (RED before fix, GREEN after):

| Case | Setup                                                                                        | Expectation                                              |
|------|----------------------------------------------------------------------------------------------|----------------------------------------------------------|
| R5   | Phase-2 created 1 *untracked* test file under `tests/unit/` (absent from Phase-1 boundary)   | Phase-2 boundary commit contains it                      |

R5 is the bisect-anchor case for greenfield test writes. A second
optional case may cover the mixed scenario (one untracked + one
modified-tracked staged together) at the skeptic's discretion; the
authoritative new contract is R5.

### Acceptance gates

- R1–R4 remain green.
- R5 transitions from RED (against current `ae9e6c8`) to GREEN under
  the widened staging block.
- Full `tests/unit/` pytest suite — no new regressions. INV-008
  hardened tests stay green
  (`tests/unit/test_close_slice_hardened.py`,
  `tests/unit/test_cross_slice_isolation.py`,
  `tests/unit/test_agent_prompt_updates.py::test_phase_4_prompt_forbids_self_commit`).
- `git log --pretty=%s -n 5 | grep '^phase-2:'` — the Phase-2 boundary
  commit on this slice itself includes `tests/unit/...` paths under
  `git show --name-only`. (Self-application bisect anchor; the test
  file added by this slice is staged by the very fix it exercises.)

### Self-application bisect anchor

The Phase-2 boundary commit *on this slice* must contain the new R5
test case. Because the new test file is untracked at the moment the
Phase-2 boundary commit is built, only the post-fix orchestrator can
stage it — making the slice's own Phase-2 commit the empirical proof
that the untracked-enumeration extension closed the residual half of
issue #26.

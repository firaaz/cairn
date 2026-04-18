# Phase 3 Implementation notes — identifier-scheme/slice-and-feature-rename

Decisions the intent did not pin down, resolved by Builder per
`docs/operational-reference.md:53`.

## 1. §9 disposition — baseline source

**Decision:** (C) drop `adr-003-landed-at-slice` frontmatter key entirely.
Baseline comes purely from git history: the commit that introduced
`docs/adr/cliff-failure-mode-and-v1-defenses.md`, located via
`git log --diff-filter=A -- <path>`.

**Why:** Phase 2 already resolved this by committing the regression guard
`TestFrontmatterBaselineKeyIgnored` (`tests/unit/test_dogfood_evaluate.py:655-683`).
The test asserts that a stale `adr-003-landed-at-slice: 2` in frontmatter does
not override the git-derived baseline. That test is GREEN-on-commit only if
the evaluator never reads that frontmatter key. Disposition (C) is therefore
the Phase 2-encoded answer; (A) "repurpose to sha/id" is incompatible with
the committed tests.

## 2. §8-analog baseline-missing fallback — exit code

**Decision:** exit 2 + stderr diagnostic (not exit 1).

**Why:** Intent §184 and `TestBaselineMissingFallback`
(`tests/unit/test_dogfood_evaluate.py:689-748`) permit either exit 1
("proceed with conservative baseline") or exit 2 ("diagnostic + skip") so
long as silent-pass is precluded. Exit 2 was chosen because:

- Semantic fit with §8: §8's "sweep due" conservative default signals "we
  can't confirm it isn't due, so assume yes." The evaluator's "insufficient
  data" default (exit 2) is the structurally equivalent conservative signal
  — "we can't confirm gate status, so don't bless."
- No spurious FAIL: exit 1 with a "first-commit baseline" fallback would
  count every `slice: ... — complete` commit in the repo as post-ADR, which
  on a fresh clone without the ADR committed yet would exit 1 (FAIL: 10+
  slices no catch). That's noisy and wrong.
- Simplicity: one conditional path in `main`, no need to define what
  "first-commit baseline" means across edge cases (root commit? first slice
  commit? etc.).

Both `test_missing_adr_baseline_emits_stderr_diagnostic` and
`test_missing_adr_baseline_does_not_silent_pass` accept exit 2.

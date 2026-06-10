# Close — carrier-hierarchy-refocus

Intent: `.claude/skill-runs/carrier-hierarchy-refocus/intent.md` (snapshot 2d24db1).
Challenge: five rounds, final `challenge-pass` (`intent-challenge.md`); four real catches — settings-deregistration brick, premise_guard receipts transfer, unsatisfiable handoff clause, role_guard path-shape defect.
Close-review: `close-review-pass` conditional on operator residual acceptance (`close-review.md`); F1 (uncommitted-doc handoff pointer) caught and fixed at 4d8738d.

## Final verification (clean worktree at 4d8738d, reviewer-reproduced independently)

- `uv run pytest -q` — 703 passed, 2 skipped, 2 xfailed
- `uv run python scripts/validate_architecture.py` — ALL CHECKS PASSED (13 invariants, 48 ADRs)
- `bash scripts/smoketest_hooks.sh` — exit 0; role_guard deny + allow-absolute liveness PASS

## Landed (7 commits, c775a0e..4d8738d)

ADR `carrier-hierarchy-and-process-diet` + INV-013; role_guard gh#35 repair (deny→exit 2 paired with path normalization, both directions tested); hook liveness suite; handoff diet (4 threads, open-issue mirror removed, 6-thread cap test); one loop (cairn-tdd-feature + /decision legacy); Check F carrier declarations (19 contract blocks, 14 rationale-only); roadmap re-anchored. 18 gh issues closed per the operator-approved sweep (#4 #5 #6 #8 #9 #10 #11 #12 #13 #15 #16 #17 #18 #22 #23 #26 #29 retired/resolved; #35 fixed citing both paired defects).

## Operator-ratified residual risk (sign-off 2026-06-10)

- **Historical bisect gap**: 3050df1 (validator + 10 tests red — fix-verifier pruned one commit late) and 25bb90f (handoff pointer to then-uncommitted doc) are red in clean checkouts; HEAD verified green; history not rewritten on the shared tree.
- Live envelope enforcement is now real for consumers — audit `active-envelope.yaml` before pulling (ADR D4, roadmap §2); downstream uptake unconfirmed.
- Non-gating hooks' liveness rests on the per-class interpretation (enforcers block; reality-check corrects; carrier emits).
- Plan deviations ratified at sign-off: premise_guard retained (not demoted); test_handoff_contract amended (coverage assertion removed); role_guard repaired (not deleted — operator call); live-constraint enumeration is the corpus itself via Check F, not ADR prose.

## Next

Roadmap top item: measure the production gate (de-prime the intent-challenge brief, live data). Spec-elicitation handoff thread returns when its plan doc is committed.

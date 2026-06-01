# Close-review — intent-template-operator-prompt

> Verdict returned by the fresh-context `intent-review` agent (agentId
> a7a483c6f6800aa87). Transcribed at close because the agent's in-run Write to
> this path did not persist; content is its returned report verbatim.

**Status: close-review-pass.** All three checks pass against the live diff and
re-run evidence.

## Findings
- **All clauses hold.** MS-1/MS-2/MS-3 satisfied; MN-1 (INV-003 + the eight's
  derive-don't-fabricate) untouched — the `wrong-if` leak the intent named does
  not occur. The carve-out is scoped to one named section in all three sites, and
  `phase-1-tdd.md` affirmatively re-binds: *"Derive-don't-fabricate binds only the
  eight schema sections that follow."*
- **The flagged residual is now mechanically guarded.**
  `test_operator_prompt_reconciled_in_authoritative_shape_source` asserts both
  "operator prompt" and "exempt" appear in `phase-1-tdd.md` — the two-places-in-sync
  risk is a test, not prose-only.
- **Evidence live-confirmed.** 640 passed / 2 skipped / 2 xfailed; focused suite
  14 passed (new assertions + eight-heading-in-order regression both green);
  `validate_architecture.py` ALL CHECKS PASSED.
- **Scope clean.** Diff touches exactly the three execution-scope files;
  scope-statement matches diff size.

## Clause results
- MS-1 (Operator Prompt before What): PASS — `templates/intent.md`, regression cursor-walk skips it.
- MS-2 (verbatim + derive-exempt guidance): PASS — `templates/intent.md`.
- MS-3 (eight headings present + in order, regression-meta): PASS — `test_intent_template_shape_and_eight_headings` GREEN.
- MN-1 (INV-003 four-phase + eight's derive-don't-fabricate untouched): PASS — single-line `phase-1-tdd` diff, no phase/role lines touched, carve-out single-section in all 3 sites, validator ALL CHECKS PASSED; `wrong-if` leak absent.

## Residual risk (documented, not a block)
The in-sync guard checks presence + an "exempt" substring anywhere in
`phase-1-tdd.md`, not the positive "binds only the eight" sentence — a future
reword could keep the test green while weakening the bind. The prose currently
reads correctly.

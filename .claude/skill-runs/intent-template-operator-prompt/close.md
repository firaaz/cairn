# Close — intent-template-operator-prompt

- Intent: `.claude/skill-runs/intent-template-operator-prompt/intent.md`
- Challenge: `.claude/skill-runs/intent-template-operator-prompt/intent-challenge.md` (challenge-pass after 1 sustained block + revision)
- Close-review: `.claude/skill-runs/intent-template-operator-prompt/close-review.md` (close-review-pass)

## Final verification
- `uv run pytest -q`: 640 passed, 2 skipped, 2 xfailed
- focused (`test_intent_template_graduated_contract` + `test_template_extraction` + `test_handoff_contract`): 19 passed
- `scripts/validate_architecture.py`: ALL CHECKS PASSED (12 invariants)

## Shipped
gh#28 mitigation 2 — verbatim, derive-exempt `## Operator Prompt` section in
`templates/intent.md`, reconciled in `.claude/agents/phase-1-tdd.md` + the
template comment; drift guarded by
`test_operator_prompt_reconciled_in_authoritative_shape_source`.

## Scope-out (routed elsewhere)
- gh#28 #3 (per-section length caps): separable + decision-weight → its own `/decision`.
- gh#28 #1 (slash-command prompt) and #4 (cheap-re-runs doc): not addressed.

## Residual risk (accepted)
The in-sync guard checks substrings, not the positive "binds only the eight"
sentence — a future reword could pass the test while weakening the bind. Prose
currently correct.

## Trial E
First felt-cost data point: `docs/operator-field-notes-2026-06-01.md`. Net: the
loop felt lighter than four-phase for this size, and the front-challenge caught a
semantic over-read the mechanical gate missed. Caveats: n=1, self-referential
vehicle, same-family co-miss residual unmeasured; slice-#25 counterfactual still
pending as the separate acceptance gate.

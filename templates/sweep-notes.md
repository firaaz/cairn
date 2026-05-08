<!--
Phase 4 (Auditor) sweep-notes template. Operational summary:
`docs/operational-reference.md` "Phase 4: Integration".

The Auditor runs the full test suite, the architecture validator, and the
adjacent-code regression check; verifies each declared invariant with
`file:line` citation evidence (assertions backed by what was actually found,
not from memory); and records the verdict here. On implementation failure,
RAISE_ISSUE rather than patching the implementation.
-->
---
feature-id: <feature-id>
as-of: <YYYY-MM-DD commit-sha>
phase: 4-integration
verdict: <PASS | FAIL | RAISE_ISSUE>
---

## Test results

<!-- `uv run pytest -q` output summary. Pass/fail counts, FAILED list. Cite
`/tmp/<feature-id>-baseline-failures.txt` for regression-attribution. -->

## Validator results

<!-- `uv run python scripts/validate_architecture.py` stdout. Expect
`ALL CHECKS PASSED`. -->

## Invariant verification

<!-- One row per invariant declared in `intent.md`'s `invariants-touched`.
Each row must carry a `file:line` citation showing the binding-surface
evidence. -->

| Invariant | Evidence (`file:line`) | Verdict |
|---|---|---|
| <INV-XXX> | `<path>:<line>` | <PASS|FAIL> |

## Adjacent code regression check

<!-- Files outside the envelope that interact with the changed surface.
Confirm no regressions; cite test output. -->

## Handoff append (optional)

<!-- If the feature's outcome materially changes session state, append a
short pointer to `.claude/handoff.md`. Keep within the 150–400-token budget;
detail belongs in commit messages, not the handoff. -->

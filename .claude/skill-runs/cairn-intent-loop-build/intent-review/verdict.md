# intent-review increment #1 — draft verdict

Status: DRAFTED, not landed. Two canonical-target artifacts realized under
`proposed/`, validated against each other and against the live `close-review`
node. No canonical path written; no Python module introduced.

## Drafts

- `proposed/intent-review.md` → lands at `.claude/agents/intent-review.md`
- `proposed/test_intent_review_agent.py` → lands at `tests/unit/test_intent_review_agent.py`
- `intent.md` — the intent contract for this increment (front-challenge presumed passed; premise_guard exits 0)

## Self-check (run in this worktree, not against canonical paths)

- `premise_guard.py intent.md` → exit 0 (every cited quote grounds in live source).
- Every assertion of `proposed/test_intent_review_agent.py` passes when its
  `AGENT_PATH`/`WORKFLOW_PATH` are pointed at `proposed/intent-review.md` and the
  live YAML: name == intent-review, Write granted, report path present, both
  verdict statuses present, all 7 verdict fields present
  (verdict, clause_results, evidence_summary, residual_risk, findings,
  missing_evidence, required_rework), all 3 evidence ids present
  (contract-clause-check, evidence-adequacy-check, scope-check), obligation
  strings present (same-context + fallback + diff size).
- `ruff check proposed/test_intent_review_agent.py` → clean.
- `close-review` node id present in `workflows/cairn-intent.yaml`.
- Canonical `.claude/agents/intent-review.md` and
  `tests/unit/test_intent_review_agent.py` confirmed ABSENT (RED precondition).

## Contract fidelity

The persona mirrors `intent-challenge.md` scoped to close-review:
front-loaded Skeptic → back-loaded Reviewer; three checks instead of per-premise
counterfactual; same report-only single-file discipline; same "real finding, not
a hurdle" framing. The two verdict envelopes carry exactly the
`close-review` node's `pass_output`/`fail_output` keys.

## Open decisions

None. Increment is fully specified by the node + ADR D2/D9.

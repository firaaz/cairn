# Intent Challenge Report

Registry: `cairn-intent`
Stage: `cairn-intent-challenge`
Case: `trial-e-w1-case-04`
Intent: `.claude/skill-runs/trial-e-w1-case-04/intent.md`
Verdict: Pass

## Scope

This run used only the case intent, the cited source file from Premise Grounding,
`docs/adr/intent-management-loop.md`, and `checks/premise_guard.py`. No
construction was performed.

`docs/adr/intent-management-loop.md:57-64` defines the front-loaded
intent-challenge as a fresh-context attack on intent premises against live source
before construction. `docs/adr/intent-management-loop.md:100-104` records the
intent-challenge contract and the slice-#25-style front-challenge acceptance gate.

## Premise Source Checks

### P1

Label: `premise_guard resolves cited premise sources as PROJECT_ROOT / source`

Intent citation:

- Source: `checks/premise_guard.py`
- Quoted text:

```python
source = premise.get("source")
quote = premise.get("quote")
resolved = PROJECT_ROOT / source
```

Mechanical check:

- The quoted executable code is live at `checks/premise_guard.py:98-100`.
- The quote is not a docstring or comment; it is inside `_check_premises`.
- `checks/premise_guard.py:95-100` shows `_check_premises` iterating premise
  mappings, extracting `source` and `quote`, then resolving `resolved` with the
  exact expression `PROJECT_ROOT / source`.

Semantic check:

- The label faithfully describes the cited live behavior: cited premise sources
  are resolved by assigning `resolved = PROJECT_ROOT / source`.
- The intent's no-op refactor premise is semantically plausible only if extraction
  of `source` and `quote` remains separate from changing resolution, type
  validation, grounding, suffix selection, and failure messages.
- The contract's failure-preservation claims are supported by adjacent live code:
  `checks/premise_guard.py:101-103` reports missing sources,
  `checks/premise_guard.py:104-108` reports unreadable sources after read failure,
  and `checks/premise_guard.py:109-113` reports stale or fabricated quotes via
  the grounded matcher.

Challenge result: P1 passes. No challenged premise is blocked.

## Semantic Counterfactual Search

- Stale-docstring counterfactual: rejected. The grounded quote is live executable
  code at `checks/premise_guard.py:98-100`, not stale prose.
- Wrong-model counterfactual: rejected for this intent. A model that claims
  premise sources resolve by another expression would contradict the live
  assignment in `_check_premises`.
- Slice-#25-style verbatim-grounding counterfactual: rejected for this intent.
  The premise quote could pass verbatim grounding, but the inspected live
  surrounding behavior does not contradict the premise label or the stated
  no-op refactor boundary. The source still performs missing, unreadable, and
  stale/fabricated failure handling immediately downstream of the cited
  extraction and resolution.
- Residual refactor hazard: a future helper extraction must not move resolution
  into a helper, coerce `source`, change the `Path(source).suffix` argument to
  `grounded`, alter failure strings, or bypass the existing string validation at
  `checks/premise_guard.py:176-187`. Those hazards are implementation risks, not
  contradictions in the current intent premise.

## Verdict

Pass. P1 is mechanically grounded and semantically supported by live source. No
slice-#25-style counterfactual was found that both passes the cited quote
grounding and contradicts the live `checks/premise_guard.py` behavior.

Human sign-off is still required before construction.

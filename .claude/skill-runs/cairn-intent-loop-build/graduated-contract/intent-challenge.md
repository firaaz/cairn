# intent-challenge — graduated-contract (increment #3)

**Verdict: challenge-pass.** All six premises are verbatim-present in their cited
sources AND each label faithfully describes what the cited span means. Every
must-satisfy / must-not-violate clause that depends on a premise holds against
live source at snapshot ef14b98. No mechanical gate is introduced; the intent's
boundary matches ADR D3 and the Trial-D plan-doc constraints.

## Per-premise source checks (verbatim + semantic)

### P1 — docs/adr/intent-management-loop.md:67 — PASS
Quote `"carries at least a thin (one-liner) intent; depth graduates by size via the D3 exception tags."`
verbatim-present (D3 block, lines 66–70). Label: "depth graduates by size via the
four exception tags — this increment realizes that dial."
- Semantic: faithful. D3's "the D3 exception tags" resolves to the four
  `EXCEPTION_TAGS` (D3 + plan-doc both enumerate them as those four).
- Counterfactual attempted (grounded true / claim false): the intent reframes the
  tags as a "depth-graduation dial." That is an interpretive gloss, but it does not
  contradict D3 — a tag lets a larger clause stay thin instead of forcing a split,
  which is exactly graduation-by-size. Defensible, not a misread.
- Dependent clause `must-satisfy[0]` (template documents all four tags as the dial)
  holds.

### P2 — docs/adr/intent-management-loop.md:68 — PASS
Quote `"a one-line scope-statement in the contract (attackable by the"` verbatim-present.
Label: "D3 defines the completeness floor as a one-line scope-statement."
- Semantic: faithful — D3 literally states `completeness floor = a one-line
  scope-statement in the contract`.
- Counterfactual: none survives; the surrounding sentence is unambiguous.
- Dependent clause `must-satisfy[1]` (template requires a one-line scope-statement
  as the completeness floor) holds.

### P3 — docs/adr/intent-management-loop.md:69 — PASS
Quote `"front-challenge) + the close-review smell-testing contract-depth against diff size. No hard"`
verbatim-present. Label: "D3 forbids a hard cardinality gate; enforcement is
front-challenge + close-review, not the template."
- Semantic: faithful once read around the truncation. The quote ends mid-sentence at
  "No hard"; the full D3 sentence is "No hard cardinality gate." Reading the next
  word confirms the label's claim. premise_guard only checks the verbatim span (it
  matches); the semantic completion is supported.
- Counterfactual: could "No hard …" mean something other than "no hard cardinality
  gate"? No — the line continues directly into "cardinality gate." Rejected.
- Dependent `must-not-violate[1]` (no hard cardinality gate / mechanical depth
  enforcement) and the Boundary block hold. Minor stylistic note (non-blocking): the
  quote is awkwardly truncated; a future edit could end it at "gate." for clarity.

### P4 — scripts/lib/atomicity.py:15 — PASS
Quote `{"universal-set", "regression-meta", "operator-bound", "trivial-existence"}`
verbatim-present (the `EXCEPTION_TAGS = frozenset({...})` literal, lines 14–16).
Label: "EXCEPTION_TAGS is the source of truth for the four tag names (FLI-1 parity)."
- Semantic: faithful. Confirmed the module defines exactly these four, and the
  existing `test_intent_template_contract_tags_match_exception_tags`
  (tests/unit/test_template_extraction.py:190) already asserts each tag appears in
  templates/intent.md and passes (7 passed). FLI-1 and `must-satisfy[0,4]` hold.

### P5 — workflows/cairn-intent.yaml:47 — PASS
Quote `"description: One-line scope statement plus must-satisfy floor."` verbatim-present
(the `contract-floor` evidence of the `load-or-form-intent` node, `required: true`).
Label: "the node's contract-floor evidence is the one-line scope statement plus
must-satisfy floor this template guidance realizes."
- Semantic: faithful. The node requires a one-line scope statement + must-satisfy
  floor as evidence; the template guidance documents that requirement so authors
  produce it. "Realizes" is the correct relation (template = authoring guidance for
  the node's required evidence).
- Counterfactual attempted: does the YAML "scope statement" mean something different
  from D3's "scope-statement"? No — the node prompt (lines 22–27) forms "a thin
  contract with at least a one-line must-satisfy clause, execution scope, evidence
  expectation, and write envelope," which is the same floor. Rejected.

### P6 — templates/intent.md:120 — PASS
Quote `except: "universal-set: the consumer set is the 3 repos listed in roadmap.md"`
verbatim-present (worked example in the existing `## Contract` block). Label: "the
template already carries a worked exception-tag example; graduation guidance is
ADD-not-REPLACE on top of the existing Contract block."
- Semantic: faithful. Confirmed the `## Contract` block exists with this worked
  tagged clause; all four tag names already appear in the file (universal-set ×3,
  the others ×1). ADD-not-REPLACE (FLI-3) is consistent with live state.

## Semantic counterfactual search (slice-#25-style)

- **Truncated-quote-changes-meaning (P3):** the "No hard" span could in principle be
  completed differently; verified by reading the next token that it completes to
  "No hard cardinality gate." Claim survives.
- **Tag-set drift (P4):** verified the template tag set still equals the code
  frozenset via the live parity test (green); no drift counterfactual survives.
- **YAML-floor ≠ ADR-floor (P5):** verified the node's "scope statement" floor is the
  same concept as D3's "scope-statement"; no divergence.

## Build-shape verification (non-premise, confirms the increment is well-formed)

- `scope-statement` hyphenated token is currently ABSENT from templates/intent.md —
  so the new test's distinct assertion (`scope-statement` present) is genuinely RED
  at HEAD and turns GREEN only after the template guidance lands. Correct TDD shape.
- The four tag-names assertion is redundant with the existing parity test (already
  green); the intent acknowledges this (Verification lines 82–84) — honest, not a
  defect.
- New test file `tests/unit/test_intent_template_graduated_contract.py` does not yet
  exist (lands later) — consistent with the write constraints.
- Intent Boundary / Explicit Scope-Out match the Trial-D plan-doc: `## Contract`
  stays optional + fail-open, EARS is guidance-only (no syntactic enforcement), tag
  correctness stays operator/review-bound, no cardinality gate. No contradiction
  with D3 or D6 found.

## Blocking evidence
None.

## Open decisions surfaced
None. The increment is a template-guidance + regression-test realization of a
fully-decided mechanism (ADR D3). No cross-cutting contract or externally-visible
behavior is left open. No structural template change is required to carry the
guidance (additive comment text inside the existing `## Contract` section
suffices), so the `escalate-when` structural trigger does not fire.

# intent-challenge report — intent-review-close-review-subagent (Trial-E increment #1)

Role: front-loaded Skeptic, fresh context. Attacked every premise in
`.claude/skill-runs/cairn-intent-loop-build/intent-review/intent.md` against live
source. `premise_guard` only proves each `quote:` is verbatim-present in its
`source:` (confirmed: exit 0). It does NOT prove the `label:`/dependent claim
MEANS what the source says — that semantic gap is the attack below.

## premise-source-checks

1. **pass_output (close-review-pass)** — `workflows/cairn-intent.yaml:199-205`.
   Read the close-review node (begins `- id: close-review`, line 167). `pass_output.status`
   is `close-review-pass`; `fields` are `verdict, clause_results, evidence_summary,
   residual_risk`. Label faithful.
2. **fail_output (close-review-blocked)** — `workflows/cairn-intent.yaml:206-212`.
   `fail_output.status` is `close-review-blocked`; `fields` are `verdict, findings,
   missing_evidence, required_rework`. Label faithful. Union of pass+fail fields is
   exactly the 7-element universal-set the must-satisfy `except` enumerates.
3. **contract-depth + same-context refusal** — `workflows/cairn-intent.yaml:177-178`,
   inside the close-review node prompt: "evidence adequate for the contract depth.
   Do not accept same-context self-review as a fallback." `grep` confirms this phrase
   is UNIQUE to lines 177-178 (only other `same-context` is line 72, the
   intent-challenge charter). Label faithful.
4. **write_envelope report-only** — `workflows/cairn-intent.yaml:185-188`.
   `mode: report-only`, single path `^\.claude/skill-runs/[^/]+/close-review\.md$`.
   Label faithful; this literal regex is what the mirror test asserts `in body`.
5. **contract-clause-check** — `workflows/cairn-intent.yaml:190`. Required evidence id.
6. **evidence-adequacy-check** — `workflows/cairn-intent.yaml:193`. Required evidence id.
7. **scope-check** — `workflows/cairn-intent.yaml:196`. Required evidence id.
   (5-7) The node's `evidence` list is exactly these three, each `required: true`.
8. **executor fresh_agent / context fresh** — `workflows/cairn-intent.yaml:213-215`,
   inside the close-review node. Label faithful. (Counterfactual on cross-node
   misattribution resolved below.)
9. **ADR D3 completeness floor** — `docs/adr/intent-management-loop.md:68-69`. The
   floor = "a one-line scope-statement in the contract (attackable by the
   front-challenge) + the close-review smell-testing contract-depth against diff
   size." Label says the floor "includes" the close-review smell-test — accurate
   (one of two floor components). Quoted span carries no markdown bold markers, so
   it is verbatim-present.
10. **intent-challenge tools** — `.claude/agents/intent-challenge.md:4`:
    `tools: Read, Write, Bash, Grep, Glob`. Sole frontmatter `tools:` line. Label faithful.
11. **CAIRN_ROOT three parents up** — `tests/unit/test_intent_challenge_agent.py:18`:
    `CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent`. Label faithful
    (correct only at `tests/unit/`).
12. **_node() selector** — `tests/unit/test_intent_challenge_agent.py:25`:
    `return {node["id"]: node for node in workflow["nodes"]}["intent-challenge"]`.
    Label faithful (intent-review test changes only the trailing id to `close-review`).

## semantic-counterfactual-search

For each premise I constructed a reading in which the grounded quote is true but
the intent's claim is false, then tested it against the source.

- **P8 (executor/context) — the one real attack.** `executor: fresh_agent` /
  `context: fresh` is verbatim-grounded TWICE (lines 113-114, the *intent-challenge*
  node, and lines 214-215, the *close-review* node). Counterfactual: the intent cites
  the wrong node's block. Tested: line 214-215 falls inside the close-review node
  (167..<219). The label attributes the pair to the close-review node, and the
  close-review node genuinely is fresh-context. Dual-match does not falsify a TRUE
  attribution. Counterfactual does NOT hold.
- **P3 (same-context refusal).** Counterfactual: the phrase belongs to a different
  node's prompt (e.g. construct). Tested: `grep` shows it only at 177-178. Does NOT hold.
- **P9 (ADR D3).** Counterfactual: the smell-test is the *entire* floor, so the label
  over-claims by implying close-review owns the floor. Tested: label uses "includes,"
  the floor is explicitly two-part, and the derived must-satisfy clause (thin contract
  on heavy diff = finding) is exactly what D3 prescribes for close-review. Does NOT hold.
- **P1/P2 (verdict envelopes).** Counterfactual: fields belong to a sibling node.
  Tested: pass/fail blocks at 199-212 are inside the close-review node; field sets
  match the labels exactly. Does NOT hold.
- **P4 (write path).** Counterfactual: report-only mode is the front node's, or the
  path regex differs. Tested: 185-188 are the close-review node's write_envelope; regex
  is the literal the test will assert. Does NOT hold.
- **P5/P6/P7 (evidence ids).** Counterfactual: an id is optional or named differently.
  Tested: each is `required: true` at 190/193/196. Does NOT hold.
- **P10 (tools).** Counterfactual: a second `tools:` line narrows the grant. Tested:
  line 4 is the only one. Does NOT hold.
- **P11/P12 (mirror-test lines).** Counterfactual P11: the label mis-states depth.
  Three `.parent` = three levels; correct only at `tests/unit/`. Holds as stated, not
  falsified. P12: selector reads node by id; label accurate. Does NOT hold.

## Non-blocking observations (forwarded, not findings)

- **Verification feasibility, not a premise falsehood.** P11's label is TRUE precisely
  because it is load-bearing: the draft test at `proposed/test_intent_review_agent.py`
  sits four dirs below the worktree root, so `parent.parent.parent` resolves to
  `.claude/skill-runs/cairn-intent-loop-build/`, NOT the cairn root. The intent's
  Verification step ("when run against the proposed persona, passes every assertion")
  therefore cannot run in-place without a CAIRN_ROOT override pointing at the worktree
  root and the proposed persona path. This does not falsify any premise — the intent
  EXPLICITLY flags it (Feature-Local Invariant 2 + the `wrong-if` clause require the
  resolution stay identical so it is correct at `tests/unit/`). Constructor must verify
  via an env/path override, or move/copy to `tests/unit/` to run; the report-only
  proposed/ location cannot host a directly-runnable mirror test. Surfaced for the
  constructor, not a block.
- **Risk Surface is honest, not a premise gap.** The intent itself names the residual
  (structure test pins string presence, not behavioral force; Trial-E D9 integration
  catches a hollow obligation). That is a known, recorded EXPOSED risk, not an
  unsupported premise.

## verdict

All 12 premises are verbatim-grounded (premise_guard exit 0) AND survive the
counterfactual attack: every label faithfully describes the cited source, and every
must-satisfy clause depending on a premise holds against live `workflows/cairn-intent.yaml`,
`.claude/agents/intent-challenge.md`, `tests/unit/test_intent_challenge_agent.py`, and
`docs/adr/intent-management-loop.md`. No premise survives a reading where the quote is
true but the claim is false. PASS.

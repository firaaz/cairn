---
id: intent-review-close-review-subagent
name: intent-review close-review subagent (Trial-E increment #1)
snapshot-sha: ef14b98
invariants-touched: []
---

## What
Author the `intent-review` close-review subagent — the fresh-context close
checkpoint of the cairn-intent loop (ADR D2 checkpoint (b)) — as two LANDED-LATER
canonical artifacts: a persona at `.claude/agents/intent-review.md` and a
structure-contract test at `tests/unit/test_intent_review_agent.py`. The persona
mirrors `intent-challenge.md` scoped to close-review; the test mirrors
`test_intent_challenge_agent.py`, pinning the persona prose to the `close-review`
node in `workflows/cairn-intent.yaml`. This increment produces only DRAFTS under
`proposed/`; canonical paths land in-session after operator approval.

## Why
ADR `intent-management-loop` D2 makes the fresh close-review one of the two
decorrelation checkpoints bracketing fluid construction; D9 makes its
input/verdict contract a unit-test acceptance item. The `close-review` node
already exists in the workflow as the machine contract, but no persona realizes
it and no test pins persona-to-node, so the contract can drift silently. This
increment closes that gap symmetrically to the already-shipped front-loaded
`intent-challenge`.

## Boundary
Does NOT implement the construction node, the `close` node, the SessionStart
carrier (D5), or any new hook (D6 reuses the three shipped guards). Does NOT
write any canonical path now — `.claude/agents/`, `tests/`, the YAML, or the ADR.
Does NOT introduce a Python module: the executors render each node's verdict
shape from the YAML as string templates and the agent emits a JSON verdict line;
no per-subagent module exists or is called. Does NOT add the semantic-judgment
test (that is the Trial-E integration per D9, not a unit test).

## Specification
Two draft artifacts under `.claude/skill-runs/cairn-intent-loop-build/intent-review/proposed/`:

- `intent-review.md` (draft of canonical `.claude/agents/intent-review.md`):
  - Frontmatter `name: intent-review`; `tools: Read, Write, Bash, Grep, Glob`;
    a sharp one-line description.
  - Body names the allowed_inputs: the intent contract
    (`.claude/skill-runs/<feature>/intent.md`), the git diff for the construction
    work, the full focused test output, architecture-validation output when
    relevant, and close evidence produced by construct.
  - Body walks the three evidence ids: `contract-clause-check`,
    `evidence-adequacy-check`, `scope-check`.
  - Body states the report-only write path
    `^\.claude/skill-runs/[^/]+/close-review\.md$` (the literal regex from the
    node `write_envelope.paths[0]`, so the test's `report_path in body` mirror passes).
  - Body carries the close-review obligation: REFUSE same-context self-review as
    a fallback (decorrelation), and smell-test contract DEPTH against diff size
    (the D3 completeness floor — a thin contract on a heavy diff is a FINDING).
  - Ends with the two exact stdout JSON verdict envelopes whose keys match the
    node fields:
    - pass: `{"status":"close-review-pass","verdict":...,"clause_results":...,"evidence_summary":...,"residual_risk":...}`
    - block: `{"status":"close-review-blocked","verdict":...,"findings":...,"missing_evidence":...,"required_rework":...}`
- `test_intent_review_agent.py` (draft of canonical
  `tests/unit/test_intent_review_agent.py`): a faithful mirror of
  `test_intent_challenge_agent.py` with `AGENT_PATH` → `.claude/agents/intent-review.md`,
  `_node()` selecting the `close-review` node, identical `CAIRN_ROOT` relative
  logic so it runs unchanged once moved to `tests/unit/`.

## Verification
- `proposed/test_intent_review_agent.py` exists and, when run against the
  proposed persona, passes every assertion: file exists; frontmatter
  `name == "intent-review"`; `Write` in tools and the `close-review.md` report
  path string present in body; both `close-review-pass` and `close-review-blocked`
  statuses present; every field of `pass_output.fields`
  (`verdict, clause_results, evidence_summary, residual_risk`) and
  `fail_output.fields` (`verdict, findings, missing_evidence, required_rework`)
  present in body; all three evidence ids present; the close-review obligation
  strings present (same-context-fallback refusal + depth-vs-diff smell test).
- `uv run python -c "import yaml; print([n['id'] for n in yaml.safe_load(open('workflows/cairn-intent.yaml'))['nodes']])"` lists `close-review` (test selector is valid).
- `grep` confirms the two verdict envelope status literals appear verbatim in the
  proposed persona.

## Risk Surface
The persona could pass the structure test (all literals present) yet collapse the
decorrelation obligation in prose — e.g. wording that lets a same-context closer
self-certify, or that treats the depth-vs-diff smell test as optional. The test
pins string presence, not behavioral force, so a hollow obligation passes CI; the
Trial-E integration (D9) is what catches it. Mitigation: obligation phrased as a
hard REFUSE/FINDING, mirroring intent-challenge's "real finding, not a hurdle".

## Feature-Local Invariants
- The proposed persona and test must agree with the `close-review` node as the
  single source: every verdict field, status, evidence id, and the report-only
  write path the test asserts is read FROM the node, never hardcoded divergently.
- The test must keep `test_intent_challenge_agent.py`'s `CAIRN_ROOT` resolution
  (`Path(__file__).resolve().parent.parent.parent`) so it is correct only when
  landed at `tests/unit/`.

## Explicit Scope-Out
- No edit to `workflows/cairn-intent.yaml` or `docs/adr/intent-management-loop.md`
  (they are the sources this realizes, per the ADR's authoritative-contract role).
- No canonical-path writes this increment (all canonical landings are post-approval).
- No Python module / no executor change (honest-minimal: no real caller exists).
- No semantic close-review judgment test (Trial-E integration owns that, D9).

## Premise Grounding

```yaml
premises:
  - source: workflows/cairn-intent.yaml
    quote: |
      pass_output:
      status: close-review-pass
      fields:
        - verdict
        - clause_results
        - evidence_summary
        - residual_risk
    label: "the close-review node's pass_output is status close-review-pass with fields verdict/clause_results/evidence_summary/residual_risk — the keys the persona's pass envelope must mirror"
  - source: workflows/cairn-intent.yaml
    quote: |
      fail_output:
      status: close-review-blocked
      fields:
        - verdict
        - findings
        - missing_evidence
        - required_rework
    label: "the close-review node's fail_output is status close-review-blocked with fields verdict/findings/missing_evidence/required_rework — the keys the persona's block envelope must mirror"
  - source: workflows/cairn-intent.yaml
    quote: |
      evidence adequate for the contract depth. Do not accept same-context
    label: "the close-review node prompt mandates contract-depth adequacy and forbids same-context self-review as a fallback — the persona's decorrelation obligation"
  - source: workflows/cairn-intent.yaml
    quote: |
      mode: report-only
      paths:
        - ^\.claude/skill-runs/[^/]+/close-review\.md$
    label: "the close-review node write_envelope is report-only with the single close-review.md path the persona body must name and the test asserts present"
  - source: workflows/cairn-intent.yaml
    quote: |
      - id: contract-clause-check
    label: "contract-clause-check is a required evidence id of the close-review node the persona must walk"
  - source: workflows/cairn-intent.yaml
    quote: |
      - id: evidence-adequacy-check
    label: "evidence-adequacy-check is a required evidence id of the close-review node the persona must walk"
  - source: workflows/cairn-intent.yaml
    quote: |
      - id: scope-check
    label: "scope-check is a required evidence id of the close-review node the persona must walk"
  - source: workflows/cairn-intent.yaml
    quote: |
      executor: fresh_agent
      context: fresh
    label: "the close-review node executes as a fresh-context agent — the decorrelation property the persona's same-context refusal enforces"
  - source: docs/adr/intent-management-loop.md
    quote: |
      front-challenge) + the close-review smell-testing contract-depth against diff size. No hard
    label: "ADR D3 completeness floor includes the close-review smell-testing contract-depth against diff size — the depth-vs-diff obligation the persona must carry"
  - source: .claude/agents/intent-challenge.md
    quote: |
      tools: Read, Write, Bash, Grep, Glob
    label: "intent-challenge grants tools Read, Write, Bash, Grep, Glob — the tool grant the mirrored intent-review persona uses"
  - source: tests/unit/test_intent_challenge_agent.py
    quote: |
      CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
    label: "the mirror test resolves CAIRN_ROOT three parents up, correct only at tests/unit/ — the relative logic the intent-review test must keep identical"
  - source: tests/unit/test_intent_challenge_agent.py
    quote: |
      return {node["id"]: node for node in workflow["nodes"]}["intent-challenge"]
    label: "_node() in the mirror test selects a node by id from workflow nodes — the intent-review test changes only the id to close-review"
```

## Contract

```yaml
must-satisfy:
  - the proposed intent-review persona frontmatter shall set name to intent-review and grant the Write tool
  - clause: the proposed persona body shall contain every verdict field of the close-review node pass_output and fail_output
    except: "universal-set: the set is verdict, clause_results, evidence_summary, residual_risk, findings, missing_evidence, required_rework"
  - clause: the proposed persona body shall name every required evidence id of the close-review node
    except: "universal-set: the set is contract-clause-check, evidence-adequacy-check, scope-check"
  - the proposed persona body shall state the report-only close-review.md write path
  - if the closer would review in the same context that produced the diff, then the proposed persona shall refuse same-context self-review as a fallback
  - the proposed persona shall smell-test contract depth against diff size and treat a thin contract on a heavy diff as a finding
  - when run against the proposed persona, the proposed mirror test shall pass every assertion
must-not-violate:
  - no canonical path (.claude/agents/, tests/, workflows/cairn-intent.yaml, docs/adr/intent-management-loop.md) is written or edited this increment
  - no Python module is introduced (no real caller exists; executors render verdict shapes from the YAML)
  - the persona and test must not hardcode verdict fields, statuses, evidence ids, or the write path divergently from the close-review node
wrong-if:
  - the proposed persona omits either the close-review-pass or close-review-blocked status literal
  - the proposed test's CAIRN_ROOT resolution differs from test_intent_challenge_agent.py so it would not run unchanged at tests/unit/
  - the proposed test selects a node id other than close-review
escalate-when:
  - an open design question surfaces that the ADR/brainstorm left to /decision (record in open_decisions with a proposed default; do not silently commit)
evidence:
  - proposed/test_intent_review_agent.py passes against proposed/intent-review.md (all assertions)
  - grep confirms both verdict status literals verbatim in proposed/intent-review.md
  - the close-review node id is present in workflows/cairn-intent.yaml nodes
execution-scope:
  - .claude/skill-runs/cairn-intent-loop-build/intent-review/
```

/*
 * Dynamic Workflow — build the three remaining cairn-intent-loop increments toward Trial E,
 * each under the cairn-intent loop's own decorrelation discipline.
 *
 *   #1 intent-review close-review subagent        (.claude/agents/intent-review.md + test)   [fully specified]
 *   #2 canonical cairn-intent skill + using-cairn SessionStart carrier (.claude/skills/...)   [open contract Qs — SURFACE]
 *   #3 graduated-contract + completeness-floor rules (templates/intent.md + tests)             [mechanism decided: ADR D3]
 *
 * Runs in worktree feat/cairn-intent-loop-build (off dev). Each increment is an independent
 * decorrelated arc:  form-intent -> front-challenge -> construct(TDD draft) -> close-review.
 *
 * HARD CONSTRAINTS (the loop's invariants, honored deliberately):
 *  - Dynamic workflows take NO mid-run operator input -> the loop's two sign-off boundaries
 *    collapse into ONE terminal operator review. The workflow STOPS there.
 *  - NO canonical-path writes. Every stage writes ONLY under
 *    .claude/skill-runs/cairn-intent-loop-build/<inc>/ (intent, verdicts, and DRAFTS under proposed/).
 *    The honest RED->GREEN landing + commit happens in-session, in this worktree, AFTER approval.
 *  - SURFACE, do not DECIDE: where an increment hits a genuinely-open design question
 *    (esp. #2's "carrier fired" testable definition / token budget / fallback — a /decision-class
 *    question per the brainstorm), the agent records it in open_decisions with a proposed default
 *    + tradeoff. It must NOT silently commit a cross-cutting contract. The close-review flags any
 *    un-surfaced commitment.
 *  - Honest-minimal: no Python module unless a real caller exists (none does — executors render
 *    verdict shapes from the YAML).
 *
 * Each agent() is fresh-context — that IS the decorrelation the challenge/close-review require
 * (ADR docs/adr/intent-management-loop.md D2/D4).
 */

export const meta = {
  name: 'cairn-intent-loop-build',
  description: 'Build the 3 remaining cairn-intent-loop increments (#1 intent-review, #2 skill+carrier, #3 graduated-contract) as decorrelated, reviewable, ready-to-land drafts toward Trial E',
  phases: [
    { title: 'Form intent' },
    { title: 'Front-challenge' },
    { title: 'Construct (TDD draft)' },
    { title: 'Close-review' },
    { title: 'Cross-consistency' },
  ],
}

const SCRATCH = '.claude/skill-runs/cairn-intent-loop-build'

const CONTEXT = `
Repo: cairn — a methodology repo (TDD-by-construction dispatch skill, hooks, validator). cwd is the repo root of worktree feat/cairn-intent-loop-build (branched off dev). All of dev's files are present.
The upcoming trial is **Trial E**: drop phase-1 derivation; dogfood the new \`cairn-intent\` intent-management loop on a real cairn increment (ADR docs/adr/intent-management-loop.md, accepted/provisional).

CONSTRAINTS YOU MUST OBEY:
- Write ONLY under ${SCRATCH}/<increment-id>/ (your intent.md, your verdict report, and DRAFTS under proposed/). NEVER write a canonical path (.claude/agents/, .claude/skills/, tests/, templates/, .claude/settings.json, workflows/). Those land in-session after operator approval.
- Honest-minimal: introduce NO Python module unless a real caller already exists. (Executors scripts/lib/{claude,codex}_workflow_executor.py render each node's verdict shape from the YAML as string templates; the agent emits a JSON verdict line. No per-subagent module exists or is called. Confirmed.)
- SURFACE, don't DECIDE: if you hit a genuinely-open design question (a cross-cutting contract, an externally-visible behavior, anything the brainstorm/ADR left to /decision), DO NOT silently commit it. Record it in open_decisions with a concrete proposed default + the tradeoff, and leave it for the operator.
- The authoritative contracts are the nodes in workflows/cairn-intent.yaml and the ADR. Your draft artifacts are REALIZATIONS of those, never sources — do not edit the YAML or the ADR.

Read live source with Read (offset/limit). Do not call any MCP server.
`

const INCREMENTS = [
  {
    id: 'intent-review',
    title: '#1 intent-review close-review subagent',
    spec: `
INCREMENT #1 — the intent-review close-review subagent (the load-bearing fresh-context close checkpoint; ADR D2/D9). FULLY SPECIFIED.

Canonical targets (LAND LATER, do not write now): .claude/agents/intent-review.md  AND  tests/unit/test_intent_review_agent.py
Read: workflows/cairn-intent.yaml (the "close-review" node ~lines 167-217), .claude/agents/intent-challenge.md (the persona blueprint to MIRROR), tests/unit/test_intent_challenge_agent.py (the structure-contract test to MIRROR), templates/intent.md, checks/premise_guard.py, docs/adr/intent-management-loop.md (D2/D9).

The persona (.claude/agents/intent-review.md) MUST mirror intent-challenge.md scoped to close-review:
- frontmatter: name: intent-review; tools: Read, Write, Bash, Grep, Glob; a sharp description.
- body names allowed_inputs (intent contract, git diff, full focused test output, architecture-validation output, close evidence from construct).
- body walks the three evidence ids: contract-clause-check, evidence-adequacy-check, scope-check.
- body states the report-only write path .claude/skill-runs/<feature>/close-review.md.
- body carries the close-review obligation = REFUSE same-context self-review as a fallback (decorrelation) + smell-test contract DEPTH against diff size (the ADR D3 completeness floor: a thin contract on a heavy diff is a FINDING, not a pass).
- ends with the two exact stdout JSON verdict envelopes whose keys match the node fields:
  pass:  {"status":"close-review-pass","verdict":...,"clause_results":...,"evidence_summary":...,"residual_risk":...}
  block: {"status":"close-review-blocked","verdict":...,"findings":...,"missing_evidence":...,"required_rework":...}
The test (tests/unit/test_intent_review_agent.py) is a faithful mirror of test_intent_challenge_agent.py: AGENT_PATH -> .claude/agents/intent-review.md; _node() selects the "close-review" node; asserts file exists, frontmatter name=="intent-review", Write tool granted + close-review.md report path in body, BOTH verdict envelope statuses + EVERY field of pass_output.fields + fail_output.fields present, all three evidence ids present, and the close-review obligation strings present (same-context refusal + depth-vs-diff smell test). Keep CAIRN_ROOT relative logic identical so it runs unchanged once moved to tests/unit/.
Open decisions expected: NONE (fully specified). Honest-minimal: no module.`,
  },
  {
    id: 'skill-and-carrier',
    title: '#2 canonical cairn-intent skill + using-cairn SessionStart carrier',
    spec: `
INCREMENT #2 — the canonical Claude-Code-side cairn-intent dispatch skill + the using-cairn SessionStart carrier (ADR D1 coexisting skill, D5 carrier). DESIGN-HEAVY: has OPEN /decision-class questions you MUST surface, not decide.

Canonical targets (LAND LATER, do not write now): .claude/skills/cairn-intent/SKILL.md ; .claude/skills/using-cairn/SKILL.md ; the SessionStart carrier registration (likely .claude/settings.json) ; tests for the carrier's "fired" detection + fallback.
Read: docs/adr/intent-management-loop.md (D1, D5), docs/adr/delivery-mechanism-friction.md (the using-cairn SessionStart carrier; the <=2k-token budget), workflows/cairn-intent.yaml (the loop nodes the skill orchestrates: load-or-form-intent -> intent-challenge -> construct -> close-review -> close), .claude/skills/cairn-tdd-feature/SKILL.md (the canonical Claude skill LAYOUT precedent), plugins/cairn/skills/cairn-intent/SKILL.md AND plugins/cairn/skills/using-cairn/SKILL.md (RECONCILE — the canonical Claude skill drives the SAME YAML and dispatches the .claude/agents personas; it must NOT duplicate the Codex plugin's logic, only provide the Claude-Code-native surface), .claude/settings.json (existing hook/config surface).

The cairn-intent SKILL.md orchestrates: load-or-form intent -> (on a NEW or materially-changed intent only) dispatch the intent-challenge fresh agent + operator sign-off -> fluid construct (tests test-first) -> dispatch the intent-review fresh close-review + operator sign-off -> close (commit + handoff). Approval is DELTA-TRIGGERED (re-fires only on a premise or must-satisfy clause edit; D2). cairn-tdd-feature stays as the fallback (D1).
The using-cairn carrier (D5): on session open it LOADS the active intent (resume) or signals a new one is needed — load is cheap, NO gate. Fallback: if it doesn't fire, the skill's first step does load/form explicitly (carrier is an optimization, not the only path).

OPEN DECISIONS — record each in open_decisions (proposed default + tradeoff), do NOT commit:
  (a) the exact TESTABLE "carrier fired" definition and how a unit test detects it,
  (b) the <=2k-token budget enforcement mechanism,
  (c) the precise fallback contract / signal shape.
(Brainstorm Q4 leaves these to /decision; ADR D5 gives the shape but not the exact test.) Draft the skill bodies and a PROPOSED carrier mechanism, but flag (a)-(c) for the operator. Reconciliation hazard: keep verdict-field/node consistency with the Codex plugin SKILLs.`,
  },
  {
    id: 'graduated-contract',
    title: '#3 graduated-contract + completeness-floor rules',
    spec: `
INCREMENT #3 — graduated-contract + completeness-floor rules in templates/intent.md (ADR D3). MECHANISM DECIDED by the ADR; mostly template guidance + tests.

Canonical targets (LAND LATER, do not write now): templates/intent.md (guidance additions) ; a new tests/unit/test_intent_template_graduated_contract.py (assert the template carries the dial + the scope-statement requirement).
Read: docs/adr/intent-management-loop.md (D3), docs/plans/2026-05-20-cairn-thin-substrate-trials.md (Probe A exception classes; Trial D), docs/plans/2026-05-30-cairn-trial-d-scope-split.md, templates/intent.md (current), checks/atomicity_guard.py, checks/premise_guard.py.

ADR D3 (decided): Contract mandatory, depth GRADUATED by size via the four exception tags (universal-set / regression-meta / operator-bound / trivial-existence). The COMPLETENESS FLOOR = a one-line scope-statement in the contract (attackable by the front-challenge) + the close-review smell-testing contract-depth against diff size. NO hard cardinality gate.
So this increment = (i) add template guidance: the exception-tag dial with one-line semantics for each tag, the one-line scope-statement requirement, and how depth graduates (trivial one-liner must-satisfy -> full grammar + premise grounding); (ii) a unit test asserting templates/intent.md carries the four tag names + the scope-statement requirement. Enforcement lives in the subagents (the front-challenge attacks the scope-statement; the #1 close-review smell-tests depth-vs-diff) — do NOT add a mechanical cardinality gate.
Open decisions: minimal. Flag ONLY if you find the template needs a structural change that is itself decision-weight.`,
  },
]

const FORM_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['intent_path', 'contract_summary', 'premises', 'delta_kind', 'ready_for_challenge'],
  properties: {
    intent_path: { type: 'string' },
    contract_summary: { type: 'string' },
    premises: { type: 'array', items: { type: 'string' }, description: 'each premise as "label — source:line"' },
    delta_kind: { type: 'string', enum: ['new', 'material-change', 'resume'] },
    ready_for_challenge: { type: 'boolean' },
  },
}
const CHALLENGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['status', 'verdict', 'challenged_premises', 'premise_source_checks', 'semantic_counterfactual_search', 'blocking_evidence', 'required_intent_revision', 'report_path'],
  properties: {
    status: { type: 'string', enum: ['challenge-pass', 'challenge-blocked'] },
    verdict: { type: 'string' },
    challenged_premises: { type: 'array', items: { type: 'string' } },
    premise_source_checks: { type: 'array', items: { type: 'string' } },
    semantic_counterfactual_search: { type: 'array', items: { type: 'string' } },
    blocking_evidence: { type: 'array', items: { type: 'string' } },
    required_intent_revision: { type: 'string' },
    report_path: { type: 'string' },
  },
}
const CONSTRUCT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['proposed_paths', 'red_green_plan', 'draft_summary', 'honest_minimal', 'open_decisions'],
  properties: {
    proposed_paths: { type: 'array', items: { type: 'string' } },
    red_green_plan: { type: 'string', description: 'exact in-session commands to land + observe RED then GREEN' },
    draft_summary: { type: 'string' },
    honest_minimal: { type: 'boolean' },
    open_decisions: { type: 'array', items: { type: 'string' }, description: 'each: "decision — proposed default — tradeoff"; empty if none' },
  },
}
const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['status', 'verdict', 'clause_results', 'evidence_summary', 'residual_risk', 'findings', 'missing_evidence', 'required_rework', 'honest_minimal_confirmed', 'open_decisions_flagged', 'report_path'],
  properties: {
    status: { type: 'string', enum: ['close-review-pass', 'close-review-blocked'] },
    verdict: { type: 'string' },
    clause_results: { type: 'array', items: { type: 'string' } },
    evidence_summary: { type: 'string' },
    residual_risk: { type: 'string' },
    findings: { type: 'array', items: { type: 'string' } },
    missing_evidence: { type: 'array', items: { type: 'string' } },
    required_rework: { type: 'string' },
    honest_minimal_confirmed: { type: 'boolean' },
    open_decisions_flagged: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
}
const CROSS_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['coherent', 'cross_findings', 'landing_order', 'blocking_decisions'],
  properties: {
    coherent: { type: 'boolean' },
    cross_findings: { type: 'array', items: { type: 'string' }, description: 'inconsistencies across the three draft packages (e.g. skill references intent-review wrongly; template rules contradict the close-review smell-test)' },
    landing_order: { type: 'array', items: { type: 'string' }, description: 'recommended in-session landing order with rationale' },
    blocking_decisions: { type: 'array', items: { type: 'string' }, description: 'operator decisions that must be resolved before any landing' },
  },
}

const dir = (inc) => `${SCRATCH}/${inc.id}`

// Each increment runs an independent decorrelated arc; pipeline = no barrier between stages.
const arcs = await pipeline(
  INCREMENTS,
  // Stage 1 — form the intent (durable anchor) + premise grounding
  async (inc) => {
    const intent = await agent(`${CONTEXT}
${inc.spec}

TASK (${inc.title}): First run \`mkdir -p ${dir(inc)}/proposed\`. Then author the thinnest-sufficient intent CONTRACT for THIS increment, following templates/intent.md, and write it to ${dir(inc)}/intent.md.
Include must-satisfy / must-not-violate / execution-scope / evidence clauses pinned to the canonical targets above, and a '## Premise Grounding' block (premise_guard format: source / quote / label) whose quotes are VERBATIM from the live files you cite. Set delta_kind="new". Set ready_for_challenge=true only if every premise quote is verbatim-present in its source.`,
      { label: `form:${inc.id}`, phase: 'Form intent', schema: FORM_SCHEMA })
    return { inc, intent }
  },
  // Stage 2 — front-loaded decorrelation challenge (fresh context)
  async (a) => {
    const challenge = await agent(`${CONTEXT}
${a.inc.spec}

TASK (${a.inc.title}): You are the front-loaded Skeptic, fresh context. Attack the intent at ${a.intent.intent_path} against LIVE source. premise_guard only checks each quote is verbatim-present; it does NOT check the label/claim MEANS what the intent asserts — that semantic gap is your job. For each premise: open the cited span, read around it, and test whether the label faithfully describes the code/contract and whether every must-satisfy clause depending on it holds. Explicitly attempt a counterfactual reading (grounded quote true, intent claim false). Block (status=challenge-blocked) if any premise's claim is unsupported; pass otherwise. Write your report to ${dir(a.inc)}/intent-challenge.md.`,
      { label: `challenge:${a.inc.id}`, phase: 'Front-challenge', schema: CHALLENGE_SCHEMA })
    return { ...a, challenge }
  },
  // Stage 3 — construct the drafts test-first (to scratch, gated on challenge pass)
  async (a) => {
    if (a.challenge.status === 'challenge-blocked') {
      log(`[${a.inc.id}] front-challenge BLOCKED — skipping construct (intent needs revision)`)
      return { ...a, construct: { skipped: true, proposed_paths: [], red_green_plan: '', draft_summary: 'skipped: front-challenge blocked', honest_minimal: true, open_decisions: [] } }
    }
    const construct = await agent(`${CONTEXT}
${a.inc.spec}

TASK (${a.inc.title}): The intent passed the front-challenge. DRAFT every canonical-target artifact into ${dir(a.inc)}/proposed/ using the SAME filename it will have once landed (e.g. proposed/intent-review.md, proposed/test_intent_review_agent.py, proposed/SKILL-cairn-intent.md, proposed/templates-intent.md, etc. — pick clear names and list them in proposed_paths). Apply test-first discipline: where a test exists, draft it to fully express the contract. Introduce NO Python module. Do NOT write canonical paths and do NOT run pytest against canonical paths.
red_green_plan = the exact in-session shell commands to (i) move/copy each drafted test to its canonical path, run \`uv run pytest\` and observe RED, then (ii) move/copy each drafted artifact to its canonical path, run \`uv run pytest\` and observe GREEN. List every open design decision in open_decisions (proposed default + tradeoff); set honest_minimal=true iff no module was introduced.`,
      { label: `construct:${a.inc.id}`, phase: 'Construct (TDD draft)', schema: CONSTRUCT_SCHEMA })
    return { ...a, construct }
  },
  // Stage 4 — fresh-context close-review of the drafts against the contract + ADR
  async (a) => {
    if (a.construct.skipped) {
      return { ...a, review: { status: 'close-review-blocked', verdict: 'upstream front-challenge blocked', clause_results: [], evidence_summary: '', residual_risk: '', findings: ['front-challenge blocked this increment'], missing_evidence: [], required_rework: a.challenge.required_intent_revision, honest_minimal_confirmed: true, open_decisions_flagged: [], report_path: '' } }
    }
    const review = await agent(`${CONTEXT}
${a.inc.spec}

TASK (${a.inc.title}): You are the fresh-context close-reviewer. The drafts are at: ${a.construct.proposed_paths.join(', ')}. The intent is at ${a.intent.intent_path}.
Audit the drafts against (i) the authoritative contract (the relevant workflows/cairn-intent.yaml node and/or the ADR), (ii) the intent's must-satisfy clauses, and (iii) ADR docs/adr/intent-management-loop.md (D1/D2/D3/D5/D9 as relevant). Verify per-clause pass/fail; check evidence adequacy and that proposed scope matches the intent's execution-scope; confirm honest-minimal (no module); and smell-test contract DEPTH vs the change size (completeness floor). For any test draft, reason structurally (or copy drafts into a throwaway ${dir(a.inc)}/_check/ tree mimicking repo layout and run pytest there — NEVER write canonical paths) about whether it goes RED without the artifact and GREEN with it. REFUSE same-context self-review: judge on the live contract, not the constructor's claims. Re-flag any open decision the constructor surfaced AND any un-surfaced cross-cutting commitment you find. Write your report to ${dir(a.inc)}/close-review.md. status=close-review-pass only if every clause holds; else close-review-blocked.`,
      { label: `review:${a.inc.id}`, phase: 'Close-review', schema: REVIEW_SCHEMA })
    return { ...a, review }
  },
)

// Barrier: cross-consistency across the three draft packages (needs all arcs)
const built = arcs.filter(Boolean)
const cross = await agent(`${CONTEXT}

TASK: Cross-consistency review across the three drafted increment packages under ${SCRATCH}/{intent-review,skill-and-carrier,graduated-contract}/proposed/.
These increments are coupled by design: #2's cairn-intent skill DISPATCHES #1's intent-review agent at the close-review boundary and references the loop nodes; #2's carrier loads the intent anchor; #3's graduated-contract rules are what #1's close-review smell-tests depth against. Read the drafts and verify they COHERE: the skill references intent-review.md by the right name and dispatches the right node; verdict-field names are consistent across persona drafts and the YAML; the template's scope-statement requirement matches what the front-challenge/close-review expect; nothing in one draft contradicts another. Recommend a landing_order (with rationale) for the in-session RED->GREEN landing, and list blocking_decisions = operator decisions (esp. #2's carrier-fired definition / token budget / fallback) that must be resolved before ANY landing.`,
  { label: 'cross-consistency', phase: 'Cross-consistency', schema: CROSS_SCHEMA })

const summarize = (a) => ({
  id: a.inc.id,
  title: a.inc.title,
  intent_path: a.intent?.intent_path,
  ready_for_challenge: a.intent?.ready_for_challenge,
  challenge_status: a.challenge?.status,
  challenge_report: a.challenge?.report_path,
  required_intent_revision: a.challenge?.required_intent_revision || '',
  proposed_paths: a.construct?.proposed_paths || [],
  red_green_plan: a.construct?.red_green_plan || '',
  open_decisions: a.construct?.open_decisions || [],
  honest_minimal: (a.construct?.honest_minimal !== false) && (a.review?.honest_minimal_confirmed !== false),
  review_status: a.review?.status,
  review_findings: a.review?.findings || [],
  required_rework: a.review?.required_rework || '',
  open_decisions_flagged: a.review?.open_decisions_flagged || [],
  review_report: a.review?.report_path,
})

return {
  stopped_at: 'operator-signoff-boundary',
  worktree: 'feat/cairn-intent-loop-build',
  scratch_root: SCRATCH,
  increments: built.map(summarize),
  cross,
  note: 'No canonical files written and no commit made. Drafts + decorrelated verdicts are in scratch. Operator reviews, resolves blocking_decisions, then in-session honest RED->GREEN landing + commit happen in this worktree.',
}

# Cairn as interaction protocol — reframe and trial design

**Date:** 2026-05-13
**Status:** Framing agreed; trial selection pending (operator-bound, will resume on another system)
**Audience:** future cairn maintainer (and future-self picking this up cold elsewhere)

---

## TL;DR

Cairn's load-bearing job is the **human-AI interaction protocol** that makes medium-to-large codebases tractable under AI-assisted development — not "a TDD workflow." Current cairn (phases, hooks, ADRs, handoffs, dispatch skill) are partial implementations of that protocol, not the protocol itself.

The minimal-elegant design is: **every interaction artifact carries a small uniform contract; prose is for understanding, the contract is what review attaches to; durability is enforced by property-based testing of contract clauses; delegation happens via step-by-step micro-contract assembly.**

This is forward, not regression — M4 retired the wrong substrate; this fills the gap M4's absence revealed. Cairn never had contracts in this sense.

---

## How the framing emerged

This 2026-05-13 brainstorm went through three reframes:

1. **Workflow-shape (the status quo)** — cairn = TDD pipeline with phase agents and ADRs. Friction = symptoms; fix per symptom. Rejected because the symptom set explodes into a patch-stack and the operator catches over-engineered ADRs going through.
2. **Model-layer (interim)** — cairn lacks structured state; add a thin declarative model. Rejected because (a) M4 retired exactly this kind of substrate for good reasons; (b) it doesn't address the *human-AI interaction* layer the operator named as the actual abstraction.
3. **Interaction protocol (current)** — cairn's unit isn't "a slice" or "a phase," it's the **interaction** between a human and an AI agent collaborating on a growing codebase. Everything cairn has (phases, hooks, ADRs, handoffs) are interaction primitives; the methodology should be designed at that layer, not the workflow layer.

The deepest single observation: **TDD-by-construction works at defeating rubber-stamping because RED tests are a falsifiable surface separable from the prose intent.** Every other artifact in cairn (ADR, intent, plan, handoff, decision) lacks an equivalent structured falsification surface — which is why they rubber-stamp. The fix is to give them one, uniformly.

---

## The six interaction contracts

A good human-AI collaboration must maintain six conditions. Map cairn's current strength to each:

| Contract | What it means | Current cairn |
|---|---|---|
| **Intent-faithful** | AI solves the problem the human has, not a near-cousin | Weak — wrong-model propagation P1→P2→P3 |
| **Reviewable** | Human verifies output without redoing the work | Weak — rubber-stamping at every prose review point |
| **State-durable** | Collaboration survives pauses, role changes, fresh sessions | Weak — manual handoff toil, prose narratives |
| **Authority-clear** | Decisions/destructive actions have clear authorization | **Strong** — hooks, role envelope, append-only ADRs |
| **Error-catchable** | Mistakes surface early at the right moment | Mixed — mechanical errors caught, semantic ones don't |
| **Cost-bounded** | Tokens, time, attention, future-debt stay in check | Weak — no architectural counter-pressure, prose-only review |

Cairn's asymmetric strength on Authority-Clarity is because that leg yields to mechanical enforcement. The other five legs depend on review being *substantive*, which prose-against-prose can't guarantee.

---

## The mechanism: contracts at every interaction artifact

Every interaction artifact (slice intent, ADR, plan, handoff, decision, feature spec) carries a **small, structured, machine-checkable contract** in its frontmatter. Prose stays — humans read prose to gain understanding. But review attaches to the contract, not the prose.

### Uniform contract skeleton

```yaml
contract:
  must-satisfy:
    - <acceptance criterion, mechanically checkable>
    - ...
  must-not-violate:
    - <anti-goal, observable>
    - ...
  wrong-if:
    - <observable condition under which this artifact should be revisited/revoked>
    - ...
  escalate-when:
    - <condition where AI must stop and ask the operator>
    - ...
  evidence:
    - <how contract satisfaction is demonstrated on submission>
```

Targeted size: ~5–10 lines total. If a contract grows past ~15 lines, that's a smell — either the artifact is doing too much or the contract is being prosed-up.

### Per-artifact instantiations (initial guess; trial will validate)

- **Slice intent** → must-satisfy = list of RED-test invariants; must-not-violate = scope anti-goals (don't touch X, no new deps); evidence = test transcript + diff stat
- **ADR** → must-satisfy = decision boundary; wrong-if = observable triggers for revisit; evidence = trace of decision-application in codebase
- **Plan** → must-satisfy = phase outputs; must-not-violate = scope-creep markers; wrong-if = effort-overrun thresholds; evidence = artifacts per phase
- **Handoff** → must-satisfy = state items each pointing to primary source; no narrative prose; evidence = the manifest itself
- **/operator-brief** → renders the union of all open contracts and their states; brief is contract-state, not summary

### Durability mechanism: property-based testing of contracts

Contracts are not point-in-time claims. Each clause has **properties**; properties have **generators**; generators continuously probe for counterexamples. Hypothesis-style. This is what keeps contracts live as the codebase grows — the scale-enablement requirement isn't met by "we wrote good contracts once," it's met by "the contracts are adversarially tested every commit and fail loudly when the codebase outgrows them."

PBT-on-contracts also defeats rubber-stamping at the meta level: you cannot rubber-stamp a contract whose property test is trying to break it. The contract author *has* to think about counterexamples to write the property. If they can't write the property, they can't write the contract — that's the forcing function for clarity.

### Delegation mechanism: step-by-step micro-contract assembly

The delegation moment is not "AI produces full intent → operator reviews." It's "AI proposes one micro-contract per turn → operator approves/rejects/amends → repeat." The full contract is the composition of approved micro-contracts. Brainstorming-skill is the closest existing template.

This collapses two failure modes at once:

- **AI-blabber** (agents tend to over-deliver prose to demonstrate understanding) — can't blabber when limited to one micro-contract per turn
- **Operator-attention** (rubber-stamping increases with artifact length) — each turn is small enough to actually review

It also makes the contract *jointly authored*, which is structurally different from "AI authors, operator approves."

---

## Why this isn't M4 regression

M4 retired:
- Orchestrator
- cairn-knowledge MCP server
- Slice lifecycle state machinery
- Pipeline substrate registries
- `close_slice` lifecycle

M4 did not retire a contract layer. The DC-* family in `slice-close-contract` was small and contract-shaped, but it was bundled with the retired substrate. This design lives in **artifact frontmatter via the existing validator** — no new orchestrator, no MCP, no daemon, no state layer. The mechanism is uniform schema + property tests, both in the existing tree.

---

## Dogfood constraint

Cairn is heavily dogfooded — cairn-on-cairn is the primary test bed. Any protocol must be light enough that applying it to cairn-itself in the next session doesn't slow cairn-itself down. This rules out:
- New files outside the artifact's own frontmatter
- New validator binaries
- New state layers
- New MCP servers
- Schema-everywhere discipline that turns every artifact into a 50-line YAML

If the trial's contract block exceeds ~15 lines, or the property test takes more than 30 minutes to write, those are smells indicating over-design.

---

## Trial proposals — pick one before further reasoning

The operator has said "it's cheaper to try than reason our way out of it." Two candidates. Recommendation: A first; B if A succeeds.

### Trial A: handoff as the first contract-shaped artifact

**Why this first:** lowest coupling to existing machinery (changing handoff doesn't break Phase 2/3/4 expectations), highest-frequency operator pain (8 manual refreshes in a row), most falsifiable outcome (handoff either renders mechanically from state-pointers or it doesn't), and `/operator-brief` falls out naturally as the renderer.

**Trial-contract (the trial itself follows the protocol):**

```yaml
contract:
  must-satisfy:
    - handoff.md grows a frontmatter contract block (~10 lines)
    - one property test exists at tests/unit/test_handoff_contract.py
    - property test runs against any handoff and fails if contract violated
    - one pause-resume cycle happens with the new shape, operator drives it cold
  must-not-violate:
    - no new files outside handoff.md + one test file
    - no new substrate layer, no MCP, no daemon
    - contract block stays under 15 lines
    - validator changes restricted to one function
  wrong-if:
    - the property test is itself prose-shaped (we're vibes-grading the contract)
    - operator still feels like they're authoring narrative on resume
    - the contract block needs amendment after first use (signals over-design)
  escalate-when:
    - property test takes >30 minutes to write
    - contract block grows past 15 lines while drafting
  evidence:
    - diff to .claude/handoff.md showing contract block
    - tests/unit/test_handoff_contract.py with property-based generators
    - operator's one-line verdict after pause-resume cycle
```

**Concrete first-pass handoff contract:**
- `must-satisfy`: every open thread has a primary-source pointer (file path / issue # / ADR id); blocked threads name their blocker; every in-flight slice has a phase state
- `must-not-violate`: no narrative prose; every entry is a pointer or a tagged state
- `wrong-if`: any pointer fails to resolve on resume; operator reports "I had to dig outside the handoff to know what's going on"
- `evidence`: handoff renders deterministically from state pointers (no operator authorship of the narrative)

**Properties to test:**
- Every entry's pointer resolves to a real file/issue/ADR
- Mutating a state-item (e.g., closing an issue) is reflected in the next handoff render
- Adversarial: introducing a hidden open thread (issue not in handoff) is caught by the property test

**Estimated effort:** 1 session.

### Trial B: slice intent as the first contract-shaped artifact

**Why this might be right instead:** highest-stakes rubber-stamping case (intent rubber-stamping → wrong-model propagation through P1→P2→P3). If protocol defeats rubber-stamping here, we've validated against the hardest test. Phase agents now consume a contract not prose, which fixes wrong-model propagation in one stroke.

**Why I'm wary:** coupled to Phase 2 RED-test generation. Changing intent shape forces Phase 2 prompt rework. Bigger trial, bigger blast radius if it doesn't work.

Trial-contract: same shape, substituting "one slice runs end-to-end under new intent contract; Phase 2 RED tests are generated from the contract not the prose; operator reports whether rubber-stamping at Phase 1 review is reduced."

---

## What was poked at but not resolved

These were surfaced in the conversation, flagged honest-uncertainty, and deferred:

- **The "moments" decomposition** (delegation / submission / review / decision / handoff / authorization / disagreement). Right direction but underdeveloped — the list is provisional. If correct, **phases-as-they-stand become "one mode of executing under a contract"** — optional decomposition for complex contracts, not mandatory structure. Needs more thought.
- **Whether AI can author contracts without prose-leakage.** Empirical question; only the trial answers it. Schema constrains output but the free-text fields (anti-goals, wrong-if) can degrade to vibes if not policed.
- **Whether the trial succeeds for cairn-on-cairn but fails for consumer-project use.** Cairn is heavily dogfooded; consumer-case validation is harder without the consumer present.
- **Adoption protocol.** If contracts become real, retrofitting existing artifacts (22 open issues, ~10 active plans, 30+ ADRs) is its own work stream. Discipline: new artifacts must have contracts; old ones retrofit only when touched.

---

## Orthogonal pains (not addressed by this design)

- V-3 SSH-clone bug (Claude Code plugin resolver hardcodes SSH for `source: "github"`)
- Windsurf Cascade Hooks invisible in user's build
- Node 20 deprecation in CI actions (issue #32, deadline 2026-06-02)

These are infrastructure / platform-shaped, separate work streams.

---

## Next action when this resumes on another system

1. **Decide Trial A or Trial B.** Recommendation: A.
2. **Author the chosen trial's first-pass contract** (the trial-contract above is a draft; the *artifact* contract is the deliverable).
3. **Run the trial in one session.** Time-box to one session per the dogfood constraint.
4. **Report against the trial-contract's evidence clauses.** Not a vibe-report — explicit checklist.
5. **Decide:** extend protocol to next artifact type, iterate on contract shape, or abandon framing.

If A succeeds, candidate next trials: ADR contract (highest scale-enablement payoff because ADRs decay silently as the codebase grows; PBT-on-ADR-contracts is the durability mechanism), then slice intent (validate against the hardest rubber-stamping case).

---

## Conversation source

Framing emerged in a session on 2026-05-13. Four parallel research agents were dispatched on:
1. Cairn current state (post-M4 surface, open backlog, friction)
2. Claude Code primitive usage in cairn (idiomatic vs fighting-the-platform)
3. Claude Code best practices for methodology repos in 2026
4. Operator-field friction synthesis (what actually hurts when driving cairn)

The conversation went through three reframes (workflow → model-layer → interaction protocol). Operator repeatedly caught the assistant's patch-stacking tendency and steered toward elegant re-foundations. The framing reframe ("interaction protocol, not workflow") came from the operator. The contracts-with-PBT mechanism emerged jointly. The trial-and-stop-reasoning move came from the operator.

Related memory entries (on the originating machine; may not be present on resume system):
- `feedback_prefer_elegant_over_patches.md`
- `cairn_interaction_protocol_reframe_2026-05-13.md`
- `mechanical_enforcement_is_backbone_of_cairn.md`
- `context_discipline_philosophy.md`

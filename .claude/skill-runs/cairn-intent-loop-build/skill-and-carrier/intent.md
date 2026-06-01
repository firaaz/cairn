---
id: skill-and-carrier
name: "cairn-intent Claude-Code dispatch skill + using-cairn SessionStart carrier"
snapshot-sha: ef14b9862b73260b8b9e192ca687e8af677ee454
invariants-touched: [INV-004]
---

<!--
Trial-E increment #2 intent contract. Authored under the cairn-intent loop
(load-or-form-intent node). The authoritative contracts are the nodes in
workflows/cairn-intent.yaml and docs/adr/intent-management-loop.md; the
artifacts this intent governs are REALIZATIONS of those, never sources.
delta_kind: new.
-->

## What

Author two Claude-Code-native skill bodies and a SessionStart carrier mechanism for
the cairn-intent loop: (1) `.claude/skills/cairn-intent/SKILL.md` — a dispatch skill
that orchestrates the loop nodes in `workflows/cairn-intent.yaml`
(load-or-form-intent → intent-challenge → construct → close-review → close) using the
Claude-Code-native surface (the Agent tool dispatching `.claude/agents` personas, not
the Codex `spawn_agent` renderer); (2) `.claude/skills/using-cairn/SKILL.md` — the
Claude-Code skill-chooser entry point; (3) a PROPOSED SessionStart carrier that on
session-open loads the active intent (resume) or signals a new one is needed. This
increment writes only DRAFTS under `proposed/`; canonical files land in-session after
operator approval.

## Why

ADR `intent-management-loop` D1 mandates a new `cairn-intent` dispatch skill that
coexists with `cairn-tdd-feature`, and D5 mandates the `using-cairn` SessionStart
carrier with a testable "fired" definition and a load/form fallback. ADR
`delivery-mechanism-friction` D1 fixes the carrier's pointer-only, ≤2,000-token shape.
The Codex plugin already ships `cairn-intent`/`using-cairn` SKILLs driving the SAME
YAML; the Claude side must provide the native surface WITHOUT duplicating the Codex
plugin's renderer logic. This is Trial E's dogfood increment.

## Boundary

Does NOT retire `cairn-tdd-feature`, modify INV-003 or the firm phase ADRs, edit
`workflows/cairn-intent.yaml` or either ADR, author the close-review/intent-review
persona file (increment #1 territory), introduce any new Python module, or COMMIT the
three open-decision questions (carrier "fired" test, ≤2k enforcement, fallback signal
shape) — those are surfaced for the operator. Does NOT write any canonical path in
this increment; all output is drafts under `proposed/`.

## Specification

Protocol-level commitments the drafts must realize:

- `cairn-intent/SKILL.md` frontmatter: `name: cairn-intent` + a `description:`
  scoping it to intent-management dispatch (parallel to the Codex SKILL's framing but
  Claude-Code-native).
- The skill orchestrates the five nodes by their canonical YAML ids:
  `load-or-form-intent`, `intent-challenge`, `construct`, `close-review`, `close`.
- Fresh-context boundaries dispatch via the Agent tool: `intent-challenge` →
  `subagent_type: intent-challenge` (the persona at `.claude/agents/intent-challenge.md`);
  `close-review` → the fresh close-reviewer persona (named by increment #1; the skill
  references it by role, not by a hardcoded file name this increment cannot verify).
- Both fresh boundaries carry `human_signoff_after: true` (per YAML and ADR D2's two
  decorrelation checkpoints); `load-or-form-intent`, `construct`, `close` run
  `executor: conversation`, `context: current`, `human_signoff_after: false`.
- Approval is DELTA-TRIGGERED: intent-challenge + operator sign-off re-fire only on a
  new/material-change intent — a premise or `must-satisfy` clause edit — never on code
  diff-size (ADR D2; YAML `material-delta-classification` evidence).
- Verdict-field/node names in the SKILL drafts match `workflows/cairn-intent.yaml`
  EXACTLY (`delta_kind` ∈ {new, material-change, resume}; node `pass_output`/`fail_output`
  field names) so the Claude surface and the Codex SKILL stay reconciled.
- `using-cairn/SKILL.md` is a Claude-Code skill-chooser; its `cairn-intent` entry points
  at `workflows/cairn-intent.yaml` (same as the Codex chooser line) but routes to the
  Claude dispatch skill, not the Codex renderer snippet.
- The PROPOSED carrier emits, on session open, either the active-intent pointer (resume)
  or a no-intent signal, within a ≤2,000-token pointer-only budget; load is cheap with
  NO gate.

## Verification

- The skill draft references every node id in `workflows/cairn-intent.yaml` verbatim
  (grep each of the five ids in the draft).
- The draft's verdict/field vocabulary diffs clean against the YAML node `pass_output`/
  `fail_output` field names (no invented fields).
- The drafts live only under
  `.claude/skill-runs/cairn-intent-loop-build/skill-and-carrier/proposed/` — confirm no
  canonical path (`.claude/skills/`, `.claude/settings.json`, `tests/`, `templates/`,
  `workflows/`, the ADRs) was written by this increment (`git status` shows changes only
  under the skill-run dir).
- `## Premise Grounding` passes `uv run python checks/premise_guard.py <intent>` (exit 0)
  at the approval gate.
- `## Open Decisions` enumerates exactly the three /decision-class questions (a)-(c) with
  a concrete proposed default + tradeoff each, and NONE is committed as a canonical edit.

## Risk Surface

The domain-level wrongness that would pass a green file-existence check: the Claude
`cairn-intent` SKILL silently re-implements the Codex renderer's logic (duplicating the
loop instead of providing the native Agent-tool surface), or drifts a verdict field name
from the YAML so the two SKILLs disagree about the same loop — a reconciliation leak no
draft-write test catches. Second: silently COMMITTING a carrier "fired"/budget/fallback
contract (a) (b) (c) instead of surfacing it, foreclosing an operator /decision.

## Feature-Local Invariants

- The Claude `cairn-intent` SKILL drives the SAME `workflows/cairn-intent.yaml` and
  dispatches `.claude/agents` personas; it MUST NOT duplicate the Codex plugin's
  renderer logic — only provide the Claude-Code-native surface.
- No new Python module is introduced (honest-minimal: no real caller exists; executors
  render verdict shape from the YAML as string templates, the agent emits the JSON
  verdict line).
- Open-decision questions (a)-(c) are RECORDED with proposed defaults, never silently
  committed.

## Explicit Scope-Out

- The exact testable carrier "fired" definition + its unit test (open decision a).
- The ≤2k-token budget enforcement mechanism (open decision b).
- The precise fallback contract / no-intent signal shape (open decision c).
- The close-review/intent-review persona file (increment #1).
- Any canonical-path landing (settings.json registration, real SKILL files, carrier
  tests) — deferred to in-session operator-approved landing.
- `cairn-tdd-feature` retirement (ADR D7, future firm supersession).

## Premise Grounding

```yaml
premises:
  - source: docs/adr/intent-management-loop.md
    quote: |
      **D1 — Coexisting skill, no retirement here.** Build a new `cairn-intent` dispatch skill that
    label: "ADR D1 mandates a NEW cairn-intent dispatch skill coexisting with cairn-tdd-feature; this increment realizes the Claude-Code surface of it."
  - source: docs/adr/intent-management-loop.md
    quote: |
      **D5 — SessionStart carrier.** Build the `using-cairn` SessionStart carrier
      (`delivery-mechanism-friction` D1) with a **testable "fired" definition** (emits the intent
      pointer or a no-intent signal within the ≤2k-token INV-004 budget) and a **fallback**: if it
      doesn't fire, the skill's first step does load/form explicitly (carrier is an optimization,
      not the only path).
    label: "ADR D5 fixes the carrier shape (testable fired = emits intent pointer or no-intent signal within ≤2k budget; skill-first-step fallback); the exact test/budget/signal are left open."
  - source: docs/adr/intent-management-loop.md
    quote: |
      edited live. **Approval is delta-triggered** — re-fires only on a **premise or `must-satisfy`
      clause edit** (not on code diff-size). Construction is **fluid** (one continuous conversation,
      tests test-first, no phase resets), bracketed by **two decorrelation checkpoints**:
    label: "ADR D2 makes approval delta-triggered (re-fires only on premise/must-satisfy edit, not diff-size); the SKILL must encode delta-triggered re-fire, not per-session approval."
  - source: docs/adr/delivery-mechanism-friction.md
    quote: |
      Ship `using-cairn` SessionStart skill at `dist/skills/using-cairn/SKILL.md`, registered via `dist/hooks/hooks.json` per `m5-plugin-deployment-pattern` D4. Injection is **pointer-only**, hard-budgeted ≤2,000 tokens. Content: one-line substrate description, slash-command name-list with one-line each (no `.full.md` siblings), dispatch entry point literal, envelope-mode paragraph, gate-behavior paragraph, pointers to CONSUMER.md / operational-reference / spec-v1 for Tier-2 reads. Mirrors `context-discipline-protocol` three-tier shape: SessionStart is Tier-1 pointer, not summary.
    label: "delivery-mechanism-friction D1 fixes the carrier as pointer-only, hard-budgeted ≤2,000 tokens — the budget the proposed carrier mechanism must respect."
  - source: plugins/cairn/skills/using-cairn/SKILL.md
    quote: |
      - Use `cairn-intent` to operate the thin intent-management workflow from `workflows/cairn-intent.yaml`.
    label: "The Codex using-cairn chooser already routes cairn-intent at the SAME workflows/cairn-intent.yaml; the Claude chooser must point at the same YAML, not duplicate the Codex renderer."
  - source: .claude/skills/cairn-tdd-feature/SKILL.md
    quote: |
      Sequences four phase subagents to deliver a feature with TDD discipline and phase isolation. Each phase runs in a fresh context window via the Agent tool. This is cairn's protocol-layer dispatch primitive, post-orchestrator.
    label: "cairn-tdd-feature is the existing Claude dispatch skill that runs fresh subagents via the Agent tool; it is the LAYOUT precedent and stays as the coexisting fallback (ADR D1)."
  - source: workflows/cairn-intent.yaml
    quote: |
      executors:
        claude_dynamic_workflows:
    label: "The YAML carries a claude_dynamic_workflows executor block; the Claude SKILL realizes the conversation + fresh-agent boundaries this block describes, not the Codex spawn_agent dispatch."
  - source: .claude/agents/intent-challenge.md
    quote: |
      You are the front-loaded Skeptic of the cairn-intent loop. On a new or materially-changed intent you attack its premises against live source **before** construction starts, with fresh context and no same-context fallback. You have seen only the intent and the source it cites — not the reasoning that produced it.
    label: "The intent-challenge persona already exists; the cairn-intent SKILL dispatches it as a fresh-context subagent (subagent_type: intent-challenge) at the front-loaded checkpoint."
```

## Contract

```yaml
must-satisfy:
  - clause: where a new or materially-changed intent exists, the cairn-intent SKILL draft shall dispatch the intent-challenge fresh-context subagent and require operator sign-off before construction
    except: "operator-bound: operator confirms the human sign-off boundary is encoded after intent-challenge per workflows/cairn-intent.yaml human_signoff_after: true"
  - clause: the cairn-intent SKILL draft references every loop node id from workflows/cairn-intent.yaml
    except: "universal-set: the node set is the 5 ids in workflows/cairn-intent.yaml — load-or-form-intent, intent-challenge, construct, close-review, close"
  - the cairn-intent SKILL draft shall keep approval delta-triggered, re-firing the challenge only on a premise or must-satisfy clause edit and never on code diff-size
  - the using-cairn SKILL draft shall route the cairn-intent entry at workflows/cairn-intent.yaml without duplicating the Codex plugin renderer logic
  - the proposed carrier draft shall, on session open, emit either the active-intent pointer or a no-intent signal as a pointer-only payload
  - where the carrier does not fire, the cairn-intent SKILL draft's first step shall load or form the intent explicitly
  - clause: the increment shall record exactly the three open-decision questions (carrier fired-test, 2k-budget enforcement, fallback signal shape) with a proposed default and tradeoff each, and commit none of them
    except: "universal-set: the open-decision set is the 3 questions a/b/c in the ## Open Decisions block"
must-not-violate:
  - INV-004 fresh-session token budget — the proposed carrier stays within the ≤2,000-token pointer-only ceiling
  - INV-003 and the firm phase ADRs remain unmodified — cairn-tdd-feature is retained as the coexisting fallback (ADR D1/D7)
  - no canonical path is written this increment — only drafts under the skill-run proposed/ dir
wrong-if:
  - the Claude cairn-intent SKILL re-implements the Codex renderer logic instead of providing the native Agent-tool surface
  - any verdict/field name in the SKILL drafts diverges from a workflows/cairn-intent.yaml node pass_output/fail_output field name
  - any open-decision question is silently committed as a canonical contract instead of surfaced
  - a new Python module is introduced with no existing caller
escalate-when:
  - a draft cannot satisfy a node contract without editing workflows/cairn-intent.yaml or an ADR (those are sources, not realizations)
  - the close-review persona name is needed concretely but increment #1 has not fixed it
evidence:
  - grep of the 5 node ids present in the cairn-intent SKILL draft
  - diff of SKILL-draft verdict/field vocabulary against workflows/cairn-intent.yaml node field names (no invented fields)
  - git status showing writes confined to .claude/skill-runs/cairn-intent-loop-build/skill-and-carrier/
  - premise_guard exit 0 on this intent.md
  - the ## Open Decisions block enumerating a/b/c with proposed defaults, uncommitted
execution-scope:
  - .claude/skill-runs/cairn-intent-loop-build/skill-and-carrier/intent.md
  - .claude/skill-runs/cairn-intent-loop-build/skill-and-carrier/proposed/
```

## Open Decisions

<!--
SURFACE, don't DECIDE. Each carries a concrete proposed default + the tradeoff and is
left for the operator. Brainstorm Q4 leaves (a)-(c) to /decision; ADR D5 gives the shape
but not the exact test. Do NOT commit these as canonical edits this increment.
-->

- **(a) Testable "carrier fired" definition + unit-test detection.**
  Proposed default: define "fired" as the carrier writing/refreshing a single
  machine-readable marker on session open — an `active-intent` line in `.claude/handoff.md`
  (resume) OR an explicit `cairn-intent: none` signal token — and have the unit test assert
  the carrier function returns that marker shape (pointer string or the no-intent sentinel)
  given a fixture session-open input, rather than asserting on Claude-Code host behaviour
  the test cannot drive.
  Tradeoff: a pure-function marker test is deterministic and host-independent (good), but it
  tests the carrier's RENDER, not that Claude Code actually injects it at SessionStart — the
  real "fired on the host" claim stays an integration/dogfood observation (Trial E), not a
  unit test. Asserting on real host injection would need a live Claude-Code session harness
  cairn does not have.

- **(b) ≤2k-token budget enforcement mechanism.**
  Proposed default: enforce the ≤2,000-token pointer-only ceiling with a unit test that
  measures the carrier payload's size against a `CAIRN_CARRIER_TOKEN_BUDGET` env-var
  (default 2000, per the no-hardcoded-budget rule) using a cheap char/word proxy, NOT a
  tokenizer dependency — keeping deps at pydantic/typer/pyyaml (ADR D6).
  Tradeoff: a char/word proxy adds no dependency and fails closed on bloat (good), but it
  approximates tokens — it can pass a payload that a real tokenizer would score >2k, or
  conversely flag a compact one. delivery-mechanism-friction D6 contemplated a CI
  token-budget check; whether cairn wants the proxy unit test, a CI step, or both is the
  operator's call. (Note: D6 names `dist/`-side CI; this increment's carrier is the
  `.claude/`-side source, so the budget mechanism may differ.)

- **(c) Precise fallback contract / no-intent signal shape.**
  Proposed default: the fallback is the cairn-intent SKILL's first step (`load-or-form-intent`)
  unconditionally running load/form — the carrier is a pure optimization, so the SKILL does
  NOT branch on "did the carrier fire?"; it always loads/forms, and a fired carrier merely
  means the pointer is already in context. The no-intent signal is the literal sentinel from
  (a) (`cairn-intent: none`), surfaced verbatim so the SKILL step can recognize "form a new
  intent" vs "resume the pointed-at one".
  Tradeoff: unconditional load/form is the simplest, most robust fallback (the carrier can
  never strand a session) and matches ADR D5's "carrier is an optimization, not the only
  path" — but it means the carrier's pointer is re-derived by the SKILL step even when the
  carrier did fire, a small redundant read. The alternative (SKILL trusts the carrier marker
  and skips re-load when present) is cheaper but couples the SKILL to the carrier's exact
  marker contract and risks a stale-load if the marker drifts — which the ADR pre-mortem
  flagged as a fatal failure mode for the rejected "approve every session" design.

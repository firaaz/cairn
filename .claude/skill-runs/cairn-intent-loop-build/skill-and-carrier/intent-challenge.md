# intent-challenge — skill-and-carrier (Trial-E increment #2)

Front-loaded Skeptic, fresh context. Target intent:
`.claude/skill-runs/cairn-intent-loop-build/skill-and-carrier/intent.md`
(snapshot-sha `ef14b98`, confirmed = current HEAD).

`premise_guard.py` exits **0** on this intent (run with
`CLAUDE_PROJECT_DIR=<worktree>`): every `quote:` is verbatim-present in its
`source:`. That only certifies the quote is live. The challenge below is
semantic: does each `label:` faithfully describe the cited span, and do the
dependent `must-satisfy` clauses hold against the live source?

## premise-source-checks

**P1 — intent-management-loop.md, D1 quote (intent lines 127-130).**
Read `docs/adr/intent-management-loop.md:52-56`. Quote
`"**D1 — Coexisting skill, no retirement here.** Build a new \`cairn-intent\`
dispatch skill that"` is verbatim at line 52. Surrounding lines confirm the
label exactly: D1 says build a NEW `cairn-intent` skill that "coexists with
`cairn-tdd-feature` (unchanged)" and the four-phase pipeline/INV-003/firm phase
ADRs are "retained unmodified." Label ("ADR D1 mandates a NEW cairn-intent
dispatch skill coexisting with cairn-tdd-feature; this increment realizes the
Claude-Code surface") is faithful. Dependent clauses: `must-not-violate` "INV-003
... remain unmodified — cairn-tdd-feature retained as the coexisting fallback"
holds against D1. **Survives.**

**P2 — intent-management-loop.md, D5 quote (intent lines 132-137).**
Read `docs/adr/intent-management-loop.md:77-81`. Quote verbatim. D5 says: build
the `using-cairn` SessionStart carrier with a "testable 'fired' definition (emits
the intent pointer or a no-intent signal within the ≤2k-token INV-004 budget)"
and a "fallback: if it doesn't fire, the skill's first step does load/form
explicitly (carrier is an optimization, not the only path)." Label is faithful,
INCLUDING the load-bearing tail "the exact test/budget/signal are left open" —
D5 fixes the *shape* but specifies neither the test mechanism nor the budget
enforcement nor the signal token. This directly licenses the intent's
SURFACE-don't-DECIDE handling of open decisions (a)-(c). Dependent clauses: the
carrier must-satisfy ("emit either the active-intent pointer or a no-intent
signal as pointer-only") and the fallback clause ("where the carrier does not
fire, the SKILL's first step shall load or form the intent explicitly") both map
1:1 to D5. **Survives.**

**P3 — intent-management-loop.md, D2 quote (intent lines 140-143).**
Read `docs/adr/intent-management-loop.md:58-64`. Quote verbatim
("...edited live. **Approval is delta-triggered** — re-fires only on a **premise
or `must-satisfy` clause edit** (not on code diff-size). Construction is
**fluid**..."). Label ("approval delta-triggered, re-fires only on
premise/must-satisfy edit, not diff-size; the SKILL must encode delta-triggered
re-fire, not per-session approval") is faithful; D2's "intent is an always-on
anchor ... Approval is delta-triggered" and the two-decorrelation-checkpoints
sentence back it. Dependent clause (must-satisfy "keep approval delta-triggered,
re-firing the challenge only on a premise or must-satisfy clause edit and never
on code diff-size") is a verbatim restatement of D2. **Survives.**

**P4 — delivery-mechanism-friction.md, D1 quote (intent lines 145-147).**
Read `docs/adr/delivery-mechanism-friction.md:37-39`. Quote verbatim. D1 fixes
the carrier as pointer-only, hard-budgeted ≤2,000 tokens. Label ("delivery-
mechanism-friction D1 fixes the carrier as pointer-only, hard-budgeted ≤2,000
tokens — the budget the proposed carrier mechanism must respect") is faithful.

Counterfactual attempted (the one place a misread could hide): D1's literal text
ships the carrier at **`dist/skills/using-cairn/SKILL.md`** registered via
**`dist/hooks/hooks.json`** — the distribution side. This increment's canonical
target is the **`.claude/`-side** `using-cairn/SKILL.md` and a SessionStart
registration "likely in `.claude/settings.json`." So is the label asserting a
`.claude/`-side ≤2k budget that the quoted `dist/`-side D1 does not actually
mandate? Checked: the label scopes only to "the budget the proposed carrier
mechanism must respect" — it claims the *budget*, not the *location*, and the
budget (≤2k pointer-only, INV-004) is location-independent by D1+D5+INV-004.
The intent does NOT silently assert the carrier lives at `dist/` nor that the
`dist/` registration is this increment's target; open-decision (b) explicitly
flags the divergence ("D6 names `dist/`-side CI; this increment's carrier is the
`.claude/`-side source, so the budget mechanism may differ"). The counterfactual
does not hold — the label is budget-only and the location tension is surfaced,
not buried. Verified `dist/skills/using-cairn/` exists but is EMPTY and
`dist/hooks/hooks.json` carries no SessionStart entry — the carrier is genuinely
unbuilt on both sides, consistent with the intent. **Survives.**

**P5 — plugins/cairn/skills/using-cairn/SKILL.md quote (intent lines 149-151).**
Read `plugins/cairn/skills/using-cairn/SKILL.md:17`. Quote verbatim
("- Use `cairn-intent` to operate the thin intent-management workflow from
`workflows/cairn-intent.yaml`."). Label ("the Codex using-cairn chooser already
routes cairn-intent at the SAME workflows/cairn-intent.yaml; the Claude chooser
must point at the same YAML, not duplicate the Codex renderer") is faithful: the
chooser line names the same YAML. The "not duplicate the Codex renderer" half of
the label is corroborated by the sibling Codex `cairn-intent/SKILL.md`, whose
"Rendering Dispatch Briefs" section is the renderer logic (a `render_codex_
dispatch_brief` snippet + `spawn_agent`/`fork_context: false`) that the Claude
surface must NOT reproduce. Dependent clauses (`must-satisfy` "route the
cairn-intent entry at workflows/cairn-intent.yaml without duplicating the Codex
plugin renderer logic"; `wrong-if` "re-implements the Codex renderer logic")
hold. **Survives.**

**P6 — .claude/skills/cairn-tdd-feature/SKILL.md quote (intent lines 153-155).**
Read `.claude/skills/cairn-tdd-feature/SKILL.md:8`. Quote verbatim ("Sequences
four phase subagents to deliver a feature with TDD discipline and phase
isolation. Each phase runs in a fresh context window via the Agent tool. This is
cairn's protocol-layer dispatch primitive, post-orchestrator."). Label
("cairn-tdd-feature is the existing Claude dispatch skill that runs fresh
subagents via the Agent tool; it is the LAYOUT precedent and stays as the
coexisting fallback") is faithful: the file IS a Claude-Code dispatch skill that
calls the Agent tool with `subagent_type:` (Steps 4-10), and D1 retains it as the
fallback. **Survives.**

**P7 — workflows/cairn-intent.yaml quote (intent lines 157-160).**
Read `workflows/cairn-intent.yaml:270-271` (`executors:` / `claude_dynamic_
workflows:`). Quote verbatim. Label ("The YAML carries a
claude_dynamic_workflows executor block; the Claude SKILL realizes the
conversation + fresh-agent boundaries this block describes, not the Codex
spawn_agent dispatch") — checked the block body (lines 271-292): it documents a
`split_reason` (Claude dynamic workflows can't take mid-run input → approval
boundaries are separate runs), a `save_policy`, and two `runs`
(`cairn-intent-challenge`, `cairn-intent-close-review`) each with
`human_signoff_after: true`. This is the Claude-side executor, distinct from the
`codex_agents` block (lines 293-318) that uses `spawn_agent`/`fork_context:
false`. Label faithful.

Counterfactual attempted: does "the conversation + fresh-agent boundaries this
block describes" overclaim? The `claude_dynamic_workflows` block names only the
two FRESH-agent runs; the three `conversation`-executor nodes (load-or-form,
construct, close) are listed under the separate `conversation:` executor block
(lines 319-323), not under `claude_dynamic_workflows`. So the intent's premise
label folds two executor blocks ("conversation + fresh-agent boundaries") into a
claim attributed to the single quoted `claude_dynamic_workflows` block. This is
loose phrasing, but NOT a false claim about source: (i) the intent's actual
Specification (lines 61-63) and must-satisfy clauses correctly assign
`executor: conversation` to the three nodes and `fresh_agent` only to
intent-challenge/close-review — matching the YAML node `execution:` blocks
exactly (verified node-by-node: load-or-form-intent `executor: conversation`
L62, intent-challenge `executor: fresh_agent` L113, construct `conversation`
L162, close-review `fresh_agent` L213, close `conversation` L266); (ii) the
premise's operative assertion is the contrast "not the Codex spawn_agent
dispatch," which is true. The counterfactual reading (claude_dynamic_workflows
alone describes the conversation nodes) does not survive contact with the
Specification, which sources the per-node executors correctly. No dependent
clause inherits a false belief. **Survives** (with the loose-phrasing note above
recorded for the operator, not blocking).

**P8 — .claude/agents/intent-challenge.md quote (intent lines 162-164).**
Read `.claude/agents/intent-challenge.md:7`. Quote verbatim. Label ("The
intent-challenge persona already exists; the cairn-intent SKILL dispatches it as
a fresh-context subagent (subagent_type: intent-challenge) at the front-loaded
checkpoint") is faithful: the file exists at `.claude/agents/intent-challenge.md`
(confirmed via `ls`), its frontmatter `name: intent-challenge` makes
`subagent_type: intent-challenge` a real dispatch target, and the body is the
front-loaded fresh-context Skeptic. **Survives.**

## semantic-counterfactual-search

For each premise I constructed a reading where the grounded quote is true but the
intent claim is false:

- **P1**: "D1 retires cairn-tdd-feature" — FALSE reading, D1 says "no retirement
  here" + "retained unmodified." Counterfactual does not hold; label is correct.
- **P2**: "D5 fixes the exact fired-test / budget mechanism / signal token, so
  surfacing them as open decisions is wrong" — FALSE reading. D5 fixes only the
  shape; the label's "exact test/budget/signal are left open" is the faithful
  reading. The slice-#25 trap here would be COMMITTING (a)-(c) as if D5 settled
  them; the intent does the opposite (surfaces them). Counterfactual does not
  hold.
- **P3**: "approval re-fires per session / on diff-size" — FALSE reading, D2 says
  "delta-triggered ... not on code diff-size." Counterfactual does not hold.
- **P4** (the load-bearing one): "the ≤2k budget the label cites is a
  `.claude/`-side mandate D1 makes" — D1's quote is `dist/`-side. Tested: label
  claims budget (location-independent), not location; open-decision (b) surfaces
  the `dist/` vs `.claude/` divergence explicitly. Counterfactual does not hold —
  the misread is pre-empted by the intent's own surfacing.
- **P5**: "the Codex chooser proves the Claude SKILL may reuse the Codex
  renderer" — FALSE reading; chooser shares the YAML, and the sibling Codex
  cairn-intent SKILL is the renderer the Claude side must NOT duplicate (wrong-if
  clause). Counterfactual does not hold.
- **P6**: "cairn-tdd-feature is being retired/replaced as the precedent" — FALSE
  reading; it stays as the D1 fallback. Counterfactual does not hold.
- **P7**: "claude_dynamic_workflows describes the conversation-executor nodes" —
  partially-tempting reading (the block only names the two fresh-agent runs). It
  does NOT survive against the intent's node-level Specification, which sources
  each node's executor from its own YAML `execution:` block correctly. Recorded
  as loose premise phrasing, not a false dependent claim. Counterfactual does not
  hold at the level that matters (no must-satisfy clause inherits a false
  belief).
- **P8**: "the intent-challenge persona doesn't exist / isn't a valid
  subagent_type" — FALSE; file present, `name: intent-challenge` frontmatter
  makes it dispatchable. Counterfactual does not hold.

## Corroborating live-source checks (beyond the cited premises)

- `.claude/settings.json` carries only PreToolUse/PostToolUse hooks — **no
  SessionStart entry**; `dist/hooks/hooks.json` likewise. The carrier registration
  is genuinely net-new, consistent with the intent treating it as PROPOSED.
- No `close-review`/`intent-review` persona file exists under `.claude/agents/`,
  `dist/agents/`, or `plugins/cairn/agents/`. The intent correctly references the
  close-reviewer "by role, not by a hardcoded file name this increment cannot
  verify" (intent lines 58-60) and scopes the persona file out to increment #1
  (Explicit Scope-Out). This is the right SURFACE/ESCALATE handling — no
  fabricated dependency.
- All five node ids are present in `workflows/cairn-intent.yaml` (`id:` count:
  load-or-form-intent 1, intent-challenge 1, construct 1, close-review 2, close 3
  — extras are the executor-run `nodes:` references; the verification clause is
  satisfiable). `delta_kind` IS a real `pass_output` field (YAML L53). The value
  enum `{new, material-change, resume}` (intent L68) lives in YAML *description*
  prose (L44) + node prompt prose (L26-27), not as a pinned machine enum, and
  `material_change` is a separate `pass_output` field (L55). This is the intent's
  own reconciliation-target vocabulary, declared as such in Specification — not a
  premise citing the YAML for an enum it lacks. Not a misrepresentation.
- `premise_guard.py` docstring + body confirm it reads the `## Premise Grounding`
  block, diffs each quote verbatim against live source, and does NOT read
  `label:` — exactly the gap this challenge fills. Ran it: **exit 0**.

## verdict

All eight premises survive the semantic challenge. Every `label:` faithfully
describes its cited span, no dependent `must-satisfy` clause inherits a belief no
quote pins, and the two tempting counterfactuals (P4 `dist/`-vs-`.claude/` budget
location, P7 executor-block scope) are pre-empted by the intent's own surfacing
(open-decision b) and node-level Specification respectively. The slice-#25 trap
for this increment — silently committing the carrier fired-test / ≤2k-budget /
fallback-signal contract that D5 leaves open — is actively avoided: the intent
records them as open decisions (a)-(c) with proposed defaults + tradeoffs and
commits none. No blocking finding. Two non-blocking notes for the operator: (1)
P7's premise label folds the conversation + fresh-agent executor blocks into a
claim attributed to the single quoted `claude_dynamic_workflows` block — loose
phrasing, correctly disambiguated in the Specification; (2) open-decision (b)'s
`dist/`-side (D6) vs `.claude/`-side budget-mechanism divergence is real and
correctly surfaced, not resolved.

```json
{"status": "challenge-pass", "verdict": "All 8 premises grounded AND semantically faithful; the D5-open carrier contracts (a/b/c) are surfaced not committed; no must-satisfy clause inherits an unpinned belief.", "challenged_premises": ["P1-D1-coexist", "P2-D5-carrier", "P3-D2-delta-triggered", "P4-deliveryD1-2k-budget", "P5-codex-using-cairn-chooser", "P6-cairn-tdd-feature-precedent", "P7-yaml-claude_dynamic_workflows", "P8-intent-challenge-persona"], "cited_evidence": ["intent-management-loop.md:52-56 (D1)", "intent-management-loop.md:77-81 (D5)", "intent-management-loop.md:58-64 (D2)", "delivery-mechanism-friction.md:37-39 (D1)", "plugins/cairn/skills/using-cairn/SKILL.md:17", ".claude/skills/cairn-tdd-feature/SKILL.md:8", "workflows/cairn-intent.yaml:270-271 + per-node execution blocks", ".claude/agents/intent-challenge.md:7", "premise_guard exit 0", "no SessionStart in .claude/settings.json or dist/hooks/hooks.json", "no close-review persona file present"], "blocked_counterfactuals": ["P2: D5 settles the exact fired-test/budget/signal (false — D5 fixes shape only; intent surfaces a/b/c)", "P4: the cited 2k budget is a .claude/-side mandate (false — label is budget-only, location divergence surfaced in open-decision b)", "P7: claude_dynamic_workflows block describes the conversation-executor nodes (false — Specification sources per-node executors correctly)"]}
```

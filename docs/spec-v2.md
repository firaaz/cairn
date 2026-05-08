# Slice-Based Development System (spec v2)

*Personal methodology, Claude Code-coupled, single-developer use. This document is the spec; the implementation lives in `.claude/` plus `checks/`, `scripts/`, and `commands/claude-code/`.*

*Revision: spec v2 is a structural redraft of v1. The trigger was direct dogfooding evidence: cairn's primary user — the author — was preferring not to use cairn for daily work because the four-fresh-session phase ceremony cost more (operator attention and tokens) than it bought (test depth, implementation fidelity, architectural fit) compared to plain superpowers TDD with brainstorming inline. Two related problems compounded the cost: (a) ADRs and ARCHITECTURE.md were producing artifacts but not producing the constraint they were supposed to produce — cited but not consulted; firm-by-fiat; validator-green ≠ semantically sound; (b) the operator was doing too much of the discipline-authoring work (intent.md, plan-doc, ADR drafting, dispatch invocation) when the design promise was that discipline lives in the agent layer below the conversation, not above it.*

*v2 keeps v1's honesty, empirical anchoring, and mechanical enforcement layer. It rewrites the per-feature workflow: the four sequential fresh-session phases collapse into a continuous-conversation feature loop with one fresh-context review subagent at loop close (where the strongest empirical anchor — Song et al. 2026 — actually attaches). It reframes routing as agent-recognized rather than operator-driven slash commands. It demotes the greenfield/modification distinction to mode-agnostic. It marks the substrate redesign (ADRs / ARCHITECTURE.md) as an explicit open question rather than papering over the credibility gap.*

*v2 deliberately does NOT collapse cairn's fragmented file artifacts into a single document. Fragmentation is a context-discipline feature, not a bug — it lets `/catchup` Tier 2 query specific files rather than load a monolith.*

*v2 does NOT supersede v1 until the operator promotes it. Until then, v1 remains the canonical spec; v2 is the proposal.*

---

## Status Legend

Each section and major claim is tagged with implementation status so attacks land at the right layer:

- **[IMPLEMENTED]** — Working in the repo. Observable.
- **[IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE]** — Feature exists; no hook or validator enforces it. Discipline-only.
- **[PARTIAL]** — Partially implemented. The description specifies what is and what isn't.
- **[PLANNED]** — Designed; not yet built. Concrete enough to implement next.
- **[DESIGN-ONLY]** — Described; no implementation plan. Marked so reviewers know not to attack it as if it ran.
- **[OPEN-QUESTION]** — Named, unresolved. Brought into the spec deliberately rather than papered over.
- **[ACKNOWLEDGED]** — Failure mode the system cannot prevent. Discipline only.
- **[V2-PROPOSAL]** — Element new in v2 relative to v1; not yet implemented; concrete enough to schedule.
- **[DEFENSE-IMPLEMENTED]**, **[DEFENSE-PARTIAL]**, **[DEFENSE-PLANNED]** — Tags applied to known failure modes describing the state of the defense, not the failure mode itself.

---

## 1. Scope [IMPLEMENTED]

The system is for **genuinely complex software engineering** — safety-critical systems, long-horizon projects with many interwoven components, domains where integration between components is the hard part, and projects accumulating architectural decisions that are actively maintained. It is for human-led engineering where AI is a powerful collaborator but the human remains responsible for architectural integrity over time.

**It is not for simple software.** For CRUD apps, prototypes, AI wrappers, and internal scripts, the overhead is pure waste. Frontier models with planning modes and auto-compact handle straightforward work effectively without any of this. The system's value comes from preventing failure modes that only manifest in complex, long-horizon work.

**Mode-agnostic.** v1 made greenfield-first the default and treated modification as a documented extension. v2 drops that distinction. Real projects iterate from day one; greenfield is a transient phase, not a design center. The discipline applies the same way to creating a new module and to changing an existing one. Where v1 prescribed "read public interfaces only" for modification slices, v2 makes that a soft heuristic, not a phase rule — what matters is that the work doesn't smuggle in implementation knowledge that the verification step is supposed to discover independently.

**Daily-usability constraint.** v2 elevates day-to-day usability to a first-class scope constraint. A methodology that the author refuses to use on routine work cannot reach the long-horizon coherence wins it claims. If the operator-facing friction exceeds the per-feature value, the system has failed even if every individual mechanism is theoretically sound. This constraint is the design center of v2's loop redesign (§5) and is recorded as a known unaddressed constraint in v1 (humans-must-remain-operable) extended in §16.

---

## 2. Core Thesis [V2-PROPOSAL replaces v1 §2]

Complex AI-assisted development requires **role purity at the verification step** combined with **conversation continuity during construction**. The mechanism is a single fresh-context review subagent dispatched at the close of a feature loop, not four fresh sessions one per phase.

**Conversation continuity during construction.** Building a feature is a tightly-coupled cognitive process: spec evolves as constraints surface; tests evolve as the spec sharpens; implementation surfaces edge cases that loop back to the spec. v1's four-fresh-session phase model severed these loops, forcing the operator to re-bootstrap context at each boundary and producing artifacts that crossed the boundary thinner than the construction process required. The empirical evidence v1 cited for the dual mechanism (Song et al. 2026, 4.0 F1-point improvement from cross-context review) is specifically about **review**, not construction. v2 preserves the review claim and abandons the per-phase claim.

**Role purity at the verification step.** A fresh-context subagent dispatched at loop close — given only the spec, the implementation diff, and the test output — produces independent verification that the same agent's continuous-session self-review demonstrably does not (Tsui et al. 2025, 64.5% self-correction blind-spot rate). This single fresh-context anchor is where role purity earns its weight. Multiplying it across four phases multiplied the cost without multiplying the value.

**Operator-strategic / agent-discipline UX thesis.** The operator is the strategic mind: deciding what the project is, what to build next, what counts as "right" at the architectural level. Discipline — TDD's RED-before-GREEN, decision protocol's adversarial enumeration, substrate maintenance, verification — lives in the agent layer (skills + hooks + subagents) below the conversation. The operator's role at session boundaries is to *close* sessions when topic shifts or context bloats; the agent can prompt this. The operator does not author intent.md, plan-docs, ADR drafts, or dispatch invocations. The agent does.

These three commitments are inseparable. Fresh-context review without conversation continuity reproduces v1's per-feature cost without the construction-loop integrity. Conversation continuity without fresh-context review reproduces single-session self-confirmation. Operator-strategic without agent-discipline reproduces ad-hoc prompting. The combination is the v2 mechanism.

The role-purity-at-verification claim is more defensible than v1's role-purity-at-every-phase claim because the load-bearing empirical work (Song et al.) is about cross-context review specifically. v2 narrows the claim to where the evidence actually supports it. Where the evidence is absent (per-phase role purity), v2 stops claiming it.

---

## 3. What the Thesis Does Not Claim

**It does not claim fresh context catches model-inherent correlated errors.** Cross-family error agreement is well documented (Kim et al., ICML 2025; see §17). Two fresh sessions of the same model family will reproduce the same systematic blind spots. The mechanism being defended is review-step contamination during the same continuous session, not model-inherent bias.

**It does not claim every phase boundary needs a fresh session.** v1 made this claim and v2 retracts it. The empirical evidence supports fresh-context review as a checkpoint, not as a ubiquitous pipeline rule.

**It does not claim subagents are useless.** Subagents are the right tool for branching paths inside a loop iteration — parallel exploration, scoped lookups, the fresh-context review checkpoint itself. They are the wrong tool when their return summaries pollute the parent's context unboundedly. v2 binds review-subagent returns with a hard word cap (~200 words) at the protocol level, identical to the `/catchup` Tier 2 cap.

**It does not claim compaction is bad.** Compaction is useful within a continuing conversation. It is inadequate as a substitute for the committed artifacts that persist across sessions and as inputs to fresh-context review.

**It does not claim committed artifacts are interpretation-stable.** Natural language is not interpretation-stable. Two readers can read the same document and arrive at different interpretations of ambiguous sections. This is a real failure mode (interpretation drift) distinct from authorship contamination. See §13.

**It does not claim the substrate as currently shaped is sound.** ADRs and ARCHITECTURE.md as currently implemented have credibility issues — firm-by-fiat firmness tags, cited-but-not-consulted ADR references, validator-green that doesn't catch semantic drift. v2 names this as an explicit open question (§9) rather than papering over it.

**It does not claim its discipline is justified by current evidence.** The system's rigor is calibrated to a higher confidence level than the empirical support justifies. This is a deliberate trade-off for safety-critical work, not an oversight. Users should make this trade-off consciously. See §17 (calibration gap).

---

## 4. Routing: Ad-Hoc, Decide, Feature-Loop [V2-PROPOSAL]

Routing in v2 is **agent-recognized**. The operator describes the work in natural language. The agent classifies the work and selects a discipline path. The operator can override the classification at any point.

Three paths:

- **Ad-hoc edit** — one-line fix, doc tweak, multi-file refactor with no clear failing-test shape. The agent edits directly. The operator envelope (`.claude/active-envelope.yaml`) gates writes; reversibility-guard and reality-check still fire. Conventional commit prefix from the registry.
- **Decide skill** — work touches invariants, boundaries, data ownership, or module structure. The agent invokes the decide skill (lightened version of v1's `/decision` adversarial protocol) and surfaces an ADR draft for operator approval. ADR is committed before any implementation work begins.
- **Feature-loop skill** — vertical behavior change with a clear failing-test shape. The agent invokes the feature-loop skill (§5). Multiple commits across the loop iteration; one fresh-context review subagent at loop close.

Routing rule of thumb: if the work could change what downstream features can assume, route to decide. If it only fills in detail within an existing assumption, route to feature-loop. Anything smaller routes to ad-hoc.

**Routing recovery.** When agent classification is wrong, the operator overrides. The skill itself can also raise a routing escalation — e.g., feature-loop discovering an architectural invariant change mid-loop fails the loop and triggers decide. Existing v1 routing recovery rules (§4) carry forward unchanged.

**Routing as a wall (v2 promise).** Agent-recognized routing is the v2 wall against the routing-self-classification failure mode v1 named (§13). The agent explicitly classifies and the operator confirms the classification surfaces in the conversation, not in a slash command. This is friction-plus-walls one level up: the wall is the agent's mandatory classification step before any work; the friction is the conversation overhead of correcting a misclassification.

The slash-command surface (`/decision`, `/start-slice`, `/handoff`, `/catchup`) is preserved as an explicit-invocation escape but is not the default. v2's default is conversational; slash commands are the operator's explicit override.

---

## 5. Feature Loop [V2-PROPOSAL replaces v1 §5]

A feature loop is a continuous-conversation iteration over four steps: **spec-evolve → tests → code → review**. Each step commits its artifact. The loop iterates until the review step passes. The fresh-context boundary applies once per loop, at the review step, not between steps.

The four steps run in the same session. The operator and agent share the conversation context throughout. Skills called inside the loop (TDD, brainstorming, dispatch-parallel) inherit the conversation context. The review step alone runs in a fresh subagent with bounded context.

**Step 1 — Spec-evolve.** The agent maintains the per-feature spec at `.claude/skill-runs/<feature-id>/intent.md` (file path unchanged from v1; authoring shifts from operator to agent). On loop entry, the agent drafts the spec from the conversation. On each loop iteration where new constraints surface (from test discovery, implementation reality, or operator direction), the agent updates the spec and surfaces the diff for operator approval. The intent file holds: envelope (the source-write regex set), what/why/boundary, specification detail, verification criteria, and properties (§15). Plan-doc files at `docs/plans/<date>-<feature-id>.md` remain a separate persistence layer for operator-authored project goals; the agent reads them but doesn't author them.

**Step 2 — Tests.** The agent writes RED tests against the current spec. RED is verified (the test must fail before implementation is allowed to start). This is the same RED-before-GREEN discipline as superpowers TDD; v2 places it inside the loop rather than as a phase boundary. Test files commit when RED is verified.

**Step 3 — Code.** The agent writes implementation that turns RED tests GREEN. The implementation runs under the role_guard envelope read from the current spec's envelope field. reality-check (ruff format / ruff check) fires on every Python edit. GREEN is verified before the loop advances.

**Step 4 — Review.** The agent dispatches a fresh-context review subagent. The review subagent receives only:
- the current spec (`intent.md`)
- the diff committed by Steps 2 and 3
- full pytest output
- the architecture validator output
- the list of declared invariants and their evidence requirements

The review subagent's charter is to verify each declared invariant against the current codebase with `file:line` citation evidence, run cross-module checks (imports, types), produce a pass/fail summary, and return ≤200 words. The subagent has no access to the conversation history, the spec-evolve drafting reasoning, or the test-design reasoning. This is the fresh-context boundary.

**Loop exit conditions.** The loop exits when (a) review passes, in which case the agent commits the review's sweep-notes to `.claude/skill-runs/<feature-id>/integration/sweep-notes.md` and surfaces the result to the operator; or (b) review fails for an implementation reason, in which case the agent escalates to the operator (do not patch implementation to force review pass — that recreates the correlated-error problem); or (c) review fails for a spec reason (the spec was wrong, not the implementation), in which case the agent loops back to spec-evolve.

**Commit cadence.** Each step commits when complete: spec-evolve commits intent.md (and plan-doc if authored inline); tests commits the test files; code commits the implementation; review commits sweep-notes. Iterations within the loop produce additional commits (re-spec, additional tests). The git history is the audit trail — same as v1, more linear.

**What v2 keeps from v1's phase model.** RED-before-GREEN as discipline. Envelope-gated writes. Fresh-context for verification. ADRs as decision substrate. Mechanical enforcement via hooks. Integration sweeps (§11). The feature-id-keyed workspace at `.claude/skill-runs/<feature-id>/`.

**What v2 drops.** Four sequential fresh-session phase boundaries. Four separate phase-N-tdd agents (collapsed to one feature-loop skill plus the review subagent). Operator-authored intent.md / plan-doc dispatch ceremony. The mandatory plan-doc-then-skill-invoke gesture before starting work.

---

## 6. Decision Skill [V2-PROPOSAL replaces v1 §6]

The decide skill is v1's eight-sub-phase adversarial decision protocol, lightened and packaged as an agent-invokable skill rather than an operator slash command. The protocol survives because it has earned its keep — adversarial enumeration plus pre-mortem catches bad architectural calls. The packaging changes because operator-driven invocation was a friction layer that caused the protocol to be skipped on borderline calls.

**v2 decide-skill phases (lightened from v1's eight to six):**

- **Phase 0 — Constraint Harvest.** Read ARCHITECTURE.md, ADR index, relevant ADRs, lessons file. Produce a list of specific constraints with source citations. Surface conflicts.
- **Phase 1 — Forced Enumeration.** Enumerate at least three viable approaches with evidence-backed citations (file:line for codebase, ADR-id for substrate). Rate each against pre-mortem scenarios.
- **Phase 2 — Pre-Mortem.** Imagine the decision failed three months from now. Three failure scenarios: technical, scale, integration.
- **Phase 3 — Adversarial Stress Test.** Disconfirming search; steel-man the second-best approach; assumption audit.
- **Phase 4 — Decision Record.** Draft the ADR with proper YAML frontmatter. Default `firmness: provisional`.
- **Phase 5 — Independent Verification (firm decisions only).** Fresh-context subagent re-runs Phases 1-3 independently. Same output → high confidence; divergent output → surface to operator. See §7.
- **Phase 6 — Propagation.** After the ADR is accepted: update ARCHITECTURE.md; check whether any in-progress feature-loop's spec needs updating; verify superseded ADR frontmatter; record cross-cutting patterns in `docs/lessons.md`. (Was Phase 6 in v1; preserved as Phase 6.)

**v2 changes from v1 decide protocol:**

- v1's Phase 0.5 (User-Journey Trace) merges into Phase 0 Constraint Harvest as a sub-step. The user-journey-trace insight (every workflow boundary needs a mechanism) is preserved as a constraint-harvest check, not a separate sub-phase.
- v1's Phase 5 (Independent Verification) carries forward unchanged. Same-family fresh-context, with cross-family as [DESIGN-ONLY] (§8).
- The operator does not invoke `/decision`. The agent recognizes the work as decision-shaped and runs the skill. The operator can also explicitly invoke the slash-command surface for an override.

**Decision → Feature-Loop Immutability.** A feature loop that follows a decision is not free to revisit the decision. If spec-evolve discovers a problem with the decision, the only legal move is to fail back to a new decide invocation that supersedes the previous ADR. spec-evolve cannot patch around a flawed decision — that routes around the verification.

---

## 7. Independent Verification [PARTIAL]

**What is implemented (v1, carries forward).** A fresh same-family Claude session is given the decision question, the constraint envelope, ARCHITECTURE.md, and relevant ADRs. The fresh session re-runs Phases 1-3 independently. The two sessions' conclusions are compared:

- **Same approach chosen** → high confidence, proceed.
- **Different approach, same constraints identified** → trade-offs differ; surface to human.
- **Different constraints identified** → merge constraint sets and re-evaluate.

**What v2 adds.** Independent verification anchors the decide-skill Phase 5 *and* the feature-loop review step (§5). Both are fresh-context same-family. The decide-skill Phase 5 runs only for firm decisions; the feature-loop review step runs every loop iteration. v2's claim is that one fresh-context anchor per work unit (one decision, one feature loop) is the load-bearing element, not one anchor per phase.

**What is not implemented.** Cross-family adversarial verification (§8). Phase 5 in the running system uses fresh-same-family verification only.

**Synthesis paradox.** Even the implemented verification has the property that the fresh session is the same model family as the original. Same-family models share roughly 60% of their structural error patterns (Kim et al., ICML 2025; §17). Independent verification by a fresh same-family session catches role contamination from authorship; it does not catch model-inherent blind spots that both sessions share. This is accepted as a cost of operating with what is currently practical to ship.

**No mechanical gate (carried from v1).** Phase 5 is not enforced by any hook or commit gate. The discipline of running it for firm decisions is convention, not enforcement. See §14, incident #1 — the firm ADRs in this repo were committed before `/decision` had been used on live work.

For provisional decisions, Phase 5 is skipped — provisional decisions are expected to be revisited as the project learns more.

---

## 8. Cross-Family Adversarial Verification [DESIGN-ONLY]

A stronger Phase 5 would use models from different families (e.g., Claude + GPT + Gemini) with raw inputs preserved verbatim, static instruction templates, and convergent-divergence detection at synthesis. **None of this is in the running system.** What runs is fresh-same-family verification only (§7).

Two structural commitments for any future implementation (preserved from v1):

1. **Raw inputs are not authored by Claude.** The input documents (constraint envelope, problem statement, ARCHITECTURE.md excerpts) given to the cross-family models must be sourced from the substrate as-is, not paraphrased or restructured by the originating Claude session. Paraphrasing reintroduces correlated framing.
2. **Independent analysis precedes any view of Claude's work.** The cross-family models must produce their own analysis before being shown what Claude concluded. Comparison happens only at synthesis, not during reasoning.

**Bounded promise.** Even cross-family verification's promise of independence is bounded by Kim et al.'s correlated-errors finding: ~60% error agreement across 350+ LLMs on one leaderboard, driven by shared architectures and providers. Any future cross-family check is motivated by this bound but cannot escape it entirely.

---

## 9. Substrate Redesign [OPEN-QUESTION]

The substrate — ADRs, ARCHITECTURE.md, lessons.md, validator — has a credibility crisis that v2 names but does not solve.

**Observed failure modes.**

1. **Firm-by-fiat firmness.** Most firm ADRs in the repo were committed in the initial commit, before `/decision` had ever run on live work (see §14 incident #1). The firmness label confers authority that was not earned through the protocol.
2. **Cited but not consulted.** Phase 1 / spec-evolve outputs cite ADRs in intent.md by id, but the agent producing the work doesn't necessarily let the constraint shape the work — the citation can be a name-drop that satisfies the discipline's surface form without absorbing the discipline's substance.
3. **Validator green ≠ semantically sound.** The mechanical validator checks reference integrity (forward / backward / staleness). It does not detect semantic contradiction between two ADRs that pass all reference checks. The green light misleads.
4. **Substrate as cognitive load.** ARCHITECTURE.md exists as a derived view of ADRs, but the *purpose* it was created for — making invariants present and consultable during work — does not reliably fire. Invariants that should fire are missed. Either the substrate is not being read at the moments where it would matter, or it is being read but not absorbed, or what's in it isn't the right thing to be reading.

**Four candidate redesign directions, none committed:**

- **A. Executable invariants.** Each firm ADR ships with a checkable assertion (file shape, import constraint, behavioral property). The validator runs assertions mechanically on every change. "Cited but not consulted" becomes "fails the check." ARCHITECTURE.md becomes a derived report of which invariants hold today.
- **B. Per-feature spec absorbs decision context.** When a feature-loop starts, the agent extracts the relevant ADR constraints into the feature spec inline (rather than citing them by id). The feature spec carries the constraint surface; the ADR is the corpus-level summary.
- **C. Consultation hook.** When intent.md cites ADR X, a hook requires the implementation to demonstrably honor X — grep evidence, named test, or other mechanical signal. Discipline becomes mechanical enforcement.
- **D. Conversation-derived ADR drafting.** The operator never authors an ADR. When the conversation makes an architectural commitment, the agent drafts the ADR + invariant + check, the operator approves the diff. ADRs become byproduct of conversation, not input to it.

**Precondition: substrate audit.** Before any of A-D ships, the existing firm ADRs must be walked through Phase 5 retroactively, or demoted to provisional with recorded rationale (this was scheduled in v1 as "Session N+1" and remains outstanding). v2 promotes this from a scheduled item to a precondition for the redesign. A redesign that ships on top of unaudited firm ADRs inherits their credibility crisis.

This section is the most important [OPEN-QUESTION] in v2 and is named explicitly so it does not quietly disappear.

---

## 10. Mechanical Enforcement [IMPLEMENTED + V2 ADDITIONS PLANNED]

The system uses Claude Code's native primitives to enforce discipline at the layers where mechanical enforcement is feasible. The enforcement is friction-plus-walls: hard mechanical blocks where possible, friction where mechanical blocks would be too brittle.

**Three current hooks (carry forward from v1, unchanged):**

- **Reversibility guard** (PreToolUse on `Bash|Edit|Write`): blocks `rm -rf` / `rm -fr`, `git push --force` / `-f` (allows `--force-with-lease`), `git reset --hard`, `git clean -fd`, `DROP TABLE`, `DROP DATABASE`. Blocks Write to `.env*` and lock files. Enforces ADR append-only.
- **Role guard** (PreToolUse on `Edit|Write|MultiEdit|NotebookEdit`): per-role allowlist when `AGENT_ROLE` is set; operator-envelope (`.claude/active-envelope.yaml`) when unset. Envelope is regex-driven, fail-closed on malformed YAML. EXPAND_ENVELOPE=1 escape hatch logs to `.claude/envelope-grants.log`.
- **Reality check** (PostToolUse on `Edit|Write`): runs `ruff format` and `ruff check --fix` on Python files. Sub-second runtime budget. Skipped silently if ruff missing.

**v2 hook additions [PLANNED, named not built]:**

The operator has stated that more hooks are wanted, with two qualifiers: (a) less invasive — the EXPAND_ENVELOPE escape hatch keeps firing because envelopes are mis-shaped, which is a tell that the envelope concept itself needs a rethink (probably as part of the substrate redesign §9); (b) actually useful — each new hook must catch something that materially changes outcomes, not produce theatre.

Three v2 hook additions named here:

- **Consultation check.** When the current feature spec cites an ADR, and the implementation diff doesn't show evidence of the ADR's constraint being honored (grep/named-test/other mechanical signal — exact form depends on substrate redesign §9 outcome), the hook surfaces a warning. PostToolUse on commit boundaries.
- **Spec drift detector.** When code is changed without a corresponding spec update (within the same loop iteration), the hook surfaces a warning. The intent is to catch the case where implementation discoveries quietly diverge from the persisted spec — the case where Fowler-style code→spec sync is needed.
- **Session-boundary reminder.** Tracks conversation length, topic shift signal, and time since last session close. Prompts the operator to consider closing the session when the cost-of-staying signal exceeds the cost-of-resetting signal. The operator manages session boundaries; the agent prompts them.

None of the three v2 hooks are designed in detail. Each is named here so v2 readers know what is intended and so substrate redesign work can be sequenced with the consultation-check hook in mind.

**Mechanical validator (carries from v1).** `scripts/validate_architecture.py` checks ARCHITECTURE.md ↔ ADR consistency. Caveat: not auto-enforced on ADR changes; must be run manually. Auto-enforcement on ADR file writes is a known operational gap (§14, incident #2).

**Phase gates by git commits (rewritten for v2 loop).** The v1 four-fresh-session phase gates collapse in v2. Loop-step commits (spec / tests / code / review) still happen in order — the agent must commit Step N before starting Step N+1 — but the gates are intra-loop, not inter-session. The git history remains the audit trail.

**No master orchestrator (carries from v1).** A "use cairn" wrapper skill that drives multiple feature loops sequentially is deliberately not part of the system. The operator remains the orchestrator across loops.

---

## 11. Integration Sweeps [IMPLEMENTED]

Two feature loops that each pass review independently can produce a system that's broken in ways neither could see. A schema change in feature A breaks queries in feature B; a tool signature change in feature C orphans a client added in feature D. Cross-feature failures are silent by definition.

Integration sweeps run every N feature loops (cadence configurable in `.claude/sweep.yaml`). The sweep:

1. Loads invariants from `docs/ARCHITECTURE.md`.
2. Enumerates possible cross-feature failure modes specific to this codebase before checking anything.
3. Verifies each invariant against the current codebase with file:line evidence.
4. Runs cross-module checks (imports, lint, types).
5. Produces a pass/fail summary.

If a sweep finds failures, new feature loops are created to fix them through the normal loop. The system does not retroactively edit completed loops.

**v2 note.** Integration sweeps are downstream of the substrate redesign (§9). If the substrate moves to executable invariants (candidate A), much of the sweep's invariant-verification logic becomes the same code path as the per-loop review step — the sweep then becomes a corpus-level run of the per-loop check rather than a separate ceremony. If the substrate stays as-is, sweeps remain the principal cross-feature defense.

---

## 12. Operator UX as Design Constraint [V2-PROPOSAL]

This section is new in v2 and elevates two prior themes (humans-must-remain-operable from v1 §16; daily-usability from §1) to a first-class design constraint.

**The constraint.** Cairn must serve daily work. A methodology its primary user prefers not to use cannot reach the long-horizon coherence wins it claims, because the system never gets enough use to demonstrate the wins. Daily-usability is not aesthetic preference; it is a precondition for the system's value to manifest.

**Operationalized:**

- **Operator authoring load is a metric.** If the operator is authoring intent.md, plan-docs, ADR drafts, or dispatch invocations as routine pre-work, the agent layer is failing. Authoring belongs in the agent.
- **Conversation continuity is the default.** Fresh-session boundaries are exceptional events (verification step; major topic shift) prompted by the agent, not the per-feature default.
- **Friction must earn its weight.** Each piece of operator-facing ceremony (slash command, file authoring, manual gate) must catch failure modes the conversation alone would miss. Ceremony that doesn't earn its weight gets dropped, even if it's "correct in principle."
- **Humans-must-remain-operable (preserved from v1).** The codebase and substrate must remain operable by humans even if AI services are gone. The substrate (ADRs, ARCHITECTURE.md, lessons.md) is human-readable; v2 does not regress this. The codebase generated by AI may not be — this remains an unaddressed constraint (§16).

**Why this is a constraint, not a wish.** v2 was triggered by the operator-authored observation: "I prefer not to use cairn nowadays." That data point is more important than any individual mechanism. v2's redesign is downstream of taking that data point seriously.

---

## 13. Known Failure Modes

**Authorship contamination at the verification step** [DEFENSE-IMPLEMENTED]. Same-session self-review fails to catch errors the same agent introduced. Defense: fresh-context review subagent at loop close (§5). Carries forward from v1, narrowed to the verification step.

**Authorship contamination during construction** [DEFENSE-RETRACTED v2]. v1 claimed the per-phase fresh-session boundary defended this. v2 retracts the claim because the empirical evidence (Song et al.) is about review specifically, and because the cost of per-phase fresh sessions exceeded the value in dogfooding. v2 does not currently defend this failure mode — the bet is that conversation continuity during construction does not produce errors that fresh-context review at loop close fails to catch. This is a v2 hypothesis under test.

**Interpretation drift** [DEFENSE-PARTIAL]. An AI agent reading a natural-language spec may hallucinate a plausible resolution to ambiguity rather than flag the ambiguity. Defense: explicit decisions-deferred sections in the spec, plus independent enumeration of additional ambiguities by the review subagent. Catches ambiguities either party can enumerate. Does not catch ambiguities both miss because they share metacognitive blind spots.

**Ceremony fatigue** [ACKNOWLEDGED, downgraded by v2]. A tired operator skips handoff, merges phases, or skips triage. v1 marked this acknowledged. v2 reduces ceremony surface by collapsing per-phase boundaries and shifting authoring to the agent, which materially reduces what there is to skip. Defense moved from acknowledged-only to defense-by-reduction.

**Routing mistakes** [DEFENSE-PARTIAL → upgraded by v2]. v1 self-classification was friction not a wall. v2 makes routing agent-recognized and surfaces the classification in the conversation; operator overrides confirm or correct. Friction-plus-wall pattern moves to the agent layer.

**Cross-feature integration failures** [DEFENSE-IMPLEMENTED]. Integration sweeps with cadence tracking (§11). Defense is empirical, not preventative.

**ADR corpus semantic drift** [DEFENSE-PARTIAL]. The mechanical validator catches reference and staleness drift. It does not catch semantic drift. v2 substrate redesign (§9) is the path to a stronger defense; until then, the defense remains discipline.

**Hook bypass** [ACKNOWLEDGED]. Hooks are friction-plus-walls. The walls are real for the cases they cover. A determined or careless agent could work around the friction layer; the wall layer holds. Treat hooks as speed bumps in the right place, not as security boundaries.

**The review death spiral** [DEFENSE-IMPLEMENTED]. A loop iteration fails review, the agent rewrites the implementation to make review pass, the new implementation passes review but is fundamentally wrong because the spec was also wrong. Discipline: review-fail-for-implementation-reasons escalates to operator. Patching to force review pass is forbidden. This is v1's Phase 4 death spiral defense, narrowed and renamed for the loop.

**Tests as AI-generated verification** [DEFENSE-PLANNED]. The test step produces tests, and the tests are AI-generated. The verification depends on the test agent's ability to think of cases — exactly the surface where AI's blind spots and the implementation agent's blind spots can coincide. Property-based testing (§15) addresses this structurally and is promoted from "planned" in v1 to a first-class element of the v2 spec-evolve step.

**Ceremony exceeds value on day-to-day work** [DEFENSE-PROPOSED v2]. v2's named failure mode. Defense: the v2 redesign itself — agent-discipline, conversation continuity, agent-recognized routing, per-loop fresh-context review instead of per-phase. The defense is the system as proposed; v2's success criterion is whether the operator returns to daily use of cairn after the redesign ships. This is the empirical test v2 stakes itself on.

**Substrate as theatre** [DEFENSE-OPEN-QUESTION v2]. v2's other named failure mode (§9). Defense: substrate redesign, choice among four candidate directions. Until that work happens, the defense is named-but-absent.

---

## 14. Known Substrate Incidents

This section names four real incidents in the running implementation, carried forward from v1 with minor updates.

**Incident 1 — Firm ADRs committed without Phase 5 Independent Verification.** ADRs 001-007 were all committed in the initial commit (`e68840e`, 2026-04-08), before `/decision` had been used on live work. Four are declared `firmness: firm`. Phase 5 has no evidence of having run on them. **v2 escalates this from "scheduled" to "precondition for substrate redesign" (§9).** No A/B/C/D substrate direction can ship on top of unaudited firm ADRs.

**Incident 2 — context-tiers-integration missing from `docs/adr/index.md`.** A 451-line proposed ADR exists as a file but is not in the index. The mechanical validator would catch this if extended with an index-coverage check, and would catch it sooner if it ran automatically on ADR file writes. Still scheduled, still outstanding.

**Incident 3 — Subagent escape hatch removed.** Earlier `DEVELOPMENT-SYSTEM.md` allowed subagent calls within a single session as alternatives to separate sessions for slices under ~50K loaded tokens. v1 deleted this and committed to fresh sessions for all phase boundaries. v2 partially reverses: subagents are the right tool for the verification step inside a feature loop, with a hard return-cap. v2's claim is that the feature-loop review subagent IS the fresh-context boundary, and four-phase-per-feature fresh sessions were over-application. Subagents remain the wrong tool when their returns are unbounded. The bounded-return discipline is the v2 commitment.

**Incident 4 — Modification slices feature without mechanical defense.** v1 supported modification slices with a discipline-only public-interfaces-only rule. **v2 dissolves this incident by going mode-agnostic (§1).** The discipline that public-interfaces-only was meant to enforce — not smuggling implementation knowledge into the spec step — is now a soft heuristic not a phase rule. The mechanical-defense gap goes away because the rule no longer exists in the form that needed mechanical defense.

---

## 15. Planned Additions

### Property-Based Testing as a First-Class Spec Element [PROMOTED in v2]

v1 marked PBT as a planned addition at the Phase 1 → Phase 2 boundary. v2 promotes PBT to a first-class element of the spec-evolve step.

The plan:

- During spec-evolve, the agent drafts properties expressing invariants about the feature's behavior. Example shapes: idempotence (`f(f(x)) == f(x)`), round-trip consistency (`decode(encode(x)) == x`), invariant preservation, oracle equivalence, authorization invariants.
- Properties become part of the feature spec (`intent.md`) as a structured constraint surface.
- The tests step translates each property into a property-based test using a framework like Hypothesis (Python). The translation is mechanical; the framework generates test cases automatically.
- The code step must produce code that satisfies all property tests in addition to example-based tests.
- The review step runs the full property suite. Property failures become permanent test fixtures with their shrunk minimal counterexamples.

The key property: **the property is human-or-agent-authored at the spec level, the test cases are mechanically generated by the framework, and the verification is independent of any agent's case-thinking**. This addresses the structural concern that AI-generated tests have correlated blind spots with AI-generated implementations.

### Hook Additions [PLANNED]

Three new hooks (§10): consultation check, spec drift detector, session-boundary reminder. Each is named, not yet designed. Sequence consultation-check after the substrate redesign (§9) is decided.

### Substrate Redesign [OPEN-QUESTION]

Four candidate directions captured in §9. v2 schedules: (1) substrate audit (Incident 1) as precondition; (2) selection among A/B/C/D; (3) implementation as a sequence of feature loops.

---

## 16. Known Unaddressed Constraints

### Humans Must Remain Operable Without AI [DESIGN-ONLY]

The codebase and substrate must remain operable by humans even if AI services are gone or if the developer has to work without AI tooling for any reason. This is an active constraint to fight for, not a soft preference. The whole field of AI-assisted development currently ignores this — every existing tool optimizes for delegation, none preserves human operability as a design goal.

The substrate (ADRs, ARCHITECTURE.md, hand-maintained lessons file) is human-readable, which is the precondition for this constraint. But the *codebase* the AI generates may not be — it may be optimized for AI consumption, may use patterns no human on the team would have chosen, may accumulate complexity faster than any human can keep up with by reading.

There is currently no mechanism in this system to actively defend human operability of the generated code over time. This is named here as a known unaddressed constraint so that future work can attempt to address it. Possible directions, none yet committed:

- Per-feature human-readable summaries that capture what changed and why in a format a developer with no AI could read and act on.
- Mandatory architectural simplicity constraints (file size, function complexity, dependency depth) enforced by hooks.
- Periodic "AI off" sessions where the operator attempts to navigate and modify the codebase without AI assistance, surfacing places where comprehension has degraded.

### Operator-Strategic UX Retention [DESIGN-ONLY, V2 NEW]

v2's redesign is staked on the claim that shifting authoring load to the agent layer recovers the operator-strategic UX. There is currently no mechanism to verify that this shift sticks over time. As the project grows, agent-layer authoring may itself accumulate complexity that surfaces back to the operator (in approval diffs, in conversation length, in the cost of correcting agent classifications). v2 names this risk and does not yet defend it. Candidate directions: agent-layer complexity budgets; periodic operator-friction audits.

### Semantic ADR Drift [DESIGN-ONLY, OVERLAPS §9]

The mechanical validator does not catch semantic drift between ADRs. The integration sweeps re-read recent ADRs and flag suspected conflicts, but this is hopeful judgment, not mechanism. v2 substrate redesign (§9) is the path to a structural defense.

---

## 17. Empirical Support and Limits

This system has partial empirical support and a known unfalsifiable core. Three controlled findings are directly relevant:

1. **Song et al. (2026)¹** measured a 4.0 F1-point improvement from cross-context review (conducted in a fresh session with no access to production conversation history) over same-session self-review on injected-error detection across 30 artifacts and 150 errors. The control condition — reviewing twice in the same session — did not beat reviewing once, ruling out repetition as the mechanism. **This is the empirical anchor for v2's fresh-context review at loop close.** v2 does not extend this finding to per-phase fresh sessions; v1 did, and v2 retracts the extension.
2. **Tsui et al. (2025)²** measured a 64.5% average self-correction blind-spot rate across 14 open-source non-reasoning models, directly supporting the claim that within-session self-review is unreliable. A minimal "Wait" prompt reduced blind spots by 89.3%, suggesting the capability exists but requires triggering — supporting v2's external-review-checkpoint design.
3. **Kim et al. (ICML 2025)³** documented substantial correlated errors across 350+ LLMs, with models agreeing roughly 60% of the time when both err on one leaderboard, driven by shared architectures and providers. This finding **bounds** how much fresh same-family sessions can catch and is why any future cross-family verification (§8, [DESIGN-ONLY]) is motivated in the first place.

Supporting evidence: **Panickssery et al. (NeurIPS 2024)⁴** established a causal link between self-recognition and self-preference in LLM evaluators via finetuning experiments, directly supporting the role-separation motivation for evaluation. **Zahn et al. (2026)⁵** provides theoretical grounds for why context compaction is structurally lossy — parametric memory suffers interference proportional to semantic density — which is why v2 still uses committed artifacts at loop boundaries rather than compacted summaries for cross-loop persistence.

None of these findings resolves the central unfalsifiable claim. There is no current experiment that would distinguish "review-step contamination was a real problem the fresh-context check prevented" from "the fresh-context check did nothing but happened to coincide with higher-quality output because the operator had more time to think." This is a methodology-research limitation, not a system flaw.

The system operates under explicit **calibration gap**: its discipline is more rigorous than the evidence justifies, as a deliberate trade-off for safety-critical work. v2 narrows the calibration gap relative to v1 by retracting claims (per-phase fresh sessions) that the evidence did not support and tightening claims (review-step fresh-context) that the evidence does support.

**References.**

1. Song et al., "Cross-Context Review: Improving LLM Output Quality by Separating Production and Review Sessions," 2026. arXiv:2603.12123.
2. Tsui et al., "Self-Correction Bench: Uncovering and Addressing the Self-Correction Blind Spot in LLMs," 2025. arXiv:2507.02778.
3. Kim et al., "Correlated Errors in Large Language Models," ICML 2025. arXiv:2506.07962.
4. Panickssery et al., "LLM Evaluators Recognize and Favor Their Own Generations," NeurIPS 2024.
5. Zahn et al. (cited for the theoretical compaction-loss argument), 2026. arXiv:2603.17781 (possibly related).

---

## 18. Open Questions

These are questions v2 has not answered. Each is a place where further work could move the system forward.

- **Substrate redesign selection.** Among A (executable invariants), B (per-feature spec absorption), C (consultation hook), D (conversation-derived drafting), which earns the implementation cost? §9 is the main [OPEN-QUESTION] of v2.
- **Loop concretness.** §5 names the loop steps and commit cadence but not the exact agent surface (which skill, which subagent dispatch, how the spec-evolve step decides whether to update intent.md or trigger a decide-skill escalation). This needs implementation-level concretness in the next planning cycle.
- **The construction-continuity hypothesis.** v2 claims conversation continuity during construction does not produce errors that loop-close review fails to catch. This is a hypothesis under test. What empirical signal would falsify it?
- **Routing wall strength.** v2 makes routing agent-recognized but does not specify the classifier's contract or escape behavior. Is the agent's classification authoritative? What if the agent can't classify? The mechanism needs design.
- **Stronger machine-checkable routing.** What would automatic detection look like — feature-loop envelopes touching files referenced in firm ADR consequences?
- **Cross-family synthesis.** What mechanism would actually achieve independent cross-family verification without creating a worse correlated-errors problem at the synthesis layer?
- **Formal verification for the critical 10%.** For the smallest, most safety-critical components, is there a layer where formal verification (TLA+, Lean, refinement types) earns its weight?
- **Personas as loop-step openers.** Would assigning a different persona at each loop step (skeptic-test-writer, builder-implementer, integrator-auditor) reinforce role purity beyond what the loop achieves alone? v1 carried this question; v2 keeps it open.
- **Handoff document quality assessment.** Is there a way to mechanically assess whether a handoff note is good enough to bootstrap the next session?
- **Decision archaeology.** Can the ADR corpus be queried (mechanically or via LLM) for "what decisions led to the current shape of X"? This would change the substrate from a forward-only log into a navigable graph.
- **Distinguishing failure modes in post-mortem.** When something goes wrong, the system has multiple defenses. Can a post-mortem reliably determine *which* defense should have caught the failure? Without that, learning is shallow.

---

## 19. Relationship to Spec-Driven Development

This system is a flavor of spec-driven development. SDD at the abstract level claims: the spec is the load-bearing artifact, code is downstream of it, the discipline is in keeping the spec authoritative. Every concrete SDD implementation makes specific choices about what counts as a spec, how it's authored, how it's enforced, how it evolves.

This system implements SDD with three specific structural commitments:

1. **Specs are not trusted as authored.** ADRs are provisional until they survive the adversarial decide-skill protocol. Even after the protocol, they're subject to mechanical validation and supersession when learning happens. Trust in the substrate is earned by structure, not assumed from authorship.
2. **A single agent in a single session cannot both author and consume the spec faithfully at the verification step.** The fresh-context review subagent at loop close exists because within-session self-review cannot be trusted at the verification moment. v2 narrows v1's stronger claim — that no single agent can author and consume across any phase boundary — to the verification moment specifically, where the empirical evidence supports the claim.
3. **Discipline lives in the agent layer.** Mechanical hooks, agent-invoked skills, fresh-context subagents — the operator stays strategic. v2's daily-usability constraint (§1, §12) is the wedge that drives this commitment. SDD implementations that put the spec-authoring load on the operator either survive only in heavyweight contexts or quietly atrophy in daily use; the agent-layer discipline is v2's bid for SDD that survives day-to-day.

These commitments are what dominant SDD tools hand-wave. Most SDD tools assume the spec is authoritative once written, run their workflows in continuous conversations where the same agent moves through phases without external review, and rely on operator-driven workflow ceremony for the discipline that should be structural enforcement.

---

## 20. Adversarial Review Guidance

This document is intended to stand on its own under adversarial review. v2 has been less battle-tested than v1; reviewers should attend to the v2-specific claims and the open questions explicitly.

When attacking a claim, identify the implementation status tag:

- An attack against an **[IMPLEMENTED]** claim that the implementation does not actually do is a writeup bug. Report it as such.
- An attack against an **[IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE]** claim should target the mechanical-defense gap.
- An attack against a **[PARTIAL]** claim should specify whether it targets the part that is implemented or the part that is not.
- An attack against a **[PLANNED]** or **[V2-PROPOSAL]** claim is a design refinement before the planned thing lands.
- An attack against a **[DESIGN-ONLY]** claim is help with whether to commit to the design at all.
- An attack against an **[OPEN-QUESTION]** claim is help with deciding the question.

### What to Attack

The strongest attacks against v2 will target one of these:

1. **The construction-continuity hypothesis.** v2 retracts v1's per-phase fresh-session claim and asserts that conversation continuity during construction is fine as long as review is fresh. An attack that surfaces a class of error fresh-context review cannot catch — but per-phase fresh sessions could — would damage v2's central proposal.
2. **The agent-recognized routing wall.** v2 promotes routing from friction to wall via agent classification. An attack showing the classifier itself is the failure point — that the agent systematically mis-classifies under realistic conditions — would damage the routing redesign.
3. **The substrate redesign deferral.** v2 names the substrate as an open question. An attack arguing the spec is incoherent without resolving the question — that A/B/C/D are not equivalent and the choice changes everything else — would force the question into the spec-writing cycle rather than the next implementation cycle.
4. **The daily-usability claim.** v2 stakes itself on the operator returning to daily use of cairn after the redesign. An attack arguing the redesign doesn't move the friction needle — that authoring shifts from operator to operator-as-approver but the cognitive load stays similar — would expose a hidden assumption.
5. **Routing self-classification under pressure.** The operator's override pressure under deadline may downgrade decide → feature-loop, or feature-loop → ad-hoc, defeating the agent classification. v1 attack carries forward.
6. **Phase decomposition itself.** v2's loop is four steps (spec / tests / code / review). An attack proposing a cleaner decomposition would be valuable.

### What Not to Waste Effort On

- Arguing the system should be tool-agnostic. v0/v1/v2 is Claude Code-coupled by design.
- Arguing this is over-engineered for simple software. §1 explicitly excludes simple software.
- Arguing the role-reset thesis is unproven. v2 narrows the thesis to the verification step where evidence exists; arguments against the verification-step claim should engage with Song et al.
- Arguing subagents could replace the loop entirely. v2 specifically uses a subagent at the review step; the question is whether per-phase subagents earn their weight, and §14 incident #3 addresses the historical context.
- Arguing compaction is equivalent to committed artifacts. §17 cites Zahn et al.
- Arguing cross-family verification should be in the system as if it ran. It is [DESIGN-ONLY] in §8.

### How to Structure a Review

A review should state which attacks were mounted, which succeeded and why, which failed and why, the strongest single attack, what the system would need to change to address it, and an overall verdict. A review that finds nothing is less useful than a review that finds one decisive hole.

---

## 21. Closing Note

v2 is the response to direct dogfooding evidence that the v1 design did not survive the daily-usability test for its primary user. v2 narrows the empirical claim to where the evidence supports it (review-step fresh context), shifts authoring load from operator to agent, drops the greenfield/modification distinction, names the substrate question as an open question rather than papering over the credibility gap, and elevates daily usability to a first-class scope constraint.

v2 is not finished. Two large pieces — the substrate redesign (§9) and the concrete loop implementation (§5, §18) — are explicitly open. v2 ships as a proposal: the spec-level commitment to the redesign direction, the explicit naming of what is unsolved, and the discipline of the honesty layer carried forward from v1.

The strongest feature of v2, like v1, is not any particular mechanism. It is the honesty about what is implemented, what is partial, what is planned, what is design-only, what is open question, and what has known substrate incidents. Each status is marked so attacks land at the right layer.

Anyone adopting this system is making a conscious bet that the underlying mechanisms are real even though the strongest forms of those claims remain unproven. v2's bet is narrower than v1's: only the verification-step fresh-context claim and the agent-discipline / operator-strategic split. Those are the bets v2 stakes itself on.

---

## Changelog from v1

Major changes:

- **§2 Core thesis rewritten.** v1's per-phase fresh-session claim is retracted. v2 narrows to fresh-context-at-verification + conversation-continuity-during-construction + operator-strategic / agent-discipline.
- **§5 Phase definitions replaced with feature loop.** Four sequential fresh sessions collapse into one continuous-conversation loop with a fresh-context review subagent at close.
- **§4 Routing rewritten.** Operator-driven slash commands → agent-recognized routing; operator override remains.
- **§6 Decision protocol becomes decide skill.** Eight sub-phases lighten to six (Phase 0.5 absorbed into Phase 0). Invocation surface shifts from operator slash command to agent-invoked skill.
- **§9 Substrate marked [OPEN-QUESTION].** Four candidate redesign directions captured. Substrate audit (Incident 1) promoted from scheduled to precondition.
- **§12 Operator UX added as design constraint.** Daily-usability promoted to first-class.
- **§1 Scope: greenfield-first dropped, mode-agnostic adopted.**
- **§13 Failure modes expanded.** "Ceremony exceeds value on day-to-day work" and "Substrate as theatre" added with v2 defenses (the redesign itself; substrate redesign).
- **§14 Incident 4 dissolved** by the mode-agnostic move.
- **§15 PBT promoted** from planned-at-Phase-1→2 to first-class spec element.
- **§17 Empirical support narrowed.** Calibration gap reduced by retracting v1's over-extension of Song et al.

Preserved from v1 substantially unchanged:

- Status legend and adversarial review framing
- §3 What the thesis does not claim (extended)
- §7 Independent verification mechanism (re-anchored)
- §8 Cross-family adversarial verification [DESIGN-ONLY]
- §10 Mechanical enforcement (three current hooks; v2 hook additions named)
- §11 Integration sweeps
- §14 Substrate incidents (1-3 carried forward; 4 dissolved)
- §16 Humans-must-remain-operable
- §17 Empirical references

---

*End of spec v2.*

# Slice-Based Development System (spec v1)

*Personal methodology, Claude Code-coupled, single-developer use. This document is the spec; the implementation lives in `.claude/` in projects that use the system.*

*Revision: spec v1 merges three sources — the v0 honesty-audit spec, an earlier "richer" spec that was never committed to a file, and the implementation reality of `.claude/` in this repo. Earlier versions oversold cross-family verification and the synthesis mechanism; the v0 honesty audit corrected that. This v1 restores valuable conceptual refinements from the earlier spec that the v0 over-corrected away, adds four implementation realities both prior specs missed, and is **deliberately not auto-loaded** into every session — Layer 2 of a three-layer content tiering. See `CLAUDE.md` (Layer 0 pointer) and `.claude/DEVELOPMENT-SYSTEM.md` (Layer 1 operational reference) for the lighter tiers.*

---

## Status Legend

Each section and major claim is tagged with implementation status so attacks land at the right layer:

- **[IMPLEMENTED]** — Working in `.claude/`. Observable in this repo.
- **[IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE]** — Feature exists in the implementation, but no hook or validator mechanically enforces it. Discipline-only.
- **[PARTIAL]** — Partially implemented. The description specifies what is and what isn't.
- **[PLANNED]** — Designed but not yet built. Concrete enough to implement next.
- **[DESIGN-ONLY]** — Described but no implementation plan. Marked here so reviewers know not to attack it as if it ran.
- **[ACKNOWLEDGED]** — Failure mode the system cannot prevent. Discipline only.
- **[DEFENSE-IMPLEMENTED]**, **[DEFENSE-PARTIAL]**, **[DEFENSE-PLANNED]** — Tags applied to known failure modes describing the state of the system's defense, not the failure mode itself.

---

## 1. Scope [IMPLEMENTED]

The system is for **genuinely complex software engineering** — safety-critical systems, long-horizon projects with many interwoven components, domains where integration between components is the hard part, and projects accumulating architectural decisions that are actively maintained. It is for human-led engineering where AI is a powerful collaborator but the human remains responsible for architectural integrity over time.

**It is not for simple software.** For CRUD apps, prototypes, AI wrappers, and internal scripts, the overhead is pure waste. Frontier models with planning modes and auto-compact handle straightforward work effectively without any of this. The system's value comes from preventing failure modes that only manifest in complex, long-horizon work.

**Greenfield-first, with modification slices as a documented extension.** The system was designed for greenfield. Brownfield is a different problem and the system is not designed for it. Modification slices (changing existing behavior in files that already exist) are supported as a documented extension — the rule is "read public interfaces only, not internal implementation logic" — but no hook mechanically enforces this and the defense is discipline-only. See section 5 and section 14 for the implementation status.

---

## 2. Core Thesis [IMPLEMENTED]

Complex AI-assisted development requires phase boundaries with clean context resets between them. The mechanism is **dual and inseparable**.

**Context engineering.** A fresh session loads only the committed artifact of the previous phase, not the accumulated trace of how it was produced. The committed artifact is externally stored and reviewable.

**Role reset.** The session boundary forces a deliberate switch in cognitive role. Within a continuous session, narrative momentum prevents clean role transitions — neither human nor AI can reliably stop being the author and start being the critic without an external interruption. Closing one session and opening another is that interruption.

These two mechanisms are inseparable. Context engineering alone fails because narrative momentum carries authorship bias forward. Role reset alone (reopening the same conversation) fails because the loaded state is still the polluted trace. The session boundary as committed artifact plus handoff document plus new session is the unique mechanism that satisfies both at once.

Beyond context engineering and human reset, the session boundary also achieves **role purity**: each phase has a different cognitive role, and a fresh session prevents the previous role's framing from leaking into the next role's evaluation. Three distinct benefits, one mechanism. Role purity is the most defensible of the three because it does not depend on the contested human-reset claim — even if role-reset turns out to be psychologically inert, role purity remains a structural property of fresh sessions loading only declared inputs.

The role-reset half of the dual mechanism has no direct experimental validation. It is theoretically grounded and directly observed in practice. Adopting this system means betting that the role-reset thesis is load-bearing. That bet is reasonable for safety-critical work where the asymmetric cost of contamination justifies acting on plausible-but-unproven mechanisms. See section 17 for what evidence does and does not exist.

---

## 3. What the Thesis Does Not Claim

**It does not claim fresh context catches model-inherent correlated errors.** Cross-family error agreement is well documented (Kim et al., ICML 2025; see section 17). Two fresh sessions of the same model family will reproduce the same systematic blind spots. The mechanism being defended is role contamination during authorship, not model-inherent bias.

**It does not claim subagents are useless.** Subagents are the right tool for branching paths inside a phase — parallel exploration, scoped lookups, well-defined sub-tasks. They are the wrong tool for linear pipeline boundaries because subagent return summaries pollute the parent's context, defeating isolation. The earlier subagent escape hatch in `DEVELOPMENT-SYSTEM.md` has been deleted (section 14, incident #3).

**It does not claim compaction is bad.** Compaction is useful within a phase. It is inadequate as a phase boundary because it is a lossy self-summary chosen by a degraded model. The committed artifact at the phase boundary is the alternative.

**It does not claim committed artifacts are interpretation-stable.** Natural language is not interpretation-stable. Two readers can read the same document and arrive at different interpretations of ambiguous sections. This is a real failure mode (interpretation drift) distinct from authorship contamination. See section 13.

**It does not claim its discipline is justified by current evidence.** The system's rigor is calibrated to a higher confidence level than the empirical support justifies. This is a deliberate trade-off for safety-critical work, not an oversight. Users should make this trade-off consciously. See section 17 (calibration gap).

---

## 4. Routing: Decision vs. Slice [IMPLEMENTED]

Before starting work, determine whether the work needs a formal decision:

- **Touches invariants, boundaries, data ownership, or module structure** → run `/decision` first. This produces an ADR through the adversarial decision protocol (constraint harvest, user-journey trace, pre-mortem, forced enumeration, stress test, decision record, independent verification, propagation). The ADR updates ARCHITECTURE.md, then a slice implements it.
- **Implementation within existing boundaries** → go straight to `/start-slice`. The invariants and ADRs already define the constraints; the slice fills in detail.

Rule of thumb: if the work could change what downstream slices can assume, it needs `/decision`. If it only fills in detail within an existing assumption, it needs `/start-slice`.

The routing is self-classification under metadata pressure. It is a partial defense, not an enforced one. Stronger machine-checkable routing criteria — automatic detection when a slice envelope touches files mentioned in firm ADR consequences — are on the roadmap but not yet implemented.

### Routing Recovery Rules

When routing is wrong, do not patch around the mistake:

- **Slice started, architectural invariant discovered** → fail the slice, restart with a `/decision` that produces the ADR, then re-enter the slice with the new constraint as input.
- **Slice started on the assumption the envelope is greenfield, modification turns out to be required** → stop, declare the slice as modification, acknowledge the mechanical-defense gap (see section 14, incident #4), proceed with elevated human review.
- **Decision started, work turns out to be trivial implementation** → demote by marking the ADR as provisional and skipping Phase 5 Independent Verification. The constraint harvest and enumeration sub-phases remain valuable even for trivial work.

---

## 5. Phase Definitions [IMPLEMENTED]

A slice is a vertical feature cut that goes through four phases. Each phase has the same structural properties: declared inputs, a committed artifact as output, a fresh session at its start, and a handoff to the next phase. Phase transitions are enforced by **git commits**, not by session state.

**Phase 1 — Intent.** Define what to build without reading source code (greenfield) or by reading only public interfaces (modification — see sub-note below). Output: `intent.md` with envelope (YAML), what/why/boundary, specification detail, and verification criteria. Declare which invariants from ARCHITECTURE.md are touched and which ADRs are relevant.

**Phase 2 — Validation.** Write tests against the intent. The validation agent has not seen how implementation will work. Before writing tests, enumerate ambiguities in the intent and resolve them by reference to ARCHITECTURE.md/ADRs or flag for human resolution. Output: test suite in `tests/` plus brief approach summary in `.claude/current-slice/validation/approach.md`.

**Phase 3 — Implementation.** Write code that passes the tests. The implementing agent has not seen the validation agent's reasoning — only the tests themselves. Treats tests as black-box constraints. Output: code that passes the validation suite. Decisions the intent did not pin down go to `.claude/current-slice/implementation/notes.md`.

**Phase 4 — Integration.** Verify declared invariants against the codebase with citation evidence (grep, file reads). Run full test suite, not just slice tests. Run the architecture validator. Check for regressions in adjacent code. Output: pass/fail verdict on declared invariants, recorded in `.claude/current-slice/integration/sweep-notes.md`.

Each phase boundary is gated by a git commit. The next phase cannot start until the previous phase's artifact is committed.

**Modification slices [IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE].** Slices that change the behavior of files that already exist (rather than creating new modules) are a documented extension. The rule is: read only the public interfaces of files in the envelope (function signatures, class definitions, docstrings). Do not read internal implementation logic. The intent should describe the target behavior, not the delta from current behavior. **No hook enforces this.** Whether the Phase 1 agent actually limits its reads to public interfaces is discipline-dependent. See section 14 (substrate incidents) for context.

---

## 6. Decision Protocol [IMPLEMENTED]

The Decision phase exists because architectural decisions are the most upstream task. Every invariant, every slice, every test, and every line of implementation flows from decisions. A bad decision that feels right produces a confident, well-tested, completely wrong system. The cost of getting a decision wrong is the cost of all downstream work that builds on it.

The protocol has eight sub-phases (Phase 0 through Phase 6, plus Phase 0.5). Sub-phases 0–4 run in a single session by the same agent. Sub-phase 5 (Independent Verification) requires a fresh session. Sub-phase 6 (Propagation) is a post-acceptance follow-up.

**Phase 0 — Constraint Harvest.** Read ARCHITECTURE.md, ADR index, relevant ADRs, lessons file. Produce a list of specific constraints this decision must respect, each with source citation. If constraints conflict with each other, surface the conflict before proceeding.

**Phase 0.5 — User-Journey Trace.** Trace the workflow this decision enables end-to-end. At every session boundary, artifact boundary, and state transition, identify what mechanism moves things forward. Gaps in the journey are gaps in the decision. *(This phase exists because the v0 build shipped without session handoff skills — a gap caught only by walking through the user journey.)*

**Phase 1 — Pre-Mortem.** Imagine the decision failed three months from now. Write at least three failure scenarios: technical, scale, integration.

**Phase 2 — Forced Enumeration.** Enumerate at least three viable approaches with evidence-backed citations (file:line for codebase evidence, ADR-NNN for docs evidence). Memory is where correlated errors hide. Rate each approach against the pre-mortem scenarios.

**Phase 3 — Adversarial Stress Test.** Attack the strongest approach. Disconfirming search (actively look for evidence the approach is wrong), steel-man the opposition (argue the second-best approach as strongly as possible), assumption audit (list every assumption, classify each as verified or believed, determine whether the approach degrades gracefully when assumptions fail).

**Phase 4 — Decision Record.** Write the decision as a draft ADR with proper YAML frontmatter. ADRs default to `firmness: provisional`.

**Phase 5 — Independent Verification (firm decisions only).** See section 7.

**Phase 6 — Propagation.** After the ADR is accepted: run `/refresh-architecture` to update ARCHITECTURE.md; check whether any in-progress slice's intent.md needs updating because new constraints invalidate existing intents; verify that any superseded ADR's frontmatter was updated; record any cross-cutting patterns in `docs/lessons.md`. *(This sub-phase is in the implementation at `.claude/commands/decision.md:121-128` but was missing from the v0 spec.)*

### Decision → Intent Immutability

The Intent phase that follows a Decision is **not free to revisit the decision**. If Intent discovers a problem, the only legal move is to fail back to a new Decision phase producing a new ADR that supersedes the previous one. Intent cannot patch around a flawed decision because that would route around the verification. This is the same principle as the Phase 4 failure escape hatch, applied upstream.

---

## 7. Independent Verification (Phase 5) [PARTIAL]

**What is implemented:** A fresh same-family Claude session is given the decision question, the constraint envelope, ARCHITECTURE.md, and relevant ADRs. The fresh session re-runs Phases 1–3 independently and produces its own conclusions. The two sessions' conclusions are compared:

- **Same approach chosen** → high confidence, proceed.
- **Different approach, same constraints identified** → trade-offs differ; surface to human.
- **Different constraints identified** → merge constraint sets and re-evaluate.

**What is not implemented:** Cross-family adversarial verification (see section 8). Phase 5 in the running system uses fresh-same-family verification only.

**Synthesis paradox.** Even the implemented verification has the property that the fresh session is the same model family as the original. Same-family models share roughly 60% of their structural error patterns (Kim et al., ICML 2025; see section 17). Independent verification by a fresh same-family session catches role contamination from authorship; it does not catch model-inherent blind spots that both sessions share. This is accepted as a cost of operating with what is currently practical to ship. It is a known hole the system carries because no current alternative is better at the price.

**No mechanical gate.** Phase 5 is not enforced by any hook or commit gate. The discipline of running it for firm decisions is convention, not enforcement. See section 14, incident #1 — the firm ADRs in this repo were committed before `/decision` had been used on live work, so Phase 5 has no evidence of having run on them.

For provisional decisions, Phase 5 is skipped — provisional decisions are expected to be revisited as the project learns more.

---

## 8. Cross-Family Adversarial Verification [DESIGN-ONLY]

A stronger Phase 5 would use models from different families (e.g., Claude + GPT + Gemini) with raw inputs preserved verbatim, static instruction templates, and convergent-divergence detection at synthesis. **None of this is in the running system.** What runs is fresh-same-family verification only (section 7).

The earlier spec described two structural commitments for any future implementation:

1. **Raw inputs are not authored by Claude.** The input documents (constraint envelope, problem statement, ARCHITECTURE.md excerpts) given to the cross-family models must be sourced from the substrate as-is, not paraphrased or restructured by the originating Claude session. Paraphrasing reintroduces correlated framing.
2. **Independent analysis precedes any view of Claude's work.** The cross-family models must produce their own analysis before being shown what Claude concluded. Comparison happens only at synthesis, not during reasoning.

Both commitments are noted here so that if cross-family verification is ever built, the design starts from these constraints.

**Bounded promise.** Even cross-family verification's promise of independence is bounded by Kim et al.'s correlated-errors finding: ~60% error agreement across 350+ LLMs on one leaderboard, driven by shared architectures and providers. Any future cross-family check is motivated by this bound but cannot escape it entirely.

---

## 9. Three-Track Routing (3 / 4 / 5 phase) by Consequence Radius [DESIGN-ONLY]

An earlier spec proposed three routing tracks instead of binary Decision/Slice routing:

- **3-phase track** for low-consequence work: Intent → Implementation → Integration (Validation collapsed into Intent).
- **4-phase track** for normal work: the standard Intent → Validation → Implementation → Integration.
- **5-phase track** for high-consequence work: adds a Pre-Decision gate before Intent.

The shape of the routing was "consequence radius" — how far downstream a wrong answer would propagate.

**Status: not implemented.** The running system uses simpler binary routing (Decision vs. Slice). Three-track routing is kept here as a design roadmap because the binary routing is a rough fit for actual project consequence — small bug fixes should not pay full pipeline cost — but the friction of self-classifying into three tracks is unproven and may not justify the complexity. The simpler routing is what ships.

---

## 10. Substrate: ADRs and ARCHITECTURE.md [IMPLEMENTED]

**ARCHITECTURE.md as derived view.** Synthesized from ADRs, not hand-maintained. Every statement traces to a decision; every active firm decision is reflected in the document. A mechanical validator (`scripts/validate_architecture.py`) checks three conditions:

- **Forward (Check A):** every invariant references a valid non-superseded ADR.
- **Backward (Check B):** every accepted firm ADR has at least one invariant.
- **Staleness (Check C):** no invariant references a superseded or deprecated ADR.

The synthesis is creative (AI generation); the validation is mechanical (regex-based Python script). They must not be conflated.

**ADRs as append-only with pragmatic exceptions.** Append-only for substantive content. To change a decision, write a superseding ADR. Frontmatter updates (status, superseded-by, firmness) and editorial fixes (typos, formatting) are allowed in-place. The reversibility hook checks only the first line of the `old_string` to prevent multiline-bypass attacks where a body edit is disguised as a frontmatter change. Editorial fixes can be authorized via `ADR_EDITORIAL_FIX=1` and are logged.

**ADR index.** A hand-maintained table of all ADRs with status, firmness, topic, and date. Human-readable entry point into the decision corpus. *(Caveat: the validator currently does NOT check that every ADR file is in the index — see section 14, incident #2.)*

**Lessons file.** Hand-maintained, small. Short observations of cross-cutting patterns discovered during development that aren't tied to a specific decision. Feeds into the Constraint Harvest sub-phase of future decisions.

**Slice directory.** When a slice is active, `.claude/current-slice/` holds slice metadata, intent document, validation tests/approach, implementation notes, and integration sweep notes. The directory is part of git history and is the audit trail.

---

## 11. Mechanical Enforcement [IMPLEMENTED]

The system uses Claude Code's native primitives to enforce discipline at the layers where mechanical enforcement is feasible. The enforcement is friction-plus-walls: hard mechanical blocks where possible, friction where mechanical blocks would be too brittle.

**Phase gates by git commits.** Phase 2 cannot start until Phase 1's artifact (`intent.md`) is committed. Phase 3 cannot start until Phase 2's artifact (validation tests) is committed. Phase 4 cannot start until Phase 3's artifact (implementation source files) is committed. Git commits are the only state that survives session crashes, machine restarts, and developer fatigue. The `/start-slice` skill checks for these artifacts in git history before advancing.

**Hooks at the tool layer (wired in `.claude/settings.json`).**

- **Reversibility guard** (PreToolUse on `Bash|Edit|Write`): blocks `rm -rf`/`rm -fr`, `git push --force` and `-f` (allows `--force-with-lease`), `git reset --hard`, `git clean -fd`, `DROP TABLE`, `DROP DATABASE`. Blocks Write to `.env*` files and to lock files (`uv.lock`, `package-lock.json`, `poetry.lock`). Enforces ADR append-only on `docs/adr/*` files: blocks Write to existing ADR files; blocks Edit to ADR bodies but allows first-line frontmatter changes (`status:`, `superseded-by:`, `superseded_by:`, `firmness:`).
- **Scope guard** (PreToolUse on `Edit|Write`): reads the current slice's `intent.md` envelope and blocks edits to files outside the declared scope. Administrative paths are always allowed (`.claude/current-slice/*`, `.claude/handoff.md`, `.claude/sweep.yaml`, `docs/adr/*`, `docs/ARCHITECTURE.md`, `docs/lessons.md`). Test files for source files in the envelope are auto-included. **Goes dormant when slice status is `complete` or `failed`.** Provides an `EXPAND_ENVELOPE=1` escape hatch that logs the expansion to `.claude/current-slice/envelope-expansions.log` and permits the edit.
- **Reality check** (PostToolUse on `Edit|Write`): runs `ruff format` and `ruff check --fix` on Python files only. Skipped silently if `ruff` is not on PATH. Total runtime budgeted under 1 second.

**Mechanical validator.** `scripts/validate_architecture.py` checks ARCHITECTURE.md ↔ ADR consistency (Checks A, B, C from section 10). **Caveat: the validator is not auto-enforced on ADR changes.** It must be run manually, typically by `/refresh-architecture` or by the developer at integration time. Auto-enforcement on ADR file writes is a known operational gap (see section 14, incident #2).

**Session handoff/catchup protocol.** `/handoff` packages context at session end and writes a handoff note. `/catchup` reads the handoff note at session start and loads only phase-appropriate context, with explicit reporting of what was deliberately excluded. The Excluded list makes context isolation visible to both human and AI.

**No master orchestrator.** A "use slice-system" wrapper skill is deliberately not part of the system. The slice system's whole point is that phases are not in one continuous narrative — they are separated by session boundaries that no single agent crosses. A master orchestrator would defeat the purpose. The developer remains the orchestrator across phases.

---

## 12. Integration Sweeps [IMPLEMENTED]

Two slices that each pass Phase 4 independently can produce a system that's broken in ways neither slice could see. A schema change in slice A breaks queries in slice B; a tool signature change in slice C orphans a client added in slice D. Cross-slice failures are silent by definition.

Integration sweeps run every N slices (cadence configurable in `.claude/sweep.yaml`, starting at every slice during calibration and loosening once data shows the right cadence). The sweep:

1. Loads invariants from `docs/ARCHITECTURE.md`.
2. Enumerates possible cross-slice failure modes specific to this codebase before checking anything.
3. Verifies each invariant against the current codebase with file:line evidence.
4. Runs cross-module checks (imports, lint, types).
5. Produces a pass/fail summary.

If a sweep finds failures, new slices are created to fix them through the normal 4-phase pipeline. The system does not retroactively edit completed slices.

---

## 13. Known Failure Modes

**Authorship contamination** [DEFENSE-IMPLEMENTED]. The primary failure mode the system addresses. Defense: phase boundaries with fresh sessions. Structural and the central claim of the system.

**Interpretation drift** [DEFENSE-PARTIAL]. An AI validator reading a natural-language intent document may hallucinate a plausible resolution to ambiguity rather than flag the ambiguity. Defense: explicit decisions-deferred sections in intent, plus independent enumeration of additional ambiguities by the validator. Catches ambiguities either party can enumerate. Does not catch ambiguities both miss because they share metacognitive blind spots.

**Ceremony fatigue** [ACKNOWLEDGED]. A tired developer skips handoff, merges phases, or skips triage. The system cannot prevent this. Recovery: when a step is skipped, acknowledge the slice was completed without full discipline, mark it as such, and use the next slice as a reset.

**Routing mistakes** [DEFENSE-PARTIAL]. Documented in section 4. Self-classification can downgrade work to lighter tracks under deadline pressure. Recovery paths exist (section 4, routing recovery rules) but rely on discovering the misclassification.

**Cross-slice integration failures** [DEFENSE-IMPLEMENTED]. Integration sweeps with cadence tracking. Defense is empirical, not preventative.

**ADR corpus semantic drift** [DEFENSE-PARTIAL]. The mechanical validator catches reference and staleness drift. It does not catch semantic drift — two ADRs that are technically consistent but contradict in meaning. Integration sweeps re-read recent ADRs and flag suspected conflicts, but this is judgment, not mechanism. See section 16 (Known Unaddressed Constraints).

**Hook bypass** [ACKNOWLEDGED]. Hooks are friction-plus-walls. The walls are real for the cases they cover (scope, ADR append-only, destructive commands). A determined or careless agent could work around the friction layer (`shutil.rmtree`, `find -delete`, `truncate -s 0`, replacing test assertions with `pass`); the wall layer holds. Treat hooks as speed bumps in the right place, not as security boundaries.

**The Phase 4 death spiral** [DEFENSE-IMPLEMENTED]. A slice fails Phase 4, the developer rewrites the implementation to make tests pass, the new implementation passes Phase 4 but is fundamentally wrong because the tests were also wrong. Discipline: when Phase 4 fails for implementation reasons, the slice is marked failed, archived to `.claude/completed-slices/<ID>-failed/`, and a new slice starts with the failure as input context. Patching to force Phase 4 to pass is forbidden.

**Tests as AI-generated verification** [DEFENSE-PLANNED]. The validation phase produces tests, and the tests are AI-generated. The verification depends on the validation agent's ability to think of cases — exactly the surface where AI's blind spots and the implementation agent's blind spots can coincide. The planned addition (section 15, PBT at the Phase 1→2 boundary) addresses this structurally.

---

## 14. Known Substrate Incidents

This section names four real incidents in the running implementation. Each is tagged honestly so attacks land at the right layer.

**Incident 1 — Firm ADRs committed without Phase 5 Independent Verification.** ADRs 001-007 were all committed in the initial commit (`e68840e`, 2026-04-08), before `/decision` had been used on live work. Four are declared `firmness: firm` (001, 003, 004, 005). Phase 5 has no evidence of having run on them. This is a known substrate gap. The honest position is that these firm ADRs are in the substrate by initial-commit fiat, not by adversarial verification. **Substrate audit is scheduled (Session N+1)** to walk each firm ADR through Phase 5 retroactively or to demote it to provisional with a recorded rationale.

**Incident 2 — ADR-008 missing from `docs/adr/index.md`.** A 451-line proposed ADR (`008-universal-rag-mcp-server-architecture.md`) exists as a file but is not in the index. The mechanical validator would catch this if it were extended with an index-coverage check, and would catch it sooner if it ran automatically on ADR file writes. It does not. The validator runs only when invoked manually or via `/refresh-architecture`. **Auto-enforcement is scheduled (Session N+2).**

**Incident 3 — Subagent escape hatch removed.** Earlier `DEVELOPMENT-SYSTEM.md` (lines 88–90, pre-merge) described "Session vs. Subagent Mode" and said: *"For slices where all phases fit comfortably in one session (loaded context under ~50K tokens), subagent calls within a single session are a valid alternative to separate sessions."* This contradicted the central thesis of the system (the session boundary is load-bearing) and had zero calibration data — it was speculative permissiveness, not measured discipline. It has been deleted in the v1 merge. **The system officially commits to fresh sessions for all phase boundaries.** Subagents remain valid for branching paths inside a phase (parallel exploration, scoped lookups), but not as replacements for the session boundary on the linear pipeline.

**Incident 4 — Modification slices feature without mechanical defense.** The implementation supports modification slices (changing existing behavior in already-existing files) with the rule "read public interfaces only, not internal implementation logic" — see `.claude/DEVELOPMENT-SYSTEM.md` and `start-slice.md` Step 5. **No hook enforces this.** Whether the Phase 1 agent actually limits its reads to public interfaces is discipline-dependent. Tagged [IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE] throughout the spec. A future hook addition that intercepts Read calls during Phase 1 and reports lines crossed into implementation logic is possible but not scheduled — the friction-vs-noise tradeoff is unproven.

---

## 15. Planned Additions

### Property-Based Testing at the Phase 1 → Phase 2 Boundary [PLANNED]

The plan:

- During Phase 1 (Intent), the human author writes properties expressing invariants about the slice's behavior. Example shapes: idempotence (`f(f(x)) == f(x)`), round-trip consistency (`decode(encode(x)) == x`), invariant preservation (sum-of-balances unchanged after any transaction sequence), oracle equivalence (fast implementation matches simple implementation), authorization invariants (no sequence of API calls can produce a state where an unauthorized user has elevated access).
- Properties become part of `intent.md` as a structured constraint surface. They cross the Phase 1 → Phase 2 boundary alongside the rest of the intent.
- Phase 2 (Validation) translates each property into a property-based test using a framework like Hypothesis (Python) or proptest (Rust). The translation is mechanical; the framework generates test cases automatically from the input description.
- Phase 3 (Implementation) must produce code that satisfies all property tests in addition to example-based tests.
- Phase 4 (Integration) runs the full property suite as part of the integration check. Property failures become permanent test fixtures with their shrunk minimal counterexamples.

The key property of this addition: **the property is human-authored, the test cases are mechanically generated by the framework, and the verification is independent of any AI's case-thinking**. This addresses the structural concern that AI-generated tests have correlated blind spots with AI-generated implementations.

PBT does not replace example-based tests; it adds a verification layer that catches the structural bugs example-based testing cannot reach. The hexagonal architecture of typical projects using this system makes the functional core the natural place for properties — pure functions are exactly where PBT is cheapest to use.

This is planned, not implemented. The phase boundary mechanics already support adding constraint-surface artifacts; adding properties as one such artifact does not require restructuring.

---

## 16. Known Unaddressed Constraints

### Humans Must Remain Operable Without AI [DESIGN-ONLY]

The codebase and substrate must remain operable by humans even if AI services are gone or if the developer has to work without AI tooling for any reason. This is an active constraint to fight for, not a soft preference. The whole field of AI-assisted development currently ignores this — every existing tool optimizes for delegation, none preserves human operability as a design goal.

The substrate (ADRs, ARCHITECTURE.md, hand-maintained lessons file) is human-readable, which is the precondition for this constraint. But the *codebase* the AI generates may not be — it may be optimized for AI consumption, may use patterns no human on the team would have chosen, may accumulate complexity faster than any human can keep up with by reading.

There is currently no mechanism in this system to actively defend human operability of the generated code over time. This is named here as a known unaddressed constraint so that future work can attempt to address it. Possible directions, none yet committed:

- Per-slice human-readable summaries that capture what changed and why in a format a developer with no AI could read and act on.
- Mandatory architectural simplicity constraints (file size, function complexity, dependency depth) enforced by hooks.
- Periodic "AI off" sessions where the developer attempts to navigate and modify the codebase without AI assistance, surfacing places where comprehension has degraded.

These are sketches, not designs. The constraint is named so that it doesn't quietly disappear as the rest of the system evolves toward more delegation.

### Semantic ADR Drift [DESIGN-ONLY]

The mechanical validator catches forward, backward, and staleness drift in references between ARCHITECTURE.md and ADRs. It does not catch semantic drift — two ADRs that are technically consistent (no missing references, no superseded references) but contradict each other in meaning. Over time, the substrate can become internally incoherent while passing all mechanical checks. The integration sweeps currently re-read recent ADRs and flag suspected conflicts, but this is hopeful judgment, not mechanism.

A more structural approach is needed. Possible directions, none yet committed:

- Treating ADRs as a graph with explicit dependency edges, making contradictions a mechanical query.
- Differential invariants — every firm ADR declares a property the code must satisfy, and drift detection becomes the set of properties that are now jointly unsatisfiable.
- Periodic semantic re-review of the ADR corpus by a separate agent whose only job is conflict detection.

This is a real design problem and the system does not yet have a clean answer.

---

## 17. Empirical Support and Limits

This system has partial empirical support and a known unfalsifiable core. Three controlled findings are directly relevant:

1. **Song et al. (2026)¹** measured a 4.0 F1-point improvement from cross-context review (conducted in a fresh session with no access to production conversation history) over same-session self-review on injected-error detection across 30 artifacts and 150 errors. The control condition — reviewing twice in the same session — did not beat reviewing once, ruling out repetition as the mechanism. This is the strongest single empirical anchor for the claim that the session boundary itself is load-bearing.
2. **Tsui et al. (2025)²** measured a 64.5% average self-correction blind-spot rate across 14 open-source non-reasoning models, directly supporting the claim that authorship contamination is a real phenomenon distinct from model-inherent error. A minimal "Wait" prompt reduced blind spots by 89.3%, suggesting the capability exists but requires triggering — which indirectly supports the role-switching design.
3. **Kim et al. (ICML 2025)³** documented substantial correlated errors across 350+ LLMs, with models agreeing roughly 60% of the time when both err on one leaderboard, driven by shared architectures and providers. This finding **bounds** how much fresh same-family sessions can catch and is why any future cross-family verification (see section 8, [DESIGN-ONLY]) is motivated in the first place.

Supporting evidence: **Panickssery et al. (NeurIPS 2024)⁴** established a causal link between self-recognition and self-preference in LLM evaluators via finetuning experiments, directly supporting the role-separation motivation for evaluation. **Zahn et al. (2026)⁵** provides theoretical grounds for why context compaction is structurally lossy — parametric memory suffers interference proportional to semantic density — which is why the system uses committed artifacts at phase boundaries rather than compacted summaries.

None of these findings resolves the central unfalsifiable claim. There is no current experiment that would distinguish "role contamination was a real problem the fresh session prevented" from "the fresh session did nothing but happened to coincide with higher-quality output because the developer had more time to think." This is a methodology-research limitation, not a system flaw, but it means the system's strongest claim — that the human-reset half of the dual mechanism is load-bearing — cannot currently be proven.

The system operates under explicit **calibration gap**: its discipline is more rigorous than the evidence justifies, as a deliberate trade-off for safety-critical work. Users adopting this system should make the trade-off consciously rather than implicitly.

Earlier internal drafts of this spec cited additional specific statistics — a "50% more leniently" number for self-preference bias and "60% fact destruction / 54% constraint erosion" numbers attributed to Zahn — that could not be verified against the source papers and have been removed. This is the honesty audit the spec is supposed to do to itself.

**References.**

1. Song et al., "Cross-Context Review: Improving LLM Output Quality by Separating Production and Review Sessions," 2026. arXiv:2603.12123.
2. Tsui et al., "Self-Correction Bench: Uncovering and Addressing the Self-Correction Blind Spot in LLMs," 2025. arXiv:2507.02778.
3. Kim et al., "Correlated Errors in Large Language Models," ICML 2025. arXiv:2506.07962.
4. Panickssery et al., "LLM Evaluators Recognize and Favor Their Own Generations," NeurIPS 2024.
5. Zahn et al. (cited for the theoretical compaction-loss argument), 2026. arXiv:2603.17781 (possibly related). The earlier internal-draft co-author "Chana" could not be verified against the source paper and is not cited here.

---

## 18. Open Questions

These are questions the system has not answered. Each is a place where further work could move the system from "plausible methodology" toward "evidenced methodology."

- **The dual mechanism falsification experiment.** What minimal experiment would distinguish in-session-discipline from session-boundary effect? Until this experiment exists, the dual-mechanism claim is not testable.
- **Phase decomposition refinement.** Is the four-phase shape optimal? Or would a different decomposition based on what phases *produce* (rather than how many exist) be cleaner?
- **Stronger machine-checkable routing.** Self-classification into Decision vs. Slice is friction, not a wall. What would automatic detection look like — slice envelopes touching files referenced in firm ADR consequences?
- **Cross-family synthesis by a different family.** What mechanism would actually achieve independent cross-family verification without creating a worse correlated-errors problem at the synthesis layer?
- **PBT as defense against interpretation drift.** Can property-based testing (section 15) catch interpretation drift in addition to AI-test blind spots, or is it orthogonal?
- **Formal verification for the critical 10%.** For the smallest, most safety-critical components — the parts where bugs cost the most — is there a layer where formal verification (TLA+, Lean, refinement types) earns its weight? The system does not currently have one.
- **Personas as phase openers.** Would assigning a different persona at each phase boundary (skeptic-validator, builder-implementer, integrator-auditor) reinforce role purity beyond what the fresh session achieves alone?
- **Handoff document quality assessment.** Is there a way to mechanically assess whether a handoff note is good enough to bootstrap the next session? Length? Specific sections? Consumption error rate when read by `/catchup`?
- **Decision archaeology.** Can the ADR corpus be queried (mechanically or via LLM) for "what decisions led to the current shape of X"? This would change the substrate from a forward-only log into a navigable graph.
- **Distinguishing failure modes in post-mortem.** When something goes wrong, the system has multiple defenses (phases, sweeps, hooks, validator). Can a post-mortem reliably determine *which* defense should have caught the failure? Without that, learning is shallow.

---

## 19. Relationship to Spec-Driven Development

This system is a flavor of spec-driven development, not a rejection of it. SDD at the abstract level claims: the spec is the load-bearing artifact, code is downstream of it, the discipline is in keeping the spec authoritative. Every concrete SDD implementation makes specific choices about what counts as a spec, how it's authored, how it's enforced, how it evolves.

This system implements SDD with two specific structural commitments that dominant SDD tools (Spec Kit, BMAD, Kiro) hand-wave:

1. **Specs are not trusted as authored.** ADRs are provisional until they survive an adversarial protocol. Even after the protocol, they're subject to mechanical validation and supersession when learning happens. Trust in the substrate is earned by structure, not assumed from authorship.
2. **A single agent in a single session cannot both author and consume the spec faithfully.** The slice protocol exists because within-session role switching cannot be trusted. Phase boundaries with fresh sessions are how the substrate reaches the implementation without contamination.

These commitments are what the rest of SDD's implementations don't make. Most SDD tools assume the constitution or PRD is authoritative once written, run their workflows in continuous conversations where the same agent moves through phases, and rely on workflow ceremony for the discipline that should be structural enforcement.

The framing this system fits into: **what SDD looks like when you take its own claims seriously enough to enforce them against the failure modes (correlated errors, role contamination, substrate drift) the dominant SDD implementations don't address.** It is not a novel methodology. It is a more disciplined implementation of an existing tradition.

---

## 20. Adversarial Review Guidance

This document is intended to stand on its own under adversarial review. The system has been revised through multiple rounds of attack, and findings have been incorporated. A reviewer should not need to be told what attacks have already landed — the system either embodies the fix or explicitly acknowledges the residual limit.

When attacking a claim, identify the implementation status tag:

- An attack against an **[IMPLEMENTED]** claim that the implementation does not actually do is a writeup bug. Report it as such.
- An attack against an **[IMPLEMENTED-WITHOUT-MECHANICAL-DEFENSE]** claim should target the mechanical-defense gap, not the discipline.
- An attack against a **[PARTIAL]** claim should specify whether it targets the part that is implemented or the part that is not.
- An attack against a **[PLANNED]** claim is a design refinement before the planned thing lands.
- An attack against a **[DESIGN-ONLY]** claim is help with whether to commit to the design at all.

### What to Attack

The strongest attacks against this system will target one of these:

1. **The dual mechanism's load-bearing claim.** The human-reset half has no direct experimental validation. An attack that proposes a falsifiable experiment — or argues from other evidence that in-session discipline suffices — would damage the system more than any other.
2. **Omission contamination in cross-family verification.** Defense is at [DESIGN-ONLY] level anyway, but if attacked: the raw inputs are still produced by Claude, so any constraint Claude fails to identify in Constraint Harvest cannot be attacked on its basis.
3. **Metacognitive limits in interpretation drift defenses.** The defense requires either the intent author or validator to enumerate an ambiguity. Both can share the same blind spot.
4. **The calibration gap as a practical problem.** The system acknowledges discipline is calibrated higher than evidence. An attack showing this honesty leads to predictable discipline erosion in real use (users reading the honest admission and deciding to skip protections) would show the epistemic honesty is a practical liability.
5. **Routing self-classification under pressure.** Metadata justification is friction, not a wall. Under deadline pressure, developers may systematically downgrade work.
6. **Phase decomposition itself.** The current four-phase shape (or the earlier spec's 3/4/5) may not be optimal. An attack proposing a cleaner decomposition based on what phases *produce* rather than how many exist would be valuable.

### What Not to Waste Effort On

- Arguing that the system should be tool-agnostic. v0/v1 is Claude Code-coupled by design. Tool-portability is a packaging decision orthogonal to the methodology.
- Arguing that this is over-engineered for simple software. Section 1 explicitly excludes simple software.
- Arguing that the role-reset thesis is unproven. The document acknowledges this explicitly. Attack the practical consequences of the uncertainty, not the uncertainty itself.
- Arguing that subagents could replace fresh sessions on the linear pipeline. Section 3 and section 14 (incident #3) address this explicitly.
- Arguing that compaction is equivalent to committed artifacts. Section 17 cites Zahn et al. on this.
- Arguing that cross-family verification should be in the system as if it ran. It is [DESIGN-ONLY] in section 8. Attack the fresh-same-family mechanism on its own merits, not against the cross-family aspiration that does not exist.

### How to Structure a Review

A review should state which attacks were mounted, which succeeded and why, which failed and why, the strongest single attack, what the system would need to change to address it, and an overall verdict. The goal is to find holes, not to validate. A review that finds nothing is less useful than a review that finds one decisive hole.

---

## 21. Closing Note

This system is one engineer's attempt to assemble a coherent methodology for complex AI-assisted development from the available primitives in Claude Code. It is not a proven methodology. It is a defensible architectural choice based on plausible mechanism, partial empirical support, and direct practitioner observation in safety-critical contexts.

The system's strongest feature is not any particular mechanism. It is the honesty about what is implemented, what is partial, what is planned, what is design-only, and what has known substrate incidents. Each of those statuses is marked so attacks land at the right layer.

Anyone adopting this system is making a conscious bet that the underlying mechanisms are real even though the strongest forms of those claims remain unproven. That bet is reasonable for safety-critical greenfield work where the asymmetric cost of contamination justifies acting on plausible-but-unproven mechanisms. It is unreasonable for simple work where the asymmetry is absent.

The system is not finished. It will continue to be revised as further review surfaces new attacks and as real project experience surfaces new failure modes. The current version is what has survived the attacks so far — not what is provably correct.

---

*End of spec v1.*

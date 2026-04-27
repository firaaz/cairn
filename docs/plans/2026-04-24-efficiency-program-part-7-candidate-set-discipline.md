# Efficiency Program Part 7 — Candidate-set Discipline Research

**Date:** 2026-04-24
**Status:** Research phase complete (§3-§9). Post-review reframe in §10 supersedes §8 digest on the context-reduction axis. Compression audit (§12, separate doc) follows. GO signal for `/decision` is conditional on operator confirming framing per §10.6, not §8.3.
**Series:** docs/plans/2026-04-18-efficiency-program (extends Parts -1 through 6 with a research part preceding a project-defining `/decision`)
**Trigger:** `docs/plans/2026-04-18-session-compression-audit.md:61` — F2 candidate-set leakage. Slice C of the compression feature is blocked pending the `/decision` this research prepares.
**Weight class:** Project-defining. Operator flagged this as potentially foundational to cairn's long-term shape.

---

## 1. Context & problem

### 1.1 The failure mode (F2)

From the session-compression audit (`docs/plans/2026-04-18-session-compression-audit.md:61`):

> Phase 2 tests often need to accept multiple valid implementations (the point of intent-not-impl). But enumerating the set IN THE TEST leaks the set into Phase 3 as an affordance constraint.

Concrete F2 signature: Phase 3 (Builder) chooses implementation X because X was in the test's enumeration, not because the Builder re-derived X from intent. The test-embedded enumeration anchors the Builder's affordance space. This destroys cairn's core property: **independence-of-re-derivation across phase boundaries.**

### 1.2 Why it matters — the independence thesis

Cairn's core thesis: **AI-reviewing-AI with shared context produces correlated errors that look like verification.** The 4-6x token baseline (vs. single-session dev) is partly the cost of keeping phases independently re-derivable — fresh sessions, differently-scoped agents, minimal shared reasoning. If Phase 2 and Phase 3 share a candidate set (whether explicitly in intent.md or implicitly embedded in tests), their error modes correlate and the verification ceases to be independent.

F2 is a specific failure of this property at the Phase-2↔Phase-3 boundary. But the general class of failures — shared-reasoning surface between phases that should be independent — appears in multiple forms:
- Phase 2 tests anchor Phase 3 (F2, our target).
- Phase 1 intent framing anchors both Phase 2 and Phase 3 (shape-neutral failure; not F2-specific).
- Phase 4 audit relies on Phase 3's self-reported rationale (orthogonal failure).

This research targets F2 primarily but must not solve F2 in a way that worsens other independence failures.

### 1.3 Literature context (preliminary)

Recent synthesis (operator-provided, to be validated in R1/R2):
- **2,500-token context-quality cliff** — response quality degrades beyond ~2,500 tokens of retrieved context (January 2026 systematic analysis, citation TBD in R2).
- **"Lost in the middle"** — accuracy drops >30% when critical information sits mid-prompt.
- **Hierarchical multi-agent 97.7% accuracy at 61% cost** — budget models for workers, frontier for lead orchestrator (citation TBD).
- **Agentic SDLC 86% token concentration in code-review + code-completion** — the iterative verification loop IS the cost.

Implication: **Over-contextualized phases are BOTH more expensive AND lower-quality.** Compression is not just a cost lever; it's a verification-fidelity lever. This reframe shapes how to weight shape options.

### 1.4 Operator's framing (from 2026-04-24 plan-prep dialog)

- **Q1 Reframe**: accept both verification-fidelity AND auditability weighted equally; look for a lower-level structural move that handles both simultaneously rather than a per-case compromise.
- **Q2 Phase 5**: mandatory independent-verification step for firm decisions. Doubles phase budget.
- **Q3 Escalation cap**: no fixed number; per-feature budget set at shaping time based on complexity.
- **Q4 Part-0-ADR order**: this `/decision` lands BEFORE Part 0 ADR `phase-artifact-immutability-and-evidence-persistence` so Part 0's D3 ("candidate-sets must cite intent.md line") can be written shape-aware.
- **Q6 Read enforcement**: if chosen shape requires asymmetric reads, instruction-only at first landing (matches firm ADR `phase-lock-and-role-declaration`); hook-upgrade only if empirical violations observed.

---

## 2. Research scope

Five streams:

- **R1 — External agentic-framework survey.** Cursor, Aider, Devin, SWE-agent, Claude Code, LangGraph, AutoGen, OpenAI Swarm + recent academic literature (MAST, preference leakage, DMAD). **Status: complete (§3).**
- **R2 — Non-LLM verification-independence literature.** Formal methods, code review, pair programming, red/blue-team, dual-control finance, scientific peer review, hardware verification, safety engineering. **Status: complete (§4).**
- **R3 — Cairn-internal empirical audit.** Evidence of F2-shaped incidents in cairn's own history; contrasting clean-slice patterns; base rate estimate. **Status: complete (§5).**
- **R4 — Shape-space deep-dive.** 20 shapes (A–K seeds + M–Q analytical additions + R–W literature-surfaced) + composites. **Status: complete (§6).**
- **R5 — Decision-calibration meta-research.** Is `/decision` protocol sufficient for this weight class? Firmness recommendation. **Status: complete (§7).**

---

## 3. R1 — External agentic-framework survey

### 3.1 Per-framework findings

**Cursor (Plan Mode, Cursor 3 April 2026).** Plan-then-execute with human approval gate. Plan artifact is editable. Notably: Anysphere documented that Composer learned clarification-asking behavior via reward-hacking — had to be stabilized via reward-function changes. **Implication for cairn:** ambiguity-handling as emergent incentive-sensitive behavior is unreliable. Cairn should structurally enforce just-in-time escalation (Shape J), not rely on model incentives.

**Aider (Architect/Editor, Sept 2024).** Two inference passes with specialized roles. 85% pass when Architect is o1-preview and Editor is DeepSeek/o1-mini. Benefit interpreted as specialization (reasoning vs edit-format), not independence. No read-asymmetry — Editor receives Architect's full prose. **Implication for cairn:** model-heterogeneity across roles is a well-established lever for correlated-error defense; does not address affordance-space leakage.

**Devin 2.0 (Cognition Labs).** Planner researches codebase → human approves → Executor iterates. Temporal separation only; Executor sees plan + codebase. No published independence-of-verification architecture. **Implication:** industry default is shared-context planner/executor — cairn's asymmetric-reads stance is empirically unusual.

**SWE-agent (Princeton, NeurIPS 2024, arXiv:2405.15793).** Agent-Computer Interface (ACI) — curated commands/observations per step. Single-agent, not multi-role. The ACI principle of *curating what the agent sees at each step* is a sibling concept to cairn's asymmetric reads (Shape D).

**Claude Code (Anthropic).** Subagents provide fresh-context isolation: new conversation, scoped tools, separate system prompts, only final message returns to parent. Skills use progressive disclosure (metadata → body on demand). **Closest existing analog to cairn's phase-role reads.** Cairn already rides this substrate; the question is artifact-content asymmetry, not session asymmetry.

**LangGraph.** Subgraphs support **partitioned state** as a first-class primitive: subgraph declares its own schema; only overlapping keys surface back to parent. State-transformation functions project parent state to narrower subgraph view. **Near-exact analog of cairn's Shape D.** Strong cross-domain validation that asymmetric reads are a production-viable pattern.

**AutoGen (Microsoft Agent Framework).** Role-based message-visibility scoping is not documented as first-class; bolt-on via custom proxies. **Cautionary:** "multi-agent framework" does not imply "information-partitioned framework."

**OpenAI Swarm / Agents SDK.** Stateless; explicit `context_variables` dict agents read/write. Sender chooses what receiver sees. **Maps cleanly to Shape E (receipt-only handoff).**

### 3.2 Recent academic literature (2024-2026)

**Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (arXiv:2503.13657, NeurIPS 2025).** Introduces MAST — a 14-mode failure taxonomy over three categories: system design, inter-agent misalignment, task verification. 150 annotated traces (κ=0.88), 1600-trace dataset. **Directly validates F2 as a first-class failure category.**

**Preference Leakage (arXiv:2502.01534, Feb 2025).** When data-generator and judge LLMs share model family/lineage, judge preferences contaminate. Ranking impact exceeds egocentric bias. **Direct academic formalization of cairn's F2** — shared information between producer and verifier destroys independence. Cairn can cite this for empirical grounding.

**Monoculture collapse (Redis, Augment, Galileo 2025-2026).** Agents on similar models share correlated vulnerabilities. **Conformity bias:** confident assertions anchor downstream; false consensus locks in.

**DMAD — Diverse Multi-Agent Debate (ICLR 2025).** Agents with distinct reasoning approaches outperform homogeneous debaters. Initial answer diversity correlates with performance. **Heterogeneous foundation models: 91% vs 82% on GSM-8K.** Supports Shape F (parallel Readers) and Shape K (parallel Builders).

**SWE-Bench Pro (arXiv:2509.16941) and SWE-rebench (arXiv:2505.20411).** ~54% relative overestimation from evaluation leakage; 176 erroneous patches passed SWE-Bench Verified. Not correlated-error-across-agents specifically, but evidence that benchmark-level leakage is pervasive.

### 3.3 Patterns seen across frameworks

1. **Partitioned state / schema projection** (LangGraph, Claude Code subagents) — first-class support for "this role sees X, not Y."
2. **Explicit handoff payloads** (Swarm) — sender curates receiver's view.
3. **Model heterogeneity across roles** (Aider, DMAD literature) — reduces correlated failure but doesn't address information leakage.
4. **Plan-then-execute with human approval** (Cursor, Devin) — default industry pattern; full shared context. **Cairn explicitly rejects this.**
5. **Fresh-context subagents** (Claude Code) — conversation-history isolation.
6. **Progressive disclosure** (Skills) — load-on-demand reduces upfront anchoring.
7. **Independent judges** (PwC/CrewAI validation patterns) — separate judge with own criteria.

### 3.4 Cairn-mapping

| Shape | External analog | Strength |
|---|---|---|
| A | No direct analog — cairn would be first | Distinctive |
| **B** | Cursor/Devin shared plan | **Anti-pattern per academic literature (monoculture, preference-leakage)** |
| D | LangGraph partitioned subgraph state; Swarm explicit handoff | **Strong** |
| E | OpenAI Swarm explicit context-variable handoff; cryptographic commitment would be **novel** | Strong |
| F | DMAD multi-agent debate, diverse initial answers | Strong |
| I | Claude Code Skills progressive disclosure; LangGraph schema projection | **Strong** |
| J | Cursor clarification-asking (but reward-hacked — unreliable) | Escalation-as-artifact appears novel |
| K | DMAD + multi-agent debate literature | Strong |

### 3.5 Novel / surprise findings

- **No framework surveyed uses cryptographic commitment on handoff payloads.** Shape E's hash-receipt would be genuinely novel.
- **No framework enforces "contract-only tests" as a structural invariant.** Shape A may be cairn's most distinctive contribution.
- **Industry default is shared-context planner/executor.** Cairn's asymmetric-reads stance is empirically vindicated by 2025 academic work but has no production-tool peer.
- **Preference-leakage paper** is a near-exact academic formalization of F2 and should be cited in the ADR.
- **MAST taxonomy** names verification-failure as a formal category — cairn's problem is a known studied failure mode, not hypothetical.

---

## 4. R2 — Non-LLM verification-independence literature

### 4.1 Per-domain findings

**Formal methods / model checking.** Assume-guarantee (A/G) reasoning (Pnueli 1985; Abadi & Lamport, TOPLAS 1995) formalizes read-asymmetry: a component is verified against an *assumption* about its environment and a *guarantee* it provides; verifier sees the interface, not the implementation. **DO-178C (airborne software)** Table A-3 requires formal "independence" for high-DAL verification, defined as the verifier *not having participated in producing the artifact under review*. **LCF-kernel trust (Milner 1978)** enforces that trust attaches to the statement, not the derivation.
- **Maps to:** Shape E (receipt-only handoff), Shape I (P3 blind to spec).

**Software code review.** Bacchelli & Bird, "Expectations, Outcomes, and Challenges of Modern Code Review" (ICSE 2013): reviewers with too much context defer to author's framing; fresh eyes outperform domain embedding at the margin. Rigby & Bird (FSE 2013): cross-team reviewers had materially higher defect-finding rates than same-subteam reviewers. Bosu/Greiler/Bird (MSR 2015): review utility correlates with reviewer's prior unfamiliarity with the specific change. Baum et al. (2016): review comment-quality degrades with length and consecutive reviews — direct argument for fresh sessions.
- **Maps to:** Shape D, Shape F. Argues for temporal separation beyond session boundaries.

**Pair programming.** Hannay/Dybå/Arisholm/Sjøberg meta-analysis (IST 2009), 18 studies: pair benefit is small (d≈0.23) and task-dependent. On simple tasks pairs *underperform* solos due to **cognitive convergence** — partners synchronize on a single mental model and lose error-independence. **This is the most important cross-domain finding for cairn:** shared real-time context destroys error-independence even among skilled reviewers. Argues against any shape where P2 and P3 share live context.
- **Maps to:** Strong support for Shape E. Argues against any "pair" shape with iterative draft exchange.

**Red-team / Blue-team.** NSA ROE templates require information asymmetry. **"Red-team capture"** (Mudge, Sandia IORTA): long-duration red teamers optimize against known blue-team blind spots. Sandia's countermeasure: **rotation every 12-18 months**. Zenko's *Red Team* (2015) documents CIA Red Cell reporting outside the analytic chain; receives the question but not the analytic product. Purple-team models explicitly sacrifice independence → produce **training value, not assessment value** (Applebaum et al., MITRE CALDERA).
- **Maps to:** Shape E strong. Suggests a novel cairn shape — *role rotation across slices*.

**Dual-control / maker-checker.** SOX §404 and PCI-DSS 6.4.2 enforce separation of duties at the access-control layer — maker literally cannot see checker's queue. **SWIFT CSCF control 5.1** (explicit): *"the second individual must have independent access to the transaction details, not derived from the first individual's presentation of them."* **Bangladesh Bank heist 2016** is the canonical failure — both roles read the same compromised SWIFT queue, so a compromised message affordance-anchored both. Post-incident remedy: artifact-level independent retrieval, not handoff.
- **Maps to:** Shape D strong. Suggests novel shape — *independent-retrieval handoff* (stronger than D because asymmetry is enforced at the read interface, not by agent compliance).

**Scientific peer review.** Camerer et al. (Nature Human Behaviour 2018): pre-registered hypothesis specification is the dominant predictor of replicability. **Tomkins/Zhang/Heavlin (PNAS 2017):** single-blind reviewers 1.76× more likely to recommend acceptance for papers from famous authors — **quantifies affordance-leakage bias from a single channel in a randomized controlled trial.** Mellers/Hertwig/Kahneman (2001): adversarial collaboration pairs reviewers with *opposing priors* and pre-commits to mind-changing evidence.
- **Maps to:** Shape F (double-blind + diverse Readers). Suggests novel shape — *adversarial-prior instantiation*.

**Hardware verification.** Piziali's DV methodology (2004) + UVM guides enforce **DV writes coverage from architectural spec, not from RTL**. Reading RTL before writing coverage is a process violation. Failure mode has a name: **"coverage implementation bias"** — coverage enumerates what RTL does rather than what spec requires. **This is F2 precisely.** Foster's Functional Verification Trends surveys (Siemens biennial since 2007): bug-escape rates correlate with DV's RTL exposure.
- **Maps to:** Shape I (three-tier artifact with P3 blind to spec) — "almost verbatim" the DV discipline.

**Safety engineering (HAZOP/FMEA/FTA).** HAZOP (IEC 61882, Kletz 1992) uses **exogenous guide words** — *no, more, less, reverse, boundary, partial-failure* — applied systematically to each design parameter. Guide words come from the methodology, NOT the design. Prevents the review team from converging on designer's mental model. HAZOP leader must be non-involved. FMEA (MIL-STD-1629A) uses an enumerated failure-mode library independent of the specific design.
- **Maps to:** Suggests novel shape — *exogenous guide-word test generation* (P2 writes tests from a methodology-owned failure-class list, not from intent).

### 4.2 Cross-domain synthesis

**Mechanisms appearing in 4+ domains (strong generality):**

1. **Read-asymmetry on specific artifacts** — A/G reasoning, diff-blindness for reviewers, RTL-blindness for DV, spec-only for replicators, maker-checker independent retrieval, red-team blindness to detection rules. **Six domains converge.**
2. **Temporal/session separation with no live context sharing** — pair-programming cognitive convergence, review fatigue, red-team rotation, HAZOP leader non-involvement. Four domains.
3. **Exogenous prompt structure** (not derived from the artifact) — HAZOP guide words, FMEA library, FTA top-down, adversarial-collab pre-registration. Four domains.
4. **Institutional/reporting separation** — CIA Red Cell, DO-178C independence, SOX duties. Three domains, regulatory weight.

**Empirical base rates when controls absent:**
- Tomkins et al. 2017: **1.76× acceptance bias from identity leakage alone** (RCT on ICML).
- Hannay 2009: pair-programming benefit collapses to near-zero on simple tasks due to cognitive convergence.
- Bangladesh Bank 2016: 100% control failure when maker-checker shared presentation layer.

**Convergent message: without mechanical asymmetry, reviewer independence is performative. Role labels alone do not produce independence; only artifact-level access control does.**

### 4.3 Cairn-mapping summary

| Shape | Non-LLM analog | Strength |
|---|---|---|
| A | HAZOP top-down; FTA undesired-event-first | Strong (exogenous framing) |
| **B** | **Purple-team model** | **Anti-pattern — deliberately sacrifices independence; produces training value, not assessment** |
| D | DV blind to RTL; maker-checker independent retrieval; red-team blind to blue rules | **Very strong — six domains** |
| E | A/G reasoning; CIA Red Cell; SWIFT post-Bangladesh | Very strong — four domains |
| F | Many Labs replication; double-blind panels | Strong |
| I | DV architectural-spec-only coverage | **Very strong — "almost verbatim" the DV discipline** |
| J | Adversarial-collab escalation; HAZOP adjudication | Moderate |
| K | Many Labs multi-site replication | Strong (note: convergence = spec-adequacy evidence, not correctness) |

**Shape B warrants a warning in the ADR:** it has an analog (purple team) but that analog is consistently classified in the security literature as producing training value, not assessment value. If cairn adopts B, the resulting artifact cannot claim independence-preserving verification.

### 4.4 Novel shapes suggested by literature (named to avoid clash with R4's M-Q)

- **Shape R — Exogenous guide-word test generation (HAZOP analog).** P2 tests generated by applying a fixed, methodology-owned guide-word list to intent parameters, not by P2 freely enumerating from intent. Forces coverage of failure classes intent didn't mention; mechanically decouples test structure from implementation affordance space. **Directly addresses F2 at the generation step, not propagation step.**

- **Shape S — Role rotation across slices (red-team rotation analog).** No single agent instance plays the same phase role for consecutive related slices. Prevents F2 priors accumulating across a feature's slices.

- **Shape T — Adversarial-prior instantiation (adversarial collaboration analog).** P2 system prompt encodes priors *opposing* P1's natural framing. Goes beyond "different session" to "different disposition." Mellers/Hertwig/Kahneman 2001 empirical support.

- **Shape U — Independent-retrieval handoff (post-Bangladesh SWIFT analog).** P3 does not receive artifacts from P2; P3 retrieves from a store P2 wrote to. Store enforces access control — P3's store view hides `candidate-sets.yaml` even if P2 wrote it. **Stronger than Shape D** because asymmetry is enforced at the read interface, not by agent compliance.

- **Shape V — Two-source corroboration for spec (DO-178C multi-version analog).** intent.md fed to P3 is a merge of two independently-produced intents; any divergence surfaced as ambiguity rather than silently resolved. Combines F with a different use of divergence — not arbitration, but flagging.

- **Shape W — Pre-registered success criteria (replication-crisis analog).** Before P3 runs, a separate artifact commits what P3's output must demonstrate to count as successful — independent of anything P3 produces. Prevents P4 from anchoring on P3's framing of its own success. **Camerer 2018: single largest predictor of replicability.**

---

## 5. R3 — Cairn-internal empirical audit

### 5.1 Primary F2 evidence: efficiency-program-afternoon-wins / all-seven

**Slice commits:** `5e2194f` (intent) → `b6850bd` (validation) → `b7c3e5e` (implementation) → `92a7b15` (complete) → `7798561` (handoff).

**Phase 2 test enumeration pattern** (from `b6850bd:.claude/current-slice/validation/approach.md`):

The Skeptic explicitly enumerated candidate sets in Python tuples:
- **Item 1 (role cheatsheet hook):** `CANDIDATE_HOOK_NAMES` = `(checks/session-start.sh, checks/role-cheatsheet.sh, checks/session_start.sh, checks/cheatsheet.sh)`.
- **Item 7 (status dashboard renderer):** `CANDIDATE_RENDERER_PATHS` = `[scripts/render_status.sh, scripts/status.sh, scripts/render_status.py, scripts/status.py]`.

**Phase 3 implementation outcome** (from `b7c3e5e:.claude/current-slice/implementation/notes.md`):

Builder A explicitly chose from the enumerated set, documenting:
> "Hook named `checks/role-cheatsheet.sh` (chosen from the test's `CANDIDATE_HOOK_NAMES` tuple)."
> "This works because the Phase 2 test's `CANDIDATE_HOOK_NAMES` tuple iterates in order; `role-cheatsheet.sh` is the first existing hook the test finds."

**This is direct evidence of F2.** Phase 3 did not derive the hook name from intent's semantic requirements; it picked the first match from Phase 2's enumeration. The audit documents this as a MEDIUM-severity finding at `docs/plans/2026-04-18-session-compression-audit.md:22`.

**Recovery cost:** Phase 4 auditor flagged but did not block. Artifact shipped. Recovery via independent audit session only — post-hoc detection.

### 5.2 Contrasting clean case: SLICE-003-precursor

**Phase 2 test shape** explicitly avoided enumeration:
- V1: "exactly 1 `## Phase Skill Guide` heading" (binary).
- V2: "content includes four phase names, four role names, ≥1 skill" (open-ended quantity).
- V3: "includes 'living registry' note AND 'ADR-004' citation" (required-string conjunction, not alternatives).
- V6: "`adrs-referenced` field existence + failure message naming 'missing ADR'" (no enumeration).

**Ambiguity resolutions:** Every ambiguity (A1-A7) preserved Builder freedom with escape hatches:
- "V4 tests for textual anchor inside Mode A region; Builder picks exact format."
- "V2 tests content (4 phases × 4 roles × ≥1 skill), not byte equivalence. Verbatim is a Builder instruction, not a Skeptic test criterion."
- "`docs/adr/NNN-*.md` resolution deferred to Builder. V6 tests existence check presence."

**Load-bearing mechanism:** The approach.md was **quarantined from Phase 3**: "Phase 3 Builder should NOT load... `.claude/current-slice/validation/approach.md`" — approach.md exists for Phase 4 Auditor only.

**Recovery cost:** Zero. Passed Phase 4 cleanly.

### 5.3 Lessons documentation — F2 signals and structural analogs

- **L-003 (Phase 5 Independent Verification — index-row leak)** is **cairn's own structural analog of F2 at the Phase 4→5 boundary**: Phase 4's `docs/adr/index.md` update was visible to Phase 5 subagent, "pre-anchoring the enumeration to whatever the title reveals." Mitigation: phase-commit splitting. **Critical: cairn has already experienced and mitigated candidate-set leakage at another phase boundary.**
- **L-004 (Inherited threshold).** Counter from D1 reused in D3 without re-examining whether failure classes were "the same kind of thing." Fix: three-class reason schema preventing conflation. Parallel pattern to F2 (reusing structure without re-validating applicability).
- **L-007 (Framing-doc attribution inheritance).** ADR's D2 enforcement built on upstream framing doc's claim; Phase 5 verification found it factually wrong. Rule: "verify each [code-level assertion] against the implicated code path... or mark each unverified claim explicitly on a premise list that Phase 5 is instructed to re-examine." **Inverse defense against F2.**
- **L-008 (Phase-3 commit discipline).** Phase 3 committed subset of envelope changes under context pressure. F2 is a special case of this pattern — context pressure causes P3 to anchor on visible structure rather than re-derive.
- **L-009 (sweep.yaml clobbering).** F2 at file-role level: agent saw file name matching its work and treated it as target destination.

### 5.4 Git archaeology

Escalation / re-dispatch commits sampled: `9555262` (cost-discipline P4→P3), `3acc6cc` (compression P3→P1 full rewind), `7feebbd` (manual P3 recovery), `bbdc8e1` (mid-slice intent amendment), `8e619c3` (envelope expansion for fixture reconciliation — possible F2 signal: P3 discovered scope P2 didn't require).

**No commits contain the word "candidate" in subjects.** Git-log archaeology alone cannot directly confirm F2 incidents, but the frequency of re-dispatches + amendments (~1 per 50-100 slices sampled) suggests Phase 3 frequently discovers misalignments causing roll-back.

### 5.5 Quantitative summary

| Metric | Finding |
|---|---|
| Total completed slices visible | ~30-40 |
| Slices with explicit F2 documentation | 1 (efficiency-program-afternoon-wins/all-seven) |
| Slices with clean Phase 2 non-enumeration | 1 clearly documented (SLICE-003-precursor); others not examined |
| Slices with F2-adjacent lessons | 4 (L-003, L-004, L-007, L-008) |
| **F2 rate when Phase 2 enumerates in test code** | **1/1 observed — high probability** |
| **F2 rate when Phase 2 avoids enumeration** | **0/1 observed — zero documented** |
| Evidence confidence | **Low-to-medium**: one smoking-gun case, one clean contrast, four adjacent lessons, many slices unexamined |

**Evidence is thin but directional: enumeration enables anchoring.**

### 5.6 Shape-seed support from internal evidence

| Shape | Internal evidence | Strength |
|---|---|---|
| **A (contract-only tests)** | SLICE-003-precursor clean record | **Moderate support** |
| **B (intent-level candidate-sets)** | No slices found using this at intent level; candidates live in P2 tests | **Weak — disfavored in practice** |
| Current-implicit pattern (intent under-specifies, P2 enumerates) | efficiency-program/all-seven produces F2 | **F2 occurs here reliably** |
| D (asymmetric reads) | Not directly observed; SLICE-003-precursor's "don't load approach.md" is proto-D pattern | Weak-to-moderate support |
| J (just-in-time operator escalation) | SLICE-003-precursor E1/E2 escalations work | **Moderate support** |

### 5.7 Internal-evidence recommendations

1. **Phase 2 test discipline:** behavioral assertions (schema, contract, presence) over enumerated alternatives. `CANDIDATE_HOOK_NAMES` is an anti-pattern.
2. **Explicit escalation over implicit enumeration:** Phase 2 ambiguities escalate to operator per L-002, not bake into test choice-points.
3. **Quarantine Phase 2 reasoning from Phase 3:** SLICE-003-precursor's "Builder must NOT load approach.md" is load-bearing; make it standard handoff content.
4. **Operator intent-clarification at Phase 1→2 gate** (L-007 echo): discovered-during-P2 ambiguities escalate back to P1.
5. **If Shape B adopted, it needs explicit ADR specifying candidate-list protocol.** Currently cairn's intent-level Shape B is absent; making it explicit requires protocol-gating.

---

## 6. R4 — Shape-space deep-dive

Every shape described by six properties:
1. **Mechanism** — how it operates concretely at the phase-boundary level.
2. **Independence property** — which phase-pair coupling it attacks; under what conditions it fails open.
3. **Auditability property** — what artifact is produced that supports mechanical audit; how Phase 4 uses it.
4. **Cost axes** — Opus-side tokens (P1/P2), Sonnet-side tokens (P3/P4), operator turns, infrastructure build cost.
5. **Failure modes** — at least two, with recovery path.
6. **Part-0-ADR interaction** — D1 (append-only intent), D2 (sweep-notes as evidence), D3 (candidate-sets cite intent.md line).

### 6.1 Shape A — Contract-only tests

**Mechanism.** Phase 2 Skeptic writes tests as behavioral invariants drawn from `intent.md` only. Tests pattern over contract properties ("any valid renderer must accept role playbooks"), not over enumerated options ("render-via-sh or render-via-js"). Phase 3 Builder chooses from the unbounded affordance space; no candidate set is visible in any artifact.

**Independence property.** Maximal — Phase 2 and Phase 3 share zero candidate-set structure. Only intent.md is shared between them.

**Auditability property.** Weak — Phase 4 audits Phase 3's implementation against contract tests, not against an explicit authorized enumeration. "Did this pass the behavioral tests?" is the checklist.

**Cost axes.** Low — no additional artifacts; P2 writes behavioral tests (comparable effort to enumeration-style); P4 audit is post-hoc.

**Failure modes.**
- A1: P2's behavioral invariants are too loose → P3 ships a valid-passing but intent-divergent implementation → P4 escalation. Post-hoc detection.
- A2: P2 and P3 both misread `intent.md` identically (correlated error via intent prose, not via candidate set). Shape A does not prevent; Phase 5 verification required.

**Part-0-ADR interaction.** D3 vacuous — no candidate-sets exist to cite intent.md lines. D1/D2 orthogonal.

### 6.2 Shape B — Explicit `candidate-sets:` YAML in `intent.md`

**Mechanism.** Phase 1 Reader adds a `candidate-sets:` block to `intent.md` enumerating authorized options with rationale. Phase 2 tests reference the enumeration (tests may pattern over set membership). Phase 3 chooses from the set. Phase 4 audits set-membership.

**Independence property.** Weak across the Reader↔Skeptic↔Builder triangle — the set is shared between all three agent roles. "Builder chose X because X was in the set" becomes explicit rather than implicit, which is honesty but not independence.

**Auditability property.** Strong — set is a first-class artifact; P4 audit reduces to membership check + "does chosen option satisfy intent?"

**Cost axes.** Low — YAML structure in intent.md; P1 writes more upfront; P4 audit is mechanical.

**Failure modes.**
- B1: Reader's enumeration omits a valid option or includes an invalid one → P1 amendment required (expensive relative to in-phase fix).
- B2: Candidate set anchors both P2 and P3 — neither questions membership. Shape B does not prevent; Phase 5 required.

**Part-0-ADR interaction.** D3 fully binding — every `candidate-sets:` entry must cite an `intent.md` line authorizing the ambiguity.

### 6.3 Shape C — Hybrid (per-case classification)

**Mechanism.** Phase 1 classifies ambiguities: high-consequence get Shape-B treatment (explicit `candidate-sets:`); low-consequence get Shape-A treatment (contract-only). Reader must author classification heuristic for each ambiguity.

**Independence property.** Case-dependent. Where Shape A treatment used, strong. Where Shape B used, weak.

**Auditability property.** Mixed — the classification decision itself is auditable (why was this ambiguity deemed low-consequence?), but Shape A portions audit weakly.

**Cost axes.** Moderate — classification overhead at P1; additional rationale prose per ambiguity.

**Failure modes.**
- C1: Reader misclassifies high-consequence ambiguity as low → shape-A failure mode on a high-stakes decision. Compounds A1/A2 for that ambiguity.
- C2: Classification becomes bureaucratic overhead; Reader spends context budget on classification heuristics. May push Reader past the 2,500-token quality cliff.
- C3: Classification criteria drift across slices without enforcement → protocol erosion.

**Part-0-ADR interaction.** D3 partially binding (on the Shape-B portions only). D1 orthogonal.

### 6.4 Shape D — Asymmetric phase reads

**Mechanism.** Split `intent.md` (goal + success conditions + out-of-scope, no enumeration) and `candidate-sets.yaml` (authorized paths + rationale). Read scoping:

| Artifact | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| `intent.md` | write | read | read | read |
| `candidate-sets.yaml` | write | read | **NOT read** | read |
| P2 tests (behavioral, not enumeration-literal) | — | write | read | read |
| P3 implementation | — | — | write | read |

P2 uses the set as specification scaffold but writes behavioral tests (Shape-A-style). P3 is structurally blind to the set.

**Independence property.** Strong at the P1↔P3 edge and the P2↔P3 edge — the candidate set's influence on P3 is eliminated by construction. Independence is topological, not instructional.

**Auditability property.** Strong — set is a committed artifact; P4 audits "is P3's choice ∈ set?" mechanically. Discrepancy flagged: P3 found a valid alternative Reader didn't enumerate — Reader amends set.

**Cost axes.** Low — new artifact file; agent-prompt edit to `.claude/agents/phase-3-implementer.md` adding "do not read `.claude/current-slice/candidate-sets.yaml`". P4 gets slightly richer audit surface. No infrastructure.

**Failure modes.**
- D1: Reader's set is wrong. P3 (blind) may independently produce a valid alternative; P4 audit flags divergence as positive signal — Reader amends. **This is actually stronger than Shape B: P3's blindness enables genuinely novel options to surface.**
- D2: P2's behavioral tests fail to capture set-relevant distinctions → P3 passes tests with unanticipated implementation that violates intended set semantics. Recovery: P2 amendment.
- D3: Instruction-only read-scoping is violable. P3 could read `candidate-sets.yaml` if it chose to. Firm ADR `phase-lock-and-role-declaration` chose instruction over enforcement — this is consistent discipline but not a mechanical guarantee.

**Part-0-ADR interaction.** D3 rewording required — "candidate-sets must cite the intent.md line that authorized the ambiguity" — citation target becomes cross-file (yaml → md). D1 compatible (candidate-sets.yaml can be append-only). D2 compatible (yaml is committed).

### 6.5 Shape E — Receipt-only handoff P2→P3

**Mechanism.** P3 does not read P2's test source at all. P3 receives `{test-count, pass-condition-summary ≤100 words, test-suite-hash}` as handoff artifact. P3 writes implementation blind to test structure. Phase 4 runs P2's actual tests against P3's implementation; failure triggers RE_DISPATCH to P3 with diagnostic summary (not test source).

**Independence property.** Maximal at the P2↔P3 edge — even the implicit candidate set encoded in test structure is invisible to P3.

**Auditability property.** Strong — tests are committed artifacts P4 runs mechanically. Summary-as-handoff is a committed artifact; its accuracy is P2's responsibility.

**Cost axes.** High — breaks the TDD feedback loop P3 currently uses ("iterate to green"). P3 round-trip cost multiplies: write → P4 runs tests → fail → RE_DISPATCH → write → ... Operator involvement may rise.

**Failure modes.**
- E1: Summary misrepresents test conditions → P3 optimizes to wrong targets → repeated failure-escalation loop. Recovery: P2 amends summary.
- E2: P3 without test feedback cannot iterate efficiently → slice duration balloons on ambiguous intents.
- E3: Tests that test non-functional properties (timing, output structure) become harder to summarize faithfully.

**Part-0-ADR interaction.** D3 vacuous (no candidate-sets if Shape E is alone). D2 compatible. Introduces new artifact type (summary-as-handoff) whose schema needs definition.

### 6.6 Shape F — Parallel P1 Readers with divergence arbitration

**Mechanism.** Phase 1 runs TWICE in parallel — two Opus sessions with perturbed system prompts (or different role-instruction variants). Two `intent.md` drafts produced; diffed. Operator arbitrates divergence BEFORE any downstream phase runs. Final `intent.md` is the reconciled output.

**Independence property.** Targets the Reader-framing layer — not the P2↔P3 leakage F2 per se, but the A2/B2 correlated-intent-misread failure mode. Does not address candidate-set-through-tests anchoring directly.

**Auditability property.** Divergence-log (what Readers DISAGREED on) is a committed artifact. Rich evidence of ambiguity even if reconciled.

**Cost axes.** Doubles P1 cost (Opus — the expensive side). Operator arbitration adds turns.

**Failure modes.**
- F1: Two Readers produce identical-enough drafts despite independent dispatch → false confidence (correlation via same training data / shared framing of intent brief). Can be mitigated by deliberate perturbation heuristics (e.g., "adversarial Reader" mode).
- F2 (Shape F F2): Operator arbitration stalls at high divergence → feature shaping halts.

**Part-0-ADR interaction.** Orthogonal to D3 (operates at P1 level). D1 compatible. D2 extended — divergence-log is new evidence artifact.

### 6.7 Shape I — Three-tier artifact (intent / spec / plan)

**Mechanism.** Generalization of Shape D across multiple constraint dimensions:
- `intent.md` — WHAT (goal + success conditions). Read by all phases.
- `spec.yaml` — HOW constrained (invariants, candidate-sets, perf budgets, coverage targets, firmness flags). Read by P2 + P4, NOT P3.
- `implementation-plan.md` — P3-internal artifact; P3's own scratchpad/plan.

P3's read scope: intent.md + P2 tests + envelope. Everything that would bias affordance selection lives in `spec.yaml`.

**Independence property.** Strong at the P3 boundary — all enumeration-class constraints partitioned into the spec file P3 doesn't read. Extensible: new constraint classes (perf, coverage) get the same treatment without reopening the design.

**Auditability property.** Strong — everything P4 audits lives in one structured file with clear schema.

**Cost axes.** Moderate — schema design upfront; P1 learns new yaml structure; migration cost if adopted retroactively on existing slices.

**Failure modes.**
- I1: Schema drift over time — `spec.yaml` becomes an accretion target without governance. Mitigation: schema versioning + validator.
- I2: Over-quantization — things that don't fit the schema get shoehorned; human nuance lost. Risk highest for novel ambiguity classes.
- I3: Same D3 instruction-violation risk as Shape D.

**Part-0-ADR interaction.** D3 generalized — applies to every `spec.yaml` entry. New schema gets its own schema-version ADR. D1/D2 compatible.

### 6.8 Shape J — Just-in-time ambiguity resolution

**Mechanism.** No upfront enumeration artifacts. When Phase 2 or Phase 3 encounters unresolved ambiguity, they STOP and emit `ambiguity-escalation-N.md` to operator. Operator resolves synchronously → Phase 1 appends to `intent.md` using Part-0-ADR D1's append-only machinery → phases resume. Each resolution is a discrete committed event.

**Independence property.** Strong at discovery time — no upfront set biases any phase. Each ambiguity is resolved where it matters, not anticipated.

**Auditability property.** Very strong — chronology of resolutions IS the audit trail. Every ambiguity has a committed resolution event with operator-authored rationale.

**Cost axes.** Variable — additional operator turns per ambiguity; slices with many ambiguities become operator-heavy. Slices with few ambiguities benefit: zero upfront cost.

**Failure modes.**
- J1: High-ambiguity slices degenerate into operator-dialog loops; phases stop-wait-resume repeatedly. May defeat cairn's "orchestrated autonomous" property.
- J2: Ambiguity not recognized as ambiguity → phase proceeds with silent assumption → F2-style failure reappears. Requires phases to be disposed toward raising ambiguity rather than resolving silently.
- J3: Asynchronous operator availability → phases block for extended periods.

**Part-0-ADR interaction.** D1 aligned natively (intent is already append-only per D1). D3 unneeded (no candidate-sets). D2 extended — escalation log is new evidence artifact.

### 6.9 Shape K — Parallel Phase-3 builders with convergence check

**Mechanism.** Phase 3 runs N=2 or N=3 times in parallel on identical inputs (intent + tests + envelope) with separate Sonnet sessions. All N implementations submitted to Phase 4 together. Phase 4 checks: all converge → accept any; diverge → operator arbitrates which satisfies intent+tests best; divergence logged.

**Independence property.** Statistical defense against Phase-3 correlated error specifically. Does not touch artifact structure — structural move is at the dispatch level. Orthogonal to F2's artifact-layer analysis.

**Auditability property.** Moderate — divergences become committed artifacts; which implementation won and why is recoverable. No structural candidate-set artifact.

**Cost axes.** Multiplies Phase 3 cost by N. P3 is on Sonnet (cheap side) after Lever 1, so rate-limit-quota impact is smaller than Opus duplication. But convergence-check logic is new infrastructure.

**Failure modes.**
- K1: All N builders produce the same wrong answer (correlated error they share despite independent dispatch — e.g., same training-data bias). Statistical defense doesn't catch; Phase 5 does.
- K2: Divergence arbitration becomes operator-heavy at high N.
- K3: Convergence-check algorithm has its own failure modes (what counts as "same" implementation? Structural-diff? Behavioral-equivalence?)

**Part-0-ADR interaction.** Orthogonal to D3. D2 extended — divergence-log new evidence. D1 orthogonal.

### 6.10 New shapes surfaced during analysis

#### 6.10.1 Shape M — Intent kernel quantization

**Mechanism.** `intent.md` restructured as strict YAML kernel with no free-form prose:
```yaml
goal: <one-sentence>
success-conditions: [list]
invariants-respected: [list of INV-NNN refs]
out-of-scope: [list]
firmness: provisional | firm
ambiguities:
  - id: A1
    question: <specific question>
    authorized-options: [list | "any valid per goal"]
    rationale: <why this ambiguity exists>
```
Machine-parseable. Downstream phases get clean structured context.

**Independence property.** Moderate — kernel is shared across all phases but contains no more than strict schema permits; no latitude for prose-embedded anchoring.

**Auditability property.** Maximal — every field is a mechanical audit target.

**Cost axes.** Low runtime; high one-time schema-design cost.

**Failure modes.**
- M1: Schema too rigid to capture human-nuanced goals → forced to use generic labels that lose meaning.
- M2: Schema evolution becomes an ADR-class concern; changing kernel schema is a protocol-layer decision.

**Part-0-ADR interaction.** D1 compatible (append-only applies to each `ambiguities:` entry). D3 absorbed into `ambiguities[].authorized-options` field schema.

#### 6.10.2 Shape N — Artifact-commit isolation (mechanical read boundary)

**Mechanism.** Extend existing commit-isolation pattern: Phase N can only read paths committed by Phase N-1 or earlier. Enforced via git-log inspection in agent dispatch prep (list readable paths from prior phases' commits; reject reads outside that set). Anti-forward-reading.

**Independence property.** Strong temporal — no phase can read artifacts that haven't been committed by a prior phase. Forces round-trip through git as the independence mechanism.

**Auditability property.** Strong — every read is traceable to a committed artifact.

**Cost axes.** Moderate — new role_guard read-hook design; list-prior-phase-commits preflight; additional orchestrator complexity.

**Failure modes.**
- N1: Agents have legitimate cross-phase read needs (e.g., Phase 4 reads everything) that require explicit exceptions.
- N2: Reopens phase-lock-and-role-declaration's "instruction over enforcement" discipline — now we have read-hook enforcement. ADR conflict.
- N3: Git-log inspection adds latency to every dispatch.

**Part-0-ADR interaction.** Would require a new ADR establishing read-enforcement as legitimate mechanism (supersedes or amends phase-lock-and-role-declaration). D1/D2/D3 compatible but interact with the new read-hook.

#### 6.10.3 Shape O — Intent via operator Q&A transcript

**Mechanism.** Phase 1 Reader operates as synchronous operator Q&A rather than writing prose. Every ambiguity becomes an explicit question to operator. `intent.md` becomes the transcript: `Q: ... / A (operator): ... / Q: ... / A: ...`. No post-hoc enumeration exists; all authorization happens in the Q&A at Phase 1.

**Independence property.** Strong — there is no enumeration artifact for downstream phases to anchor on; there is only explicit operator authorization at question-level granularity.

**Auditability property.** Very strong — every authorization is a discrete Q/A pair with operator attestation.

**Cost axes.** Operator-heavy at P1; zero at P2/P3/P4. Trades Opus cost for operator turns. Highly operator-dependent.

**Failure modes.**
- O1: Operator not available for synchronous Q&A → P1 stalls.
- O2: Reader doesn't recognize ambiguity → proceeds with silent assumption.
- O3: Q&A format loses prose nuance; some intent content is hard to Q&A-ify.

**Part-0-ADR interaction.** D1 extended (append-only applies to transcript). D3 absorbed (authorization is the A-side of Q&A pairs, citing is trivial). D2 compatible.

#### 6.10.4 Shape P — Specialist-pair Reader (division of labor at P1)

**Mechanism.** Phase 1 runs two specialized Reader variants: **Goal Reader** focuses on success conditions and out-of-scope; **Constraint Reader** focuses on invariants, firmness, candidate-sets. Each produces its own artifact-slice. Operator merges (or accepts as-is if no conflict).

**Independence property.** Targets Reader-framing bias via division of labor, not via duplication. Each specialist has a narrow scope and less latitude for framing error.

**Auditability property.** Strong — each Reader's artifact is distinct; merge conflicts (if any) are audit-visible.

**Cost axes.** Roughly 2x P1 cost (similar to Shape F) but specialized outputs may be shorter than full Reader, so possibly <2x. Operator merge adds turns.

**Failure modes.**
- P1: Division boundary is itself a design question — where does Goal Reader end and Constraint Reader begin?
- P2: Specialization may be counterproductive for cross-cutting intents.
- P3: Two readers reading same intent brief is still correlation through the brief itself.

**Part-0-ADR interaction.** D1/D2/D3 orthogonal. Requires new agent role definitions for the two Reader variants.

#### 6.10.5 Shape Q — Kernel + exhaust

**Mechanism.** Middle-ground between Shape A and Shape I: `intent.md` is a strict YAML kernel (like Shape M but less extreme); `intent-rationale.md` is free-form prose exhaust read ONLY by P1 and P4. Phases 2 and 3 see kernel only.

**Independence property.** Strong at the P2↔P3 edge via bounded rationale surface. Allows free-form reasoning at Reader time without letting it anchor downstream.

**Auditability property.** Strong — kernel is mechanical; rationale is prose evidence for P4 audit.

**Cost axes.** Low — two-file split, agent-prompt edits.

**Failure modes.**
- Q1: Kernel-vs-rationale boundary unclear in practice; Reader unsure where to put what.
- Q2: Same instruction-violation risk as Shape D for read-scoping.

**Part-0-ADR interaction.** D3 absorbed into kernel's `ambiguities:` schema. D1 compatible per-file. D2 compatible.

### 6.10.6 Shapes R–W (surfaced by R2 literature review)

Renumbered from R2's L-Q to avoid clash with section 6.10's M-Q:

**Shape R — Exogenous guide-word test generation (HAZOP analog).** P2 tests generated by applying a fixed, methodology-owned guide-word list (`no, more, less, reverse, boundary, concurrent, partial-failure`) to intent parameters. Forces coverage of failure classes intent didn't mention. Decouples test structure from implementation affordance space at the generation step.
- **Independence:** strong — test coverage emerges from exogenous methodology, not from intent-framed affordances.
- **Auditability:** strong — guide-word list is a protocol artifact; audit verifies each word applied to each parameter.
- **Cost axes:** P2 work shifts but doesn't grow; methodology-owned list is one-time protocol authoring.
- **Failure modes:** R1 — guide-word list ossifies and fails to cover novel failure classes. R2 — mechanical application produces irrelevant tests for some parameters.
- **Part-0-ADR interaction:** Orthogonal to D3 (no candidate-sets). Guide-word list becomes new protocol artifact.

**Shape S — Role rotation across slices (red-team analog).** No single agent instance plays the same phase role for consecutive related slices. Prevents F2 priors from accumulating across a feature's slices.
- **Independence:** targets cross-slice priors specifically; does not address within-slice F2 directly.
- **Auditability:** weak — rotation is an invariant over time, not a per-slice artifact.
- **Cost axes:** moderate dispatch complexity; no per-slice token cost.
- **Failure modes:** S1 — agents are ephemeral to begin with; "rotation" at subagent level may be vacuous. S2 — long-context windows may re-anchor on similar slices anyway.
- **Part-0-ADR interaction:** Orthogonal.

**Shape T — Adversarial-prior instantiation.** P2 system prompt encodes priors *opposing* P1's natural framing. If P1 reads intent charitably, P2 is instructed to assume intent is under-specified and the charitable reading is wrong. Mellers/Hertwig/Kahneman 2001 empirical support.
- **Independence:** targets A2 (correlated-intent-misread) directly — P2 is dispositionally unlikely to share P1's framing.
- **Auditability:** moderate — P2's rationale now includes "adversarial reading" content, which P4 can audit.
- **Cost axes:** agent-prompt edit; no infrastructure. Likely longer P2 outputs.
- **Failure modes:** T1 — adversarial P2 over-rejects valid implementations (false positives); recovery is operator adjudication.
- **Part-0-ADR interaction:** Orthogonal to D3. D2 compatible.

**Shape U — Independent-retrieval handoff (post-Bangladesh SWIFT analog).** P3 does not receive artifacts from P2; P3 retrieves from a store P2 wrote to. Store enforces access control — P3's view hides `candidate-sets.yaml` even if P2 wrote it. **Stronger than Shape D** because asymmetry is enforced at the read interface, not by agent compliance.
- **Independence:** maximal — mechanical enforcement, not instruction.
- **Auditability:** strong — access-control logs are audit artifacts.
- **Cost axes:** significant infrastructure (store with access-control layer; retrieval API); larger than Shape D.
- **Failure modes:** U1 — reopens phase-lock-and-role-declaration's "instruction over enforcement" discipline; ADR-level conflict. U2 — store complexity adds failure modes that didn't exist before.
- **Part-0-ADR interaction:** D3 adjusted as in Shape D. Would require a new ADR sanctioning read-enforcement mechanism.

**Shape V — Two-source corroboration for spec (DO-178C dissimilar-software analog).** intent.md fed to P3 is a merge of two independently-produced intents by parallel P1 Readers. Any divergence surfaced as ambiguity rather than silently resolved. Combines F with different use of divergence — not arbitration, but flagging.
- **Independence:** targets Reader-framing bias via corroboration.
- **Auditability:** divergence-as-ambiguity is itself an audit artifact.
- **Cost axes:** +1x P1 Opus; operator arbitration for divergences.
- **Failure modes:** V1 — two Readers produce identical intents by correlation (same training data) → false confidence. V2 — divergence rate high → many ambiguity artifacts to manage.
- **Part-0-ADR interaction:** D1 compatible (intent is append-only). D2 extended.

**Shape W — Pre-registered success criteria (replication-crisis analog).** Before P3 runs, a separate artifact commits what P3's output must demonstrate to count as successful — independent of anything P3 produces. Prevents P4 from anchoring on P3's framing of its own success. Camerer 2018: single largest predictor of replicability.
- **Independence:** targets the P3↔P4 boundary specifically (P4 audit independence from P3 self-reporting).
- **Auditability:** maximal — success criteria are a committed artifact; audit is mechanical check against criteria.
- **Cost axes:** low — new committed artifact, small authoring time at P2 (success criteria are often a test-suite subset).
- **Failure modes:** W1 — pre-registered criteria themselves carry framing bias (who wrote them, when). Operator review required.
- **Part-0-ADR interaction:** D2 extended (success criteria are new evidence artifact).

### 6.11 Composites

#### D + F — Asymmetric reads + parallel Readers

Addresses both F2 (downstream leakage) and A2 (Reader-framing correlated error). Phase 1 runs two Readers (Shape F); reconciled output split into intent.md + candidate-sets.yaml (Shape D). Strong at both edges; moderate cost overhead (+1x P1 Opus, +file split).

#### D + K — Structural + statistical

Shape D prevents candidate-set anchoring at P3 read time; Shape K runs P3 N times to catch P3-internal correlated errors. Hedged against both artifact-layer and agent-layer failure modes. Cost: file split + (N-1)x Sonnet. Infrastructure: dispatch N-parallel convergence check.

#### I + J — Rich schema + just-in-time

spec.yaml starts empty; ambiguities get resolved into spec.yaml entries as they're encountered (via Shape J's escalation mechanism). Spec.yaml grows during slice execution rather than being written upfront at P1. Novel hybrid: upfront schema, just-in-time population.

#### F + J — Parallel Readers + just-in-time

Two Readers at P1 producing complementary artifacts (not duplicated); ambiguities they disagreed on become the initial `ambiguity-escalation-N.md` entries. Synthesis combines Reader-divergence-as-ambiguity-discovery. Cost heavy.

#### D + F + K — Full defense-in-depth

Asymmetric reads + parallel Readers + parallel Builders. Most expensive ($$$ on both Opus and Sonnet sides) but maximal independence defense across all three phase-role boundaries. Likely overkill for routine slices; reserve for high-firmness work.

#### M + J — Strict kernel + just-in-time

Kernel forces ambiguities to be declared; J handles resolution when discovered. Marriage of static schema and dynamic resolution. Fewest latent ambiguities; most operator turns.

### 6.12 Comparison table (all 20 shapes)

| Shape | Source | Independence edge | Audit strength | Opus cost | Sonnet cost | Operator turns | Infra | Lit support |
|---|---|---|---|---|---|---|---|---|
| A | Seed | Intent-prose shared only | Weak | — | — | — | — | HAZOP top-down |
| B | Seed | **None (shared set)** | Strong | — | — | — | — | **Purple-team ANTI-PATTERN** |
| C | Seed | Case-dependent | Mixed | — | — | — | — | Weak |
| **D** | Seed | P1↔P3, P2↔P3 | Strong | — | — | — | file split + prompt | **Very strong (6 domains)** |
| E | Seed | P2↔P3 total | Strong | — | — | +++ (failure loops) | summary schema | A/G reasoning |
| F | Seed | Reader framing | Strong | +1x P1 | — | + (arbitrate) | parallel dispatch | DMAD + double-blind |
| **I** | Seed | All edges generalized | Strong | — | — | — | schema + file split | **DV discipline "almost verbatim"** |
| J | Seed | Discovery-time | Very strong | — | — | ++ (per ambiguity) | escalation flow | Adversarial-collab escalation |
| K | Seed | P3-internal statistical | Moderate | — | +(N-1)x P3 | + (arbitrate) | convergence check | Many Labs replication |
| M | Analysis | Schema-bounded | Maximal | — | — | — | schema design | — |
| N | Analysis | Temporal (commit) | Strong | — | — | — | read-hook | — |
| O | Analysis | Authorization-level | Very strong | — | — | +++ (synchronous) | Q&A flow | — |
| P | Analysis | Reader specialization | Strong | ~1.5x P1 | — | + (merge) | two agent defs | — |
| Q | Analysis | P2↔P3 rationale-bounded | Strong | — | — | — | file split + prompt | — |
| **R** | R2 lit | P2 generation decoupled | Strong | — | — | — | guide-word list | **HAZOP** |
| S | R2 lit | Cross-slice priors | Weak | — | — | — | dispatch routing | Red-team rotation |
| **T** | R2 lit | P1↔P2 disposition | Moderate | — | — | — | agent-prompt edit | **Mellers 2001** |
| **U** | R2 lit | P3 mechanical | Maximal | — | — | — | store + access-control | **SWIFT post-Bangladesh** |
| V | R2 lit | Reader-framing via corroboration | Strong | +1x P1 | — | + (arbitrate) | parallel dispatch | DO-178C dissimilar software |
| **W** | R2 lit | P3↔P4 | Maximal | — | — | — | new artifact | **Camerer 2018 — top predictor** |

**Reading the table.** "—" means negligible incremental cost over current baseline; "+" means small; "++" moderate; "+++" high. Costs compound across composites.

### 6.13 R4 observations (refined with R1/R2/R3 findings)

**Cross-referenced with literature and internal evidence:**

- **Shape B is consistently classified as anti-pattern.** R2 six-domain survey: purple-team model, the closest non-LLM analog to Shape B, "deliberately sacrifices independence → produces training value, not assessment value." Academic literature (preference leakage, monoculture collapse) further validates. R3: zero cairn slices use intent-level enumeration — it's already disfavored in practice. **Recommendation: Shape B alone is non-viable for a firm decision. If enumeration is needed, Shape D or I (split with read asymmetry) subsumes it.**

- **Shape I has the strongest literature match.** R2: "almost verbatim the DV discipline" — hardware verification has enforced P3-blind-to-spec as coverage-engineering standard for two decades with measurable bug-escape reduction (Foster FV Trends surveys). R1: LangGraph's partitioned subgraph state is first-class primitive, near-exact Shape-I analog.

- **Shape D has the broadest cross-domain validation (6 domains).** DV blind to RTL, maker-checker independent retrieval, red-team blind to blue rules, Claude Code subagents, LangGraph subgraphs, OpenAI Swarm explicit handoff. R3 internal evidence: SLICE-003-precursor's "don't load approach.md" is proto-D. **Likely the right starting point for first-landing provisional.**

- **Shape U dominates Shape D strictly on enforcement but not on cost.** Post-Bangladesh SWIFT discipline: asymmetry enforced at the read interface, not by sender compliance. Strongest guarantee. Highest infrastructure. **Upgrade path from D → U makes sense empirically.**

- **Shape A has the strongest internal empirical backing.** R3: SLICE-003-precursor ran clean. R2: HAZOP top-down framing + contract-first discipline. **Internal evidence is 1/1 clean vs 1/1 F2-positive when enumeration present.** Small n, strong direction.

- **F2's sibling L-003 has existing cairn mitigation.** R3 surfaced that cairn has already experienced and mitigated candidate-set-leakage at the Phase 4→5 boundary (index-row pre-anchoring, fixed via phase-commit splitting). The F2 problem is not novel; only this instance at Phase 2→3 is.

- **Tomkins 2017 (PNAS) provides empirical base rate: 1.76× bias from single channel leakage** in randomized-controlled human-reviewer trial. Strong prior that LLM agents will leak at similar or higher rates absent mechanical asymmetry.

- **Shape R (HAZOP guide-words) addresses F2 at the generation step, uniquely.** All other shapes prevent propagation of an already-formed candidate set. Shape R prevents the set from forming in the first place. Composes orthogonally with D/I/U.

- **Shape W (pre-registered success criteria) targets the P3↔P4 boundary specifically.** Camerer 2018: single largest predictor of replicability in social science. Cairn's P4 auditor reads P3's implementation + P3's own notes; anchoring is plausible. Cheap to add, defense-in-depth.

- **The project-defining lower-level structural move the operator asked for** most plausibly lives in Shape D/I/U (artifact-topology asymmetry) + Shape T (dispositional asymmetry in P2) + Shape W (pre-registration to break P4 anchoring). **D+T+W is a composite that attacks all three independence edges (P1↔P3, P1↔P2, P3↔P4) mechanically.**

- **Cairn's asymmetric-reads stance is empirically vindicated by 2025 academic work** (preference leakage, MAST taxonomy, DMAD) but has no production-tool peer. Cairn would be in novel territory on Shape A/E specifically; D/I/U have analogs (LangGraph, DV, SWIFT).

---

## 7. R5 — Decision-calibration meta-research

### 7.1 Is `/decision` protocol sufficient?

Per `commands/claude-code/decision.full.md`, `/decision` has 6 phases:

- **Phase 0 — Constraint Harvest**: read ARCHITECTURE.md, adr/index.md, relevant ADRs, lessons.md. Produce constraint envelope with citations.
- **Phase 0.5 — User-Journey Trace**: every session/artifact/state boundary must have a mechanism. Gaps are failure scenarios.
- **Phase 1 — Pre-Mortem**: ≥3 failure scenarios (technical, scale, integration).
- **Phase 2 — Forced Enumeration**: ≥3 genuinely viable approaches with evidence from files, not memory.
- **Phase 3 — Adversarial Stress Test**: disconfirming search, steel-man runner-up, assumption audit.
- **Phase 4 — Decision Record**: ADR via `/new-adr`.
- **Phase 5 — Independent Verification (firm only)**: fresh subagent reruns Phases 1-3 without prior reasoning.
- **Phase 6 — Propagation**: `/refresh-architecture`, lesson recording, ADR supersession.

**Assessment.** The protocol is robust for ADR-class decisions. Phase 5 already mandates independent verification for firm decisions — aligns with operator's Q2 answer. Phase 2's "evidence from files, not memory" + "≥3 viable approaches" discipline prevents the common shallow-decision failure mode.

**What's potentially insufficient for project-defining weight:**

1. **Phase 5's single-session verification may be insufficient for decisions that shape future phase contracts.** The verification subagent reads only constraint envelope + ARCHITECTURE.md + ADRs — it does NOT read the research doc. For project-defining decisions, a verification that doesn't see the research base may miss evidence-based considerations.

2. **Phase 2's enumeration floor (≥3) is a minimum, not a ceiling.** For project-defining decisions, we already have 14 shapes (A, B, C, D, E, F, I, J, K, M, N, O, P, Q) plus composites. The discipline is ensuring all are evaluated, not hitting the minimum.

3. **No explicit "sweep after N slices" mechanism.** A firm decision landed here shapes every subsequent slice. If the chosen shape turns out wrong at slice 5, reverting is expensive. Some decisions benefit from landing provisional, running through several slices under the chosen shape, and upgrading to firm only after empirical validation.

4. **The protocol does not currently require a research-phase document.** Phase 0's "constraint harvest" is lightweight vs. the R1-R5 scope this research doc undertakes.

### 7.2 Recommended augmentations for project-defining weight

1. **Land provisional-first with explicit upgrade criteria.** Don't fire `firmness: firm` on the first ADR. Use:
   ```
   firmness: provisional
   upgrade-to-firm-when:
     - N slices have shipped under the chosen shape
     - <= K escalations per feature observed
     - Phase 5 verification (when firm) passes on first pass
   ```
   This inserts an empirical gate between decision and ceremony.

2. **Research doc as an explicit Phase 0 input.** This research doc (R1-R5) becomes a read-only input to Phase 0 constraint-harvest. Phase 5 verification gets an amended input set: {constraint envelope, ARCHITECTURE.md, relevant ADRs, **this research document**}. Not doing so means verification can't leverage the work that has been done.

3. **Two-reviewer Phase 5.** For project-defining decisions specifically, Phase 5 runs twice with different system-prompt seeds. Strong correlated-error defense analogous to Shape F. Cost: additional +1x Opus. Justified by decision weight.

4. **Pre-commit dogfood.** Before the ADR lands firm, dogfood the chosen shape on ONE slice and collect empirical data on its behavior. `compression/slice-C` becomes a natural dogfood target.

### 7.3 Firmness recommendation

**Provisional-first, upgrade path explicit.** Rationale:
- Operator's Q2 ("mandatory Phase 5 when firm") implies firm upgrade triggers significant cost. Don't trigger that cost until empirical validation warrants.
- Cairn's pattern on recent decisions (e.g., INV-009 advisory-at-introduction) supports provisional-then-firm staged adoption.
- Project-defining decisions are precisely the ones where first-pass confidence is weakest — the reason they're heavy is the consequences are large, not because the answer is obvious.

**Upgrade criteria recommendation (to be ratified by operator in /decision Phase 0):**
- At least 3 slices have landed under the chosen shape without F2-pattern recurrence.
- Operator has observed one full close cycle (sweep + handoff) under the chosen shape.
- No amendment-required escalation ran outside the per-feature escalation budget.
- If shape requires new infrastructure (hook, schema): infrastructure has been committed and exercised by at least 2 slices.

### 7.4 Evidence-sufficiency rubric

Before firing `/decision`, the following evidence should be assembled (roughly — R1/R2/R3 are shaping the thresholds):

| Stream | Minimum evidence | Nice-to-have |
|---|---|---|
| R1 External frameworks | 4+ frameworks surveyed with citations | Published findings on correlated-error rates |
| R2 Non-LLM literature | 3+ domains with cited empirical studies | Quantitative base rates |
| R3 Cairn-internal | Either evidence of F2 with slice-id citations OR confident null result | Clean-slice pattern characterization |
| R4 Shape-space | Full A-K + new shapes + composites | Infrastructure cost estimates per shape |
| R5 Decision-calibration | Firmness recommendation with rationale | Upgrade-path specification |

**Go condition:** all five streams have at least minimum evidence; operator has reviewed; recommendations are coherent.
**No-go condition:** any stream is thin enough that `/decision` would decide on correlated-model memory rather than research-grounded evidence.

### 7.5 Project-defining vs routine

A decision is project-defining if:
- It changes what cairn's phase-role contract means (e.g., what P3 reads).
- It affects multiple invariants simultaneously.
- Reverting it requires cascading amendments across ≥3 existing ADRs or slices.
- Downstream slices cannot proceed without the decision landed.

All four apply to this candidate-set discipline decision:
- Phase-role reads change (D, E, I, N, Q all touch this).
- Invariants affected: cliff-failure-mode, phase-artifact-immutability, phase-lock-and-role-declaration (potential amendment of).
- Revert cost: every slice using the chosen shape embeds the shape in its artifacts.
- Downstream blocked: Slice C is explicit; other sibling slices reference this decision.

**Project-defining decisions benefit from heavier process.** The augmentations in §7.2 are proportionate.

---

## 8. Operator digest

> **Note (2026-04-24 post-review):** §8 was written assuming F2-prevention as primary axis. Operator critique identified that the goal is **per-feature context reduction**, with F2-prevention as a constraint. §10 supersedes §8.2's recommendation (D+T+W) for the cost-reduction objective. Read §8 for the F2-prevention analysis; read §10 for the revised recommendation.

### 8.1 What the evidence actually says

Three independent evidence streams converged on the same ranking:

1. **Shape B is non-viable for firm adoption.** R2 non-LLM literature: its closest analog (purple team) is consistently classified as training-value-only, not assessment. R1 academic: preference-leakage paper (arXiv:2502.01534) directly formalizes the failure mode. R3 internal: zero cairn slices currently use intent-level enumeration. Shape B should not be in the firm-decision shortlist.
2. **Artifact read-asymmetry (Shapes D/I/U) has overwhelming cross-domain support.** Six non-LLM domains converge on read-asymmetry as the load-bearing mechanism: DV (verbatim), maker-checker, red-team, formal A/G, scientific replication, HAZOP leader non-involvement. LangGraph provides a first-class primitive. Cairn's own clean-case (SLICE-003-precursor) used a proto-D pattern.
3. **Correlated-error has an empirical base rate of at minimum 1.76× in a single-channel randomized trial (Tomkins PNAS 2017).** Without mechanical asymmetry, reviewer independence is performative (Hannay 2009 meta-analysis). Role labels alone do not produce independence.

### 8.2 Top candidate shapes (ranked)

1. **D+T+W composite (Recommended primary):** asymmetric file reads (D) + adversarial P2 priors (T) + pre-registered success criteria (W). Attacks all three independence edges (P1↔P3, P1↔P2, P3↔P4) mechanically. D is instruction-layer; T is agent-prompt-layer; W is artifact-layer. Combined infrastructure: one new file (`candidate-sets.yaml`), one agent-prompt revision (P2 + P3), one new committed artifact type (success criteria per slice). Low implementation cost; high leverage.
2. **I (Three-tier spec, standalone):** strongest pure-literature match (DV discipline). Larger schema investment. Candidate if the ADR wants generality over multiple constraint classes beyond candidate-sets.
3. **D (Asymmetric reads, standalone):** cheapest first move; literature-backed; internally precedented. Candidate for provisional-first adoption, upgrade to I or U after empirical validation.
4. **U (Independent-retrieval handoff):** strongest mechanical guarantee but reopens phase-lock-and-role-declaration's instruction-over-enforcement stance. Candidate for firm-upgrade path, not first-landing.
5. **A (Contract-only tests) + operator escalation:** strongest *internal* empirical backing (SLICE-003-precursor). Lowest infrastructure — purely a P2 discipline. Candidate if operator prefers "no new file machinery, discipline via agent-prompt edits alone."
6. **R (HAZOP guide-words):** unique among all shapes for preventing candidate-set from forming at generation step. Composes with everything. Candidate as an orthogonal addition to whichever primary is chosen.

### 8.3 Recommended `/decision` framing

```
/decision

Question: How should Cairn structure phase-role artifact reads and P2 test
generation to mechanically prevent F2 candidate-set leakage across the
Phase 2 → Phase 3 boundary, and to prevent analogous anchoring at the
Reader (A2) and Auditor (P3→P4) boundaries?

Seed shape space (20 shapes enumerated in research doc): A, B, C, D, E, F,
I, J, K, M, N, O, P, Q, R, S, T, U, V, W plus composites.

Primary recommended composite: D + T + W
Primary recommended standalone: D (provisional, upgrade-path to I or U)
Excluded from firm shortlist: B (anti-pattern per R2)

Primary target: F2 candidate-set leakage at Phase 2 → Phase 3.
Secondary targets: A2 Reader-framing correlated error (Phase 1 ↔ Phase 2/3),
P3→P4 self-reporting anchoring.

Firmness target: provisional on first landing; upgrade to firm after:
  - 3 slices ship under chosen shape without F2 recurrence
  - no per-feature escalation budget exceeded
  - Phase 5 verification passes on first attempt

Constraint citations:
  - docs/adr/phase-lock-and-role-declaration.md (firm — instruction over enforcement)
  - docs/adr/cliff-failure-mode-and-v1-defenses.md (provisional — primary target)
  - docs/plans/2026-04-18-session-compression-audit.md:22 (F2 finding)
  - docs/lessons.md: L-003 (phase-commit splitting precedent),
    L-004 (reused-structure risk), L-007 (framing-doc inheritance),
    L-008 (context pressure → deviation)
  - Part 0 ADR (pending — phase-artifact-immutability-and-evidence-persistence)

External citations for empirical grounding:
  - Preference Leakage (arXiv:2502.01534) — direct F2 formalization
  - MAST taxonomy (arXiv:2503.13657) — verification-failure as formal category
  - Tomkins/Zhang/Heavlin PNAS 2017 — 1.76× base rate for single-channel leakage
  - Camerer et al. Nature Human Behaviour 2018 — pre-registration as top replicability predictor
  - Hannay et al. IST 2009 — cognitive convergence in shared-context review
```

### 8.4 Unknowns for `/decision` to resolve

Beyond selecting the shape composite, `/decision` must determine:

1. **Exact D3 rewording for Part-0 ADR.** Under Shape D/I/U, candidate-sets live in a different file; D3's "must cite intent.md line" becomes cross-file citation.
2. **Does `candidate-sets.yaml` become mandatory per slice, or conditional on P1 declaring ambiguities?** (Relates to Shape-J/-O interaction.)
3. **What's the specific Shape-T adversarial-prior prompt?** Agent-prompt-layer design for P2.
4. **Shape-W success-criteria format:** test-suite-subset, YAML-structured, or free-form operator-authored?
5. **Phase 5 verification protocol when firm:** fresh-Skeptic re-reads intent (+ candidate-sets, if Shape D/I) and re-writes tests; what are the divergence-as-evidence criteria?
6. **Read-enforcement (Q6 already answered "instruction-only at first"):** telemetry for detecting violations.
7. **Escalation budget format in feature.yaml** (Q3 answered "complexity-gated"): concrete field and operator-set defaults.

### 8.5 Go/no-go signal

**GO.** All five research streams returned with minimum evidence:

- R1: 8 frameworks surveyed + 5 academic papers cited ✓
- R2: 8 non-LLM domains with load-bearing citations + empirical base rates ✓
- R3: F2 confirmed in 1 slice with commit-level evidence, 1 clean contrast, 4 adjacent lessons ✓
- R4: 20 shapes characterized across 6 properties, comparison table, composability analysis ✓
- R5: `/decision` protocol sufficient with three recommended augmentations; firmness recommendation crisp ✓

Evidence is coherent; recommendations converge. Proceed to `/decision` with this research doc as Phase-0 input.

### 8.6 Augmentations recommended alongside `/decision` invocation

From §7.2, applied to this specific decision:

1. **Provisional-first with explicit upgrade criteria** — baked into framing above.
2. **This research doc as Phase-0 input** — explicit addition to standard `/decision` protocol for project-defining weight.
3. **Two-reviewer Phase 5** — when upgrading to firm, run Phase 5 twice with perturbed system prompts. Addresses Shape-F-level Reader-framing correlated error at the verification step itself.
4. **Pre-commit dogfood** — compression/slice-C becomes the dogfood slice under the chosen shape before ADR upgrade to firm.

---

## 9. Open questions for /decision itself (running list)

1. If Shape D (or composites including D) wins, what's the exact rewording of Part-0-ADR D3?
2. If Shape I wins, what's the initial `spec.yaml` schema? Who governs its evolution?
3. If Shape J or O wins, how does the orchestrator handle synchronous operator availability constraints?
4. If a dispatch-layer shape (E, F, K, P) wins, what are the new role-guard surface implications?
5. What's the specific sweep-after-N criterion for upgrading provisional → firm?
6. Should `candidate-sets.yaml` (under Shape D/I variants) be mandatory-per-slice or optional-when-authorized?
7. Interaction with Phase 5 verification: if mandatory, what's the minimum viable Phase 5 protocol for slices under the chosen shape?

---

## 10. Context-reduction reframe (post-§8 critique, 2026-04-24)

### 10.1 What sections 1-10 missed

§1.3's stated literature context flagged that "over-contextualized phases are BOTH more expensive AND lower-quality" and §1.4 recorded operator's Q1 answer asking for a "lower-level structural change." But the shape-space analysis in §6 and the digest in §8 optimized for "prevent F2 + preserve auditability" with cost as a balanced constraint. **They did not optimize for total per-feature context reduction.**

Operator critique (2026-04-24, post-research-review): every recommended shape either holds total context flat or increases it. The actual goal — features eating fewer tokens and less time — requires shapes that **decrease** context, not just shapes that prevent anchoring.

### 10.2 Revised constraint mix (operator-confirmed)

Both **independence** and **cost reduction** are soft constraints; neither is absolute. Shapes are ranked by tradeoff, not by independence-preserving filtering. This explicitly opens shapes that weaken independence in exchange for material cost savings — most importantly Shape Y (phase-skip on declared triviality), which the prior framing ruled out.

### 10.3 Shape ranking by context-cost direction

**Decrease total context:**
- **M (intent kernel quantization)** — strict YAML kernel ~500 tokens vs current prose intent ~2000. Cuts ~1500 tokens × N reading phases per slice. Single largest context-volume win in the seed+analytical space.
- **A (contract-only tests)** — IF behavioral tests are systematically smaller than enumeration tests. Marginal, depends on test verbosity.
- **D (asymmetric reads)** — total slice context ≈ unchanged, but P3's read shrinks because `candidate-sets.yaml` is hidden from P3. Per-phase compression even without total-volume change.

**Hold roughly flat:**
- B, C, S, T, U, W — structural without volume change at the artifact level.
- Q (kernel + exhaust) — splits volume across files but doesn't reduce total.

**Increase context:**
- E (RE_DISPATCH loops), F (2x P1), I (more files, larger schema), J (escalation accretion), K (N-1 extra builders), O (Q&A grows), P (~1.5x P1), V (2x P1).

### 10.4 New shapes designed for context reduction

**Shape X — Distilled handoff at every phase boundary.** Each phase produces full output AND a ≤N-token distillation. Next phase reads only the distillation + protocol-mandated artifacts. **Hard cap on context cumulation across phases.** Critical constraint: distillation must be **mechanical/schema-extraction**, not generative-LLM, otherwise the distiller introduces shared-reasoning surface (an independence violation, not a cost win). Schema design upfront; dispatch logic carries distillation alongside full output.
- **Independence:** preserved IF distillation is mechanical. Violated if distillation is LLM-summarization.
- **Cost:** large reduction — caps per-phase read regardless of slice complexity.
- **Failure modes:** X1 — schema can't capture all relevant content; mechanical extraction loses signal. X2 — phases over-rely on distilled view and miss content needed for correctness.

**Shape Y — Phase-skip on declared triviality.** P1 intent kernel includes a `triviality:` field; if declared trivial (zero material ambiguities, no firm-invariant touched, additive-only change), trivial slices skip P2 antagonism and run with a reduced agent set (P1 → P3 → light P4 instead of P1 → P2 → P3 → P4). **Concedes independence at the trivial tier in exchange for ~25-50% slice cost reduction.** Trivial-slice escape hatch was already raised in cost-discipline brainstorming as Track B.
- **Independence:** explicitly weakened on trivial slices. Preserved on non-trivial.
- **Cost:** large reduction on trivial slices; zero on non-trivial.
- **Failure modes:** Y1 — slice is mis-declared trivial, ships an F2 incident. Recovery: post-hoc detection in /sweep + amendment. Y2 — operator pressure makes "trivial" too elastic; trivial designation accretes to non-trivial work.

**Shape AA — Context-distiller skill.** Already in efficiency-program roadmap (`00-program.md:42`). Service-call between phases. **Same independence constraint as X — only safe if mechanical extraction; LLM-summarization breaks independence.** Implementation as Skills-style helper rather than agentic handoff.

**Shape BB — Hard token-budget per phase, enforced at write-time.** Each phase has a hard output-token cap declared in the agent prompt; agent must produce within budget. Compression at generation, not at consumption. Cleaner failure mode than truncation (agent retries within budget rather than mid-thought cut).
- **Independence:** orthogonal — doesn't touch read graph.
- **Cost:** moderate reduction by capping output growth.
- **Failure modes:** BB1 — budget too tight, agents under-deliver. BB2 — budget too loose, no actual compression.

**Shape CC — Read-set audit and pruning** (methodology, not structural shape). Audit each phase agent's actual read surface against actual usage. Trim loaded-but-unused content. Continuous optimization, not a one-shot structural change. **This is the work the compression-audit follow-on (§12, separately) will do.**

### 10.5 Revised composite recommendations

Three composites worth landing under the revised constraint mix:

**Primary — M + D + BB (context-reducing F2 defense, independence preserved):**
- **M** quantizes intent → biggest single context drop across all phases.
- **D** asymmetrizes reads → P3 reads less, F2 prevented at structural level.
- **BB** caps output growth → bounds phase-volume drift over time.

Combined infrastructure: schema for intent kernel; one new file (`candidate-sets.yaml`); agent-prompt revisions for read-scoping (P3) + output budgets (all four phases). Estimated context reduction: 30-50% on intent-prose alone (M); marginal-to-zero on shared reads of ARCHITECTURE.md/ADRs (the §12 audit will quantify).

**Aggressive — M + D + Y + BB (max cost reduction, accepting trivial-tier independence loss):**
- Adds **Y** to skip P2 on declared-trivial slices.
- Cost reduction: estimated 25-50% on trivial slices, 30-50% on non-trivial (from M+D+BB intent-prose savings alone).
- Independence cost: explicit on trivial slices, none on non-trivial.

**Distillation — M + D + X + BB (cap context cumulation explicitly):**
- Adds **X** distilled-handoff requirement at phase boundaries.
- Distillation must be mechanical; schema-extraction.
- Hardest implementation of the three — schema design is upfront work.
- Largest cost ceiling — context per phase capped regardless of slice complexity.

T (adversarial P2 priors) and W (pre-registered success criteria) from §8 remain available as cost-neutral independence-defense additions to any of these composites. They don't reduce context but don't increase it either.

### 10.6 Revised `/decision` framing

```
/decision

Question: How should Cairn structure phase-role artifacts, reads, and
output budgets to MECHANICALLY REDUCE per-feature token-and-time cost
while preserving independence-of-re-derivation as a soft constraint
(weakening allowed where cost gain is material) and not regressing
auditability?

Primary axis: context reduction per slice (measured in total tokens
read across all phases).
Secondary axis (soft constraint): independence-of-re-derivation.
Tertiary axis (soft constraint): auditability.

Excluded from firm shortlist:
- B (anti-pattern per R2 §4.1 purple-team analog)
- All shapes that explicitly increase context: F, I, J, K, O, P, V

Primary recommended composite: M + D + BB
Aggressive option: M + D + Y + BB (accepts trivial-tier independence loss)
Cap-context option: M + D + X + BB (mechanical-distillation handoff)

Firmness target: provisional on first landing; upgrade to firm after:
  - 3 slices ship under chosen shape with measured context reduction ≥30%
  - no F2 recurrence in any of those 3 slices
  - no per-feature escalation budget exceeded
  - Phase 5 verification passes on first attempt

Constraint citations:
  (as in §8.3 — unchanged)

External citations adding context-reduction grounding:
  - 2,500-token quality cliff (§1.3 — over-contextualized phases lower quality)
  - Lost-in-the-middle (§1.3 — accuracy drops >30% mid-context)
  - Hierarchical multi-agent 97.7%/61% cost (§1.3)
  - Agentic SDLC 86% token concentration in code-review/completion (§1.3)
```

### 10.7 What §8's recommendation got wrong

§8.2 ranked **D+T+W** as primary recommendation. Under the original framing (prevent F2 + preserve auditability + balance cost), this was internally consistent. Under the revised framing (context reduction as primary axis), D+T+W is wrong because:
- **T (adversarial P2 priors)** is cost-neutral, not cost-reducing.
- **W (pre-registered success criteria)** adds a new committed artifact — net flat or slightly increasing.
- Neither addresses the intent-prose-volume issue, which is the largest single context cost.

§8 should be read as F2-prevention analysis. §10 supersedes it for the cost-reduction objective. Both are valid decompositions; the operator's actual question matches §11.

### 10.8 Unified structural primitive — operator-confirmed direction

**Operator critique (2026-04-24, post-§10.6):** the M+D+BB composite is still a multi-part trade. The right direction is a **single structural move** that handles both context-reduction AND independence-preservation simultaneously, because they are not actually in tension — *the shared surface IS the context volume that propagates across phases*. Less shared surface = both cheaper AND more independent. They are aligned axes.

**Mechanical observation grounding the primitive.** Current cairn agent definitions (`.claude/agents/phase-{1,2,3,4}-*.md`) declare only WRITE surfaces (`Writes: ...` line per agent; enforced via `role_guard.py` PreToolUse hook). READ surfaces are ad-hoc — agents use Read/Grep/Glob freely against whatever's in the working tree. This asymmetry is the leverage point: write-side discipline already exists; **read-side discipline is the unbuilt half of the contract**.

#### The primitive: declared per-phase READ envelope

Each agent definition gains a `Reads:` field listing:
- Specific paths the phase MAY read (with size caps per artifact, expressed as max-token or max-byte budgets).
- A "default projection" for large shared artifacts (ARCHITECTURE.md, ADRs) — phase-specific subsets, not the full file.
- An explicit denylist for paths the phase MUST NOT read (the F2-prevention surface — e.g., P3's denylist includes `.claude/current-slice/candidate-sets.yaml` if Shape D is layered on).

Enforcement, per Q6 commitment: instruction-only at first landing. Telemetry tracks read-violations. PreToolUse Read-hook is a later upgrade if violations accumulate empirically.

#### Why this is one move, not three

Compare to the M+D+BB composite §10.5 proposed:
- **M (intent kernel)** is one form of "the artifact this phase reads is bounded." Strict-read-envelope subsumes it: just declare `intent.md: max-tokens 500`, kernel-form-required.
- **D (asymmetric reads)** is one form of "different phases read different paths." Strict-read-envelope subsumes it: P3's `Reads:` excludes `candidate-sets.yaml`.
- **BB (per-phase output budget)** was the cost-control half. Strict-read-envelope is the *input-control* half — and input is where independence and cost are actually shared. Output budget can stay as a separate complementary discipline, but it's not the structural lever.

Strict-read-envelope is the *generative* primitive that makes M, D, and dozens of similar moves trivial special cases. Each future "phase X should read Y less" gets expressed as an envelope edit, not a new ADR.

#### How this wins on both axes simultaneously

| Axis | Mechanism |
|---|---|
| **Context reduction** | Per-artifact size caps in the envelope; phase-specific projections of large artifacts; default-deny what's not listed. Hard ceiling on per-phase read volume. |
| **Independence (F2-prevention)** | Anything that would create shared-reasoning surface between phases (e.g., candidate-sets) is excluded from downstream phases' envelopes. Mechanical separation, not instruction. |
| **Independence (A2-style framing)** | Phase 1's read envelope excludes prior-phase artifacts; Phase 4 sees only what's needed for audit, not P3's notes. Configured per-edge. |
| **Auditability** | Envelope itself is a committed artifact (in agent definitions, version-controlled). Audit checklist becomes mechanical: "did this phase read only its envelope?" telemetry-verifiable. |
| **Quality (2,500-token cliff)** | Size caps keep every phase under the cliff by construction. |

#### Composability

The strict-read-envelope primitive composes with:
- **Shape T (adversarial P2 priors)** — orthogonal; agent prompt-layer change, doesn't touch envelope.
- **Shape W (pre-registered success criteria)** — adds an artifact; success-criteria.yaml is just another envelope entry for P4.
- **Shape R (HAZOP guide-words)** — methodology in P2 agent prompt; envelope unchanged.
- **Shape Y (phase-skip on triviality)** — orthogonal at orchestrator-dispatch level; envelopes are per-phase, dispatch decides which phases run.
- **Shape AA (mechanical distiller)** — provides the projections that envelopes reference for large artifacts.

These remain available as orthogonal additions; the envelope primitive doesn't preclude any.

#### Failure modes of the primitive itself

- **DD1 — envelope ossifies.** Once declared, agents stop reasoning about read needs and follow envelope rotely. Recovery: telemetry on envelope-violation events surfaces under-specification.
- **DD2 — instruction-only enforcement violated.** P3 reads `candidate-sets.yaml` despite envelope. Recovery: empirical violation triggers Read-hook upgrade.
- **DD3 — projections become a maintenance burden.** Each large shared artifact needs a phase-specific projection that drifts. Recovery: mechanical-distillation generators (Shape AA) regenerate projections.

#### Revised primary recommendation

**Land strict-read-envelope as the unified structural primitive. Provisional firmness. Layer Shape T, Shape W, Shape R as orthogonal cost-neutral independence-defense additions if/when warranted. Defer enforcement upgrade to Read-hook (Shape U-style) until empirical violations justify it.**

This single primitive is what the operator's framing was pointing toward: not a tradeoff, not a composite — a structural change that defines what each phase reads, with simultaneously cheaper, more independent, and more auditable outcomes by construction.

### 10.9 What the compression audit (§12, follow-on doc) will do

The next research phase, dispatched separately, will:
1. Measure actual per-phase context volumes from `.claude/orchestrator-debug/` logs.
2. Map agent prompt prefixes (`.claude/agents/*.md`) and identify static vs dynamic portions.
3. Identify cross-phase redundancy (ARCHITECTURE.md re-read 4×, ADRs re-read N×).
4. Quantify the "waste portion" of the 4-6× baseline vs the "independence portion."
5. Propose concrete cuts with measured token savings.

§12 produces empirical grounding for sizing the cost reductions claimed in §11.

---

## 11. References

- `docs/plans/2026-04-18-session-compression-audit.md:45-49, :61-63` — source of shape A/B seeds and Part 0 ADR scope
- `docs/plans/2026-04-18-efficiency-program/00-program.md` — parent program
- `docs/plans/2026-04-23-cost-discipline-design.md` — recent design-doc style reference
- `docs/adr/phase-lock-and-role-declaration.md` — firm constraint on instruction-vs-enforcement
- `docs/adr/cliff-failure-mode-and-v1-defenses.md` — primary target citation
- `docs/adr/compression-infrastructure-bootstrap.md` — provisional, will be superseded
- `commands/claude-code/decision.full.md` — protocol reference
- `scripts/slice_orchestrator.py:1288-1303` — dispatch exemplar (Lever 1 splice pattern)
- `.claude/agents/phase-{1,2,3,4}-*.md` — current role-read-scoping instruction style
- `.claude/features/compression.yaml` — where Slice C will land post-decision
- `.claude/features/cost-discipline.yaml` — sibling feature (Lever 1 exemplar)

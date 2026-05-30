# Approach B — Lightened 4-phase (evolve, don't replace)

**Advocate brief.** Forced-enumeration Phase 2. I argue the strongest honest case for B, then name its real weakness. The lead adjudicates.

**Sourcing note:** `brainstorm-1-charter-cycle.md` and `landscape.md` are not in the repo (the brainstorm dir holds only `00-rejected-adaptive-pivot-exploration.md`); the charter-cycle shape and C1–C8 verdicts are taken as quoted verbatim in `01-constraint-envelope.md` §0/§4 and `02-journey-trace.md`. All `phase-pipeline-evaluation.md` and `phase-lock-and-role-declaration.md` cites are direct reads.

---

## B in one frame

**KEEP** the 4-phase pipeline, INV-003, and the two FIRM ADRs (`phase-lock-and-role-declaration`, `phase-pipeline-evaluation`) — **no firm-ADR supersession.** Apply phase-pipeline-evaluation's *own* ruling — "The right calibration is not fewer phases but lighter ceremony within phases" (`phase-pipeline-evaluation.md:50-51`) — by cutting dead weight, not phases:

1. **Delete the dead AGENT_ROLE machinery** (`02-journey-trace.md:15` — `role_guard.py:137` reads it; injected nowhere; confirmed dead code, F5). This is the unambiguous ceremony cut: a safety property the design *claims* but doesn't have.
2. **Simplify SKILL.md** — strip the heavy per-phase commit-gate prose to the load-bearing minimum.
3. **(Optional) Move per-phase dispatch from fresh SESSIONS to named foreground SUBAGENTS** — preserving the four cognitive cleaves and equivalent isolation. Arc A's verdict (per `00-lead-findings.md:10`): foreground + named + capped subagents preserve isolation + role-purity. The A2 canary backs this empirically (below).
4. **ADD the charter/intent-file primitive** (`goal:`/`done:`/`constraints:`/append-only `amendments:` + amendment protocol) as a **lightweight front-end to Phase 1** — NOT a replacement for the phases. The `done:`/`constraints:` lineage + append-once policy salvaged from `slice-intent-contract` (`01-constraint-envelope.md:35` P2 salvage) resurface here, where they belong: one durable Phase-1 artifact, not a four-phase collapse.

**Supersede only the 2 PROVISIONAL ADRs** (`slice-intent-contract`, `identity-and-scope-deferral`). Zero firm supersession. Zero INV-003 retirement.

**Identity:** the **cliff thesis stays the headline.** Goal-commitment-vs-reactivity is a **scoped SUB-CLAIM** — a Phase-1 hardening, positioned per `cliff-failure-mode-and-v1-defenses` D0 (`01-constraint-envelope.md:38` P5) as a cliff-COMPONENT, not a co-equal rival target.

---

## 1. The case — why evolving the proven pipeline beats replacing it

### The decisive evidence is a FIRM ADR that already ran this experiment and ruled for B

`phase-pipeline-evaluation` (FIRM, 2026-04-13) is not a prior; it is the **verdict of a completed 5-slice evaluation** of exactly the question this arc re-opens. Its findings:

- **"The four phases remain correct. The phase names are load-bearing"** (`phase-pipeline-evaluation.md:25`). Four distinct cognitive modes "resist compression" — and the ADR shows *why* each boundary carries weight: Intent must be separated from Validation to keep the correlated-error defense; Validation from Implementation because "the Skeptic's independence from implementation reasoning is the core defense property"; Integration is a terminal audit gate "with different incentives than the Builder" (`phase-pipeline-evaluation.md:27`).
- **The ceremony fix is named, and it is B's thesis verbatim:** "The temptation is to allow skipping phases for 'simple' work. The evidence argues against this... **The right calibration is not fewer phases but lighter ceremony within phases**" (`phase-pipeline-evaluation.md:49-51`). The ADR even states the structure *already permits* this: "nothing mandates a minimum test count or a minimum Phase 3 implementation size" (`:58`).
- **The roles are non-vacuous across work types** — demonstrated on code (dogfood-evaluator) AND non-code (protocol-doc slice, 4-ADR design slice) work, with the Auditor catching cross-slice contamination even in non-code work (`phase-pipeline-evaluation.md:38-46`).
- **INV-003 is reaffirmed** on this evidence (`phase-pipeline-evaluation.md:104`).

This is empirically supported, not asserted. The lead's own synthesis concedes the point: phase-pipeline-evaluation "is the heaviest counter-evidence (and it backs comparator B)" (`00-lead-findings.md:8`). **The charter cycle proposes to supersede the one FIRM ADR whose explicit, evidence-backed finding is "do exactly what B does."** That is the structural fact the lead must weigh: A discards a 5-slice empirical result to chase an unmeasured one.

### The A2 canary independently proves the session boundary IS the isolating mechanism

The single load-bearing belief under the four-phase lock is A2: the Phase 1→Phase 2 boundary prevents smuggled implementation reasoning (`phase-lock-and-role-declaration.md:192`). It was committed FIRM with a **mechanical tripwire** and no operational evidence — an honest bet. The bet has now been *paid off*:

> **"A2 tripwire status: NOT FIRED."** ... **"0 of 5 slices in the current window show design token leakage from intent to approach. The A2 canary has not fired. The Phase 1→Phase 2 session boundary is providing the isolation phase-lock-and-role-declaration assumed."** (`phase-pipeline-evaluation.md:74,84`)

This is the empirical keystone. The boundary that separates the cognitive modes **demonstrably isolates** — 0/5, measured against a falsifiable canary. Arc A's finding that *foreground named capped subagents* preserve the same isolation (`00-lead-findings.md:10`) means B can take the optional dispatch-modernization (#3) without sacrificing the property the canary validated. **B keeps the mechanism that has 5 slices of green evidence. A trades it for a re-injection hook that does not exist** (`02-journey-trace.md:13`, Gap 1) **and a one-lead orchestration whose C3 isolation is explicitly un-re-verified** (`01-constraint-envelope.md:19` F5).

### The convergence argument — B is what A becomes once you strip the overclaim

The lead's F2 is the hinge: the charter cycle does NOT actually drop the cognitive cleaves — "charter-formation=Intent; skeptic-worker=Validation/test-first; build-worker=Implementation; verify-worker=Integration/Auditor with build≠check" (`00-lead-findings.md:10`). It replaces the *machinery* (session-boundary ceremony, AGENT_ROLE, per-phase commit gates, fixed SKILL.md) with subagent dispatch + charter. The lead's exact words: **"'Phases-out' oversells; 'machinery-out, cleaves-preserved-via-subagents' is the honest claim. → A and B may CONVERGE"** (`00-lead-findings.md:10`).

If A and B converge on the cleaves and differ only on machinery-and-framing, then B is strictly the lower-risk path to the same place: it gets the machinery cut **without** the firm supersession, the INV-003 retirement, or the unmeasurable identity claim. B is not the conservative alternative to A's redesign — **B is A's honest payload minus A's overclaim.**

---

## 2. Constraint fit — the firm envelope is SATISFIED, not superseded

B's defining property: because it preserves the INV-003 core, the firm constraints in `01-constraint-envelope.md` §1 that the charter cycle marks **REQUIRES-SUPERSEDING** are, under B, **SATISFIED**:

| Constraint | Under A (charter cycle) | Under B |
|---|---|---|
| F1 `phase-lock-and-role-declaration` (FIRM, owns INV-003) | REQUIRES-SUPERSEDING | **SATISFIED** — kept; AGENT_ROLE deletion is a D2-consistent ceremony cut, not a supersession (roles stay instructed, exactly as D2 already specifies them: `phase-lock-and-role-declaration.md:47-48`) |
| F2 `phase-pipeline-evaluation` (FIRM, INV-003) | REQUIRES-SUPERSEDING | **SATISFIED + VINDICATED** — B *executes* its `:50-51` finding |
| F3 `feature-slice-model` D0 (FIRM) | REQUIRES-SUPERSEDING (amend D0) | **SATISFIED** — slice→4-phase coupling untouched |
| F4 spec §2 dual-mechanism | SATISFIES *with caveat* — must argue the bet survives at lower phase-cardinality (4 boundaries → ~2; `01-constraint-envelope.md:18`) | **SATISFIED cleanly** — B keeps all four boundaries; no "survives at lower cardinality" argument needed |
| F5 spec §3 (subagents pollute parent on linear boundaries) | SATISFIES *with a live C3 attack* — one-lead return-channel accumulation un-re-verified (`01-constraint-envelope.md:19`) | **SATISFIED** — B's optional dispatch is foreground+named+capped per the arc-A provisos; and B can keep session boundaries entirely if C3 re-verify fails |

**The supersession cost of B is exactly two PROVISIONAL ADRs:**

- `slice-intent-contract` (provisional) — its Step-5.5-ceremony premise is the right thing to retire; its `done:`/`constraints:`/append-once lineage is **salvaged into the charter primitive** (`01-constraint-envelope.md:35`). Its "no LLM-judge" must-not-violate is preserved (no semantic mechanization — concordant with the closed validator-type whitelist, `01-constraint-envelope.md:107` F7).
- `identity-and-scope-deferral` (provisional) — superseded via its own validly-armed **D3.4** operator-directive trigger (`01-constraint-envelope.md:34` P1).

Against A's TRUE cost — **5 ADRs (2 provisional + 3 firm) + INV-003 retirement + ≥1 new invariant + the `validate_phase_topology` regex binding removed** (`01-constraint-envelope.md:54-66` §3) — B's blast radius is **the 2 the direction doc actually enumerated.** The lead's F1 finding ("Supersession scope is 5 ADRs + INV-003, not 2") is a critique of A's under-framed blast radius; it is simply **not a cost B pays.**

---

## 3. Pre-mortem exposure (`03-premortem.md` S1–S7)

### B STRUCTURALLY AVOIDS:

**S1 — the one-way door defended by prose (high × high, the pre-mortem headline).** S1's mechanism: the ADR "superseded 3 FIRM ADRs + retired INV-003, so the append-only cost is paid and irreversible," and the identity claim "now rests entirely on prose discipline" against an unmeasurable failure mode, so re-litigation "now need[s] to UNWIND 3 firm supersessions" (`03-premortem.md:29`). **B has no firm one-way door.** It supersedes 2 provisional ADRs (provisional = cheap to flip, by design). If goal-commitment-vs-reactivity proves unmeasurable, B walks it back as a Phase-1 refinement that didn't pan out — INV-003 and the firm pipeline are untouched. S1's "irreversible append-only cost paid on an unmeasurable hinge" is the pre-mortem's #1 risk **and it is the risk B was constructed to not take.** This is B's single strongest result.

**S3 — correlated-error rubber-stamp; verify certifies the builder's shared blind spot (high × med-high).** This is subtle and decisive. S3's finding: build≠check buys **role-purity, not error-decorrelation** — a same-model fresh-context reviewer shares ~60% weights-level blind spots with the builder (Kim et al.), and the charter cycle "collapses to one same-model blind verifier... strictly less decorrelation than the machinery it supersedes" (`03-premortem.md:37`, `:61`). **B keeps the full four-role pipeline including the session-boundary Validation≠Implementation cleave that the A2 canary shows actually decorrelates (0/5 leakage, `phase-pipeline-evaluation.md:84`).** The four cognitive modes give more independent surfaces for an error to be caught than one build≠check cleave does. The pre-mortem's own cross-cut is explicit: "the cycle has LESS decorrelation than what it supersedes" (`03-premortem.md:61`). **B is the more-decorrelation option, empirically.**

**Gap 6 / the in-cycle /decision collapse → reduces S2's compounding.** A's §7 nests a full /decision pipeline *inside* a work-cycle, which `phase-lock-and-role-declaration` **already rejected** as Approach C on the upstream-asymmetry principle: "decisions belong **upstream** of slices... not **inside** them" (`phase-lock-and-role-declaration.md:148`; trace Gap 6, `02-journey-trace.md:60`). B keeps the asymmetry — decisions run upstream via `/decision`, the slice consumes the landed ADR through the D3 `adrs-referenced` gate (`phase-lock-and-role-declaration.md:59`). **B does not re-introduce the rejected collapse**, so it does not pull decision-adversariality into the build window (the mechanism by which Gap 6 compounds S2, `03-premortem.md:65`).

**S4 reduced (concurrent `.claude/` corruption, L-019).** S4 is driven by *two* A-specific preconditions: a per-turn re-injection hook reading/writing charter state under concurrency, AND no per-worker write-scope (`03-premortem.md:41`). B's charter is a lightweight Phase-1 artifact, not a per-turn hook-emitted live-state file, so the hook-race vector (charter write races hook read → emits half-written goal) largely evaporates. The write-scope gap (Gap 2) is *shared* — see below.

### B SHARES with A:

**S2 — cross-cycle ADR↔code drift (high × high).** This is the honest one. The actual cliff (C1, residual leg #2) forms ACROSS the slice corpus over months — it "lives ABOVE any single subagent dispatch" (`03-premortem.md:33`). **Neither A nor B touches this**, because semantic ADR↔code alignment is architecturally unmechanizable under the closed validator-type whitelist (`01-constraint-envelope.md:107` F7). B's advantage is narrower and honest: by keeping the cliff as the **headline** and goal-commitment as a scoped sub-claim, B does not *claim* to have addressed the cross-cycle cliff. A's "complement" framing canonizes a co-equal value pointed at the *wrong axis* for its own stated identity (`03-premortem.md:59`); B avoids that miscalibration by positioning, even though it shares the underlying non-solution.

**S7 — constraint-harvest mis-curation (med × med).** If B adopts the optional disposable-harvest-worker pattern, it inherits the same recall-under-cap omission risk (`03-premortem.md:53`). Shared. (B can decline the harvest worker and keep Phase-1 reads inline, trading context-budget for recall — a live mitigation A's design forecloses.)

**S5 — `amendments:` log rot / discipline decay (med × high).** B adds the charter primitive, so it inherits the `done:`-singularity rubber-stamp and amendment-log discipline-decay risk (`03-premortem.md:45`) — **but materially reduced**, because B's charter is not re-injected per turn (Gap 1 fix is A's, not B's), so the "15-entry narrative re-injected every turn → context-bloat" failure mode (`03-premortem.md:45`) does not apply to B. Residual: the operator can still rubber-stamp a fuzzy `done:`. Shared-but-lighter.

**S6 — migration straddle (high × med).** Partially shared and **much smaller for B.** S6's severity scales with the size of the superseded machinery coexisting with the half-built replacement, and with INV-003's retirement removing the `validate_phase_topology` binding the consumer's validator runs (`03-premortem.md:49`). **B retires no firm machinery and removes no invariant binding** — the consumer keeps the same 4-phase shape, the same `validate_phase_topology`, the same agent-def discoverability. B's only migration delta is deleting dead AGENT_ROLE wiring (which fires nowhere, so removing it is behavior-neutral) and adding an optional charter file. **The validator-goes-green-by-vacuity failure (`03-premortem.md:49`) is impossible under B** — the invariant it checks still exists.

### What B does NOT solve (be honest):

- **B keeps ceremony cost.** B *lightens* ceremony per phase but keeps four phases. If the operator's actual pain is "four phases is too many boundaries for a single-operator repo," B does not fix that — it bets (with phase-pipeline-evaluation's 5-slice evidence, `:49-58`) that the pain is the *machinery*, not the *count*. If that bet is wrong, B under-delivers.
- **B's goal-commitment sub-claim is thinner than A's headline.** A makes goal-commitment-vs-reactivity the identity. B demotes it to a Phase-1 hardening. If the operator opened this arc *specifically* to canonize goal-commitment as cairn's identity, B does not give them that — by design (see §5).

---

## 4. Downstream impact — minimal migration; familiar pipeline

The consumer (`complex-rag-analysis`, on a `.slice-system → .` symlink, ~917s pytest) keeps:

- The **same 4-phase shape** its `.claude/settings.json` hook wiring, agent-def discoverability, and orchestrator already assume (`03-premortem.md:49`).
- The **same `validate_phase_topology` binding** — INV-003 is not retired, so the consumer's validator does not error or go green-by-vacuity.
- The **same four `phase-{1,2,3,4}-tdd.md` agent defs** (capability cleanup of dead AGENT_ROLE references only).

B's migration is: (a) delete dead AGENT_ROLE wiring (behavior-neutral — it fires nowhere, `02-journey-trace.md:15`); (b) optionally swap session-dispatch for foreground-subagent-dispatch in SKILL.md; (c) add an optional charter front-end. No symlink-lockstep agent-dir + hook-entry + invariant migration is forced. Contrast A's straddle: months-long coexistence of retired 4-phase machinery with the half-built charter cycle, colliding with gh:#33's own SessionStart-skill work competing for the same event (`03-premortem.md:49`, `:65`).

**Per L-022** (`01-constraint-envelope.md:39` P6): if B ships the charter primitive with any parsed contract, the implementing slice round-trips the real consumer — but B's parsed surface is one structural-parser binding over an optional file, vs A's per-turn re-injection hook that must be fire-tested across compaction + resume.

---

## 5. Honest weakness — the single strongest reason to reject B

**B is incrementalism that dodges the identity question the operator opened the arc to settle — and it under-evidences its own positioning call.**

The operator triggered D3.4 to *settle cairn's identity*, with a stated "complement" starting position that puts goal-commitment-vs-reactivity alongside the cliff. B refuses that framing: it keeps the cliff as headline and demotes goal-commitment to a scoped Phase-1 sub-claim. A skeptic says, fairly: **"You were asked what cairn IS. B's answer is 'the same thing it already was, with the dead code removed and a new front-end form.' That is a maintenance ticket wearing an identity ADR's clothes."** B ships no new firm identity claim; under F11 (`01-constraint-envelope.md:25`) a provisional identity ADR cannot be a *firm* identity claim — so B arguably produces no identity ADR at all, just a cleanup + a provisional supersession.

The sharper edge: **brainstorm-1 named a real failure mode** — input-reactive over-steering, the agent whipsawing on the operator's latest message — and B's response is to fold it into Phase 1 rather than mechanize it. If that reactivity failure is genuinely distinct from the cliff (brainstorm-1 framed it as "distinct from but adjacent to the drift/rot arc," `01-constraint-envelope.md:38`), then B's demotion-to-sub-claim **structurally fails to capture it**: a Phase-1 intent artifact that isn't re-injected per turn does not defend against mid-session reactivity at all — it just records the goal once and trusts the pipeline. B gets its S5-avoidance (no per-turn hook) **precisely by not building the mechanism that would address reactivity** — the same hook (Gap 1) it criticizes A for not having. **B cannot simultaneously claim "reactivity is real enough to fold into Phase 1" and "we don't need the re-injection hook."** Pick one. If reactivity is real, B under-builds; if it isn't, B's sub-claim is empty. That tension is B's fatal risk, and it is the mirror image of A's S1: A over-commits to an unmeasured mechanism; B under-commits and may capture nothing.

**The lead's adjudication question:** Is cairn's identity *settled enough by the cliff alone* that goal-commitment is genuinely a sub-claim (→ B is right-sized and S1-safe)? Or did the operator open this arc because the cliff is NOT the whole identity and reactivity needs first-class mechanization (→ B dodges the question and only A's headline answers it, at A's S1/S3 cost)? B wins if the answer is "the cliff is the identity and the 5-slice pipeline evidence should not be discarded for an unmeasured pivot." B loses if the answer is "reactivity is the un-captured half of cairn's identity and a Phase-1 form that isn't re-injected does not capture it."

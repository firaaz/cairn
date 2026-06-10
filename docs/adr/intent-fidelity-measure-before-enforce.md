---
id: intent-fidelity-measure-before-enforce
name: "Intent-fidelity at Step 3a — populate the baseline and measure (incl. cross-family) before enforcing; pilot the engagement forcing-function"
status: accepted
carrier: rationale-only
firmness: provisional
supersedes: null
superseded-by: null
resolved-by: trial-e-closure-adjudication
topic: architecture
invariants-touched: []
date: 2026-06-01
---

# Intent-fidelity at Step 3a — populate the baseline and measure before enforcing; pilot the engagement forcing-function

## Status

Accepted (post-`/decision` arc `step3a-fidelity-surface`, 2026-06-01; operator-selected "ADR + pilot C" after Phases 0–3). **Provisional** — supersedes nothing and modifies no invariant, so Phase 5 independent verification is not required. It is *consistent with* `intent-contract-cost-model`'s deferral (it generates that deferral's gating data) and *extends* `intent-management-loop` without invalidating any of its decisions.

## Date

2026-06-01

## Context

The operator reports rubber-stamping at the cairn-intent **Step 3a** operator sign-off: the gate surfaces the whole ~250–400-line LLM-authored `intent.md` plus the challenge verdict as one all-or-nothing approval, with no declared floor (`.claude/skills/cairn-intent/SKILL.md:60`). The named driver is **information volume + latency** — the fresh-context challenge round-trip costs the operator their framing, so they approve to keep moving.

The `/decision` arc opened to redesign that surface so it is derived from the operator's *irreducible job* (intent-fidelity + value/scope; the human cannot validate correctness because an AI wrote the code — `cliff-failure-mode-and-v1-defenses/D-context`, `:48`). Round-1 (constraint harvest, journey trace, pre-mortem) and a Phase-2 steelman panel + Phase-3 adversarial pass produced a result that **reversed the obvious redesign**:

1. **The decorrelation trilemma (no free source).** A single same-family fresh-context challenger ~60% co-misses fidelity leaps (`intent-contract-cost-model/D3`, `:97`, EXPOSED); cross-family is the *named* fallback but its co-miss delta is unmeasured (S7); pushing the operator to be the source relocates the rubber-stamp (S1), amputates un-enumerated externalities under any compression (S5), and goes stale on amendment (S10). Every single-source mechanism has a named killer.
2. **The metric trap.** Fast approval is observationally identical to disengagement (S4); the only signal that distinguishes them — post-close fidelity-defect-escape — is silent and slow by construction (`cliff-failure-mode-and-v1-defenses`) and sample-starved at single-operator throughput (S6). **No enforcement redesign can be empirically validated here.**
3. **The empty baseline (verified on disk).** The proposed "right-by-construction" core (a deterministic clause↔intent traceability check + wiring the operator's fidelity anchor) rests on `## Operator Prompt` — which is **absent from 7/7 real cairn-intent intents** (only the meta-intent that created the field has it) and **never authored by the loop** (`SKILL.md:49` forms a thin contract with no fidelity anchor; the field is a four-phase `phase-1-tdd` artifact recently pinned to the *template* via gh#28). A check over an absent baseline passes vacuously — the `validator shall report a result → log-and-exit-0` floor-erosion canary L-028 names, not a defense.
4. **The category error.** "Right-by-construction" conflates *determinism of a check* with *value of a check*. Cardinality coverage being deterministically true says nothing about fidelity or engagement; its value is the same unmeasured question `intent-contract-cost-model/D3` deferred. Committing it would declare victory on a different problem than posed — the S4 self-deception, one level up.
5. **The gate is barely exercised.** cairn-intent was just activated (~0 real Trial-E runs; dogfood-log empty of fidelity entries). We lack data that rubber-stamping bites *here*, let alone that a fix works.

Governing prior decisions: `intent-contract-cost-model/D3`,`/D4`,`/D5` deferred the heavy-band fidelity bundle (traceability + agent-declared/challenger-attacked severity + front-loaded fidelity challenge) gated on Trial E, recording "no new automated intent-fidelity backstop until D3 lands." L-028 mandates that any compressed approval surface declare the floor with severity as the *challenger's* input (never operator review) and never narrate a structural check as a semantic catch. `intent-management-loop/D6` is "no new hooks."

## Decision

**Measure before enforce.** Commit only capture + measurement (right-by-construction or evidence-generating); defer all enforcement until the generated data justifies it.

**D1 — Populate the fidelity baseline.** Wire the operator's fidelity intent into the cairn-intent loop's authoring step (`SKILL.md:49`) as a durable, mandatory artifact — capture, in the operator's own prose at authoring time, what the work must be faithful to and must never do. This is captured as **measurement input, not an enforcement gate** (it carries the S1 relocation risk, so it must not become a pass/fail gate now). It gives the currently-inert anchor a populated existence for the first time.

**D2 — Instrument the gap (same-family AND cross-family).** Log, per intent: the operator's pre-gate verdict vs what the existing front intent-challenge and close-review actually catch. Additionally, run the **front fidelity challenge cross-family** (Claude drafts / Codex challenges, leveraging the in-flight `codex-hook-parity` work) to measure the Claude-vs-Codex co-miss rate on cairn's fidelity-leap class — the exact datum `intent-contract-cost-model/D3` named as the cross-family escalation trigger. This converts "defer cross-family forever" into "defer until measured."

**D3 — Pilot the engagement forcing-function (C) as an instrumented probe.** At Step 3a, add **one** planted-decoy clause (the operator must catch and specifically reject to proceed) plus **one** active-recall question — O(1) in clause count, not per-clause (avoids the S9 grind). The decoy must NOT be generated same-family (use deterministic mutation of a real clause, or the cross-family challenger). `decoy-catch-rate + rejection-specificity` is an **in-band, per-intent engagement signal** — the only candidate that escapes the defect-escape data-starvation (S6). This is piloted to *measure engagement*, not committed as enforcement.

**D4 — Defer all committed enforcement.** No surface compression (A); no deterministic traceability check or widened challenger as a *load-bearing* gate; no committed cross-family enforcement (B). Each is revisited when D2/D3 produce data. Because D1–D3 generate `intent-contract-cost-model/D5`'s Trial-E gating data and ship no enforcement bundle, **this decision does not supersede that deferral** — it feeds it.

**D5 — Metric discipline.** Do NOT adopt review-time-under-15-min as a success target (`slice-intent-contract/wrong-if`, `:20`) — it rewards the disengagement it claims to detect (S4). Success is judged on the generated signals (decoy-catch-rate, cross-family co-miss delta, operator-miss-vs-challenger-catch rate), with post-close defect-escape as the slow backstop.

## Consequences

**Changes (implementation, to land via the cairn-intent loop as separate feature work):**
- `.claude/skills/cairn-intent/SKILL.md` — Step 1 authoring gains the baseline-capture (D1); Step 3a gains the instrumented decoy + active-recall (D3).
- `templates/intent.md` — a populated fidelity-baseline section authored *in the loop* (distinct from the four-phase `## Operator Prompt`).
- `workflows/cairn-intent.yaml` — node/evidence wiring for the baseline, the measurement log, and the cross-family challenge path.
- `.claude/agents/intent-challenge.md` — may consume the baseline as input for the *measured* (not gating) fidelity attack; cross-family invocation path.
- A function-based Python helper under `checks/`/`scripts/lib/` for deterministic decoy mutation + the measurement artifact — invoked as a **skill-step, not a PreToolUse hook**, so it does not breach `intent-management-loop/D6`.
- Parity edits to the Codex `cairn-intent` skill (two-surface parity, `SKILL.md:8`).

**Invariants:** none touched. INV-003 binds only `cairn-tdd-feature`, not cairn-intent (verified: `validate_phase_topology` never references the loop). INV-004 (context budget) is unaffected — the pilot is gate-time, not session-start. Extends `intent-management-loop` (provisional); does not violate its D2 (the decoy sits at the *existing* 3a approval moment — no new per-session ceremony, no diff-size trigger).

**What gets harder (honest):** more moving parts at the gate; decoy generation must avoid the same-family blind spot; **decoy-fatigue** (a predictable decoy → pattern-rejection → S1 reborn) must be actively monitored via catch-rate/rejection-specificity; the baseline-capture itself carries the S1 relocation risk and is mitigated *only* by being measurement-only, not a gate; cross-family adds a runtime dependency on Codex availability (acceptable because it is being stood up anyway, and the path degrades to same-family measurement if Codex is absent — recorded, not silent).

## Alternatives Considered

- **A — Predict-before-see (compress the surface; operator declares floor in prose; derived severity; challenger vs frozen criteria).** Rejected as a *commit*: S1 (relocates the stamp onto the floor-prompt under unchanged latency), S5 (compression amputates externality-recall — its worst case), and unvalidatable (S4/S6). Its one durable idea — capture the operator's fidelity intent — survives as D1, *without* the compression.
- **B — Cross-family fidelity challenger as committed enforcement.** Rejected as a commit: the co-miss delta is unmeasured for cairn's fidelity class (S7). Its *measurement* is folded into D2 (via Codex); commitment is deferred to a future `/decision` triggered by that measurement — honoring the pre-recorded escalation rather than betting on it.
- **C — Engagement forcing-function as committed enforcement.** Rejected as committed enforcement: declares no floor (non-conformant alone per L-028) and risks decoy-fatigue. Adopted instead as an **instrumented pilot** (D3), because its decoy-catch-rate is uniquely an in-band metric that escapes S6.
- **D — Pure measure-first (no structural change).** Rejected alone: S6 (never converges — single-operator throughput + long-latency silent failure starve the sample; deferral becomes permanent). Addressed by *first* populating the baseline (D1) so fidelity is measurable at all, and adding C's fast in-band metric (D3) so measurement can converge in weeks, not the six-month cliff window. This decision is D done *correctly*: measure on a populated baseline with a fast instrument.
- **E — Declare-floor + mechanize-edge, no compression ("E-core," the Phase-2 winner).** **Failed in Phase 3:** the baseline (`## Operator Prompt`) is empty in the live loop (D-context point 3); no prose↔EARS matcher exists under function-based-Python-only (`scripts/lib/premise_match.py:grounded` is substring-only, needs verbatim overlap absent between prose and EARS); and its "right-by-construction" claim is a category error (determinism ≠ value, point 4). Its only salvageable residue is D1 + D2 — which this decision adopts.

## Risk Register

| Pre-mortem scenario | How this decision handles it |
|---|---|
| **S1 — relocation** (stamp moves to the floor-prompt) | D1 is measurement-only (not a gate), so a boilerplate floor costs nothing yet; D3's decoy is the *active* anti-relocation probe; monitor floor-entropy + decoy-catch-rate. |
| **S2 — severity leaked onto user** | No severity field is ever rendered to the operator (no compression, no operator-set band — `intent-contract-cost-model/D-deferred-constraint-2`). |
| **S3 — same-family co-miss** | Not relied upon. The same-family challenger stays as-is; D2 *measures* its miss rate rather than trusting it. |
| **S4 — wrong-target metric** | D5 explicitly rejects review-time; success = generated signals, defect-escape as backstop. |
| **S5 — externality amputation** | No compression — the full contract stays in front of the operator; breadth-of-trigger preserved. |
| **S6 — measure-first never converges** | D1 makes fidelity measurable (baseline exists); D3's decoy-catch-rate is a fast in-band per-intent signal, not the starved defect-escape. |
| **S7 — cross-family collapse/unmeasured** | D2 *measures* the cross-family delta via the in-flight Codex integration; degrades to same-family measurement (recorded) if Codex is absent. Commitment deferred to that data. |
| **S8 — ADR orphan / missing firm supersession** | Provisional; supersedes nothing; no `human_signoff_after` contract change beyond an additive decoy at the existing moment. No firm-decision web touched. |
| **S9 — per-clause grind at scale** | D3 is O(1) in clauses (one decoy + one recall), not per-clause. |
| **S10 — amendment re-fire bypasses the gate** | Known gap; the measurement (D2) instruments the delta-re-fire path too, so the bypass surfaces as data rather than shipping silently. No claim to have closed it. |

## Follow-on triggers

- Cross-family co-miss delta (D2) materially below same-family ~60% on the fidelity-leap class → open a `/decision` to commit B (cross-family enforcement).
- Decoy-catch-rate stays high with specific rejections over the trial window → consider committing C as enforcement; if it decays (fatigue) → C is falsified, record EXPOSED.
- Sufficient populated-baseline + measurement to satisfy `intent-contract-cost-model/D5`'s Trial-E gate → that ADR's D3 deferral can be adjudicated (pass = commit the heavy-band bundle; fail = retire the ambition).

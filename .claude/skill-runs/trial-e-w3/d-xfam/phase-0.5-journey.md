# D-xfam — Phase 0.5: journey trace

How "commit cross-family fidelity enforcement?" became a live operator-bound call, and
what binds it.

## The arc

1. **The complaint.** Operator reports rubber-stamping at cairn-intent Step 3a — the gate
   surfaces the whole ~250–400-line `intent.md` + verdict as one all-or-nothing approval,
   no declared floor. Named driver: information volume + latency (`SKILL.md:60`,
   ADR `:25`). Opens `/decision` arc `step3a-fidelity-surface` (2026-06-01).

2. **The decorrelation trilemma** (ADR `:29`). Phases 0–3 of that arc found **every
   single-source decorrelation mechanism has a named killer**:
   - same-family fresh challenger → ~60% co-miss on fidelity leaps (Kim, EXPOSED,
     `intent-contract-cost-model/D3:97`);
   - operator-as-source → relocates the stamp (S1), amputates externalities under
     compression (S5), goes stale on amendment (S10);
   - **cross-family** → the *named fallback*; its only objection is that the co-miss
     delta is **unmeasured** (S7) — a measurement gap, not a structural flaw.
   Cross-family is therefore the one mechanism the trilemma leaves *standing pending data*.

3. **The resolution — measure before enforce.** The arc reversed the obvious redesign:
   commit only capture + measurement, defer all enforcement (D4). Critically:
   - **D2** folds cross-family *measurement* in — Claude drafts / Codex challenges,
     leveraging in-flight `codex-hook-parity` — explicitly converting "defer cross-family
     forever" into "defer until measured" (`:43`).
   - **B** (cross-family as *committed* enforcement) is rejected **as a commit** (`:68`):
     "the co-miss delta is unmeasured (S7) … commitment is deferred to a future `/decision`
     triggered by that measurement — honoring the pre-recorded escalation rather than
     betting on it."
   - **The trigger** (`:90`) sets the firing condition: cross-family co-miss materially
     below same-family ~60%.

4. **dp3 measures the same-family baseline** (2026-06-02, two-checkpoint co-miss probe,
   de-primed/blind/sandboxed):
   - front arm (intent-challenge analogue): **5/5 vs ground truth, 0/3 miss**;
   - close arm (intent-review analogue): 4/5 — **missed D2**, the no-friendly-tell case;
   - **total two-checkpoint co-miss: 0/3.**
   Load-bearing finding: fidelity protection is **front-loaded, not two independent shots** —
   the close-review is a *conditional* backstop (works only when the defect propagates into a
   diff-visible regression). The **same-family front-arm baseline this decision compares
   against = 0/3 miss.**

5. **W1 measures cross-family** (2026-06-04, the spec's missing datum). Fresh no-context
   **Codex** front-challenger over the dp3 corpus, blind grader:
   - **5/5 vs ground truth** — 3/3 planted fidelity defects blocked, 2/2 controls passed,
     **0 misses, 0 false positives** (`grader.json`).
   - Cross-family-vs-same-family front-arm co-miss on this corpus: **0/3.**
   - **No measured delta below the baseline — because the baseline (dp3) already had no
     misses.** Cross-family matched same-family; it did not improve on it.
   - **Provenance caveat (load-bearing):** the five cases were *reconstructed from the dp3
     corpus inside the Codex session*, not freshly Claude-authored. If strict Claude-draft
     provenance is required, rerun from a Claude-authored case pack.

6. **D-xfam (this `/decision`)** owns the formal "not triggered / commit" adjudication. The
   ADR's `:94` and the W1 field note both hand the call here. The live operator-bound
   question (brief): **is the Codex-reconstructed provenance acceptable for a "not triggered"
   close, or is a Claude-authored rerun required first?**

## What binds this decision

- `intent-fidelity-measure-before-enforce` — D2 (measure), D4 (defer), D5 (metric
  discipline), the B-rejection (`:68`), the trigger (`:90`).
- `intent-contract-cost-model/D3` (`:97`) — the original cross-family escalation trigger and
  the ~60% prior.
- `intent-management-loop/D6` — no new hooks.
- dp3's front-loaded asymmetry finding (`operator-field-notes-2026-06-02`).

## Downstream coupling (for ordering, per brief)

D-xfam's result feeds **D-cost** (the "front-loaded fidelity challenge value" question) and
**D-retire** (the cross-family angle). Suggested surface order: D-xfam → D-cost → D-retire.

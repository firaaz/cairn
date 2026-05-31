# /decision thin-cairn-intent-management — Phases 0–3 synthesis

Raw agent output: workflow `decision-thin-cairn-intent-management` (run wf_9a44b8ce-b8a),
6 agents. This file is the synthesized record + my Phase 3 work.

## Phase 0 — constraint envelope (decisive items)

- **INV-003 is firm + machine-bound** (`validate_phase_topology`, `ARCHITECTURE.md:30-37`):
  "every cairn-tdd feature runs through exactly four phases… locked; changes require a
  superseding ADR." **D8 of `cairn-thin-substrate-direction` explicitly RETAINS** INV-003 +
  the firm phase ADRs (`:140-143`). ⇒ **This decision cannot retire the 4-phase.** Retirement
  is a *separate, firm supersession* gated on Trial E.
- Daily-usability is first-class (the reason v1 was abandoned, spec-v2 §2). No new
  infra/deps. Premise-grounding is the keystone (D7). The 7 open Qs are the agenda.

## Phase 0.5 — journey: what's mechanized vs GAP

- Mechanized: premise_guard (grounding at approval), role_guard/reversibility/atomicity
  (ambient), handoff contract (INV-002).
- **GAPs (build scope):** the cairn-intent skill, the `intent-challenge` + `intent-review`
  subagents, the SessionStart carrier — all unbuilt. Plus the 7 open Qs are unmechanized.

## Phase 1 — broadened pre-mortem (4 NEW failure scenarios)

1. **Partial consumer adoption via stale `.slice-system`** — hooks (premise_guard etc.)
   missing/misconfigured downstream → decorrelation silently fails. (integration, serious)
2. **Cross-family decorrelation cost/latency cascade** — if Q3 → cross-family, two
   coldstarts/intent vs the INV-004 budget. (scale, serious)
3. **Intent divergence across host tools** — carrier fires on Claude Code, not Cursor →
   divergent intent files. (integration, serious)
4. **premise_guard symlink-traversal escape** — a `.slice-system/…` premise path reads
   cairn's source not the consumer's → false-green grounding. (technical, serious)

## Phase 2 — forced enumeration (verdicts)

| Approach | Firm-constraint fit | Daily-usability | Verdict |
|---|---|---|---|
| **A1 Coexist-then-Retire** (new `cairn-intent` skill alongside, retire on Trial-E pass) | **Fits all** (retirement deferred) | Delivers it | **WINNER** — conditional on resolving Q1–Q7 |
| A2 Augment-in-place (intent gates inside the 4 phases) | Fits (no retirement) | **Violates** — keeps per-phase ceremony; two-mode toggle hazard | Runner-up / fallback if A1's Trial E fails |
| A3 spec-v2 wholesale (promote v2, retire now) | **Violates** INV-003/D8 + bypasses trial-gating | Hypothesized | Rejected-but-future (= where A1 *leads* if Trial E passes) |

## Phase 3 — adversarial stress test

- **Steel-man A2:** zero-migration, zero-risk, honors all firm ADRs, and its gates ARE real
  decorrelation. If the operator's real pain were only "4-phase lacks semantic grounding," A2
  delivers that defense without a new skill. **Why it still loses:** it keeps the 4-phase
  spine — failing the *stated* intent (move to intent management) and the documented
  daily-usability driver. A2 is the fallback, not the primary.
- **Disconfirming search on A1:** A1 fails if (a) Q1/Q4 resolve loose → ceremony returns (A1
  degrades to A2-plus-risk); (b) Q3 needs cross-family → cost breaks INV-004; (c) the
  premise_guard symlink escape is real in consumers. All are *gated by Trial E*, which is
  exactly A1's de-risking: build + test, retire only on pass.
- **Assumption audit (verified vs believed):**
  - VERIFIED: INV-003 firm+bound; D8 retains phase ADRs; the 3 gates shipped; the carrier is
    **unbuilt** (checked: `using-cairn` / `cairn-*` agents NOT FOUND).
  - BELIEVED (⇒ Trial-E acceptance tests, not assumed): the front-challenge actually blocks
    slice-#25-style misreads; same-family decorrelation is sufficient (Kim et al. 60% warns
    otherwise); the carrier hits ≤2k budget with a reliable fired-definition.

**Conclusion:** Approach **A1**, reframed as **build-the-coexisting-path-and-gate**, NOT
retire-now. The ADR is **provisional** (it supersedes nothing — coexistence doesn't violate
INV-003), so **Phase 5 independent verification is not required for this ADR**; the *future
retirement* ADR (superseding INV-003 + the phase ADRs) is the firm one that gets Phase 5.

## Proposed resolutions to the 7 open questions

1. **Material-change threshold (Q1):** re-trigger approval + front-challenge on a **premise or
   must-satisfy clause edit**, NOT on code diff-size. The challenge is about grounding; only
   premise/clause changes alter what must be challenged. Code work inside an approved contract
   flows freely. (Tight against drift, no ceremony on construction.)
2. **Completeness floor (Q2):** a one-line **scope-statement in the contract** (attackable by
   the front-challenge) + the **close-review smell-tests contract-depth vs diff size** as a
   finding. No hard cardinality gate (arbitrary + gameable).
3. **Decorrelation strength (Q3):** **same-family fresh-context for now**, cross-family
   recorded as EXPOSED with a revisit trigger (Trial E shows a correlated miss). Rationale:
   Song et al. supports cross-*context* (same-family fresh-context provides it); cross-*family*
   breaks INV-004 + adds infra. — **OPERATOR FORK.**
4. **Carrier contract (Q4):** "fired" = carrier emitted the intent pointer or a no-intent
   signal within ≤2k tokens; **fallback** = the skill's first step does load/form explicitly
   (carrier is an optimization, not the only path). Unit-tested.
5. **Retirement trigger (Q5):** Trial-E pass = (slice-#25 counterfactual blocks at the
   front-challenge) AND (≥1 real cairn increment ships via cairn-intent, operator confirms no
   semantic-grounding leak) AND (felt cost < 4-phase). On pass → a **separate firm supersession
   ADR** retires cairn-tdd-feature + supersedes INV-003 + phase ADRs, with a coexistence sunset
   window. — **OPERATOR FORK** (sharpness/sunset).
6. **Multi-operator divergence (Q6):** scope as **single-operator-per-branch** for now (intent
   lives in git; branches own their intent); multi-operator reconciliation EXPOSED + deferred
   to a future decision when a real multi-operator consumer appears.
7. **Trivial-session boundary (Q7):** a session that **writes** to the repo needs at least a
   thin (one-liner) intent; **read-only / Q&A sessions are exempt**. The graduated floor keeps
   thin-intent cost near-zero; no separate diff-size carve-out.

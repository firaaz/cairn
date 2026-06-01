# Phase 3 — Adversarial Stress Test: E-core (and reversal)

/decision arc `step3a-fidelity-surface`, 2026-06-01. Fresh-context attack on the Phase-2 winner (E-core), plus operator-verified disk facts.

## Verdict: E-core FAILS as written → narrow to "measure on a populated baseline."

## The pivotal fact (operator-verified, not relayed)
E-core's components 1 & 3 wire `## Operator Prompt` as the challenger's fidelity baseline; component 2 diffs clauses against it. But:
- **7/7 real cairn-intent intents in `.claude/skill-runs/*/intent.md` have NO `## Operator Prompt`.** Only `intent-template-operator-prompt/intent.md` (the meta-intent that created the field) has it. (Verified by grep this session.)
- **The loop never authors it.** `.claude/skills/cairn-intent/SKILL.md:49` (`load-or-form-intent`) forms "the thinnest sufficient contract" = scope line + one `must-satisfy` + evidence + envelope. Zero mentions of Operator Prompt in the SKILL or `workflows/cairn-intent.yaml` (verified). It is authored only by the four-phase `phase-1-tdd.md` from a plan-doc — a different skill. Pinned to `templates/intent.md` via gh#28 but never wired into the loop.

⇒ A deterministic check over an absent baseline fail-opens vacuously (`premise_guard`-style, the only precedent): it ships a green stamp meaning "no baseline existed to violate" — the exact `validator shall report a result → log-and-exit-0` floor-erosion canary (L-028 `:563`, cost-model deferred-constraint-1 `:80-84`). **E reproduces the failure it claims to defeat.**

## The three attacks that land
1. **Empty baseline (fatal to E-1/E-3).** Above. To fix it you must *first* make operator-fidelity-criteria a populated, mandatory loop artifact — which is Approach A's missing-mechanism #1, with A's S1 relocation cost. E cannot borrow A's payload while disclaiming A's cost.
2. **No prose↔EARS matcher (fatal to E-2).** The only structural matcher on disk is `scripts/lib/premise_match.py:grounded` — normalized substring, which works only because a premise pins a *verbatim quote*. Operator Prompt is free prose; clauses are EARS (`if <cond>, the <sys> shall <resp>`). No lexical overlap; function-based Python with no semantic matcher cannot establish correspondence. The cardinality check fires on legitimate work → operator re-trained to dismiss it → **rubber-stamp relocates onto "wave away the noisy check."**
3. **Category error (fatal to E's headline claim).** "Right-by-construction" conflates *determinism of the metric* with *value of the metric*. Cardinality coverage being deterministically true says nothing about fidelity or about engagement (the arc's actual question). E's value claim — "catching orphan/unrealized clauses reduces fidelity defects" — is itself UNMEASURED: the same value question cost-model D3 deferred. E supersedes the deferral on the thin evidence it claimed to escape, and declares victory on a *different* problem (visible-cardinality) than the one posed (operator disengagement) — the S4 self-deception pattern, one level up.

## Steelman of the opposition (strongest case against acting): D — measure-first
L-027 ("don't let adversarial completeness select the null action") is E's license to act — but L-027's corrective is precise: find the mechanism that survives the attacks AND is buildable AND whose *load-bearing value is established*, then prove it with a spike. E's value is NOT established; its spike is a vacuously-passing check. The deferral was gated on Trial-E data that **does not exist** — the dogfood-log has ~0 real Trial-E entries and 7/7 intents lack the baseline. cairn-intent is freshly activated (git log: "finalize cairn-intent activation … first Trial-E dry-run"). So we'd be redesigning a barely-exercised gate: we lack data that the problem manifests *here*, let alone that a fix works.

## Reshaped recommendation
The honest, value-establishing, deferral-CONSISTENT move (not a supersession):
1. **Populate the baseline.** Wire the operator's fidelity intent into the cairn-intent loop's authoring step (`SKILL.md:49`) as a durable artifact — capture what the operator already states in prose. (Carries A's S1 risk, so it ships as *measurement input*, not an enforcement gate.)
2. **Measure (D, on the populated baseline).** Instrument the gap: operator pre-gate verdict vs what the existing challenger / close-review catch, to GENERATE the Trial-E signal the deferral is gated on.
3. **Defer all enforcement** (traceability check, widened challenger as load-bearing, compression, cross-family). Priority-1 deferred = C's engagement forcing-function, because decoy-catch-rate is the only candidate with a fast in-band metric that escapes S6.

This reconverges on the operator's *original* "measure first" instinct — but adds the prerequisite it lacked (populate the baseline first; measurement over an empty baseline is meaningless) and the full understanding of WHY every enforcement path fails (trilemma + metric trap + category error + empty baseline).

**Firmness:** provisional. Procedural cost is LOW — extends `intent-management-loop` (provisional) + a measurement artifact; consistent with cost-model D3 (generates its gating data), so likely NO D3/D4/D5 supersession needed.

## Meta
This conclusion must NOT be rubber-stamped into an append-only ADR without operator sign-off — the arc is about not rubber-stamping. Phase 4 is gated on operator confirmation.

---
id: using-cairn-carrier-contract
name: "using-cairn carrier contract — dynamic SessionStart command-emitter, cairn-internal-first"
status: accepted
firmness: provisional
supersedes: null
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-06-01
---

# using-cairn carrier contract — dynamic SessionStart command-emitter, cairn-internal-first

## Status

Accepted (post-`/decision` arc `using-cairn-carrier`, 2026-06-01; operator-selected
Approach D after Phases 0–3, over three refuted briefed approaches A/B/C). **Provisional** —
this ADR pins a *provisional* carrier for the provisional `intent-management-loop`, modifies no
invariant, and ships nothing to consumers, so Phase-5 independent verification is not required.
The firm consumer-distribution decision is deferred to the future D7 retirement ADR.

## Date

2026-06-01

## Context

`intent-management-loop` **D5** committed to a `using-cairn` SessionStart carrier with a "testable
fired-definition + fallback within the ≤2k-token budget," but left the *exact* contract open; the
brainstorm (`docs/plans/2026-05-31-thin-cairn-intent-management.md` Q4) routed it to `/decision`.
This ADR resolves that contract. It is the #2 increment toward Trial E (after `intent-review` and
the graduated-contract rules landed on `feat/cairn-intent-loop-build`).

The `/decision` arc (Phases 0–3 recorded at `.claude/skill-runs/using-cairn-carrier-decision/`)
forced three approaches and **adversarially refuted all three**, converging on a synthesized
fourth (Approach D). Three facts were verified against live source and are load-bearing:

- **F1 — distribution coupling.** `scripts/build_dist.py:31` ships
  `.claude-plugin/hooks-template.json → dist/hooks/hooks.json` **unconditionally** ("allow-list IS
  the contract"; no per-block transform). A SessionStart block in the *shipped* template therefore
  reaches every consumer. "cairn-internal only" is achievable **only** by registering the carrier
  in cairn's *local* `.claude/settings.json` (not in the allow-list).
- **F2 — no SKILL hook type.** Claude Code's SessionStart hook schema has only `type: command`
  (verified against `.claude-plugin/hooks-template.json` + the superpowers/warp precedents). A
  `SKILL.md` cannot itself be the registered+fired artifact; `delivery-mechanism-friction` D1's
  "SessionStart skill" resolves to a command emitter.
- **F3 — L-012 hazard.** `docs/lessons.md` L-012: a SessionStart bash hook emitting the imperative
  line *"No active slice — /start-slice"* caused an opus-4-7/low Phase-4 agent to hard-refuse four
  times, quoting the hook text verbatim. Carrier emission must be neutral and state-accurate.
- A real tokenizer is **dep-forbidden** (standing deps = pydantic/typer/pyyaml;
  `intent-management-loop` D6), so a token-exact CI budget gate cannot be built today.

## Decision

**D1 — Realization.** The carrier is a SessionStart `type: command` bash emitter
(`checks/using-cairn-carrier.sh`). This is what `delivery-mechanism-friction` D1's "SessionStart
skill" resolves to under F2; D1 is reconciled by reading "carrier/skill" as *the thing that fires
at SessionStart*. Honest-minimal: no Python module, and it is **not** a fourth enforcement guard
(`intent-management-loop` D6 "no new hooks" names the three enforcement guards).

**D2 — Fired definition (D5 sub-q1).** The carrier emits a deterministic first-line marker
`CAIRN_CARRIER_FIRED`, then either a **dynamic** active-intent pointer (resolved from
`.claude/handoff.md` / the active `.claude/skill-runs/<feature>/intent.md`) **or** an explicit
no-intent signal. Unit-tested as a **render** test (run the script against a fixture
`CLAUDE_PROJECT_DIR`; assert the marker, the pointer-on-resume / no-intent-on-empty, and `rc == 0`
on every path). Honest scope: this tests render, **not** host injection — "fired on the host" is a
Trial-E integration observation (`intent-management-loop` D9), never a unit test.

**D3 — Budget (D5 sub-q2).** Emission is byte-clamped, env-overridable
(`CAIRN_CARRIER_BUDGET_BYTES`, default 8000 ≈ 2k tokens), per CLAUDE.md no-hardcoded-sizes. The
≤2k sub-budget has **no** CI token enforcement today; the `delivery-mechanism-friction` D6 CI
tokenizer gate is recorded **EXPOSED** and deferred to the D7/distribution ADR (a real tokenizer
is dep-forbidden — do not fake it). The byte-clamp is the only runtime backstop.

**D4 — Fallback (D5 sub-q3).** The `cairn-intent` skill Step 1 (load-or-form-intent) runs
**unconditionally** and never branches on carrier state. Non-firing is indistinguishable from
firing (both converge on the on-disk handoff + intent.md). This is the named prevention for the
rejected "approve-every-session" stale-load **fatal** mode; the carrier can only redundantly help,
never strand or gate.

**D5 — Neutral, state-accurate emission (L-012 / F3).** The carrier emits **only** a neutral
pointer — **no imperative instruction prose** (no "run the X skill"). It respects the handoff
state token (INV-002 `{open, blocked, deferred}`) and does not emit a stale/closed-feature pointer
verbatim. On a read-only / no-write session it emits at most the bare marker. Unit-tested.

**D6 — Distribution (D5 sub-q5).** **cairn-internal ONLY.** The carrier is registered in cairn's
*local* `.claude/settings.json` — **not** in `scripts/build_dist.py`'s ALLOW_LIST and **not** in
`.claude-plugin/hooks-template.json` (both ship to consumers, F1). Cairn dogfoods it via
self-consumption (INV-011). Consumers receive nothing until a future **firm** D7 retirement ADR
adds the ALLOW_LIST rows. This is the only mechanically-honest "internal-only" posture.

**D7 — Acceptance (D9 alignment).** Unit tests cover: the fired-detection render (D2), the
unconditional load-or-form fallback + the previously-uncovered load-or-form-intent node, and
neutral/state-aware emission + the budget clamp (D3/D5). Trial-E dogfood is the integration test.

## Consequences

### Easier

- D5's open carrier contract is resolved with a buildable, dep-free, honest-minimal design.
- Cairn dogfoods the carrier with **zero consumer blast radius** (D6).
- The fatal stale-load mode is structurally defused by the unconditional fallback (D4).
- The L-012 tier-sensitivity hazard is designed out, not merely noted (D5).

### Harder

- Consumers keep paying the cold-start orientation friction through the Trial-E window — the
  friction win is **deferred**, not delivered.
- The ≤2k budget has only a byte-proxy backstop + an EXPOSED CI gate (D3).
- "Fired on host" is unprovable by unit test; only Trial-E observes it (D2).
- A D7 follow-on must build the CI tokenizer gate and the build_dist ALLOW_LIST rows before any
  consumer ship.

## Alternatives Considered

- **A — thin bash hook, "internal-only" via the shipped template.** *Refuted (fatal).* "Internal
  only" is mechanically impossible: build_dist ships `hooks-template.json` unconditionally (F1), so
  landing the SessionStart block either dangles a hook on every consumer session or ships the full
  blast radius. D adopts A's thin-emitter core but registers it in local `.claude/settings.json`.
- **B — D1-literal SKILL payload, ship-to-consumers-now.** *Refuted (fatal).* A static SKILL body
  structurally cannot emit D5's dynamic pointer ("fires but does not point"); its distinguishing CI
  tokenizer budget gate is dep-forbidden. B collapses into D's dynamic emitter + byte-clamp.
- **C — defer the carrier; run Trial E on the skill alone.** *Refuted as the realization (strongest
  safety case).* Un-actions the imperative D5/D1 "build the carrier" without a superseding ADR —
  out of this slice's authority — and deletes the D9 fired-detection test scope. Its verified merits
  (neutral emission, a fallback-only test, the load-or-form coverage gap) are **harvested into D**.

## Risk Register

| ID | Risk | Prob | Impact | Mitigation |
|----|------|------|--------|------------|
| R1 | Consumer distribution blast radius (stale `.slice-system` / non-CC host) | n/a now | High | Deferred to D7; D6 cairn-internal-only neutralizes it for the trial |
| R2 | L-012 tier-sensitive hard-refusal on imperative carrier prose | Med | High | D5 neutral, state-accurate emission + read-only suppression; unit-tested |
| R3 | ≤2k budget drift with no CI token gate | Med | Med | D3 byte-clamp backstop; CI tokenizer EXPOSED + deferred (dep-forbidden today) |
| R4 | Stale/closed-feature pointer emitted verbatim (pre-mortem S2) | Med | Med | D5 handoff-state-token awareness; the unconditional fallback reproduces — does not correct — a stale handoff, so handoff hygiene stays an operator responsibility |
| R5 | "Fired on host" unobservable by unit test | High | Low | Accepted: render-tested at unit, host-injection is the Trial-E integration observation (D9) |

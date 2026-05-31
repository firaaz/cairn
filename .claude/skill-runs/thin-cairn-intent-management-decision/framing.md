# /decision — thin-cairn-intent-management

## Question

Should cairn retire the predefined four-phase pipeline (`cairn-tdd-feature`) in favor of
**intent management** (the thin-substrate direction's Trial E), and if so, how — adjudicating
the 7 open questions below?

## Inputs (read these)

- `docs/plans/2026-05-31-thin-cairn-intent-management.md` — the brainstorm design (committed
  8476d8c): agreed shape, components, how the pre-mortem reshaped it. **Primary input.**
- `docs/adr/cairn-thin-substrate-direction.md` — accepted direction (D1–D8). D8 retains the
  firm phase ADRs + INV-003; Trial E gated on premise_guard (shipped) + Trial D.
- `docs/plans/2026-05-20-cairn-thin-substrate-trials.md` — Trials A–E, probes A/B/C, open Qs.
- `docs/spec-v2.md` — feature-loop + daily-usability proposal (UNPROMOTED; spec-v1 canonical).
- `docs/adr/delivery-mechanism-friction.md` — `using-cairn` SessionStart carrier (D1, unbuilt).

## Agreed shape (from brainstorm)

Intent = always-on anchor; approval delta-triggered (not per-session); fluid construction
bracketed by **two decorrelation checkpoints** (front-loaded intent-challenge + fresh
close-review); contract mandatory, graduated by size, with a completeness floor. New skill
coexists with `cairn-tdd-feature`. First real run = Trial E.

## Pre-mortem already done

A 6-refuter adversarial pre-mortem (workflow `intent-management-design-premortem`, 2026-05-31)
reshaped the design: it found "approve every session" **fatal** (ceremony recreation +
stale-load), and the semantic-misread gap **serious** (fixed by the front-challenge). See the
spec's "How this answers the pre-mortem" section. Phase 1 here should BROADEN beyond this
(scale / integration / technical scenarios), not repeat it.

## The 7 open questions = the decision agenda

1. "Material change" threshold that re-triggers approval + front-challenge.
2. Completeness-floor mechanism (cardinality vs. attestation vs. agent check).
3. Decorrelation strength — same-family vs. cross-family for challenge/review.
4. SessionStart carrier contract — testable "fired" definition + fallback + ≤2k-token budget.
5. Fate of the four-phase substrate — retirement trigger; firm phase ADRs + INV-003.
6. Multi-session / multi-operator intent divergence.
7. Trivial-session boundary (touches-repo → needs thin intent vs. exempt read-only/Q&A).

## Constraints to respect

- Daily-usability is first-class (the reason v1 was abandoned; spec-v2 §2).
- No new orchestrator/MCP/daemon/state layer (ADR out-of-scope). Deps: pydantic/typer/pyyaml.
- ADR D8 retains the firm phase ADRs + INV-003 — methodology is orthogonal to the grounding
  identity, not auto-superseded.
- Cairn is consumed downstream (`.slice-system → .`); changes have cross-repo blast radius.

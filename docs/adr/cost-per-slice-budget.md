---
id: cost-per-slice-budget
name: "Cost-per-slice budget — INV-009 provisional introduction with advisory-only semantics"
status: accepted
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: scope
adrs-referenced: [orchestrator-observability, slice-close-contract, feature-slice-model, cliff-failure-mode-and-v1-defenses, context-discipline-protocol]
invariants-touched: [INV-009]
date: 2026-04-24
---

# cost-per-slice-budget: Per-slice total spend and token-count budget

## Status
Accepted

## Date
2026-04-24

## Context

Cairn has an ambient-context invariant (INV-004, ≤40k turn-1 tokens) but **no invariant on per-slice total spend**. A full cairn slice fires four subagent dispatches (writer, skeptic, implementer, integrator), each with its own system prompt, artifact re-reads, and cache-cold start. Portfolio project (a cherry-pick consumer of cairn's ideas) reportedly achieves "almost-as-good" outcomes at roughly a quarter of cairn's cost — the ~4× premium lives in dispatch, not in ambient context or enforcement hooks. Until tokens-and-dollars per phase are recorded in the canonical observability artifact, every downstream optimization (Lever 1 per-phase model config, Lever 2 compression, Track B lightweight-slice hatch) is vibes-based.

This ADR is produced alongside the `cost-discipline/track-0-telemetry` slice, which lands the measurement plumbing (additive fields on `<slug>-result.json`, `--output-format json` at the subagent dispatch site, a `_record_phase_cost(phase, tokens, model)` helper, a dated `PRICING_TABLE_<date>` module constant, and a Cost section in `<slug>-result.md`). Measurement without an invariant is a dashboard; measurement with an invariant is a discipline. This ADR supplies the invariant.

**Why provisional, not firm.** The invariant *shape* (per-slice total tokens + per-slice total USD ≤ threshold) is evidence-driven and correct. The *thresholds* are not yet evidence-bound — they cannot be set before the next three slices are measured. Shipping a firm invariant with made-up thresholds would either fire false-red (blocking real work) or false-green (making the invariant a no-op). Provisional firmness with advisory-only failure mode at introduction lets the invariant exist as a discipline-signalling artifact while its threshold accumulates evidence. Precedent: `orchestrator-observability` (provisional, iterating on consumer evidence); `INV-004` was advisory at introduction and became hard only after its first baseline landed.

**Why cost-per-slice, not cost-per-phase or cost-cumulative.** Cost per-phase is subordinate — optimizing a cheap phase while an expensive one bloats is a loss. Cumulative cost across a session is noise for a solo operator: the unit of work is the slice, and comparing slice A against slice B (or against the same slice under a different model config) is the actionable comparison. This matches design-plan OQ#2 (`/status` surfaces per-slice cost, not cumulative).

## Decision

Cairn commits to a new provisional invariant **INV-009 — Cost-per-slice budget**, bundling four properties:

### D1 — Invariant shape

The telemetry plumbing defined by the `cost-discipline/track-0-telemetry` slice produces two scalars per slice in `<slug>-result.json`:

- `tokens_total` — sum across the four token classes (`input`, `cache_creation`, `cache_read`, `output`) across all subagent dispatches in the slice's lifecycle.
- `cost_total_usd` — sum of `cost_by_phase_usd`, each per-phase entry computed from the `pricing_snapshot` recorded at slice init and the observed per-phase token counts.

INV-009 asserts:

> `tokens_total` ≤ `Y TBD` tokens AND `cost_total_usd` ≤ `$X TBD` USD, where the thresholds are set from measured baseline per D2.

Both conjuncts must hold for the invariant to pass. Thresholds are enforced conjunctively (not independently) because token-and-dollar drift couple: a slice can be token-cheap and dollar-expensive (Opus-heavy), or token-expensive and dollar-cheap (Sonnet-heavy). Both surfaces need ceilings.

### D2 — Threshold-setting procedure (evidence-bound)

Thresholds `X` and `Y` are deliberately `TBD` at this ADR's introduction. The rebaseline procedure mirrors INV-004's precedent:

1. **Land telemetry** — the `cost-discipline/track-0-telemetry` slice (this slice) ships the plumbing.
2. **Accumulate baseline** — either (a) re-run the three most recent closed slices' `close_slice` telemetry against archived commits to harvest three data points, or (b) accept a forward-only baseline: record `cost_total_usd` / `tokens_total` on the next three slices.
3. **Set threshold at `ceil(p75 × 1.25)`** — 75th-percentile of observed values times 1.25 headroom to absorb fan-out and retries. Record baseline data points in a dedicated follow-on slice (`housekeeping/inv009-rebaseline-<reason>`).
4. **Rebaseline when floors shift.** Compounding floor changes — model price changes, compression landing, platform system-prompt growth — that cross the current threshold trigger a new `housekeeping/inv009-rebaseline-<reason>` slice.

The `ceil(p75 × 1.25)` formula is a named convention, not a speculative ideal. The 1.25 multiplier absorbs known-but-unpredictable cost sources (retry amplification, cluster fan-out beyond single dispatch, cache-cold starts). Narrower multipliers fire false-red; wider multipliers fire false-green. The `p75` (rather than `p95` or `max`) biases toward catching sustained drift rather than worst-case outliers.

### D3 — Firmness: provisional, advisory-only at introduction

`INV-009` ships with:

- **Firmness: provisional.** Promotes to firm after either (a) one rebaseline cycle demonstrates discipline (threshold holds for ≥3 slices without false-positive mutes), or (b) a consumer project other than the known cherry-pick consumer adopts the invariant. The strategic plan names "adoption by one project other than portfolio" as the existence test for cairn clearing academic-land; that adoption event is an acceptable firmness-promotion trigger.

- **Advisory-only at introduction.** While thresholds are `None` (the default both in the check helper and in `scripts/slice_orchestrator.py`'s `INV_009_COST_THRESHOLD_USD` / `INV_009_TOKEN_THRESHOLD` module constants), the INV-009 machine check emits a `UserWarning` rather than raising. This is deliberate: a red-fail invariant whose threshold is `None` would either (a) coerce to `0` and block every non-empty slice, or (b) require a separate mute toggle that makes the invariant a no-op in practice. The warn-only discipline signal is more honest: "we committed to the invariant, we have not yet committed to a threshold." Once thresholds are numeric (set by a rebaseline slice), the same check body raises on breach.

- **Precedent.** INV-004's first landing was advisory; the first `housekeeping/inv004-rebaseline` slice (2026-04-16) set its first measurable threshold. `orchestrator-observability` is provisional on a schema whose consumer is the yet-unlanded fleet-coordinator. Both ADRs accept that the evidence-gathering window is a named stage of the invariant's lifecycle, not a design failure.

### D4 — Machine check (test-file assertion; AST/grep migration deferred)

At introduction, the INV-009 machine check is a test-file assertion in `tests/unit/test_slice_orchestrator_cost.py` (landed by the `cost-discipline/track-0-telemetry` slice's Phase 2 skeptic). The test references the most-recent `<slug>-result.json` in `.claude/orchestrator-debug/` and runs a helper (`_check_inv_009(state, cost_threshold, token_threshold)`) whose branch logic is:

- If either threshold is `None` → emit `UserWarning("INV-009 advisory: thresholds TBD at introduction ...")` and return `"advisory"` (test passes).
- If both thresholds are numeric → assert `cost_total ≤ cost_threshold` and `tokens_total ≤ token_threshold`. Breach raises `AssertionError("INV-009: ...")`.

The module-level constants `INV_009_COST_THRESHOLD_USD` and `INV_009_TOKEN_THRESHOLD` on `scripts/slice_orchestrator.py` default to `None` and are the single source of truth for the threshold values. A rebaseline slice updates those constants; no test-file rewrite is required.

**Migration path.** AST/grep anchoring for the INV-009 invariant-check block lands under `cliff-failure-mode-and-v1-defenses` D2's design slice when that slice runs. The `docs/ARCHITECTURE.md` entry for INV-009 ships a `type: test-ref` block that points to the test file above, matching the interim convention for assertion blocks whose machine check is pytest-anchored.

### D5 — Operational envelope (what this ADR does NOT do)

INV-009 governs the per-slice telemetry surface. It does **not**:

- Plumb `--max-budget-usd` into subagent dispatch (design-plan OQ#3; deferred until baseline variance observed).
- Halt a mid-phase subagent when a budget is crossed (requires graceful-abort work not yet scoped).
- Impose hard-fail semantics at introduction (design-plan OQ#1 recommendation: advisory at intro; this ADR adopts that recommendation).
- Cumulate cost across slices in `/status` (design-plan OQ#2; per-slice only).
- Govern consumer-project pricing tables (design-plan OQ#5; park as roadmap for multi-vendor support).

Bumping `schema_version` on `<slug>-result.json` is explicitly out of scope for the plumbing slice per `orchestrator-observability` D4 (additive fields do not bump schema_version); INV-009's check reads the additive fields without version-gating.

## Invariant declaration

**INV-009** — *Cost-per-slice budget (provisional, advisory-only at introduction).* A slice's total token consumption (`tokens_total`) and total dollar cost (`cost_total_usd`), as recorded in `.claude/orchestrator-debug/<slug>-result.json` at close, do not exceed thresholds `Y` and `$X` respectively. Thresholds are set by a rebaseline slice at `ceil(p75 × 1.25)` over a baseline of three measured slices (or the next three slices forward-only, per D2). While thresholds are `None`, the machine check is advisory (warns on every invocation) rather than raising; the invariant still exists as a discipline-signalling commitment.

Machine-check path at introduction: `tests/unit/test_slice_orchestrator_cost.py` (the Phase 2 skeptic test file introduced by the `cost-discipline/track-0-telemetry` slice). `/refresh-architecture` propagates this to `docs/ARCHITECTURE.md` as a `type: test-ref` invariant-check block; AST/grep anchoring migrates under D2's design slice.

## Consequences

**Made easier:**

- Downstream cost-discipline levers (Lever 1 per-phase model config, Lever 2 compression, Track B lightweight-slice hatch) all become measurable against a named invariant rather than argued against vibes.
- Closed slices accrete a per-slice cost record in `<slug>-result.json` via the `pricing_snapshot`/`cost_by_phase_usd`/`cost_total_usd` fields; historical reinterpretation at cost-at-the-time stays correct because `pricing_snapshot` is copied from the dated `PRICING_TABLE_<date>` constant at slice init, not looked up retroactively.
- Operator-visible cost surface: `<slug>-result.md` carries a Cost section with a totals line and a per-phase table; `/status` surfaces a one-line cost per-slice (current and last-closed) without drifting into cumulative noise.

**Made harder:**

- Pricing changes ship as **new** dated `PRICING_TABLE_<date>` constants, not edits to an existing constant. This is a deliberate friction: silent price drift — the kind that makes "our cost dropped last week" invisible in git log — is refused by construction.
- Rebaseline discipline adds a new operational cadence. A slice touching any compounding cost floor (model price change, compression landing) owes a `housekeeping/inv009-rebaseline-<reason>` slice if the change crosses the current threshold. Precedent: INV-004's rebaseline slices (two landed so far).
- Because INV-009 is warn-only at introduction, Phase-4 auditors verifying "invariant passes" must distinguish pass-with-warning (advisory fire) from pass-silently (thresholds numeric, observation under ceiling). Documented explicitly in `docs/operational-reference.md`.

**Invariant impact:**

- **INV-009 (new, provisional).** Declared by this ADR. `/refresh-architecture` propagates to `docs/ARCHITECTURE.md` with a `type: test-ref` invariant-check block naming `tests/unit/test_slice_orchestrator_cost.py`.
- **INV-003 (phase contracts).** Unchanged. The plumbing slice adds telemetry at the dispatch site without modifying the four-phase pipeline, phase-role assignments, or agent-prompt content. The Phase-3/4 agents do not need to know cost is being measured; dispatch-site instrumentation is transparent to them.
- **INV-004 (≤40k turn-1 tokens).** Unchanged. `/status`'s one-line cost addition is bounded within INV-004's existing budget. `tests/unit/test_context_budget.py` continues to pass without edit.
- **INV-006 (always-create feature file).** Satisfied by the companion `cost-discipline/track-0-telemetry` slice landing `.claude/features/cost-discipline.yaml` with this slice and the follow-on `cost-discipline/lever-1-per-phase-model` slice declared.
- **INV-008 (slice-close contract).** Unchanged. `close_slice` is not modified by the plumbing slice; the existing state-persist already captures the final values at close. No new commit sites, no `mkdir`, no wipe-path changes.

**Operational envelope:**

- `PRICING_TABLE_<date>` is reserved as a module-level convention in `scripts/slice_orchestrator.py`. Multiple dated constants may coexist (historical); `_init_state_dict` references the current one to seed `pricing_snapshot`. Pricing-change slices add a new constant and update the reference; the old constant is retained for interpreting archived slices.
- `INV_009_COST_THRESHOLD_USD` and `INV_009_TOKEN_THRESHOLD` module constants in `scripts/slice_orchestrator.py` are the single source of truth for the INV-009 threshold values. They default to `None`; rebaseline slices flip them to numeric.
- `.claude/orchestrator-debug/<slug>-result.json` gains additive fields (`tokens_by_phase`, `cost_by_phase_usd`, `model_by_phase`, `tokens_total`, `cost_total_usd`, `pricing_snapshot`) per `orchestrator-observability` D4's additive-safe contract. `schema_version` stays at `"1.0"`.

## Alternatives Considered

### A1 — Firmness choice

| Approach | Core idea | Why rejected or chosen |
|----------|-----------|------------------------|
| **A1a — Firm at introduction with numeric thresholds guessed now** | Pick `$5 USD / 500k tokens` (or similar) based on operator estimate; ship firm | Rejected: threshold without measured baseline is a vibes commitment. False-red on normal slices kills the invariant's credibility; false-green makes it a no-op. Evidence-bound thresholds are the whole point of D2 |
| **A1b — Advisory firm** | Firm firmness, warn-only semantics baked into the invariant-check | Rejected: firmness and enforcement-mode are separate knobs. Firm firmness signals "shape is stable, supersession costs supersession ADR"; advisory-only semantics signal "enforcement evidence not yet sufficient." Coupling them muddles both signals |
| **A1c — Chosen: provisional, advisory-only, threshold-TBD** | Provisional firmness + advisory-only at intro + rebaseline procedure named | Invariant exists as a discipline commitment; threshold-TBD is explicit; rebaseline path is documented; promotion-to-firm trigger is named (rebaseline cycle OR external consumer adoption) |

### A2 — Threshold formula

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **A2a — Hard max from 3 baseline slices** | Threshold = max observed cost; trip on any excess | Too tight: absorbs no retry or fan-out headroom; guaranteed false-red on next non-trivial slice |
| **A2b — p95 × 2.0** | Biases toward catching only extreme outliers | Too loose: invariant becomes a no-op for all but pathological slices; loses drift-detection signal |
| **A2c — Chosen: p75 × 1.25** | Balance between catching sustained drift and absorbing known-variance sources | Named, defensible multiplier; 1.25 matches fan-out + retry empirical range per design-plan risk register; p75 biases toward sustained-drift detection |

### A3 — Scope: per-slice vs per-phase vs cumulative

Discussed above under Context (D1 rationale) and in the design-plan OQ#2 recommendation. Per-slice wins because: (a) the slice is the unit of work for a solo operator; (b) per-phase optimization without slice-level ceilings leads to whack-a-mole (optimize phase 3, phase 1 bloats, total unchanged); (c) cumulative across a session is noise — the actionable comparison is slice-to-slice under varying model config.

### A4 — Pricing table placement

| Approach | Core idea | Why rejected or chosen |
|----------|-----------|------------------------|
| **A4a — External YAML file** | `.claude/pricing/2026-04-24.yaml`; orchestrator reads at init | Rejected: adds a file-discovery surface and YAML-parsing dependency; pricing changes should be visible in git log as Python commits, not YAML edits. Matches orchestrator-observability's stdlib-only new-code rule |
| **A4b — Single mutable table** | One `PRICING_TABLE` dict, edited on price changes | Rejected: silent pricing drift is the failure mode this ADR is trying to prevent. A single mutable table invites PR-free edits that invalidate archived slice cost records |
| **A4c — Chosen: dated module constants, append-only** | `PRICING_TABLE_<YYYY>_<MM>_<DD>` per pricing update; `_init_state_dict` references the current one; `pricing_snapshot` deep-copies at init | Every price change is a visible diff; `pricing_snapshot` in state preserves historical interpretability; stdlib-only; matches INV-004's additive-constant convention |

## Risk Register

- **R1 — Threshold-setting slice never lands.** INV-009 stays advisory-only forever. Mitigation: `cost-discipline/lever-1-per-phase-model` slice (the measurement target for the first rebaseline) is already sequenced in `.claude/features/cost-discipline.yaml` with `after: [cost-discipline/track-0-telemetry]`; a third slice (`housekeeping/inv009-rebaseline-initial`) is the natural follow-on after two data points accumulate. If neither lands within ~10 slices post-Track-0, the invariant itself is re-evaluated rather than the threshold set by fiat.

- **R2 — Pricing table drifts silently.** A future contributor edits an existing `PRICING_TABLE_<date>` constant rather than adding a new dated constant, invalidating archived slice cost records whose `pricing_snapshot` was deep-copied at their init time. Mitigation: `pricing_snapshot` is copied at init, not looked up at close; archived state files stay self-contained. A future `reality-check.sh`-style hook could grep for edits to existing pricing constants (deferred to a dedicated slice if drift is observed).

- **R3 — Retries double-count tokens.** Mitigation: `_record_phase_cost` is idempotent per-phase (overwrites on retry, does not accumulate); retry counts already live in `retries_by_phase` per `orchestrator-observability` D4. Cost attribution stays attached to the most recent successful dispatch. This is contracted as V14 / V18 in the Phase 2 skeptic test file.

- **R4 — `claude -p --output-format json` envelope shape drifts.** Mitigation: the slice's Precondition P1 captured the live envelope shape via smoke-test on 2026-04-24 before Phase 1 accepted; the Phase 2 skeptic's fixture (`FIXTURE_ENVELOPE_RAW`) encodes the observed shape verbatim. If Anthropic changes the envelope, `_parse_usage_envelope` fails visibly (fixture test breaks, not silently producing zeros).

- **R5 — Pricing-snapshot bloat in state JSON.** Low. Typical `pricing_snapshot` is ~1 KB per slice even with multiple priced models; negligible against existing state-file size. If multi-vendor support lands (design-plan OQ#5), snapshot may grow; re-evaluate at that point.

- **R6 — Advisory-only at introduction masks real overruns.** The `UserWarning` emit is observable in pytest output and in the Cost section of `<slug>-result.md`, but a harried operator may skim past it. Mitigation: the operational-reference documents the advisory semantics explicitly; the first rebaseline cycle is scoped to convert advisory to hard within 3 measured slices.

### Assumption audit

This ADR is provisional; formal Phase 5 verification is not required. Primary believed assumptions:

- **`ceil(p75 × 1.25)` is a sensible formula at the 3-slice baseline scale.** Believed. Small-sample percentile estimates are noisy; the 1.25 multiplier over-accommodates this by design. If the first rebaseline cycle reveals the threshold being repeatedly crossed by <10% margins, the formula is the first thing to re-examine.
- **Operator will actually land a rebaseline slice within the target window.** Believed. R1 names the mitigation (10-slice window re-evaluation).
- **Token counts from `claude -p --output-format json` are authoritative for dispatch spend.** Believed. The envelope emits `usage.{input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}` plus a `total_cost_usd` field and `modelUsage` per-model breakdown. Cairn uses the four token classes + its own `PRICING_TABLE` rather than the envelope's `total_cost_usd` because: (a) pricing_snapshot discipline requires cairn-controlled arithmetic; (b) envelope costs may bundle flags (e.g., max-budget-usd pre-charge) that cairn wants to see isolated; (c) cairn's own per-1k rates are auditable at the dated-constant level.

## Consequences for in-progress work

- **`cost-discipline/track-0-telemetry` (this slice).** Ships the measurement plumbing and the ADR + ARCHITECTURE entry + feature file + operational-reference + status documentation. INV-009 is introduced advisory-only at close.
- **`cost-discipline/lever-1-per-phase-model` (next slice).** Per-phase model-config plumbing; generates the first measured cost-delta data points. Explicit dependency via `.claude/features/cost-discipline.yaml` `after: [cost-discipline/track-0-telemetry]`.
- **`housekeeping/inv009-rebaseline-initial` (follow-on).** First threshold-setting slice once three slices of cost data accumulate. Flips `INV_009_COST_THRESHOLD_USD` and `INV_009_TOKEN_THRESHOLD` from `None` to numeric; no ADR edit required (the threshold-setting mechanism is already contracted by this ADR's D2).
- **`cliff-failure-mode-and-v1-defenses` D2 design slice (future).** AST/grep anchoring for INV-009's invariant-check block lands when D2 runs; this ADR's `type: test-ref` block migrates at that time.

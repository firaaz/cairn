# Cost discipline — Track 0 (measurement) and Lever 1 (per-phase model config) design

Date: 2026-04-23
Status: design (precedes ADR + slices)
Supersedes: none
Related: `docs/plans/2026-04-18-session-compression-audit.md`, `docs/plans/2026-04-20-observability-and-close-slice-design.md`, `~/.claude/plans/actually-it-looks-like-glimmering-journal.md` (strategic plan approved 2026-04-23)

## Problem

Cairn has a measured ambient-context invariant (INV-004, ≤40k turn-1 tokens) but **no invariant on per-slice total spend**. In practice a full cairn slice fires four subagent dispatches (writer, skeptic, implementer, integrator), each with its own system prompt, artifact re-reads, and cache-cold start. Portfolio project (a cherry-pick consumer of cairn ideas) achieves "almost-as-good" outcomes at roughly a quarter of cairn's cost — the 4x premium lives in dispatch, not in ambient or enforcement. Cairn already acknowledges in spec §1 that the methodology is "pure waste" for work that doesn't warrant the full four-phase split.

Two orthogonal cost levers are available now, both under-spec:

1. **Telemetry** — the orchestrator already emits observability state (`phase_timings`, `retries_by_phase`, `cluster_dispatches`) but does not track **tokens consumed per phase** or **dollar estimate per slice**. Without these, every downstream optimization is vibes-based.
2. **Per-phase model** — operator memory (`project_per_phase_model_and_thinking.md`) flags that phases 3 and 4 are mechanical enough to run on Sonnet (≈5x cheaper than Opus) with no output-quality hit. Never acted on.

This design covers both. Track 0 (telemetry + governing invariant INV-009) lands first, because Lever 1's effect is unmeasurable without it.

## Non-goals

- **Compression (Lever 2 per strategic plan).** Slices C/D/F remain on their own track. Track 0 precedes them so their cost impact is measurable.
- **Cutting hooks, validator, role_guard, INV-004, or handoff-as-pointer.** These are zero-LLM-cost enforcement. Not on the table.
- **New escape hatches for lightweight slices.** That is Track B in the strategic plan; separate design.
- **Replacing Opus everywhere.** Phases 1 and 2 (writer, skeptic) stay on Opus-high by explicit design — they are the load-bearing synthesis phases.

## Track 0 — measurement infrastructure

### INV-009 — cost-per-slice budget (proposed)

**Shape.** Per-slice total spend ≤ $X USD AND per-slice total tokens ≤ Y tokens, where:
- Token count sums input + cache_creation + cache_read + output across all subagent dispatches in the slice's lifecycle.
- Dollar estimate uses per-model published pricing × token class, computed at close.

**Threshold.** Deliberately left as `X TBD / Y TBD` in the initial ADR. The first-cut threshold comes from **measured baseline**, not guess. Procedure:
1. Land telemetry (Track 0 slice).
2. Re-run the three most recent closed slices' `close_slice` telemetry against archived commits to get three data points. If re-run is infeasible, accept forward-only baseline: measure the next three slices (one per week of normal operator cadence).
3. Set threshold at `ceil(p75 × 1.25)` to allow 25% headroom for fan-out and retries. Record baseline data points in the ADR.
4. Rebaseline discipline matches INV-004's precedent — a dedicated `housekeeping/inv009-rebaseline-<reason>` slice when a compounding floor change (model price change, compression landing, platform system-prompt growth) crosses the threshold.

**Firmness.** `provisional` at introduction. Matches `orchestrator-observability`'s precedent: the invariant shape is correct, but the threshold is evidence-bound and the measurement is not yet consumer-driven. Promotes to firm after (a) one rebaseline cycle demonstrates discipline, or (b) a consumer project adopts the invariant. The strategic plan names "adoption by one project other than portfolio" as the existence test for cairn clearing academic-land.

**Machine check.** Initially a test-file assertion against the most recent `<slug>-result.json` in `.claude/orchestrator-debug/`. Migrates to AST/grep anchoring under cliff-failure-mode-and-v1-defenses D2 when that lands. Per INV-009's own provisional status, advisory-failure only at introduction (warning, not red) — red after the first threshold is set from measured data.

### Telemetry extension

**Schema additions to `<slug>-result.json`** (additive, per orchestrator-observability D4 contract — does NOT bump `schema_version`):

```python
{
    # ... existing fields ...
    "tokens_by_phase": dict,     # {phase_str: {"input": int, "cache_creation": int, "cache_read": int, "output": int}}
    "cost_by_phase_usd": dict,   # {phase_str: float} — computed from tokens × model pricing
    "model_by_phase": dict,      # {phase_str: str} — resolved at dispatch time, records actual model used
    "tokens_total": int,         # sum across all four token classes across all phases
    "cost_total_usd": float,     # sum of cost_by_phase_usd
    "pricing_snapshot": dict,    # {"opus-4-7": {"input_per_1k": float, ...}, ...} — records the table used
}
```

**Why `pricing_snapshot`.** Prices change. Archived slices should be reinterpretable at their cost-at-the-time, not retroactively reshaped when pricing moves. Snapshot belongs in the state dict.

**Source of token counts.** `claude -p` subprocess emits usage metadata when invoked with `--output-format json` (single-result JSON) or `--output-format stream-json` (streamed). The orchestrator currently dispatches without either (`scripts/slice_orchestrator.py:984-992`, cmd is `claude -p --agent <role> --permission-mode <mode> <inputs>`), so output is raw text. Slice 1's envelope adds `--output-format json` and parses the result envelope for `usage.input_tokens` / `output_tokens` / `cache_creation_input_tokens` / `cache_read_input_tokens`, aggregating per-phase and attributing to the model recorded in `model_by_phase[phase]`. **Flag shape confirmed 2026-04-23 via `claude -p --help`**: `--output-format`, `--model`, `--effort`, `--max-budget-usd`, `--verbose` all exist as named. `--output-format json` changes stdout parsing — the current text-tail parser at `_dispatch_once` will break until slice 1 lands the JSON envelope reader.

**Close-summary surfacing.** `<slug>-result.md` (deterministically generated from JSON per observability D2) gains a **Cost** section with:
- Total tokens + total USD at the top
- Per-phase table: phase | model | tokens | USD
- Pricing snapshot reference (not full dump; just "pricing: 2026-04-23 table" with a link)

**`/status` integration.** Surfaces current-slice's running cost (if slice active) and last-closed-slice's total cost. One line each. Bounded by INV-004's token budget on `/status` output.

### Implementation points in `scripts/slice_orchestrator.py`

Concrete sites (line numbers from 2026-04-23 HEAD; verify at slice-open):

- `scripts/slice_orchestrator.py:234-258` `_init_state_dict` — add the seven new fields with zero/empty defaults.
- `scripts/slice_orchestrator.py:~380-400` `_persist_state` / `_write_result_md` — extend MD projection to render the Cost section.
- Subagent dispatch site (search: `claude -p` or `_run_claude_subprocess`) — parse usage metadata, call a new `_record_phase_cost(phase, tokens_dict, model)` helper that updates `tokens_by_phase`, `cost_by_phase_usd`, `model_by_phase`, `tokens_total`, `cost_total_usd`. Idempotent per-phase (overwrites on retry, not accumulates — retries are already counted in `retries_by_phase`).
- `close_slice` — no change required. The existing state-persist already captures the final values at close.
- New module-level constant `PRICING_TABLE_2026_04_23` or similar, with a dated comment — so pricing changes are explicit commits, not silent edits.

### Expected slice: `cost-discipline/track-0-telemetry` (or similar feature/slice id)

Single slice, envelope:
- `scripts/slice_orchestrator.py` — the additions above
- `tests/unit/test_slice_orchestrator_cost.py` — new; verifies additive fields, pricing attribution, idempotent retry behavior, JSON-to-MD projection
- `docs/adr/cost-per-slice-budget.md` — new ADR; introduces INV-009 provisional
- `docs/ARCHITECTURE.md` — new invariant entry for INV-009 + invariant-check block
- `docs/operational-reference.md` — document the new env-var behavior, the cost surfacing in `/status` and close summary
- `commands/claude-code/status.md` / `.full.md` — describe the cost line

Out of envelope: model config (Lever 1 lands as a separate slice after Track 0 measurement is green).

## Lever 1 — per-phase model config

### `AGENT_MODEL_CONFIG`

Module-level dict in the orchestrator:

```python
# Pricing floor — phases 1/2 are synthesis-heavy, phases 3/4 are mechanical.
# Per project_per_phase_model_and_thinking.md (operator memory, 2026-04-23).
# --effort choices (from `claude -p --help`): low | medium | high | xhigh | max
AGENT_MODEL_CONFIG = {
    "phase-1-writer":       {"model": "claude-opus-4-7",   "effort": "high"},
    "phase-2-skeptic":      {"model": "claude-opus-4-7",   "effort": "high"},
    "phase-3-implementer":  {"model": "claude-sonnet-4-6", "effort": "medium"},
    "phase-4-integrator":   {"model": "claude-sonnet-4-6", "effort": "low"},
    "issue-triager":        {"model": "claude-opus-4-7",   "effort": "medium"},
}
```

### Env-var overrides

Per-role override precedence: env-var > dict default. Names follow pattern `CAIRN_MODEL_<ROLE_UPPER_UNDERSCORE>` and `CAIRN_EFFORT_<ROLE_UPPER_UNDERSCORE>`. Example: `CAIRN_MODEL_PHASE_3_IMPLEMENTER=claude-opus-4-7 CAIRN_EFFORT_PHASE_3_IMPLEMENTER=high` for a slice where the operator judges the implementer will hit Opus-worthy complexity.

A third native flag — `--max-budget-usd <amount>` — is documented by `claude -p --help` and caps a dispatch's spend. Slice 1 does **not** plumb it; decision on a per-phase or per-slice hard cap is Open Question #3, to be answered after baseline measurement. Named here because its existence affects the design space: the enforcement hook is upstream, not something cairn needs to build.

Rationale for env-var granularity at role level (not slice level): operator flips it for an in-flight experiment, reverts next slice. Slice-level would require an intent.md field, which is premature — we don't yet have evidence that per-slice variation matters.

### Dispatch plumbing

`_run_claude_subprocess` (or whatever dispatches `claude -p`) takes `role` as an argument (probably already does, for logging). It resolves config via:

```python
def _resolve_model_config(role: str) -> tuple[str, str | None]:
    env_model = os.environ.get(f"CAIRN_MODEL_{role.upper().replace('-', '_')}")
    env_thinking = os.environ.get(f"CAIRN_EFFORT_{role.upper().replace('-', '_')}")
    default = AGENT_MODEL_CONFIG.get(role, {"model": "claude-opus-4-7", "thinking": "high"})
    return (env_model or default["model"], env_thinking or default["thinking"])
```

Passed to `claude -p` via `--model <model>` and `--effort <level>`. Flag names confirmed 2026-04-23 via `claude -p --help`. Insertion point: `scripts/slice_orchestrator.py:984-992` (the `cmd = ["claude", "-p", "--agent", role, ...]` list) — splice `--model` and `--effort` args after `--agent <role>`. Keep resolver pure-Python; no shell-escaping surprises because `subprocess.Popen` is called with a list, not a shell string.

`model_by_phase[phase]` (from Track 0 schema) records the *resolved* model, so cost attribution is honest even when env-var overrides fire.

### Expected slice: `cost-discipline/lever-1-per-phase-model` (or similar)

Envelope:
- `scripts/slice_orchestrator.py` — `AGENT_MODEL_CONFIG` dict, `_resolve_model_config` helper, dispatch plumbing
- `tests/unit/test_slice_orchestrator_model_config.py` — new; verifies default resolution, env-var override precedence, dispatch flag passing
- `docs/operational-reference.md` — document `CAIRN_MODEL_<ROLE>` / `CAIRN_EFFORT_<ROLE>` env-vars alongside existing `CAIRN_<KNOB>` pattern
- `.claude/agents/phase-*.md` — no change expected; agent instruction content is model-agnostic

No new ADR. This is a knob, not a structural change. The ADR that would be required is if we committed to a specific cost target (e.g., "Opus is forbidden in phases 3/4"). We do not commit to that; we commit to a tunable default.

Out of envelope: compression (Lever 2); lightweight-slice hatch (Track B).

### Expected measurement (to validate the slice worked)

Run two slices of comparable shape — one with default config, one with `CAIRN_MODEL_PHASE_3_IMPLEMENTER=claude-opus-4-7 CAIRN_MODEL_PHASE_4_INTEGRATOR=claude-opus-4-7` (pre-change parity). Compare `cost_total_usd` from the two `<slug>-result.json` files. Target: default-config slice ≥30% cheaper on phases 3+4. Actual outcome recorded in sweep-notes at close.

## Slice decomposition

| Order | Slice id candidate | Envelope | Why this order |
|---|---|---|---|
| 1 | `cost-discipline/track-0-telemetry` | orchestrator + test + ADR + ARCHITECTURE + operational-reference + status command | Nothing downstream measurable without this |
| 2 | `cost-discipline/lever-1-per-phase-model` | orchestrator + test + operational-reference | Immediate 40% financial reduction lever; needs Track 0 to prove it |

Both slices live under one feature: `cost-discipline` (per INV-006 always-create-feature-file policy).

## Risk register

- **`claude -p` output schema not yet confirmed.** Medium. Mitigation: verification step before slice 1 opens; slice cannot begin Phase 1 until the flag + JSON format are confirmed in a smoke test. Added to the slice's intent `preconditions` when it opens.
- **Pricing table drifts silently.** Low. Mitigation: `PRICING_TABLE_<date>` constant with dated comment, pricing_snapshot in every state file. Changing prices is a visible commit.
- **Sonnet on phase 3/4 regresses output quality.** Medium (acknowledged by operator but unverified). Mitigation: default is configurable via env-var; ship, measure, and if the next three integration slices run on Sonnet and all green with no regressions flagged, we treat the hypothesis as validated. If regression emerges, the env-var override is the immediate remedy, and the slice 2 commit can be reverted without touching telemetry.
- **Subagent retries double-count tokens.** Medium. Mitigation: `_record_phase_cost` is idempotent per-phase (overwrites on retry) rather than accumulating. Retry count already captured separately in `retries_by_phase`. Cost attribution stays attached to the successful dispatch.
- **Pricing snapshot bloat in state JSON.** Low. One model line per phase; total under 1 KB even with three models. Not a size concern.

## Open questions (seeds for future /decision)

1. **Should INV-009 be a hard fail or advisory-only at introduction?** Precedent: INV-004 is hard; orchestrator-observability D4 schema is advisory on new fields. Recommendation: advisory at introduction (warn, don't fail); promote after first rebaseline.
2. **Does `/status` surface cost per-slice or cumulative (across all slices this session)?** Recommendation: per-slice only. Cumulative is noise for a solo operator; distracts from the current unit of work.
3. **Do we need a `CAIRN_COST_BUDGET_USD` slice-level cap that halts dispatch when crossed?** Deferred. Requires knowing how to halt a mid-phase subagent gracefully, which requires separate work. First ship visibility; decide enforcement after observing baseline variance.
4. **Lightweight-slice hatch (strategic plan Track B) interaction.** A lightweight slice by design skips subagent dispatch, so its cost is ≈0 (just shell hooks). Track 0's schema has a natural slot for this (all `tokens_by_phase` empty, `cost_total_usd = 0`). When Track B lands, nothing in this design needs to change.
5. **Multi-consumer pricing tables.** If cairn ships to a consumer using a different model vendor, `PRICING_TABLE` becomes consumer-configurable. Out of scope for v1; park as roadmap.

## Verification (cross-slice)

After both slices land:
1. `<slug>-result.json` for the two slices shows populated cost fields.
2. Close summary and `/status` display the totals.
3. A measured comparison (default config vs pre-change-parity env override) shows the expected ~40% reduction on phases 3+4.
4. INV-009 check runs against the most recent slice's result file; advisory pass.
5. Sweep-notes at close of slice 2 records the baseline numbers that seed the eventual threshold-setting.

If step 3 does not show the expected reduction (within tolerance), that is a finding — either the cost model is wrong (mitigation: re-examine pricing table + token aggregation) or phases 3/4 are not as Sonnet-compatible as memory assumed (mitigation: revert default via env-var override, land memory update, open separate design slice to understand which phases should stay Opus).

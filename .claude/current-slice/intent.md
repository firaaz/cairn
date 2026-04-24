---
slice: cost-discipline/track-0-telemetry
date: 2026-04-24
phase: 1-intent
v1-scope: cliff-failure-mode-and-v1-defenses D2 (introduces a new machine-checkable invariant — INV-009 — alongside ADR codification)
invariants-introduced: [INV-009]
invariants-touched: [INV-003, INV-004, INV-006, INV-008]
adrs-referenced:
  - orchestrator-observability   # D4 additive-safe schema contract relied on
  - slice-close-contract         # INV-008 close_slice surface preserved
  - feature-slice-model          # INV-006 always-create feature file
adrs-created:
  - cost-per-slice-budget        # this slice introduces INV-009; enforced via V6 structural check + envelope scope-guard + V7 ARCHITECTURE.md entry
preconditions:
  - "Smoke-test `claude -p --output-format json` usage envelope BEFORE Phase 1 accepts. Confirm the result-JSON exposes `usage.input_tokens`, `usage.output_tokens`, `usage.cache_creation_input_tokens`, `usage.cache_read_input_tokens` (or document the actually-emitted field names so the parser keys against reality, not the design-doc guess). Per design plan risk register L163."
  - "Flag existence already confirmed 2026-04-23 via `claude -p --help`: `--output-format`, `--model`, `--effort`, `--max-budget-usd`, `--verbose` exist as named."
envelope:
  - "scripts/slice_orchestrator.py"
  - "tests/unit/test_slice_orchestrator_cost.py"
  - "tests/unit/test_invariant_assertions.py"  # Amendment 2026-04-24 (phase-4 raise-issue): widen EXPECTED_INVARIANT_IDS at :1115 to include INV-009; scope-gap caught by Phase 4 auditor Ground 2
  - "docs/adr/cost-per-slice-budget.md"
  - "docs/ARCHITECTURE.md"
  - "docs/operational-reference.md"
  - "commands/claude-code/status.md"
  - "commands/claude-code/status.full.md"
  - ".claude/features/cost-discipline.yaml"
out-of-scope:
  - "Lever 1 per-phase model config (CAIRN_MODEL_<ROLE>, CAIRN_EFFORT_<ROLE>, AGENT_MODEL_CONFIG dict, dispatch --model/--effort plumbing) — own follow-on slice cost-discipline/lever-1-per-phase-model"
  - "Lever 2 compression slices (Slices C/D/F under their own track)"
  - "Track B lightweight-slice escape hatch (separate strategic-plan track)"
  - "`--max-budget-usd` plumbing into dispatch (design-plan OQ#3, deferred until baseline variance observed)"
  - "Hard-fail INV-009 enforcement (OQ#1 recommendation: advisory at introduction; promotes after first rebaseline)"
  - "Cumulative /status totals across slices (OQ#2 recommendation: per-slice only)"
  - "Multi-consumer / multi-vendor pricing tables (OQ#5 — roadmap)"
  - "AST/grep anchoring for INV-009 invariant-check (lands under cliff-failure-mode-and-v1-defenses D2 design slice when D2 runs)"
  - "Bumping schema_version (additive-only fields per orchestrator-observability D4 contract)"
  - "Phase-3 / Phase-4 implementer/integrator agent-prompt changes beyond what dispatch-site token-capture plumbing implicitly requires (the agents do not need to know cost is being measured)"
  - "close_slice edits — existing state-persist already captures final values at close (design plan §Implementation points)"
  - "init_new_slice edits, new commit sites, mkdir surprises, generalised state-shape rewrites"
---

# Intent — cost-discipline/track-0-telemetry

## What and Why

**What.** Land Track 0 of the cost-discipline program: per-phase token-usage and dollar-cost telemetry inside `scripts/slice_orchestrator.py`, recorded in the `<slug>-result.json` state file under additive fields, projected into a Cost section in the derived `<slug>-result.md`, and governed by a new provisional invariant **INV-009 — cost-per-slice budget**. The dispatch site at `:984-992` gains `--output-format json`, parses the usage envelope, and routes per-phase totals through a new idempotent `_record_phase_cost(phase, tokens, model)` helper.

**Why.** Cairn has no invariant on per-slice spend. A measured 4× cost premium over a cherry-pick consumer (portfolio) lives in subagent dispatch — but every optimization downstream (Lever 1 per-phase model, Lever 2 compression, Track B lightweight hatch) is vibes-based until tokens-and-dollars per phase are recorded in the canonical observability artifact. Track 0 must land first because nothing downstream is measurable without it (design plan §Slice decomposition).

**Boundary.** Telemetry plumbing + ADR + advisory invariant only. Lever 1, Lever 2, Track B, hard-fail INV-009, cumulative `/status`, `--max-budget-usd` plumbing, and AST anchoring for the INV-009 check are all out of scope per the envelope above. No source-shape rewrites; additive fields per orchestrator-observability D4; no `schema_version` bump; close_slice untouched.

## Specification Detail

### S1 — Seven additive fields in `_init_state_dict`

`scripts/slice_orchestrator.py:234-258` (`_init_state_dict`) gains the following keys with zero/empty defaults. None bumps `schema_version` (additive-safe contract per `orchestrator-observability` D4).

```python
"tokens_by_phase":   dict,   # {phase_str: {"input": int, "cache_creation": int, "cache_read": int, "output": int}}
"cost_by_phase_usd": dict,   # {phase_str: float}
"model_by_phase":    dict,   # {phase_str: str} — resolved model recorded at dispatch
"tokens_total":      int,    # sum across all four token classes across all phases
"cost_total_usd":    float,  # sum of cost_by_phase_usd values
"pricing_snapshot":  dict,   # {model_id: {"input_per_1k": float, "cache_creation_per_1k": float, "cache_read_per_1k": float, "output_per_1k": float}}
```

(Six field-names above; the seventh additive surface is the module-level constant in S4 whose contents seed `pricing_snapshot` at slice start.)

### S2 — Dispatch site adds `--output-format json` and parses usage

**Amendment 2026-04-24 (phase-4 raise-issue Ground 1):** the original S2 wording below was insufficient — the Phase-3 implementer landed helpers but did NOT wire them into `_dispatch_once`, leaving the telemetry as dead code. The line-specific integration requirements below are MANDATORY and checked structurally in V3.

**S2.a — Required edit site 1.** In `_dispatch_once` (currently at `scripts/slice_orchestrator.py:1172` function start, cmd list at `:1190-1198`), the `cmd = [...]` list for the subagent dispatch MUST include the literal pair `"--output-format", "json"` as command arguments. The `grep` check `grep -n '"--output-format"' scripts/slice_orchestrator.py` must return at least one match inside the `_dispatch_once` function body.

**S2.b — Required edit site 2.** After the `claude -p` subprocess returns (currently around `:1235-1256` in `_dispatch_once`), the orchestrator MUST call `_record_phase_cost(phase, _parse_usage_envelope(stdout), model)` (or an equivalent call-pattern passing the parsed usage and dispatched model to the recorder). A grep of `_record_phase_cost` in `scripts/slice_orchestrator.py` MUST show at least one call outside the definition at `:407`. `_parse_usage_envelope` MUST similarly show at least one call outside its definition at `:340`.

**S2.c — Parser adaptation.** The structured-tail parser for agent-returned JSON (e.g. `proposed_slice_id`, `status`) is unchanged — the agent's stdout lives inside the `claude -p` JSON envelope's `result` field. Only the outer-envelope reader is new. The envelope shape is a JSON array of event objects (`init` / `assistant` / `rate_limit_event` / `result`); the `result` event is terminal and holds both `usage` (with keys `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` — confirmed via P1 smoke-test 2026-04-24) and a top-level `total_cost_usd` field.

**S2.d — Error tolerance.** If the JSON envelope is malformed or the `result` event is absent (e.g. a subprocess crashed mid-stream), the cost-recording step MUST NOT crash the dispatch. Log a warning to stderr and proceed with empty `tokens` for that phase — this matches the idempotent-retry contract in §S3.

**S2.e — Resolved model attribution.** Pass the *resolved* model string (from `AGENT_MODEL_CONFIG` / env-var overrides in the future; currently the runtime default) as the `model` argument to `_record_phase_cost` so `model_by_phase[phase]` records the actually-dispatched model.

### S3 — `_record_phase_cost(phase, tokens, model)` helper, idempotent per-phase

A new pure helper at the module level updates `tokens_by_phase[phase]`, `cost_by_phase_usd[phase]`, `model_by_phase[phase]`, then recomputes `tokens_total` and `cost_total_usd` from the post-update dicts.

**Idempotent per-phase**, not accumulating: a redispatch of the same phase **overwrites** the entry rather than adding to it. Retry counts already live in `retries_by_phase` (firm field per orchestrator-observability D4); cost attribution stays attached to the most recent successful dispatch. This matches the design plan's risk-register mitigation for "subagent retries double-count tokens" (design L166).

### S4 — `PRICING_TABLE_2026_04_24` module constant

A dated constant `PRICING_TABLE_2026_04_24` (or the slice's actual close date, fixed at Phase 3) holds per-model `{"input_per_1k": float, ...}` for every model the orchestrator may dispatch. The dated suffix is load-bearing: pricing changes ship as **new** dated constants in visible commits, not silent edits to a single mutable table. `_init_state_dict` copies this table into `pricing_snapshot` so archived slices stay reinterpretable at their cost-at-the-time.

### S5 — `_write_result_md` Cost section

The pure-function projection that derives `<slug>-result.md` from the state JSON gains a **Cost** section. Content (per design plan §Close-summary surfacing):

- One line: `Total: <N> tokens, $<X.XX> USD` (top of the section).
- One table: phase | model | tokens | USD (one row per `phases_completed`).
- One footer line: `pricing: <PRICING_TABLE constant name>` (no full table dump in the MD).

Cadence is unchanged (terminal transitions only, per orchestrator-observability D5). MD continues to be derived deterministically from JSON; no independent MD write path.

### S6 — INV-009 introduction (provisional, advisory-only)

A new ADR `docs/adr/cost-per-slice-budget.md` introduces **INV-009 — cost-per-slice budget**:

- **Shape.** Per-slice total spend ≤ `$X TBD` USD AND per-slice total tokens ≤ `Y TBD` tokens, where the sums are the `tokens_total` / `cost_total_usd` fields of the slice's `<slug>-result.json`.
- **Threshold.** Deliberately `X TBD / Y TBD` at introduction. Procedure for setting the first cut documented per design plan §INV-009: re-run telemetry against three recent closed slices (or accept forward-only baseline of next three slices), set threshold at `ceil(p75 × 1.25)`, record baseline data points in the ADR, rebaseline via dedicated `housekeeping/inv009-rebaseline-<reason>` slice when a compounding floor change crosses it (mirrors INV-004 precedent).
- **Firmness.** `provisional`. Promotes to firm after either (a) one rebaseline cycle demonstrates discipline, or (b) a consumer project other than portfolio adopts the invariant.
- **Machine check.** Initially a test-file assertion in `tests/unit/test_slice_orchestrator_cost.py` against the most recent `<slug>-result.json` in `.claude/orchestrator-debug/`. Migrates to AST/grep anchoring under cliff-failure-mode-and-v1-defenses D2 when that slice runs.
- **Advisory at introduction.** Per OQ#1 recommendation: warn-only, no red fail at introduction (precedent: orchestrator-observability D4 schema is advisory on new fields; INV-004 became hard only after baseline). Promotes to red after the first measured threshold lands.

### S7 — `docs/ARCHITECTURE.md` invariant entry

A new INV-009 entry plus its `invariant-check` block, additive to the existing INV-001..INV-008 sequence. Citation: `(cost-per-slice-budget)`. The `invariant-check` block points to the test-file assertion landing in S6.

### S8 — `docs/operational-reference.md` documentation

Three additions, additive only:

- The `PRICING_TABLE_<date>` constant convention and the rule that pricing changes ship as new dated constants.
- Advisory semantics of INV-009 at introduction (warn, don't fail) and the rebaseline path.
- The Cost section in `<slug>-result.md` and the one-line cost surfacing in `/status`.

### S9 — `commands/claude-code/status.md` and `status.full.md`

Both files describe the one-line cost surfacing — **per-slice only, not cumulative** (per OQ#2). Two cases:

- Slice active: one line showing the current slice's running cost (`tokens_total` / `cost_total_usd` from the in-progress `<slug>-result.json`).
- Last-closed slice: one line showing the last-closed slice's total cost.

INV-004's token budget on `/status` output is preserved — one line each, bounded.

### S10 — Feature file at `.claude/features/cost-discipline.yaml` (always-create)

Created this slice per INV-006 (feature-slice-model D3 always-create). Lists this slice plus the planned follow-on `cost-discipline/lever-1-per-phase-model` (Lever 1) with `after: [cost-discipline/track-0-telemetry]`, since Lever 1 is unmeasurable without Track 0.

### S11 — What is NOT touched

`schema_version` stays at `1.0` (additive only). `close_slice`, `_is_slice_already_closed`, the wipe step, and the resume matrix are all untouched (existing state-persist captures the final values at close per design plan). `commit_phase_handoff` is not extended. No new commit sites. No `mkdir`. The Phase-3/4 agents need no prompt changes beyond what dispatch-site instrumentation transparently provides.

## Boundary

**In scope.** Exactly the eight envelope files listed above (scripts, test, ADR, ARCHITECTURE, operational-reference, two status command files, feature file).

**Out of scope.** Lever 1 model-config plumbing; Lever 2 compression; Track B lightweight hatch; `--max-budget-usd` enforcement; hard-fail INV-009; cumulative `/status`; multi-vendor pricing tables; AST/grep anchoring for INV-009 (waits on D2's design slice); schema_version bump; close_slice edits; agent-prompt changes; new commit sites.

## Verification

### Structural assertions (Phase 4 Auditor, grep / file-presence)

- **V1** `_init_state_dict` initialization carries all six new field-keys (`tokens_by_phase`, `cost_by_phase_usd`, `model_by_phase`, `tokens_total`, `cost_total_usd`, `pricing_snapshot`) with empty/zero defaults. No existing field removed or retyped. `schema_version` literal still equals `"1.0"`.
- **V2** Module-level constant whose name matches `^PRICING_TABLE_\d{4}_\d{2}_\d{2}$` exists in `scripts/slice_orchestrator.py`; it is a dict with at least one entry whose value contains `input_per_1k`.
- **V3** The dispatch-site command list at the subagent dispatch site contains the literal `"--output-format"` followed by `"json"`.
- **V4** A new helper `_record_phase_cost` exists with signature accepting `(phase, tokens_or_usage, model)` (positional or keyword).
- **V5** `_write_result_md` (or its renamed equivalent) produces output containing the literal heading `## Cost` and the literal token `pricing:` when state has any populated `tokens_by_phase` entry.
- **V6** `docs/adr/cost-per-slice-budget.md` exists; YAML frontmatter `firmness: provisional`; body contains the literal token `INV-009`, the literal `X TBD`, the literal `Y TBD`, and the rebaseline procedure prose.
- **V7** `docs/ARCHITECTURE.md` contains a new `**INV-009**` entry AND a sibling `invariant-check INV-009` block that points to `tests/unit/test_slice_orchestrator_cost.py`. ADR citation `(cost-per-slice-budget)` present.
- **V8** `docs/operational-reference.md` contains documentation for the `PRICING_TABLE_<date>` constant convention, the INV-009 advisory semantics, AND the Cost section in `<slug>-result.md`.
- **V9** `commands/claude-code/status.md` AND `commands/claude-code/status.full.md` each contain one cost-surfacing line description; neither contains the words "cumulative" or "across slices" applied to cost.
- **V10** `.claude/features/cost-discipline.yaml` exists, contains slice id `cost-discipline/track-0-telemetry`, and lists `cost-discipline/lever-1-per-phase-model` with `after: [cost-discipline/track-0-telemetry]`.
- **V21** (Amendment 2026-04-24) `_dispatch_once` body (the function whose docstring mentions agent subprocess dispatch) contains at least one call to `_record_phase_cost(` with arguments — i.e., `grep -n '_record_phase_cost(' scripts/slice_orchestrator.py` must return MORE than one line (one is the `def`; additional lines prove callers exist). Same check for `_parse_usage_envelope(`.
- **V22** (Amendment 2026-04-24) `tests/unit/test_invariant_assertions.py:~1115` constant `EXPECTED_INVARIANT_IDS` (or equivalent-named set) contains `"INV-009"`. `uv run pytest tests/unit/test_invariant_assertions.py` exits zero — no regressions from the INV-009 introduction.

### Behavioral assertions (Phase 2 Skeptic test file `tests/unit/test_slice_orchestrator_cost.py`, Phase 4 Auditor verifies green)

- **V11** Defaults: a freshly-initialized state dict has `tokens_by_phase == {}`, `cost_by_phase_usd == {}`, `model_by_phase == {}`, `tokens_total == 0`, `cost_total_usd == 0.0`, `pricing_snapshot` is a non-empty dict copied from `PRICING_TABLE_<date>`.
- **V12** JSON usage parsing: feeding the JSON-envelope reader a recorded fixture of `claude -p --output-format json` output produces a tokens dict with the four expected keys (`input`, `cache_creation`, `cache_read`, `output`), all non-negative ints.
- **V13** Pricing attribution: `_record_phase_cost("phase-1-writer", {input:1000, cache_creation:0, cache_read:0, output:1000}, "claude-opus-4-7")` populates `cost_by_phase_usd["phase-1-writer"]` to the value computed by `(1000/1000)*input_price + (1000/1000)*output_price` from the snapshot — exact arithmetic, not approximate.
- **V14** Idempotent retry: two consecutive `_record_phase_cost("phase-3-implementer", ..., ...)` calls leave `tokens_by_phase["phase-3-implementer"]` equal to the **second** call's tokens (overwrite, not sum). `retries_by_phase` is independently asserted unchanged by this helper.
- **V15** JSON→MD projection: rendering an MD from a state with two populated phase entries produces a `## Cost` section containing both phase rows, the totals line, and the `pricing:` footer. Text fixture-match.
- **V16** PRICING_TABLE constant presence: `from scripts import slice_orchestrator` (or equivalent), the test asserts at least one attribute matching `^PRICING_TABLE_\d{4}_\d{2}_\d{2}$` exists and is a non-empty dict.
- **V17** INV-009 advisory check: the test that asserts INV-009 against the most recent `<slug>-result.json` warns (does not fail / does not raise) when thresholds are still TBD; the warn-vs-fail switch is gated on the threshold being a non-`None` numeric.

### Property-style checks (stdlib only, no Hypothesis — precedent: tests/unit/test_context_discipline_protocol.py:12)

Uses `random.Random(seed)` with fixed seed for determinism. No third-party generator library (CLAUDE.md stdlib-only rule + slice rescope 2026-04-12).

- **V18** Idempotency property (`_record_phase_cost` overwrite-not-sum). Seed `random.Random(42)`. Generate a sequence of 50 `(phase, tokens, model)` triples drawn from {phase-1-writer, phase-2-skeptic, phase-3-implementer, phase-4-integrator} × random non-negative token dicts × one model. Apply all 50 in order. Assert for each phase: final `tokens_by_phase[phase]` equals the **last** triple's tokens for that phase (found by replay), not an accumulated sum. Same assertion for `cost_by_phase_usd[phase]`: equals cost computed from the last triple's tokens, not a sum of per-call costs.
- **V19** Additivity property (totals equal sum-of-parts). Seed `random.Random(43)`. Build 10 populated states each with a random subset of phases populated (1–4 phases) and random non-negative token dicts. For each state assert `tokens_total == sum(v for phase_tokens in tokens_by_phase.values() for v in phase_tokens.values())` AND `cost_total_usd == sum(cost_by_phase_usd.values())` (within float tolerance `1e-9` for cost_total_usd, exact for tokens_total).
- **V20** Non-negativity + zero-invariant property (arithmetic soundness). Seed `random.Random(44)`. For 100 random non-negative token dicts: `_record_phase_cost` result yields `cost_by_phase_usd[phase] >= 0.0`. Separately: calling `_record_phase_cost("phase-1-writer", {input:0, cache_creation:0, cache_read:0, output:0}, <any known model>)` yields `cost_by_phase_usd["phase-1-writer"] == 0.0` exactly (not approximately).

### Invariant checks (Phase 4 Auditor)

- **INV-009 (introduced)** — provisional, advisory-only at introduction. Evidence: ADR exists with `firmness: provisional`; ARCHITECTURE.md entry plus invariant-check block exist; test-file assertion exists and is advisory-only when threshold TBD.
- **INV-003** — phase contracts unchanged. Evidence: no edits to `commands/claude-code/start-slice.md`, no edits to `.claude/agents/phase-*.md`, no edits to the Phase Skill Guide. Dispatch plumbing only.
- **INV-004** — `/status` output stays bounded. Evidence: `commands/claude-code/status.md` and `.full.md` describe one cost line each, not a multi-slice dump; `tests/unit/test_context_budget.py` continues to pass (no new ambient context loaded by `/status`).
- **INV-006** — feature file at `.claude/features/cost-discipline.yaml` exists per always-create. Evidence: file present, structurally valid YAML, slice listed.
- **INV-008** — `close_slice` lifecycle untouched. Evidence: no edits to `close_slice`, `_is_slice_already_closed`, `_wipe_current_slice`, `_bundle_handoff_md`, or the resume matrix; existing state-persist already captures the final cost values at close (no new write path needed).

### Precondition gate (must clear BEFORE Phase 1 accepts)

- **P1** Smoke-test `claude -p --output-format json` on a trivial prompt; capture the actual envelope shape; record observed key paths for `usage.{input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens}` (or whatever is actually emitted) into the Phase 2 test fixtures so the parser keys against reality. If the envelope shape disagrees materially with the design-doc assumption, **the slice does NOT proceed to Phase 2** until the implementation S2/S3 is updated; this is a real gate, not advisory (design-plan risk register L163).

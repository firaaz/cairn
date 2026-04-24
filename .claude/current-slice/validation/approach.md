# Phase 2 Approach — cost-discipline/track-0-telemetry

## Strategy

Single new file `tests/unit/test_slice_orchestrator_cost.py` exercises the Phase-3
contract across 22 tests mapped 1:1 to intent §Verification V11–V20 (plus two
light preservation/helper complements). Tests import `slice_orchestrator` via the
existing `pyproject.toml` `pythonpath=["scripts"]` hook and never spawn a
`claude` subprocess. Each test asserts either module-attribute shape (V11, V16,
V17), helper behaviour (V12–V15), or property-style invariants (V18–V20 using
`random.Random(seed)` per `test_context_discipline_protocol.py` precedent — no
Hypothesis per CLAUDE.md stdlib-only rule).

At this phase: 18/22 are RED. The 4 already-green are preservation assertions
(`schema_version` stays `"1.0"`) and three tests of the test-file-local
`_check_inv_009` advisory helper whose warn-vs-fail semantics are contracted at
Phase 2 and frozen thereafter.

## Ambiguity resolution

- **Envelope shape (precondition P1).** Unlocked by live smoke-test on
  2026-04-24: `claude -p --output-format json` emits a JSON array; the terminal
  `type=="result"` element carries `usage.{input_tokens,
  cache_creation_input_tokens, cache_read_input_tokens, output_tokens}` plus
  `modelUsage`. Fixture `FIXTURE_ENVELOPE_RAW` encodes this verbatim.
- **Parser name.** `_parse_usage_envelope(raw_stdout)` chosen (matches existing
  `_parse_structured_tail` convention). Phase 3 may rename but must update both
  sides.
- **Phase-key convention.** Role-strings (`phase-1-writer`…) per V13/V14/V18.
- **PRICING_TABLE constant.** Regex `^PRICING_TABLE_\d{4}_\d{2}_\d{2}$`; Phase 3
  picks the slice close date.
- **INV-009 thresholds.** Module constants `INV_009_COST_THRESHOLD_USD`,
  `INV_009_TOKEN_THRESHOLD` default to `None` at introduction (advisory-only per
  design OQ#1). `_check_inv_009` emits `UserWarning` when `None`; raises on
  breach when numeric.
- **pricing_snapshot independence.** Deep-copy of PRICING_TABLE at init
  (archive reinterpretability).
- **Unknown-model behaviour.** Unspecified by intent; not exercised.

## Out of scope for Phase 2

No production code. No tests for `--max-budget-usd`, Lever 1 model plumbing,
cumulative `/status`, hard-fail INV-009, or multi-vendor pricing (all deferred
per intent out-of-scope list). No edits to Phase-3/4 agent prompts.

# Phase 2 Approach — cost-discipline/lever-1-tier-retune

## Test surface

All retune assertions live in the existing
`tests/unit/test_slice_orchestrator_model_config.py` (per intent §Spec Detail
Edit 2; brief's `tests/unit/scripts/slice_orchestrator/` path conflicts with
the project's flat-test convention and is resolved out-of-scope by Phase 1).
No new test file is created; no production code is read beyond the
already-public `AGENT_MODEL_CONFIG` literal and the `_resolve_model_config`
contract documented in §Spec Detail.

## RED set

Two retune-row assertions — net new from §Verification:

- `test_default_phase_3_implementer_resolves_sonnet_high` — P3 effort high.
- `test_default_phase_4_integrator_resolves_opus_low` — P4 model opus.

Plus seven in-place retunes of the prior lever-1-per-phase-model T-numbered
coverage that pinned the old defaults: T2, T3, T6, T10 (x2), T11-default,
and `test_agent_model_config_default_values_match_spec`. Together: nine
tests RED at Phase 2; `uv run pytest tests/unit/test_slice_orchestrator_model_config.py -q`
reports `9 failed, 23 passed`.

## GREEN regression guards

Six §Verification bullets re-assert contracts that the retune must NOT
change: P1, P2, triager defaults; both env-override-still-wins paths
(P3 effort, P4 model — the operator-revert paths named in §Why); and
unknown-role fallback (locks `_resolve_model_config` body byte-identical
per §Spec Detail). These pass today and must keep passing — they catch
scope creep into the helper body or accidental drift on unchanged rows.

## Ambiguities resolved

- *Brief envelope vs intent envelope* (`dispatch.py` vs `core.py`; new test
  dir vs existing flat file) — resolved by Phase 1's intent §Spec Detail;
  wiring already shipped under lever-1-per-phase-model, this slice only
  retunes literals.
- *`_dispatch_once` argv-shape tests post-retune* — kept structural; values
  follow from `_resolve_model_config` and are covered by the unit-level
  defaults tests, no extra dispatch-level argv asserts needed.

No spec ambiguity unresolved; no `RAISE_ISSUE` warranted.

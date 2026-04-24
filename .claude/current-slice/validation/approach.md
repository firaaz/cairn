# Phase 2 Approach — cost-discipline/lever-1-per-phase-model

## Strategy

Tests assert the public interface of two new symbols (AGENT_MODEL_CONFIG,
_resolve_model_config) and one dispatch-site invariant (--model/--effort
in argv), corresponding exactly to spec items T1-T10 plus a T11 extension for
the model_by_phase attribution honesty requirement (spec section 4 / INV-009).

## Ambiguities Resolved

**A1 - dispatch site scope.** The brief says "cmd in dispatch_phase_agent"
but the actual cmd list lives in _dispatch_once (called by dispatch_phase_agent).
Tests target _dispatch_once directly (accessible at module level).
_run_with_live_stderr is monkeypatched to capture the argv list without
spawning a subprocess.

**A2 - dispatch_triager not covered.** issue-triager appears in
AGENT_MODEL_CONFIG but dispatch_triager has a separate cmd list not mentioned
in spec section 3. No test is added for triager cmd plumbing - flagged for
Phase 3 to decide whether to extend.

**A3 - empty-string semantics.** T10 is unambiguous: os.environ.get(k) or
default short-circuits on empty string. Tests assert dict default is used.

**A4 - model_by_phase recording timing.** Spec section 4 says "before
subprocess call". Tests assert the post-dispatch value equals the resolved
model; they do not assert ordering relative to the subprocess (unobservable
in isolation). Phase 3 may choose to record model before the call (for
timeout-path honesty) or via the existing _record_phase_cost wiring - either
satisfies T11.

## Test Shape

- **T1-T4, T_default**: parametrised default-resolution cases.
- **T5-T7, T10**: env-var override/empty-string cases (monkeypatch, isolated).
- **T8**: unknown-role fallback to opus/high.
- **T9** (3 variants): argv structure check via _run_with_live_stderr mock.
- **T11** (2 variants): model_by_phase post-dispatch value.
- **Normalisation** (3 cases): hyphen-to-underscore uppercase key derivation.

All 24 tests are RED against current production code.

# Phase 2 — Skeptic approach

## Ambiguity enumeration

1. **`ts` format tolerance.** Intent §Helper contract specifies `datetime.now(timezone.utc).isoformat()` which yields `+00:00`. Test t1b accepts the legacy `Z` shorthand as well so a future stdlib swap does not regress; the parser round-trip via `fromisoformat(ts.replace("Z","+00:00"))` keeps the contract honest.
2. **`count` semantics for `redispatch_cap_exceeded`.** Intent gives `count: int` without specifying base. The cap trips on the **second** redispatch from the same source phase (B15), so `count >= 2` is the contract Phase 2 asserts. Phase 3 may pick exact == 2.
3. **Cost / token threshold breach sites.** `INV_009_*` constants are both `None` (introduced-provisional, `core.py:116-117`); no detection site exists today. Phase 2 RED list (intent §Verification) intentionally omits tests for these two events — flagged here for Phase 3 to either (a) introduce guards alongside the wiring, or (b) leave the emission sites unwired pending rebaseline. Resolution: deferred to Phase 3 per intent (mechanism-only slice; no new ADR).
4. **`agent_timeout` wired-call test.** Intent locates the site at `dispatch.py`'s `subprocess.TimeoutExpired` catch (line 174). Phase 2 covers helper surface only (t1a-d); the wired-call test is out of scope per intent §Verification.

## Test coverage map

- **t1a-t1d** — helper unit contract: append, schema, ISO8601-UTC, F5-tolerant parent-dir creation. Direct calls into `core._record_orchestrator_event`.
- **t2a/t2b** — lifecycle wiring: monkeypatched `dispatch_phase_agent` + `dispatch_triager` (mirrors `test_redispatch_cap.py`); asserts `phase_redispatch` with `from_phase`/`to_phase` and `redispatch_cap_exceeded` with `phase`/`count`. No subprocess fires.
- **t3** — archival pipeline: `_ARTIFACT_RELPATHS` membership + byte-identical snapshot via `_copy_artifacts_to_sweep_results` (mirrors `test_slice_orchestrator_artifact_preservation.py`).

## Confirmed RED

`uv run pytest tests/unit/test_orchestrator_events_capture.py -q` → **7 failed**: t1a-d (`AttributeError: ... _record_orchestrator_event`), t2a/b (`events.jsonl` absent), t3 (`_ARTIFACT_RELPATHS` lacks entry). INV-008 / INV-003 untouched; stdlib-only (`json`, `datetime.timezone.utc`, `pathlib.Path`).

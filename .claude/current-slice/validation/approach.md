---
slice: compression/orchestrator-hardening
phase: 2-validation
date: 2026-04-19
---

# Validation Approach — Skeptic

## Verification artifact map

Intent's `### Verification` block enumerates 8 items. Skeptic-owned coverage:

| Intent item | Skeptic delivers | File |
|---|---|---|
| 1 — `--permission-mode` flag in cmd | `test_f1_dispatch_agent_cmd_includes_permission_mode_flag` (RED) | `tests/unit/test_orchestrator_hardening.py` |
| 1 — value aligns with role_guard | `test_f1_dispatch_agent_permission_mode_value_is_acceptedits` (RED) | same |
| 1 — value behind a module constant | `test_f1_permission_mode_value_lives_in_module_level_constant` (RED) | same |
| 1 (extension) — every dispatch_agent call carries the flag | `test_f1_phase_3_dispatcher_inherits_permission_mode` (RED) | same |
| 2 — `init_new_slice` writes `brief:` verbatim | `test_f2_init_new_slice_writes_brief_key_to_slice_yaml` (RED) | same |
| 2 — `read_slice_state` round-trips | `test_f2_brief_round_trips_through_read_slice_state` + `test_f2_brief_with_embedded_colon_round_trips` (RED ×2) | same |
| 3 — `run_phase_loop` propagates brief | `test_f2_run_phase_loop_propagates_brief_into_phase_1_dispatch` (RED) | same |
| 4 — F3 state-machine tests pass against real slice.yaml | F3 monkeypatch added to existing tests (now GREEN) | `tests/unit/test_slice_orchestrator_state_machine.py:178,196` |
| 5 — suite-level delta | Phase 4 Auditor reconciles (see "Pre-existing failures" below) | — |
| 6 — `validate_architecture.py` exits 0 | Phase 4 Auditor | — |
| 7 — `ruff` clean on envelope | Phase 4 Auditor | — |
| 8 — manual dogfood readiness | Successor-slice marker; not Phase 4 | — |

Verify-RED status at Phase 2 commit:

- `test_orchestrator_hardening.py`: **8 failed** (all 8 RED, expected — Builder must implement F1 + F2 to turn them GREEN).
- `test_slice_orchestrator_state_machine.py::test_v2_6_*` and `::test_a8_*`: **2 passed** (F3 monkeypatch fix is self-contained Skeptic work — no Builder involvement needed).

Run command (rerun before Phase 3 hand-off if state has drifted):
```
uv run pytest tests/unit/test_orchestrator_hardening.py \
              tests/unit/test_slice_orchestrator_state_machine.py::test_v2_6_run_phase_loop_failed_retries_once \
              tests/unit/test_slice_orchestrator_state_machine.py::test_a8_retry_uses_same_inputs_and_envelope -v
```

## Ambiguities enumerated and resolved

Intent.md was scanned for every place a different valid Builder choice could break a downstream commitment. 13 ambiguities surfaced; 13 resolved without escalation. Listed below with the resolution rule applied.

**A1 — F1 literal value of `--permission-mode`.**
Intent §F1: `acceptEdits` "or whichever CLI value aligns with role_guard.py being the effective write-path gate per compression-infrastructure-bootstrap." Resolution: `acceptEdits` is the only Claude Code permission mode that yields `Write`/`Edit`/`MultiEdit`/`NotebookEdit` tool calls to PreToolUse hooks (`default` auto-denies under `-p`; `plan` is read-only; `bypassPermissions` skips hooks entirely). ADR `compression-infrastructure-bootstrap` Decision 2 names role_guard.py as the inner gate analogous to scope-guard. Therefore `acceptEdits` is the unique value that satisfies the ADR. Pin literal in test. Builder may select a different value only by ADR-citing the alternative in `implementation/notes.md` and updating the test in the same commit.

**A2 — F1 "module-level constant" structural commitment.**
Intent §F1: "value is a module-level constant so future audits can locate it without grep." Resolution: test asserts there exists ≥1 UPPERCASE module-level attribute on `slice_orchestrator` whose value equals `"acceptEdits"` — enforces the structural commitment without pinning the constant's *name*. Builder picks the name (`PERMISSION_MODE`, `CLAUDE_PERMISSION_MODE`, etc.).

**A3 — F1 CLI argument form.**
Two-token (`--permission-mode acceptEdits`) vs single-token (`--permission-mode=acceptEdits`). Resolution: existing `dispatch_agent` cmd already uses two-token form for `--agent` (`scripts/slice_orchestrator.py:111`). Test assertion uses `cmd.index("--permission-mode")` then `cmd[idx+1]` — the two-token form. Matches established convention.

**A4 — F2 brief edge cases (multi-line, special chars).**
Intent §F2 commits to "preserving whitespace and quoting." `read_slice_state` is single-line `:`-partition based (`scripts/slice_orchestrator.py:50`). Resolution: cover single-line brief w/ embedded colon (high-value RED — `partition(":")` only splits the first colon, so well-formed serialisations should survive). Skip multi-line briefs — beyond `read_slice_state`'s current capability and would force out-of-envelope changes.

**A5 — F2 `init_new_slice` signature.**
Existing signature: `init_new_slice(brief)` (`scripts/slice_orchestrator.py:335`). Already takes `brief`. ✓ no ambiguity.

**A6 — F2 ordering of `brief:` line in slice.yaml.**
Intent does not specify. Resolution: test asserts `brief:` line exists with the value somewhere in the file; Builder picks placement. Recommended (not enforced): write after `current_phase` to preserve readability.

**A7 — F2 `run_phase_loop(max_phase=1)` test mechanism.**
`run_phase_loop` already accepts `max_phase=4` default (`scripts/slice_orchestrator.py:237`). Passing `max_phase=1` exits the loop after Phase 1 dispatch. ✓ no orchestrator change needed for the test mechanism.

**A8 — F2 how Phase 1 dispatch reads the brief.**
Currently `run_phase_loop` builds `inputs = {"phase": phase, "role": role, "slice_id": _slice_id()}` (line 241) — no `brief`. Resolution: Builder must extend by reading `brief` from `read_slice_state(SLICE_YAML)` and merging into the inputs dict. Test asserts the result via stubbed `dispatch_agent` capture. The reading mechanism (read at loop entry vs read on every iteration) is Builder's choice.

**A9 — F3 monkeypatch site.**
Pattern already established at `tests/unit/test_slice_orchestrator_state_machine.py:170`: `monkeypatch.setattr(so, "_current_phase", lambda: 1, raising=False)`. Resolution: copy this line into the two F3 tests after the existing `monkeypatch.setattr(so, "commit_phase_handoff", ...)` line so the patch is in scope before `run_phase_loop` runs.

**A10 — F3 `_current_phase` return value.**
Both F3 tests assert `call_log.count("phase-1-writer") == 2`. Resolution: `lambda: 1` — loop starts at phase 1, `dispatch_agent` is stubbed to return FAILED, retry-once fires, loop escalates after second FAILED. Asserts hold. ✓

**A11 — F-wire JSON-tail return contract.**
Intent §F-wire: "behaviour unchanged. No new exit statuses." Resolution: existing tests in `test_slice_orchestrator_state_machine.py` (V2.5, V2.6, V2.7, A1, A5, A6, A8) already cover the contract. No new test needed.

**A12 — Stub `subprocess.run` return shape.**
`dispatch_agent` calls `_parse_structured_tail(proc.stdout or "")` (line 126) and returns FAILED if it returns None. Resolution: stub returns `subprocess.CompletedProcess(args=cmd, returncode=0, stdout='{"status": "OK"}', stderr="")` so the parser sees a valid JSON tail. Tests that only inspect `cmd` work fine; tests that need a particular return value can override.

**A13 — `init_new_slice` git side-effects in tests.**
`init_new_slice` calls `subprocess.run(["git", "add", ...], check=False)` and `subprocess.run(["git", "commit", ...], check=False)` after writing `slice.yaml`. Resolution: both use `check=False`, so they fail silently in `tmp_path` (no `.git` dir). No stub required; minor stderr noise is acceptable.

## Pre-existing failures — Phase 4 Auditor reconciliation note

Intent §Verification 5 expects 3 pre-existing failures to remain after this slice (2 `test_adr_rename_sweep`, 1 `test_item_8_dogfooding_findings_section_in_sweep_notes`). At Phase 2 commit time, the full suite shows **18 failures total**:

- 8 — F1+F2 tests in this slice (intentional RED, will go GREEN in Phase 3)
- 3 — `test_adr_rename_sweep` (2) + `test_item_8` (1) → matches intent expectation
- 7 — **NOT mentioned in intent**:
  - 3 × `test_hook_relpath_bypass.py` (TestV1/V2/V3 bare/legacy/slice-system-prefixed)
  - 3 × `test_hook_tolerance.py` (TestV3FrontmatterEditBothForms ×3)
  - 1 × `test_housekeeping_post_slice_a_tidy.py::test_item_d_no_empty_current_slice_subdirs`

These 7 are entirely outside this slice's envelope (no edits to `checks/`, no edits to `tests/unit/test_hook_*.py`). They likely emerged between sweep #20 (when intent was authored) and the Phase 2 commit, OR sweep #20 under-counted. Either way, this is a baseline drift that Phase 4 Auditor must reconcile against the slice's "0 net new failures" commitment.

**Skeptic position:** the 7 baseline failures pre-date this slice's Phase 2 work and are out-of-envelope. They do not block Phase 3 hand-off, but Phase 4 Auditor should:

1. Re-baseline against the actual pre-Phase-2 head (`eb6920d`) to confirm these 7 were already failing.
2. If confirmed pre-existing: log them in `integration/sweep-notes.md` as "baseline carry-over from sweep #20 → 10 (5 documented + 7 undocumented)" and proceed.
3. If any of the 7 were introduced by this slice's Phase 2/3 commits: investigate and either widen the envelope or open a follow-up slice.

## Skeptic open questions for Builder (Phase 3)

1. **PERMISSION_MODE constant placement.** Recommend declaring near the existing `DEFAULT_TIMEOUT_HARD` constant block (`scripts/slice_orchestrator.py:35`) so all dispatcher knobs live together. Not enforced.

2. **`brief` propagation site.** Two reasonable Builder choices: (a) read brief once at `run_phase_loop` entry and pass through to the inputs dict on each Phase 1 dispatch; (b) re-read on every iteration via a helper. Either satisfies the test. Recommend (a) — fewer file reads, brief is immutable post-init per intent.

3. **`init_new_slice` slice.yaml schema.** Builder should consider whether to extend the current minimal write (`id`/`name`/`status`/`current_phase`) to include the canonical fields documented in `start-slice.full.md` Step 4 (`started`, `completed`, `invariants-touched`, `adrs-referenced`, `adrs-created`). This is **out of scope for this slice** per intent §Boundary; flagged here only so Builder doesn't accidentally drift into it. The brief-only extension is the contract.

4. **F3 monkeypatch as fixture?** The two F3 tests both add the same monkeypatch line. A pytest fixture would DRY this. Not enforced — keep the explicit patches per the established style of the file.

## Out-of-scope confirmations

The following intent boundaries are upheld in the test design:

- No edits to `.claude/agents/*.md` (phase-agent prompts).
- No edits to `checks/role_guard.py`, `checks/scope-guard.sh`, `checks/reversibility-guard.sh`.
- No edits to `settings.json`.
- No new exit statuses on `dispatch_agent`.
- No edits to `compression-infrastructure-bootstrap` ADR.
- Sweep-#20 stale-test cleanup (`test_adr_rename_sweep`, housekeeping `test_item_8`) remains deferred to a separate `housekeeping/` micro-slice — F3 explicitly does not bundle this work.

## Hand-off protocol

After this approach.md is committed alongside the test changes, run `/handoff phase` to package Phase 2 context, then `/start-slice phase 3` in a fresh session to enter Implementation. Builder loads only intent.md + the test files (NOT this approach.md, per phase-lock D2's "Builder does not load Phase 2's reasoning about why tests are shaped as they are").

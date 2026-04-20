# Observability and close_slice Hardening — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. This plan is the input to `/start-slice`; Phase 1–4 orchestration turns it into code.

**Goal:** Land INV-008 (slice-close lifecycle correctness) + the provisional observability artifact shape, hardening `close_slice` against R1/R2/R3/R4 and giving downstream consumers a stable substrate at `.claude/orchestrator-debug/`.

**Architecture:** Three logical blocks inside `scripts/slice_orchestrator.py` (observability primitives, lifecycle hardening, heartbeat daemon) plus prompt edits on `.claude/agents/phase-{1..4}-*.md`. State is a single module-level dict persisted atomically on every transition (JSON canonical, MD derived close-only). INV-008 enforcement is three-layered: orchestrator-code skip of `commit_phase_handoff` at max phase, prompt constraint on the Phase-4 agent, and a defensive `git log -1` drift detector.

**Tech Stack:** Python stdlib only (CLAUDE.md constraint — no PyYAML, no requests; threading, json, os, atexit, fcntl-free). pytest via `uv run pytest`. bash for hook surface. No new third-party deps.

---

## Source contracts (read before touching scope)

| Pointer | Role |
|---------|------|
| `docs/adr/slice-close-contract.md` | **Firm.** INV-008 = DC-3 (idempotent close) + DC-4 (sole commit source) + DC-7 (slug isolation). Contracts DC-5 wipe + DC-6 13-row resume matrix. Read **before** editing `close_slice`, `run_phase_loop`, `_slice_id_slug`, or any agent prompt. |
| `docs/adr/orchestrator-observability.md` | **Provisional.** D1–D9: placement, JSON canonical / MD derived, schema v1.0 B2/B3 hybrid, three-level error policy, retention tripwire (100 files / 1 MB), heartbeat cadence defaults. Read **before** adding any observability file path or schema field. |
| `docs/plans/2026-04-20-observability-and-close-slice-design.md` | Design spec. Function signatures, state-dict schema, call graphs, MD sidecar template, 38-test inventory, cluster assignment. The §Testing section is the RED-suite skeleton Phase 2 turns into test files. |
| `docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md` | Rejected-alternatives archive. Consult only on "why not approach X?" questions. |

**Rule:** This plan points to the sources; it does not reproduce their reasoning. When the plan and an ADR conflict, the ADR wins.

---

## Scope & non-goals

**In scope (this slice):**
- Observability primitives (`_atomic_write`, `_persist_state`, `_generate_result_md`, `_write_result_md`, `_append_index_entry`, `_observability_paths`, `_update_state`) + module-level state dict.
- Heartbeat daemon class + main-thread restart detection.
- `close_slice` rewrite — idempotent, wipe-before-commit, slug-isolated.
- `run_phase_loop` skip of `commit_phase_handoff` at `phase == max_phase`; defensive `git log -1` drift check before the close commit.
- `_is_slice_already_closed` precondition (4-signal check).
- `_wipe_current_slice` with file-already-absent tolerance + strict propagation on other `OSError`.
- `_reconcile_resume_state` — 13-row matrix + default-refuse + heartbeat advisory.
- `_persist_state` slug-collision tripwire (read-existing → refuse on `slice_id` mismatch).
- Phase-4 prompt: "do not self-commit" rule. Phase-1..4 prompts: P1 Bash-heredoc escape note + P2 no-preemptive-refuse rule.
- 35 unit tests + 3 integration tests across 8 test files (design doc §Testing).

**Non-goals (deferred slices):**
- Worktree-scoped locking (`fcntl.flock`), PID-scoped role guard, parallel-worktree integration tests.
- Path C (orchestrator-owned writes to `.claude/**`).
- `/decision` Phase 0 + Phase 4 refinements for L-003/L-007.
- Retention policy for `.claude/orchestrator-debug/` (deferred behind D8 tripwire).
- Ruff F841 at `tests/unit/test_post_timeout_reconcile.py:101` (housekeeping slice).
- Phase-4 FAILED path (slice-close-contract D2 "out of scope" note).

---

## Artifact inventory

### Code (create)

- `tests/unit/test_observability_writer.py` — 10 tests (DC-1 + error policy).
- `tests/unit/test_state_schema.py` — 4 tests.
- `tests/unit/test_heartbeat.py` — 7 tests (DC-2).
- `tests/unit/test_close_slice_hardened.py` — 7 tests (DC-3, DC-4 mechanical, DC-5).
- `tests/unit/test_resume_reconcile.py` — 10 tests (DC-6 matrix rows).
- `tests/unit/test_cross_slice_isolation.py` — 3 tests (DC-7) + slug collision tripwire test.
- `tests/unit/test_agent_prompt_updates.py` — 6 tests (P1 ×4, P2, DC-4 prompt).
- `tests/integration/test_signal_observability.py` — 3 tests.

### Code (modify)

- `scripts/slice_orchestrator.py` — three logical blocks added, `close_slice` replaced, `run_phase_loop` gains max-phase skip + defensive check, `main` gains heartbeat start + atexit registration + resume-reconcile call.
- `.claude/agents/phase-4-integrator.md` — add DC-4 anti-behavior ("do not issue `git commit` in Phase 4").
- `.claude/agents/phase-{1,2,3,4}-*.md` — add P1 Bash-heredoc note + P2 no-preemptive-refuse rule.

### Runtime artifacts (created at orchestration time; repo-tracked only if committed)

- `.claude/orchestrator-debug/<slug>-result.json` — per-slice canonical state.
- `.claude/orchestrator-debug/<slug>-result.md` — per-slice human sidecar.
- `.claude/orchestrator-debug/index.jsonl` — shared append-only stream.
- `.claude/current-slice/.heartbeat` — ephemeral, wiped by close_slice DC-5.

### Docs (touch none in this slice)

- `docs/ARCHITECTURE.md` — propagation of INV-008 deferred to the next `/refresh-architecture` (runs from the close handoff, not inside the slice).
- No new ADRs land in this slice; both already landed at `d11277b`.

---

## Cluster assignment (Phase 3 fan-out)

Copied verbatim from design doc §Testing → "Cluster assignment". Phase 2 emits this to `.claude/current-slice/validation/coupling-clusters.yaml`.

```yaml
- name: orchestrator-internals
  files:
    - scripts/slice_orchestrator.py
    - tests/unit/test_observability_writer.py
    - tests/unit/test_state_schema.py
    - tests/unit/test_heartbeat.py
    - tests/unit/test_close_slice_hardened.py
    - tests/unit/test_resume_reconcile.py
    - tests/unit/test_cross_slice_isolation.py
    - tests/integration/test_signal_observability.py

- name: agent-prompts
  files:
    - .claude/agents/phase-1-writer.md
    - .claude/agents/phase-2-skeptic.md
    - .claude/agents/phase-3-implementer.md
    - .claude/agents/phase-4-integrator.md
    - tests/unit/test_agent_prompt_updates.py
```

Rationale: orchestrator code + its unit/integration tests share a single file (`slice_orchestrator.py`); prompt edits are textually independent and can run in parallel.

---

## State-dict schema v1.0 (canonical)

Reproduced for quick reference. Authoritative source: orchestrator-observability D4.

```python
STATE_SCHEMA_VERSION = "1.0"

# Firmly committed (internally motivated)
state = {
    "schema_version": "1.0",
    "slice_id": str,
    "started_at": str,                # ISO 8601 UTC
    "ended_at": str | None,
    "status": str,                    # see enum
    "exit_code": int | None,
    "current_phase": int,             # 1..4
    "phases_completed": list[int],
    "phase_timings": dict,            # {phase_str: {"started_at", "ended_at", "duration_seconds"}}
    "retries_by_phase": dict,         # {phase_str: int}
    "cluster_dispatches": list[dict], # phase-3 trail
    "degradation_reason": str | None, # append-preserving (D7)
    "observability_errors": dict,     # {"persist_state": int, ...}
    "final_commit": str,
    "summary": str,
    # Additive-safe (forward-compat)
    "worktree_path": str,
    "orchestrator_pid": int,
}
```

**Status enum.** Non-terminal: `IN_PROGRESS`, `DEGRADED`. Terminal: `OK`, `FAILED`, `ABORTED`, `ESCALATED`, `SIGNALED`.

**Env vars.** `CAIRN_HEARTBEAT_INTERVAL` (default `10.0`), `CAIRN_HEARTBEAT_STALE` (default `30.0`). Both `int(os.environ.get(...))`-style per CLAUDE.md; document in `docs/operational-reference.md` at close-handoff refresh (not in this slice).

---

## DC-6 resume matrix (13 rows, verbatim from slice-close-contract D4)

| `result.json` status | `slice.yaml` | HEAD | Action |
|----------------------|--------------|------|--------|
| absent | absent | any | Fresh slice — start at Phase 1 |
| absent | `in-progress` | `^slice: .* — init$` | Re-init from slice.yaml |
| absent | `in-progress` | other | Refuse — manual intervention |
| `IN_PROGRESS` | `in-progress` | matches `current_phase` | Resume at `current_phase` |
| `IN_PROGRESS` | `in-progress` | ahead | Refuse — JSON stale |
| `IN_PROGRESS` | `in-progress` | behind | Refuse — expected commit missing |
| `IN_PROGRESS` | `complete` | `slice: complete` | Fix up JSON → OK, exit 0 |
| `OK` | `complete` | `slice: complete` | Already closed, exit 0 |
| `OK` | `complete` | not `slice: complete` | Refuse — commit missing |
| `OK` | `in-progress` | any | Refuse — JSON ahead |
| `DEGRADED` | (any) | (any) | Treat as IN_PROGRESS |
| `FAILED`/`ABORTED`/`SIGNALED` | `in-progress` | any | Refuse — prior terminated |
| corrupt JSON | (any) | (any) | Refuse — parse error |

Default: any state-triple not matching a row refuses with the literal triple printed.

---

## Phase 1 — intent.md (writer)

**Task 1.1:** Produce `.claude/current-slice/intent.md` distilling this plan. Include: goal statement, scope bullets, non-goals bullets, the artifact inventory table, the cluster assignment block, a one-paragraph pointer to each ADR/design doc, and the DC-6 matrix.

**Task 1.2:** Commit:
```bash
git add .claude/current-slice/intent.md .claude/current-slice/handoff-phase-1.md
git commit -m "handoff: phase 1 complete"
```
(Orchestrator emits the phase-1 boundary commit per existing `commit_phase_handoff` flow — unchanged for phases 1–3.)

---

## Phase 2 — RED suite (skeptic)

Phase 2 produces all 8 test files with failing bodies, plus `.claude/current-slice/validation/approach.md` and `coupling-clusters.yaml`.

### Task 2.1 — conftest fixtures

**Create:** `tests/conftest.py` (or extend existing).

**Fixture inventory (required):**
- `orchestrator_tmp_home(tmp_path)` — creates `tmp_path/.claude/current-slice/`, `tmp_path/.claude/orchestrator-debug/`, seeds a minimal `slice.yaml`, initializes a git repo with one commit.
- `mock_state(slice_id, current_phase=1)` — returns a well-formed state dict matching schema v1.0.
- `slug_for(slice_id)` — mirror of `_slice_id_slug` (prevents test bypassing the production mapper).

**Exit criteria:** fixture file commits, then `uv run pytest tests/unit/test_state_schema.py::test_state_dict_includes_schema_version -v` collects (even if it errors).

### Task 2.2 — `tests/unit/test_state_schema.py` (4 tests)

Tests (skeleton bodies referencing symbols that do not yet exist in `scripts/slice_orchestrator.py`):
- `test_state_dict_includes_schema_version` — asserts `state["schema_version"] == "1.0"`.
- `test_state_dict_required_fields_present` — asserts every firmly-committed field from the schema block is present.
- `test_status_enum_values_match_spec` — non-terminal + terminal sets match.
- `test_worktree_path_and_orchestrator_pid_populated_on_init` — after `_update_state(slice_id=...)` followed by the init path, both additive-safe fields are populated (not `None`).

### Task 2.3 — `tests/unit/test_observability_writer.py` (10 tests)

- `test_atomic_write_succeeds_first_attempt`
- `test_atomic_write_retries_once_on_oserror` — mock `os.rename` to raise `OSError` first, succeed second; assert one stderr log, success.
- `test_atomic_write_raises_on_second_failure`
- `test_persist_state_uses_atomic_write` — assert tempfile + rename pattern (stat sequence, or mock verification).
- `test_persist_state_preserves_schema_version`
- `test_write_result_md_only_runs_on_terminal_transition` — call `_persist_state(...)` with `status=IN_PROGRESS`; assert MD file absent. Then with `status=OK`; assert present.
- `test_md_is_derived_from_json_state` (DC-1) — load state JSON, call `_generate_result_md`, assert the output contains `state["slice_id"]`, `state["status"]`, and the phase-timing rows.
- `test_append_index_entry_atomic_under_interleaved_writes` — two threads each append 50 entries; assert 100 well-formed JSON lines.
- `test_degraded_status_replaces_in_progress_on_retry_exhaustion` — force `_atomic_write` to always fail; assert `status=DEGRADED`, `degradation_reason` populated.
- `test_degradation_reason_persists_through_terminal_transition` — set degradation, then transition to OK; assert `degradation_reason` still set (D7 append-preserving).

### Task 2.4 — `tests/unit/test_heartbeat.py` (7 tests; DC-2)

- `test_heartbeat_updates_file_periodically` — start daemon with interval=0.05; wait 0.2s; assert mtime advanced ≥3 times.
- `test_heartbeat_survives_transient_write_error` — patch `_atomic_write` to raise once; daemon continues.
- `test_heartbeat_thread_death_detected_by_main_thread`
- `test_heartbeat_one_restart_attempt_then_degrade`
- `test_heartbeat_stops_cleanly_on_sigterm`
- `test_heartbeat_never_writes_result_json` (DC-2) — monkeypatch `_atomic_write`; record paths; daemon runs; assert no path is `result.json`.
- `test_state_writer_never_writes_heartbeat` (DC-2) — symmetric.

### Task 2.5 — `tests/unit/test_close_slice_hardened.py` (7 tests)

- `test_close_slice_twice_is_noop` (DC-3) — close, then call close again; assert HEAD unchanged, no second commit.
- `test_close_slice_short_circuits_on_already_closed_state` (DC-3) — precondition returns True → no filesystem writes.
- `test_close_slice_bundles_handoff_before_wipe` — mock `_wipe_current_slice`; bundle side-effect observable.
- `test_close_slice_wipe_runs_before_commit` — assert wipe observable in working tree before the commit.
- `test_wipe_clears_all_except_slice_yaml` (DC-5) — seed current-slice with 5 files + a subdir; assert only `slice.yaml` remains; empty dirs removed.
- `test_wipe_raises_on_undeletable_file` (DC-5, non-ENOENT `OSError`) — chmod a file to unwritable then call wipe; assert `RuntimeError`. **Not** `FileNotFoundError` (that path is the tolerance case; cover it in `test_wipe_tolerates_file_already_absent`).
- `test_close_slice_produces_single_slice_complete_commit` (DC-4 mechanical) — full run; assert exactly one commit with subject `slice: complete`, zero with `^handoff: phase 4 complete$`.
- *(Add two more implied by DC-5 split)* `test_run_phase_loop_skips_commit_at_phase_4_boundary` (DC-4 orchestrator-code), `test_wipe_tolerates_file_already_absent` (DC-5 F5 case).

### Task 2.6 — `tests/unit/test_resume_reconcile.py` (10 tests, DC-6)

Each test names a matrix row. The tests build state via the `orchestrator_tmp_home` fixture, call `_reconcile_resume_state()`, and assert the action.
- `test_resume_fresh_slice_starts_at_phase_1`
- `test_resume_reinits_from_slice_yaml_when_head_at_init`
- `test_resume_in_progress_matching_state_resumes`
- `test_resume_exits_1_when_head_ahead_of_json_phase`
- `test_resume_exits_1_when_head_behind_json_phase`
- `test_resume_fixes_up_lagged_json_when_close_succeeded`
- `test_resume_exits_0_when_already_closed`
- `test_resume_exits_1_when_json_ok_but_commit_missing`
- `test_resume_exits_1_when_json_ahead_of_slice_yaml`
- `test_resume_refuses_to_resume_failed_slice`
- `test_resume_exits_1_on_corrupt_result_json`
- `test_resume_degraded_is_treated_as_in_progress`
- `test_resume_unknown_triple_refuses_with_triple_printed` — synthesize an impossible state (e.g., OK / in-progress / any); assert stderr contains the literal triple.

(13 cases, consolidated to ~10 test functions via parametrize or per-case funcs — choose at Phase 2's discretion.)

### Task 2.7 — `tests/unit/test_cross_slice_isolation.py` (4 tests, DC-7)

- `test_sequential_slices_keep_separate_result_files` — run the init path twice with different slice-ids; assert two distinct `<slug>-result.json` files co-exist.
- `test_slice_id_slug_used_in_all_debug_paths` — assert every file in `.claude/orchestrator-debug/` is either `index.jsonl` or starts with a known slug.
- `test_index_jsonl_entries_include_slice_id_tag` — every JSONL line has `"slice_id"` key.
- `test_slug_collision_exits_failed` — seed `<slug>-result.json` with `slice_id: "a/b-c"`; attempt persist under `slice_id: "a-b/c"` (both slug to same); assert FAILED exit + stderr contains `slug collision`.

### Task 2.8 — `tests/unit/test_agent_prompt_updates.py` (6 tests)

- `test_phase_1_prompt_mentions_bash_heredoc_escape` (P1) — grep for `heredoc` or `<<'EOF'`.
- `test_phase_2_prompt_mentions_bash_heredoc_escape` (P1)
- `test_phase_3_prompt_mentions_bash_heredoc_escape` (P1)
- `test_phase_4_prompt_mentions_bash_heredoc_escape` (P1)
- `test_all_phase_prompts_have_do_not_refuse_preemptively_rule` (P2) — loop over all four prompts; each contains the rule text.
- `test_phase_4_prompt_explicitly_forbids_self_commit` (DC-4 prompt layer).

### Task 2.9 — `tests/integration/test_signal_observability.py` (3 tests)

- `test_sigterm_writes_signaled_status_via_atexit` — launch orchestrator in subprocess; SIGTERM; assert `<slug>-result.json` has `status=SIGNALED`.
- `test_atexit_writes_final_state_on_normal_exit`
- `test_atexit_writes_final_state_on_failed_exit`

### Task 2.10 — validation artifacts

**Create:** `.claude/current-slice/validation/approach.md` — maps each DC to its tests, links ADRs, names the cluster-assignment file.

**Create:** `.claude/current-slice/validation/coupling-clusters.yaml` — as shown in Cluster assignment above.

### Task 2.11 — confirm RED

Run: `uv run pytest tests/unit/ tests/integration/ -v`

Expected: every new test fails with `ImportError`, `AttributeError`, or assertion failure. Existing tests remain GREEN (if any pre-existing test overlaps with new coverage — e.g., `tests/unit/test_close_slice_invocation.py` — Phase 2 reconciles by either deleting the pre-existing file or keeping it and marking new tests as additive; decide at Phase 2 time and record in `approach.md`).

### Task 2.12 — Phase 2 commit (orchestrator-issued)

The orchestrator emits `handoff: phase 2 complete` after Phase 2 OK. No additional commit needed.

---

## Phase 3a — orchestrator-internals cluster

Each sub-task: write the implementation, run the relevant tests, observe GREEN, move to the next. One commit at the end of the cluster (orchestrator issues cluster-level commit on Phase 3 OK).

### Task 3a.1 — module-level state + schema constant

**File:** `scripts/slice_orchestrator.py` (near existing imports).

Add `STATE_SCHEMA_VERSION = "1.0"`, `STATUS_NON_TERMINAL`, `STATUS_TERMINAL`, `_state: dict = {}` module-level, and an `_init_state_dict(slice_id: str)` helper that populates the schema shape with defaults.

Run: `uv run pytest tests/unit/test_state_schema.py -v` → all GREEN.

### Task 3a.2 — `_observability_paths(slice_id: str) -> dict`

Returns `{"result_json": Path, "result_md": Path, "index_jsonl": Path, "heartbeat": Path}`. `index_jsonl` is un-slugged (shared); others use `_slice_id_slug(slice_id)` prefix.

### Task 3a.3 — `_atomic_write(path, content)`

Tempfile in same directory + `os.rename`. One retry on `OSError` (no delay). Second failure raises. Single stderr log on first failure.

Run: `uv run pytest tests/unit/test_observability_writer.py::test_atomic_write_succeeds_first_attempt tests/unit/test_observability_writer.py::test_atomic_write_retries_once_on_oserror tests/unit/test_observability_writer.py::test_atomic_write_raises_on_second_failure -v`

### Task 3a.4 — `_update_state(**fields)` + `_persist_state(state)` (without slug-collision tripwire yet)

`_update_state` merges into the module-level dict (no disk write). `_persist_state` atomic-writes JSON. On retry-exhaustion: set `status=DEGRADED`, `degradation_reason`, then one retry of the degradation write; if it also fails → `sys.exit(1)` with `orchestrator: observability fully unwritable; cannot continue`.

Run: the 4 `_persist_state` / `_update_state` tests.

### Task 3a.5 — Slug-collision tripwire in `_persist_state`

Before writing `<slug>-result.json`, `stat` + parse existing file; if `slice_id` field mismatches current, `sys.exit(1)` with `orchestrator: slug collision — <slug> is already claimed by <other_slice_id>; rename one of the two slices and retry`.

Run: `tests/unit/test_cross_slice_isolation.py::test_slug_collision_exits_failed`.

### Task 3a.6 — `_generate_result_md(state)` + `_write_result_md(state)`

Pure function: state dict → markdown per design doc §Components "Markdown sidecar shape". Atomic-write via `_atomic_write`. Called only on terminal transitions.

Run: the 3 MD-related tests.

### Task 3a.7 — `_append_index_entry(entry)`

`O_APPEND` open, one line of JSON + newline, close. Caller supplies `slice_id` in entry.

Run: `test_append_index_entry_atomic_under_interleaved_writes`, `test_index_jsonl_entries_include_slice_id_tag`.

### Task 3a.8 — `_HeartbeatDaemon(threading.Thread)`

Daemon thread; loops `while not self._stop.is_set()`, touches `.heartbeat` via tempfile+rename, sleeps `CAIRN_HEARTBEAT_INTERVAL`. Internal try/except with `seen_errors: set` so each error class logs once. `stop()` sets an `Event`.

Main-thread periodic sampling: in `run_phase_loop`'s main body (or a separate supervisor), every N iterations check `self._heartbeat.is_alive()`; if False, attempt one restart; on second failure → `status=DEGRADED`.

Run: the 7 heartbeat tests.

### Task 3a.9 — `_is_slice_already_closed(state) -> bool`

Checks:
1. `slice.yaml` `status == "complete"`
2. `.claude/handoff.md` exists and non-empty
3. `.claude/current-slice/` contains only `slice.yaml` (recursive check)
4. `git log -1 --format=%s` equals literal `"slice: complete"`

All 4 → True; any False → False.

### Task 3a.10 — `_wipe_current_slice()`

Recursively walk `.claude/current-slice/`; delete every file that is not `slice.yaml`; remove empty subdirectories. `FileNotFoundError` → tolerate (F5 case). Other `OSError` → raise `RuntimeError`.

Run: `test_wipe_clears_all_except_slice_yaml`, `test_wipe_raises_on_undeletable_file`, `test_wipe_tolerates_file_already_absent`.

### Task 3a.11 — `close_slice` rewrite

Replace `scripts/slice_orchestrator.py:981-1003` with the hardened sequence (design doc §Components "close_slice() hardened sequence"):

1. `if _is_slice_already_closed(state): return` — DC-3 short-circuit.
2. `_write_slice_state(status=complete, current_phase=4)` — slice.yaml first.
3. `_bundle_handoff_md()` — existing bundle logic extracted into a helper.
4. `_wipe_current_slice()` — DC-5.
5. **Defensive drift check:** `subject = _git("log", "-1", "--format=%s")`; if `re.match(r"^handoff: phase [0-9]+ complete$", subject)`: stderr `orchestrator: prior phase-commit detected on HEAD ('<subject>'); DC-4 invariant may have been violated — see slice-close-contract D2`.
6. `_git("add", str(SLICE_YAML), str(handoff))` + `_git("commit", "--allow-empty", "-m", "slice: complete")`.
7. `_update_state(status="OK", exit_code=0, final_commit=..., ended_at=..., summary=...)`.
8. `_persist_state(state)`; `_write_result_md(state)`.

Run: `tests/unit/test_close_slice_hardened.py -v`.

### Task 3a.12 — `run_phase_loop` max-phase skip

At line 841-843: wrap `commit_phase_handoff(phase, ...)` in `if phase < max_phase:`. Phase 4 OK skips to `phase += 1` directly; the subsequent `close_slice` call (from the outer loop exit) is the sole commit source.

Apply the same guard at line 850-854 (FAILED → retry → OK path).

Run: `test_run_phase_loop_skips_commit_at_phase_4_boundary`, `test_close_slice_produces_single_slice_complete_commit`.

### Task 3a.13 — `_reconcile_resume_state()`

Implements the 13-row matrix verbatim. Reads: `orchestrator-result.json`, `slice.yaml`, `git log -1 --format=%s`. Optional: `.heartbeat` mtime → advisory stderr only.

Default case (triple not in matrix): stderr `orchestrator: unrecognized resume state: (<json_status>, <yaml_status>, <head_subject>)`; exit 1.

Run: `tests/unit/test_resume_reconcile.py -v`.

### Task 3a.14 — `main()` init dance + atexit + resume path

Update `main()` (line 1014):

```python
# after parse_args, before run_phase_loop
_init_state_dict(slice_id)
_update_state(worktree_path=str(Path.cwd().resolve()), orchestrator_pid=os.getpid(), started_at=_utc_timestamp(), status="IN_PROGRESS")
_persist_state(_state)
_heartbeat = _HeartbeatDaemon(heartbeat_path, interval=float(os.environ.get("CAIRN_HEARTBEAT_INTERVAL", 10.0)))
_heartbeat.start()
atexit.register(_final_persist_and_md)
atexit.register(_heartbeat.stop)
if args.resume:
    reconciled = _reconcile_resume_state()
    _update_state(**reconciled)
    _persist_state(_state)
```

`_final_persist_and_md`: if `status` is non-terminal, set to appropriate terminal (most common: `status="SIGNALED"` when entered via signal; otherwise infer from exception presence). Write MD.

Also: `_clean_shutdown` (line 771) should NOT duplicate the state write — atexit is the single terminal writer.

### Task 3a.15 — run all Phase 3a tests

```bash
uv run pytest tests/unit/test_observability_writer.py \
              tests/unit/test_state_schema.py \
              tests/unit/test_heartbeat.py \
              tests/unit/test_close_slice_hardened.py \
              tests/unit/test_resume_reconcile.py \
              tests/unit/test_cross_slice_isolation.py \
              tests/integration/test_signal_observability.py -v
```

Expected: all GREEN. Orchestrator issues cluster commit on Phase 3 OK.

---

## Phase 3b — agent-prompts cluster

### Task 3b.1 — Phase-4 prompt DC-4 rule

**Modify:** `.claude/agents/phase-4-integrator.md`.

Add near the top (after the role declaration), in an "Anti-behaviors" block if one exists else create one:

> **Do not issue any `git commit` in Phase 4.** Produce `handoff-phase-4.md` and `integration/sweep-notes.md` as working-tree artifacts; the orchestrator's `close_slice` bundles and commits them.

### Task 3b.2 — P1/P2 rules across all four phase prompts

**Modify:** `.claude/agents/phase-{1,2,3,4}-*.md`.

In each prompt's preamble, add:

- **P1 — Bash-heredoc escape (Learning L3):** when Writing to `.claude/**` paths during the A1 sensitive-file window, use Bash heredoc (`cat <<'EOF' > path`) rather than the Write tool.
- **P2 — Do not refuse preemptively (Learning L4):** always attempt the tool call; let the hook layer gate you. Refusing based on prior-art docs is a false-positive anti-pattern.

### Task 3b.3 — run Phase 3b tests

```bash
uv run pytest tests/unit/test_agent_prompt_updates.py -v
```

Expected: all GREEN. Orchestrator issues cluster commit.

---

## Phase 4 — integration (integrator + end-to-end gate)

### Task 4.1 — full suite

```bash
uv run pytest tests/unit/ tests/integration/ -v
```

Expected: GREEN. No regressions in existing tests.

### Task 4.2 — architecture validator

```bash
uv run python scripts/validate_architecture.py
```

Expected: PASS. No INV changes land in this slice (INV-008 was declared at `d11277b` and propagates at the post-close `/refresh-architecture`, not during the slice).

### Task 4.3 — integration gate

```bash
uv run python scripts/integration_gate.py
```

Expected: PASS.

### Task 4.4 — end-to-end observability smoke test

**New gate in `scripts/integration_gate.py` (or adjacent):** spawn the orchestrator against a trivial slice; after it completes, assert:
- `<slug>-result.json` exists with `status: OK`, `final_commit != ""`, `schema_version == "1.0"`.
- `<slug>-result.md` exists and non-empty.
- `index.jsonl` exists; at least one line with `"event": "cluster_dispatch"` (phase-3) if a phase-3 cluster ran.
- `.claude/current-slice/` contains exactly `slice.yaml`.
- `git log -1 --format=%s` == `slice: complete`.
- `git log -2 --format=%s | head -1` != `handoff: phase 4 complete` (DC-4 check).

### Task 4.5 — sweep notes

**Create:** `.claude/current-slice/integration/sweep-notes.md` — the integration sweep report. Phase 4 agent produces this per existing flow.

### Task 4.6 — Phase 4 handoff (working-tree artifact only)

**Create:** `.claude/current-slice/handoff-phase-4.md` — Phase 4's handoff content.

**Do NOT commit from Phase 4.** Per DC-4, `close_slice` stages and commits these files in the `slice: complete` commit.

### Task 4.7 — close_slice invocation

Orchestrator invokes `close_slice(state)` after Phase 4 OK. The hardened sequence handles bundle + wipe + commit + state persist + MD.

---

## Verification matrix (pre-close)

| Contract | Test / gate | Expected |
|----------|-------------|----------|
| INV-008 DC-3 | `test_close_slice_twice_is_noop`, `test_close_slice_short_circuits_on_already_closed_state` | GREEN |
| INV-008 DC-4 (mechanical) | `test_run_phase_loop_skips_commit_at_phase_4_boundary`, `test_close_slice_produces_single_slice_complete_commit` | GREEN |
| INV-008 DC-4 (prompt) | `test_phase_4_prompt_explicitly_forbids_self_commit` | GREEN |
| INV-008 DC-7 | `test_sequential_slices_keep_separate_result_files`, `test_slice_id_slug_used_in_all_debug_paths`, `test_slug_collision_exits_failed` | GREEN |
| DC-5 wipe | `test_wipe_clears_all_except_slice_yaml`, `test_wipe_raises_on_undeletable_file`, `test_wipe_tolerates_file_already_absent` | GREEN |
| DC-6 resume | 10 matrix tests | GREEN |
| Observability D2 | `test_md_is_derived_from_json_state` | GREEN |
| Observability D3 | `test_heartbeat_never_writes_result_json`, `test_state_writer_never_writes_heartbeat` | GREEN |
| Observability D4 | `test_state_dict_includes_schema_version`, `test_state_dict_required_fields_present` | GREEN |
| Observability D6 | `test_degraded_status_replaces_in_progress_on_retry_exhaustion` | GREEN |
| Observability D7 | `test_degradation_reason_persists_through_terminal_transition` | GREEN |
| Full suite | `uv run pytest tests/unit/ tests/integration/` | GREEN |
| Architecture | `scripts/validate_architecture.py` | PASS |
| Integration | `scripts/integration_gate.py` + e2e smoke | PASS |

---

## Close-handoff queue (post-slice, not in this slice)

- `/integration-sweep` (first since Slice 2 close; sweep.yaml pre-bumped).
- `/refresh-architecture` — propagates INV-008 to `docs/ARCHITECTURE.md` with `invariant-check` blocks pointing to the hardened tests.
- `/new-adr` for retention policy if D8 tripwire fires during this slice's dogfood.
- Document `CAIRN_HEARTBEAT_INTERVAL` + `CAIRN_HEARTBEAT_STALE` in `docs/operational-reference.md:339-344` neighborhood.
- Follow-up slice: Path C (orchestrator-owned writes); multi-instance hardening (worktree-scoped locking, PID-scoped role_guard, parallel-worktree integration test).

---

## References

- `docs/adr/slice-close-contract.md` — firm contract.
- `docs/adr/orchestrator-observability.md` — provisional shape.
- `docs/plans/2026-04-20-observability-and-close-slice-design.md` — design spec.
- `docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md` — rejected alternatives.
- `docs/lessons.md` L-007 — framing-doc attribution inheritance.
- `.claude/learning.md` L1–L8, C1–C2 — motivating pain points.
- `docs/ARCHITECTURE.md` — current INV-001..INV-008 roster.
- `scripts/slice_orchestrator.py:732,825,841,981,1014` — edit anchors.

---
slice-id: compression/slice-3-observability-and-close-slice
feature: compression
phase: 1
role: writer
adrs-touched: [slice-close-contract, orchestrator-observability]
invariants-touched: [INV-008, INV-002]
---

# Intent — compression/slice-3-observability-and-close-slice

## What

Land INV-008 (slice-close lifecycle correctness) in `scripts/slice_orchestrator.py` and the provisional observability-artifact shape at `.claude/orchestrator-debug/`. Scope: three logical blocks inside the orchestrator (observability primitives, lifecycle hardening, heartbeat daemon) + prompt edits on all four phase agents.

## Why

Two consecutive slices (`compression/slice-1-infrastructure`, `compression/slice-2-state-machine`) exhibited close_slice pathologies (`.claude/learning.md` C2): R1 non-idempotent close, R2 missing wipe, R3 redundant per-phase commit at Phase 4 boundary, R4 no resume-after-crash reconciliation. Downstream consumers (fleet-coordinator epic) will read this substrate and inherit the bugs. ADRs landed at `d11277b` on 2026-04-20: `slice-close-contract` (firm) declares INV-008 = DC-3 idempotent close + DC-4 sole commit source + DC-7 slug isolation, plus operational DC-5 wipe and DC-6 13-row resume matrix; companion `orchestrator-observability` (provisional) fixes D1 placement, D2 JSON-canonical/MD-derived, D4 schema v1.0 B2/B3 hybrid, D6 three-level error policy, D7 append-preserving degradation, D8 retention tripwire, D9 heartbeat cadence.

## Boundary

**In:** observability primitives (`_atomic_write`, `_persist_state`, `_generate_result_md`, `_write_result_md`, `_append_index_entry`, `_observability_paths`, `_update_state`, module-level `_state`); `_HeartbeatDaemon` + main-thread restart detection; `close_slice` rewrite (idempotent, wipe-before-commit, slug-isolated); `run_phase_loop` max-phase `commit_phase_handoff` skip + defensive `git log -1` drift check; `_is_slice_already_closed` (4-signal); `_wipe_current_slice` (F5-tolerant, strict on other `OSError`); `_reconcile_resume_state` (13-row matrix + default-refuse + heartbeat advisory); `_persist_state` slug-collision tripwire; Phase-4 prompt DC-4 anti-behavior; Phase-1..4 prompts P1 heredoc note + P2 no-preemptive-refuse; 35 unit tests + 3 integration tests across 8 files.

**Out:** worktree-scoped locking (`fcntl.flock`), PID-scoped role_guard, parallel-worktree integration tests; Path C orchestrator-owned `.claude/**` writes; `/decision` Phase 0/4 for L-003/L-007; retention policy (deferred behind D8 tripwire); ruff F841 at `tests/unit/test_post_timeout_reconcile.py:101` (housekeeping); Phase-4 FAILED preservation path (slice-close-contract D2 note); `docs/ARCHITECTURE.md` INV-008 propagation (runs from close handoff via `/refresh-architecture`, not inside slice); no new ADRs land here.

## Specification

### Artifact inventory

**Create (tests):**
- `tests/unit/test_state_schema.py`
- `tests/unit/test_observability_writer.py`
- `tests/unit/test_heartbeat.py`
- `tests/unit/test_close_slice_hardened.py`
- `tests/unit/test_resume_reconcile.py` (13 matrix rows via parametrize)
- `tests/unit/test_cross_slice_isolation.py` (incl. slug collision tripwire)
- `tests/unit/test_agent_prompt_updates.py`
- `tests/integration/test_signal_observability.py`

**Modify:**
- `scripts/slice_orchestrator.py` — three logical blocks added; `close_slice` replaced (`:981-1003`); `run_phase_loop` `:841,:850-854` gain `if phase < max_phase:` guard + defensive check; `main` `:1014` gains `_init_state_dict` + heartbeat start + `atexit.register` + resume-reconcile path.
- `.claude/agents/phase-4-integrator.md` — DC-4 anti-behavior ("do not issue `git commit` in Phase 4").
- `.claude/agents/phase-{1,2,3,4}-*.md` — P1 Bash-heredoc note + P2 no-preemptive-refuse rule.

**Runtime artifacts (orchestration-time):**
- `.claude/orchestrator-debug/<slug>-result.json` (canonical, every transition + atexit)
- `.claude/orchestrator-debug/<slug>-result.md` (terminal-only, derived)
- `.claude/orchestrator-debug/index.jsonl` (`O_APPEND`, every failure log + phase-3 cluster dispatch)
- `.claude/current-slice/.heartbeat` (ephemeral; wiped by DC-5)

### Cluster assignment (Phase 3 fan-out)

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

Rationale: orchestrator code + its unit/integration tests all share `slice_orchestrator.py`; prompt edits are textually independent.

### State-dict schema v1.0 (authoritative in orchestrator-observability D4)

Firmly committed: `schema_version="1.0"`, `slice_id`, `started_at`, `ended_at`, `status`, `exit_code`, `current_phase`, `phases_completed`, `phase_timings`, `retries_by_phase`, `cluster_dispatches`, `degradation_reason` (append-preserving, D7), `observability_errors`, `final_commit`, `summary`.
Additive-safe: `worktree_path`, `orchestrator_pid`.
Status enum — non-terminal: `IN_PROGRESS`, `DEGRADED`. Terminal: `OK`, `FAILED`, `ABORTED`, `ESCALATED`, `SIGNALED`.
Env: `CAIRN_HEARTBEAT_INTERVAL` (default `10.0`), `CAIRN_HEARTBEAT_STALE` (default `30.0`).

### DC-6 resume matrix (13 rows)

| `result.json` | `slice.yaml` | HEAD | Action |
|---|---|---|---|
| absent | absent | any | Fresh — start Phase 1 |
| absent | in-progress | `^slice: .* — init$` | Re-init from slice.yaml |
| absent | in-progress | other | Refuse — manual intervention |
| IN_PROGRESS | in-progress | matches `current_phase` | Resume at `current_phase` |
| IN_PROGRESS | in-progress | ahead | Refuse — JSON stale |
| IN_PROGRESS | in-progress | behind | Refuse — expected commit missing |
| IN_PROGRESS | complete | `slice: complete` | Fix up JSON → OK, exit 0 |
| OK | complete | `slice: complete` | Already closed, exit 0 |
| OK | complete | not `slice: complete` | Refuse — commit missing |
| OK | in-progress | any | Refuse — JSON ahead |
| DEGRADED | (any) | (any) | Treat as IN_PROGRESS |
| FAILED/ABORTED/SIGNALED | in-progress | any | Refuse — prior terminated |
| corrupt JSON | (any) | (any) | Refuse — parse error |

Default: unmatched triple refuses with literal triple printed; heartbeat mtime within `CAIRN_HEARTBEAT_STALE` → advisory stderr only.

### DC-4 three-layer enforcement

1. **Primary (orchestrator code):** `run_phase_loop` wraps `commit_phase_handoff(phase, ...)` in `if phase < max_phase:`; Phase 4 OK proceeds directly to `close_slice`.
2. **Defense (prompt):** Phase-4 integrator agent forbids self-commit; grep test enforces.
3. **Drift detector:** before the close commit, `git log -1 --format=%s` against `^handoff: phase [0-9]+ complete$`; match emits advisory stderr.

### DC-3 precondition (`_is_slice_already_closed`)

Returns True iff all four: `slice.yaml status: complete`; `.claude/handoff.md` present and non-empty; `.claude/current-slice/` contains only `slice.yaml`; `git log -1 --format=%s == "slice: complete"`.

### DC-5 wipe semantics

Delete every file in `.claude/current-slice/` except `slice.yaml`; remove empty subdirs. `FileNotFoundError` tolerated (F5 operator-rebase corner). Other `OSError` → `RuntimeError` propagates.

### DC-7 slug isolation

Every `.claude/orchestrator-debug/` file is either `index.jsonl` (shared, each entry tagged with `slice_id`) or carries the `<slice-id-slug>` prefix (`slice_id.replace("/", "-")`, per `scripts/slice_orchestrator.py:187-188`). Tripwire: `_persist_state` reads any existing `<slug>-result.json`; if its `slice_id` mismatches current, `sys.exit(1)` with loud stderr.

### Observability error policy (D6)

Level 1: `_atomic_write` one retry no-delay on `OSError`, stderr log on first failure.
Level 2: second failure → `status=DEGRADED`, populate `degradation_reason`, continue.
Level 3: DEGRADED write itself fails → `sys.exit(1)` with `orchestrator: observability fully unwritable; cannot continue`.
Heartbeat thread: self-healing try/except (one log per error class); main-thread periodic `is_alive()` check; one restart attempt, then `status=DEGRADED`.

### Source contracts

| Pointer | Role |
|---|---|
| `docs/adr/slice-close-contract.md` | **Firm.** INV-008 declaration; read before editing `close_slice`, `run_phase_loop`, `_slice_id_slug`, or any agent prompt |
| `docs/adr/orchestrator-observability.md` | **Provisional.** D1–D9 observability shape; read before adding any path/schema field |
| `docs/plans/2026-04-20-observability-and-close-slice-design.md` | Design spec — function sigs, call graphs, MD template, test inventory, cluster assignment; §Testing = Phase 2 RED-suite skeleton |
| `docs/plans/2026-04-20-observability-and-close-slice-plan.md` | Task decomposition (source of this intent) |
| `docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md` | Rejected-alternatives archive |

Rule: when plan conflicts with ADR, the ADR wins.

## Verification

**Phase-2 RED gate.** New tests (8 files, ≈35 unit + 3 integration) all fail with `ImportError`/`AttributeError`/assertion; existing suite stays GREEN; any overlap with pre-existing `tests/unit/test_close_slice_invocation.py` is reconciled in `.claude/current-slice/validation/approach.md`.

**Phase-3 GREEN gates.**
- 3a cluster: `uv run pytest tests/unit/test_observability_writer.py tests/unit/test_state_schema.py tests/unit/test_heartbeat.py tests/unit/test_close_slice_hardened.py tests/unit/test_resume_reconcile.py tests/unit/test_cross_slice_isolation.py tests/integration/test_signal_observability.py -v` → all GREEN.
- 3b cluster: `uv run pytest tests/unit/test_agent_prompt_updates.py -v` → all GREEN.

**Phase-4 integration gate.**
- `uv run pytest tests/unit/ tests/integration/ -v` → GREEN, no regressions.
- `uv run python scripts/validate_architecture.py` → PASS (no INV changes land; propagation is post-close).
- `uv run python scripts/integration_gate.py` → PASS.
- End-to-end smoke: orchestrator against trivial slice → asserts `<slug>-result.json` has `status: OK`, `final_commit != ""`, `schema_version == "1.0"`; `<slug>-result.md` present and non-empty; `index.jsonl` has >=1 entry; `.claude/current-slice/` contains exactly `slice.yaml`; `git log -1 --format=%s == "slice: complete"`; `git log -2 --format=%s | head -1 != "handoff: phase 4 complete"`.

**Contract-to-test map.**

| Contract | Tests |
|---|---|
| INV-008 DC-3 | `test_close_slice_twice_is_noop`, `test_close_slice_short_circuits_on_already_closed_state` |
| INV-008 DC-4 (code) | `test_run_phase_loop_skips_commit_at_phase_4_boundary`, `test_close_slice_produces_single_slice_complete_commit` |
| INV-008 DC-4 (prompt) | `test_phase_4_prompt_explicitly_forbids_self_commit` |
| INV-008 DC-7 | `test_sequential_slices_keep_separate_result_files`, `test_slice_id_slug_used_in_all_debug_paths`, `test_slug_collision_exits_failed` |
| DC-5 | `test_wipe_clears_all_except_slice_yaml`, `test_wipe_raises_on_undeletable_file`, `test_wipe_tolerates_file_already_absent` |
| DC-6 | 13 matrix rows + default-refuse |
| Observability D2 | `test_md_is_derived_from_json_state` |
| Observability D3 | `test_heartbeat_never_writes_result_json`, `test_state_writer_never_writes_heartbeat` |
| Observability D4 | `test_state_dict_includes_schema_version`, `test_state_dict_required_fields_present`, `test_status_enum_values_match_spec`, `test_worktree_path_and_orchestrator_pid_populated_on_init` |
| Observability D6 | `test_degraded_status_replaces_in_progress_on_retry_exhaustion` |
| Observability D7 | `test_degradation_reason_persists_through_terminal_transition` |

**Close-handoff queue (post-slice, not in scope):** `/integration-sweep` (first since Slice 2); `/refresh-architecture` propagates INV-008; `/new-adr` for retention if D8 tripwire fires; document heartbeat env-vars at `docs/operational-reference.md:339-344`; follow-up Path C + multi-instance slice.

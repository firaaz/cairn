# Observability and close_slice Hardening — Design

---
date: 2026-04-20
status: draft (pre-/decision)
brainstorm-doc: docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md
related-plan: docs/plans/2026-04-20-compression-pipeline-hardening-plan.md
related-learnings: .claude/learning.md (L1-L8, C1-C2)
supersedes-scope: docs/plans/2026-04-20-compression-pipeline-hardening-plan.md §3.0 (partially — multi-instance deferred)
---

## Goal

Harden `scripts/slice_orchestrator.py`'s `close_slice` step and add a structured observability layer (JSON state, markdown sidecar, failure index, liveness heartbeat). Fix the known pain points surfaced by Slice 2's close-out learnings (L1–L8, C1–C2). Land forward-compatible schema and atomic-write primitives so the future fleet coordinator can consume orchestrator state without retrofits.

This slice does **not** land worktree-scoped locking, PID-scoped role-guard, or parallel-worktree integration tests. Those were the original Slice 3 (§3.0) scope and are deferred to a follow-up slice.

## Glossary

Short codes used throughout this doc. Always defined on first use; this table is the canonical reference.

### Failure-mode codes (motivating pain points)

| Code | Definition |
|------|------------|
| **R1** | `close_slice` is not idempotent — crash between its three steps (write `slice.yaml` `status: complete`, bundle `handoff.md`, `git commit`) leaves partial state that `--resume` cannot recover from. |
| **R2** | `close_slice` wipe gap — residue in `.claude/current-slice/` survives slice close; corresponds to Learning L8. |
| **R3** | Redundant-commit race — Phase-4 integrator agent commits `handoff: phase 4 complete`, then `close_slice` commits `slice: complete`. Two commits per close; ordering unclear; corresponds to Learning C2. |
| **R4** | Resume-after-mid-slice-crash reconciliation — no mechanism today to compare `orchestrator-result.json`, `slice.yaml`, and `git HEAD` when orchestrator dies mid-phase. |
| **P1** | Bash-heredoc write-escape (discovered per Learning L3) is documented in the Phase-1/2/3/4 agent prompts. |
| **P2** | "Always attempt the tool call; do not refuse preemptively based on prior-art docs" rule (Learning L4) is codified into the agent-prompt preambles. |

### Observability shape code

| Code | Definition |
|------|------------|
| **O3** | Observability shape adopted: incremental `orchestrator-result.json` (state) + markdown sidecar `orchestrator-result.md` generated from that JSON at close time + append-only `index.jsonl` (failure and dispatch stream) + `.heartbeat` liveness file. |

### Architectural decision codes

| Code | Definition |
|------|------------|
| **D1** | Placement decision — observability artifacts live in `.claude/orchestrator-debug/` (cross-slice persistent), not `.claude/current-slice/` (slice-scoped). |
| **D2** | Source model — `orchestrator-result.json` is the canonical state; the markdown sidecar is generated deterministically from that JSON by a pure function. No parallel write paths. |
| **D3** | Forward-compat posture — invest now in multi-instance-ready schema (`worktree_path`, `orchestrator_pid`, `phase_timings[]`, `retries_by_phase{}`) and atomic-write primitives. Retrofitting after consumers exist is more expensive than paying the cost today. |

### Design contracts (slice-local post-conditions)

| Code | Definition |
|------|------------|
| **DC-1** | Single source of truth for observability — `orchestrator-result.md` is always generated from `orchestrator-result.json` via a pure function; no independent MD write path. |
| **DC-2** | Heartbeat and state are decoupled — the heartbeat daemon thread writes only to `.heartbeat`; the state writer writes only to `orchestrator-result.json` and `orchestrator-result.md`. No shared lock. |
| **DC-3** | `close_slice` is idempotent — safe to invoke any number of times; the second and subsequent calls short-circuit without side effects. |
| **DC-4** | `close_slice` is the only source of the `slice: complete` commit — Phase-4 agent does not self-commit. |
| **DC-5** | Wipe is explicit and surfaces errors — `close_slice` deletes every file in `.claude/current-slice/` except `slice.yaml`, raising on any deletion failure. |
| **DC-6** | Resume path is read-first, act-second — on `--resume`, the orchestrator reads `result.json`, `slice.yaml`, and `git HEAD`, exiting non-zero on divergence rather than silently picking a winner. |
| **DC-7** | Cross-slice artifact isolation — every file in `.claude/orchestrator-debug/` is keyed by `slice-id-slug`, except `index.jsonl` whose entries are slice-id-tagged. |

Candidates for INV elevation (via a follow-up `/decision` run): **DC-3**, **DC-4**, **DC-7**.

### Project-wide identifiers (defined elsewhere)

- `INV-001..INV-007` — project-wide invariants in `docs/ARCHITECTURE.md`; backed by ADRs; machine-checked by `scripts/validate_architecture.py`. This slice adds no new INVs.
- `L1..L8`, `C1..C2` — entries in `.claude/learning.md` from the Slice 2 close-out.
- `B1..B16` — code-bug backlog codes from `docs/plans/2026-04-20-compression-pipeline-hardening-design.md`. Slice 2 landed B1–B16; referenced here for context.

---

## Architecture

### Artifact paths introduced

| Path | Purpose | Lifetime |
|------|---------|----------|
| `.claude/orchestrator-debug/<slice-id-slug>-result.json` | Canonical orchestrator state; written on every phase transition plus final `atexit` write. | Cross-slice persistent (survives for `/catchup phase N` history, fleet-coordinator reads). |
| `.claude/orchestrator-debug/<slice-id-slug>-result.md` | Human-readable sidecar generated deterministically from the JSON. | Cross-slice persistent. |
| `.claude/orchestrator-debug/index.jsonl` | Single append-only stream of failure logs + phase-3 cluster dispatches; entries tagged with `slice_id`. | Cross-slice persistent. |
| `.claude/current-slice/.heartbeat` | Ephemeral ISO timestamp touched every `CAIRN_HEARTBEAT_INTERVAL` seconds by a background daemon thread. | Lives for the duration of the slice; removed by `close_slice`'s wipe (DC-5). |

### Code loci (where changes land)

**`scripts/slice_orchestrator.py`** gains three logical blocks, co-located near their existing nearest neighbors in the file:

1. **Observability primitives block** — near existing `_write_failure_log` / `_write_cluster_log`. New helpers for atomic write, state persistence, MD generation, index append.
2. **Lifecycle hardening block** — replaces the existing `close_slice` at line 981; adds `_is_slice_already_closed`, `_wipe_current_slice`, `_reconcile_resume_state`.
3. **Heartbeat daemon block** — a small `threading.Thread` subclass. Instantiated and started in `main()` before `run_phase_loop`; stopped via `atexit`.

**`.claude/agents/phase-{1,2,3,4}-*.md`** — each receives the Bash-heredoc escape note (**P1**) and the "don't refuse preemptively" rule (**P2**). The Phase-4 prompt additionally receives an explicit "do not self-commit; let `close_slice` finalize" instruction (**DC-4** enforcement).

**`tests/unit/`** — eight new test files. **`tests/integration/`** — one new test file for signal handling. Detailed in §Testing below.

### What this slice does not touch

- `dispatch_phase_agent`, `dispatch_triager` — return contracts unchanged.
- `_parse_structured_tail` — unchanged.
- `_run_with_live_stderr` — unchanged.
- Phase-3 fan-out internals (`dispatch_phase_3`) — orchestrator records cluster dispatches into state, but the fan-out logic itself is untouched.
- `docs/ARCHITECTURE.md` — no new INVs.
- `docs/adr/` — no new ADRs (architectural commitments stay as slice-local DCs; elevation queued for follow-up `/decision`).

---

## Components

### State-dict schema (canonical object written to `orchestrator-result.json`)

```python
{
    "schema_version": "1.0",                    # bumped on incompatible changes

    # Identity
    "slice_id": "compression/slice-3-observability-and-close-slice",
    "worktree_path": "/abs/path/to/worktree",   # forward-compat for fleet-coordinator
    "orchestrator_pid": 12345,                  # forward-compat

    # Lifecycle timing
    "started_at": "2026-04-20T15:00:00+00:00",  # ISO 8601 UTC
    "ended_at": None,                           # populated on terminal transition

    # Status
    "status": "IN_PROGRESS",                    # one of the enum values below
    "exit_code": None,                          # 0, 1, 130, etc — set on terminal

    # Phase progress
    "current_phase": 2,                         # 1..4, active phase
    "phases_completed": [1],                    # phases that returned OK
    "phase_timings": {
        "1": {"started_at": "...", "ended_at": "...", "duration_seconds": 45.2}
    },
    "retries_by_phase": {                       # re-dispatch counts (B14/B15)
        "2": 1
    },

    # Phase-3 fan-out trail
    "cluster_dispatches": [
        {"phase": 3, "cluster": "orchestrator-internals",
         "dispatched_at": "...", "status": "OK",
         "commit_hash": "abc1234", "duration_seconds": 220.5}
    ],

    # Degradation state
    "degradation_reason": None,                 # str — which write, errno, phase — persists post-terminal
    "observability_errors": {                   # per-writer transient-error counts
        "persist_state": 0,
        "write_result_md": 0,
        "append_index": 0,
        "heartbeat": 0
    },

    # Close-out
    "final_commit": "",                         # set by close_slice on OK close
    "summary": ""                               # short human-readable line
}
```

**Status enum values:**

- Non-terminal: `IN_PROGRESS`, `DEGRADED`
- Terminal: `OK`, `FAILED`, `ABORTED`, `ESCALATED`, `SIGNALED`

`DEGRADED` replaces `IN_PROGRESS` when an observability write has exhausted its retry budget. On terminal transition, status moves to one of the terminal values; `degradation_reason` persists, so post-close consumers can see "this slice ran degraded at some point."

**Schema versioning:** consumers assert `schema_version == "1.0"` before trusting fields. Future slices increment this when introducing breaking changes.

### Function signatures

**Observability primitives:**

```python
def _atomic_write(path: Path, content: str) -> None:
    """Atomic write via tempfile + os.rename. Retries once with no delay on OSError; raises on second failure."""

def _observability_paths(slice_id: str) -> dict:
    """Return {'result_json': ..., 'result_md': ..., 'index_jsonl': ..., 'heartbeat': ...}."""

def _update_state(**fields) -> None:
    """Merge fields into the module-level state dict. Does NOT persist."""

def _persist_state(state: dict) -> None:
    """Write state to result.json atomically. Catches retry-exhausted OSError, marks DEGRADED, retries one more time for the degradation write itself; exits FAILED if even that fails (Level 3)."""

def _generate_result_md(state: dict) -> str:
    """Pure function: state dict → markdown string."""

def _write_result_md(state: dict) -> None:
    """Derive MD from state, atomic-write to result.md path. Called only at terminal transitions (close-only cadence)."""

def _append_index_entry(entry: dict) -> None:
    """Append-only JSONL write to index.jsonl via O_APPEND. Caller supplies slice_id in entry."""
```

**Lifecycle hardening:**

```python
def close_slice(state: dict) -> None:
    """Idempotent slice finalization. Implements DC-3, DC-4, DC-5."""

def _is_slice_already_closed(state: dict) -> bool:
    """Precondition check: status=complete AND handoff.md exists AND wipe verified AND slice: complete commit on HEAD."""

def _wipe_current_slice() -> None:
    """Delete every file in .claude/current-slice/ except slice.yaml. Raises RuntimeError on any error (DC-5)."""

def _reconcile_resume_state() -> dict:
    """Read result.json, slice.yaml, git HEAD. Return reconciled state or raise SystemExit(1). Implements DC-6."""
```

**Heartbeat daemon:**

```python
class _HeartbeatDaemon(threading.Thread):
    """Touches .heartbeat with current ISO timestamp every `interval` seconds.
    daemon=True. Self-healing internal loop; logs per unique error class; never exits except via stop()."""

    def __init__(self, heartbeat_path: Path, interval: float): ...
    def run(self) -> None: ...
    def stop(self) -> None: ...  # sets an Event, thread exits on next loop iteration
```

### Call graph

**`main()` initialization (new dance):**

```
main()
├── parse args
├── _update_state(slice_id, worktree_path, orchestrator_pid, started_at, status="IN_PROGRESS")
├── _persist_state(state)                                  # initial result.json
├── _HeartbeatDaemon(heartbeat_path, interval=CAIRN_HEARTBEAT_INTERVAL).start()
├── atexit.register(_final_persist_and_md)                 # single terminal writer
├── atexit.register(_stop_heartbeat)
├── if args.resume:
│       reconciled = _reconcile_resume_state()             # DC-6
│       _update_state(**reconciled)
│       _persist_state(state)
├── run_phase_loop()
└── exit
```

**`run_phase_loop()` additions:**

At every significant transition, call `_update_state(...)` then `_persist_state(state)`:

- On phase entry: `current_phase=N`, timing start
- On phase OK: `phases_completed.append(N)`, timing end
- On RE_DISPATCH: `retries_by_phase[target] += 1`, `current_phase=target`
- On phase-3 cluster dispatch: append to `cluster_dispatches`; call `_append_index_entry`
- On FAILED terminal (after retries exhausted): `status="FAILED"`, `exit_code=1`, `summary=...`
- On ESCALATE_TO_USER: `status="ESCALATED"`, `exit_code=1`
- On ABORT: `status="ABORTED"`, `exit_code=1`
- After successful `close_slice`: `status="OK"`, `exit_code=0`, `final_commit=...`

Existing control flow is unchanged. All additions are side calls to the observability helpers.

**`close_slice()` hardened sequence:**

```
close_slice(state)
├── if _is_slice_already_closed(state): return              # DC-3 short-circuit
├── _write_slice_state(status=complete, current_phase=4)    # slice.yaml first
├── _bundle_handoff_md()                                    # existing bundle logic
├── _wipe_current_slice()                                   # DC-5
├── _git("add", str(SLICE_YAML), str(handoff))
├── _git("commit", "--allow-empty", "-m", "slice: complete") # DC-4 single-source commit
├── _update_state(status="OK", exit_code=0, final_commit=..., ended_at=..., summary=...)
├── _persist_state(state)
└── _write_result_md(state)                                 # close-only MD generation
```

**Order matters:** bundle before wipe (wipe removes the inputs). Commit after wipe (commit captures the wiped current-slice/). Persist state after commit (state records the commit hash).

### Markdown sidecar shape (generated from state)

```markdown
# Orchestrator Result — <slice-id>

**Status:** OK
**Exit code:** 0
**Slice:** `compression/slice-3-observability-and-close-slice`
**Orchestrator PID:** 12345
**Worktree:** `/Users/.../compression`

## Timeline
- **Started:** 2026-04-20T15:00:00+00:00
- **Ended:**   2026-04-20T15:47:22+00:00
- **Duration:** 47m 22s

## Phases
| Phase | Role                | Status | Duration | Retries |
|-------|---------------------|--------|----------|---------|
| 1     | phase-1-writer      | OK     | 45.2s    | 0       |
| 2     | phase-2-skeptic     | OK     | 3m 12s   | 0       |
| 3     | phase-3-implementer | OK     | 38m 45s  | 0       |
| 4     | phase-4-integrator  | OK     | 4m 18s   | 0       |

## Phase 3 Clusters
- `orchestrator-internals`: OK (commit `abc1234`, 22m 5s)
- `agent-prompts`: OK (commit `def5678`, 16m 40s)

## Final Commit
`<short-hash>` slice: complete

## Summary
<state.summary>

## Degradation
<If degradation_reason is None: "None.">
<Otherwise: the degradation reason + observability_errors table>
```

---

## Data Flow

### Who writes what, when

| File | Writer | Cadence | Atomic? |
|------|--------|---------|---------|
| `orchestrator-debug/<slug>-result.json` | Main thread, `_persist_state()` | Every state transition + final `atexit` | Yes — tempfile + `os.rename` |
| `orchestrator-debug/<slug>-result.md` | Main thread, `_write_result_md()` | Only on terminal transitions (close-only cadence) | Yes |
| `orchestrator-debug/index.jsonl` | Main thread, `_append_index_entry()` | On every failure log + every phase-3 cluster dispatch | `O_APPEND` atomic for small writes |
| `current-slice/.heartbeat` | Heartbeat thread | Every `CAIRN_HEARTBEAT_INTERVAL` seconds (default 10s) | Yes |
| `current-slice/slice.yaml` | Main thread (existing) | Phase transitions + close | Existing writer |
| `current-slice/handoff-phase-N.md` | Phase-N agent (existing) | At phase's commit | Agent's concern |
| `current-slice/integration/sweep-notes.md` | Phase-4 agent (existing) | During Phase 4 | Agent's concern |
| `handoff.md` | Main thread, via `close_slice` bundler | Slice close | File replaced in close_slice |
| `orchestrator-debug/<slug>-phase-{N}-{role}-{ts}.log` | Main thread (existing) | On failed agent dispatch | Existing writer |

### Concurrency model

Two threads touch observability state:

- **Main thread** — all orchestration, all state mutation, writes to `result.json`, `result.md`, `index.jsonl`. Never writes to `.heartbeat`.
- **Heartbeat thread** — reads system time, writes only to `.heartbeat`. Never reads or writes state dict, JSON, or MD. Daemon thread; internal try/except loop so transient write failures don't kill it.

Per **DC-2**: no shared lock between these threads. They never touch the same file.

**Subprocess children** (agent dispatches) — do not touch observability files. Their writes are scoped by `scope-guard.sh` envelope gate + `role_guard.py`.

### Write-ordering guarantees (main thread)

For every state transition:

```
1. _update_state(**fields)                # mutate in-memory dict
2. _persist_state(state)                   # atomic-write JSON
3. [if terminal] _write_result_md(state)   # atomic-write MD (close-only cadence)
4. [optional] _append_index_entry(entry)   # append to index.jsonl
```

- If the main thread crashes between step 1 and step 2: in-memory dict is ahead; disk shows stale state. Next successful `_persist_state()` catches up, or heartbeat staleness reveals the death.
- `os.rename` is POSIX-atomic: readers see either old complete or new complete, never torn.

### Read ordering (consumers)

- **`/catchup`** — reads `.claude/handoff.md` (Tier 1). May read `.claude/orchestrator-debug/<slug>-result.md` on `/catchup phase N` with a slice pointer.
- **`_reconcile_resume_state()`** — reads `result.json`, `slice.yaml`, `git rev-parse HEAD`.
- **Fleet coordinator (future)** — reads `index.jsonl` via tail; reads per-slice `result.json` on demand.
- **Humans** — read `result.md` primarily, fall back to `result.json` for machine-level inspection.

Readers always assume `result.json` may lag live state by up to one phase transition. `.heartbeat` mtime is the "liveness now" signal.

### Exit paths and what persists

| Exit scenario | Terminal `status` | Path to terminal write | What persists |
|---------------|-------------------|------------------------|---------------|
| Normal OK close | `OK` | `close_slice()` writes state; `atexit` fires but is no-op | Full state, MD, handoff.md, slice.yaml, commit |
| FAILED after retries | `FAILED` | `run_phase_loop` returns 1; `atexit` fires `_final_persist_and_md` | Full state, MD (no commit, no wipe) |
| ESCALATE_TO_USER | `ESCALATED` | Same as FAILED | Full state, MD |
| ABORT | `ABORTED` | `_abort_slice` sets state; `atexit` fires | Full state, MD, slice.yaml aborted |
| SIGINT / SIGTERM | `SIGNALED` | `_clean_shutdown` terminates child, calls `sys.exit(130)`; `atexit` writes | Full state, MD |
| SIGKILL / hard crash | (stale) | No cleanup | Last `_persist_state()` write + last heartbeat touch |
| OOM / power loss | (stale) | Same as SIGKILL | Same |

**Key property:** in every soft-exit path, terminal state hits disk via `atexit`. Only SIGKILL leaves stale state; heartbeat age signals the death.

### Resume reconciliation matrix (DC-6)

| `result.json` status | `slice.yaml` | Git HEAD | Action |
|----------------------|--------------|----------|--------|
| absent | absent | (any) | Fresh slice — start at Phase 1 |
| `IN_PROGRESS` | `in-progress` | HEAD matches JSON's `current_phase` | Resume at `current_phase` |
| `IN_PROGRESS` | `in-progress` | HEAD ahead of JSON's `current_phase` | **Diverge** — print "JSON stale vs. HEAD"; exit 1 |
| `IN_PROGRESS` | `in-progress` | HEAD behind JSON's `current_phase` | **Diverge** — print "expected commit missing"; exit 1 |
| `IN_PROGRESS` | `complete` | has `slice: complete` commit | **JSON lagged after close** — emit warning, fix up JSON in place (status=OK, final_commit=HEAD, ended_at=now), write, exit 0 |
| `OK` | `complete` | `slice: complete` commit present | Slice already closed — print "already closed"; exit 0 |
| `OK` | `complete` | commit missing | **Diverge** — print "JSON OK but no commit"; exit 1 |
| `OK` | `in-progress` | (any) | **Diverge** — print "JSON ahead of slice.yaml"; exit 1 |
| `DEGRADED` | (any) | (any) | Treat as `IN_PROGRESS`; apply the corresponding row above |
| `FAILED` / `ABORTED` / `SIGNALED` | `in-progress` | (any) | **Refuse** — print "prior run terminated as <status>; manual intervention required"; exit 1 |
| corrupt JSON | (any) | (any) | **Refuse** — print "result.json parse error"; exit 1 |

### Multi-instance forward-compat (even though not landed)

- **Per-worktree isolation** — each orchestrator has its own slice_id, result.json, heartbeat. No collisions.
- **`index.jsonl` is per-worktree** (not globally shared). Same-worktree appends are O_APPEND-safe.
- **Atomic writes everywhere** — concurrent readers never see torn files.

---

## Error Handling

### Policy

**Lifecycle operations are strict.** Wipe failures, commit failures, resume divergence → slice exits non-zero.

**Observability writes use retry → degrade → fail (three-level model):**

1. **Level 1 — Bounded retry.** `_atomic_write()` retries once with no delay on OSError (Option B from brainstorming). If the retry succeeds, the transient is invisible; the error is logged to stderr.
2. **Level 2 — Degraded mode.** If the retry also fails, the slice enters `DEGRADED` status. `degradation_reason` is populated. Slice continues running; consumers see the status change and can respond.
3. **Level 3 — Strict failure.** If the `DEGRADED` state write itself fails (can't even record the degradation), the orchestrator exits FAILED with explicit reason: `orchestrator: observability fully unwritable; cannot continue`.

### Failure catalog

| Failure | Severity | Behavior | User sees |
|---------|----------|----------|-----------|
| `_atomic_write()` transient | Level 1 (retry) | Two attempts total, no delay | Stderr log on first failure |
| `_persist_state()` exhausts retry | Level 2 (degrade) | Set `status=DEGRADED`, `degradation_reason`, continue | Live stderr + `degradation_reason` in next readable state |
| `_write_result_md()` fails | Level 2 (degrade) | Same | Same |
| `_append_index_entry()` exhausts retry | Level 2 (degrade) | Same; entry dropped | Same |
| Heartbeat thread write fails | Self-healing | try/except in loop; continues | Stderr log per unique error class |
| Heartbeat thread dies | Level 2 + restart | Main thread detects on periodic sampling; attempts one restart; if restart fails, status=DEGRADED | Stderr + degradation in state |
| `DEGRADED` state write also fails | **Level 3 (strict)** | Exit FAILED | `orchestrator: observability fully unwritable; cannot continue` |
| `_wipe_current_slice()` fails | Strict (DC-5) | Raise `RuntimeError`; close_slice propagates; exit non-zero | Stderr + full traceback |
| `_bundle_handoff_md()` fails | Strict | Raise; close_slice propagates | Stderr + traceback |
| `_git commit` fails in close_slice | Strict (B11) | `_git` helper raises | Stderr + git stderr |
| Resume reconciliation diverges | Strict (DC-6) | Print triple + diagnostic; exit 1 | Triple + suggested action |
| Corrupt `result.json` on resume | Strict | Exit 1 | Parse error + path |
| Phase-3 cluster agent failure | Existing flow | FAILED classification + backoff (B8); then triager | Live stderr + cluster log path |

### Signal + atexit interaction

- **Normal exit** (return 0, return 1) → `atexit` fires `_final_persist_and_md()`. Single terminal writer.
- **SIGINT / SIGTERM** → `_clean_shutdown` (existing, B13) terminates child subprocess, then `sys.exit(130)`. `atexit` fires. Handler does not duplicate the state write; atexit is the single writer.
- **SIGKILL / hard crash** → no cleanup. Last `_persist_state()` write + last heartbeat touch survive.
- **Exception from `close_slice` or `run_phase_loop`** → caught by `main()`; `atexit` fires; traceback to stderr via live-stream.

### Error message style

```
orchestrator: <short description>: <details or path>
```

Prefixed to stderr; consistent with existing `_git` helper output.

---

## Testing

### Test organization

Per-concern files, not per-DC. Matches cairn's existing convention (e.g., `test_dispatch_contract_separation.py` bundles three related tests).

### Contract-to-test mapping

| Contract | Test file | Tests |
|----------|-----------|-------|
| **DC-1** | `test_observability_writer.py` | `test_md_is_derived_from_json_state` |
| **DC-2** | `test_heartbeat.py` | `test_heartbeat_never_writes_result_json`, `test_state_writer_never_writes_heartbeat` |
| **DC-3** | `test_close_slice_hardened.py` | `test_close_slice_twice_is_noop`, `test_close_slice_short_circuits_on_already_closed_state` |
| **DC-4** | `test_agent_prompt_updates.py` + `test_close_slice_hardened.py` | `test_phase_4_prompt_forbids_self_commit`, `test_close_slice_produces_single_slice_complete_commit` |
| **DC-5** | `test_close_slice_hardened.py` | `test_wipe_clears_all_except_slice_yaml`, `test_wipe_raises_on_undeletable_file` |
| **DC-6** | `test_resume_reconcile.py` | Nine tests, one per matrix row |
| **DC-7** | `test_cross_slice_isolation.py` | `test_sequential_slices_keep_separate_result_files`, `test_slice_id_slug_used_in_all_debug_paths`, `test_index_jsonl_entries_include_slice_id_tag` |

### Test file list (full)

```
tests/unit/
├── test_observability_writer.py
├── test_state_schema.py
├── test_heartbeat.py
├── test_close_slice_hardened.py
├── test_resume_reconcile.py
├── test_cross_slice_isolation.py
└── test_agent_prompt_updates.py

tests/integration/
└── test_signal_observability.py
```

### Test function inventory

`test_observability_writer.py`:
- `test_atomic_write_succeeds_first_attempt`
- `test_atomic_write_retries_once_on_oserror`
- `test_atomic_write_raises_on_second_failure`
- `test_persist_state_uses_atomic_write`
- `test_persist_state_preserves_schema_version`
- `test_write_result_md_only_runs_on_terminal_transition`
- `test_md_is_derived_from_json_state` (DC-1)
- `test_append_index_entry_atomic_under_interleaved_writes`
- `test_degraded_status_replaces_in_progress_on_retry_exhaustion`
- `test_degradation_reason_persists_through_terminal_transition`

`test_state_schema.py`:
- `test_state_dict_includes_schema_version`
- `test_state_dict_required_fields_present`
- `test_status_enum_values_match_spec`
- `test_worktree_path_and_orchestrator_pid_populated_on_init`

`test_heartbeat.py`:
- `test_heartbeat_updates_file_periodically`
- `test_heartbeat_survives_transient_write_error`
- `test_heartbeat_thread_death_detected_by_main_thread`
- `test_heartbeat_one_restart_attempt_then_degrade`
- `test_heartbeat_stops_cleanly_on_sigterm`
- `test_heartbeat_never_writes_result_json` (DC-2)
- `test_state_writer_never_writes_heartbeat` (DC-2)

`test_close_slice_hardened.py`:
- `test_close_slice_twice_is_noop` (DC-3)
- `test_close_slice_short_circuits_on_already_closed_state` (DC-3)
- `test_close_slice_bundles_handoff_before_wipe`
- `test_close_slice_wipe_runs_before_commit`
- `test_wipe_clears_all_except_slice_yaml` (DC-5)
- `test_wipe_raises_on_undeletable_file` (DC-5)
- `test_close_slice_produces_single_slice_complete_commit` (DC-4)

`test_resume_reconcile.py` (DC-6):
- `test_resume_fresh_slice_starts_at_phase_1`
- `test_resume_in_progress_matching_state_resumes`
- `test_resume_exits_1_when_head_ahead_of_json_phase`
- `test_resume_exits_1_when_head_behind_json_phase`
- `test_resume_exits_0_when_already_closed`
- `test_resume_exits_1_when_json_ok_but_commit_missing`
- `test_resume_exits_1_when_json_ahead_of_slice_yaml`
- `test_resume_fixes_up_lagged_json_when_close_succeeded`
- `test_resume_refuses_to_resume_failed_slice`
- `test_resume_exits_1_on_corrupt_result_json`

`test_cross_slice_isolation.py` (DC-7):
- `test_sequential_slices_keep_separate_result_files`
- `test_slice_id_slug_used_in_all_debug_paths`
- `test_index_jsonl_entries_include_slice_id_tag`

`test_agent_prompt_updates.py`:
- `test_phase_1_prompt_mentions_bash_heredoc_escape` (P1)
- `test_phase_2_prompt_mentions_bash_heredoc_escape` (P1)
- `test_phase_3_prompt_mentions_bash_heredoc_escape` (P1)
- `test_phase_4_prompt_mentions_bash_heredoc_escape` (P1)
- `test_all_phase_prompts_have_do_not_refuse_preemptively_rule` (P2)
- `test_phase_4_prompt_explicitly_forbids_self_commit` (DC-4)

`tests/integration/test_signal_observability.py`:
- `test_sigterm_writes_signaled_status_via_atexit`
- `test_atexit_writes_final_state_on_normal_exit`
- `test_atexit_writes_final_state_on_failed_exit`

**Total:** 35 unit tests + 3 integration tests across 8 test files.

### Cluster assignment (Phase 2 output)

```yaml
# .claude/current-slice/validation/coupling-clusters.yaml

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

### RED suite skeleton (Phase 2 deliverables)

Phase 2 skeptic produces:

1. `.claude/current-slice/validation/approach.md` — how tests map to DCs; references the DC-6 matrix; links to this design doc.
2. `.claude/current-slice/validation/coupling-clusters.yaml` — as above.
3. All 8 test files with skeleton bodies — each test has arrange / act / assert structure, with calls to functions that do not exist yet (ImportError / NameError at collection time, or calls to stub `NotImplementedError` functions).
4. Any conftest fixtures needed (e.g., fixture for creating a mock slice.yaml + git repo + debug-dir in `tmp_path`).

After Phase 2 commits, `uv run pytest tests/unit/ tests/integration/` must RED for every listed function. Phase 3 clusters turn them GREEN.

### Phase 4 integration gates

- `uv run pytest tests/unit/ tests/integration/ -v` — all GREEN
- `uv run python scripts/validate_architecture.py` — passes (no INV changes this slice)
- `uv run python scripts/integration_gate.py` — passes
- **New gate — end-to-end observability smoke test:** spawn a trivial slice via the orchestrator; assert `orchestrator-result.json` exists with `status: OK`, `orchestrator-result.md` generated, `index.jsonl` has entries for phases and close, `.claude/current-slice/` wiped except `slice.yaml`, `.heartbeat` removed.

---

## Items queued for `/decision` (architectural commitments to lock before `/start-slice`)

| Tag | Item |
|-----|------|
| `[DECISION]` **D1** | Placement in `.claude/orchestrator-debug/` vs. `.claude/current-slice/` |
| `[DECISION]` **D2** | JSON primary + MD derived via pure function |
| `[DECISION]` **D3** | Forward-compat schema fields + atomic-write helper adopted now |
| `[DECISION]` **DC-3** | `close_slice` idempotency contract (candidate for INV elevation) |
| `[DECISION]` **DC-4** | `close_slice` is sole source of `slice: complete` commit; Phase-4 agent does not self-commit (candidate INV; changes agent-prompt behavior) |
| `[DECISION]` **DC-7** | Cross-slice artifact isolation via slice-id-keyed filenames (candidate INV) |
| `[DECISION]` | DC-4 enforcement mechanism: prompt-change (chosen) vs. orchestrator-side reconciliation |
| `[DECISION]` | State-dict schema v1.0: exact field set, types, required vs. optional |
| `[DECISION]` | Heartbeat cadence default (`CAIRN_HEARTBEAT_INTERVAL` = 10.0s) and staleness threshold (`CAIRN_HEARTBEAT_STALE` = 30.0s) |
| `[DECISION]` | `_clean_shutdown` signal handler does not duplicate atexit writes — atexit is single terminal writer |
| `[DECISION]` | DC-6 resume matrix row set — revised row "IN_PROGRESS / complete / commit present = JSON lagged after close, fix up in place, exit 0" |
| `[DECISION]` | `status=DEGRADED` as enum value (not separate `was_degraded` flag); `degradation_reason` persists across terminal transition |
| `[DECISION]` | Observability write retry strategy: Option B (one retry, no delay) |
| `[DECISION]` | MD write cadence: close-only (not per-transition) |
| `[DECISION]` | Heartbeat restart policy: one attempt then degrade |

The `/decision` run reads this entire design doc + the companion brainstorm doc, synthesizes a decision record, and produces an ADR that codifies the architectural commitments (especially the INV-elevation candidates DC-3, DC-4, DC-7).

---

## Future work (queued for follow-up slices)

- **Multi-instance hardening** (original §3.0 scope): E1 worktree-scoped `fcntl.flock`, E2 PID-scoped `role_guard`, parallel-worktree integration test.
- **Path C** — orchestrator-owned writes to resolve A1 sensitive-file gate permanently. Design queued per session handoff.
- **INV elevation** for DC-3, DC-4, DC-7 via a new ADR (`orchestrator-close-slice-and-observability-contract` or similar name) — produces three new INV entries in `docs/ARCHITECTURE.md` with `invariant-check` blocks pointing to this slice's regression tests.
- **Ruff F841** leftover at `tests/unit/test_post_timeout_reconcile.py:101` — housekeeping.

---

## References

- **Learnings driving this slice:** `.claude/learning.md` L1 (A1 spike scope-inadequate), L2 (bypassPermissions half-broken), L3 (Bash-heredoc workaround), L4 (don't refuse preemptively), L5 (fencing tolerance in parser), L6 (test mocking rule), L7 (B14+B15 validated live), L8 (close_slice wipe gap), C1 (d3-bypass ADR caveat), C2 (close_slice weakest link).
- **Prior slice:** `compression/slice-2-state-machine` — landed B1–B16; closed at commit `9b34f44`.
- **Related design doc:** `docs/plans/2026-04-20-compression-pipeline-hardening-design.md` — failure-mode taxonomy (A/B/D/E codes); §6 covered Slice 2, §7 covered original Slice 3 scope.
- **Related plan doc:** `docs/plans/2026-04-20-compression-pipeline-hardening-plan.md` §3.0 — original Slice 3 brief; scope partially superseded by this doc.
- **Project invariants:** `docs/ARCHITECTURE.md` INV-001 through INV-007.
- **Validator:** `scripts/validate_architecture.py`.

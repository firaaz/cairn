# Compression Pipeline Hardening — Design

**Date:** 2026-04-20
**Feature:** `compression`
**Branch:** `feature/compression`
**Status:** Design approved (this session). Forward plan pending via `writing-plans`.
**Brainstorm source:** 2026-04-20 debugging session following closure of `identifier-scheme/rename-sweep-test-robust` (2026-04-20, D3 bypass).

## 1. Context

Cairn's compression pipeline (`scripts/slice_orchestrator.py` + 5 role agents + `checks/role_guard.py`) shipped via feature `compression` Slice A. The central claim — a single session completes a four-phase slice via dispatched role-scoped subagents, no user intervention between phases — **has not been demonstrated end-to-end.** Every completed slice since Slice A closed has relied on human backstopping at phase boundaries.

Failure evidence from the most recent slice (`identifier-scheme/rename-sweep-test-robust`, closed 2026-04-20 via D3 bypass):

- `phase-1-writer` RAISE_ISSUE — couldn't write `.claude/current-slice/intent.md` / `slice.yaml`.
- `phase-2-skeptic` RAISE_ISSUE — couldn't write `.claude/current-slice/validation/approach.md`.
- `phase-3-implementer` RAISE_ISSUE — Phase 2 authoring bug (C1 test self-reference).
- `phase-4-integrator` FAILED twice — couldn't write `.claude/current-slice/integration/sweep-notes.md` even with explicit `settings.json` allowlist + `--permission-mode acceptEdits` + `--permission-mode bypassPermissions`.

All four `.claude/**`-write blocks share a root cause: the Claude Code harness's sensitive-file gate fires inside nested `claude -p` subagent sessions and is not overridden by `permissions.allow` or `--permission-mode` flags. The agent sees an interactive permission prompt and has no user to approve, so it escalates.

In parallel, audit of `scripts/slice_orchestrator.py` (482 lines) reveals seventeen code-level bugs spanning dispatch, state-machine, serialization, and fan-out concerns. Plus three observability and two concurrency gaps.

**Constraint — "base strong."** Fleet coordinator (Feature 6, designed 2026-04-15) spawns N slice orchestrators concurrently in separate worktrees. Every known failure mode multiplies N× at that scale. The hardening must close the full failure list, not a tier of it.

## 2. Failure modes inventory

Categorized; each has a mechanical regression test in the plan.

### A — Harness / permissions (observed)

- **A1.** Subagent sensitive-file gate blocks `.claude/current-slice/**` writes despite `settings.json` allowlist and permission-mode flags. Load-bearing: every phase hits this.
- **A2.** Subagent `mkdir` under `.claude/current-slice/` is also gated. Integrator needs dir before Write.
- **A3.** `checks/role_guard.py` exists but is NOT registered in `.claude/settings.json`. Inner gate of the two-layer gating (ADR `compression-infrastructure-bootstrap`) is absent in practice.

### B — Orchestrator code bugs

- **B1.** `dispatch_agent` checks `status == "OK"` but `issue-triager` returns `{action, target_phase}` — every triager call writes a noise failure log. Logged twice in the last slice's debug directory.
- **B2.** `dispatch_phase_3` fast-fails on first RAISE_ISSUE / FAILED and discards peer-cluster results. Triage info lost.
- **B3.** Line 417: `f'brief: "{brief}"'` — unescaped. `"`, `\`, or `\n` in the brief breaks `slice.yaml`.
- **B4.** Same class at lines 416 and 427 for `name`.
- **B5.** `_parse_structured_tail` is line-oriented. Pretty-printed multi-line JSON tail silently mis-parses as FAILED.
- **B6.** `_parse_clusters` is ad-hoc — brittle to comments, indentation variance, quoted paths with colons.
- **B7.** `AGENT_ENVELOPE` uses `:` separator. Breaks on paths containing `:`.
- **B8.** FAILED retry is one-shot, no classification (transient/malformed/logic). No backoff. Rate-limit failures waste retry budget.
- **B9.** Timeout kills subprocess but doesn't reconcile partial commits the child may have made. Git state ambiguous post-timeout.
- **B10.** `close_slice` defined at line 424 but never called. Phase 4 OK → loop exits → slice stays `in-progress` forever.
- **B11.** `commit_phase_handoff` uses `subprocess.run(..., check=False)` for every git call. Silent failures advance phase as if handoff committed.
- **B12.** `_current_phase` swallows parse errors and returns 1 — malformed `slice.yaml` silently restarts Phase 1.
- **B13.** No SIGINT / SIGTERM handler. Ctrl+C orphans `claude -p` child; state ambiguous.
- **B14.** `RE_DISPATCH` updates in-memory `phase` but not `slice.yaml.current_phase`. Crash mid-redispatch → `--resume` restarts at wrong phase.
- **B15.** Design §6 specifies "max 1 re-dispatch per phase"; code doesn't enforce it. Pathological triager loops indefinitely.
- **B16.** `dispatch_phase_3` with empty-files cluster: `AGENT_ENVELOPE=""` → `role_guard._envelope_patterns("") → []` → all writes denied. Deadlock once hook is wired.
- **B17.** `dispatch_agent` embeds the phase-return contract; triager and any future non-phase agents need separate contracts.

### D — Observability gaps

- **D1.** Failure logs flat, not indexed by slice-id. Hard to grep at scale.
- **D2.** Per-cluster stdout lost in Phase 3 (B2 above).
- **D3.** No live progress between phases. Subprocess is `capture_output=True` — nothing visible until completion.

### E — Concurrency / multi-instance

- **E1.** No lockfile on `.claude/current-slice/`. Two orchestrators in the same worktree would race.
- **E2.** Global `AGENT_ROLE` env var. If role-guard is wired, an ambient `AGENT_ROLE=...` in the user's shell activates the hook outside orchestrator dispatch.

## 3. Architecture decision — A1 resolution path

Load-bearing because A1's fix determines the agent-return contract, which determines whether several B-bugs exist at all. Empirical determination in Slice 1's Phase 2, before committing to a path.

**Spike (Slice 1 Phase 2, ~2 hours):**
- Spike 1: `additionalDirectories` in `settings.json` overlay.
- Spike 2: `--permission-mode bypassPermissions` re-verified (handoff says tried; verify against current CLI version).
- Spike 3: Claude Agent SDK Python invocation instead of `claude -p` CLI.

Each spike = one shell command against `phase-2-skeptic` writing `.claude/current-slice/validation/approach.md`. Results persisted to `docs/plans/2026-04-20-a1-spike-results.md`.

**Path X — current contract, settings fix.** One spike works. `role_guard.py` gets wired; minor dispatch cleanup. Cheapest.

**Path Y — contract redesign, orchestrator-owned disk writes.** No spike works. Agents return `{status, artifacts: {path: content}, summary, ...}` via stdout JSON. Orchestrator writes all `.claude/**` files with `Path.write_text` (not a Claude session — not subject to harness). Agents keep non-sensitive writes (`tests/`, source). Architecturally preferred (matches compression design doc §6 P6 — "orchestrator is code, not a Claude session"), more expensive (5 agent prompts + dispatch pathway + tests change).

**Decision:** the spike is cheap insurance. Commit to Path X if any spike works; fall through to Path Y otherwise. Slice 1 absorbs whichever wins.

## 4. Slice decomposition

Three back-to-back slices. Slice 1 is foundational; Slices 2 and 3 can be executed via the now-working compression pipeline (dogfood).

| Slice | Scope | Size |
|---|---|---|
| **1 — foundation** | A1 spike + resolution (Path X or Y), A3 role_guard wiring, B1 dispatch contract separation, B5 multi-line JSON tail, B17 per-role return parsers, live-stderr observability brought forward from Slice 3. | medium-large |
| **2 — state machine + serialization** | B2, B3, B4, B6, B7, B8, B9, B10, B11, B12, B13, B14, B15, B16. Regression test per bug. PyYAML adoption for cluster + slice.yaml parsing. | medium |
| **3 — multi-instance + observability** | E1 worktree lockfile, E2 role-guard PID scope, D1 debug log index, D3 structured JSON exit for fleet-coordinator consumption, parallel-worktree dogfood integration test. | medium (smallest) |

## 5. Slice 1 — foundation

### 5.1 A1 spike + resolution

Described in §3 above. Spike produces `docs/plans/2026-04-20-a1-spike-results.md`; resolution path (X or Y) drives the rest of the slice.

### 5.2 role_guard.py wiring (A3)

Register in `.claude/settings.json` as a PreToolUse hook for `Write | Edit | MultiEdit | NotebookEdit`:

```json
{
  "matcher": "Write|Edit|MultiEdit|NotebookEdit",
  "hooks": [{"type": "command", "command": "uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py"}]
}
```

`role_guard.py` as-is already no-ops when `AGENT_ROLE` is unset (line 62 — compat preserved).

### 5.3 Dispatch contract separation (B1, B5, B17)

Replace `dispatch_agent(role, inputs) → dict` with typed pair:

```python
def dispatch_phase_agent(role, inputs, ...) -> PhaseResult:
    # contract: {status: "OK|RAISE_ISSUE|FAILED", commit_hash, summary, ...}

def dispatch_triager(issue_hash, phase, slice_id) -> TriagerResult:
    # contract: {action: "ESCALATE_TO_USER|RE_DISPATCH|ABORT", target_phase, amendment, rationale}
```

Shared internals: `_run_claude_subprocess`, `_parse_structured_tail`, `_write_failure_log`. Differing: expected-schema validation and "what counts as a clean return."

`_parse_structured_tail` (B5) gains multi-line JSON support: scan backwards from last line's closing `}`, walk up until brace-balanced, attempt `json.loads`. Line-scan fallback preserved for backward-compat.

### 5.4 Live-stderr observability (moved forward from Slice 3)

Replace `subprocess.run(capture_output=True)` with `subprocess.Popen(stderr=PIPE, stdout=PIPE)` + tee pump that streams child stderr to orchestrator stderr in real-time while also buffering for post-hoc capture. Each line prefixed `[phase-N-role|slice-id]`.

`CAIRN_ORCHESTRATOR_DEBUG` env var controls verbosity; default-on until autonomous end-to-end is proven, then default-off.

Debug log filename becomes `{slice-id-slug}-phase-{n}-{role}-{timestamp}.log` (D3 brought forward — trivial rename at the existing write site).

### 5.5 Slice 1 tests

- `tests/unit/test_dispatch_contract_separation.py` — triager contract validates; valid triager returns produce no noise log.
- `tests/unit/test_multiline_json_tail.py` — pretty-printed JSON tail parses to object.
- `tests/unit/test_role_guard_wired.py` — settings.json registers the hook; hook fires on Write/Edit tool calls.
- `tests/unit/test_orchestrator_live_stderr.py` — child stderr reaches orchestrator stderr within < 500ms of emission.
- **`tests/integration/test_compressed_slice_end_to_end.py`** — a trivial slice runs four phases via the orchestrator, zero human intervention, exit code 0, `sweep-notes.md` present, `slice.yaml status: complete`.

Slice 1 passes when the integration test is GREEN.

## 6. Slice 2 — state machine + serialization

### 6.1 State-machine durability

- **B10** `close_slice(state)` invoked at the end of `run_phase_loop` on OK-from-Phase-4. Transitions `slice.yaml`, rebuilds `.claude/handoff.md` from phase handoffs, advances `sweep.yaml.last-sweep-at-slice-id`, final commit.
- **B14** Before `phase = target; continue` in the RE_DISPATCH branch, persist `current_phase: target` to `slice.yaml` and commit `"slice: re-dispatch phase N → phase T"`. `--resume` recovers correctly.
- **B15** In-memory `redispatch_count: dict[int, int]`. Second RE_DISPATCH to same phase escalates to user.
- **B12** `_current_phase` on parse error exits 1 with clear message pointing at `slice.yaml`. No silent restart.
- **B13** `signal.signal(SIGINT | SIGTERM, _clean_shutdown)`. Handler: SIGTERM the active `Popen` child, wait 5s, SIGKILL if alive, exit 130.

### 6.2 Git-state reconciliation

- **B11** Every `subprocess.run(["git", ...])` call goes through a `_git(cmd)` helper that asserts `returncode == 0` and raises on failure with the command's stderr. No silent advance.
- **B9** After `TimeoutExpired`, `_git("log", "--oneline", "-1")` compares HEAD against pre-dispatch HEAD. If advanced, record `{partial_commit: sha, timeout: s}` in failure log so triager can decide.

### 6.3 Serialization (PyYAML adopted)

- **B3/B4** `read_slice_state` replaced with `yaml.safe_load`. Writes use `yaml.safe_dump` with `default_flow_style=False`. Brief / name with any character now round-trip correctly.
- **B6** `_parse_clusters` replaced with `yaml.safe_load` + explicit schema validation (list of `{name: str, files: list[str]}`). Malformed → clear error.
- **B7** `AGENT_ENVELOPE` encoded as JSON list: `'["path1","path2"]'`. `role_guard._envelope_patterns` parses via `json.loads`. Paths with `:` safe.

`pyproject.toml`: `uv add pyyaml`.

### 6.4 Phase 3 robustness

- **B16** `dispatch_phase_3` with empty clusters or all-empty-files: warn once, dispatch one implicit cluster with envelope from `intent.md`. If intent envelope also empty: return FAILED with clear message.
- **B2** Every cluster's result collected and written to `.claude/orchestrator-debug/{slice-id}-phase-3-cluster-{name}-{timestamp}.log`, even on fast-fail return. First RAISE_ISSUE / FAILED still determines orchestrator return, but peer diagnostics preserved.
- **B8** FAILED classification:
  - `transient`: returncode in {124}, or "rate limit"/"overloaded"/"429"/"503" in stderr → retry up to 3× with exponential backoff (1s, 4s, 16s).
  - `malformed`: unparseable JSON tail → retry once.
  - `logic`: agent self-reported FAILED → retry once.
  - Classification logged to failure-log.

### 6.5 Slice 2 tests

Fourteen unit tests (one per bug). Plus:
- `test_orchestrator_resume_correctness.py` — mid-redispatch crash → `--resume` → state recovered.
- `test_orchestrator_signal_handling.py` — SIGTERM mid-phase → child reaped, state file consistent, exit 130.
- `test_phase_3_parallel_isolation.py` — 3 mock clusters, 1 fails fast, peer diagnostics captured.

Slice 2 passes when: every B-bug test GREEN and Slice 1 integration test still GREEN.

## 7. Slice 3 — multi-instance + observability

### 7.1 Worktree lock (E1)

`fcntl.flock` on `.claude/current-slice/.lock` at orchestrator entry, non-blocking acquire. Worktree-scoped (one lock per worktree, which is the right granularity). Second orchestrator in same worktree → clean abort with PID of holder. Different worktrees → both run.

### 7.2 Role-guard scope (E2)

`role_guard.py`: if `AGENT_ROLE` set but `CAIRN_ORCHESTRATOR_PID` unset or PID mismatch, deny with clear error. Orchestrator sets both env vars at dispatch. Prevents ambient `AGENT_ROLE` activation.

### 7.3 Structured JSON exit

On exit, write `.claude/current-slice/orchestrator-result.json`:

```json
{
  "slice_id": "...",
  "status": "OK|FAILED|ABORTED|ESCALATED",
  "exit_code": 0,
  "final_commit": "...",
  "phases_completed": [1, 2, 3, 4],
  "redispatches": {"2": 1},
  "started_at": "...",
  "ended_at": "...",
  "summary": "..."
}
```

Fleet coordinator reads this for rich detail; exit code is the fast-path signal.

### 7.4 Debug log index (D1)

`.claude/orchestrator-debug/index.jsonl` — one line per failure: `{timestamp, slice_id, phase, role, reason, log_path}`. Appended atomically with `O_APPEND`. `grep -E` / `jq` is the query surface.

### 7.5 Parallel-worktree dogfood

`tests/integration/test_parallel_worktrees.py`:

1. Create two temp git worktrees of the current branch.
2. Write distinct trivial slice specs into each.
3. Launch both orchestrators concurrently via `Popen`.
4. Wait with timeout.
5. Assert: both exit 0; both `orchestrator-result.json` have `status: OK`; commits on each worktree's branch only; no cross-contamination.

Proof-of-safety for fleet-coordinator parallel-slice dispatch.

### 7.6 Slice 3 tests

- `test_slice_lock.py` — second orchestrator in same worktree aborts with PID message.
- `test_role_guard_pid_scope.py` — ambient `AGENT_ROLE` without orchestrator PID → denied.
- `test_orchestrator_result_json.py` — JSON produced on every exit path (OK, FAILED, ABORTED, ESCALATED).
- `test_debug_log_index.py` — index append atomic under concurrent writes.
- **`test_parallel_worktrees.py`** — integration proof.

Slice 3 passes when: parallel-worktree test GREEN and Slice 1/2 regression stays GREEN.

## 8. Cross-cutting — dependencies and invariants

- **pyproject.toml:** `uv add pyyaml`. Only new dep. Rationale recorded in memory (`stdlib_only_scope.md`): CLAUDE.md "stdlib-only" targets Python-idiom deps (decorators, metaprogramming), not libs with Rust equivalents.
- **ADR impact:** `compression-infrastructure-bootstrap` unchanged — role_guard's mechanism is what that ADR authorized. `cliff-failure-mode-and-v1-defenses` D4 unchanged — no new role-keyed mechanism introduced; scope stays "role-keyed write-path hook" per the authorization.
- **Invariants touched:** INV-003 (the same narrow exception compression-infrastructure-bootstrap created); no others.
- **Consumer impact:** Downstream projects consuming via `.slice-system → .` see: new PyYAML dep, role_guard now fires when `AGENT_ROLE` set (still no-op otherwise), new `.claude/current-slice/.lock` and `.claude/current-slice/orchestrator-result.json` files. No breaking changes.

## 9. Exit criteria — "base strong"

- **Autonomous end-to-end slice** (Slice 1 integration test): one `/start-slice "<brief>"`, zero human touches between init and close.
- **Zero known bugs** (Slices 2 + 3 regression tests): every A/B/D/E item on §2 has a mechanical test.
- **Parallel-worktree safety** (Slice 3 integration test): two orchestrators in two worktrees, concurrent, both complete without cross-contamination.
- **Fleet-coordinator interface** (Slice 3): `orchestrator-result.json` on disk + structured exit code.
- **Debug visibility** (Slice 1): live stderr streaming, slice-id-correlated logs, indexed failures.

When all five hold, fleet coordinator (Feature 6) can consume the pipeline as a reliable primitive.

## 10. Out of scope

- **Fleet coordinator itself (Feature 6).** This design is the foundation F6 consumes; the daemon/FIFO/asyncio architecture is orthogonal and already designed (`2026-04-15-fleet-coordinator-design.md`).
- **Additional agent roles.** Current five (phase-1..4 + triager) are sufficient. Splitting phase-3 by change-type (refactor vs greenfield vs bugfix) stays deferred per `2026-04-18-slice-compression-protocol-design.md` §12 Q3.
- **Windows portability.** `fcntl.flock` is POSIX. Windows port (if ever) uses `msvcrt.locking`. Not in scope.
- **Rust port.** End-of-v1; Python design keeps the port mechanical.

## 11. Risks

- **Path Y redesign enlarges Slice 1.** If all three A1 spikes fail, Slice 1 absorbs the agent-prompt rewrite + orchestrator artifact-write pathway. Mitigation: Slice 1's envelope is already written to accommodate Path Y; the size committed up-front.
- **PyYAML adoption crosses a CLAUDE.md line.** Memory entry `stdlib_only_scope.md` clarifies the intent. A CLAUDE.md rephrase is a drive-by consideration next time it's touched; not blocking.
- **Live-stderr streaming may leak secrets if an agent echoes env.** Agents currently don't; if any future agent does, stderr goes to user's terminal. Standard subprocess risk, not cairn-specific. Flagged for agent-prompt review.
- **Parallel-worktree test is slow.** Creating two worktrees + running two full slices via subprocess may take minutes. Marked as integration test; not in the unit default.

## 12. Pointers

- `scripts/slice_orchestrator.py` (482 lines) — the orchestrator to harden.
- `checks/role_guard.py` (98 lines) — the inner gate to wire.
- `.claude/settings.json` — hook registration site.
- `.claude/orchestrator-debug/` (gitignored) — existing failure-log directory; logs from recent slice inform the failure-modes inventory.
- `docs/adr/compression-infrastructure-bootstrap.md` — authorizing ADR for role_guard; governs scope.
- `docs/plans/2026-04-18-slice-compression-protocol-design.md` — original design; P6 ("orchestrator is code, not a Claude session") is the architectural grounding for Path Y.
- `docs/plans/2026-04-15-fleet-coordinator-design.md` — downstream consumer of this hardening.
- **Companion doc** (to be authored next via `writing-plans`): `docs/plans/2026-04-20-compression-pipeline-hardening-plan.md`.

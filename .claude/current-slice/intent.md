---
slice: compression/slice-2-state-machine
date: 2026-04-20
phase: 1-intent
invariants-touched: [INV-003]
adrs-referenced:
  - compression-infrastructure-bootstrap
  - cliff-failure-mode-and-v1-defenses
  - phase-lock-and-role-declaration
envelope:
  - "scripts/slice_orchestrator.py"
  - "checks/role_guard.py"
  - "tests/unit/test_orchestrator_*.py"
  - "tests/unit/test_role_guard_envelope_json.py"
  - "tests/unit/test_close_slice_invocation.py"
  - "tests/unit/test_redispatch_persistence.py"
  - "tests/unit/test_redispatch_cap.py"
  - "tests/unit/test_malformed_slice_yaml.py"
  - "tests/unit/test_signal_handler.py"
  - "tests/unit/test_git_helper_check.py"
  - "tests/unit/test_post_timeout_reconcile.py"
  - "tests/unit/test_yaml_brief_round_trip.py"
  - "tests/unit/test_yaml_clusters_schema.py"
  - "tests/unit/test_phase_3_empty_cluster_guard.py"
  - "tests/unit/test_phase_3_per_cluster_logs.py"
  - "tests/unit/test_failed_classification_backoff.py"
out-of-scope:
  - "Slice 3 scope: E1 worktree lockfile, E2 role-guard PID scope, D1 debug-log index, D3 orchestrator-result.json, parallel-worktree integration test"
  - "New agent roles or phase-3 splits (deferred per design §10)"
  - "Windows portability of signal/lock primitives"
  - "Modifications to phase-1-writer / phase-2-skeptic / phase-3-implementer / phase-4-integrator / issue-triager agent prompts"
  - "Changes to .claude/settings.json hook registration (Slice 1 scope)"
  - "Live-stderr pump or debug-log filename shape (Slice 1 scope)"
  - "Path Y / Path C agent-return-with-artifacts contract redesign (tracked separately — Slice 1's Path X decision is empirically gapped against the harness sensitive-file gate; follow-up ADR/slice pending)"
---

### What and Why

Slice 1 made the compression pipeline able to run a trivial slice end-to-end; it left fourteen catalogued code-level defects in `scripts/slice_orchestrator.py` that turn every non-trivial slice into a coin-flip and multiply N× under fleet-coordinator parallelism. This slice closes that backlog so the orchestrator behaves deterministically across crashes, malformed input, transient subprocess failure, and Phase 3 fan-out variability — the "base strong" exit criterion of `docs/plans/2026-04-20-compression-pipeline-hardening-design.md` §9.

### Specification Detail

**State-machine durability**

- **B10 — `close_slice` invocation.** `run_phase_loop` MUST call `close_slice(state)` exactly once when Phase 4 returns `status: OK` and the loop exits the `while 1 <= phase <= max_phase` band. After the call, `slice.yaml` carries `status: complete` and `current_phase: 4`, `.claude/handoff.md` is rebuilt by concatenating `handoff-phase-{1..4}.md` (separator: `\n---\n`) followed by `integration/sweep-notes.md` if present, and a single commit `slice: complete` stages both files.
- **B12 — malformed `slice.yaml` exit.** `_current_phase()` MUST NOT return `1` on parse failure; it MUST raise `SystemExit` with exit code `1` and a stderr message of the form `orchestrator: malformed slice.yaml at <path>: <reason>`. The same applies to `_slice_id()` and `_slice_brief()` — they MUST surface parse errors rather than returning fallback strings that silently drive Phase 1 with bogus inputs.
- **B13 — SIGINT/SIGTERM handler.** Orchestrator entry registers `signal.signal(SIGINT, _clean_shutdown)` and `signal.signal(SIGTERM, _clean_shutdown)`. `_clean_shutdown(signum, frame)` SIGTERMs the active `Popen` child (tracked in a module-level `_active_child` reference set by `_run_with_live_stderr`), waits up to `int(os.environ.get("CAIRN_SHUTDOWN_GRACE_S", "5"))` seconds, SIGKILLs if still alive, and exits 130 (SIGINT) or 143 (SIGTERM).
- **B14 — RE_DISPATCH persistence.** Before the `phase = target; continue` line in the `RE_DISPATCH` branch, persist `current_phase: target` to `slice.yaml` (round-trip via PyYAML — see B3) and stage+commit with message `slice: re-dispatch phase {N} → phase {target}`. `--resume` after mid-redispatch crash MUST land at `target`, not `N`.
- **B15 — max-1 redispatch cap.** `run_phase_loop` MUST maintain `redispatch_count: dict[int, int]` (key = source phase). On the second RE_DISPATCH whose source phase is already in the dict, the orchestrator MUST escalate to user with stderr message `orchestrator: phase {N} re-dispatched twice; escalating per design §6.1` and return exit code `1` without invoking the triager again.

**Git-state reconciliation**

- **B11 — `_git` helper.** Every `subprocess.run(["git", ...])` call site in `slice_orchestrator.py` (currently in `commit_phase_handoff`, `_abort_slice`, `init_new_slice`, `close_slice`) MUST route through a `_git(*args, **kwargs) -> subprocess.CompletedProcess` helper that calls `subprocess.run([...], check=True, capture_output=True, text=True)` and on `CalledProcessError` raises with the original `stderr` re-attached to the exception message. No silent advancement on failed git commits.
- **B9 — post-timeout HEAD reconciliation.** `_run_with_live_stderr` captures `pre_dispatch_head = _git("rev-parse", "HEAD").stdout.strip()` before `Popen.start`. On `subprocess.TimeoutExpired`, after killing the child, the orchestrator runs `post_head = _git("rev-parse", "HEAD").stdout.strip()`; if `post_head != pre_dispatch_head`, the failure log MUST include `{partial_commit: <post_head>, pre_dispatch_head: <pre_head>, timeout_s: <elapsed>}` so the triager can see partial progress.

**Serialization (PyYAML adopted; dep already in `pyproject.toml`)**

- **B3/B4 — brief + name round-trip.** `read_slice_state(path)` MUST be replaced with `yaml.safe_load(Path(path).read_text())` returning a `dict`. Every `slice.yaml` write site (`init_new_slice`, `close_slice`, `_abort_slice`, B14's RE_DISPATCH persist) MUST use `yaml.safe_dump(state, default_flow_style=False, sort_keys=False)`. A brief containing `"`, `\`, `\n`, `:`, or `#` MUST round-trip byte-for-byte through one write→read cycle.
- **B6 — cluster parsing.** `_parse_clusters(text)` MUST be replaced with `yaml.safe_load(text)` plus an explicit schema check: top-level value is a list of dicts each with `name: str` and `files: list[str]`. Schema violation raises `ValueError` with a message naming the offending cluster index. Comments, indentation variance, and quoted paths containing `:` MUST parse correctly.
- **B7 — JSON-list envelope encoding.** `dispatch_phase_3` MUST set `AGENT_ENVELOPE = json.dumps(cluster["files"])` (a JSON array, e.g. `'["scripts/foo.py","tests/bar.py"]'`). `checks/role_guard.py::_envelope_patterns(raw)` MUST parse via `json.loads(raw)` returning a `list[str]`; on `JSONDecodeError`, fall back to the legacy `:`-split path with one stderr warning (back-compat for any external invocation that still uses `:`). Patterns containing `:` (Windows-style paths, anchors) MUST survive round-trip.

**Phase 3 robustness**

- **B16 — empty-cluster guard.** `dispatch_phase_3` MUST treat `clusters == []` AND every `cluster["files"] == []` as the "implicit cluster" case. Implicit-cluster envelope MUST default to the slice's intent-envelope (read from `slice.yaml.envelope` if present; else from `intent.md`'s YAML envelope frontmatter via PyYAML). If the intent envelope is also empty, `dispatch_phase_3` MUST return `{status: "FAILED", summary: "phase-3 empty envelope: no clusters declared and intent envelope is empty"}` without dispatching any agent. A single stderr warning `orchestrator: phase-3 falling back to intent envelope (no clusters declared)` is emitted on the implicit-cluster path.
- **B2 — per-cluster log capture.** `dispatch_phase_3` MUST write each cluster's stdout+stderr+result-dict to `.claude/orchestrator-debug/{slice-id-slug}-phase-3-cluster-{cluster-name}-{timestamp}.log` regardless of whether the orchestrator's return is determined by an earlier RAISE_ISSUE/FAILED. The first RAISE_ISSUE still wins (return order preserved); the first FAILED still wins after RAISE_ISSUE; OK still wins last — but no peer cluster log is dropped.
- **B8 — FAILED classification + exponential backoff.** When a phase agent returns `status: FAILED`, the orchestrator MUST classify:
  - **transient** — child returncode in `{124}`, OR child stderr contains any of `rate limit`, `overloaded`, `429`, `503` (case-insensitive). Retry up to `int(os.environ.get("CAIRN_FAILED_TRANSIENT_MAX_RETRIES", "3"))` times with exponential backoff `time.sleep(1 * 4**attempt)` (1s, 4s, 16s).
  - **malformed** — `_parse_structured_tail` returned `None`. Retry once.
  - **logic** — agent self-reported FAILED with parseable tail. Retry once (preserves existing one-shot behavior).
  - Each retry attempt is logged to the failure log with `{attempt: N, classification: transient|malformed|logic, backoff_s: <s>}`. After exhausting retries, escalate per existing two-failure rule.

### Boundary

Out of scope (deferred to Slice 3 unless noted):

- **E1** worktree `.claude/current-slice/.lock` (Slice 3).
- **E2** PID-scoped role_guard activation (Slice 3).
- **D1** `.claude/orchestrator-debug/index.jsonl` indexed failure log (Slice 3 — distinct from B2's per-cluster log).
- **D3** `.claude/current-slice/orchestrator-result.json` structured exit (Slice 3).
- Parallel-worktree dogfood integration test (Slice 3).
- Any change to phase-1/2/3/4 or issue-triager agent prompts in `.claude/agents/`.
- Any change to `.claude/settings.json` hook registration.
- Live-stderr tee pump and debug-log filename rename — Slice 1 scope, already shipped.
- Path Y / Path C agent-return-with-artifacts contract redesign — tracked separately; Slice 1's Path X decision (`bypassPermissions`) is empirically gapped against the hardcoded `.claude/**` sensitive-file gate, so Path C is required for fleet-coordinator-class use cases. Not this slice.
- Non-`slice_orchestrator.py` / `role_guard.py` source files outside the test envelope.
- Documentation/ADR edits beyond updating `.claude/features/compression.yaml` slice-list entry.

### Verification

- `tests/unit/test_close_slice_invocation.py`: stub `dispatch_phase_agent` returning `OK` for all four phases; assert `run_phase_loop` exits 0, `slice.yaml` has `status: complete` + `current_phase: 4`, `.claude/handoff.md` exists with the four phase-handoff bodies joined by `\n---\n`, and one git commit named `slice: complete` is created.
- `tests/unit/test_malformed_slice_yaml.py`: write `slice.yaml` containing `id: [unterminated`; assert `_current_phase()` raises `SystemExit` with code `1` and stderr matches `orchestrator: malformed slice.yaml`.
- `tests/unit/test_signal_handler.py`: spawn the orchestrator as a subprocess running a sleep-only stub agent; send SIGTERM; assert exit code `143`, child PID no longer alive within `CAIRN_SHUTDOWN_GRACE_S + 1` seconds, and `slice.yaml` is well-formed YAML post-shutdown.
- `tests/unit/test_redispatch_persistence.py`: stub Phase 2 to return RAISE_ISSUE, triager to return `RE_DISPATCH target_phase=1`; before `phase = 1` continues, assert `slice.yaml.current_phase == 1` is committed and a commit message matching `slice: re-dispatch phase 2 → phase 1` exists.
- `tests/unit/test_redispatch_cap.py`: simulate two RE_DISPATCHes from Phase 2; assert second triager call is NOT made, orchestrator exits `1`, stderr matches `re-dispatched twice`.
- `tests/unit/test_git_helper_check.py`: monkey-patch `subprocess.run` to return `returncode=1, stderr="permission denied"` for any `git commit`; assert `_git` raises `CalledProcessError` whose message contains `permission denied`, and `commit_phase_handoff` propagates that exception (does NOT swallow).
- `tests/unit/test_post_timeout_reconcile.py`: stub `_run_with_live_stderr` to raise `TimeoutExpired` after a real git commit by the child; assert failure log JSON contains `partial_commit`, `pre_dispatch_head`, and `timeout_s` keys with non-empty SHA values.
- `tests/unit/test_yaml_brief_round_trip.py`: for each brief in `['quote"in', 'colon: here', 'back\\slash', 'newline\nhere', 'hash#here']`, call `init_new_slice(brief)` (with stubbed dispatch_phase_agent), then `read_slice_state(SLICE_YAML)`, assert `state["brief"] == brief` byte-for-byte.
- `tests/unit/test_yaml_clusters_schema.py`: feed `_parse_clusters` (a) a well-formed two-cluster doc with comments and indentation variance — assert two clusters returned with correct files; (b) a list-of-strings instead of list-of-dicts — assert `ValueError` mentioning index.
- `tests/unit/test_role_guard_envelope_json.py`: set `AGENT_ROLE=phase-3-implementer`, `AGENT_ENVELOPE='["scripts/a:b.py","tests/c.py"]'`; pipe `{"tool_name":"Write","tool_input":{"file_path":"scripts/a:b.py"}}` to `role_guard.main`; assert exit `0`. Repeat with legacy `AGENT_ENVELOPE='scripts/a.py:tests/b.py'`; assert exit `0` and one stderr warning line about legacy format.
- `tests/unit/test_phase_3_empty_cluster_guard.py`: `CLUSTERS_YAML` absent, intent envelope = `["scripts/x.py"]`; assert one implicit-cluster dispatch is made with `AGENT_ENVELOPE` matching the intent envelope. Repeat with empty intent envelope; assert FAILED return with the expected summary, no agent dispatch.
- `tests/unit/test_phase_3_per_cluster_logs.py`: three stub clusters where cluster #1 returns OK, #2 returns FAILED, #3 returns OK; assert `dispatch_phase_3` returns the FAILED dict AND all three `.claude/orchestrator-debug/*-phase-3-cluster-*.log` files exist on disk.
- `tests/unit/test_failed_classification_backoff.py`: stub agent to return FAILED with stderr `"rate limit exceeded"`; assert exactly 3 retries fire, total wall time is within `[21, 30]` seconds (mocked `time.sleep`), and the failure log records each attempt's classification.
- `uv run pytest` is GREEN end-to-end (regression check that no Slice 1 test broke).

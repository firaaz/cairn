---
slice: compression/slice-1-foundation
date: 2026-04-20
phase: 1-intent
invariants-touched: [INV-003]
adrs-referenced:
  - compression-infrastructure-bootstrap
  - phase-lock-and-role-declaration
  - cliff-failure-mode-and-v1-defenses
adrs-created: []
envelope:
  - "scripts/slice_orchestrator.py"
  - "checks/role_guard.py"
  - ".claude/settings.json"
  - "tests/unit/test_dispatch_contract_separation.py"
  - "tests/unit/test_multiline_json_tail.py"
  - "tests/unit/test_role_guard_wired.py"
  - "tests/unit/test_orchestrator_live_stderr.py"
  - "tests/integration/test_compressed_slice_end_to_end.py"
  - "docs/plans/2026-04-20-a1-spike-results.md"
  - ".claude/agents/phase-1-writer.md"
  - ".claude/agents/phase-2-skeptic.md"
  - ".claude/agents/phase-3-implementer.md"
  - ".claude/agents/phase-4-integrator.md"
  - ".claude/agents/issue-triager.md"
out-of-scope:
  - "B2..B16 state-machine and serialization bugs (Slice 2)"
  - "PyYAML adoption and yaml.safe_load/dump migration (Slice 2)"
  - "Worktree lockfile, role-guard PID scope (Slice 3 - E1/E2)"
  - "orchestrator-result.json structured-exit contract (Slice 3)"
  - "Indexed debug-log jsonl (Slice 3 - D1)"
  - "Fleet coordinator integration (Feature 6)"
  - "Additional agent roles; phase-3 split by change-type"
  - "Windows portability; Rust port"
---

### What and Why

The compression pipeline has never demonstrated its load-bearing claim: one `/start-slice` invocation dispatches four role-scoped phase agents end-to-end with zero human intervention between phases. Every closed slice since infrastructure shipped has required human backstopping because four distinct `.claude/current-slice/**` write paths trip the harness sensitive-file gate inside nested `claude -p` subagent sessions. This slice closes the gap: empirically resolve the permissions block (A1), wire the authorized inner gate (A3), separate dispatch so triager returns are no longer misread as phase failures (B1, B17), make the tail parser tolerate pretty-printed JSON (B5), and surface live child stderr to the operator (D3 brought forward). Foundation for Slices 2 and 3; precondition for fleet-coordinator consumption.

### Boundary

Out: every state-machine / serialization bug (B2-B16), PyYAML adoption, multi-worktree locking, PID-scoped role-guard, orchestrator-result.json, indexed failure-log jsonl, additional agent roles, Windows/Rust portability. Bugs B10/B11/B12/B13/B14/B15 remain latent until Slice 2.

### Specification Detail

**A1 resolution (spike-driven, decided in Phase 2).** Three spikes, each one shell command driving phase-2-skeptic to write `.claude/current-slice/validation/approach.md`:
- Spike 1: `additionalDirectories` in a project-level `settings.json` overlay.
- Spike 2: `--permission-mode bypassPermissions` on the inner `claude -p` call.
- Spike 3: Claude Agent SDK Python invocation instead of `claude -p` CLI.

Persist results to `docs/plans/2026-04-20-a1-spike-results.md`. **Path X** (any spike passes): the current agent-return contract stands; dispatch cleanup proceeds within this slice envelope as-is. **Path Y** (all three fail): agents return a structured object on stdout (status, artifacts map of path-to-content, summary) and the orchestrator performs every `.claude/**` `Path.write_text` in-process. Path Y expands this slice envelope to the five `.claude/agents/*.md` prompts and additional dispatch code paths but does NOT change exit criteria.

**A3 - role_guard.py wiring.** `.claude/settings.json` registers a `PreToolUse` hook with matcher `Write|Edit|MultiEdit|NotebookEdit` whose command invokes `uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py`. The hook MUST no-op when `AGENT_ROLE` is unset (per compression-infrastructure-bootstrap D1, already honored at the hook source).

**B1 / B17 - dispatch contract split.** Replace the single `dispatch_agent(role, inputs) -> dict` with a typed pair:
- `dispatch_phase_agent(role, inputs, ...) -> PhaseResult` validating status in (OK, RAISE_ISSUE, FAILED) plus commit_hash and summary fields.
- `dispatch_triager(issue_hash, phase, slice_id) -> TriagerResult` validating action in (ESCALATE_TO_USER, RE_DISPATCH, ABORT) plus target_phase, amendment, rationale fields.

Shared internals (subprocess invocation, tail parsing, failure-log writer) stay factored. A triager return with action RE_DISPATCH and no status field MUST NOT write a noise failure log - that is the regression this split prevents.

**B5 - multi-line JSON tail.** `_parse_structured_tail` scans backward from the child's last line: on a closing brace it walks upward until braces balance, then attempts `json.loads` on the joined span. The single-line fallback is preserved. Pretty-printed JSON tails (newlines inside the object) MUST parse successfully.

**D3 - live stderr.** Every dispatched `claude -p` subprocess uses `subprocess.Popen(stderr=PIPE, stdout=PIPE)` with a tee-pump thread that forwards each child stderr line to orchestrator stderr prefixed `[phase-N-role|slice-id]` within 500 ms of emission, while buffering the full stream for failure-log capture. `CAIRN_ORCHESTRATOR_DEBUG` (default on) gates verbosity.

**Debug log filename.** Emit `.claude/orchestrator-debug/<slice-id-slug>-phase-<n>-<role>-<timestamp>.log` where `slice-id-slug` is the full slice id with `/` replaced by `-` and `timestamp` is `YYYYMMDDTHHMMSSZ`.

### Verification

1. **Spike log present and decisive.** `docs/plans/2026-04-20-a1-spike-results.md` lists all three spikes with PASS/FAIL and names the chosen path. Phase 2 attaches the chosen path to intent via an amendment note before writing any test.
2. **role_guard hook registered.** `tests/unit/test_role_guard_wired.py` parses `.claude/settings.json`, asserts a `PreToolUse` entry with matcher `Write|Edit|MultiEdit|NotebookEdit` whose command resolves to `checks/role_guard.py`, and asserts the hook no-ops for a sample tool-call JSON when `AGENT_ROLE` is unset.
3. **Dispatch contract separation.** `tests/unit/test_dispatch_contract_separation.py` calls `dispatch_triager` with a mocked subprocess whose stdout tail is a single-line triager JSON (action RE_DISPATCH, target_phase 2); asserts the return validates, asserts no failure log is written, and asserts a `dispatch_phase_agent` call rejects a tail missing the status field with a clear error.
4. **Multi-line JSON tail.** `tests/unit/test_multiline_json_tail.py` feeds a trailing pretty-printed JSON object (newlines inside braces) to `_parse_structured_tail`; asserts the dict parses to the expected shape. Single-line fallback case also asserted.
5. **Live stderr streaming.** `tests/unit/test_orchestrator_live_stderr.py` dispatches a stub subprocess that emits three stderr lines at 100 ms intervals; asserts each line reaches the orchestrator stderr FD within 500 ms of emission, prefixed `[phase-N-role|slice-id]`, and that the full stream is also captured in the per-phase debug log at the renamed path.
6. **Autonomous end-to-end.** `tests/integration/test_compressed_slice_end_to_end.py` invokes the orchestrator on a trivial slice spec in a throwaway worktree, asserts exit code 0, asserts all four phases produced commits on the branch, asserts `.claude/current-slice/integration/sweep-notes.md` exists, asserts `slice.yaml.status == complete`, and asserts zero permission prompts were emitted to stderr.

Slice 1 passes when (6) is GREEN and (1)-(5) are GREEN.

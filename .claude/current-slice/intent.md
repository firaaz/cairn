---
slice: compression/infrastructure
date: 2026-04-19
phase: 1-intent
invariants-touched: [INV-003]
adrs-referenced: [compression-infrastructure-bootstrap, phase-lock-and-role-declaration, parallelism-v1]
v1-defense-alignment: D3
envelope:
  - "scripts/slice_orchestrator.py"
  - "checks/role_guard.py"
  - ".claude/agents/phase-1-writer.md"
  - ".claude/agents/phase-2-skeptic.md"
  - ".claude/agents/phase-3-implementer.md"
  - ".claude/agents/phase-4-integrator.md"
  - ".claude/agents/issue-triager.md"
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice-legacy.md"
  - "commands/claude-code/settings.json"
  - ".claude/platform-probe.md"
  - "tests/unit/test_role_guard.py"
  - "tests/unit/test_slice_orchestrator_state_machine.py"
  - "tests/unit/test_slice_id_derivation.py"
  - "docs/operational-reference.md"
out-of-scope:
  - "Part 0 ADR (P1–P6 + D1/D2/D3) — Slice B's scope; Slice A deliberately does NOT pre-ratify role-discipline principles beyond the role_guard.py authorization already granted by compression-infrastructure-bootstrap."
  - "Additional role-keyed hooks (role-keyed Read gating, role-keyed Bash gating, role-keyed subagent-dispatch filters). compression-infrastructure-bootstrap scopes authorization to write-path only."
  - "Distillation agents (Part 1 efficiency-program scope)."
  - "Thin-dispatcher refactors of /catchup, /handoff, /integration-sweep — future slices only."
  - "`commit_handoff.sh` obsolescence decision — deferred."
  - "`.claude/slice-candidates/` primitive — deferred per design §11."
  - "Fleet-coordinator F6 worker integration."
  - "Windsurf port, Rust migration."
  - "Any edit to `compression-infrastructure-bootstrap` or any other existing ADR body (append-only substrate)."

## What and Why

Ship the compression substrate — a Python state-machine orchestrator that dispatches role-scoped Claude agents per phase via `claude -p --agent <role>`, plus a PreToolUse hook (`checks/role_guard.py`) that enforces per-role write-path restrictions keyed on the `AGENT_ROLE` env var — so that subsequent slices can run under compressed execution and Slice B (Part 0 ADR) can dogfood the path in a fresh session rather than serially. This slice is the *infrastructure* half of the Slice-A / Slice-B coupling scoped by `compression-infrastructure-bootstrap`; Slice B is the dogfood and the Part-0 ratification.

The slice closes under the **existing serial `/start-slice` protocol** — not under its own compressed dispatch. `AGENT_ROLE` is unset during Slice A's own phases, so `role_guard.py` is a no-op on this slice (chicken-and-egg resolved per bootstrap ADR Risk Register). The orchestrator and role agents are *shipped*, not *used* by this slice.

## Specification Detail

### 1. `checks/role_guard.py` (new; PreToolUse hook)

Reads tool-call JSON from stdin. Reads `AGENT_ROLE` + optional `AGENT_ENVELOPE` from environment. Behavior:

- `AGENT_ROLE` unset → exit 0 (no-op). Non-compressed slices unaffected.
- Tool not in `{Write, Edit, MultiEdit, NotebookEdit}` → exit 0.
- `tool_input.file_path` empty → exit 0.
- `AGENT_ROLE == phase-3-implementer` → allow iff path matches one of the colon-separated regex patterns in `AGENT_ENVELOPE`; empty `AGENT_ENVELOPE` denies. Deny writes to stderr with the path.
- `AGENT_ROLE ∈ {phase-1-writer, phase-2-skeptic, phase-4-integrator}` → allow iff path matches one of the role's static regex patterns below; else deny with the role's `deny_message`.
- Unknown role → deny with stderr `"role_guard: unknown role '<role>'"`.

Static `ROLE_POLICIES` table (authoritative at this slice; Slice B's Part 0 ADR ratifies/adjusts):

| Role | Allow patterns (regex, anchored at `^`) |
|---|---|
| `phase-1-writer` | `^\.claude/current-slice/intent\.md$`, `^\.claude/current-slice/slice\.yaml$`, `^\.claude/features/[^/]+\.yaml$` |
| `phase-2-skeptic` | `^tests/`, `^\.claude/current-slice/validation/` |
| `phase-3-implementer` | envelope-driven (see above) |
| `phase-4-integrator` | `^\.claude/current-slice/integration/`, `^\.claude/current-slice/handoff-phase-\d+\.md$`, `^\.claude/handoff\.md$`, `^\.claude/current-slice/slice\.yaml$`, `^\.claude/sweep\.yaml$` |

Exit codes: `0` = allow, `1` = deny (with stderr diagnostic), `2` = malformed stdin. The hook is registered in `commands/claude-code/settings.json` under `PreToolUse` with matcher `"Write|Edit|MultiEdit|NotebookEdit"` and command `"python3 $CLAUDE_PROJECT_DIR/checks/role_guard.py"`.

### 2. `scripts/slice_orchestrator.py` (new; Python 3, stdlib only)

Entry point: `python3 scripts/slice_orchestrator.py --brief "<text>" | --resume | --legacy`. Mutually-exclusive; one required.

Public functions (named, testable):

- `read_slice_state(path) -> SliceState` — line-parses `slice.yaml` (no third-party yaml dep). Returns dict with at least `id`, `name`, `status`, `current_phase`. Integer `current_phase` coerced.
- `dispatch_agent(role, inputs, envelope=None, timeout_hard=None) -> AgentReturn` — invokes `subprocess.run(["claude", "-p", "--agent", role, json.dumps(inputs)], …)` with `env = os.environ.copy() | {AGENT_ROLE: role, AGENT_ENVELOPE: envelope}`. Parses the last JSON-object line of stdout. On timeout or missing structured tail, returns `{"status": "FAILED", "summary": "<diagnostic>"}`. Hard timeout default from `CAIRN_PHASE_<N>_TIMEOUT_HARD` env var (fallback `1800`).
- `dispatch_phase_3(slice_id) -> AgentReturn` — reads `.claude/current-slice/validation/coupling-clusters.yaml` (line-parser; absent → single implicit cluster with empty files). Fans out one `dispatch_agent(role="phase-3-implementer", …)` per cluster via `concurrent.futures.ThreadPoolExecutor(max_workers=min(len(clusters), 8))`. Reconciles: any `RAISE_ISSUE` → propagate; else any `FAILED` → propagate; else synthesize `{"status": "OK", "commit_hash": ",".join(hashes), "summary": "; ".join(summaries)}`.
- `run_phase_loop(max_phase=4) -> int` — phase-by-phase state machine. Phase 3 routes via `dispatch_phase_3`; other phases via `dispatch_agent(ROLE_FOR_PHASE[phase], …)`. Returns `0` on success, non-zero on escalation.
- `commit_phase_handoff(phase, summary, commit_hash)` — writes `.claude/current-slice/handoff-phase-<N>.md` with YAML frontmatter (`phase`, `commit`) and body summary; `git add` + `git commit -m "handoff: phase <N> complete"`.
- `init_new_slice(brief) -> SliceState` — dispatches `phase-1-writer` with `{"brief": brief, "ask": "propose_slice_id"}`. Validates `proposed_slice_id` against `^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$`; malformed → `SystemExit`. Creates `.claude/current-slice/slice.yaml` with `status: in-progress` and `current_phase: 1`, then commits.
- `close_slice(state)` — sets `status: complete`, assembles `.claude/handoff.md` from `handoff-phase-<1..4>.md` + `integration/sweep-notes.md`, commits.
- `legacy_start_slice() -> int` — prints a message telling the operator to follow `start-slice-legacy.md` manually; returns 0. Does *not* execute prose protocol.

Return-envelope contract (structured return, last line of agent stdout parses as JSON):

```json
{"status": "OK|RAISE_ISSUE|FAILED", "commit_hash": "<sha>", "summary": "<=100 words", "proposed_slice_id": "<ns>/<topic>"}
```

Routing table in `run_phase_loop`:

- `OK` → commit handoff, advance phase.
- `FAILED` → retry once (same phase, same role); second `FAILED` → return non-zero escalation.
- `RAISE_ISSUE` → dispatch `issue-triager` with `{issue_commit_hash, current_phase, slice_id}`. Triager returns `{"action": "ESCALATE_TO_USER|RE_DISPATCH|ABORT", "target_phase": <int>, "amendment": "<short>", "rationale": "<=50w"}`. `ESCALATE_TO_USER` writes `.claude/handoff.md` partial-close + returns non-zero. `RE_DISPATCH` sets `phase = max(target_phase, 1)` and continues. `ABORT` rewrites `slice.yaml` `status: aborted`, commits, returns non-zero.
- Unknown `status` → print diagnostic, return non-zero.

Timeout env-var knobs (documented in `docs/operational-reference.md`): `CAIRN_PHASE_1_TIMEOUT_HARD`, `CAIRN_PHASE_2_TIMEOUT_HARD`, `CAIRN_PHASE_3_TIMEOUT_HARD`, `CAIRN_PHASE_4_TIMEOUT_HARD`. Defaults: `1800` (seconds). No hardcoded values outside these defaults (CLAUDE.md "No hardcoded timeouts/sizes in consumer-facing scripts").

### 3. Agent definitions (`.claude/agents/*.md` — five files)

Each file: YAML frontmatter with `name`, `description`, `tools`; body = role system prompt + structured-return contract. `tools` is the outer gate (Claude Code's allowed-tools mechanism); `role_guard.py` is the inner gate (write-path).

- `phase-1-writer.md` — `tools: [Read, Write, Edit, Bash, Grep, Glob]`; description declares forbidden-source-read rule (greenfield) or public-interface-only (modification).
- `phase-2-skeptic.md` — same tools; description declares test-only authoring + approach.md + coupling-clusters.yaml authoring.
- `phase-3-implementer.md` — same tools; description declares envelope-bound source authoring, no test modification.
- `phase-4-integrator.md` — same tools; body mandates "you MUST write `integration/sweep-notes.md` before returning OK" (F3 audit-finding prevention).
- `issue-triager.md` — `tools: [Read, Grep, Glob]` (read-only); body narrowly scopes its decision space to `{ESCALATE_TO_USER, RE_DISPATCH, ABORT}`.

System-prompt content is sourced from `docs/plans/2026-04-18-efficiency-program/05-part-3-phase-role-agents.md` where available, extended with the compression-slice's structured-return contract on every agent's last instruction.

### 4. Thin `/start-slice` refactor

- `commands/claude-code/start-slice.md` → rewritten to a thin dispatcher (~30 lines). Detects aborted/in-progress slice (propose resume), reads brief from args, falls back to handoff "Next" or prompt; invokes `python3 scripts/slice_orchestrator.py --brief|--resume`. `--legacy` flag (or `CAIRN_LEGACY_START_SLICE=1`) defers to `start-slice-legacy.md`.
- `commands/claude-code/start-slice-legacy.md` → archive of the current `start-slice.md` + `start-slice.full.md` content, retained as the fallback protocol until ≥5 clean compressed slices have landed (per compression design §10).

### 5. Pre-Task 0 platform probe

Before any other task: execute the design's §Pre-Task 0 probe — verify `claude -p --agent <name>` is the correct invocation (try `--subagent` / `--role` if not), verify `tools` frontmatter mechanically enforces via a write-denial test. Commit findings to `.claude/platform-probe.md`. **If the probe reveals the flag name or enforcement semantics differ, PAUSE the slice and escalate before proceeding** — downstream task invocations depend on the discovered interface.

### 6. `docs/operational-reference.md` update

Add a short subsection documenting the four `CAIRN_PHASE_<N>_TIMEOUT_HARD` env vars and the `CAIRN_LEGACY_START_SLICE` toggle. Append to existing env-var table or create one if absent.

## Boundary (out of scope)

Enumerated in the YAML envelope above. Explicit callouts:

- **No Part 0 ADR content** is authored by this slice. Any prose that attempts to articulate P1–P6 or formalize D1/D2/D3 at the compression-feature level is out of scope; `compression-infrastructure-bootstrap`'s narrow authorization is the only ADR-level paper trail this slice leans on.
- **No existing-ADR body edits.** If Phase 3 discovers a need to amend `compression-infrastructure-bootstrap` or any adjacent ADR (including to correct a declared-output-path table row), the slice escalates — `reversibility-guard.sh` blocks the edit anyway, and prose-level ADR amendments are not Slice-A scope.
- **No changes to `checks/scope-guard.sh`, `checks/reversibility-guard.sh`, `checks/reality-check.sh`.** These remain envelope-keyed, append-only, and lint/format gates respectively — orthogonal to `role_guard.py` per INV-003's "scope mechanism-specific" clause.
- **No changes to `/catchup`, `/handoff`, `/integration-sweep`.** Thin-dispatcher refactors of these are not infrastructure-scope; they are later incremental slices.
- **No new invariants.** INV-003's wording already reflects `compression-infrastructure-bootstrap`'s narrow exception (see `docs/ARCHITECTURE.md:31`). No architecture edits beyond the operational-reference env-var documentation.

## Verification

All checks must pass at Phase 4. Each is concrete, evidence-backed.

### V1 — `checks/role_guard.py` correctness

Run `uv run pytest tests/unit/test_role_guard.py -v`. Expected: ≥7 tests pass covering:

1. `AGENT_ROLE` unset → exit 0 (no-op).
2. `phase-1-writer` + `Write` to `.claude/current-slice/intent.md` → exit 0.
3. `phase-1-writer` + `Write` to `src/main.py` → exit 1 with `"phase-1-writer"` in stderr.
4. `phase-2-skeptic` + `Write` to `tests/unit/test_foo.py` → exit 0.
5. `phase-2-skeptic` + `Edit` on `.claude/current-slice/intent.md` → exit 1 (F1 prevention).
6. `phase-3-implementer` + `Edit` on `.claude/current-slice/intent.md` → exit 1 with `"intent"` in stderr (primary F1 prevention).
7. `phase-4-integrator` + `Write` to `.claude/current-slice/integration/sweep-notes.md` → exit 0 (F3 support).
8. Unknown role → exit 1 with `"unknown role"` in stderr.

### V2 — Orchestrator state-machine correctness

Run `uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v`. Expected: tests pass for:

1. `--help` returns 0 with `--brief` or `--resume` in stdout.
2. `read_slice_state` parses a minimal `slice.yaml` correctly (id/current_phase/status fields).
3. `dispatch_agent` parses a structured-return-final-line stdout; returns dict with `status`, `commit_hash`, etc.
4. `dispatch_agent` on malformed stdout → `{"status": "FAILED", "summary": "…malformed…"}`.
5. `run_phase_loop` with mocked `OK` dispatch → advances phase, calls `commit_phase_handoff`.
6. `run_phase_loop` with mocked `FAILED` dispatch → retries once; second `FAILED` → returns non-zero.
7. `run_phase_loop` with mocked `RAISE_ISSUE` → dispatches `issue-triager` once; `ESCALATE_TO_USER` → returns non-zero.
8. `dispatch_phase_3` with 3-cluster `coupling-clusters.yaml` → calls `dispatch_agent` 3× with `role="phase-3-implementer"`.

### V3 — Slice-id regex

Run `uv run pytest tests/unit/test_slice_id_derivation.py -v`. Expected: valid ids (`compression/infrastructure`, `identifier-scheme/doc-sweep`, `fleet-coordinator/push-protocol`) match; invalid ids (caps, missing segment, spaces) do not.

### V4 — Adversarial hook test (executed by hand at Phase 4)

```bash
AGENT_ROLE=phase-3-implementer AGENT_ENVELOPE="^scripts/foo\.py$" python3 checks/role_guard.py <<< '{"tool_name":"Edit","tool_input":{"file_path":".claude/current-slice/intent.md"}}'
echo "exit: $?"
```

Expected: `exit: 1` with stderr.

### V5 — Full test suite regression-free

Run `uv run pytest`. Expected: all pre-existing tests still pass (no regressions from hook registration or skill refactor).

### V6 — Architecture validator green

Run `uv run python scripts/validate_architecture.py`. Expected: exit 0. All 7 invariant assertions pass; ADR corpus validates; `compression-infrastructure-bootstrap` is recognized.

### V7 — INV-003 evidence table (Phase 4 `integration/sweep-notes.md`)

| INV | Statement | Status | Evidence |
|---|---|---|---|
| INV-003 | Roles instructed not hook-enforced, narrow exception for role-keyed write-path via `checks/role_guard.py` | PASS | `checks/role_guard.py` is the only new role-keyed hook; enforces `Write/Edit/MultiEdit/NotebookEdit` only (no `Read`, no `Bash`, no dispatch filter) — file grep confirms. `docs/ARCHITECTURE.md:31` already carries the narrow-exception wording. |

### V8 — Pre-Task 0 probe outcome

`.claude/platform-probe.md` committed; documents whether `claude -p --agent <name>` works as assumed and whether `tools:` frontmatter mechanically denies disallowed writes. If either probe failed and the slice proceeded anyway, the probe doc documents the adapted invocation path.

### V9 — Hook registration syntactic validity

```bash
python3 -c "import json; json.load(open('commands/claude-code/settings.json'))"
```

Expected: silent (valid JSON). PreToolUse array contains the `role_guard.py` entry.

### V10 — Legacy escape-hatch preserved

Inspect `commands/claude-code/start-slice.md` — contains reference to `--legacy` flag and `CAIRN_LEGACY_START_SLICE` env var. `start-slice-legacy.md` exists and mirrors the pre-refactor protocol content.

### V11 — Audit-finding F1/F3/F4 prevention mechanisms are *present* (even if not exercised until Slice B)

- F1 (intent.md post-Phase-2 edits): `role_guard.py` denies `phase-2-skeptic`/`phase-3-implementer` edits to `intent.md`. Covered by V1 tests 5 + 6.
- F3 (sweep-notes.md missing at close): `phase-4-integrator.md` system prompt mandates sweep-notes authorship before returning `OK`; structured-return protocol makes that the only path to slice close.
- F4 (handoff-phase-<N>.md missing): `commit_phase_handoff` is called on every `OK`-returning phase; unconditional by construction.

F5 (handoff claims not traceable to git) is an emergent property of the above three — every claim in final `handoff.md` is assembled from committed `handoff-phase-<N>.md` files, each of which carries its source commit hash in frontmatter. No file-read test proves this in Slice A; Slice B's dogfood is the empirical check.

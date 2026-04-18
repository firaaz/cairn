---
slice: compression/infrastructure
phase: 2-validation
date: 2026-04-19
role: Skeptic
---

# Approach — Phase 2 validation of compression/infrastructure

Phase 2 output for Phase 3 consumption. Records (1) ambiguities enumerated from
`intent.md`, (2) how each was resolved, and (3) what the RED tests under `tests/unit/` lock in.

## Ambiguity resolutions

Each item is a spec gap in `intent.md` that Phase 2 must settle before tests can be
written. Disposition: **Settled** (spec pins it; test asserts), **Judgment**
(Skeptic test-design call within ADR scope), **Escalated** (architectural —
decided by user turn-by-turn during this phase).

### A1. Structured-return JSON parser rules — *Judgment*

`intent.md:80-84` specifies the JSON schema but not how `dispatch_agent` parses it
from stdout. Parser contract locked here:

- Walk stdout lines **in reverse**; first line that parses under `json.loads` and
  is a JSON object (`dict`) is the structured return.
- Leading/trailing whitespace on the line is stripped before parsing.
- Blank / non-JSON lines above and below are ignored.
- No structured return found → `{"status": "FAILED", "summary": "malformed structured return"}`.

Rationale: "last JSON-object line" is unambiguous under reverse-walk; embedded
`}` in strings is handled by `json.loads` natively.

### A2. `coupling-clusters.yaml` schema — *Escalated (user approved)*

`intent.md:73` specifies the *absent-file* fallback but not the schema when present.
**User-approved schema:**

```yaml
clusters:
  - name: auth-core
    files: ["^src/auth/", "^tests/auth/"]
  - name: worker
    files: ["^src/workers/"]
```

- Each cluster has a `name` (string) and `files` (list of regex strings).
- Per-cluster `AGENT_ENVELOPE` = `":".join(cluster.files)` (colon-separated, matching
  `role_guard.py`'s envelope regex-list convention from `intent.md:50`).
- Absent file → single implicit cluster `{"name": "default", "files": []}` — one
  `dispatch_agent` call with `envelope=""`. Because `AGENT_ENVELOPE=""` denies
  all writes for `phase-3-implementer` (per intent.md:50), the absent-file case
  is only usable by slices with no envelope-gated writes (no-op Phase 3).

Parser is line-based, consistent with `read_slice_state` (`intent.md:71`). Phase 3
decides stdlib-only line-parser vs `pyyaml` (dependency already in
`pyproject.toml`). Phase 2 tests use a fixture format Phase 3 must parse; exact
parser shape is an implementation detail.

### A3. Platform-probe flag shape — *Deferred to Phase 3*

`intent.md:112-114` explicitly scopes this to Phase 3's Pre-Task 0 probe, with a
PAUSE-and-escalate gate if the probe falsifies `claude -p --agent <name>`.
Phase 2 tests assume the spec'd invocation; Phase 3's probe outcome may amend.
No Phase 2 test action.

### A4. `AGENT_ENVELOPE` empty-string vs unset — *Settled*

`intent.md:50` says "empty `AGENT_ENVELOPE` denies" for `phase-3-implementer`.
Unset env var is treated identically: `os.environ.get("AGENT_ENVELOPE", "")`
yields `""` for both cases. Test covers both — both deny.

### A5. Unknown-status exit code — *Judgment*

`intent.md:91` specifies "print diagnostic, return non-zero" without a specific
code. Locked: `run_phase_loop` returns `2` for unknown-status (distinct from `1`
= retry-exhausted `FAILED` escalation, `0` = success). Tests assert `!= 0`, not
a specific value — allows Phase 3 to choose any non-zero without breaking tests.

### A6. `RAISE_ISSUE` `target_phase` bounds — *Escalated (user chose B3 + amendment)*

`intent.md:90` reads `phase = max(target_phase, 1)` — a floor clamp only. User-
approved strict validation (both floor and ceiling):

- `target_phase` must be `int` and `∈ {1..max_phase}` (default `max_phase=4`).
- Malformed / out-of-bounds / missing → treat as unknown-status: print diagnostic,
  return non-zero. No silent clamp.
- No retry (issue-triager *is* the escalation path; retrying a hallucinating
  triager compounds the bug).
- **Spec amendment:** the `max(target_phase, 1)` clause in `intent.md:90` is
  superseded by strict validation. Phase 3 implements the amended rule;
  intent.md body itself is append-only and unchanged.

Rationale: `target_phase` has no arithmetic source — it's pure LLM output from
the triager. Silent clamping erases malformed intent; loud failure surfaces
the hallucination to the user.

### A7. `read_slice_state` minimum fields — *Settled*

`intent.md:71` "Returns dict with at least `id`, `name`, `status`, `current_phase`"
— "at least" tolerates extra keys. Tests cover both minimal and extra-keys
fixtures; extras pass through without error.

### A8. Retry-once semantics on `FAILED` — *Settled*

`intent.md:89` "retry once (same phase, same role)" — natural reading is same
invocation: identical `role`, `inputs`, `envelope`, `timeout_hard`, and `env`
passthrough. Tests assert `dispatch_agent` receives the same positional +
keyword args across both invocations.

## Test strategy

Three RED test files under `tests/unit/`, stdlib + pytest only (per
`CLAUDE.md`):

### `test_role_guard.py` — V1 coverage (`intent.md:134-146`)

Subprocess-invokes `checks/role_guard.py` with stdin tool-call JSON and env vars
(`AGENT_ROLE`, `AGENT_ENVELOPE`). Asserts on exit code + stderr substring.
Covers the 8 V1 cases + A4 (unset vs empty envelope) + non-write-tool short-
circuit + empty `file_path` short-circuit + malformed stdin (exit 2).

### `test_slice_orchestrator_state_machine.py` — V2 coverage (`intent.md:148-158`)

Imports `slice_orchestrator` as a module (path wired via `pyproject.toml`).
Monkeypatches `dispatch_agent` at module scope to stub agent returns
per-test. `--help` test is a subprocess invocation. Fixtures in
`tmp_path`; uses `monkeypatch.chdir` to isolate slice-yaml and coupling-
clusters reads. Covers V2 cases 1-8 + A1 parser edges + A5 unknown-status
+ A6 target_phase strict validation + A7 extra-keys tolerance + A8 retry-
same-args.

### `test_slice_id_derivation.py` — V3 coverage (`intent.md:161-162`)

Tests the regex `^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$` via
`slice_orchestrator.is_valid_slice_id(s) -> bool` (assumed exposed).
Valid + invalid fixtures per V3.

## ADR constraints reinforced by tests

- **`compression-infrastructure-bootstrap`** (§authorization): `role_guard.py`
  matcher is `Write|Edit|MultiEdit|NotebookEdit` only. Tests assert `Read`,
  `Bash`, `Grep`, `Glob` with any role → exit 0. No role-keyed gating beyond
  write-path.
- **`phase-lock-and-role-declaration`** (D2): anti-behaviors are *instructed*
  (via agent system prompts), not mechanized beyond write-path. No test asserts
  role-keyed cognition gating (e.g., "Skeptic cannot grep source").
- **`parallelism-v1`** (D3): `dispatch_phase_3` fan-out via
  `ThreadPoolExecutor(max_workers=min(len(clusters), 8))` is legal within-slice
  parallelism. Test asserts 3-cluster fixture → 3 dispatch calls.

## Out-of-scope for Phase 2 tests

- Live `claude -p --agent` invocation (subprocess mocked or stubbed).
- End-to-end slice run (that's Slice B's dogfood).
- `phase-4-integrator` sweep-notes authorship enforcement (agent-system-prompt
  behavior, not hook-enforced — no test can assert prompt fidelity).
- F5 traceability (emergent property, per `intent.md:209`).

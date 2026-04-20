# Compression Pipeline Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. NOTE: This plan is executed as three back-to-back cairn slices via `scripts/slice_orchestrator.py`, not as a linear task list in a single session. Each slice's Phase 3 implementer follows that slice's task breakdown below.

**Goal:** Harden `scripts/slice_orchestrator.py` and `checks/role_guard.py` so a single `/start-slice "<brief>"` completes a four-phase slice autonomously (zero human intervention) and two orchestrators run safely in parallel worktrees.

**Architecture:** Three serial slices. Slice 1 (foundation) resolves A1 sensitive-file gate via empirical spike, wires role_guard, and separates the dispatch return contracts — this is what unblocks autonomous end-to-end. Slices 2 and 3 are executed via the now-working compression pipeline itself (dogfood). Slice 2 sweeps the 14 code bugs and adopts PyYAML; Slice 3 adds worktree-lock, PID-scoped role-guard, structured JSON exit, and parallel-worktree integration test.

**Tech Stack:** Python 3 (`subprocess`, `json`, `fcntl`, `signal`), PyYAML (new dep), pytest, Claude Code subagent dispatch (`claude -p --agent <role>`), Claude Code hooks (`checks/role_guard.py`).

**Design doc:** `docs/plans/2026-04-20-compression-pipeline-hardening-design.md`. Failure-mode taxonomy (A/B/D/E codes) in design §2 — referenced throughout this plan.

---

## Execution model

Each slice below is launched via:

```bash
/start-slice "<slice brief from Slice N 'Brief' subsection below>"
```

The orchestrator dispatches:
- **Phase 1 (phase-1-writer)** — writes `.claude/current-slice/intent.md` + `slice.yaml` from the brief. Output: proposed slice id, envelope, ADRs referenced.
- **Phase 2 (phase-2-skeptic)** — writes `.claude/current-slice/validation/approach.md` + `coupling-clusters.yaml` + the RED test suite in `tests/unit/`.
- **Phase 3 (phase-3-implementer)** — implements to turn the RED suite GREEN. May be fanned out across clusters.
- **Phase 4 (phase-4-integrator)** — runs full pytest + validator, writes `sweep-notes.md`, closes slice.

Commits land at phase boundaries. Within Phase 3 the sub-tasks below are implementer guidance, not commit boundaries — all sub-task code commits as one Phase 3 commit per cluster.

---

## SLICE 1 — Foundation

### 1.0 Brief (for `/start-slice`)

```
Harden the compression pipeline's dispatch layer so one slice runs autonomously end-to-end. Resolve A1 (subagent sensitive-file gate on .claude/current-slice/**) via empirical spike testing three candidate fixes and committing to whichever works. Wire checks/role_guard.py into .claude/settings.json as PreToolUse hook. Separate dispatch_agent into dispatch_phase_agent and dispatch_triager with distinct return contracts. Fix _parse_structured_tail to handle multi-line JSON. Replace subprocess.run capture_output with Popen tee-pump streaming child stderr live to orchestrator stderr with [phase-N-role|slice-id] prefix. Rename debug logs to {slice-id-slug}-phase-{n}-{role}-{timestamp}.log. Integration test: a trivial slice runs four phases via the orchestrator with zero human intervention, exits 0, produces sweep-notes.md. References design doc docs/plans/2026-04-20-compression-pipeline-hardening-design.md §5.
```

### 1.1 Phase 2 — RED test list

Phase-2-skeptic writes these tests (all RED before Phase 3):

- `tests/unit/test_dispatch_contract_separation.py`
  - `test_phase_agent_result_validates_status_field`
  - `test_triager_result_validates_action_field`
  - `test_triager_return_does_not_write_failure_log`
- `tests/unit/test_multiline_json_tail.py`
  - `test_pretty_printed_json_tail_parses`
  - `test_balanced_brace_walk_handles_nested_objects`
  - `test_line_scan_fallback_still_works`
- `tests/unit/test_role_guard_wired.py`
  - `test_settings_json_registers_role_guard_pretooluse`
  - `test_role_guard_hook_fires_on_write_tool_call_when_agent_role_set`
  - `test_role_guard_hook_noop_when_agent_role_unset`
- `tests/unit/test_orchestrator_live_stderr.py`
  - `test_child_stderr_streams_to_orchestrator_stderr`
  - `test_streamed_lines_have_slice_and_role_prefix`
  - `test_debug_log_filename_uses_slice_id_and_phase`
- `tests/integration/test_compressed_slice_end_to_end.py` *(integration — new test directory)*
  - `test_trivial_slice_completes_autonomously`

### 1.2 Phase 3 tasks

Cluster partition proposed for Phase 2 (one phase-3-implementer per cluster):
- Cluster `spike-and-wiring`: Tasks 1.3, 1.4
- Cluster `dispatch-core`: Tasks 1.5, 1.6, 1.7

### Task 1.3: A1 empirical spike + decision

**Files:**
- Create: `docs/plans/2026-04-20-a1-spike-results.md`
- (No orchestrator changes in this task — this task is pure evidence gathering.)

**Step 1: Run the baseline failure**

```bash
# Verify current behavior before proposing fixes.
cd /tmp && mkdir -p cairn-a1-spike && cd cairn-a1-spike
git init -q && git commit -q --allow-empty -m init
mkdir -p .claude/current-slice/validation
AGENT_ROLE=phase-2-skeptic claude -p --agent phase-2-skeptic \
  --permission-mode acceptEdits \
  '{"phase":2,"role":"phase-2-skeptic","slice_id":"spike/a1-baseline","brief":"write .claude/current-slice/validation/approach.md with the text hello"}' 2>&1 | tee /tmp/spike-baseline.log
```

Expected: RAISE_ISSUE with "sensitive file" in stderr.

**Step 2: Spike 1 — additionalDirectories**

```bash
cat > /tmp/spike1-settings.json <<'EOF'
{"permissions": {"allow": ["Write(.claude/current-slice/**)", "Edit(.claude/current-slice/**)"]}, "additionalDirectories": [".claude/current-slice"]}
EOF
AGENT_ROLE=phase-2-skeptic claude -p --agent phase-2-skeptic \
  --permission-mode acceptEdits \
  --settings /tmp/spike1-settings.json \
  '{"phase":2,"role":"phase-2-skeptic","slice_id":"spike/a1-s1","brief":"same task"}' 2>&1 | tee /tmp/spike1.log
```

Record PASS / FAIL + stderr excerpt.

**Step 3: Spike 2 — bypassPermissions re-verification**

```bash
AGENT_ROLE=phase-2-skeptic claude -p --agent phase-2-skeptic \
  --permission-mode bypassPermissions \
  '{"phase":2,"role":"phase-2-skeptic","slice_id":"spike/a1-s2","brief":"same task"}' 2>&1 | tee /tmp/spike2.log
```

Record PASS / FAIL + stderr excerpt.

**Step 4: Spike 3 — Claude Agent SDK**

```bash
# Install SDK in a scratch venv if not already available
uv tool install claude-agent-sdk 2>&1 || true
python3 -c "
from claude_agent_sdk import query
import os
os.environ['AGENT_ROLE'] = 'phase-2-skeptic'
for msg in query(prompt='write .claude/current-slice/validation/approach.md with hello', options={'agent': 'phase-2-skeptic', 'permission_mode': 'acceptEdits'}):
    print(msg)
" 2>&1 | tee /tmp/spike3.log
```

Record PASS / FAIL + stderr excerpt.

**Step 5: Write spike results doc**

File: `docs/plans/2026-04-20-a1-spike-results.md`. Structure:

```markdown
# A1 Spike Results — 2026-04-20

## Baseline
<one paragraph: current failure mode, stderr excerpt>

## Spike 1 — additionalDirectories
Result: PASS | FAIL
<stderr excerpt on fail, artifact path on pass>

## Spike 2 — bypassPermissions
Result: PASS | FAIL
<stderr excerpt on fail, artifact path on pass>

## Spike 3 — Claude Agent SDK
Result: PASS | FAIL
<stderr excerpt on fail, artifact path on pass>

## Decision
Path X (settings fix — which spike) | Path Y (contract redesign)
Rationale: <one paragraph>
```

**Step 6: Commit**

```bash
git add docs/plans/2026-04-20-a1-spike-results.md
git commit -m "docs(spike): a1 sensitive-file gate — empirical unblock evidence"
```

**Decision gate:** If Path Y, Tasks 1.6 and 1.7 grow to include artifact-return contract + agent-prompt rewrites. Phase 1 writer updates intent.md accordingly.

---

### Task 1.4: Wire role_guard into settings.json

**Files:**
- Modify: `.claude/settings.json` — `hooks.PreToolUse`
- Test: `tests/unit/test_role_guard_wired.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_role_guard_wired.py (add case)
import json
from pathlib import Path

def test_settings_json_registers_role_guard_pretooluse():
    settings = json.loads(Path(".claude/settings.json").read_text())
    pre = settings["hooks"]["PreToolUse"]
    role_guard_entries = [
        h for group in pre for h in group.get("hooks", [])
        if "role_guard.py" in h.get("command", "")
    ]
    assert len(role_guard_entries) == 1, f"expected 1 role_guard registration, found {len(role_guard_entries)}"
    # must match Write|Edit|MultiEdit|NotebookEdit
    matchers = [g["matcher"] for g in pre if any("role_guard.py" in h.get("command","") for h in g.get("hooks",[]))]
    assert matchers[0] == "Write|Edit|MultiEdit|NotebookEdit"
```

**Step 2: Verify it fails**

```bash
uv run pytest tests/unit/test_role_guard_wired.py::test_settings_json_registers_role_guard_pretooluse -v
```

Expected: FAIL.

**Step 3: Implement**

Edit `.claude/settings.json` — add to `hooks.PreToolUse` array:

```json
{
  "matcher": "Write|Edit|MultiEdit|NotebookEdit",
  "hooks": [{"type": "command", "command": "uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py"}]
}
```

**Step 4: Verify it passes**

```bash
uv run pytest tests/unit/test_role_guard_wired.py -v
```

Expected: PASS on all three tests in that file.

---

### Task 1.5: Separate dispatch_phase_agent and dispatch_triager

**Files:**
- Modify: `scripts/slice_orchestrator.py` — replace `dispatch_agent`, update `run_phase_loop` callers
- Test: `tests/unit/test_dispatch_contract_separation.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_dispatch_contract_separation.py
from unittest.mock import patch, MagicMock
from scripts import slice_orchestrator as orch

def test_phase_agent_result_validates_status_field():
    with patch.object(orch, "_run_claude_subprocess") as mock_run:
        mock_run.return_value = MagicMock(stdout='{"status":"OK","commit_hash":"abc","summary":"done"}', stderr="", returncode=0)
        result = orch.dispatch_phase_agent("phase-1-writer", {"brief":"test"})
        assert result["status"] == "OK"

def test_triager_result_validates_action_field():
    with patch.object(orch, "_run_claude_subprocess") as mock_run:
        mock_run.return_value = MagicMock(stdout='{"action":"RE_DISPATCH","target_phase":2,"amendment":"x","rationale":"y"}', stderr="", returncode=0)
        result = orch.dispatch_triager("abc", 2, "test/slice")
        assert result["action"] == "RE_DISPATCH"
        assert result["target_phase"] == 2

def test_triager_return_does_not_write_failure_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.object(orch, "_run_claude_subprocess") as mock_run:
        mock_run.return_value = MagicMock(stdout='{"action":"RE_DISPATCH","target_phase":2,"amendment":"x","rationale":"y"}', stderr="", returncode=0)
        orch.dispatch_triager("abc", 2, "test/slice")
    debug_dir = tmp_path / ".claude/orchestrator-debug"
    logs = list(debug_dir.glob("*-issue-triager.log")) if debug_dir.exists() else []
    assert logs == [], f"expected no triager failure logs, got {logs}"
```

**Step 2: Verify fails**

```bash
uv run pytest tests/unit/test_dispatch_contract_separation.py -v
```

Expected: FAIL (`dispatch_phase_agent` / `dispatch_triager` don't exist).

**Step 3: Implement**

Edit `scripts/slice_orchestrator.py`:

```python
# Replace existing dispatch_agent (lines 127-192) with:

def _run_claude_subprocess(role, inputs, envelope=None, timeout_hard=None):
    env = os.environ.copy()
    env["AGENT_ROLE"] = role
    if envelope is not None:
        env["AGENT_ENVELOPE"] = envelope
    timeout = _resolve_timeout(role, timeout_hard)
    cmd = ["claude", "-p", "--agent", role, "--permission-mode", PERMISSION_MODE, json.dumps(inputs)]
    return _run_with_live_stderr(cmd, env, timeout)  # defined in Task 1.7

def dispatch_phase_agent(role, inputs, envelope=None, timeout_hard=None):
    try:
        proc = _run_claude_subprocess(role, inputs, envelope, timeout_hard)
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timeout = _resolve_timeout(role, timeout_hard)
        _write_failure_log(role, inputs, "timeout", stdout, stderr, f"timeout after {timeout}s", _slice_id())
        return {"status": "FAILED", "summary": f"timeout after {timeout}s", "commit_hash": ""}

    obj = _parse_structured_tail(proc.stdout or "")
    if obj is None or "status" not in obj:
        _write_failure_log(role, inputs, proc.returncode, proc.stdout or "", proc.stderr or "",
                           "malformed agent output (no status field in JSON tail)", _slice_id())
        return {"status": "FAILED", "summary": "malformed agent output", "commit_hash": ""}
    if obj.get("status") != "OK":
        _write_failure_log(role, inputs, proc.returncode, proc.stdout or "", proc.stderr or "",
                           f"agent self-reported status={obj.get('status')!r}", _slice_id())
    return obj

def dispatch_triager(issue_commit_hash, current_phase, slice_id, timeout_hard=None):
    inputs = {"issue_commit_hash": issue_commit_hash, "current_phase": current_phase, "slice_id": slice_id}
    try:
        proc = _run_claude_subprocess("issue-triager", inputs, None, timeout_hard)
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        _write_failure_log("issue-triager", inputs, "timeout", stdout, stderr, "triager timeout", slice_id)
        return {"action": "ESCALATE_TO_USER", "rationale": "triager timeout"}

    obj = _parse_structured_tail(proc.stdout or "")
    if obj is None or "action" not in obj:
        _write_failure_log("issue-triager", inputs, proc.returncode, proc.stdout or "", proc.stderr or "",
                           "malformed triager output (no action field)", slice_id)
        return {"action": "ESCALATE_TO_USER", "rationale": "malformed triager output"}
    # Valid triager return — no failure log written.
    return obj
```

Update `run_phase_loop` (lines 306-385) to call `dispatch_phase_agent` and `dispatch_triager` in place of `dispatch_agent`. `_dispatch_for_phase` still dispatches phase-3 via `dispatch_phase_3`; phase-3's internal fan-out calls `dispatch_phase_agent` per cluster.

Update `_write_failure_log` signature to take `slice_id` as last arg (for D3 filename).

**Step 4: Verify passes**

```bash
uv run pytest tests/unit/test_dispatch_contract_separation.py -v
```

Expected: PASS.

---

### Task 1.6: Multi-line JSON tail parser

**Files:**
- Modify: `scripts/slice_orchestrator.py:92-107` (`_parse_structured_tail`)
- Test: `tests/unit/test_multiline_json_tail.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_multiline_json_tail.py
from scripts.slice_orchestrator import _parse_structured_tail

def test_pretty_printed_json_tail_parses():
    stdout = 'some output\n{\n  "status": "OK",\n  "commit_hash": "abc",\n  "summary": "done"\n}\n'
    obj = _parse_structured_tail(stdout)
    assert obj == {"status": "OK", "commit_hash": "abc", "summary": "done"}

def test_balanced_brace_walk_handles_nested_objects():
    stdout = 'noise\n{\n  "status": "OK",\n  "nested": {"a": 1, "b": {"c": 2}}\n}\n'
    obj = _parse_structured_tail(stdout)
    assert obj["status"] == "OK"
    assert obj["nested"]["b"]["c"] == 2

def test_line_scan_fallback_still_works():
    stdout = 'line1\nline2\n{"status":"OK","commit_hash":"abc","summary":"one-line"}\n'
    obj = _parse_structured_tail(stdout)
    assert obj["summary"] == "one-line"

def test_malformed_returns_none():
    assert _parse_structured_tail("no json here\n") is None
    assert _parse_structured_tail("") is None
```

**Step 2: Verify fails** (pretty-printed test fails).

**Step 3: Implement**

```python
# Replace lines 92-107 with:
def _parse_structured_tail(stdout):
    if not stdout:
        return None
    # Try line-scan first (backwards-compat fast path).
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if not line or not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            continue
    # Fall through to balanced-brace walk for multi-line JSON.
    lines = stdout.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].strip().endswith("}"):
            continue
        # Walk upward accumulating until braces balance.
        depth = 0
        start = None
        for j in range(i, -1, -1):
            depth += lines[j].count("}") - lines[j].count("{")
            if depth == 0 and "{" in lines[j]:
                start = j
                break
        if start is None:
            continue
        candidate = "\n".join(lines[start:i+1])
        # Trim leading garbage before first {
        brace = candidate.find("{")
        if brace > 0:
            candidate = candidate[brace:]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            continue
    return None
```

**Step 4: Verify passes** — all four tests GREEN.

---

### Task 1.7: Live-stderr streaming + debug filename rename

**Files:**
- Modify: `scripts/slice_orchestrator.py` — add `_run_with_live_stderr`, update `_write_failure_log`
- Test: `tests/unit/test_orchestrator_live_stderr.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_orchestrator_live_stderr.py
import subprocess, sys, time, os
from pathlib import Path
from scripts.slice_orchestrator import _run_with_live_stderr, _write_failure_log

def test_child_stderr_streams_to_orchestrator_stderr(capfd):
    script = "import sys,time; sys.stderr.write('hello\\n'); sys.stderr.flush(); time.sleep(0.1); sys.stderr.write('world\\n'); sys.stdout.write('{\"status\":\"OK\"}')"
    cmd = [sys.executable, "-c", script]
    proc = _run_with_live_stderr(cmd, os.environ.copy(), timeout=5)
    captured = capfd.readouterr()
    assert "hello" in captured.err
    assert "world" in captured.err
    assert proc.returncode == 0

def test_streamed_lines_have_slice_and_role_prefix(capfd, monkeypatch):
    # The prefix is applied by the caller (dispatch_phase_agent), not _run_with_live_stderr itself.
    # Verify dispatch applies a prefix that includes role and slice-id.
    script = "import sys; sys.stderr.write('probe-line\\n'); sys.stdout.write('{\"status\":\"OK\",\"commit_hash\":\"\",\"summary\":\"\"}')"
    # ... test dispatch_phase_agent wrapper adds [role|slice-id] prefix
    # (detail left to implementer — minimum: grep for the role and slice-id string in captured stderr)

def test_debug_log_filename_uses_slice_id_and_phase(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_failure_log("phase-2-skeptic", {"a":1}, 1, "stdout", "stderr", "reason", slice_id="feat/my-slice")
    logs = list((tmp_path / ".claude/orchestrator-debug").glob("*.log"))
    assert len(logs) == 1
    assert "feat-my-slice" in logs[0].name
    assert "phase-2-skeptic" in logs[0].name
```

**Step 2: Verify fails** — `_run_with_live_stderr` missing, slice-id not in filename.

**Step 3: Implement**

```python
# Add to scripts/slice_orchestrator.py:

def _run_with_live_stderr(cmd, env, timeout, prefix=""):
    """Popen with stderr tee'd to orchestrator stderr live + buffered for capture."""
    import threading
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout_buf = []
    stderr_buf = []

    def pump(src, dst, buf, pfx):
        try:
            for line in iter(src.readline, ""):
                if not line:
                    break
                buf.append(line)
                if dst is not None:
                    dst.write(f"{pfx}{line}" if pfx else line)
                    dst.flush()
        finally:
            src.close()

    t_out = threading.Thread(target=pump, args=(proc.stdout, None, stdout_buf, ""), daemon=True)
    t_err = threading.Thread(target=pump, args=(proc.stderr, sys.stderr, stderr_buf, prefix), daemon=True)
    t_out.start()
    t_err.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        t_out.join(timeout=2)
        t_err.join(timeout=2)
        raise subprocess.TimeoutExpired(cmd, timeout, output="".join(stdout_buf), stderr="".join(stderr_buf))
    t_out.join(timeout=2)
    t_err.join(timeout=2)
    # Build a CompletedProcess-shaped object for downstream compatibility.
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout="".join(stdout_buf), stderr="".join(stderr_buf))

# Update _write_failure_log signature:
def _write_failure_log(role, inputs, returncode, stdout, stderr, reason, slice_id="unknown-unknown"):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    slug = slice_id.replace("/", "-") if slice_id else "unknown-unknown"
    # derive phase-N token from role if possible
    phase_token = ""
    for phase_num, r in ROLE_FOR_PHASE.items():
        if r == role:
            phase_token = f"phase-{phase_num}-"
            break
    path = DEBUG_DIR / f"{slug}-{phase_token}{role}-{ts}.log"
    body = (
        f"reason: {reason}\nrole: {role}\nslice_id: {slice_id}\n"
        f"returncode: {returncode}\ninputs: {json.dumps(inputs)}\n"
        f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n"
    )
    path.write_text(body)
    print(f"orchestrator: agent failure logged to {path}", file=sys.stderr)
    return path
```

Update `_run_claude_subprocess` to pass `prefix=f"[{role}|{_slice_id()}] "` to `_run_with_live_stderr`.

**Step 4: Verify passes** — all three tests GREEN.

---

### 1.3 Phase 4 integration

Phase-4-integrator runs:

```bash
uv run pytest tests/unit/ tests/integration/ -v
uv run python scripts/validate_architecture.py
uv run python scripts/integration_gate.py
```

**Central gate:** `tests/integration/test_compressed_slice_end_to_end.py` must be GREEN. This is the autonomous end-to-end proof.

Integration test body:

```python
# tests/integration/test_compressed_slice_end_to_end.py
import subprocess, tempfile, shutil, os
from pathlib import Path

def test_trivial_slice_completes_autonomously(tmp_path, monkeypatch):
    # Set up a scratch git repo with cairn infrastructure.
    repo = tmp_path / "repo"
    shutil.copytree(".", repo, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".claude/current-slice", ".claude/orchestrator-debug"))
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    # Minimal trivial brief that exercises all four phases.
    brief = "Add a test assertion that 1+1==2 in tests/unit/test_trivial.py"
    result = subprocess.run(
        ["python3", "scripts/slice_orchestrator.py", "--brief", brief],
        capture_output=True, text=True, timeout=1200,
    )
    assert result.returncode == 0, f"orchestrator failed: stderr={result.stderr}"
    # Slice closed.
    slice_yaml = Path(".claude/current-slice/slice.yaml").read_text()
    assert "status: complete" in slice_yaml
    # Sweep-notes present.
    assert Path(".claude/current-slice/integration/sweep-notes.md").exists()
    # No manual intervention touched: check git log has only orchestrator + subagent commits.
    log = subprocess.check_output(["git", "log", "--format=%s"], cwd=repo, text=True)
    assert "manual" not in log.lower()
```

### 1.4 Slice 1 exit criteria

- All unit tests GREEN.
- Integration test `test_trivial_slice_completes_autonomously` GREEN — this is the base-has-a-pulse gate.
- `.claude/settings.json` registers role_guard hook.
- `docs/plans/2026-04-20-a1-spike-results.md` on disk with decision.

---

## SLICE 2 — State Machine + Serialization

**Executed via the compression pipeline** (dogfood — Slice 1 proved the pipeline works).

### 2.0 Brief

```
Clear the orchestrator's code-bug backlog: state-machine durability (B10 close_slice integration, B14 RE_DISPATCH state persistence, B15 max-1 redispatch cap, B12 malformed slice.yaml exit, B13 SIGINT/SIGTERM handler), git reconciliation (B11 check=True on all git calls, B9 post-timeout HEAD reconciliation), serialization (B3/B4/B6 PyYAML adoption for brief/name/clusters, B7 JSON-list envelope encoding), phase-3 robustness (B16 empty-cluster guard, B2 per-cluster log capture, B8 FAILED classification + exponential backoff). Add pyyaml dep. One regression test per bug. References design docs/plans/2026-04-20-compression-pipeline-hardening-design.md §6.
```

### 2.1 Phase 2 — RED test list

Fourteen regression tests, one per bug:

- `tests/unit/test_close_slice_integration.py::test_phase_4_ok_triggers_close_slice`
- `tests/unit/test_re_dispatch_durability.py::test_re_dispatch_persists_current_phase_before_jump`
- `tests/unit/test_max_redispatch_cap.py::test_second_re_dispatch_to_same_phase_escalates`
- `tests/unit/test_malformed_slice_yaml_exits.py::test_malformed_yaml_exits_one_not_silent_restart`
- `tests/unit/test_signal_handling.py::test_sigterm_reaps_child_and_exits_130`
- `tests/unit/test_git_helper_raises_on_failure.py::test_commit_failure_raises_not_silently_advances`
- `tests/unit/test_post_timeout_reconciliation.py::test_timeout_records_partial_commit_if_head_advanced`
- `tests/unit/test_pyyaml_slice_state.py::test_brief_with_quotes_roundtrips`
- `tests/unit/test_pyyaml_slice_state.py::test_name_with_backslash_roundtrips`
- `tests/unit/test_pyyaml_clusters.py::test_clusters_with_comments_parse`
- `tests/unit/test_json_list_envelope.py::test_envelope_with_colon_in_path`
- `tests/unit/test_empty_cluster_guard.py::test_empty_clusters_fallback_to_intent_envelope`
- `tests/unit/test_phase_3_peer_log_capture.py::test_peer_cluster_logs_written_on_fast_fail`
- `tests/unit/test_failed_classification.py::test_transient_retried_up_to_three_times_with_backoff`

Plus a state-machine property test:
- `tests/unit/test_orchestrator_resume_correctness.py::test_crash_mid_redispatch_resumes_at_target_phase`

### 2.2 Phase 3 — Tasks

Cluster partition (Phase 2 decides, proposed):
- Cluster `state-machine`: 2.3, 2.4, 2.5, 2.6, 2.7
- Cluster `git-reconciliation`: 2.8, 2.9
- Cluster `serialization`: 2.10, 2.11, 2.12
- Cluster `phase-3-robustness`: 2.13, 2.14, 2.15

### Task 2.3: close_slice integration (B10)

**Files:** `scripts/slice_orchestrator.py` — `run_phase_loop` exit path, `close_slice` call.

At the end of `run_phase_loop`, after the `while 1 <= phase <= max_phase` loop, replace `return 0` with:

```python
state = read_slice_state(SLICE_YAML)
close_slice(state)
return 0
```

`close_slice` (line 424) stays mostly as-is but gains `subprocess.run(..., check=True)` per Task 2.8.

### Task 2.4: RE_DISPATCH durability (B14)

**Files:** `scripts/slice_orchestrator.py` — RE_DISPATCH branch in `run_phase_loop`.

Before `phase = target; continue` (line 368), persist and commit:

```python
if action == "RE_DISPATCH":
    target = triager.get("target_phase")
    if not isinstance(target, int) or not (1 <= target <= max_phase):
        print(f"orchestrator: invalid target_phase {target!r}; aborting", file=sys.stderr)
        return 1
    _persist_current_phase(target)
    _git("commit", "-m", f"slice: re-dispatch phase {phase} → phase {target}", "--allow-empty")
    phase = target
    continue

def _persist_current_phase(phase):
    import yaml
    state = yaml.safe_load(SLICE_YAML.read_text()) if SLICE_YAML.exists() else {}
    state["current_phase"] = phase
    SLICE_YAML.write_text(yaml.safe_dump(state, default_flow_style=False, sort_keys=False))
    _git("add", str(SLICE_YAML))
```

### Task 2.5: Max-1 redispatch cap (B15)

**Files:** `scripts/slice_orchestrator.py` — `run_phase_loop`.

```python
# At top of run_phase_loop:
redispatch_count = {}

# In RE_DISPATCH branch, before _persist_current_phase:
if redispatch_count.get(target, 0) >= 1:
    print(f"orchestrator: phase {target} already re-dispatched once; escalating", file=sys.stderr)
    return 1
redispatch_count[target] = redispatch_count.get(target, 0) + 1
```

### Task 2.6: Malformed slice.yaml exits (B12)

**Files:** `scripts/slice_orchestrator.py:269-277` (`_current_phase`).

```python
def _current_phase():
    if not SLICE_YAML.exists():
        return 1
    try:
        import yaml
        state = yaml.safe_load(SLICE_YAML.read_text())
        value = state.get("current_phase", 1) if state else 1
        return int(value)
    except (ValueError, OSError, TypeError, yaml.YAMLError) as exc:
        print(f"orchestrator: {SLICE_YAML} malformed: {exc}. Aborting.", file=sys.stderr)
        sys.exit(1)
```

### Task 2.7: Signal handling (B13)

**Files:** `scripts/slice_orchestrator.py` — add at module level + `main`.

```python
import signal

_active_child = None

def _clean_shutdown(signum, frame):
    global _active_child
    print(f"orchestrator: received signal {signum}, shutting down", file=sys.stderr)
    if _active_child is not None and _active_child.poll() is None:
        _active_child.terminate()
        try:
            _active_child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _active_child.kill()
    sys.exit(130)

# In main() before running:
signal.signal(signal.SIGINT, _clean_shutdown)
signal.signal(signal.SIGTERM, _clean_shutdown)

# In _run_with_live_stderr, set _active_child = proc right after Popen; reset to None after wait.
```

### Task 2.8: Git helper with returncode check (B11)

**Files:** `scripts/slice_orchestrator.py` — add `_git` helper, replace all `subprocess.run(["git", ...], check=False)` callers.

```python
def _git(*args, allow_fail=False):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result
```

Update `commit_phase_handoff`, `init_new_slice`, `close_slice`, `_abort_slice` callers. Where the current code tolerates failure (e.g., commit on empty working tree), pass `allow_fail=True` explicitly.

### Task 2.9: Post-timeout git reconciliation (B9)

**Files:** `scripts/slice_orchestrator.py` — timeout branch of `dispatch_phase_agent`.

```python
# In dispatch_phase_agent timeout branch:
pre_head = _git("rev-parse", "HEAD", allow_fail=True).stdout.strip()
# ... subprocess call ...
except subprocess.TimeoutExpired as exc:
    post_head = _git("rev-parse", "HEAD", allow_fail=True).stdout.strip()
    partial = post_head if post_head != pre_head else ""
    _write_failure_log(role, inputs, "timeout", exc.stdout or "", exc.stderr or "",
                       f"timeout after {timeout}s; partial_commit={partial or 'none'}", _slice_id())
    return {"status": "FAILED", "summary": f"timeout after {timeout}s; partial={partial or 'none'}", "commit_hash": partial}
```

### Task 2.10: PyYAML for slice.yaml (B3, B4)

**Files:** `pyproject.toml` (add `pyyaml`), `scripts/slice_orchestrator.py` (`read_slice_state`, `init_new_slice`, `close_slice`).

```bash
uv add pyyaml
```

Replace `read_slice_state` (lines 52-74) with:

```python
def read_slice_state(path):
    import yaml
    data = yaml.safe_load(Path(path).read_text())
    return data if isinstance(data, dict) else {}
```

Replace manual YAML string construction in `init_new_slice` (line 414-418) and `close_slice` (line 425-429) with `yaml.safe_dump`:

```python
# init_new_slice:
state = {
    "id": proposed,
    "name": proposed,
    "status": "in-progress",
    "current_phase": 1,
    "brief": brief,
}
SLICE_YAML.write_text(yaml.safe_dump(state, default_flow_style=False, sort_keys=False))

# close_slice:
state_out = {
    "id": state.get("id", "unknown/unknown"),
    "name": state.get("name", ""),
    "status": "complete",
    "current_phase": 4,
}
SLICE_YAML.write_text(yaml.safe_dump(state_out, default_flow_style=False, sort_keys=False))
```

### Task 2.11: PyYAML for clusters (B6)

**Files:** `scripts/slice_orchestrator.py:195-217` (`_parse_clusters`).

```python
def _parse_clusters(text):
    import yaml
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"coupling-clusters.yaml malformed: {exc}")
    if not isinstance(data, list):
        return []
    clusters = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        files = item.get("files", []) or []
        if not isinstance(files, list):
            files = []
        clusters.append({"name": name, "files": [str(f) for f in files]})
    return clusters
```

### Task 2.12: JSON-list envelope (B7)

**Files:** `scripts/slice_orchestrator.py:232` (`dispatch_phase_3` envelope construction), `checks/role_guard.py:46-49` (`_envelope_patterns`).

```python
# slice_orchestrator.py:232 — replace:
envelope = ":".join(cluster["files"]) if cluster["files"] else ""
# with:
envelope = json.dumps(cluster["files"]) if cluster["files"] else "[]"

# checks/role_guard.py:46-49 — replace:
def _envelope_patterns(raw):
    if not raw:
        return []
    try:
        items = json.loads(raw)
        return [p for p in items if p]
    except (ValueError, TypeError):
        # backward-compat: colon-separated
        return [p for p in raw.split(":") if p]
```

### Task 2.13: Empty-cluster guard (B16)

**Files:** `scripts/slice_orchestrator.py:220-226` (`dispatch_phase_3`).

```python
def dispatch_phase_3(slice_id):
    if CLUSTERS_YAML.exists():
        clusters = _parse_clusters(CLUSTERS_YAML.read_text())
    else:
        clusters = []
    # Filter empty-files clusters; fall back to intent envelope.
    clusters = [c for c in clusters if c.get("files")]
    if not clusters:
        intent_envelope = _read_intent_envelope()  # new helper: reads intent.md, extracts envelope section
        if intent_envelope:
            clusters = [{"name": "implicit", "files": intent_envelope}]
        else:
            print("orchestrator: phase-3 has no clusters and no intent envelope; aborting", file=sys.stderr)
            return {"status": "FAILED", "commit_hash": "", "summary": "phase 3: no clusters, no envelope"}
    # ... rest of fan-out unchanged ...
```

`_read_intent_envelope` helper: regex-match for `envelope:` line in `intent.md`, return list of file paths.

### Task 2.14: Per-cluster log capture (B2)

**Files:** `scripts/slice_orchestrator.py:220-254` (`dispatch_phase_3`).

Even on fast-fail, iterate all `futures` (not just those returned before the first failure) and write per-cluster debug logs:

```python
results = []
for cluster, future in zip(clusters, futures):
    try:
        r = future.result()
        results.append(r)
    except Exception as exc:
        results.append({"status": "FAILED", "commit_hash": "", "summary": f"cluster {cluster['name']} exception: {exc}"})
    # Always write a per-cluster log for triage.
    _write_cluster_log(slice_id, cluster, results[-1])

def _write_cluster_log(slice_id, cluster, result):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    slug = slice_id.replace("/", "-")
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    path = DEBUG_DIR / f"{slug}-phase-3-cluster-{cluster['name']}-{ts}.log"
    body = f"cluster: {cluster['name']}\nfiles: {cluster['files']}\nresult: {json.dumps(result)}\n"
    path.write_text(body)
```

### Task 2.15: FAILED classification + backoff (B8)

**Files:** `scripts/slice_orchestrator.py` — `run_phase_loop` FAILED branch.

```python
import time

TRANSIENT_PATTERNS = ("rate limit", "overloaded", "429", "503", "timeout")

def _classify_failure(result):
    summary = (result.get("summary") or "").lower()
    if any(p in summary for p in TRANSIENT_PATTERNS):
        return "transient"
    if "malformed" in summary:
        return "malformed"
    return "logic"

# In FAILED branch:
if status == "FAILED":
    klass = _classify_failure(result)
    max_attempts = 4 if klass == "transient" else 2  # 1 initial + 3 retries transient; +1 retry for logic/malformed
    for attempt in range(1, max_attempts):
        if klass == "transient":
            delay = 4 ** (attempt - 1)  # 1, 4, 16
            print(f"orchestrator: transient failure; retrying in {delay}s (attempt {attempt+1}/{max_attempts})", file=sys.stderr)
            time.sleep(delay)
        retry = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
        if retry.get("status") == "OK":
            commit_phase_handoff(phase, retry.get("summary",""), retry.get("commit_hash",""))
            phase += 1
            break
        klass = _classify_failure(retry)
    else:
        print(f"orchestrator: phase {phase} failed after retries; escalating", file=sys.stderr)
        return 1
    continue
```

### 2.3 Phase 4 integration

All unit tests GREEN. All 14 B-bug regression tests GREEN. Integration test from Slice 1 still GREEN (no regression of foundation).

---

## SLICE 3 — Multi-instance + Observability

**Executed via the compression pipeline.**

### 3.0 Brief

```
Make the orchestrator safe to run in parallel worktrees for fleet-coordinator consumption. Add E1 worktree-scoped lockfile (fcntl.flock on .claude/current-slice/.lock), E2 role-guard PID scope (refuse if AGENT_ROLE set without matching CAIRN_ORCHESTRATOR_PID), structured JSON exit (.claude/current-slice/orchestrator-result.json on every exit path), D1 debug log index (.claude/orchestrator-debug/index.jsonl appended atomically), and a parallel-worktree integration test proving two concurrent orchestrators complete without cross-contamination. References design docs/plans/2026-04-20-compression-pipeline-hardening-design.md §7.
```

### 3.1 Phase 2 — RED test list

- `tests/unit/test_slice_lock.py::test_second_orchestrator_same_worktree_aborts_with_pid`
- `tests/unit/test_slice_lock.py::test_two_worktrees_both_acquire_lock`
- `tests/unit/test_role_guard_pid_scope.py::test_agent_role_without_pid_denied`
- `tests/unit/test_role_guard_pid_scope.py::test_agent_role_with_matching_pid_allowed`
- `tests/unit/test_orchestrator_result_json.py::test_ok_exit_writes_result_json`
- `tests/unit/test_orchestrator_result_json.py::test_failed_exit_writes_result_json`
- `tests/unit/test_orchestrator_result_json.py::test_signal_exit_writes_result_json`
- `tests/unit/test_debug_log_index.py::test_index_append_is_atomic_under_concurrent_writes`
- `tests/integration/test_parallel_worktrees.py::test_two_concurrent_orchestrators_both_complete`

### 3.2 Phase 3 — Tasks

Cluster partition proposed:
- Cluster `locking-and-scope`: 3.3, 3.4
- Cluster `result-json-and-index`: 3.5, 3.6
- Cluster `integration-test`: 3.7

### Task 3.3: Worktree lock (E1)

**Files:** `scripts/slice_orchestrator.py` — `main` entry.

```python
import fcntl

_lock_handle = None

def _acquire_slice_lock():
    global _lock_handle
    lock_path = Path(".claude/current-slice/.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        existing = lock_path.read_text().splitlines() if lock_path.exists() else []
        holder = existing[0] if existing else "unknown"
        fh.close()
        raise SystemExit(f"orchestrator: slice lock held by PID {holder}; another orchestrator is running in this worktree")
    fh.write(f"{os.getpid()}\n{datetime.datetime.now().isoformat()}\n")
    fh.flush()
    _lock_handle = fh
    return fh

# In main() before running phases:
_acquire_slice_lock()
os.environ["CAIRN_ORCHESTRATOR_PID"] = str(os.getpid())
```

### Task 3.4: Role-guard PID scope (E2)

**Files:** `checks/role_guard.py:52` (main).

```python
def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        print(f"role_guard: malformed stdin: {exc}", file=sys.stderr)
        return 2

    role = os.environ.get("AGENT_ROLE")
    if not role:
        return 0

    # E2: require orchestrator PID context for role-keyed enforcement.
    orch_pid = os.environ.get("CAIRN_ORCHESTRATOR_PID")
    if not orch_pid:
        print(f"role_guard: AGENT_ROLE={role!r} set but CAIRN_ORCHESTRATOR_PID unset; refusing writes. Set via orchestrator dispatch only.", file=sys.stderr)
        return 1

    # ... rest unchanged ...
```

### Task 3.5: Structured JSON exit

**Files:** `scripts/slice_orchestrator.py` — every exit path in `main`, `run_phase_loop`, signal handler, abort paths.

```python
import atexit

_orchestrator_result = {
    "slice_id": "",
    "status": "UNKNOWN",
    "exit_code": 1,
    "final_commit": "",
    "phases_completed": [],
    "redispatches": {},
    "started_at": datetime.datetime.now().isoformat(),
    "ended_at": "",
    "summary": "",
}

def _write_result_json():
    _orchestrator_result["ended_at"] = datetime.datetime.now().isoformat()
    path = Path(".claude/current-slice/orchestrator-result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_orchestrator_result, indent=2))

atexit.register(_write_result_json)

# Update throughout:
# - run_phase_loop: update _orchestrator_result["phases_completed"].append(phase) after each OK
# - FAILED terminal: _orchestrator_result["status"] = "FAILED"; _orchestrator_result["exit_code"] = 1
# - OK terminal (post-close): status="OK", exit_code=0, final_commit=<last commit>
# - _abort_slice: status="ABORTED"
# - ESCALATE_TO_USER: status="ESCALATED"
# - SIGINT/SIGTERM: status="SIGNALED"
```

### Task 3.6: Debug log index (D1)

**Files:** `scripts/slice_orchestrator.py` — `_write_failure_log`.

```python
def _write_failure_log(role, inputs, returncode, stdout, stderr, reason, slice_id="unknown-unknown"):
    # ... existing file write ...
    index_path = DEBUG_DIR / "index.jsonl"
    index_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "slice_id": slice_id,
        "role": role,
        "returncode": returncode,
        "reason": reason,
        "log_path": str(path),
    }
    # Atomic append using O_APPEND.
    with open(index_path, "a") as f:
        f.write(json.dumps(index_entry) + "\n")
    return path
```

### Task 3.7: Parallel-worktree integration test

**Files:** `tests/integration/test_parallel_worktrees.py`.

```python
import subprocess, tempfile, shutil, os, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def test_two_concurrent_orchestrators_both_complete(tmp_path):
    repo_root = Path(".").resolve()
    # Create two worktrees of the current branch.
    wt_a = tmp_path / "wt-a"
    wt_b = tmp_path / "wt-b"
    subprocess.run(["git", "worktree", "add", "-b", "test/parallel-a", str(wt_a)], cwd=repo_root, check=True)
    subprocess.run(["git", "worktree", "add", "-b", "test/parallel-b", str(wt_b)], cwd=repo_root, check=True)
    try:
        def run_orch(wt):
            return subprocess.run(
                ["python3", "scripts/slice_orchestrator.py", "--brief", f"add a trivial assertion {wt.name}"],
                cwd=wt, capture_output=True, text=True, timeout=1800,
            )
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_a = ex.submit(run_orch, wt_a)
            f_b = ex.submit(run_orch, wt_b)
            r_a, r_b = f_a.result(), f_b.result()
        assert r_a.returncode == 0, f"worktree A failed: {r_a.stderr}"
        assert r_b.returncode == 0, f"worktree B failed: {r_b.stderr}"
        # Both result.json present with status OK.
        res_a = json.loads((wt_a / ".claude/current-slice/orchestrator-result.json").read_text())
        res_b = json.loads((wt_b / ".claude/current-slice/orchestrator-result.json").read_text())
        assert res_a["status"] == "OK"
        assert res_b["status"] == "OK"
        # No cross-branch commits.
        log_a = subprocess.check_output(["git", "log", "--format=%H", "test/parallel-a"], cwd=repo_root, text=True).split()
        log_b = subprocess.check_output(["git", "log", "--format=%H", "test/parallel-b"], cwd=repo_root, text=True).split()
        assert res_a["final_commit"] in log_a
        assert res_b["final_commit"] in log_b
        assert res_a["final_commit"] not in log_b
        assert res_b["final_commit"] not in log_a
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt_a)], cwd=repo_root, check=False)
        subprocess.run(["git", "worktree", "remove", "--force", str(wt_b)], cwd=repo_root, check=False)
        subprocess.run(["git", "branch", "-D", "test/parallel-a"], cwd=repo_root, check=False)
        subprocess.run(["git", "branch", "-D", "test/parallel-b"], cwd=repo_root, check=False)
```

This test is slow (~5-10 min). Mark with `@pytest.mark.integration` or similar; default pytest run still includes it but CI may segregate.

### 3.3 Phase 4 integration

All unit tests GREEN. Parallel-worktree integration test GREEN. Slice 1 and Slice 2 regression tests still GREEN.

---

## Slice-ordering & handoff

1. **Slice 1** — run first via `/start-slice "<Slice 1 brief above>"`. Because the pipeline may still fail at A1 mid-slice, the user watches live-debug output and manually intervenes if the subagent wedges. Slice 1's integration test is the proof that subsequent slices can run autonomously.
2. **Slice 2** — after Slice 1 closes with PASS sweep. Run `/start-slice "<Slice 2 brief>"`. Expect no human intervention this time; if there is, that's a Slice 1 regression.
3. **Slice 3** — after Slice 2 closes. Same pattern.
4. **Sweep** — after each slice close, `/integration-sweep` advances `.claude/sweep.yaml`.

Total: three slices + three sweeps. Estimated ~1 day Slice 1 (may hit Path Y redesign), ~4 hours Slices 2 and 3 each if compression pipeline works autonomously.

---

## Plan complete and saved to `docs/plans/2026-04-20-compression-pipeline-hardening-plan.md`.

**Execution options (note: this plan is executed via the cairn compression pipeline — three `/start-slice` invocations — not via the standard subagent-driven or parallel-session modes below):**

**1. Cairn compression pipeline (this session, as the user directed)** — I launch Slice 1 via `/start-slice` in this session, user watches live debug output, intervenes if subagents wedge on A1. On close, launch Slice 2; on close, launch Slice 3. This is what the user has committed to.

**2. Subagent-Driven alternative (this session)** — I dispatch a fresh subagent per task (ignoring the cairn pipeline), reviewing between tasks. Faster iteration but bypasses the pipeline we're hardening. Not recommended given the explicit "use the compression pipeline anyway" direction.

**3. Parallel Session alternative** — Open a new session with `executing-plans`, batch execution with checkpoints. Same downside as #2.

**Recommendation: option 1.** Start Slice 1 now. I'll initiate `/start-slice` when you give the go-ahead.

# Slice Compression Protocol — Forward Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship compression infrastructure (orchestrator + role agents + role-guard hook + thin `/start-slice`) as Slice A of a new `compression` feature, then dogfood it via Slice B (Part 0 ADR).

**Architecture:** Python state-machine orchestrator (`scripts/slice_orchestrator.py`) dispatches role-scoped Claude agents per phase via `claude -p --agent <role>`; structured returns parsed by script; orchestrator holds zero cross-phase Claude context; `checks/role_guard.py` enforces write-path restrictions keyed on `AGENT_ROLE` env var; agent `.md` files declare `allowed-tools` as the outer gate.

**Tech Stack:** Python 3 (stdlib only: `subprocess`, `json`, `os`, `sys`, `pathlib`, `argparse`, `concurrent.futures`, `typing.TypedDict`). Bash for existing hooks (unchanged). Claude Code agent definitions. pytest + uv for tests.

**Source design:** `docs/plans/2026-04-18-slice-compression-protocol-design.md`.

---

## §0 — Program-level sequencing (forward map)

This plan implements Slice A. The broader program sequence:

| Phase | Work | Execution |
|---|---|---|
| **Prerequisite** | Close `identifier-scheme/doc-sweep` on `feature/identifier-scheme`. Merge feature to `dev`. | Serial, on this branch |
| **Feature creation** | New feature `compression` on `feature/compression` branch (worktree). | — |
| **Slice A** (this plan) | Compression infrastructure. | Serial (bootstrap) |
| **Slice B** | Part 0 ADR with P1-P6 + D1/D2/D3. | **Compressed (dogfood)** |
| **Slice C** | F2 fix / candidate-set hygiene (per audit seed 5) | Compressed |
| **Slice D-F** | Audit follow-ups: `envelope-immutability-guard`, `phase-4-sweepnotes-required`, `d3-rolling-window-surfacing`. | Compressed, potentially parallel |
| **Merge to dev** | After ≥3 clean compressed slices. | — |
| **Merge to master** | After `dev` stable. | Consumer release |

**After compression merges:** efficiency program Parts 1/2/6 resume on their own features; each slice is compressed; multi-slice parallelism (per `parallelism-v1` D1) available.

---

## Prerequisite — Close identifier-scheme feature first

Before starting this plan, the following slice on `feature/identifier-scheme` must close:

- `identifier-scheme/doc-sweep` — queued (absorbs residual prose cleanup from the dropped `slice-and-feature-rename` slice; see feature file for drop reason)

Merge `feature/identifier-scheme` to `dev`. **Only then** create the worktree for compression work.

**If the user chooses to skip prerequisite closure** (not recommended): the compression feature branches from current `feature/identifier-scheme` tip, accepting that downstream rebases may be messy when identifier-scheme eventually lands.

---

## Worktree setup (one-time)

**Step 1: Create worktree for compression feature**

```bash
cd /Users/mohammed.farook/Developer/lab/cairn
git worktree add .worktrees/compression -b feature/compression dev
cd .worktrees/compression
uv sync  # ensure venv
```

**Step 2: Create feature file**

```bash
cat > .claude/features/compression.yaml <<'EOF'
id: compression
name: "Slice compression — orchestrator-driven phase dispatch"
intent: "Ship compression protocol: orchestrator (Python state machine) dispatches role-scoped phase agents via claude -p; two-layer enforcement (allowed-tools + role_guard.py); D1/D2/D3 universal phase-artifact discipline. Subsumes efficiency-program Part 3 S1+S2; supersedes Part 2 E2 in original form; implements Part 2 E6."
shaped-from: docs/plans/2026-04-18-slice-compression-protocol-design.md
created: 2026-04-18
slices:
  - id: compression/infrastructure
    added: 2026-04-18
    intent: "Slice A: ship slice_orchestrator.py, phase role agents, role_guard.py hook, thin /start-slice refactor. Serial execution (bootstrap). Audit findings F1/F3/F4/F5 prevented by construction."
EOF
```

**Step 3: Verify and commit**

```bash
git add .claude/features/compression.yaml
git commit -m "feat: add compression feature file"
```

---

## Pre-Task 0 — Verify platform primitive assumptions

Before building, confirm the Claude Code CLI supports what the design assumes. If any of these fails, the design needs adaptation (see design doc §12 open question #5).

**Step 1: Verify `claude -p --agent <name>` works**

```bash
# Create a minimal test agent
mkdir -p /tmp/cairn-probe/.claude/agents
cat > /tmp/cairn-probe/.claude/agents/probe.md <<'EOF'
---
name: probe
description: Minimal probe agent for platform-primitive verification
tools: [Read]
---
You are the probe agent. Respond with just the string OK_PROBE.
EOF
cd /tmp/cairn-probe && claude -p --agent probe "say the probe phrase" 2>&1 | head -20
```

**Expected:** output contains `OK_PROBE`. If not, the `--agent` flag name may differ (try `--subagent`, `--role`, etc.) or the agent schema may differ. **Document findings** in a `.claude/platform-probe.md` note before proceeding. Adjust all downstream tasks' dispatch invocations to match discovered interface.

**Step 2: Verify allowed-tools enforcement**

```bash
cat > /tmp/cairn-probe/.claude/agents/probe-deny.md <<'EOF'
---
name: probe-deny
description: Tests allowed-tools enforcement
tools: [Read]
---
Try to write a file to /tmp/probe-test.txt. If you can, return "WROTE". If blocked, return "BLOCKED".
EOF
cd /tmp/cairn-probe && claude -p --agent probe-deny "do it" 2>&1 | head -20
```

**Expected:** output contains `BLOCKED`. If `WROTE` appears, allowed-tools is not mechanically enforced — design must add prose-level guard as fallback.

**Step 3: Commit probe findings**

```bash
git add .claude/platform-probe.md
git commit -m "chore: document Claude Code agent dispatch primitives"
```

**Decision point:** if Step 1 or Step 2 fails, PAUSE. Escalate to design doc as open issue before continuing.

---

## Task 1 — Scaffold `checks/role_guard.py` with first failing test

**Files:**
- Create: `checks/role_guard.py`
- Test: `tests/unit/test_role_guard.py`

**Step 1: Write the failing test for role_guard.py structure**

Create `tests/unit/test_role_guard.py`:

```python
"""Tests for checks/role_guard.py — role-scoped write-path enforcement."""
import json
import subprocess
from pathlib import Path

ROLE_GUARD = Path(__file__).parent.parent.parent / "checks" / "role_guard.py"


def run_guard(env_role: str | None, tool_input: dict) -> tuple[int, str]:
    """Invoke role_guard.py with env + stdin; return (exit_code, stderr)."""
    env = {"PATH": "/usr/bin:/bin"}
    if env_role is not None:
        env["AGENT_ROLE"] = env_role
    result = subprocess.run(
        ["python3", str(ROLE_GUARD)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stderr


def test_no_agent_role_env_is_noop():
    """When AGENT_ROLE is unset, role_guard must exit 0 (no enforcement)."""
    exit_code, _ = run_guard(
        env_role=None,
        tool_input={"tool_name": "Write", "tool_input": {"file_path": "/tmp/any"}},
    )
    assert exit_code == 0
```

**Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/unit/test_role_guard.py::test_no_agent_role_env_is_noop -v
```

Expected: FAIL with "No such file or directory" or similar (role_guard.py doesn't exist yet).

**Step 3: Write minimal implementation**

Create `checks/role_guard.py`:

```python
#!/usr/bin/env python3
"""Role-scoped write-path enforcement hook.

Invoked as a PreToolUse hook. Reads tool-call JSON from stdin, checks the
AGENT_ROLE env var, and validates the write path against that role's
declared-output paths. Exits 0 on allow, non-zero on deny (with stderr).

No-op when AGENT_ROLE is unset (non-compressed execution).
"""
import json
import os
import sys


def main() -> int:
    role = os.environ.get("AGENT_ROLE")
    if not role:
        return 0  # no-op when not dispatched under a role
    # Role-specific enforcement implemented in later tasks.
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Make executable and verify test passes**

```bash
chmod +x checks/role_guard.py
uv run pytest tests/unit/test_role_guard.py::test_no_agent_role_env_is_noop -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add checks/role_guard.py tests/unit/test_role_guard.py
git commit -m "feat: scaffold role_guard.py with no-op default"
```

---

## Task 2 — role_guard.py declared-outputs table + role enforcement

**Files:**
- Modify: `checks/role_guard.py`
- Test: `tests/unit/test_role_guard.py`

**Step 1: Write failing tests for each role's write-path rules**

Append to `tests/unit/test_role_guard.py`:

```python
def test_phase1_writer_allowed_intent_write():
    exit_code, _ = run_guard(
        env_role="phase-1-writer",
        tool_input={"tool_name": "Write", "tool_input": {"file_path": ".claude/current-slice/intent.md"}},
    )
    assert exit_code == 0


def test_phase1_writer_denied_src_write():
    exit_code, stderr = run_guard(
        env_role="phase-1-writer",
        tool_input={"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
    )
    assert exit_code != 0
    assert "phase-1-writer" in stderr.lower()


def test_phase2_skeptic_allowed_test_write():
    exit_code, _ = run_guard(
        env_role="phase-2-skeptic",
        tool_input={"tool_name": "Write", "tool_input": {"file_path": "tests/unit/test_foo.py"}},
    )
    assert exit_code == 0


def test_phase2_skeptic_denied_intent_edit():
    """F1 prevention: Phase 2 cannot edit intent.md."""
    exit_code, stderr = run_guard(
        env_role="phase-2-skeptic",
        tool_input={"tool_name": "Edit", "tool_input": {"file_path": ".claude/current-slice/intent.md"}},
    )
    assert exit_code != 0


def test_phase3_implementer_denied_intent_edit():
    """F1 prevention (primary): Phase 3 cannot edit intent.md."""
    exit_code, stderr = run_guard(
        env_role="phase-3-implementer",
        tool_input={"tool_name": "Edit", "tool_input": {"file_path": ".claude/current-slice/intent.md"}},
    )
    assert exit_code != 0
    assert "intent" in stderr.lower()


def test_phase4_integrator_allowed_sweep_notes():
    """D2 support: Phase 4 must be able to write sweep-notes.md."""
    exit_code, _ = run_guard(
        env_role="phase-4-integrator",
        tool_input={"tool_name": "Write", "tool_input": {"file_path": ".claude/current-slice/integration/sweep-notes.md"}},
    )
    assert exit_code == 0


def test_unknown_role_denies_by_default():
    exit_code, stderr = run_guard(
        env_role="made-up-role",
        tool_input={"tool_name": "Write", "tool_input": {"file_path": "anywhere.py"}},
    )
    assert exit_code != 0
    assert "unknown role" in stderr.lower()
```

**Step 2: Run tests, verify failures**

```bash
uv run pytest tests/unit/test_role_guard.py -v
```

Expected: 6 new tests FAIL (only no-op test passes).

**Step 3: Implement role enforcement**

Replace `checks/role_guard.py` body:

```python
#!/usr/bin/env python3
"""Role-scoped write-path enforcement hook."""
import json
import os
import re
import sys
from typing import TypedDict


class RolePolicy(TypedDict):
    allow_patterns: list[str]  # regex patterns; match = allow
    deny_message: str


ROLE_POLICIES: dict[str, RolePolicy] = {
    "phase-1-writer": {
        "allow_patterns": [
            r"^\.claude/current-slice/intent\.md$",
            r"^\.claude/current-slice/slice\.yaml$",
            r"^\.claude/features/[^/]+\.yaml$",
        ],
        "deny_message": "phase-1-writer may only write intent.md, slice.yaml, feature files",
    },
    "phase-2-skeptic": {
        "allow_patterns": [
            r"^tests/",
            r"^\.claude/current-slice/validation/",
        ],
        "deny_message": "phase-2-skeptic may only write under tests/ or validation/",
    },
    "phase-3-implementer": {
        "allow_patterns": [
            # Envelope paths supplied via AGENT_ENVELOPE env var (colon-separated)
        ],
        "deny_message": "phase-3-implementer may only write envelope paths",
    },
    "phase-4-integrator": {
        "allow_patterns": [
            r"^\.claude/current-slice/integration/",
            r"^\.claude/current-slice/handoff-phase-\d+\.md$",
            r"^\.claude/handoff\.md$",
            r"^\.claude/current-slice/slice\.yaml$",
            r"^\.claude/sweep\.yaml$",
        ],
        "deny_message": "phase-4-integrator may only write integration/, handoffs, sweep.yaml",
    },
}


def check_phase3_envelope(path: str) -> bool:
    """Phase 3 allowed-paths come from AGENT_ENVELOPE env var."""
    envelope_spec = os.environ.get("AGENT_ENVELOPE", "")
    if not envelope_spec:
        return False
    patterns = envelope_spec.split(":")
    return any(re.match(p, path) for p in patterns if p)


def is_write_tool(tool_name: str) -> bool:
    return tool_name in {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def main() -> int:
    role = os.environ.get("AGENT_ROLE")
    if not role:
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(f"role_guard: could not parse stdin JSON", file=sys.stderr)
        return 2

    tool_name = payload.get("tool_name", "")
    if not is_write_tool(tool_name):
        return 0  # reads, bash, etc. not guarded by this hook

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0

    if role == "phase-3-implementer":
        if check_phase3_envelope(file_path):
            return 0
        print(
            f"role_guard: phase-3-implementer write to '{file_path}' outside envelope",
            file=sys.stderr,
        )
        return 1

    policy = ROLE_POLICIES.get(role)
    if policy is None:
        print(f"role_guard: unknown role '{role}'", file=sys.stderr)
        return 1

    if any(re.match(p, file_path) for p in policy["allow_patterns"]):
        return 0

    print(f"role_guard: {policy['deny_message']}; got '{file_path}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run all tests, verify pass**

```bash
uv run pytest tests/unit/test_role_guard.py -v
```

Expected: all 7 tests PASS.

**Step 5: Commit**

```bash
git add checks/role_guard.py tests/unit/test_role_guard.py
git commit -m "feat: role_guard.py enforces per-role write-path restrictions"
```

---

## Task 3 — Register role_guard.py as a PreToolUse hook

**Files:**
- Modify: `commands/claude-code/settings.json` (or create `commands/claude-code/settings-compression.json` — see design §9)

**Step 1: Inspect current settings.json**

```bash
cat commands/claude-code/settings.json | head -40
```

**Step 2: Decide packaging approach**

Per design §9 open question #1: add to main `settings.json` (simpler) OR separate `settings-compression.json` (cleaner for consumers).

**Decision for Slice A:** add to main `settings.json` for simplicity; mark a TODO to split if downstream consumer conflicts arise.

**Step 3: Add hook entry**

Edit `commands/claude-code/settings.json` to append to the `PreToolUse` hooks array (exact schema — check existing entries first):

```json
{
  "matcher": "Write|Edit|MultiEdit|NotebookEdit",
  "hooks": [
    {"type": "command", "command": "python3 $CLAUDE_PROJECT_DIR/checks/role_guard.py"}
  ]
}
```

**Step 4: Verify hook is registered, no syntax errors**

```bash
python3 -c "import json; json.load(open('commands/claude-code/settings.json'))"
```

Expected: no output (valid JSON).

**Step 5: Manual smoke test**

In a separate Claude Code session or via a simulated invocation:

```bash
AGENT_ROLE=phase-3-implementer AGENT_ENVELOPE="^src/foo\.py$" python3 checks/role_guard.py <<< '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py"}}'
echo "exit: $?"
```

Expected: `exit: 0`.

```bash
AGENT_ROLE=phase-3-implementer AGENT_ENVELOPE="^src/foo\.py$" python3 checks/role_guard.py <<< '{"tool_name":"Write","tool_input":{"file_path":"src/bar.py"}}'
echo "exit: $?"
```

Expected: `exit: 1` with stderr message.

**Step 6: Commit**

```bash
git add commands/claude-code/settings.json
git commit -m "feat: register role_guard.py as PreToolUse hook"
```

---

## Task 4 — Agent definition files (5 files)

Create each agent as a standalone file. Agent markdown body includes system prompt; frontmatter declares `tools`. Exact Claude Code frontmatter schema verified per Pre-Task 0 Step 2.

**Step 1: Create `.claude/agents/phase-1-writer.md`**

Use the system-prompt content from efficiency-program Part 3 §`phase-1-writer` (file: `docs/plans/2026-04-18-efficiency-program/05-part-3-phase-role-agents.md`) as the authoritative content. Frontmatter:

```yaml
---
name: phase-1-writer
description: Phase 1 — intent + envelope authoring. Reads ADRs, ARCHITECTURE, operational-reference. Writes .claude/current-slice/intent.md + slice.yaml + feature file. Forbidden from reading src/ (exception: greenfield public interfaces per prose).
tools: [Read, Write, Edit, Bash, Grep, Glob]
---
```

Body: copy the system-prompt sketch from Part 3 source. Extend with compression-specific contract:

```
Return format (STRUCTURED — must appear verbatim on last line of output):
{"status": "OK|RAISE_ISSUE|FAILED", "commit_hash": "<sha>", "summary": "<=100 words", "proposed_slice_id": "<namespace>/<topic>"}

If RAISE_ISSUE: also commit .claude/current-slice/issues/1-<n>.md before returning.
```

**Step 2: Create `.claude/agents/phase-2-skeptic.md`**

Similar pattern. Source: Part 3 §`phase-2-skeptic`. Frontmatter:

```yaml
---
name: phase-2-skeptic
description: Phase 2 — test authoring + approach.md + coupling-clusters.yaml from intent.md alone. Forbidden from reading src/ (except public interfaces per intent).
tools: [Read, Write, Edit, Bash, Grep, Glob]
---
```

Body: Part 3 content + return format.

**Step 3: Create `.claude/agents/phase-3-implementer.md`**

Source: Part 3 §`phase-3-implementer`. Frontmatter:

```yaml
---
name: phase-3-implementer
description: Phase 3 — code implementation to pass tests. Envelope paths from slice.yaml/coupling-clusters.yaml. Forbidden from modifying tests or writing outside envelope.
tools: [Read, Edit, Write, Bash, Grep, Glob]
---
```

Body: Part 3 content + return format.

**Step 4: Create `.claude/agents/phase-4-integrator.md`**

Source: Part 3 §`phase-4-integrator`. Frontmatter:

```yaml
---
name: phase-4-integrator
description: Phase 4 — integration gate + invariant check + sweep prep + handoff write + slice close. Writes integration/sweep-notes.md (D2 mandatory at close).
tools: [Read, Edit, Write, Bash, Grep, Glob]
---
```

Body: Part 3 content + return format + "you MUST write integration/sweep-notes.md before returning OK".

**Step 5: Create `.claude/agents/issue-triager.md`**

No Part 3 source; new for compression. Frontmatter:

```yaml
---
name: issue-triager
description: Narrow reasoning on RAISE_ISSUE returns. Reads the committed issue artifact + current phase context, decides {ESCALATE_TO_USER, RE_DISPATCH, ABORT}. Read-only.
tools: [Read, Grep, Glob]
---
```

Body (concise):

```
You are the Issue Triager. A phase subagent raised an issue in a compressed slice.
Inputs via CLI args: issue_commit_hash, current_phase, slice_id.

Read:
- git show <issue_commit_hash> — the committed issue artifact
- .claude/current-slice/intent.md (if past Phase 1)
- .claude/current-slice/slice.yaml

Decide ONE action:
1. ESCALATE_TO_USER — issue needs human judgment (ADR amendment, firm-invariant change, scope contested).
2. RE_DISPATCH — previous-phase inputs can be amended to resolve.
3. ABORT — issue reveals the slice is fundamentally wrong.

Return format (verbatim last line):
{"action": "ESCALATE_TO_USER|RE_DISPATCH|ABORT", "target_phase": <int>, "amendment": "<short>", "rationale": "<=50 words"}
```

**Step 6: Verify all agent files parse**

```bash
for f in .claude/agents/*.md; do
  echo "== $f =="
  head -10 "$f"
done
```

Expected: each file's frontmatter block is visible and well-formed.

**Step 7: Smoke-test one agent via `claude -p`**

```bash
cd /tmp && claude -p --agent phase-1-writer "Return a probe response with status OK and commit_hash 0000000 and summary 'probe' and proposed_slice_id 'probe/probe'" 2>&1 | tail -5
```

Expected: output ends with a line parseable as JSON matching the schema. If not, the agent's system prompt needs reinforcement of "structured return on last line."

**Step 8: Commit**

```bash
git add .claude/agents/
git commit -m "feat: add phase-role + issue-triager agent definitions"
```

---

## Task 5 — `slice_orchestrator.py` scaffold + state reading

**Files:**
- Create: `scripts/slice_orchestrator.py`
- Test: `tests/unit/test_slice_orchestrator_state_machine.py`

**Step 1: Write failing test for state reading**

Create `tests/unit/test_slice_orchestrator_state_machine.py`:

```python
"""Tests for scripts/slice_orchestrator.py — state machine."""
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ORCHESTRATOR = Path(__file__).parent.parent.parent / "scripts" / "slice_orchestrator.py"


def test_orchestrator_imports():
    """Smoke: module runs with --help and returns usage."""
    result = subprocess.run(
        ["python3", str(ORCHESTRATOR), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--brief" in result.stdout or "--resume" in result.stdout


def test_read_slice_state_from_yaml(tmp_path):
    """Given a slice.yaml, orchestrator.read_slice_state() returns current phase."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import read_slice_state  # noqa

    slice_yaml = tmp_path / "slice.yaml"
    slice_yaml.write_text(dedent("""\
        id: test/probe
        name: "test"
        status: in-progress
        current_phase: 2
    """))

    state = read_slice_state(slice_yaml)
    assert state["id"] == "test/probe"
    assert state["current_phase"] == 2
    assert state["status"] == "in-progress"
```

**Step 2: Verify tests fail**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: FAIL (file not found).

**Step 3: Create `scripts/slice_orchestrator.py` skeleton**

```python
#!/usr/bin/env python3
"""Compressed-slice orchestrator.

State machine that dispatches role-scoped Claude agents per phase.
Owns phase advancement, handoff-writing, commit reconciliation.
Holds zero cross-phase Claude context.

Usage:
    slice_orchestrator.py --brief "<natural-language description>"
    slice_orchestrator.py --resume

See docs/plans/2026-04-18-slice-compression-protocol-design.md.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict


class SliceState(TypedDict):
    id: str
    name: str
    status: str  # in-progress | complete | aborted
    current_phase: int


def read_slice_state(path: Path) -> SliceState:
    """Read slice.yaml into a typed dict. Simple line-parser (no yaml dep)."""
    text = path.read_text()
    state: dict = {}
    for line in text.splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            v = v.strip().strip('"').strip("'")
            if v.isdigit():
                state[k.strip()] = int(v)
            else:
                state[k.strip()] = v
    return state  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--brief", type=str, help="Natural-language description for a new slice")
    g.add_argument("--resume", action="store_true", help="Resume aborted/in-progress slice")
    parser.add_argument("--legacy", action="store_true", help="Use old serial /start-slice behavior")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.legacy:
        print("Legacy mode: delegate to old /start-slice prose protocol", file=sys.stderr)
        return 0  # Stub for now; legacy dispatch implemented in Task 11.
    if args.resume:
        print("Resume not yet implemented", file=sys.stderr)
        return 2
    # --brief path: TODO Task 6+
    print(f"Would start new slice with brief: {args.brief!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Make executable + rerun tests**

```bash
chmod +x scripts/slice_orchestrator.py
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: both tests PASS.

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py
git commit -m "feat: slice_orchestrator.py scaffold + state reader"
```

---

## Task 6 — Agent dispatch primitive

**Files:**
- Modify: `scripts/slice_orchestrator.py`
- Test: `tests/unit/test_slice_orchestrator_state_machine.py`

**Step 1: Write failing test for dispatch + return parsing**

Append to `tests/unit/test_slice_orchestrator_state_machine.py`:

```python
from unittest.mock import patch, MagicMock


def test_dispatch_parses_structured_return():
    """Orchestrator dispatches claude -p and parses structured return."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import dispatch_agent  # noqa

    fake_stdout = '''Some preamble text...
Committed intent.md successfully.
{"status":"OK","commit_hash":"abc123","summary":"probe done","proposed_slice_id":"test/probe"}
'''
    with patch("slice_orchestrator.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=fake_stdout, returncode=0, stderr=""
        )
        result = dispatch_agent(
            role="phase-1-writer",
            inputs={"brief": "build a widget"},
            envelope=None,
        )

    assert result["status"] == "OK"
    assert result["commit_hash"] == "abc123"
    assert result["proposed_slice_id"] == "test/probe"


def test_dispatch_handles_malformed_return():
    """Malformed JSON tail → treated as FAILED with diagnostic."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import dispatch_agent

    with patch("slice_orchestrator.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="I have no structured output, just prose.",
            returncode=0, stderr=""
        )
        result = dispatch_agent(role="phase-1-writer", inputs={}, envelope=None)

    assert result["status"] == "FAILED"
    assert "malformed" in result["summary"].lower()
```

**Step 2: Verify tests fail**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py::test_dispatch_parses_structured_return -v
```

Expected: FAIL (dispatch_agent not defined).

**Step 3: Implement dispatch_agent**

Append to `scripts/slice_orchestrator.py`:

```python
class AgentReturn(TypedDict, total=False):
    status: str  # OK | RAISE_ISSUE | FAILED
    commit_hash: str
    summary: str
    proposed_slice_id: str
    action: str  # for issue-triager returns


def _parse_last_json_line(stdout: str) -> AgentReturn | None:
    """Extract the last line that is a valid JSON object."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def dispatch_agent(
    role: str,
    inputs: dict,
    envelope: str | None = None,
    timeout_soft: int | None = None,
    timeout_hard: int | None = None,
) -> AgentReturn:
    """Invoke `claude -p --agent <role>` with inputs; parse structured return."""
    timeout_hard = timeout_hard or int(
        os.environ.get(f"CAIRN_PHASE_{role[-1] if role[-1].isdigit() else 'X'}_TIMEOUT_HARD", "1800")
    )

    env = os.environ.copy()
    env["AGENT_ROLE"] = role
    if envelope:
        env["AGENT_ENVELOPE"] = envelope

    prompt = json.dumps(inputs)
    try:
        result = subprocess.run(
            ["claude", "-p", "--agent", role, prompt],
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_hard,
        )
    except subprocess.TimeoutExpired:
        return {"status": "FAILED", "summary": f"{role} hit hard timeout after {timeout_hard}s"}

    parsed = _parse_last_json_line(result.stdout)
    if parsed is None:
        return {
            "status": "FAILED",
            "summary": f"malformed return from {role}: no structured JSON on last line",
        }
    return parsed
```

**Step 4: Run tests, verify pass**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py
git commit -m "feat: dispatch_agent subprocess wrapper + structured return parsing"
```

---

## Task 7 — Phase-by-phase state machine loop

**Files:**
- Modify: `scripts/slice_orchestrator.py`
- Test: same

**Step 1: Write failing tests for OK / RAISE_ISSUE / FAILED routing**

```python
def test_phase_ok_advances_state(tmp_path, monkeypatch):
    """When phase returns OK, orchestrator writes handoff + advances phase."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import run_phase_loop

    # Set up slice worktree
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    slice_yaml = slice_dir / "slice.yaml"
    slice_yaml.write_text("id: t/p\nname: t\nstatus: in-progress\ncurrent_phase: 0\n")

    monkeypatch.chdir(tmp_path)

    with patch("slice_orchestrator.dispatch_agent") as mock_dispatch, \
         patch("slice_orchestrator.commit_phase_handoff") as mock_commit:
        mock_dispatch.return_value = {
            "status": "OK",
            "commit_hash": "abc",
            "summary": "done",
        }

        result = run_phase_loop(max_phase=1)

    assert mock_dispatch.called
    assert mock_commit.called
    assert result == 0


def test_phase_failed_retries_once(tmp_path, monkeypatch):
    """FAILED → orchestrator retries once; second FAILED escalates."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import run_phase_loop

    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    slice_yaml = slice_dir / "slice.yaml"
    slice_yaml.write_text("id: t/p\nname: t\nstatus: in-progress\ncurrent_phase: 0\n")

    monkeypatch.chdir(tmp_path)

    with patch("slice_orchestrator.dispatch_agent") as mock_dispatch:
        mock_dispatch.return_value = {"status": "FAILED", "summary": "broke"}
        result = run_phase_loop(max_phase=1)

    assert mock_dispatch.call_count == 2  # initial + 1 retry
    assert result != 0  # escalated to user
```

**Step 2: Verify tests fail**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: 2 new tests FAIL.

**Step 3: Implement run_phase_loop + commit_phase_handoff**

Append to `scripts/slice_orchestrator.py`:

```python
ROLE_FOR_PHASE = {
    1: "phase-1-writer",
    2: "phase-2-skeptic",
    3: "phase-3-implementer",
    4: "phase-4-integrator",
}


def commit_phase_handoff(phase: int, summary: str, commit_hash: str) -> None:
    """Write .claude/current-slice/handoff-phase-<N>.md and git-commit."""
    handoff_path = Path(f".claude/current-slice/handoff-phase-{phase}.md")
    handoff_path.write_text(
        f"---\nphase: {phase}\ncommit: {commit_hash}\n---\n\n{summary}\n"
    )
    subprocess.run(["git", "add", str(handoff_path)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"handoff: phase {phase} complete"],
        check=True,
    )


def build_phase_inputs(phase: int, slice_id: str) -> dict:
    return {"slice_id": slice_id, "phase": phase}


def run_phase_loop(max_phase: int = 4) -> int:
    """Run phases 1..max_phase. Returns 0 on success, non-zero on escalation."""
    slice_yaml = Path(".claude/current-slice/slice.yaml")
    state = read_slice_state(slice_yaml)
    current = state.get("current_phase", 0)

    phase = current + 1
    while phase <= max_phase:
        role = ROLE_FOR_PHASE[phase]
        retries = 0
        while True:
            result = dispatch_agent(role=role, inputs=build_phase_inputs(phase, state["id"]))
            status = result.get("status")
            if status == "OK":
                commit_phase_handoff(
                    phase, result.get("summary", ""), result.get("commit_hash", "")
                )
                phase += 1
                break
            elif status == "FAILED":
                retries += 1
                if retries >= 2:
                    print(
                        f"phase {phase} failed twice: {result.get('summary')}",
                        file=sys.stderr,
                    )
                    return 2
                # retry silently
                continue
            elif status == "RAISE_ISSUE":
                # TODO Task 8
                print("RAISE_ISSUE handler not yet implemented", file=sys.stderr)
                return 3
            else:
                print(f"unknown status from {role}: {status}", file=sys.stderr)
                return 4
    return 0
```

**Step 4: Run tests, verify pass**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py
git commit -m "feat: slice_orchestrator phase loop + OK/FAILED routing + handoff commit"
```

---

## Task 8 — RAISE_ISSUE handler + issue-triager dispatch

**Files:**
- Modify: `scripts/slice_orchestrator.py`
- Test: same

**Step 1: Write failing tests for RAISE_ISSUE routing**

```python
def test_raise_issue_dispatches_triager(tmp_path, monkeypatch):
    """RAISE_ISSUE return triggers issue-triager dispatch."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import run_phase_loop

    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    slice_yaml = slice_dir / "slice.yaml"
    slice_yaml.write_text("id: t/p\nname: t\nstatus: in-progress\ncurrent_phase: 0\n")
    monkeypatch.chdir(tmp_path)

    with patch("slice_orchestrator.dispatch_agent") as mock_dispatch:
        mock_dispatch.side_effect = [
            {"status": "RAISE_ISSUE", "commit_hash": "iss1", "summary": "stuck"},
            {"action": "ESCALATE_TO_USER", "rationale": "human needed"},
        ]
        result = run_phase_loop(max_phase=1)

    # Expect two dispatches: phase-1-writer + issue-triager
    assert mock_dispatch.call_count == 2
    assert mock_dispatch.call_args_list[1].kwargs["role"] == "issue-triager"
    assert result != 0  # escalated
```

**Step 2: Verify test fails**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py::test_raise_issue_dispatches_triager -v
```

Expected: FAIL.

**Step 3: Implement RAISE_ISSUE handler**

Replace the `RAISE_ISSUE` branch in `run_phase_loop`:

```python
            elif status == "RAISE_ISSUE":
                action_result = dispatch_agent(
                    role="issue-triager",
                    inputs={
                        "issue_commit_hash": result.get("commit_hash", ""),
                        "current_phase": phase,
                        "slice_id": state["id"],
                    },
                )
                action = action_result.get("action")
                if action == "ESCALATE_TO_USER":
                    write_partial_close_handoff(phase, result, action_result)
                    return 3
                elif action == "RE_DISPATCH":
                    target = action_result.get("target_phase", phase - 1)
                    if target < 1:
                        target = 1
                    phase = target
                    continue
                elif action == "ABORT":
                    abort_slice(phase, action_result)
                    return 4
                else:
                    print(f"unknown triager action: {action}", file=sys.stderr)
                    return 5
```

Add stub helpers at module level:

```python
def write_partial_close_handoff(phase: int, issue: AgentReturn, triager: AgentReturn) -> None:
    handoff = Path(".claude/handoff.md")
    handoff.write_text(
        f"---\nstatus: partial-close-escalated\nphase: {phase}\n---\n\n"
        f"Phase {phase} raised an issue requiring user action.\n\n"
        f"Issue: {issue.get('summary', '')}\n\n"
        f"Triager rationale: {triager.get('rationale', '')}\n"
    )
    subprocess.run(["git", "add", str(handoff)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"handoff: phase {phase} partial-close (issue)"],
        check=True,
    )


def abort_slice(phase: int, triager: AgentReturn) -> None:
    slice_yaml = Path(".claude/current-slice/slice.yaml")
    text = slice_yaml.read_text()
    text = text.replace("status: in-progress", "status: aborted")
    slice_yaml.write_text(text)
    subprocess.run(["git", "add", str(slice_yaml)], check=True)
    subprocess.run(["git", "commit", "-m", f"handoff: slice aborted at phase {phase}"], check=True)
```

**Step 4: Run tests, verify pass**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: all tests PASS (with some git-related warnings in mock-heavy tests — acceptable).

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py
git commit -m "feat: slice_orchestrator RAISE_ISSUE + issue-triager handling"
```

---

## Task 9 — Phase 3 parallel fan-out via concurrent.futures

**Files:**
- Modify: `scripts/slice_orchestrator.py`
- Test: same

**Step 1: Write failing test for cluster fan-out**

```python
def test_phase3_dispatches_one_per_cluster(tmp_path, monkeypatch):
    """Phase 3 reads coupling-clusters.yaml and dispatches one agent per cluster."""
    sys.path.insert(0, str(ORCHESTRATOR.parent))
    from slice_orchestrator import dispatch_phase_3

    slice_dir = tmp_path / ".claude" / "current-slice" / "validation"
    slice_dir.mkdir(parents=True)
    (slice_dir / "coupling-clusters.yaml").write_text(
        'clusters:\n'
        '  - name: A\n    files: [src/a.py]\n'
        '  - name: B\n    files: [src/b.py]\n'
        '  - name: C\n    files: [src/c.py]\n'
    )
    monkeypatch.chdir(tmp_path)

    with patch("slice_orchestrator.dispatch_agent") as mock_dispatch:
        mock_dispatch.return_value = {"status": "OK", "commit_hash": "xyz", "summary": "ok"}
        result = dispatch_phase_3(slice_id="t/p")

    assert mock_dispatch.call_count == 3
    assert all(
        call.kwargs["role"] == "phase-3-implementer"
        for call in mock_dispatch.call_args_list
    )
    assert result["status"] == "OK"
```

**Step 2: Verify test fails**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py::test_phase3_dispatches_one_per_cluster -v
```

Expected: FAIL.

**Step 3: Implement dispatch_phase_3**

Append to `scripts/slice_orchestrator.py`:

```python
from concurrent.futures import ThreadPoolExecutor


def read_coupling_clusters() -> list[dict]:
    path = Path(".claude/current-slice/validation/coupling-clusters.yaml")
    if not path.exists():
        # No clusters → single implicit cluster (envelope as a whole)
        return [{"name": "all", "files": []}]
    # Simple line-parser for yaml list-of-dict
    text = path.read_text()
    clusters = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("  - name:"):
            if current:
                clusters.append(current)
            current = {"name": line.split(":", 1)[1].strip().strip('"')}
        elif line.startswith("    files:") and current:
            files_raw = line.split(":", 1)[1].strip()
            if files_raw.startswith("["):
                current["files"] = [
                    f.strip().strip('"').strip("'")
                    for f in files_raw.strip("[]").split(",")
                ]
    if current:
        clusters.append(current)
    return clusters


def dispatch_phase_3(slice_id: str) -> AgentReturn:
    """Dispatch one phase-3-implementer per coupling cluster, in parallel."""
    clusters = read_coupling_clusters()
    with ThreadPoolExecutor(max_workers=min(len(clusters), 8)) as pool:
        futures = [
            pool.submit(
                dispatch_agent,
                role="phase-3-implementer",
                inputs={"slice_id": slice_id, "cluster": c["name"], "files": c["files"]},
                envelope=":".join(c.get("files", [])),
            )
            for c in clusters
        ]
        results = [f.result() for f in futures]

    # Reconcile: all OK → success; any RAISE/FAILED → propagate the worst
    statuses = {r.get("status") for r in results}
    if "RAISE_ISSUE" in statuses:
        raised = next(r for r in results if r.get("status") == "RAISE_ISSUE")
        return raised
    if "FAILED" in statuses:
        failed = next(r for r in results if r.get("status") == "FAILED")
        return failed
    # All OK — synthesize a single OK with concatenated summary
    commits = [r.get("commit_hash", "") for r in results]
    summaries = "; ".join(r.get("summary", "") for r in results)
    return {"status": "OK", "commit_hash": ",".join(commits), "summary": summaries}
```

Update the phase loop to route phase 3 via `dispatch_phase_3`:

```python
# Inside run_phase_loop, replace `result = dispatch_agent(...)` for phase 3:
            if phase == 3:
                result = dispatch_phase_3(slice_id=state["id"])
            else:
                result = dispatch_agent(role=role, inputs=build_phase_inputs(phase, state["id"]))
```

**Step 4: Run tests, verify pass**

```bash
uv run pytest tests/unit/test_slice_orchestrator_state_machine.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py
git commit -m "feat: phase-3 cluster fan-out via concurrent.futures"
```

---

## Task 10 — Slice init + slice-id derivation + final close

**Files:**
- Modify: `scripts/slice_orchestrator.py`
- Test: `tests/unit/test_slice_id_derivation.py` (new)

**Step 1: Write failing test for slice-id derivation**

Create `tests/unit/test_slice_id_derivation.py`:

```python
"""Tests: phase-1-writer proposes a slice-id in namespace/topic format."""
import re


def test_slice_id_shape_regex():
    """Expected shape: <namespace>/<topic-name>, both kebab-case, ASCII."""
    valid_ids = [
        "compression/infrastructure",
        "identifier-scheme/doc-sweep",
        "fleet-coordinator/push-protocol",
    ]
    invalid_ids = [
        "InvalidCaps/foo",
        "compression",  # missing topic
        "compression/",  # empty topic
        "/infrastructure",  # empty namespace
        "compression/infra spaced",  # space
    ]
    pattern = re.compile(r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$")
    for vid in valid_ids:
        assert pattern.match(vid), f"valid id failed: {vid}"
    for iid in invalid_ids:
        assert not pattern.match(iid), f"invalid id matched: {iid}"
```

(Note: this test is about the REGEX that the orchestrator uses to validate phase-1-writer's proposal. The actual proposal logic is in the agent's system prompt, validated mechanically here.)

**Step 2: Verify test passes or implement**

```bash
uv run pytest tests/unit/test_slice_id_derivation.py -v
```

If pass: commit. If fail: fix regex in step 3.

**Step 3: Implement init flow in slice_orchestrator.py**

Append to `scripts/slice_orchestrator.py`:

```python
SLICE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$")


def init_new_slice(brief: str) -> SliceState:
    """Dispatch phase-1-writer (without slice.yaml), create slice.yaml from proposal."""
    # First dispatch: phase-1-writer with brief-only, asking for slice-id proposal.
    result = dispatch_agent(role="phase-1-writer", inputs={"brief": brief, "ask": "propose_slice_id"})
    if result.get("status") != "OK":
        raise SystemExit(f"Phase 1 init failed: {result.get('summary')}")

    proposed_id = result.get("proposed_slice_id", "")
    if not SLICE_ID_PATTERN.match(proposed_id):
        raise SystemExit(f"Phase 1 proposed malformed slice_id: {proposed_id!r}")

    slice_yaml_path = Path(".claude/current-slice/slice.yaml")
    slice_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    slice_yaml_path.write_text(
        f"id: {proposed_id}\n"
        f'name: "{brief[:80]}"\n'
        f"status: in-progress\n"
        f"current_phase: 1\n"
    )
    subprocess.run(["git", "add", str(slice_yaml_path)], check=True)
    subprocess.run(["git", "commit", "-m", f"slice: {proposed_id} — init"], check=True)

    # Phase 1's handoff (commit was the init commit); write handoff file
    commit_phase_handoff(1, result.get("summary", ""), result.get("commit_hash", ""))

    return read_slice_state(slice_yaml_path)


def close_slice(state: SliceState) -> None:
    """Final close: set status=complete; assemble final handoff.md from committed artifacts."""
    slice_yaml = Path(".claude/current-slice/slice.yaml")
    text = slice_yaml.read_text().replace("status: in-progress", "status: complete")
    slice_yaml.write_text(text)

    # Assemble final handoff from phase-handoffs + sweep-notes
    parts = [f"# Slice {state['id']} — complete\n\n"]
    for n in range(1, 5):
        p = Path(f".claude/current-slice/handoff-phase-{n}.md")
        if p.exists():
            parts.append(f"\n## Phase {n}\n\n{p.read_text()}\n")
    sweep = Path(".claude/current-slice/integration/sweep-notes.md")
    if sweep.exists():
        parts.append(f"\n## Sweep notes\n\n{sweep.read_text()}\n")

    Path(".claude/handoff.md").write_text("".join(parts))
    subprocess.run(["git", "add", ".claude/handoff.md", str(slice_yaml)], check=True)
    subprocess.run(["git", "commit", "-m", f"slice: {state['id']} — complete"], check=True)
```

Update `main()` to wire init + loop + close:

```python
def main() -> int:
    args = parse_args()
    if args.legacy:
        return legacy_start_slice()
    if args.resume:
        state = read_slice_state(Path(".claude/current-slice/slice.yaml"))
    else:
        state = init_new_slice(args.brief)
    rc = run_phase_loop(max_phase=4)
    if rc != 0:
        return rc
    close_slice(state)
    return 0


def legacy_start_slice() -> int:
    """Stub: defers to the old prose-based /start-slice. Implemented in Task 11."""
    print("legacy /start-slice not implemented yet", file=sys.stderr)
    return 2
```

**Step 4: Run all unit tests**

```bash
uv run pytest tests/unit/test_slice_id_derivation.py tests/unit/test_slice_orchestrator_state_machine.py tests/unit/test_role_guard.py -v
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add scripts/slice_orchestrator.py tests/unit/test_slice_id_derivation.py
git commit -m "feat: slice init with phase-1-writer id proposal + final close"
```

---

## Task 11 — Thin `/start-slice` refactor + `--legacy` escape hatch

**Files:**
- Modify: `commands/claude-code/start-slice.md`
- (Read-only reference: the current file, preserved as `start-slice-legacy.md`)

**Step 1: Archive current skill as legacy fallback**

```bash
cp commands/claude-code/start-slice.md commands/claude-code/start-slice-legacy.md
```

Edit `start-slice-legacy.md`'s frontmatter so it is not an active `/start-slice` slash command (add `disabled: true` or rename the top heading to indicate archival).

**Step 2: Rewrite `commands/claude-code/start-slice.md` as a thin dispatcher**

Replace content with ~30 lines:

```markdown
# /start-slice

Start or resume a compressed slice via the orchestrator.

Usage:
- `/start-slice` — no args. Detects aborted/in-progress slice and proposes resume; else reads handoff "Next"; else prompts for brief.
- `/start-slice "<brief>"` — new slice with the given brief.
- `/start-slice --legacy` — use the old serial prose-based protocol.

## Protocol

1. If `.claude/current-slice/slice.yaml` exists with `status ∈ {in-progress, aborted}`:
   - Ask user: "Resume slice `<id>`? (y/n)"
   - On yes: invoke `python3 scripts/slice_orchestrator.py --resume`. Done.
2. If args are provided:
   - Pass as `--brief "<args>"` to orchestrator.
3. Else:
   - Read `.claude/handoff.md` "Next" section.
   - If it names an obvious candidate: ask user "Start slice from handoff Next? (y/n/edit)"
   - Else: prompt user for one-sentence brief.
   - Invoke `python3 scripts/slice_orchestrator.py --brief "<brief>"`.

## Legacy mode

If `--legacy` flag is passed, or `CAIRN_LEGACY_START_SLICE=1` is set, load `start-slice-legacy.md` and follow its prose protocol instead of invoking the orchestrator.

Legacy mode is retained until ≥5 clean compressed slices have landed, per compression design doc §10.
```

**Step 3: Implement `legacy_start_slice()` stub**

In `scripts/slice_orchestrator.py`, replace the legacy stub:

```python
def legacy_start_slice() -> int:
    """When --legacy is passed, defer to start-slice-legacy.md prose protocol.

    The orchestrator does not execute legacy prose directly; it prints a
    message telling the user to follow start-slice-legacy.md manually.
    """
    print(
        "Legacy mode requested. Follow commands/claude-code/start-slice-legacy.md manually.",
        file=sys.stderr,
    )
    return 0
```

**Step 4: Verify skill loads (smoke test)**

Open a fresh Claude Code session and run `/start-slice --help` or `/start-slice`. Confirm no parse errors. If errors, debug skill markdown syntax.

**Step 5: Commit**

```bash
git add commands/claude-code/start-slice.md commands/claude-code/start-slice-legacy.md scripts/slice_orchestrator.py
git commit -m "feat: thin /start-slice dispatcher + --legacy escape hatch"
```

---

## Task 12 — Integration dogfood: close Slice A serially, then run Slice B compressed

**Files:**
- This is a behavioral verification, not a code change.

**Step 1: Close Slice A of compression feature serially**

Slice A (this slice) is the compression infrastructure itself. It must close using the OLD serial protocol (because compressed execution depends on the infrastructure it is installing).

Follow `commands/claude-code/start-slice-legacy.md` (or execute the phases manually):

1. **Phase 1:** intent.md already implicit in this plan; create `.claude/current-slice/intent.md` referencing the plan + design doc. Commit.
2. **Phase 2:** tests written in Tasks 1, 6, 7, 8, 9, 10. Verify all pass:

   ```bash
   uv run pytest tests/unit/test_role_guard.py tests/unit/test_slice_orchestrator_state_machine.py tests/unit/test_slice_id_derivation.py -v
   ```

   Expected: all PASS.

3. **Phase 3:** implementation committed in Tasks 2, 4, 5, 6, 7, 8, 9, 10, 11. Verify by running the full test suite:

   ```bash
   uv run pytest tests/unit/ -v
   ```

   Expected: all PASS (new + existing).

4. **Phase 4:** integration. Write `.claude/current-slice/integration/sweep-notes.md` capturing: (a) all audit findings F1/F3/F4/F5 have prevention mechanisms in place; (b) adversarial test passes (phase-3-implementer Edit on intent.md blocked); (c) full test suite green. Commit.

**Step 2: Adversarial test**

```bash
# Set role + write to a forbidden path; verify deny
AGENT_ROLE=phase-3-implementer AGENT_ENVELOPE="^scripts/foo\.py$" python3 checks/role_guard.py <<< '{"tool_name":"Edit","tool_input":{"file_path":".claude/current-slice/intent.md"}}'
echo "exit: $?"
```

Expected: `exit: 1` with stderr.

**Step 3: Close Slice A + commit handoff**

Follow standard serial `/handoff` for Phase 4 → slice close. Close the `compression/infrastructure` slice on `feature/compression`.

**Step 4: Run Slice B (Part 0 ADR) COMPRESSED — the dogfood proof**

On the same branch (or a continuation):

```bash
python3 scripts/slice_orchestrator.py --brief "Part 0 ADR: principles for efficiency program (P1-P6 from part-0-adr-principles.md) + D1/D2/D3 universal phase-artifact discipline (from session-compression audit). Target firmness: firm. Phase 5 independent verification required."
```

**Expected behavior:**
1. Orchestrator dispatches `phase-1-writer` with brief. Agent proposes slice id `compression/part-0-adr-principles` (or similar). Intent.md committed.
2. Orchestrator dispatches `phase-2-skeptic`. Tests + approach.md + coupling-clusters committed. If ADRs are authored without code, coupling-clusters may be empty/single-cluster — acceptable.
3. Orchestrator dispatches `phase-3-implementer` (1 cluster since ADR is a single file). ADR file written + committed.
4. Orchestrator dispatches `phase-4-integrator`. sweep-notes.md written + committed.
5. Slice closes. Final handoff.md assembled from phase artifacts.

**Step 5: Verify audit findings did NOT recur**

Manual audit checklist:

- [ ] **F1:** was intent.md edited after Phase 2 started? Check git log; should see one intent commit, no subsequent edits.
- [ ] **F3:** does `.claude/current-slice/integration/sweep-notes.md` exist at slice close? Check file; should have content.
- [ ] **F4:** do `handoff-phase-1.md` through `handoff-phase-4.md` all exist? Run `scripts/verify_handoff.sh`; should pass.
- [ ] **F5:** is the final handoff.md content traceable to committed artifacts? Check that every claim in handoff.md has a git-show source; no ephemeral references.

If any check fails, the compression infrastructure has a gap. **Escalate to user** with specific finding before merging.

**Step 6: Commit integration evidence**

```bash
git add .claude/current-slice/integration/sweep-notes.md
git commit -m "integration: compression infrastructure dogfood pass"
```

---

## Task 13 — Prepare merge + handoff

**Step 1: Update `.claude/handoff.md`**

Write a comprehensive handoff:

- **State:** `compression/infrastructure` slice complete at commit `<sha>`. `compression/part-0-adr-principles` slice complete at commit `<sha>` via compressed execution. Audit findings F1/F3/F4/F5 prevented by mechanical enforcement.
- **Next:** three audit follow-up slices + Part 1 distillation agents + `commit_handoff.sh` obsolescence (see design §12 Q2).
- **Pointers:** design doc, plan doc, commits.

**Step 2: Push branch**

```bash
git push -u origin feature/compression
```

**Step 3: Open PR to dev**

```bash
gh pr create --base dev --title "feat: slice compression protocol (infrastructure + Part 0 ADR dogfood)" --body "$(cat <<'EOF'
## Summary

- Ships compression infrastructure: `slice_orchestrator.py`, role agents, `role_guard.py` hook, thin `/start-slice`.
- Dogfooded via compressed execution of Part 0 ADR slice.
- Audit findings F1/F3/F4/F5 mechanically prevented.

## Test plan

- [x] All unit tests green (`uv run pytest tests/unit/`)
- [x] Adversarial role_guard test passes (phase-3 blocked from editing intent.md)
- [x] Part 0 ADR slice closed via compressed execution
- [x] Audit findings checklist (F1/F3/F4/F5) verified not recurring
- [ ] Reviewer check: is `--legacy` escape hatch sufficient for rollback?
EOF
)"
```

**Step 4: Wait for review**

Do not merge until:
1. Reviewer confirms audit findings prevention.
2. `complex-rag-analysis` consumer audit confirms no breaking changes (or CAIRN_PHASE_4_TIMEOUT_HARD override is sufficient).
3. At least one other human manually runs `/start-slice` compressed on a trivial slice and reports success.

---

## Out of scope for this plan

- Slice-candidate primitive `.claude/slice-candidates/` — deferred per design §11.
- Full refactor of `/catchup`, `/handoff`, `/integration-sweep` to thin dispatchers — incremental, Part 2/3 scope.
- F6 worker integration — post-F6.
- Windsurf port — separate plan when that port becomes a priority.
- Rust migration — end of v1.
- `commit_handoff.sh` (Part 2 E2) — likely obsolete, but confirmation deferred to a separate slice when `/handoff` next needs changes.

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `claude -p --agent <name>` doesn't behave as design assumes | Medium | Pre-Task 0 probe; adapt dispatch interface or pause design |
| Allowed-tools not mechanically enforced | Medium | Pre-Task 0 probe; fall back to role_guard.py as sole mechanical gate |
| Phase-3 parallel dispatch has race conditions (two implementers writing overlapping paths) | Low | Orchestrator reconciles commits; overlap = Phase 2 bug; raise to user |
| Consumer projects break on settings.json merge | Medium | Ship hook registration as `settings-compression.json` if conflicts arise post-merge |
| `complex-rag-analysis` Phase 4 timeout | High (known) | Ship `CAIRN_PHASE_4_TIMEOUT_HARD` env override in Task 6 |
| Orchestrator crashes mid-phase in a way `--resume` can't recover | Low | Slice.yaml state is durable; fallback to `--legacy` per Task 11 |

## Success criteria

1. All unit tests green on `feature/compression` branch.
2. Slice A (`compression/infrastructure`) closes serially with Phase 4 sweep-notes committed.
3. Slice B (`compression/part-0-adr-principles`) closes via compressed execution.
4. Audit findings F1/F3/F4/F5 verifiably did not recur in Slice B.
5. `--legacy` escape hatch works (can fall back to old protocol).
6. PR to `dev` opened with comprehensive handoff + test plan checklist.

---

## Pointers

- Companion: `docs/plans/2026-04-18-slice-compression-protocol-design.md` — architecture, principles, disposition.
- Audit input: `docs/plans/2026-04-18-session-compression-audit.md`.
- Part 3 source: `docs/plans/2026-04-18-efficiency-program/05-part-3-phase-role-agents.md`.
- Parallelism ADR: `docs/adr/parallelism-v1.md` (D3 legitimacy).
- Fleet coordinator design: `docs/plans/2026-04-15-fleet-coordinator-design.md` (downstream composer).

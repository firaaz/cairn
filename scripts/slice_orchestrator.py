"""Cairn slice orchestrator — Python state machine driving the four-phase pipeline.

Replaces the prose `start-slice` protocol with a deterministic dispatcher that
spawns role-scoped Claude agents (`claude -p --agent <role>`) per phase, parses
their structured-return JSON tail, and routes on `status ∈ {OK, FAILED,
RAISE_ISSUE}`. Phase 3 fans out one agent per cluster declared in
`coupling-clusters.yaml`.

Stdlib only (CLAUDE.md "New code is Python, stdlib-only, function-based").
Timeouts are env-var overridable per CLAUDE.md "no hardcoded timeouts" rule.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

DEBUG_DIR = Path(".claude/orchestrator-debug")

SLICE_ID_REGEX = re.compile(r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$")

ROLE_FOR_PHASE = {
    1: "phase-1-writer",
    2: "phase-2-skeptic",
    3: "phase-3-implementer",
    4: "phase-4-integrator",
}

ROLE_TO_PHASE = {role: phase for phase, role in ROLE_FOR_PHASE.items()}

DEFAULT_TIMEOUT_HARD = 1800

PERMISSION_MODE = "bypassPermissions"

VALID_TRIAGER_ACTIONS = {"ESCALATE_TO_USER", "RE_DISPATCH", "ABORT"}

SLICE_YAML = Path(".claude/current-slice/slice.yaml")
CLUSTERS_YAML = Path(".claude/current-slice/validation/coupling-clusters.yaml")


def is_valid_slice_id(s):
    if not isinstance(s, str):
        return False
    return SLICE_ID_REGEX.fullmatch(s) is not None


def read_slice_state(path):
    state = {}
    text = Path(path).read_text()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'") and len(value) >= 2:
            value = value[1:-1]
        if key == "current_phase":
            try:
                value = int(value)
            except (ValueError, TypeError):
                pass
        state[key] = value
    return state


def _resolve_timeout(role, override):
    if override is not None:
        return override
    phase = ROLE_TO_PHASE.get(role)
    if phase is None:
        return int(
            os.environ.get(
                "CAIRN_PHASE_DEFAULT_TIMEOUT_HARD", str(DEFAULT_TIMEOUT_HARD)
            )
        )
    return int(
        os.environ.get(f"CAIRN_PHASE_{phase}_TIMEOUT_HARD", str(DEFAULT_TIMEOUT_HARD))
    )


def _parse_structured_tail(stdout):
    if not stdout:
        return None
    lines = stdout.splitlines()
    for raw in reversed(lines):
        line = raw.strip()
        if not line:
            continue
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    last_close = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].rstrip().endswith("}"):
            last_close = i
            break
    if last_close < 0:
        return None
    depth = 0
    start = -1
    for j in range(last_close, -1, -1):
        seg = lines[j]
        depth += seg.count("}") - seg.count("{")
        if depth == 0 and "{" in seg:
            start = j
            break
    if start < 0:
        return None
    candidate = "\n".join(lines[start : last_close + 1])
    brace = candidate.find("{")
    if brace > 0:
        candidate = candidate[brace:]
    try:
        obj = json.loads(candidate)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _slice_id_slug(slice_id):
    return (slice_id or "unknown-unknown").replace("/", "-")


def _utc_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_phase_log(
    slice_id, phase, role, stderr_text, stdout_text="", inputs=None, reason=""
):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slice_id_slug(slice_id)
    phase_token = phase if phase is not None else "x"
    path = DEBUG_DIR / f"{slug}-phase-{phase_token}-{role}-{_utc_timestamp()}.log"
    parts = []
    if reason:
        parts.append(f"reason: {reason}")
    parts.append(f"role: {role}")
    parts.append(f"slice_id: {slice_id}")
    parts.append(f"phase: {phase_token}")
    if inputs is not None:
        parts.append(f"inputs: {json.dumps(inputs)}")
    if stdout_text:
        parts.append("--- stdout ---")
        parts.append(stdout_text)
    parts.append("--- stderr ---")
    parts.append(stderr_text or "")
    path.write_text("\n".join(parts) + "\n")
    if reason:
        print(f"orchestrator: agent failure logged to {path}", file=sys.stderr)
    return path


def _run_with_live_stderr(cmd, env, timeout, prefix=""):
    """Popen with stderr tee'd live to sys.stderr (prefixed) + buffered for capture."""
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
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
            try:
                src.close()
            except Exception:
                pass

    t_out = threading.Thread(
        target=pump, args=(proc.stdout, None, stdout_buf, ""), daemon=True
    )
    t_err = threading.Thread(
        target=pump, args=(proc.stderr, sys.stderr, stderr_buf, prefix), daemon=True
    )
    t_out.start()
    t_err.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        t_out.join(timeout=2)
        t_err.join(timeout=2)
        raise subprocess.TimeoutExpired(
            cmd,
            timeout,
            output="".join(stdout_buf),
            stderr="".join(stderr_buf),
        )
    t_out.join(timeout=2)
    t_err.join(timeout=2)
    return subprocess.CompletedProcess(
        cmd,
        proc.returncode,
        stdout="".join(stdout_buf),
        stderr="".join(stderr_buf),
    )


def _resolve_phase_and_slice(role, inputs):
    phase = None
    slice_id = None
    if isinstance(inputs, dict):
        phase = inputs.get("phase")
        slice_id = inputs.get("slice_id")
    if phase is None:
        phase = ROLE_TO_PHASE.get(role)
    if not slice_id:
        slice_id = _slice_id()
    return phase, slice_id


def dispatch_phase_agent(role, inputs, envelope=None, timeout_hard=None):
    env = os.environ.copy()
    env["AGENT_ROLE"] = role
    if envelope is not None:
        env["AGENT_ENVELOPE"] = envelope
    timeout = _resolve_timeout(role, timeout_hard)
    phase, slice_id = _resolve_phase_and_slice(role, inputs)
    prefix = (
        f"[phase-{phase}-{role}|{slice_id}] "
        if phase is not None
        else f"[{role}|{slice_id}] "
    )
    cmd = [
        "claude",
        "-p",
        "--agent",
        role,
        "--permission-mode",
        PERMISSION_MODE,
        json.dumps(inputs),
    ]
    try:
        proc = _run_with_live_stderr(cmd, env, timeout, prefix=prefix)
    except subprocess.TimeoutExpired as exc:
        stdout_txt = exc.output or ""
        stderr_txt = exc.stderr or ""
        _write_phase_log(
            slice_id,
            phase,
            role,
            stderr_txt,
            stdout_txt,
            inputs=inputs,
            reason=f"timeout after {timeout}s",
        )
        return {
            "status": "FAILED",
            "summary": f"timeout after {timeout}s",
            "commit_hash": "",
        }

    obj = _parse_structured_tail(proc.stdout or "")
    reason = ""
    if obj is None:
        reason = "malformed agent output (no JSON-object tail)"
    elif "status" not in obj:
        reason = "agent output missing required `status` field"
    elif obj.get("status") != "OK":
        reason = (
            f"agent self-reported status={obj.get('status')!r} "
            f"summary={obj.get('summary', '')!r}"
        )
    _write_phase_log(
        slice_id,
        phase,
        role,
        proc.stderr or "",
        proc.stdout or "",
        inputs=inputs,
        reason=reason,
    )
    if obj is None:
        return {
            "status": "FAILED",
            "summary": "malformed agent output (no JSON-object tail)",
            "commit_hash": "",
        }
    if "status" not in obj:
        return {
            "status": "FAILED",
            "summary": "agent output missing required `status` field",
            "commit_hash": "",
        }
    return obj


def dispatch_triager(issue_hash, phase, slice_id, timeout_hard=None):
    env = os.environ.copy()
    env["AGENT_ROLE"] = "issue-triager"
    timeout = _resolve_timeout("issue-triager", timeout_hard)
    inputs = {
        "issue_commit_hash": issue_hash,
        "current_phase": phase,
        "slice_id": slice_id,
    }
    prefix = f"[triager|{slice_id}] "
    cmd = [
        "claude",
        "-p",
        "--agent",
        "issue-triager",
        "--permission-mode",
        PERMISSION_MODE,
        json.dumps(inputs),
    ]
    try:
        proc = _run_with_live_stderr(cmd, env, timeout, prefix=prefix)
    except subprocess.TimeoutExpired:
        return {
            "action": "ESCALATE_TO_USER",
            "target_phase": phase,
            "rationale": f"triager timeout after {timeout}s",
        }
    obj = _parse_structured_tail(proc.stdout or "")
    if obj is None:
        return {
            "action": "ESCALATE_TO_USER",
            "target_phase": phase,
            "rationale": "malformed triager output (no JSON-object tail)",
        }
    action = obj.get("action", "")
    if action not in VALID_TRIAGER_ACTIONS:
        return {
            "action": "ESCALATE_TO_USER",
            "target_phase": phase,
            "rationale": f"triager returned invalid action {action!r}",
        }
    return obj


def _parse_clusters(text):
    clusters = []
    current = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- name:"):
            if current is not None:
                clusters.append(current)
            name = stripped.split(":", 1)[1].strip()
            current = {"name": name, "files": []}
        elif stripped.startswith("files:") and current is not None:
            value = stripped.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1]
                items = [
                    item.strip().strip('"').strip("'")
                    for item in inner.split(",")
                    if item.strip()
                ]
                current["files"] = items
    if current is not None:
        clusters.append(current)
    return clusters


def dispatch_phase_3(slice_id):
    if CLUSTERS_YAML.exists():
        clusters = _parse_clusters(CLUSTERS_YAML.read_text())
    else:
        clusters = []
    if not clusters:
        clusters = [{"name": "implicit", "files": []}]

    workers = min(len(clusters), 8)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for cluster in clusters:
            envelope = ":".join(cluster["files"]) if cluster["files"] else ""
            inputs = {
                "phase": 3,
                "role": "phase-3-implementer",
                "slice_id": slice_id,
                "cluster": cluster["name"],
            }
            futures.append(
                pool.submit(
                    dispatch_phase_agent,
                    "phase-3-implementer",
                    inputs,
                    envelope,
                )
            )
        results = [f.result() for f in futures]

    for r in results:
        if r.get("status") == "RAISE_ISSUE":
            return r
    for r in results:
        if r.get("status") == "FAILED":
            return r
    return {
        "status": "OK",
        "commit_hash": ",".join(r.get("commit_hash", "") for r in results),
        "summary": "; ".join(r.get("summary", "") for r in results),
    }


def commit_phase_handoff(phase, summary, commit_hash):
    path = Path(f".claude/current-slice/handoff-phase-{phase}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"---\nphase: {phase}\ncommit: {commit_hash}\n---\n\n{summary}\n"
    path.write_text(body)
    subprocess.run(["git", "add", str(path)], check=False)
    subprocess.run(
        ["git", "commit", "-m", f"handoff: phase {phase} complete"],
        check=False,
    )


def _current_phase():
    if not SLICE_YAML.exists():
        return 1
    try:
        state = read_slice_state(SLICE_YAML)
        value = state.get("current_phase", 1)
        return int(value) if value is not None else 1
    except (ValueError, OSError, TypeError):
        return 1


def _slice_id():
    if not SLICE_YAML.exists():
        return "unknown/unknown"
    try:
        state = read_slice_state(SLICE_YAML)
        return state.get("id", "unknown/unknown")
    except (OSError, ValueError):
        return "unknown/unknown"


def _slice_brief():
    if not SLICE_YAML.exists():
        return ""
    try:
        state = read_slice_state(SLICE_YAML)
        return state.get("brief", "") or ""
    except (OSError, ValueError):
        return ""


def _dispatch_for_phase(phase, role, inputs, envelope, timeout):
    if phase == 3:
        return dispatch_phase_3(_slice_id())
    return dispatch_phase_agent(role, inputs, envelope, timeout)


def run_phase_loop(max_phase=4):
    phase = _current_phase()
    while 1 <= phase <= max_phase:
        role = ROLE_FOR_PHASE[phase]
        inputs = {"phase": phase, "role": role, "slice_id": _slice_id()}
        brief = _slice_brief()
        if brief:
            inputs["brief"] = brief
        envelope = None
        timeout = _resolve_timeout(role, None)
        result = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
        status = result.get("status", "")

        if status == "OK":
            commit_phase_handoff(
                phase, result.get("summary", ""), result.get("commit_hash", "")
            )
            phase += 1
            continue

        if status == "FAILED":
            retry = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
            if retry.get("status") == "OK":
                commit_phase_handoff(
                    phase,
                    retry.get("summary", ""),
                    retry.get("commit_hash", ""),
                )
                phase += 1
                continue
            print(
                f"orchestrator: phase {phase} failed twice; escalating",
                file=sys.stderr,
            )
            return 1

        if status == "RAISE_ISSUE":
            triager = dispatch_triager(
                issue_hash=result.get("commit_hash", ""),
                phase=phase,
                slice_id=_slice_id(),
            )
            action = triager.get("action", "")
            if action == "ESCALATE_TO_USER":
                print(
                    "orchestrator: triager escalated to user",
                    file=sys.stderr,
                )
                return 1
            if action == "RE_DISPATCH":
                target = triager.get("target_phase")
                if not isinstance(target, int) or not (1 <= target <= max_phase):
                    print(
                        f"orchestrator: invalid target_phase {target!r}; aborting",
                        file=sys.stderr,
                    )
                    return 1
                phase = target
                continue
            if action == "ABORT":
                _abort_slice()
                return 1
            print(
                f"orchestrator: triager returned unknown action {action!r}",
                file=sys.stderr,
            )
            return 1

        print(
            f"orchestrator: phase {phase} returned unknown status {status!r}",
            file=sys.stderr,
        )
        return 1

    if SLICE_YAML.exists():
        try:
            close_slice(read_slice_state(SLICE_YAML))
        except (OSError, ValueError) as exc:
            print(
                f"orchestrator: close_slice failed: {exc}",
                file=sys.stderr,
            )
            return 1
    return 0


def _abort_slice():
    if not SLICE_YAML.exists():
        return
    text = SLICE_YAML.read_text()
    new_lines = []
    saw_status = False
    for line in text.splitlines():
        if line.startswith("status:"):
            new_lines.append("status: aborted")
            saw_status = True
        else:
            new_lines.append(line)
    if not saw_status:
        new_lines.append("status: aborted")
    SLICE_YAML.write_text("\n".join(new_lines) + "\n")
    subprocess.run(["git", "add", str(SLICE_YAML)], check=False)
    subprocess.run(["git", "commit", "-m", "slice: aborted by triager"], check=False)


def init_new_slice(brief):
    result = dispatch_phase_agent(
        "phase-1-writer",
        {
            "phase": 1,
            "role": "phase-1-writer",
            "slice_id": "unknown/unknown",
            "brief": brief,
            "ask": "propose_slice_id",
        },
    )
    proposed = result.get("proposed_slice_id", "")
    if not is_valid_slice_id(proposed):
        raise SystemExit(f"init_new_slice: malformed proposed_slice_id: {proposed!r}")
    SLICE_YAML.parent.mkdir(parents=True, exist_ok=True)
    SLICE_YAML.write_text(
        f'id: {proposed}\nname: "{proposed}"\nstatus: in-progress\n'
        f'current_phase: 1\nbrief: "{brief}"\n'
    )
    subprocess.run(["git", "add", str(SLICE_YAML)], check=False)
    subprocess.run(["git", "commit", "-m", f"slice: {proposed} — init"], check=False)
    return read_slice_state(SLICE_YAML)


def close_slice(state):
    SLICE_YAML.write_text(
        f"id: {state.get('id', 'unknown/unknown')}\n"
        f'name: "{state.get("name", "")}"\nstatus: complete\n'
        f"current_phase: 4\n"
    )
    handoff = Path(".claude/handoff.md")
    parts = []
    for n in range(1, 5):
        p = Path(f".claude/current-slice/handoff-phase-{n}.md")
        if p.exists():
            parts.append(p.read_text())
    sweep = Path(".claude/current-slice/integration/sweep-notes.md")
    if sweep.exists():
        parts.append(sweep.read_text())
    handoff.write_text("\n---\n".join(parts) if parts else "")
    subprocess.run(["git", "add", str(SLICE_YAML), str(handoff)], check=False)
    subprocess.run(["git", "commit", "-m", "slice: complete"], check=False)


def legacy_start_slice():
    print(
        "orchestrator: --legacy invoked; follow commands/claude-code/start-slice-legacy.md "
        "manually for the prose-protocol path."
    )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cairn slice orchestrator — phase-by-phase agent dispatcher."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--brief",
        type=str,
        help="Brief text for a new slice (Phase 1 will derive an id from it).",
    )
    group.add_argument(
        "--resume",
        action="store_true",
        help="Resume the current slice from .claude/current-slice/slice.yaml.",
    )
    group.add_argument(
        "--legacy",
        action="store_true",
        help="Defer to commands/claude-code/start-slice-legacy.md (prose protocol).",
    )
    args = parser.parse_args(argv)

    if args.legacy:
        return legacy_start_slice()
    if args.brief:
        init_new_slice(args.brief)
    return run_phase_loop()


if __name__ == "__main__":
    sys.exit(main())

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

PERMISSION_MODE = "acceptEdits"

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
    for raw in reversed(stdout.splitlines()):
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
    return None


def _write_failure_log(role, inputs, returncode, stdout, stderr, reason):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    path = DEBUG_DIR / f"{ts}-{role}.log"
    body = (
        f"reason: {reason}\n"
        f"role: {role}\n"
        f"returncode: {returncode}\n"
        f"inputs: {json.dumps(inputs)}\n"
        f"--- stdout ---\n{stdout}\n"
        f"--- stderr ---\n{stderr}\n"
    )
    path.write_text(body)
    print(f"orchestrator: agent failure logged to {path}", file=sys.stderr)
    return path


def dispatch_agent(role, inputs, envelope=None, timeout_hard=None):
    env = os.environ.copy()
    env["AGENT_ROLE"] = role
    if envelope is not None:
        env["AGENT_ENVELOPE"] = envelope
    timeout = _resolve_timeout(role, timeout_hard)
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
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _write_failure_log(
            role,
            inputs,
            returncode="timeout",
            stdout=(exc.stdout or b"").decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or ""),
            stderr=(exc.stderr or b"").decode(errors="replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or ""),
            reason=f"timeout after {timeout}s",
        )
        return {
            "status": "FAILED",
            "summary": f"timeout after {timeout}s",
            "commit_hash": "",
        }
    obj = _parse_structured_tail(proc.stdout or "")
    if obj is None:
        _write_failure_log(
            role,
            inputs,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            reason="malformed agent output (no JSON-object tail)",
        )
        return {
            "status": "FAILED",
            "summary": "malformed agent output (no JSON-object tail)",
            "commit_hash": "",
        }
    if obj.get("status") != "OK":
        _write_failure_log(
            role,
            inputs,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            reason=f"agent self-reported status={obj.get('status')!r} summary={obj.get('summary', '')!r}",
        )
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
            inputs = {"slice_id": slice_id, "cluster": cluster["name"]}
            futures.append(
                pool.submit(
                    dispatch_agent,
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
    return dispatch_agent(role, inputs, envelope, timeout)


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
            triager = dispatch_agent(
                "issue-triager",
                {
                    "issue_commit_hash": result.get("commit_hash", ""),
                    "current_phase": phase,
                    "slice_id": _slice_id(),
                },
                None,
                _resolve_timeout("issue-triager", None),
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
    result = dispatch_agent(
        "phase-1-writer", {"brief": brief, "ask": "propose_slice_id"}
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

"""Cairn slice orchestrator — Python state machine driving the four-phase pipeline.

Replaces the prose `start-slice` protocol with a deterministic dispatcher that
spawns role-scoped Claude agents (`claude -p --agent <role>`) per phase, parses
their structured-return JSON tail, and routes on `status ∈ {OK, FAILED,
RAISE_ISSUE}`. Phase 3 fans out one agent per cluster declared in
`clusters.yaml`.

Slice 2 hardening: PyYAML round-trip serialization, `_git` helper with
check=True, signal handlers, RE_DISPATCH persistence + cap, post-timeout
HEAD reconciliation, per-cluster logs, FAILED classification + backoff,
malformed-yaml exits.
"""

from __future__ import annotations

import argparse
import atexit
import concurrent.futures
import datetime
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import yaml

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
CLUSTERS_YAML = Path(".claude/current-slice/clusters.yaml")
CLUSTERS_YAML_LEGACY = Path(".claude/current-slice/validation/coupling-clusters.yaml")
INTENT_MD = Path(".claude/current-slice/intent.md")

TRANSIENT_STDERR_RX = re.compile(
    r"rate\s*limit|overloaded|\b429\b|\b503\b", re.IGNORECASE
)

_active_child = None


def is_valid_slice_id(s):
    if not isinstance(s, str):
        return False
    return SLICE_ID_REGEX.fullmatch(s) is not None


def _normalize_slice_id(s):
    """B3: collapse dotted version suffixes into the hyphenated canonical form.

    Writers sometimes propose ids like `housekeeping/foo-1.2.3` (reading the
    version literal off a brief); `SLICE_ID_REGEX` stays strict on hyphens, so
    we rewrite dots to hyphens before validation. Non-string inputs pass
    through unchanged so the caller's own type check still fires.
    """
    if not isinstance(s, str):
        return s
    return s.replace(".", "-")


def _git(*args, **kwargs):
    """Run a git subcommand with check=True and re-attach stderr on failure.

    B11: single choke-point so no orchestrator call site silently advances on
    a failed git operation.
    """
    cmd = ["git", *args]
    kwargs.setdefault("check", True)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as exc:
        orig = exc.stderr or ""
        if orig:
            exc.args = (f"{exc.args[0] if exc.args else exc}: {orig}",)
        raise


def _read_slice_state_strict():
    """Read slice.yaml via PyYAML; SystemExit(1) on malformed. B12."""
    if not SLICE_YAML.exists():
        return {}
    text = Path(SLICE_YAML).read_text()
    try:
        state = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        print(
            f"orchestrator: malformed slice.yaml at {SLICE_YAML}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if state is None:
        return {}
    if not isinstance(state, dict):
        print(
            f"orchestrator: malformed slice.yaml at {SLICE_YAML}: "
            f"top-level is {type(state).__name__}, expected mapping",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return state


def read_slice_state(path):
    """Public read helper — used by init flow and tests. B3/B4."""
    text = Path(path).read_text()
    state = yaml.safe_load(text)
    if not isinstance(state, dict):
        return {}
    return state


def _write_slice_state(state):
    SLICE_YAML.write_text(
        yaml.safe_dump(state, default_flow_style=False, sort_keys=False)
    )


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
        line = raw.strip().strip("`").strip()
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
        if lines[i].rstrip().rstrip("`").rstrip().endswith("}"):
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


def _iso_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Observability state machine (Slice 3: INV-008 + orchestrator-observability) ---

NON_TERMINAL_STATUS = frozenset({"IN_PROGRESS", "DEGRADED"})
TERMINAL_STATUS = frozenset({"OK", "FAILED", "ABORTED", "ESCALATED", "SIGNALED"})
STATUS_VALUES = frozenset(NON_TERMINAL_STATUS | TERMINAL_STATUS)

DEFAULT_HEARTBEAT_INTERVAL = 10.0
DEFAULT_HEARTBEAT_STALE = 30.0

_state: dict = {}


def _default_observability_errors():
    return {
        "persist_state": 0,
        "write_result_md": 0,
        "append_index": 0,
        "heartbeat": 0,
    }


def _init_state_dict(slice_id):
    """Reset the module-level state dict to schema v1.0 fresh defaults."""
    _state.clear()
    _state.update(
        {
            "schema_version": "1.0",
            "slice_id": slice_id,
            "worktree_path": str(Path.cwd()),
            "orchestrator_pid": os.getpid(),
            "started_at": _iso_now(),
            "ended_at": None,
            "status": "IN_PROGRESS",
            "exit_code": None,
            "current_phase": 1,
            "phases_completed": [],
            "phase_timings": {},
            "retries_by_phase": {},
            "cluster_dispatches": [],
            "degradation_reason": None,
            "observability_errors": _default_observability_errors(),
            "final_commit": "",
            "summary": "",
        }
    )
    return _state


def _update_state(**fields):
    """Merge fields into the module-level state dict.

    D7 append-preservation: `degradation_reason` is never overwritten with None
    once it has been set; callers that need to clear it must assign directly.
    """
    for key, value in fields.items():
        if key == "degradation_reason" and value is None and _state.get(key):
            continue
        _state[key] = value


def _observability_paths(slice_id):
    """Return the four per-slice observability artifact paths (DC-7 slug-keyed)."""
    slug = _slice_id_slug(slice_id)
    return {
        "result_json": DEBUG_DIR / f"{slug}-result.json",
        "result_md": DEBUG_DIR / f"{slug}-result.md",
        "index_jsonl": DEBUG_DIR / "index.jsonl",
        "heartbeat": Path(".claude/current-slice/.heartbeat"),
    }


def _atomic_write(path, content):
    """Tempfile + os.rename atomic write. One retry with no delay on OSError."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    last_err = None
    for _ in range(2):
        try:
            tmp.write_text(content)
            os.rename(str(tmp), str(target))
            return
        except OSError as exc:
            last_err = exc
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
            continue
    assert last_err is not None
    raise last_err


def _persist_state(state):
    """Write state to <slug>-result.json atomically. D6 three-level error policy.

    DC-7 tripwire: if the target already exists with a mismatched slice_id,
    emit a loud stderr and sys.exit(1) rather than overwrite cross-slice data.
    """
    slice_id = state.get("slice_id") or "unknown/unknown"
    paths = _observability_paths(slice_id)
    target = Path(paths["result_json"])

    if target.exists():
        try:
            existing = json.loads(target.read_text())
        except (OSError, ValueError):
            existing = None
        if isinstance(existing, dict):
            existing_id = existing.get("slice_id")
            if existing_id and existing_id != slice_id:
                print(
                    f"orchestrator: slug collision on {target.name!s} — "
                    f"existing slice_id={existing_id!r} mismatches current "
                    f"slice_id={slice_id!r}; refusing to overwrite",
                    file=sys.stderr,
                )
                sys.exit(1)

    try:
        _atomic_write(target, json.dumps(state, indent=2, default=str))
        return
    except OSError as exc:
        errors = state.setdefault(
            "observability_errors", _default_observability_errors()
        )
        errors["persist_state"] = errors.get("persist_state", 0) + 1
        state["status"] = "DEGRADED"
        if not state.get("degradation_reason"):
            state["degradation_reason"] = f"persist_state: {exc}"
        print(
            f"orchestrator: persist_state write exhausted retry, "
            f"entering DEGRADED: {exc}",
            file=sys.stderr,
        )
        try:
            _atomic_write(target, json.dumps(state, indent=2, default=str))
        except OSError as exc2:
            print(
                f"orchestrator: observability fully unwritable; cannot continue: {exc2}",
                file=sys.stderr,
            )
            sys.exit(1)


def _generate_result_md(state):
    """Pure function: JSON state → human-readable markdown sidecar (D2)."""
    slice_id = state.get("slice_id", "")
    status = state.get("status", "")
    exit_code = state.get("exit_code")
    pid = state.get("orchestrator_pid", "")
    worktree = state.get("worktree_path", "")
    started = state.get("started_at", "")
    ended = state.get("ended_at", "")
    final_commit = state.get("final_commit", "")
    summary = state.get("summary", "")
    degradation = state.get("degradation_reason")

    lines = [
        f"# Orchestrator Result — {slice_id}",
        "",
        f"**Status:** {status}",
        f"**Exit code:** {exit_code}",
        f"**Slice:** `{slice_id}`",
        f"**Orchestrator PID:** {pid}",
        f"**Worktree:** `{worktree}`",
        "",
        "## Timeline",
        f"- **Started:** {started}",
        f"- **Ended:**   {ended}",
        "",
        "## Phases",
    ]
    timings = state.get("phase_timings") or {}
    retries = state.get("retries_by_phase") or {}
    completed = set(state.get("phases_completed") or [])
    lines.append("| Phase | Status | Duration (s) | Retries |")
    lines.append("|-------|--------|--------------|---------|")
    for n in (1, 2, 3, 4):
        t = timings.get(str(n)) or timings.get(n) or {}
        dur = t.get("duration_seconds", "")
        ph_status = (
            "OK"
            if n in completed
            else (status if n == state.get("current_phase") else "")
        )
        r = retries.get(str(n)) or retries.get(n) or 0
        lines.append(f"| {n} | {ph_status} | {dur} | {r} |")
    lines.append("")

    clusters = state.get("cluster_dispatches") or []
    if clusters:
        lines.append("## Phase 3 Clusters")
        for c in clusters:
            lines.append(
                f"- `{c.get('cluster', '')}`: {c.get('status', '')} "
                f"(commit `{c.get('commit_hash', '')}`, "
                f"{c.get('duration_seconds', '')}s)"
            )
        lines.append("")

    lines.append("## Final Commit")
    lines.append(f"`{final_commit}`" if final_commit else "_not committed_")
    lines.append("")
    lines.append("## Summary")
    lines.append(summary or "_none_")
    lines.append("")
    lines.append("## Degradation")
    if degradation:
        lines.append(str(degradation))
        errs = state.get("observability_errors") or {}
        for k, v in errs.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def _write_result_md(state):
    """Derive MD from state and atomic-write to <slug>-result.md.

    Close-only cadence per D2: no-op unless state is in a terminal status.
    """
    if state.get("status") not in TERMINAL_STATUS:
        return
    slice_id = state.get("slice_id") or "unknown/unknown"
    paths = _observability_paths(slice_id)
    _atomic_write(Path(paths["result_md"]), _generate_result_md(state))


def _append_index_entry(entry):
    """Append-only JSONL write to .claude/orchestrator-debug/index.jsonl (D7)."""
    slice_id = (entry or {}).get("slice_id") or "unknown/unknown"
    paths = _observability_paths(slice_id)
    idx = Path(paths["index_jsonl"])
    idx.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(entry) + "\n").encode("utf-8")
    fd = os.open(str(idx), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


# --- Heartbeat daemon (DC-2, D9) -------------------------------------------


class _HeartbeatDaemon(threading.Thread):
    """Touches `.heartbeat` with a UTC ISO timestamp every `interval` seconds.

    daemon=True. Self-healing inner loop: transient write errors are logged
    once per error class and do not kill the thread.
    """

    def __init__(self, heartbeat_path, interval=None):
        super().__init__(daemon=True)
        self.heartbeat_path = Path(heartbeat_path)
        if interval is None:
            interval = float(
                os.environ.get(
                    "CAIRN_HEARTBEAT_INTERVAL", str(DEFAULT_HEARTBEAT_INTERVAL)
                )
            )
        self.interval = float(interval)
        self._stop_event = threading.Event()
        self._logged_errors: set = set()

    def run(self):
        try:
            self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        while not self._stop_event.is_set():
            try:
                self.heartbeat_path.write_text(_iso_now())
            except OSError as exc:
                key = type(exc).__name__
                if key not in self._logged_errors:
                    self._logged_errors.add(key)
                    print(
                        f"orchestrator: heartbeat write error ({key}): {exc}",
                        file=sys.stderr,
                    )
            if self._stop_event.wait(timeout=self.interval):
                return

    def stop(self):
        self._stop_event.set()


def _start_heartbeat(hb_path, interval=None):
    daemon = _HeartbeatDaemon(hb_path, interval=interval)
    daemon.start()
    return daemon


def _check_heartbeat_alive(daemon):
    try:
        return bool(daemon.is_alive())
    except Exception:
        return False


def _handle_heartbeat_death(hb_path):
    """One restart attempt; on failure, set status=DEGRADED with reason.

    D6 Level-2 error policy for the heartbeat-thread failure mode.
    """
    new_daemon = _start_heartbeat(hb_path)
    if not _check_heartbeat_alive(new_daemon):
        errors = _state.setdefault(
            "observability_errors", _default_observability_errors()
        )
        errors["heartbeat"] = errors.get("heartbeat", 0) + 1
        _state["status"] = "DEGRADED"
        if not _state.get("degradation_reason"):
            _state["degradation_reason"] = (
                "heartbeat thread died; one restart attempt also dead"
            )
        print(
            "orchestrator: heartbeat thread dead after restart attempt; "
            "entering DEGRADED",
            file=sys.stderr,
        )
    return new_daemon


# --- Lifecycle hardening (INV-008 DC-3/DC-4/DC-5) --------------------------


def _bundle_handoff_md():
    """Concatenate the four phase handoffs (+ sweep-notes) into .claude/handoff.md."""
    handoff = Path(".claude/handoff.md")
    handoff.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for n in range(1, 5):
        p = Path(f".claude/current-slice/handoff-phase-{n}.md")
        if p.exists():
            parts.append(p.read_text())
    sweep = Path(".claude/current-slice/integration/sweep-notes.md")
    if sweep.exists():
        parts.append(sweep.read_text())
    handoff.write_text("\n---\n".join(parts) if parts else "")
    return handoff


def _wipe_current_slice():
    """Delete everything under .claude/current-slice/ except slice.yaml (DC-5).

    - FileNotFoundError is tolerated (F5 operator-rebase corner).
    - Other OSError propagates as RuntimeError.
    """
    slice_dir = Path(".claude/current-slice")
    if not slice_dir.exists():
        return

    # Walk deepest-first so directories become empty before rmdir.
    paths = sorted(slice_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for p in paths:
        if p.is_file() or p.is_symlink():
            if p.name == "slice.yaml" and p.parent == slice_dir:
                continue
            try:
                os.unlink(str(p))
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise RuntimeError(f"wipe failed for {p}: {exc}") from exc
        elif p.is_dir():
            try:
                p.rmdir()
            except FileNotFoundError:
                continue
            except OSError:
                # Non-empty (e.g. slice.yaml parent) — leave in place.
                continue


def _is_slice_already_closed(state=None):
    """DC-3 precondition check — all four signals must be satisfied."""
    # Signal 1: slice.yaml exists and status=complete
    if not SLICE_YAML.exists():
        return False
    try:
        sy = read_slice_state(SLICE_YAML)
    except yaml.YAMLError:
        return False
    if not isinstance(sy, dict) or sy.get("status") != "complete":
        return False

    # Signal 2: handoff.md present and non-empty
    handoff = Path(".claude/handoff.md")
    if not handoff.exists():
        return False
    try:
        if not handoff.read_text().strip():
            return False
    except OSError:
        return False

    # Signal 3: current-slice/ contains only slice.yaml (files)
    slice_dir = Path(".claude/current-slice")
    if slice_dir.exists():
        files = sorted(
            p.relative_to(slice_dir).as_posix()
            for p in slice_dir.rglob("*")
            if p.is_file()
        )
        if files != ["slice.yaml"]:
            return False

    # Signal 4: HEAD subject matches `slice: <id> — complete` (B5 tightened) or
    # the legacy `slice: complete` shape (backward-compat for fixtures /
    # operator-rebased histories).
    try:
        proc = _git("log", "-1", "--format=%s")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    subject = (proc.stdout or "").strip()
    if subject != "slice: complete" and not re.match(
        r"^slice: .+ — complete$", subject
    ):
        return False

    return True


# --- Resume reconciliation (DC-6) ------------------------------------------


_HANDOFF_RX = re.compile(r"^handoff: phase (\d+) complete$")
_INIT_RX = re.compile(r"^slice: .+ — init$")
_SLICE_COMPLETE_RX = re.compile(r"^slice: .+ — complete$")


def _is_slice_complete_subject(subject):
    """Accept both B5-tightened `slice: <id> — complete` and legacy `slice: complete`."""
    return subject == "slice: complete" or bool(_SLICE_COMPLETE_RX.match(subject or ""))


def _head_subject_safe():
    try:
        proc = _git("log", "-1", "--format=%s")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    return (proc.stdout or "").strip()


def _refuse_resume(triple, reason):
    """Emit the divergence line + triple to stderr and exit 1."""
    print(
        f"orchestrator: resume refuse — {reason}; "
        f"triple=(result.json={triple[0]!r}, slice.yaml={triple[1]!r}, "
        f"HEAD={triple[2]!r})",
        file=sys.stderr,
    )
    sys.exit(1)


def _reconcile_resume_state():
    """Read result.json + slice.yaml + HEAD; return reconciled dict or SystemExit(1)."""
    # Read slice.yaml if present.
    slice_exists = SLICE_YAML.exists()
    slice_status = None
    slice_phase = None
    slice_id_yaml = None
    if slice_exists:
        try:
            sy = read_slice_state(SLICE_YAML)
        except yaml.YAMLError:
            sy = {}
        if isinstance(sy, dict):
            slice_status = sy.get("status")
            slice_phase = sy.get("current_phase")
            slice_id_yaml = sy.get("id")

    # Read result.json keyed by the slice-yaml's id.
    result_data = None
    result_corrupt = False
    if slice_id_yaml:
        rj_path = DEBUG_DIR / f"{_slice_id_slug(slice_id_yaml)}-result.json"
        if rj_path.exists():
            try:
                result_data = json.loads(rj_path.read_text())
            except (OSError, ValueError):
                result_corrupt = True

    head = _head_subject_safe()

    if result_corrupt:
        _refuse_resume(("corrupt", slice_status, head), "result.json parse error")

    rj_status = result_data.get("status") if isinstance(result_data, dict) else None
    rj_phase = (
        result_data.get("current_phase") if isinstance(result_data, dict) else None
    )

    triple = (rj_status, slice_status, head)

    # Row 1: absent / absent / any
    if result_data is None and not slice_exists:
        return {"current_phase": 1, "status": "IN_PROGRESS"}

    # Rows 2/3: absent result.json with in-progress slice.yaml
    if result_data is None and slice_status == "in-progress":
        if _INIT_RX.match(head):
            return {"current_phase": 1, "status": "IN_PROGRESS"}
        _refuse_resume(triple, "missing result.json, HEAD not an init commit")

    effective = "IN_PROGRESS" if rj_status == "DEGRADED" else rj_status

    # Rows 4/5/6/11: (IN_PROGRESS|DEGRADED) + in-progress
    if effective == "IN_PROGRESS" and slice_status == "in-progress":
        expected = rj_phase if isinstance(rj_phase, int) else slice_phase
        expected = expected if isinstance(expected, int) else 1

        m = _HANDOFF_RX.match(head)
        if m:
            completed = int(m.group(1))
            if completed == expected - 1:
                res = dict(result_data)
                # Row 11: keep DEGRADED if that was the state.
                if rj_status != "DEGRADED":
                    res["status"] = "IN_PROGRESS"
                res.setdefault("current_phase", expected)
                return res
            if completed >= expected:
                _refuse_resume(
                    triple,
                    f"JSON stale vs. HEAD (HEAD phase={completed}, "
                    f"expected={expected - 1})",
                )
            _refuse_resume(
                triple,
                f"expected commit missing (HEAD phase={completed}, "
                f"expected={expected - 1})",
            )
        if _INIT_RX.match(head):
            if expected == 1:
                res = dict(result_data)
                if rj_status != "DEGRADED":
                    res["status"] = "IN_PROGRESS"
                res["current_phase"] = 1
                return res
            _refuse_resume(triple, f"HEAD at init but expected phase {expected}")
        _refuse_resume(triple, "HEAD subject unrecognised")

    # Row 7: IN_PROGRESS (or DEGRADED) / complete / slice: complete
    if effective == "IN_PROGRESS" and slice_status == "complete":
        if _is_slice_complete_subject(head):
            head_hash = _git_head_safe()
            res = dict(result_data)
            res.update(
                status="OK",
                exit_code=0,
                final_commit=head_hash,
                ended_at=_iso_now(),
            )
            return res
        _refuse_resume(
            triple,
            "slice.yaml complete but HEAD is not `slice: complete`",
        )

    # Row 8: OK / complete / slice: complete
    if rj_status == "OK" and slice_status == "complete":
        if _is_slice_complete_subject(head):
            res = dict(result_data)
            res.setdefault("exit_code", 0)
            res["status"] = "OK"
            return res
        _refuse_resume(triple, "result.json OK but `slice: complete` commit missing")

    # Row 10: OK / in-progress / any
    if rj_status == "OK" and slice_status == "in-progress":
        _refuse_resume(triple, "result.json OK but slice.yaml still in-progress")

    # Row 12: FAILED/ABORTED/SIGNALED + in-progress → refuse
    if rj_status in {"FAILED", "ABORTED", "SIGNALED"} and slice_status == "in-progress":
        _refuse_resume(triple, f"prior run terminated as {rj_status}")

    # Default-refuse (unmatched triple).
    _refuse_resume(triple, "unmatched reconciliation triple")


# --- atexit terminal writer (D6, signal integration) -----------------------


def _final_persist_and_md():
    """Single terminal writer — fires from atexit or SIGNALED handler."""
    if not _state or not _state.get("slice_id"):
        return
    try:
        _persist_state(_state)
    except SystemExit:
        raise
    except Exception as exc:
        print(
            f"orchestrator: atexit persist_state failed: {exc}",
            file=sys.stderr,
        )
    try:
        _write_result_md(_state)
    except Exception as exc:
        print(
            f"orchestrator: atexit write_result_md failed: {exc}",
            file=sys.stderr,
        )


def _register_atexit_terminal_writer():
    atexit.register(_final_persist_and_md)


def _write_phase_log(
    slice_id,
    phase,
    role,
    stderr_text,
    stdout_text="",
    inputs=None,
    reason="",
    extra=None,
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
    if extra:
        for key, value in extra.items():
            if isinstance(value, (dict, list)):
                parts.append(f"{key}: {json.dumps(value)}")
            else:
                parts.append(f"{key}: {value}")
    if stdout_text:
        parts.append("--- stdout ---")
        parts.append(stdout_text)
    parts.append("--- stderr ---")
    parts.append(stderr_text or "")
    path.write_text("\n".join(parts) + "\n")
    if reason:
        print(f"orchestrator: agent failure logged to {path}", file=sys.stderr)
    return path


def _git_head_safe():
    """Best-effort HEAD capture; empty string if git unavailable or no commits."""
    try:
        return _git("rev-parse", "HEAD").stdout.strip()
    except Exception:
        return ""


def _run_with_live_stderr(cmd, env, timeout, prefix=""):
    """Popen with stderr tee'd live + pre/post HEAD capture for reconciliation.

    B9: attaches `pre_dispatch_head`, `post_dispatch_head`, `timeout_s` to the
    TimeoutExpired exception so callers can emit a reconciliation log.
    B13: sets module-level `_active_child` so the signal handler can reach
    the running subprocess.
    """
    global _active_child
    pre_head = _git_head_safe()
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _active_child = proc
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
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            post_head = _git_head_safe()
            exc = subprocess.TimeoutExpired(
                cmd,
                timeout,
                output="".join(stdout_buf),
                stderr="".join(stderr_buf),
            )
            exc.pre_dispatch_head = pre_head
            exc.post_dispatch_head = post_head
            exc.timeout_s = timeout
            raise exc
        t_out.join(timeout=2)
        t_err.join(timeout=2)
    finally:
        _active_child = None
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


def _dispatch_once(role, inputs, envelope=None, timeout_hard=None):
    """Single dispatch attempt: spawn the agent, parse the tail, emit a log.

    Returns a dict containing at minimum `status`, `summary`, `commit_hash` —
    plus `stderr`, `stdout`, `returncode`, and a `_timeout` marker so the outer
    retry layer can classify without peeking at the agent's internals.
    """
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
        stderr_txt = exc.stderr or ""
        stdout_txt = exc.output or ""
        pre = getattr(exc, "pre_dispatch_head", "")
        post = getattr(exc, "post_dispatch_head", "")
        timeout_s = getattr(exc, "timeout_s", timeout)
        reconcile = {}
        if pre and post and pre != post:
            reconcile = {
                "partial_commit": post,
                "pre_dispatch_head": pre,
                "timeout_s": timeout_s,
            }
        extra = {"reconcile": reconcile} if reconcile else None
        _write_phase_log(
            slice_id,
            phase,
            role,
            stderr_txt,
            stdout_txt,
            inputs=inputs,
            reason=f"timeout after {timeout_s}s",
            extra=extra,
        )
        return {
            "status": "FAILED",
            "summary": f"timeout after {timeout_s}s",
            "commit_hash": "",
            "stderr": stderr_txt,
            "stdout": stdout_txt,
            "returncode": 124,
            "_timeout": True,
        }

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    obj = _parse_structured_tail(stdout)
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
        stderr,
        stdout,
        inputs=inputs,
        reason=reason,
    )
    if obj is None:
        return {
            "status": "FAILED",
            "summary": "malformed agent output (no JSON-object tail)",
            "commit_hash": "",
            "stderr": stderr,
            "stdout": stdout,
            "returncode": proc.returncode,
        }
    if "status" not in obj:
        return {
            "status": "FAILED",
            "summary": "agent output missing required `status` field",
            "commit_hash": "",
            "stderr": stderr,
            "stdout": stdout,
            "returncode": proc.returncode,
        }
    enriched = dict(obj)
    enriched.setdefault("stderr", stderr)
    enriched.setdefault("stdout", stdout)
    enriched.setdefault("returncode", proc.returncode)
    return enriched


def _classify_failure(result):
    """B8: transient | malformed | logic | timeout."""
    if result.get("_timeout"):
        return "timeout"
    stderr = str(result.get("stderr", "") or "")
    rc = result.get("returncode", 0)
    if rc == 124 or TRANSIENT_STDERR_RX.search(stderr):
        return "transient"
    stdout = result.get("stdout", "") or ""
    if _parse_structured_tail(stdout) is None:
        return "malformed"
    return "logic"


def _log_retry_attempt(role, inputs, attempt, classification, backoff_s, result):
    phase, slice_id = _resolve_phase_and_slice(role, inputs)
    _write_phase_log(
        slice_id,
        phase,
        role,
        str(result.get("stderr", "") or ""),
        str(result.get("stdout", "") or ""),
        inputs=inputs,
        reason=f"retry attempt {attempt} ({classification})",
        extra={
            "attempt": attempt,
            "classification": classification,
            "backoff_s": backoff_s,
        },
    )


def dispatch_phase_agent(role, inputs, envelope=None, timeout_hard=None):
    """Public dispatch: wraps `_dispatch_once` with B8 classification + backoff."""
    result = _dispatch_once(role, inputs, envelope, timeout_hard)
    if result.get("status") == "OK":
        return result
    classification = _classify_failure(result)
    if classification == "timeout":
        return result
    if classification == "transient":
        max_retries = int(os.environ.get("CAIRN_FAILED_TRANSIENT_MAX_RETRIES", "3"))
    else:
        max_retries = 1
    for attempt in range(1, max_retries + 1):
        backoff = 4 ** (attempt - 1) if classification == "transient" else 0
        if backoff:
            time.sleep(backoff)
        retry_result = _dispatch_once(role, inputs, envelope, timeout_hard)
        _log_retry_attempt(role, inputs, attempt, classification, backoff, retry_result)
        if retry_result.get("status") == "OK":
            return retry_result
        result = retry_result
        new_class = _classify_failure(result)
        if new_class == "timeout":
            break
        classification = new_class
    return result


_SUPERSEDE_RE = re.compile(r"\bsuperseded?\b", re.IGNORECASE)
_INV_RE = re.compile(r"\bINV-\d{3}\b", re.IGNORECASE)
_DC_RE = re.compile(r"\bDC-\d+\b", re.IGNORECASE)


def detect_superseded_test_signal(raise_issue_summary, current_slice_intent):
    """Pure-function signal detector for RAISE_ISSUE text that names tests
    superseded by a firm contract the current slice just landed.

    Returns ``{"hint": "likely_superseded", "evidence": [<tokens>]}`` when any
    trigger fires, else ``None``. Triggers:

    - ``\\bsuperseded?\\b`` (the root ``supersede`` or ``superseded``; trailing
      ``s`` as in ``supersedes`` is deliberately excluded by the right word
      boundary).
    - ``\\bINV-\\d{3}\\b`` — fires regardless of intent text.
    - ``\\bDC-\\d+\\b`` — AND-gated on the same token appearing (case
      insensitively) in ``current_slice_intent``, so unrelated DC references
      (e.g. a Phase-3 quoting someone else's ADR) do not fire.

    Evidence is the list of distinct matched tokens in first-match order of
    the summary. No I/O, deterministic; suitable for unit test. Advisory
    only — the orchestrator passes the dict through to the triager and does
    not second-guess the triager's final action.
    """
    if not raise_issue_summary:
        return None
    hits = []
    for m in _SUPERSEDE_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _INV_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _DC_RE.finditer(raise_issue_summary):
        token = m.group(0)
        if current_slice_intent and re.search(
            r"\b" + re.escape(token) + r"\b",
            current_slice_intent,
            re.IGNORECASE,
        ):
            hits.append((m.start(), token))
    if not hits:
        return None
    hits.sort(key=lambda h: h[0])
    evidence = []
    seen = set()
    for _, text in hits:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        evidence.append(text)
    return {"hint": "likely_superseded", "evidence": evidence}


def _resolve_supersession_hint(issue_hash):
    """S2 wiring: read the RAISE_ISSUE commit body via ``_git`` and the
    current slice intent, then run the pure detector. Fails open — any
    git or filesystem error leaves the triager inputs pristine.
    """
    try:
        proc = _git("log", "-1", "--format=%B", issue_hash)
    except Exception:
        return None
    summary = proc.stdout or ""
    intent_path = Path(".claude/current-slice/intent.md")
    try:
        intent_text = intent_path.read_text() if intent_path.exists() else ""
    except OSError:
        intent_text = ""
    return detect_superseded_test_signal(summary, intent_text)


def dispatch_triager(issue_hash, phase, slice_id, timeout_hard=None):
    env = os.environ.copy()
    env["AGENT_ROLE"] = "issue-triager"
    timeout = _resolve_timeout("issue-triager", timeout_hard)
    inputs = {
        "issue_commit_hash": issue_hash,
        "current_phase": phase,
        "slice_id": slice_id,
    }
    hint = _resolve_supersession_hint(issue_hash)
    if hint is not None:
        inputs["supersession_hint"] = hint
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
    action = obj.get("action") or obj.get("decision") or ""
    if action not in VALID_TRIAGER_ACTIONS:
        return {
            "action": "ESCALATE_TO_USER",
            "target_phase": phase,
            "rationale": f"triager returned invalid action {action!r}",
        }
    return obj


def _parse_clusters(text):
    """B6: yaml.safe_load + schema check. Top-level list of {name, files}.

    Accepts a `{clusters: [...]}` wrapper for backward compatibility with the
    older `validation/coupling-clusters.yaml` shape.
    """
    data = yaml.safe_load(text)
    if data is None:
        return []
    if isinstance(data, dict) and "clusters" in data:
        data = data["clusters"]
    if not isinstance(data, list):
        raise ValueError(
            f"_parse_clusters: top-level must be a list; got {type(data).__name__}"
        )
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} is not a mapping "
                f"(got {type(item).__name__})"
            )
        name = item.get("name")
        if not isinstance(name, str):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} missing string `name`"
            )
        if "files" not in item:
            raise ValueError(
                f"_parse_clusters: cluster at index {i} ({name!r}) missing `files`"
            )
        files = item["files"]
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} ({name!r}) "
                f"`files` must be a list of strings"
            )
    return data


def _load_clusters():
    for path in (CLUSTERS_YAML, CLUSTERS_YAML_LEGACY):
        if path.exists():
            return _parse_clusters(path.read_text())
    return []


def _intent_envelope():
    """Prefer slice.yaml.envelope; fall back to intent.md frontmatter. B16.

    Three possible returns:
      * non-empty list — dispatch with that envelope.
      * empty list — envelope key explicitly present as a list (possibly empty),
        OR the key is entirely absent (legacy dispatch-anyway). Dispatch
        proceeds with empty envelope.
      * None — the envelope key is declared but its value is not a list
        (e.g. `envelope:\\n` → None). Caller MUST short-circuit to FAILED.
    """
    declared_nonlist = False

    if SLICE_YAML.exists():
        try:
            state = read_slice_state(SLICE_YAML)
        except yaml.YAMLError:
            state = {}
        if isinstance(state, dict) and "envelope" in state:
            env = state["envelope"]
            if isinstance(env, list):
                return [str(e) for e in env]
            declared_nonlist = True

    if INTENT_MD.exists():
        text = INTENT_MD.read_text()
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end >= 0:
                fm_text = text[4:end]
                try:
                    fm = yaml.safe_load(fm_text)
                except yaml.YAMLError:
                    fm = None
                if isinstance(fm, dict) and "envelope" in fm:
                    env = fm["envelope"]
                    if isinstance(env, list):
                        return [str(e) for e in env]
                    declared_nonlist = True

    if declared_nonlist:
        return None
    return []


def _write_cluster_log(slice_id, cluster_name, envelope, result, stdout="", stderr=""):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slice_id_slug(slice_id)
    path = DEBUG_DIR / f"{slug}-phase-3-cluster-{cluster_name}-{_utc_timestamp()}.log"
    parts = [
        f"slice_id: {slice_id}",
        f"cluster: {cluster_name}",
        f"envelope: {envelope}",
        f"result: {json.dumps(result)}",
    ]
    if stdout:
        parts.append("--- stdout ---")
        parts.append(stdout)
    if stderr:
        parts.append("--- stderr ---")
        parts.append(stderr)
    path.write_text("\n".join(parts) + "\n")
    return path


def _phase3_dispatch_with_log(cluster, inputs, envelope, slice_id):
    result = dispatch_phase_agent("phase-3-implementer", inputs, envelope)
    _write_cluster_log(
        slice_id,
        cluster["name"],
        envelope,
        result,
        stdout=str(result.get("stdout", "") or ""),
        stderr=str(result.get("stderr", "") or ""),
    )
    return result


def dispatch_phase_3(slice_id):
    try:
        clusters = _load_clusters()
    except ValueError as exc:
        print(f"orchestrator: clusters.yaml schema error: {exc}", file=sys.stderr)
        return {"status": "FAILED", "summary": str(exc), "commit_hash": ""}

    is_implicit = (not clusters) or all(not c.get("files") for c in clusters)

    if is_implicit:
        intent_env = _intent_envelope()
        if intent_env is None:
            return {
                "status": "FAILED",
                "summary": (
                    "phase-3 empty envelope: no clusters declared and intent "
                    "envelope is empty"
                ),
                "commit_hash": "",
            }
        print(
            "orchestrator: phase-3 falling back to intent envelope "
            "(no clusters declared)",
            file=sys.stderr,
        )
        clusters = [{"name": "implicit", "files": list(intent_env)}]

    workers = min(len(clusters), 8)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for cluster in clusters:
            envelope = json.dumps(cluster["files"])
            inputs = {
                "phase": 3,
                "role": "phase-3-implementer",
                "slice_id": slice_id,
                "cluster": cluster["name"],
            }
            futures.append(
                pool.submit(
                    _phase3_dispatch_with_log,
                    cluster,
                    inputs,
                    envelope,
                    slice_id,
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
    """Stage + commit the phase agent's handoff-phase-N.md.

    Intentionally does NOT overwrite file content — the phase agent owns that
    body. Uses --allow-empty so the orchestrator records the phase boundary
    even if the agent already committed the handoff file itself. B11.
    """
    path = Path(f".claude/current-slice/handoff-phase-{phase}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _git("add", str(path))
    _git("commit", "--allow-empty", "-m", f"handoff: phase {phase} complete")


def _current_phase():
    state = _read_slice_state_strict()
    value = state.get("current_phase", 1)
    try:
        return int(value) if value is not None else 1
    except (TypeError, ValueError):
        return 1


def _persist_current_phase(new_phase):
    """B1: write `current_phase: N` to slice.yaml without clobbering siblings.

    Invoked after every successful phase-handoff commit so a subsequent
    `--resume` reads the advanced phase rather than re-dispatching the one
    that just completed.
    """
    try:
        state = read_slice_state(SLICE_YAML) if SLICE_YAML.exists() else {}
    except yaml.YAMLError:
        state = {}
    if not isinstance(state, dict):
        state = {}
    state["current_phase"] = int(new_phase)
    _write_slice_state(state)


def _slice_id():
    state = _read_slice_state_strict()
    return state.get("id", "unknown/unknown")


def _slice_brief():
    state = _read_slice_state_strict()
    return state.get("brief", "") or ""


def _dispatch_for_phase(phase, role, inputs, envelope, timeout):
    if phase == 3:
        return dispatch_phase_3(_slice_id())
    return dispatch_phase_agent(role, inputs, envelope, timeout)


def _clean_shutdown(signum, frame):
    """B13: SIGINT/SIGTERM handler — terminate active child, then exit.

    Slice 3 D6 integration: before exiting, records `status=SIGNALED` +
    `exit_code` on the module-level `_state` so the atexit terminal writer
    persists the signal-caused terminal state.
    """
    global _active_child
    grace = int(os.environ.get("CAIRN_SHUTDOWN_GRACE_S", "5"))
    child = _active_child
    if child is not None:
        try:
            child.terminate()
        except Exception:
            pass
        try:
            child.wait(timeout=grace)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass
    exit_code = 130 if signum == signal.SIGINT else 143
    try:
        if _state and _state.get("slice_id"):
            _update_state(status="SIGNALED", exit_code=exit_code, ended_at=_iso_now())
    except Exception:
        pass
    sys.exit(exit_code)


def _register_signal_handlers():
    try:
        signal.signal(signal.SIGINT, _clean_shutdown)
        signal.signal(signal.SIGTERM, _clean_shutdown)
    except (ValueError, OSError):
        # non-main thread or platform without these signals
        pass


def _persist_redispatch(source_phase, target_phase):
    """B14: write current_phase=target to slice.yaml and commit before rewind."""
    state = {}
    try:
        state = read_slice_state(SLICE_YAML) if SLICE_YAML.exists() else {}
    except yaml.YAMLError:
        state = {}
    if not isinstance(state, dict):
        state = {}
    state["current_phase"] = target_phase
    _write_slice_state(state)
    try:
        _git("add", str(SLICE_YAML))
    except subprocess.CalledProcessError:
        pass
    _git(
        "commit",
        "--allow-empty",
        "-m",
        f"slice: re-dispatch phase {source_phase} → phase {target_phase}",
    )


def run_phase_loop(max_phase=4):
    _register_signal_handlers()
    phase = _current_phase()
    redispatch_count: dict[int, int] = {}
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
            # DC-4 code layer: suppress the per-phase handoff commit at the
            # Phase-4 boundary; close_slice is the sole source of the final
            # `slice: complete` commit.
            if phase < max_phase:
                commit_phase_handoff(
                    phase,
                    result.get("summary", ""),
                    result.get("commit_hash", ""),
                )
                _persist_current_phase(phase + 1)
            phase += 1
            continue

        if status == "FAILED":
            retry = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
            if retry.get("status") == "OK":
                if phase < max_phase:
                    commit_phase_handoff(
                        phase,
                        retry.get("summary", ""),
                        retry.get("commit_hash", ""),
                    )
                    _persist_current_phase(phase + 1)
                phase += 1
                continue
            print(
                f"orchestrator: phase {phase} failed twice; escalating",
                file=sys.stderr,
            )
            return 1

        if status == "RAISE_ISSUE":
            # B15: cap re-dispatch from the same source phase to 1.
            if redispatch_count.get(phase, 0) >= 1:
                print(
                    f"orchestrator: phase {phase} re-dispatched twice; "
                    f"escalating per design §6.1",
                    file=sys.stderr,
                )
                return 1
            triager = dispatch_triager(
                issue_hash=result.get("commit_hash", ""),
                phase=phase,
                slice_id=_slice_id(),
            )
            action = triager.get("action") or triager.get("decision") or ""
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
                try:
                    _persist_redispatch(phase, target)
                except subprocess.CalledProcessError as exc:
                    print(
                        f"orchestrator: redispatch persist failed: {exc}",
                        file=sys.stderr,
                    )
                    return 1
                redispatch_count[phase] = redispatch_count.get(phase, 0) + 1
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
        except (OSError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
            print(
                f"orchestrator: close_slice failed: {exc}",
                file=sys.stderr,
            )
            return 1
    return 0


def _abort_slice():
    if not SLICE_YAML.exists():
        return
    try:
        state = read_slice_state(SLICE_YAML)
    except yaml.YAMLError:
        state = {}
    if not isinstance(state, dict):
        state = {}
    state["status"] = "aborted"
    _write_slice_state(state)
    try:
        _git("add", str(SLICE_YAML))
        _git("commit", "--allow-empty", "-m", "slice: aborted by triager")
    except subprocess.CalledProcessError:
        pass


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
    proposed = result.get("proposed_slice_id", "") if isinstance(result, dict) else ""
    proposed = _normalize_slice_id(proposed)
    if not is_valid_slice_id(proposed):
        # Fallback: record the brief even when the writer did not propose an id;
        # the operator (or a follow-up phase-1 run) can rename the slice later.
        proposed = "pending/slice"
    SLICE_YAML.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "id": proposed,
        "name": proposed,
        "status": "in-progress",
        "current_phase": 1,
        "brief": brief,
    }
    _write_slice_state(state)
    try:
        _git("add", str(SLICE_YAML))
        _git("commit", "--allow-empty", "-m", f"slice: {proposed} — init")
    except subprocess.CalledProcessError:
        pass
    return read_slice_state(SLICE_YAML)


def close_slice(state=None):
    """INV-008 slice-close contract: DC-3 idempotent, DC-4 sole commit source,
    DC-5 explicit wipe, DC-7 slug-keyed observability persistence.

    Order: slice.yaml → bundle → wipe → commit `slice: complete`.
    """
    if _is_slice_already_closed(state):
        return

    # Step 1: slice.yaml → status=complete, current_phase=max_phase.
    try:
        sy = read_slice_state(SLICE_YAML) if SLICE_YAML.exists() else {}
    except yaml.YAMLError:
        sy = {}
    if not isinstance(sy, dict):
        sy = {}
    sy["status"] = "complete"
    sy["current_phase"] = 4
    _write_slice_state(sy)

    # Step 2: bundle handoff.md before wipe removes the inputs.
    handoff = _bundle_handoff_md()

    # Drift detector (DC-4 layer 3): last commit must NOT be a phase-4 handoff.
    try:
        prior = _git("log", "-1", "--format=%s").stdout.strip()
        if prior == "handoff: phase 4 complete":
            print(
                "orchestrator: drift — HEAD is `handoff: phase 4 complete`; "
                "Phase-4 agent committed directly (DC-4 anti-behavior).",
                file=sys.stderr,
            )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Step 3: wipe current-slice (DC-5 strict; F5-tolerant).
    _wipe_current_slice()

    # Step 4: sole `slice: <id> — complete` commit (DC-4 + B5-tightened).
    slice_id_for_subject = sy.get("id") or "unknown/unknown"
    _git("add", "-f", str(SLICE_YAML), str(handoff))
    try:
        _git("add", "-u", ".claude/current-slice")
    except subprocess.CalledProcessError:
        pass
    _git(
        "commit",
        "--allow-empty",
        "-m",
        f"slice: {slice_id_for_subject} — complete",
    )

    # Step 5: persist terminal observability state.
    if _state and _state.get("slice_id"):
        head = _git_head_safe()
        _update_state(
            status="OK",
            exit_code=0,
            ended_at=_iso_now(),
            final_commit=head,
            summary=_state.get("summary") or "slice closed",
        )
        try:
            _persist_state(_state)
        except SystemExit:
            raise
        except Exception as exc:
            print(
                f"orchestrator: close-time persist_state failed: {exc}",
                file=sys.stderr,
            )
        try:
            _write_result_md(_state)
        except Exception as exc:
            print(
                f"orchestrator: close-time write_result_md failed: {exc}",
                file=sys.stderr,
            )


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

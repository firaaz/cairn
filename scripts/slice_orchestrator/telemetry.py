"""Observability artifacts: state dict, atomic writes, heartbeat, cost.

Owns the module-level ``_state`` dict that all phases mutate. Other package
modules import the singleton via ``from .telemetry import _state`` and observe
mutations across module boundaries through the shared dict identity.

Writes ``.claude/orchestrator-debug/<slug>-result.json`` (canonical state),
``<slug>-result.md`` (human sidecar), the append-only ``index.jsonl`` stream,
``.claude/current-slice/.heartbeat`` liveness, and per-phase failure logs
(``<slug>-phase-N-<role>-<ts>.log``).
"""

from __future__ import annotations

import atexit
import copy
import json
import os
import sys
import threading
from pathlib import Path

from .core import (
    DEBUG_DIR,
    DEFAULT_HEARTBEAT_INTERVAL,
    TERMINAL_STATUS,
    TOKEN_CLASSES,
    _active_pricing_table,
    _cost_for_tokens,
    _iso_now,
    _slice_id_slug,
    _utc_timestamp,
)

# Module-level state dict — singleton; other modules import this object and
# rely on dict identity to share mutations.
_state: dict = {}


def _default_observability_errors():
    return {
        "persist_state": 0,
        "write_result_md": 0,
        "append_index": 0,
        "heartbeat": 0,
    }


def _init_state_dict(slice_id):
    """Reset the module-level state dict to schema v1.0 fresh defaults.

    Cost telemetry fields (intent §S1) are additive only — ``schema_version``
    stays at ``"1.0"`` (orchestrator-observability D4 additive-safe contract).
    ``pricing_snapshot`` is a deep copy of the active dated ``PRICING_TABLE``
    constant so archived slices remain reinterpretable at their
    cost-at-the-time even if the prod table is revised later.
    """
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
            # Cost telemetry (INV-009 introduction, intent §S1). Additive —
            # schema_version deliberately NOT bumped.
            "tokens_by_phase": {},
            "cost_by_phase_usd": {},
            "model_by_phase": {},
            "tokens_total": 0,
            "cost_total_usd": 0.0,
            "pricing_snapshot": copy.deepcopy(_active_pricing_table()),
        }
    )
    return _state


def _record_phase_cost(phase, tokens, model):
    """Record per-phase token usage and dollar cost on the module state dict.

    Idempotent per-phase: a redispatch of the same phase **overwrites** its
    entry rather than accumulating (risk register L166 — retry counts
    already live in ``retries_by_phase``, so cost attribution tracks the
    most recent successful dispatch). Recomputes ``tokens_total`` and
    ``cost_total_usd`` from the post-update per-phase dicts so totals stay
    equal to sum-of-parts by construction. Does **not** mutate
    ``retries_by_phase`` — cost attribution is orthogonal to retry
    accounting.
    """
    tokens_by_phase = _state.setdefault("tokens_by_phase", {})
    cost_by_phase = _state.setdefault("cost_by_phase_usd", {})
    model_by_phase = _state.setdefault("model_by_phase", {})
    pricing = _state.setdefault("pricing_snapshot", {})

    # Overwrite, not accumulate. Copy tokens dict so caller mutations don't
    # leak into the state.
    tokens_by_phase[phase] = {c: int(tokens.get(c, 0)) for c in TOKEN_CLASSES}
    model_by_phase[phase] = model

    prices = pricing.get(model) or {}
    cost_by_phase[phase] = _cost_for_tokens(tokens_by_phase[phase], prices)

    _state["tokens_total"] = sum(
        v for phase_tokens in tokens_by_phase.values() for v in phase_tokens.values()
    )
    _state["cost_total_usd"] = sum(cost_by_phase.values())
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
    from .core import _active_pricing_table_name

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

    # Cost section (intent §S5): surfaced only when at least one phase has a
    # recorded tokens entry. Derived deterministically from the per-phase
    # dicts so MD stays a pure projection of state JSON (D2/D5).
    tokens_by_phase = state.get("tokens_by_phase") or {}
    if tokens_by_phase:
        cost_by_phase = state.get("cost_by_phase_usd") or {}
        model_by_phase = state.get("model_by_phase") or {}
        tokens_total = state.get("tokens_total", 0)
        cost_total = state.get("cost_total_usd", 0.0) or 0.0
        pricing_name = _active_pricing_table_name()
        lines.append("## Cost")
        lines.append("")
        lines.append(f"Total: {tokens_total} tokens, ${cost_total:.2f} USD")
        lines.append("")
        lines.append("| Phase | Model | Tokens | USD |")
        lines.append("|-------|-------|--------|-----|")
        for phase_name, phase_tokens in tokens_by_phase.items():
            phase_tok_sum = sum((phase_tokens or {}).values())
            phase_cost = cost_by_phase.get(phase_name, 0.0) or 0.0
            phase_model = model_by_phase.get(phase_name, "")
            lines.append(
                f"| {phase_name} | {phase_model} | {phase_tok_sum} | "
                f"${phase_cost:.4f} |"
            )
        lines.append("")
        lines.append(f"pricing: {pricing_name}")
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

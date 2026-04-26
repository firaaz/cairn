"""Subprocess dispatch + retry classification + Phase-3 cluster fan-out.

Calls out to the ``claude`` CLI per agent role with ``--output-format json``,
parses the structured tail, classifies failures, and (for Phase 3) fans out
one worker per declared cluster. Owns the module-level ``_active_child``
reference so the lifecycle signal handler can terminate the in-flight child
on SIGINT/SIGTERM.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from .core import (
    CLUSTERS_YAML,
    CLUSTERS_YAML_LEGACY,
    PERMISSION_MODE,
    ROLE_TO_PHASE,
    VALID_TRIAGER_ACTIONS,
    _classify_failure,
    _extract_agent_result_text,
    _extract_envelope_model,
    _intent_envelope,
    _parse_clusters,
    _parse_structured_tail,
    _parse_usage_envelope,
    _record_orchestrator_event,
    _resolve_model_config,
    _resolve_timeout,
    detect_superseded_test_signal,
)
from .git import _git, _git_head_safe
from .telemetry import _record_phase_cost, _state, _write_cluster_log, _write_phase_log

# Module-level handle on the in-flight child so the signal handler can
# terminate it. Mutated by `_run_with_live_stderr`; read from `lifecycle`.
_active_child = None


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
    from .resume import _slice_id

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
    resolved_model, resolved_effort = _resolve_model_config(role)
    cmd = [
        "claude",
        "-p",
        "--agent",
        role,
        "--model",
        resolved_model,
        "--effort",
        resolved_effort,
        "--permission-mode",
        PERMISSION_MODE,
        "--output-format",
        "json",
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
        _record_orchestrator_event(
            slice_id,
            "agent_timeout",
            phase=phase,
            timeout_seconds=timeout_s,
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
    # With `--output-format json`, the subprocess stdout is a JSON array
    # envelope whose terminal `result` event carries the agent's actual
    # tail in its `result` string. Extract that for `_parse_structured_tail`;
    # on any parse failure (non-envelope stubs in tests, mid-stream crash)
    # fall through to the raw stdout so existing behaviour is preserved
    # (intent §S2.c/S2.d).
    agent_text = _extract_agent_result_text(stdout) or stdout
    # Record per-phase cost telemetry (intent §S2 wiring — V3/V21). Tolerant
    # by contract: a malformed envelope yields zero tokens and empty model
    # via the helpers' `.get(..., 0)` paths, so a crashed subprocess cannot
    # topple the dispatcher (§S2.d error tolerance).
    try:
        _record_phase_cost(
            role,
            _parse_usage_envelope(stdout),
            _extract_envelope_model(stdout),
        )
    except Exception as _cost_exc:  # pragma: no cover — defensive only
        print(
            f"orchestrator: cost telemetry skipped ({_cost_exc!r})",
            file=sys.stderr,
        )
    # INV-009 honesty: always record the RESOLVED model (what was sent to
    # claude -p) so cost attribution is truthful under env-var overrides.
    # Overwrites the envelope-derived model set by _record_phase_cost above.
    _state.setdefault("model_by_phase", {})[role] = resolved_model
    obj = _parse_structured_tail(agent_text)
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
            "stdout": agent_text,
            "returncode": proc.returncode,
        }
    if "status" not in obj:
        return {
            "status": "FAILED",
            "summary": "agent output missing required `status` field",
            "commit_hash": "",
            "stderr": stderr,
            "stdout": agent_text,
            "returncode": proc.returncode,
        }
    enriched = dict(obj)
    enriched.setdefault("stderr", stderr)
    enriched.setdefault("stdout", agent_text)
    enriched.setdefault("returncode", proc.returncode)
    return enriched


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


def _load_clusters():
    for path in (CLUSTERS_YAML, CLUSTERS_YAML_LEGACY):
        if path.exists():
            return _parse_clusters(path.read_text())
    return []


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

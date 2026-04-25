"""Slice-state read/write + the 13-state-triple resume reconciliation matrix.

``slice.yaml`` is the canonical phase-pointer; ``<slug>-result.json`` is the
observability mirror; ``HEAD`` subject is the durable on-disk ground truth.
The resume reconciler reads all three and routes a default-refuse triple
through 13 named rows (intent §S2) before letting the orchestrator advance.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

from .core import (
    DEBUG_DIR,
    SLICE_YAML,
    _iso_now,
    _slice_id_slug,
)
from .git import _git, _git_head_safe, _head_subject_safe


# --- slice.yaml read/write -------------------------------------------------


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


def _slice_id():
    state = _read_slice_state_strict()
    return state.get("id", "unknown/unknown")


def _slice_brief():
    state = _read_slice_state_strict()
    return state.get("brief", "") or ""


# --- Resume reconciliation (DC-6) ------------------------------------------


_HANDOFF_RX = re.compile(r"^handoff: phase (\d+) complete$")
_INIT_RX = re.compile(r"^slice: .+ — init$")
_SLICE_COMPLETE_RX = re.compile(r"^slice: .+ — complete$")


def _is_slice_complete_subject(subject):
    """Accept both B5-tightened `slice: <id> — complete` and legacy `slice: complete`."""
    return subject == "slice: complete" or bool(_SLICE_COMPLETE_RX.match(subject or ""))


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

"""Phase 2 RED — observability primitives (D2, D6, D7).

Spec: intent.md §Observability error policy + §State-dict schema v1.0 + §DC-5.
Primitives exercised:
 - `_atomic_write(path, content)`        — tempfile + os.rename; 1 retry, no delay.
 - `_persist_state(state)`               — writes result.json atomically.
 - `_write_result_md(state)`             — terminal-only cadence; derived MD.
 - `_generate_result_md(state) -> str`   — pure function; JSON → markdown.
 - `_append_index_entry(entry)`          — O_APPEND to index.jsonl.

Expected at Phase 2: every test FAILS with AttributeError or assertion failure
— none of these primitives exist yet in `slice_orchestrator`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


# ---------- helpers ---------------------------------------------------------


def _so(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    Path(".claude/orchestrator-debug").mkdir(parents=True, exist_ok=True)
    Path(".claude/current-slice").mkdir(parents=True, exist_ok=True)
    return so


def _init_state(so, slice_id="demo/slice-x"):
    so._init_state_dict(slice_id=slice_id)
    return so._state


# ---------- _atomic_write ---------------------------------------------------


def test_atomic_write_succeeds_first_attempt(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    target = tmp_path / "out.txt"
    so._atomic_write(target, "hello")
    assert target.read_text() == "hello"


def test_atomic_write_retries_once_on_oserror(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    target = tmp_path / "out.txt"

    calls = {"n": 0}
    real_rename = os.rename

    def flaky_rename(src, dst):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("transient")
        return real_rename(src, dst)

    monkeypatch.setattr(os, "rename", flaky_rename)
    so._atomic_write(target, "retry-payload")
    assert target.read_text() == "retry-payload"
    assert calls["n"] == 2, "atomic_write must make exactly 2 attempts on first failure"


def test_atomic_write_raises_on_second_failure(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    target = tmp_path / "out.txt"

    calls = {"n": 0}

    def always_fail(src, dst):
        calls["n"] += 1
        raise OSError("still broken")

    monkeypatch.setattr(os, "rename", always_fail)
    with pytest.raises(OSError):
        so._atomic_write(target, "nope")
    assert calls["n"] == 2, "atomic_write must stop after 2 attempts total"


# ---------- _persist_state --------------------------------------------------


def test_persist_state_uses_atomic_write(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so)

    seen = {}

    def fake_atomic_write(path, content):
        seen["path"] = Path(path)
        seen["content"] = content
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    monkeypatch.setattr(so, "_atomic_write", fake_atomic_write)
    so._persist_state(state)

    assert seen["path"].name.endswith("-result.json")
    json.loads(seen["content"])  # must be valid JSON


def test_persist_state_preserves_schema_version(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so)
    so._persist_state(state)

    paths = so._observability_paths(state["slice_id"])
    data = json.loads(Path(paths["result_json"]).read_text())
    assert data["schema_version"] == "1.0"


# ---------- _write_result_md / _generate_result_md --------------------------


def test_write_result_md_only_runs_on_terminal_transition(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so)

    # Non-terminal: MD must not exist yet, and calling the writer is a contract
    # only at terminal transitions.
    paths = so._observability_paths(state["slice_id"])
    md_path = Path(paths["result_md"])
    assert not md_path.exists(), "result.md must not exist while slice is IN_PROGRESS"

    # Simulate terminal and invoke terminal writer.
    state["status"] = "OK"
    state["ended_at"] = "2026-04-20T15:47:22+00:00"
    so._write_result_md(state)
    assert md_path.exists() and md_path.read_text().strip(), (
        "result.md must be generated at terminal transition"
    )


def test_md_is_derived_from_json_state(monkeypatch, tmp_path):
    """DC-1 / D2: MD content comes deterministically from JSON state."""
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so, slice_id="demo/abc-def")
    state.update(
        status="OK",
        exit_code=0,
        final_commit="deadbee",
        summary="all green",
        ended_at="2026-04-20T16:00:00+00:00",
    )
    md = so._generate_result_md(state)
    assert isinstance(md, str) and md, "generate_result_md must return non-empty str"
    assert "demo/abc-def" in md, "MD must reference the slice id"
    assert "OK" in md
    assert "deadbee" in md
    assert "all green" in md


# ---------- _append_index_entry --------------------------------------------


def test_append_index_entry_atomic_under_interleaved_writes(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    _init_state(so)
    entries = [
        {"slice_id": "demo/slice-x", "event": "phase_3_cluster", "n": i}
        for i in range(5)
    ]
    for e in entries:
        so._append_index_entry(e)

    paths = so._observability_paths("demo/slice-x")
    idx = Path(paths["index_jsonl"])
    lines = idx.read_text().splitlines()
    assert len(lines) == len(entries), (
        f"expected {len(entries)} JSONL lines, got {len(lines)}"
    )
    for line in lines:
        rec = json.loads(line)
        assert rec["slice_id"] == "demo/slice-x"


# ---------- Degradation (D6/D7) --------------------------------------------


def test_degraded_status_replaces_in_progress_on_retry_exhaustion(
    monkeypatch, tmp_path
):
    """Level 2 error policy: _persist_state should demote IN_PROGRESS→DEGRADED
    when _atomic_write raises after its retry budget."""
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so)
    assert state["status"] == "IN_PROGRESS"

    calls = {"n": 0}

    def failing_atomic(path, content):
        calls["n"] += 1
        # Fail the first invocation (primary write), succeed the degradation
        # write so we can observe the state transition on disk.
        if calls["n"] == 1:
            raise OSError("primary write exhausted retry")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    monkeypatch.setattr(so, "_atomic_write", failing_atomic)
    so._persist_state(state)

    assert state["status"] == "DEGRADED"
    assert state["degradation_reason"], "degradation_reason must be populated"
    assert state["observability_errors"]["persist_state"] >= 1


def test_degradation_reason_persists_through_terminal_transition(monkeypatch, tmp_path):
    """D7: once degradation is set, subsequent terminal transition must
    preserve the reason rather than overwriting it."""
    so = _so(monkeypatch, tmp_path)
    state = _init_state(so)
    state["status"] = "DEGRADED"
    state["degradation_reason"] = "persist_state: [Errno 28] No space left"

    so._update_state(status="OK", exit_code=0, ended_at="2026-04-20T16:00:00+00:00")
    assert state["degradation_reason"] == ("persist_state: [Errno 28] No space left"), (
        "degradation_reason must append-preserve past terminal transition"
    )
    assert state["status"] == "OK"

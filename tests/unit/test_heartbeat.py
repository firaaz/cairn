"""Phase 2 RED — heartbeat daemon (DC-2, D6, D9).

Spec: intent.md §Observability error policy + §DC-5 + design §Components.
 - `_HeartbeatDaemon(heartbeat_path, interval)` touches `.heartbeat` every
   `interval` seconds; `daemon=True`; self-healing loop.
 - Heartbeat thread writes ONLY `.heartbeat` (DC-2 decoupling).
 - State writer (`_persist_state`, `_write_result_md`) writes never touch
   `.heartbeat` (DC-2 decoupling).
 - Main-thread sampling detects heartbeat death; one restart attempt; then
   `status=DEGRADED`.
 - Env: `CAIRN_HEARTBEAT_INTERVAL=10.0`, `CAIRN_HEARTBEAT_STALE=30.0`.

Expected at Phase 2: every test FAILS with AttributeError — the daemon class
and the main-thread restart/degrade logic do not yet exist.
"""

from __future__ import annotations

import time
from pathlib import Path


def _so(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    Path(".claude/orchestrator-debug").mkdir(parents=True, exist_ok=True)
    Path(".claude/current-slice").mkdir(parents=True, exist_ok=True)
    return so


def _start(so, hb_path, interval=0.05):
    daemon = so._HeartbeatDaemon(hb_path, interval=interval)
    daemon.start()
    return daemon


def test_heartbeat_updates_file_periodically(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"
    daemon = _start(so, hb, interval=0.05)
    try:
        time.sleep(0.2)
        assert hb.exists(), "heartbeat must touch the file within one interval"
        first = hb.read_text()
        time.sleep(0.15)
        second = hb.read_text()
        assert first != second, "heartbeat must update timestamp across intervals"
    finally:
        daemon.stop()
        daemon.join(timeout=1.0)


def test_heartbeat_survives_transient_write_error(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"

    calls = {"n": 0}
    real_write_text = Path.write_text

    def flaky_write(self, *a, **kw):
        if self == hb:
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("transient heartbeat failure")
        return real_write_text(self, *a, **kw)

    monkeypatch.setattr(Path, "write_text", flaky_write)
    daemon = _start(so, hb, interval=0.05)
    try:
        time.sleep(0.3)
        assert daemon.is_alive(), "heartbeat thread must not die on transient error"
        assert hb.exists(), "heartbeat must recover and write after transient"
    finally:
        daemon.stop()
        daemon.join(timeout=1.0)


def test_heartbeat_thread_death_detected_by_main_thread(monkeypatch, tmp_path):
    """Main-thread periodic check calls `is_alive()` and notices death."""
    so = _so(monkeypatch, tmp_path)
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"
    daemon = _start(so, hb, interval=0.05)
    daemon._stop_event.set()  # force death
    daemon.join(timeout=1.0)

    check = getattr(so, "_check_heartbeat_alive", None)
    assert check is not None, (
        "_check_heartbeat_alive() must exist for main-thread sampling"
    )
    alive = check(daemon)
    assert alive is False, "main-thread check must report dead heartbeat"


def test_heartbeat_one_restart_attempt_then_degrade(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"

    restarts = {"n": 0}

    def fake_start_heartbeat(*a, **kw):
        restarts["n"] += 1

        # Return a never-alive sentinel so the "restart succeeded" check fails.
        class _Dead:
            def is_alive(self):
                return False

            def start(self):
                pass

            def stop(self):
                pass

            def join(self, timeout=None):
                pass

        return _Dead()

    monkeypatch.setattr(so, "_start_heartbeat", fake_start_heartbeat, raising=False)
    so._handle_heartbeat_death(hb_path=hb)
    assert restarts["n"] == 1, "exactly one restart attempt expected before degrade"
    assert so._state["status"] == "DEGRADED"
    assert "heartbeat" in (so._state["degradation_reason"] or "").lower()


def test_heartbeat_stops_cleanly_on_sigterm(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"
    daemon = _start(so, hb, interval=0.05)
    daemon.stop()
    daemon.join(timeout=1.0)
    assert not daemon.is_alive(), "stop() must terminate the daemon thread"


def test_heartbeat_never_writes_result_json(monkeypatch, tmp_path):
    """DC-2: heartbeat thread touches only .heartbeat."""
    so = _so(monkeypatch, tmp_path)
    hb = tmp_path / ".claude" / "current-slice" / ".heartbeat"

    touched: list[str] = []
    real_write_text = Path.write_text

    def spy_write(self, *a, **kw):
        touched.append(str(self))
        return real_write_text(self, *a, **kw)

    monkeypatch.setattr(Path, "write_text", spy_write)
    daemon = _start(so, hb, interval=0.05)
    try:
        time.sleep(0.2)
    finally:
        daemon.stop()
        daemon.join(timeout=1.0)

    for path in touched:
        assert "result.json" not in path, (
            f"heartbeat thread wrote to {path!r}; DC-2 forbids"
        )
        assert "result.md" not in path
        assert "index.jsonl" not in path


def test_state_writer_never_writes_heartbeat(monkeypatch, tmp_path):
    """DC-2: _persist_state / _write_result_md never touch .heartbeat."""
    so = _so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")
    state = so._state

    touched: list[str] = []
    real_atomic = so._atomic_write

    def spy_atomic(path, content):
        touched.append(str(path))
        return real_atomic(path, content)

    monkeypatch.setattr(so, "_atomic_write", spy_atomic)
    so._persist_state(state)
    state["status"] = "OK"
    state["ended_at"] = "2026-04-20T15:47:22+00:00"
    so._write_result_md(state)

    for path in touched:
        assert ".heartbeat" not in path, f"state writer wrote to {path!r}; DC-2 forbids"

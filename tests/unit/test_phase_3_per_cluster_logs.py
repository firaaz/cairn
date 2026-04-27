"""Phase 2 RED — compression/slice-2-state-machine §B2.

`dispatch_phase_3` MUST write each cluster's stdout+stderr+result-dict to
`.claude/orchestrator-debug/{slice-slug}-phase-3-cluster-{cluster-name}-{ts}.log`
REGARDLESS of whether the orchestrator's return is determined by an earlier
RAISE_ISSUE/FAILED. Return-order rules: first RAISE_ISSUE wins; first
FAILED wins after RAISE_ISSUE; OK wins last. No peer cluster log is dropped.

Expected at Phase 2: FAILS — only the losing cluster's log may be persisted.
"""

from __future__ import annotations

import re
import subprocess


def _setup(monkeypatch, tmp_path):
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/p3log\nphase: 1-intent\nenvelope: [scripts/x.py]\n---\n"
    )
    (slice_dir / "slice.yaml").write_text(
        'id: demo/p3log\nname: "demo/p3log"\nstatus: in-progress\n'
        'current_phase: 3\nbrief: "b"\n'
    )
    (slice_dir / "clusters.yaml").write_text(
        "- name: alpha\n  files: [scripts/a.py]\n"
        "- name: beta\n  files: [scripts/b.py]\n"
        "- name: gamma\n  files: [scripts/c.py]\n"
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    debug_dir = tmp_path / ".claude" / "orchestrator-debug"
    monkeypatch.setattr(so, "DEBUG_DIR", debug_dir, raising=False)
    return so, debug_dir


def test_b2_all_three_cluster_logs_persist_even_when_middle_fails(
    monkeypatch, tmp_path
):
    so, debug_dir = _setup(monkeypatch, tmp_path)

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        # Map cluster → status by inspecting envelope contents.
        env = envelope or ""
        if "scripts/b.py" in env:
            return {"status": "FAILED", "commit_hash": "b", "summary": "beta-fail"}
        return {"status": "OK", "commit_hash": "x", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)

    result = so.dispatch_phase_3("demo/p3log")
    assert result.get("status") == "FAILED"

    logs = sorted(p.name for p in debug_dir.glob("*.log"))
    pattern = re.compile(
        r"^demo-p3log-phase-3-cluster-(alpha|beta|gamma)-\d{8}T\d{6}Z\.log$"
    )
    matched = [n for n in logs if pattern.match(n)]
    assert len(matched) == 3, (
        f"expected one log per cluster (alpha/beta/gamma); got {logs!r}"
    )
    clusters_seen = {pattern.match(n).group(1) for n in matched}
    assert clusters_seen == {"alpha", "beta", "gamma"}, (
        f"all three cluster names must appear; got {clusters_seen!r}"
    )


def test_b2_cluster_log_contains_result_dict(monkeypatch, tmp_path):
    so, debug_dir = _setup(monkeypatch, tmp_path)

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        return {"status": "OK", "commit_hash": "deadbee", "summary": "ok-ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    so.dispatch_phase_3("demo/p3log")

    bodies = "\n".join(p.read_text() for p in debug_dir.glob("*.log"))
    assert "deadbee" in bodies or '"commit_hash"' in bodies, (
        f"per-cluster log must contain the agent result dict; bodies={bodies!r}"
    )

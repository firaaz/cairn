"""Phase 2 RED — compression/slice-2-state-machine §B16.

`dispatch_phase_3` MUST treat absent clusters.yaml OR `clusters == []` OR
every `cluster["files"] == []` as the "implicit cluster" case. The
implicit-cluster envelope defaults to the slice's intent-envelope
(slice.yaml.envelope, else intent.md frontmatter envelope). If that is
also empty, dispatch_phase_3 returns FAILED with a summary stating
`phase-3 empty envelope: no clusters declared and intent envelope is empty`
WITHOUT dispatching any agent. A single stderr warning is emitted on the
implicit-cluster path.

Expected at Phase 2: FAILS — guard not implemented.
"""

from __future__ import annotations

import io
import sys


def _setup(monkeypatch, tmp_path, envelope_list, clusters_text=None):
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    env_lines = "\n".join(f"  - {f}" for f in envelope_list)
    (slice_dir / "intent.md").write_text(
        f"---\nslice: demo/p3\nphase: 1-intent\nenvelope:\n{env_lines}\n---\nbody\n"
    )
    (slice_dir / "slice.yaml").write_text(
        f'id: demo/p3\nname: "demo/p3"\nstatus: in-progress\n'
        f'current_phase: 3\nbrief: "b"\n'
        f"envelope:\n{env_lines}\n"
    )
    if clusters_text is not None:
        (slice_dir / "clusters.yaml").write_text(clusters_text)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    return so, slice_dir


def test_b16_no_clusters_falls_back_to_intent_envelope(monkeypatch, tmp_path):
    so, _ = _setup(monkeypatch, tmp_path, ["scripts/x.py"], clusters_text=None)

    captured_envelopes: list[str] = []

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        captured_envelopes.append(envelope if envelope is not None else "")
        return {"status": "OK", "commit_hash": "d", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)

    err = io.StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    result = so.dispatch_phase_3("demo/p3")

    assert result.get("status") == "OK", f"expected OK; got {result!r}"
    assert len(captured_envelopes) == 1, (
        f"exactly one implicit-cluster dispatch expected; got {captured_envelopes!r}"
    )
    # envelope should encode the single intent file.
    assert "scripts/x.py" in captured_envelopes[0], (
        f"implicit-cluster envelope must contain intent envelope file; "
        f"got {captured_envelopes[0]!r}"
    )
    assert "no clusters declared" in err.getvalue() or "implicit" in err.getvalue(), (
        f"expected implicit-cluster stderr warning; got {err.getvalue()!r}"
    )


def test_b16_empty_cluster_and_empty_envelope_returns_failed(monkeypatch, tmp_path):
    so, _ = _setup(monkeypatch, tmp_path, [], clusters_text=None)

    dispatch_called = []

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        dispatch_called.append(role)
        return {"status": "OK", "commit_hash": "d", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)

    result = so.dispatch_phase_3("demo/p3")
    assert result.get("status") == "FAILED", f"expected FAILED; got {result!r}"
    assert "empty envelope" in result.get("summary", ""), (
        f"summary must mention empty envelope; got {result!r}"
    )
    assert dispatch_called == [], (
        f"no agent must be dispatched on empty-envelope path; got {dispatch_called!r}"
    )


def test_b16_cluster_with_empty_files_list_is_implicit(monkeypatch, tmp_path):
    clusters_yaml = "- name: stub\n  files: []\n"
    so, _ = _setup(monkeypatch, tmp_path, ["scripts/x.py"], clusters_text=clusters_yaml)

    captured_envelopes: list[str] = []

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        captured_envelopes.append(envelope if envelope is not None else "")
        return {"status": "OK", "commit_hash": "d", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    result = so.dispatch_phase_3("demo/p3")
    assert result.get("status") == "OK"
    assert len(captured_envelopes) == 1, (
        f"cluster with empty files must collapse to single implicit dispatch; "
        f"got {captured_envelopes!r}"
    )
    assert "scripts/x.py" in captured_envelopes[0]

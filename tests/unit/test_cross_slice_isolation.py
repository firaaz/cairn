"""Phase 2 RED — DC-7 cross-slice artifact isolation + slug-collision tripwire.

Spec: intent.md §DC-7 slug isolation. Every file under
`.claude/orchestrator-debug/` is either `index.jsonl` (shared, each entry
tagged with `slice_id`) or carries the `<slice-id-slug>` prefix. Tripwire:
`_persist_state` reads any existing `<slug>-result.json`; if its `slice_id`
mismatches the current slice, `sys.exit(1)` with loud stderr.

Expected at Phase 2: every test FAILS with AttributeError — the observability
path helper and slug-collision check do not yet exist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _so(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    Path(".claude/orchestrator-debug").mkdir(parents=True, exist_ok=True)
    Path(".claude/current-slice").mkdir(parents=True, exist_ok=True)
    return so


def test_sequential_slices_keep_separate_result_files(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    # Slice A
    so._init_state_dict(slice_id="feat/a")
    so._persist_state(so._state)

    # Slice B (fresh orchestration re-uses the same DEBUG_DIR)
    so._init_state_dict(slice_id="feat/b")
    so._persist_state(so._state)

    dd = Path(".claude/orchestrator-debug")
    a = dd / "feat-a-result.json"
    b = dd / "feat-b-result.json"
    assert a.exists() and b.exists(), (
        f"both per-slice result.json files must exist; have {[p.name for p in dd.iterdir()]}"
    )
    assert json.loads(a.read_text())["slice_id"] == "feat/a"
    assert json.loads(b.read_text())["slice_id"] == "feat/b"


def test_slice_id_slug_used_in_all_debug_paths(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    paths = so._observability_paths("feat/xy-z")
    slug = "feat-xy-z"
    for key in ("result_json", "result_md"):
        assert Path(paths[key]).name.startswith(slug + "-"), (
            f"{key}={paths[key]!r} must carry the slug prefix {slug!r}"
        )
    # index.jsonl is shared — no slug prefix required.
    assert Path(paths["index_jsonl"]).name == "index.jsonl"


def test_index_jsonl_entries_include_slice_id_tag(monkeypatch, tmp_path):
    so = _so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="feat/alpha")
    so._append_index_entry(
        {"slice_id": "feat/alpha", "event": "phase_3", "cluster": "x"}
    )
    so._init_state_dict(slice_id="feat/beta")
    so._append_index_entry({"slice_id": "feat/beta", "event": "failure", "phase": 2})

    idx = Path(".claude/orchestrator-debug/index.jsonl")
    lines = [json.loads(line) for line in idx.read_text().splitlines()]
    assert [line["slice_id"] for line in lines] == ["feat/alpha", "feat/beta"]


def test_slug_collision_exits_failed(monkeypatch, tmp_path, capsys):
    """Tripwire: pre-existing <slug>-result.json whose slice_id mismatches the
    current slice must cause `_persist_state` to `sys.exit(1)` loudly."""
    so = _so(monkeypatch, tmp_path)

    # Pre-seed a stale result.json with slug "feat-x" but a DIFFERENT slice_id.
    dd = Path(".claude/orchestrator-debug")
    stale = dd / "feat-x-result.json"
    stale.write_text(json.dumps({"schema_version": "1.0", "slice_id": "feat/x-prime"}))

    so._init_state_dict(slice_id="feat/x")
    with pytest.raises(SystemExit) as exc:
        so._persist_state(so._state)
    assert exc.value.code == 1

    err = capsys.readouterr().err
    assert (
        "slug" in err.lower() or "collision" in err.lower() or "feat/x-prime" in err
    ), f"slug-collision tripwire must emit a loud stderr message; got {err!r}"

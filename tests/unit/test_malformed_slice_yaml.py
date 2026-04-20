"""Phase 2 RED — compression/slice-2-state-machine §B12.

`_current_phase()`, `_slice_id()`, `_slice_brief()` MUST raise SystemExit(1)
with stderr `orchestrator: malformed slice.yaml at <path>: <reason>` when
slice.yaml is unparseable — not silently fall back to 1/placeholder strings.

Expected at Phase 2: FAILS — current implementations return safe defaults.
"""

from __future__ import annotations

import pytest


def _setup(monkeypatch, tmp_path, body: str):
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    yaml = slice_dir / "slice.yaml"
    yaml.write_text(body)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", yaml, raising=False)
    return so


@pytest.mark.parametrize("fn_name", ["_current_phase", "_slice_id", "_slice_brief"])
def test_b12_malformed_yaml_exits_with_diagnostic(
    monkeypatch, tmp_path, capsys, fn_name
):
    so = _setup(monkeypatch, tmp_path, "id: [unterminated\n")
    fn = getattr(so, fn_name)
    with pytest.raises(SystemExit) as exc:
        fn()
    assert exc.value.code == 1, (
        f"{fn_name} must exit with code 1 on malformed yaml; got {exc.value.code}"
    )
    err = capsys.readouterr().err
    assert "orchestrator: malformed slice.yaml" in err, (
        f"{fn_name} stderr missing diagnostic prefix; got {err!r}"
    )


def test_b12_well_formed_yaml_does_not_exit(monkeypatch, tmp_path):
    so = _setup(
        monkeypatch,
        tmp_path,
        'id: demo/ok\nname: "demo/ok"\nstatus: in-progress\n'
        'current_phase: 2\nbrief: "demo"\n',
    )
    # sanity: these must still work on well-formed input
    assert so._current_phase() == 2
    assert so._slice_id() == "demo/ok"
    assert so._slice_brief() == "demo"

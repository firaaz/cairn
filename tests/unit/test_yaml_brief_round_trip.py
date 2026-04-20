"""Phase 2 RED — compression/slice-2-state-machine §B3/B4.

`read_slice_state(path)` → `yaml.safe_load`; every slice.yaml write site
→ `yaml.safe_dump(state, default_flow_style=False, sort_keys=False)`.
A brief containing `"`, `\\`, `\\n`, `:`, or `#` MUST round-trip byte-for-byte.

Expected at Phase 2: FAILS — current impl uses line-based parsing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "seed",
        ],
        cwd=tmp_path,
        check=True,
    )


@pytest.mark.parametrize(
    "brief",
    [
        'quote"in',
        "colon: here",
        "back\\slash",
        "newline\nhere",
        "hash#here",
    ],
)
def test_b3_b4_brief_round_trips_byte_for_byte(monkeypatch, tmp_path, brief):
    _init_repo(tmp_path)
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    # Phase-1 dispatch must not fire for a round-trip test.
    monkeypatch.setattr(
        so,
        "dispatch_phase_agent",
        lambda *a, **k: {"status": "OK", "commit_hash": "x", "summary": "y"},
    )

    so.init_new_slice(brief)

    state = so.read_slice_state(slice_dir / "slice.yaml")
    assert isinstance(state, dict), (
        f"read_slice_state must return dict, got {type(state)}"
    )
    assert state.get("brief") == brief, (
        f"brief must round-trip byte-for-byte;\n"
        f"  written: {brief!r}\n"
        f"  read:    {state.get('brief')!r}"
    )

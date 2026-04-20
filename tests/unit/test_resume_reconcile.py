"""Phase 2 RED — resume reconciliation (DC-6, 13 rows).

Spec: intent.md §DC-6 resume matrix (13 rows) + default-refuse + heartbeat
advisory. `_reconcile_resume_state()` reads `<slug>-result.json`,
`.claude/current-slice/slice.yaml`, and `git log -1 --format=%s`. It returns
reconciled-state dict on success, or raises `SystemExit(1)` on divergence with
the literal triple printed to stderr.

Expected at Phase 2: every row parameterisation FAILS with AttributeError —
`_reconcile_resume_state` and the 13-row matcher do not yet exist.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


# ---------- fixtures --------------------------------------------------------


SLICE_ID = "demo/slice-x"


def _init_repo(tmp_path: Path):
    sd = tmp_path / ".claude" / "current-slice"
    sd.mkdir(parents=True)
    dd = tmp_path / ".claude" / "orchestrator-debug"
    dd.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    # Seed an initial commit so HEAD exists.
    (tmp_path / "README.md").write_text("seed")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            "seed",
        ],
        cwd=tmp_path,
        check=True,
    )
    return sd, dd


def _commit(tmp_path: Path, subject: str):
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "--allow-empty",
            "-q",
            "-m",
            subject,
        ],
        cwd=tmp_path,
        check=True,
    )


def _slice_yaml(path: Path, status: str, phase: int):
    path.write_text(
        f"id: {SLICE_ID}\nname: '{SLICE_ID}'\nstatus: {status}\ncurrent_phase: {phase}\nbrief: 'b'\n"
    )


def _slug(slice_id: str) -> str:
    return slice_id.replace("/", "-")


def _write_result_json(dd: Path, slice_id: str, **fields):
    state = {
        "schema_version": "1.0",
        "slice_id": slice_id,
        "status": "IN_PROGRESS",
        "current_phase": 1,
        "started_at": "2026-04-20T15:00:00+00:00",
        "ended_at": None,
        "exit_code": None,
        "phases_completed": [],
        "phase_timings": {},
        "retries_by_phase": {},
        "cluster_dispatches": [],
        "degradation_reason": None,
        "observability_errors": {
            "persist_state": 0,
            "write_result_md": 0,
            "append_index": 0,
            "heartbeat": 0,
        },
        "final_commit": "",
        "summary": "",
        "worktree_path": "",
        "orchestrator_pid": 0,
    }
    state.update(fields)
    (dd / f"{_slug(slice_id)}-result.json").write_text(json.dumps(state))


# ---------- matrix rows -----------------------------------------------------

# Each row: (row_id, setup_fn, expect) where expect is one of:
#   "fresh"        → returns dict with current_phase=1 and status=IN_PROGRESS
#   "resume:N"     → returns dict with current_phase=N
#   "re-init"      → returns dict indicating re-init path
#   "ok-exit"      → returns dict with status=OK, exit_code=0
#   "fixup"        → returns dict marked as lagged-JSON fix-up (status=OK)
#   "refuse"       → raises SystemExit(1)


def _row1(tmp_path, sd, dd):  # absent / absent / any — fresh
    return "fresh"


def _row2(tmp_path, sd, dd):  # absent / in-progress / HEAD `^slice: .* — init$`
    _slice_yaml(sd / "slice.yaml", "in-progress", 1)
    _commit(tmp_path, f"slice: {SLICE_ID} — init")
    return "re-init"


def _row3(tmp_path, sd, dd):  # absent / in-progress / other HEAD
    _slice_yaml(sd / "slice.yaml", "in-progress", 1)
    _commit(tmp_path, "unrelated work")
    return "refuse"


def _row4(tmp_path, sd, dd):  # IN_PROGRESS / in-progress / HEAD matches current_phase
    _slice_yaml(sd / "slice.yaml", "in-progress", 2)
    _commit(tmp_path, "handoff: phase 1 complete")
    _write_result_json(dd, SLICE_ID, current_phase=2, status="IN_PROGRESS")
    return "resume:2"


def _row5(tmp_path, sd, dd):  # IN_PROGRESS / in-progress / HEAD ahead
    _slice_yaml(sd / "slice.yaml", "in-progress", 2)
    _commit(tmp_path, "handoff: phase 1 complete")
    _commit(tmp_path, "handoff: phase 2 complete")
    _write_result_json(dd, SLICE_ID, current_phase=2, status="IN_PROGRESS")
    return "refuse"


def _row6(tmp_path, sd, dd):  # IN_PROGRESS / in-progress / HEAD behind
    _slice_yaml(sd / "slice.yaml", "in-progress", 3)
    _commit(tmp_path, "handoff: phase 1 complete")
    _write_result_json(dd, SLICE_ID, current_phase=3, status="IN_PROGRESS")
    return "refuse"


def _row7(tmp_path, sd, dd):  # IN_PROGRESS / complete / slice: complete HEAD
    _slice_yaml(sd / "slice.yaml", "complete", 4)
    _commit(tmp_path, "handoff: phase 1 complete")
    _commit(tmp_path, "handoff: phase 2 complete")
    _commit(tmp_path, "handoff: phase 3 complete")
    _commit(tmp_path, "slice: complete")
    _write_result_json(dd, SLICE_ID, current_phase=4, status="IN_PROGRESS")
    return "fixup"


def _row8(tmp_path, sd, dd):  # OK / complete / slice: complete HEAD
    _slice_yaml(sd / "slice.yaml", "complete", 4)
    _commit(tmp_path, "slice: complete")
    _write_result_json(dd, SLICE_ID, current_phase=4, status="OK", exit_code=0)
    return "ok-exit"


def _row9(tmp_path, sd, dd):  # OK / complete / commit missing
    _slice_yaml(sd / "slice.yaml", "complete", 4)
    _commit(tmp_path, "some other commit")
    _write_result_json(dd, SLICE_ID, current_phase=4, status="OK", exit_code=0)
    return "refuse"


def _row10(tmp_path, sd, dd):  # OK / in-progress / any
    _slice_yaml(sd / "slice.yaml", "in-progress", 4)
    _write_result_json(dd, SLICE_ID, current_phase=4, status="OK", exit_code=0)
    return "refuse"


def _row11(tmp_path, sd, dd):  # DEGRADED / (any) / (any) — treat as IN_PROGRESS
    _slice_yaml(sd / "slice.yaml", "in-progress", 2)
    _commit(tmp_path, "handoff: phase 1 complete")
    _write_result_json(
        dd,
        SLICE_ID,
        current_phase=2,
        status="DEGRADED",
        degradation_reason="persist_state: test",
    )
    return "resume:2"


def _row12(tmp_path, sd, dd):  # FAILED / in-progress / any — refuse
    _slice_yaml(sd / "slice.yaml", "in-progress", 3)
    _write_result_json(dd, SLICE_ID, current_phase=3, status="FAILED", exit_code=1)
    return "refuse"


def _row13(tmp_path, sd, dd):  # corrupt JSON / any / any — refuse
    _slice_yaml(sd / "slice.yaml", "in-progress", 2)
    (dd / f"{_slug(SLICE_ID)}-result.json").write_text("{not-valid-json")
    return "refuse"


MATRIX = [
    ("row-1-fresh-absent-absent", _row1),
    ("row-2-reinit-absent-inprogress-init-head", _row2),
    ("row-3-refuse-absent-inprogress-other-head", _row3),
    ("row-4-resume-in-progress-matching", _row4),
    ("row-5-refuse-head-ahead-of-json", _row5),
    ("row-6-refuse-head-behind-json", _row6),
    ("row-7-fixup-lagged-json", _row7),
    ("row-8-already-closed-exit-0", _row8),
    ("row-9-refuse-ok-no-commit", _row9),
    ("row-10-refuse-ok-slice-in-progress", _row10),
    ("row-11-degraded-as-in-progress", _row11),
    ("row-12-refuse-prior-terminated-failed", _row12),
    ("row-13-refuse-corrupt-json", _row13),
]


@pytest.mark.parametrize("row_id,setup", MATRIX, ids=[r[0] for r in MATRIX])
def test_resume_matrix_row(monkeypatch, tmp_path, row_id, setup):
    sd, dd = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", sd / "slice.yaml", raising=False)
    monkeypatch.setattr(so, "DEBUG_DIR", dd, raising=False)

    expect = setup(tmp_path, sd, dd)

    if expect == "refuse":
        with pytest.raises(SystemExit) as exc:
            so._reconcile_resume_state()
        assert exc.value.code == 1
        return

    result = so._reconcile_resume_state()
    assert isinstance(result, dict), (
        f"row {row_id}: expected dict, got {type(result).__name__}"
    )

    if expect == "fresh":
        assert result.get("current_phase") == 1
        assert result.get("status") in {"IN_PROGRESS", None}
    elif expect == "re-init":
        assert result.get("current_phase") == 1
        assert result.get("status") == "IN_PROGRESS"
    elif expect.startswith("resume:"):
        n = int(expect.split(":")[1])
        assert result.get("current_phase") == n
        assert result.get("status") in {"IN_PROGRESS", "DEGRADED"}
    elif expect == "ok-exit":
        assert result.get("status") == "OK"
        assert result.get("exit_code") == 0
    elif expect == "fixup":
        assert result.get("status") == "OK"
        assert result.get("final_commit"), "fix-up must record the HEAD commit"


def test_resume_unmatched_triple_refuses_with_triple_printed(
    monkeypatch, tmp_path, capsys
):
    """Default refuse: unmatched (result.json-status, slice.yaml-status, HEAD-subject)
    triple exits 1 and prints the literal triple to stderr."""
    sd, dd = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", sd / "slice.yaml", raising=False)
    monkeypatch.setattr(so, "DEBUG_DIR", dd, raising=False)

    _slice_yaml(sd / "slice.yaml", "aborted", 2)  # unsupported status → unmatched
    _commit(tmp_path, "random")
    _write_result_json(dd, SLICE_ID, status="ESCALATED", exit_code=1)

    with pytest.raises(SystemExit) as exc:
        so._reconcile_resume_state()
    assert exc.value.code == 1

    out = capsys.readouterr()
    blob = out.err + out.out
    assert "ESCALATED" in blob or "aborted" in blob, (
        "default-refuse must print the triple (or its components) to stderr"
    )

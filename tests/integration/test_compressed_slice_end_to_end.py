"""Phase 2 RED — V6 of compression/slice-1-foundation intent.md.

The load-bearing acceptance test: a trivial slice runs four phases via
`scripts/slice_orchestrator.py` with zero human intervention, exits 0,
and produces `.claude/current-slice/integration/sweep-notes.md`.

Two layers:

  1. `test_v6_state_machine_runs_end_to_end` — default; monkeypatches
     the dispatch entry points to simulate successful phase agents
     writing their expected artifacts. Asserts the orchestrator's state
     machine threads the four phases, writes handoff commits, calls
     close_slice on Phase 4 OK, and leaves `slice.yaml status: complete`
     + `sweep-notes.md` in place.

  2. `test_v6_live_e2e_with_claude` — gated on `CAIRN_LIVE_E2E=1`;
     actually invokes `claude -p` inside a throwaway git worktree,
     following the "zero permission prompts" spec.

Both share the V1 artifact check: `docs/plans/2026-04-20-a1-spike-results.md`
exists and names a chosen path.

RED at Phase 2 because dispatch_phase_agent / dispatch_triager / the
revised state machine do not yet exist.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SPIKE_DOC = CAIRN_ROOT / "docs" / "plans" / "2026-04-20-a1-spike-results.md"

PROMPT_RE = re.compile(
    r"(sensitive-file|permission denied|requires approval|prompt user|awaiting approval)",
    re.IGNORECASE,
)


# --- V1 — spike-result artifact ---------------------------------------------


def test_v1_a1_spike_results_doc_exists_and_names_chosen_path():
    """intent.md:70 — spike log lists all three spikes with PASS/FAIL and names chosen path."""
    assert SPIKE_DOC.exists(), (
        f"intent.md:70/V1 — {SPIKE_DOC.relative_to(CAIRN_ROOT)} must exist; "
        "Phase 3 runs the three A1 spikes and writes this doc."
    )
    body = SPIKE_DOC.read_text().lower()
    for spike in ("spike 1", "spike 2", "spike 3"):
        assert spike in body, f"spike doc must mention {spike!r}; got:\n{body[:500]}"
    assert "pass" in body or "fail" in body, "spike doc must record PASS/FAIL outcomes"
    assert "path x" in body or "path y" in body, (
        "spike doc must name the chosen resolution path (X or Y)"
    )


# --- V6a — state-machine end-to-end via monkeypatched dispatch --------------


@pytest.fixture
def trivial_slice_workspace(tmp_path, monkeypatch):
    """Set up a throwaway workspace with a minimal slice.yaml and cd into it."""
    (tmp_path / ".claude" / "current-slice").mkdir(parents=True)
    (tmp_path / ".claude" / "current-slice" / "integration").mkdir()
    (tmp_path / ".claude" / "orchestrator-debug").mkdir()

    slice_yaml = tmp_path / ".claude" / "current-slice" / "slice.yaml"
    slice_yaml.write_text(
        "id: compression/e2e-trivial\n"
        'name: "compression/e2e-trivial"\n'
        "status: in-progress\n"
        "current_phase: 1\n"
        'brief: "trivial e2e fixture"\n'
    )

    # git init so handoff commits have somewhere to go
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )

    monkeypatch.chdir(tmp_path)
    return tmp_path


def _canned_phase_agent(role, inputs, *args, **kwargs):
    """Simulate a successful phase agent: write the artifact that phase owes
    and return a clean PhaseResult."""
    base = Path(".claude/current-slice")
    base.mkdir(parents=True, exist_ok=True)
    if role == "phase-1-writer":
        (base / "intent.md").write_text("---\nphase: 1\n---\nstub intent\n")
    elif role == "phase-2-skeptic":
        (base / "validation").mkdir(exist_ok=True)
        (base / "validation" / "approach.md").write_text("stub approach\n")
        (base / "validation" / "coupling-clusters.yaml").write_text(
            "clusters:\n  - name: implicit\n    files: []\n"
        )
    elif role == "phase-3-implementer":
        (base / "implementation").mkdir(exist_ok=True)
        (base / "implementation" / "notes.md").write_text("stub notes\n")
    elif role == "phase-4-integrator":
        (base / "integration").mkdir(exist_ok=True)
        (base / "integration" / "sweep-notes.md").write_text("stub sweep\n")
    return {
        "status": "OK",
        "commit_hash": "0" * 7,
        "summary": f"{role} canned OK",
    }


def _canned_triager(*_args, **_kwargs):
    return {"action": "ESCALATE_TO_USER", "target_phase": None, "rationale": "canned"}


def test_v6_state_machine_runs_end_to_end(trivial_slice_workspace, monkeypatch, capsys):
    """intent.md:75 — four phases, exit 0, sweep-notes.md, slice.yaml complete."""
    import slice_orchestrator as so

    assert hasattr(so, "dispatch_phase_agent"), (
        "intent.md:57 — dispatch_phase_agent must exist (RED precondition)"
    )
    assert hasattr(so, "dispatch_triager"), (
        "intent.md:58 — dispatch_triager must exist (RED precondition)"
    )

    monkeypatch.setattr(so, "dispatch_phase_agent", _canned_phase_agent)
    monkeypatch.setattr(so, "dispatch_triager", _canned_triager)

    rc = so.run_phase_loop(max_phase=4)
    assert rc == 0, f"run_phase_loop must exit 0 on happy path; got {rc}"

    sweep = Path(".claude/current-slice/integration/sweep-notes.md")
    assert sweep.exists(), "sweep-notes.md must be produced by Phase 4 OK"

    final_yaml = Path(".claude/current-slice/slice.yaml").read_text()
    assert "status: complete" in final_yaml, (
        f"slice.yaml must be marked complete after Phase 4 OK; got:\n{final_yaml}"
    )

    err = capsys.readouterr().err
    assert not PROMPT_RE.search(err), (
        f"intent.md:75 — zero permission prompts allowed on stderr; matched: {err!r}"
    )


def test_v6_four_phase_handoff_commits_present(trivial_slice_workspace, monkeypatch):
    """intent.md:75 — 'all four phases produced commits on the branch'."""
    import slice_orchestrator as so

    monkeypatch.setattr(so, "dispatch_phase_agent", _canned_phase_agent)
    monkeypatch.setattr(so, "dispatch_triager", _canned_triager)

    so.run_phase_loop(max_phase=4)

    log = subprocess.check_output(
        ["git", "log", "--pretty=%s"], text=True, cwd=trivial_slice_workspace
    )
    # Handoff commit per phase (1..4) plus the close_slice commit.
    for n in (1, 2, 3, 4):
        assert f"phase {n}" in log, (
            f"expected a commit mentioning 'phase {n}'; git log was:\n{log}"
        )


# --- V6b — live end-to-end (opt-in) -----------------------------------------


@pytest.mark.skipif(
    os.environ.get("CAIRN_LIVE_E2E") != "1" or shutil.which("claude") is None,
    reason="CAIRN_LIVE_E2E=1 and `claude` CLI required; this is the production path",
)
def test_v6_live_e2e_with_claude(tmp_path):
    """intent.md:75 — real orchestrator + real claude, throwaway worktree.

    Guarded by `CAIRN_LIVE_E2E=1` so CI can still run the rest of the suite
    without provisioning claude credentials. When run, it is the slice's
    exit criterion: four phases, zero prompts, sweep-notes.md.
    """
    worktree = tmp_path / "e2e-worktree"
    subprocess.run(
        ["git", "worktree", "add", "-b", "e2e-test", str(worktree), "HEAD"],
        cwd=CAIRN_ROOT,
        check=True,
    )
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(CAIRN_ROOT / "scripts" / "slice_orchestrator.py"),
                "--brief",
                "trivial-e2e: no-op slice used to prove autonomous dispatch",
            ],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=1800,
        )
        assert proc.returncode == 0, (
            f"orchestrator exit {proc.returncode}; stderr:\n{proc.stderr}"
        )
        assert not PROMPT_RE.search(proc.stderr or ""), (
            f"permission-prompt text leaked to stderr:\n{proc.stderr}"
        )
        sweep = (
            worktree / ".claude" / "current-slice" / "integration" / "sweep-notes.md"
        )
        assert sweep.exists(), "sweep-notes.md must exist after live E2E"
        yml = (worktree / ".claude" / "current-slice" / "slice.yaml").read_text()
        assert "status: complete" in yml
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=CAIRN_ROOT,
            check=False,
        )
        subprocess.run(["git", "branch", "-D", "e2e-test"], cwd=CAIRN_ROOT, check=False)

"""Phase 2 RED — substrate bug-fix contracts (B1–B5) + A3 docs gap.

Slice: housekeeping/post-inv008-and-substrate-bugs.

Each test asserts a public-interface contract specified in
.claude/current-slice/intent.md §V3, V7–V11. Phase-3 implementation is the
Builder's choice within the envelope.

  A3 — heartbeat env vars documented in operational-reference.md (intent V3)
  B1 — current_phase persisted across phase boundary (intent V7)
  B2 — phase-2-skeptic prompt forbids YAML-fragile coupling-clusters output
       and any sample fragment parses under yaml.safe_load (intent V8)
  B3 — init_new_slice normalizes dotted slug ids to hyphens (intent V9)
  B4 — pytest run does not dirty measurements/ (intent V10)
  B5 — close_slice commit subject is `slice: <id> — complete` and satisfies
       scripts/verify_handoff.sh check (c) (intent V11)

Stdlib + pytest only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------- shared fixtures -------------------------------------------------


def _init_project(
    tmp_path: Path, *, slice_id: str = "demo/slice-x", current_phase: int = 1
) -> Path:
    """Mirror the fixture used by tests/unit/test_close_slice_hardened.py so
    Phase-3 can reuse the same harness when fixing B1/B5."""
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        f"id: {slice_id}\n"
        f'name: "{slice_id}"\n'
        "status: in-progress\n"
        f"current_phase: {current_phase}\n"
        'brief: "demo brief"\n'
    )
    (slice_dir / "intent.md").write_text(
        f"---\nslice: {slice_id}\nphase: 1-intent\nenvelope: []\n---\nbody\n"
    )
    for n in (1, 2, 3, 4):
        (slice_dir / f"handoff-phase-{n}.md").write_text(
            f"---\nphase: {n}\n---\nphase-{n}-body\n"
        )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
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
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )
    return slice_dir


def _import_orchestrator(monkeypatch, tmp_path, slice_dir):
    sys.path.insert(0, str(SCRIPTS_DIR))
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so  # type: ignore

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    return so


# ---------- A3: heartbeat env-var documentation -----------------------------


def test_heartbeat_env_vars_documented_in_operational_reference():
    """A3 (intent V3): operational-reference.md MUST document both
    CAIRN_HEARTBEAT_INTERVAL and CAIRN_HEARTBEAT_STALE in its env-var
    section. Source-of-truth: ADR orchestrator-observability +
    CLAUDE.md "no hardcoded timeouts/sizes" convention.
    """
    doc = (REPO_ROOT / "docs" / "operational-reference.md").read_text()
    assert "CAIRN_HEARTBEAT_INTERVAL" in doc, (
        "operational-reference.md missing CAIRN_HEARTBEAT_INTERVAL row"
    )
    assert "CAIRN_HEARTBEAT_STALE" in doc, (
        "operational-reference.md missing CAIRN_HEARTBEAT_STALE row"
    )


# ---------- B1: current_phase persisted across phase boundary ---------------


def test_current_phase_persisted_across_phase_boundary(monkeypatch, tmp_path):
    """B1 (intent V7): after `handoff: phase 1 complete` is committed, a
    subsequent `--resume` MUST read current_phase >= 2 from slice.yaml. The
    persistence MUST happen before the next phase dispatch — not only at
    init_new_slice / close_slice. Concrete observable: drive run_phase_loop
    with a stub that returns OK on phase 1 then forces escalation on phase 2,
    then read slice.yaml.
    """
    slice_dir = _init_project(tmp_path)
    so = _import_orchestrator(monkeypatch, tmp_path, slice_dir)

    calls = {"n": 0}

    def fake_dispatch(role, inputs, envelope=None, timeout_hard=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"status": "OK", "commit_hash": "deadbee", "summary": "p1"}
        return {"status": "FAILED", "commit_hash": "fail", "summary": "p2 fail"}

    monkeypatch.setattr(so, "dispatch_phase_agent", fake_dispatch)
    so._init_state_dict(slice_id="demo/slice-x")

    rc = so.run_phase_loop(max_phase=4)
    assert rc == 1, "phase 2 forced FAILED twice → rc=1 expected"

    state = so.read_slice_state(slice_dir / "slice.yaml")
    assert state.get("current_phase") == 2, (
        "B1: slice.yaml.current_phase did not advance to 2 after "
        f"`handoff: phase 1 complete`; got {state.get('current_phase')!r}. "
        "Resume would re-dispatch Phase 1."
    )


# ---------- B2: phase-2-skeptic prompt YAML-safety directive ----------------


def test_phase_2_skeptic_prompt_documents_yaml_safety_for_clusters():
    """B2 (intent V8): the phase-2-skeptic agent prompt MUST explicitly
    instruct the writer to single-quote regex patterns in
    coupling-clusters.yaml (or equivalent YAML-safety guidance). Tested by
    structural grep on the prompt body.
    """
    prompt = (REPO_ROOT / ".claude" / "agents" / "phase-2-skeptic.md").read_text()
    lower = prompt.lower()
    has_quote_directive = (
        "single-quote" in lower
        or "single quote" in lower
        or "'pattern'" in lower
        or "yaml.safe_load" in lower
    )
    assert has_quote_directive, (
        "B2: phase-2-skeptic.md prompt is missing YAML-safety guidance for "
        "coupling-clusters regex patterns. Expected at least one of: "
        "single-quote / yaml.safe_load reference."
    )


def test_coupling_clusters_yaml_with_singlequoted_regex_round_trips():
    """B2 companion: a coupling-clusters.yaml fragment using single-quoted
    regex patterns (the form the prompt should mandate) MUST parse cleanly
    under yaml.safe_load. Locks the format the prompt instructs writers to
    emit.
    """
    sample = (
        "clusters:\n"
        "  - name: example\n"
        "    files:\n"
        "      - '^scripts/foo\\.py$'\n"
        "      - '^tests/unit/test_foo\\.py$'\n"
    )
    parsed = yaml.safe_load(sample)
    assert isinstance(parsed, dict)
    assert isinstance(parsed.get("clusters"), list)
    files = parsed["clusters"][0]["files"]
    # Round-trip the regex strings; they should compile.
    for pat in files:
        re.compile(pat)


# ---------- B3: slug dot→hyphen normalization in init_new_slice -------------


def test_init_new_slice_normalizes_dot_slug_to_hyphen(monkeypatch, tmp_path):
    """B3 (intent V9): init_new_slice given a brief whose phase-1-writer
    proposes `housekeeping/foo-1.2.3` MUST persist `housekeeping/foo-1-2-3`
    (dots normalized to hyphens). SLICE_ID_REGEX stays strict.
    """
    # Bare project skeleton; init_new_slice will create slice.yaml.
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
            "-q",
            "-m",
            "root",
        ],
        cwd=tmp_path,
        check=True,
    )
    monkeypatch.chdir(tmp_path)
    sys.path.insert(0, str(SCRIPTS_DIR))
    import slice_orchestrator as so  # type: ignore

    slice_yaml_path = tmp_path / ".claude" / "current-slice" / "slice.yaml"
    monkeypatch.setattr(so, "SLICE_YAML", slice_yaml_path, raising=False)
    monkeypatch.setattr(
        so,
        "DEBUG_DIR",
        tmp_path / ".claude" / "orchestrator-debug",
        raising=False,
    )

    def fake_dispatch(role, inputs, envelope=None, timeout_hard=None):
        # Writer proposes a dotted-version slug — pre-normalization shape.
        return {
            "status": "OK",
            "commit_hash": "writer1",
            "summary": "proposed",
            "proposed_slice_id": "housekeeping/foo-1.2.3",
        }

    monkeypatch.setattr(so, "dispatch_phase_agent", fake_dispatch)

    state = so.init_new_slice("housekeeping/foo-1.2.3 brief")
    assert state.get("id") == "housekeeping/foo-1-2-3", (
        "B3: init_new_slice did not normalize dotted slug 'housekeeping/foo-1.2.3' "
        f"→ 'housekeeping/foo-1-2-3'; got {state.get('id')!r}"
    )
    # And the regex should still admit the canonical form.
    assert so.SLICE_ID_REGEX.match("housekeeping/foo-1-2-3"), (
        "SLICE_ID_REGEX rejected canonical hyphenated form — regex must stay strict."
    )


# ---------- B4: measurement file untouched by pytest ------------------------


def test_pytest_run_does_not_dirty_measurements():
    """B4 (intent V10): a normal `uv run pytest` invocation that exercises
    test_context_budget MUST NOT leave docs/plans/measurements/ dirty.
    Builder may fix via either (a) gating the write behind a record flag or
    (b) idempotent-within-tolerance writes.

    Skips if `claude` CLI is unavailable (the inner test self-skips), making
    this a no-op in environments where the bug cannot manifest.
    """
    measurements_rel = "docs/plans/measurements/"
    pre = subprocess.run(
        ["git", "status", "--porcelain", "--", measurements_rel],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if pre.strip():
        pytest.skip(f"measurements/ already dirty pre-test: {pre.strip()!r}")

    claude_check = subprocess.run(
        ["claude", "--version"],
        capture_output=True,
        text=True,
    )
    if claude_check.returncode != 0:
        pytest.skip("claude CLI unavailable; B4 cannot manifest in this env")

    subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "tests/unit/test_context_budget.py::test_inv004_turn1_token_budget",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )

    post = subprocess.run(
        ["git", "status", "--porcelain", "--", measurements_rel],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert not post.strip(), (
        f"B4: pytest run dirtied {measurements_rel}: {post.strip()!r}. "
        "test_context_budget must not write to a tracked measurement file as "
        "a side effect of a default pytest invocation."
    )


# ---------- B5: close_slice commit subject satisfies verify_handoff (c) -----


def test_close_slice_commit_subject_matches_em_dash_pattern(monkeypatch, tmp_path):
    """B5 (intent V11): close_slice MUST write its terminal commit with subject
    `slice: <slice-id> — complete` (em-dash, slice-id present). This satisfies
    scripts/verify_handoff.sh check (c)'s `^slice: .* — complete$` regex.
    """
    slice_id = "demo/slice-x"
    slice_dir = _init_project(tmp_path, slice_id=slice_id)
    so = _import_orchestrator(monkeypatch, tmp_path, slice_dir)

    monkeypatch.setattr(
        so,
        "dispatch_phase_agent",
        lambda role, inputs, envelope=None, timeout_hard=None: {
            "status": "OK",
            "commit_hash": "dead",
            "summary": f"{role} ok",
        },
    )
    so._init_state_dict(slice_id=slice_id)

    rc = so.run_phase_loop()
    assert rc == 0, "stub dispatch should yield rc=0"
    so.close_slice(so._state)

    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    expected_pattern = rf"^slice: {re.escape(slice_id)} — complete$"
    assert re.match(expected_pattern, subject), (
        f"B5: close_slice commit subject {subject!r} does not match "
        f"required pattern {expected_pattern!r}. verify_handoff.sh check (c) "
        "requires `^slice: .* — complete$` (em-dash, slice-id present)."
    )


def test_close_slice_commit_passes_verify_handoff_check_c(monkeypatch, tmp_path):
    """B5 companion: after close_slice, scripts/verify_handoff.sh MUST exit 0
    against HEAD. Currently fails because the subject is `slice: complete`
    (no slice-id, no em-dash) — verify_handoff check (c) rejects it.
    """
    slice_id = "demo/slice-x"
    slice_dir = _init_project(tmp_path, slice_id=slice_id)
    so = _import_orchestrator(monkeypatch, tmp_path, slice_dir)

    monkeypatch.setattr(
        so,
        "dispatch_phase_agent",
        lambda role, inputs, envelope=None, timeout_hard=None: {
            "status": "OK",
            "commit_hash": "dead",
            "summary": f"{role} ok",
        },
    )
    so._init_state_dict(slice_id=slice_id)

    so.run_phase_loop()
    so.close_slice(so._state)

    verifier = REPO_ROOT / "scripts" / "verify_handoff.sh"
    result = subprocess.run(
        ["bash", str(verifier)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"B5: verify_handoff.sh exited {result.returncode} against "
        f"close_slice's HEAD commit. stderr: {result.stderr.strip()!r}"
    )

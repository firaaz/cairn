"""Phase 2 RED — compression/learnings-capture (retry).

Covers `_record_orchestrator_event` helper contract + orchestrator-side
emissions + archival pipeline wiring. Bound to the `orchestrator-events`
cluster (envelope: scripts/slice_orchestrator/{core,lifecycle,dispatch}.py
plus the `_ARTIFACT_RELPATHS` tuple).

Spec sources:
  - `.claude/current-slice/intent.md` §Helper contract, §Emission sites,
    §Archival wiring, §Verification.
  - `stash@{0}` partial Phase-3 carve from cost-discipline/lever-1-tier-retune
    (helper body, RE_DISPATCH + B15 emissions). Test contract is the spec —
    the stash is seed material only.

Expected at Phase 2 (RED):
  - t1a-d: `AttributeError` on `core._record_orchestrator_event` (helper absent).
  - t2a/t2b: `events.jsonl` not produced by `run_phase_loop` (emissions unwired).
  - t2c-e: emission-token presence in source (call-site grep) — RED until Phase 3
    wires the three remaining v1 emission sites (cost_threshold_breach,
    token_threshold_breach, agent_timeout). Brittleness explicitly accepted as
    the price of binding the otherwise-vacuous "all green" cluster to a RED
    progress signal — the same trade-off intent §Verification accepts for the
    phase-4-integrator.md prompt cluster.
  - t3a/t3b: `_ARTIFACT_RELPATHS` lacks the new entry; `_copy_artifacts_to_sweep_results`
    skips the missing events file silently.

Imports use ``slice_orchestrator`` (not ``scripts.slice_orchestrator``) per
``[tool.pytest.ini_options] pythonpath = ["scripts"]`` in ``pyproject.toml``.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
from pathlib import Path

import pytest


# --- shared fixtures --------------------------------------------------------


SLICE_ID = "compression/learnings-capture"


@pytest.fixture
def populated_current_slice(tmp_path, monkeypatch):
    """Build a `.claude/current-slice/` tree that mirrors the live envelope.

    Includes every path listed in `_ARTIFACT_RELPATHS` PLUS the new
    `integration/orchestrator-events.jsonl` so the archival test can copy a
    populated file. `chdir`s into tmp_path so all relative-path I/O the helper
    performs lands under the fixture tree.
    """
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    (cs / "validation").mkdir()
    (cs / "implementation").mkdir()
    (cs / "integration").mkdir()
    files = [
        "intent.md",
        "validation/approach.md",
        "implementation/notes.md",
        "integration/sweep-notes.md",
        "integration/orchestrator-events.jsonl",
        "handoff-phase-1.md",
        "handoff-phase-2.md",
        "handoff-phase-3.md",
        "handoff-phase-4.md",
        "integration/envelope-expansions.log",
    ]
    for rel in files:
        p = cs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"content of {rel}\n")
    yield cs


def _init_git_project(tmp_path: Path) -> Path:
    """Init a real git repo with a slice.yaml + intent.md so `_slice_id()`
    resolves and `commit_phase_handoff` can run inside the loop tests.
    """
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True, exist_ok=True)
    (slice_dir / "slice.yaml").write_text(
        f"id: {SLICE_ID}\nname: {SLICE_ID}\nstatus: in-progress\n"
        'current_phase: 1\nbrief: "b"\n'
    )
    (slice_dir / "intent.md").write_text(
        f"---\nslice: {SLICE_ID}\nphase: 1-intent\nenvelope: []\n---\n"
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "add",
            "-A",
        ],
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


# --- t1: helper contract ---------------------------------------------------


def test_t1a_helper_appends_jsonl_line(tmp_path, monkeypatch):
    """One call writes one JSON-decodable line carrying the canonical schema:
    `slice_id`, `event_type`, the supplied extra fields, and a `ts` key.
    """
    monkeypatch.chdir(tmp_path)
    from slice_orchestrator import core

    core._record_orchestrator_event(
        SLICE_ID,
        "phase_redispatch",
        from_phase=2,
        to_phase=1,
    )

    path = (
        tmp_path
        / ".claude"
        / "current-slice"
        / "integration"
        / "orchestrator-events.jsonl"
    )
    assert path.is_file(), f"helper must create {path}"
    lines = path.read_text().splitlines()
    assert len(lines) == 1, f"one call must emit exactly one line; got {lines!r}"
    record = json.loads(lines[0])
    assert record["slice_id"] == SLICE_ID
    assert record["event_type"] == "phase_redispatch"
    assert record["from_phase"] == 2
    assert record["to_phase"] == 1
    assert "ts" in record and isinstance(record["ts"], str) and record["ts"]


def test_t1b_helper_includes_iso8601_utc_timestamp(tmp_path, monkeypatch):
    """`ts` parses via `datetime.fromisoformat` and carries explicit UTC.

    Accepts both `+00:00` (the spec's canonical isoformat() output) and the
    legacy `Z` shorthand so a future stdlib swap does not regress the contract.
    """
    monkeypatch.chdir(tmp_path)
    from slice_orchestrator import core

    core._record_orchestrator_event(
        SLICE_ID, "agent_timeout", phase=3, timeout_seconds=1800
    )

    path = (
        tmp_path
        / ".claude"
        / "current-slice"
        / "integration"
        / "orchestrator-events.jsonl"
    )
    record = json.loads(path.read_text().splitlines()[0])
    ts = record["ts"]
    assert ts.endswith("+00:00") or ts.endswith("Z"), (
        f"ts must carry explicit UTC offset; got {ts!r}"
    )
    parsed = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.utcoffset() == datetime.timedelta(0), (
        f"parsed ts offset must be zero; got {parsed.utcoffset()!r}"
    )


def test_t1c_helper_appends_not_overwrites(tmp_path, monkeypatch):
    """Two successive calls produce two lines (append mode), not one overwrite."""
    monkeypatch.chdir(tmp_path)
    from slice_orchestrator import core

    core._record_orchestrator_event(
        SLICE_ID, "phase_redispatch", from_phase=2, to_phase=1
    )
    core._record_orchestrator_event(
        SLICE_ID, "redispatch_cap_exceeded", phase=2, count=2
    )

    path = (
        tmp_path
        / ".claude"
        / "current-slice"
        / "integration"
        / "orchestrator-events.jsonl"
    )
    lines = path.read_text().splitlines()
    assert len(lines) == 2, f"two calls must emit two lines; got {lines!r}"
    types = [json.loads(line)["event_type"] for line in lines]
    assert types == ["phase_redispatch", "redispatch_cap_exceeded"]


def test_t1d_helper_creates_parent_dir_if_missing(tmp_path, monkeypatch):
    """Helper is F5-tolerant: creates `integration/` if absent (operator-rebase
    corner). Equivalent to `path.parent.mkdir(parents=True, exist_ok=True)`.
    """
    monkeypatch.chdir(tmp_path)
    # Deliberately do NOT create .claude/current-slice/integration/.
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    assert not (cs / "integration").exists()

    from slice_orchestrator import core

    core._record_orchestrator_event(
        SLICE_ID, "phase_redispatch", from_phase=2, to_phase=1
    )
    assert (cs / "integration").is_dir()
    assert (cs / "integration" / "orchestrator-events.jsonl").is_file()


# --- t2: orchestrator-side emissions ---------------------------------------


def _drive_redispatch_loop(monkeypatch, tmp_path, *, phase2_responses):
    """Helper: stand up a real-git project + monkeypatch dispatch/triager so
    `run_phase_loop` exercises the RE_DISPATCH branch. `phase2_responses`
    is consumed FIFO for successive phase-2 dispatch calls.
    """
    slice_dir = _init_git_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )

    # Patch close_slice to a no-op so the loop returns cleanly without needing
    # sweep-notes / bundle / wipe wiring (out-of-scope for this test).
    monkeypatch.setattr(so, "close_slice", lambda state=None: None)

    phase2_iter = iter(phase2_responses)

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        if inputs.get("phase") == 2:
            try:
                return next(phase2_iter)
            except StopIteration:
                return {"status": "OK", "commit_hash": "f", "summary": "ok"}
        return {"status": "OK", "commit_hash": "f", "summary": "ok"}

    def phase3_stub(slice_id):
        return {"status": "OK", "commit_hash": "f", "summary": "ok"}

    def triager_stub(*args, **kwargs):
        return {"decision": "RE_DISPATCH", "target_phase": 1}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    monkeypatch.setattr(so, "dispatch_phase_3", phase3_stub)
    monkeypatch.setattr(so, "dispatch_triager", triager_stub)

    rc = None
    try:
        rc = so.run_phase_loop()
    except SystemExit as exc:
        rc = exc.code
    return rc


def _read_events(tmp_path):
    path = (
        tmp_path
        / ".claude"
        / "current-slice"
        / "integration"
        / "orchestrator-events.jsonl"
    )
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_t2a_redispatch_emits_event(tmp_path, monkeypatch):
    """A `RE_DISPATCH` triager outcome causes a `phase_redispatch` record with
    `from_phase` + `to_phase` populated. Mocks the dispatch boundary; no
    subprocess fires.
    """
    rc = _drive_redispatch_loop(
        monkeypatch,
        tmp_path,
        # First phase-2 call raises; second (after redispatch round-trip) succeeds.
        phase2_responses=[
            {"status": "RAISE_ISSUE", "commit_hash": "d", "summary": "raise"},
            {"status": "OK", "commit_hash": "f", "summary": "ok"},
        ],
    )
    assert rc == 0, f"loop must terminate cleanly; got rc={rc}"

    events = _read_events(tmp_path)
    redispatches = [e for e in events if e.get("event_type") == "phase_redispatch"]
    assert len(redispatches) >= 1, (
        f"RE_DISPATCH branch must emit at least one phase_redispatch event; got {events!r}"
    )
    record = redispatches[0]
    assert record.get("from_phase") == 2, f"from_phase must be 2; got {record!r}"
    assert record.get("to_phase") == 1, f"to_phase must be 1; got {record!r}"
    assert record.get("slice_id") == SLICE_ID
    assert "ts" in record


def test_t2b_b15_cap_emits_event(tmp_path, monkeypatch):
    """Second redispatch on the same source phase emits `redispatch_cap_exceeded`
    with `phase` + `count` populated (count semantics: count of redispatches
    attributed to that source phase, including the cap-tripping attempt — so
    `count >= 2` is the contract).
    """
    rc = _drive_redispatch_loop(
        monkeypatch,
        tmp_path,
        # Phase 2 raises every time → first triggers RE_DISPATCH, second trips cap.
        phase2_responses=[
            {"status": "RAISE_ISSUE", "commit_hash": "d", "summary": "raise"},
            {"status": "RAISE_ISSUE", "commit_hash": "d", "summary": "raise"},
        ],
    )
    assert rc == 1, f"cap trip must force exit 1; got rc={rc}"

    events = _read_events(tmp_path)
    caps = [e for e in events if e.get("event_type") == "redispatch_cap_exceeded"]
    assert len(caps) == 1, (
        f"cap trip must emit exactly one redispatch_cap_exceeded event; got {events!r}"
    )
    record = caps[0]
    assert record.get("phase") == 2, (
        f"phase must be 2 (the offending source); got {record!r}"
    )
    assert isinstance(record.get("count"), int), (
        f"count must be int; got {record.get('count')!r}"
    )
    assert record["count"] >= 2, (
        f"count must reflect the cap-tripping attempt (>=2); got {record!r}"
    )
    assert record.get("slice_id") == SLICE_ID


# --- t2c-e: call-site presence (progress signal for the three v1 emissions
# whose detection seam is not cleanly unit-mockable yet — INV-009 thresholds
# are both `None`; `agent_timeout` lives behind subprocess.TimeoutExpired).
# Brittleness explicitly accepted: the same trade-off intent §Verification
# makes for the phase-4-integrator.md prompt cluster — the alternative is no
# RED progress signal, which is exactly the failure mode the retry exists to
# close. Phase 3 satisfies these by adding one `_record_orchestrator_event`
# call per site with the canonical event_type token. -----------------------


def _read_source(rel):
    return Path(rel).read_text()


def test_t2c_cost_threshold_breach_call_site_present():
    """`core.py` carries a `_record_orchestrator_event` call passing
    `event_type="cost_threshold_breach"` (the INV-009 cost-breach detection
    site). Required fields per intent: `threshold_usd`, `observed_usd`.
    """
    text = _read_source("scripts/slice_orchestrator/core.py")
    assert '"cost_threshold_breach"' in text or "'cost_threshold_breach'" in text, (
        "core.py must wire a cost_threshold_breach emission (intent §Emission sites)"
    )
    # Pin the call shape: emission must travel through the helper, not bypass it.
    pattern = re.compile(
        r"_record_orchestrator_event\([^)]*cost_threshold_breach", re.DOTALL
    )
    assert pattern.search(text), (
        "cost_threshold_breach must be emitted via "
        "_record_orchestrator_event (intent §Helper contract)"
    )
    # Required-field tokens must appear in the same source file.
    assert "threshold_usd" in text, (
        "core.py emission must carry `threshold_usd` (intent §Emission sites)"
    )
    assert "observed_usd" in text, (
        "core.py emission must carry `observed_usd` (intent §Emission sites)"
    )


def test_t2d_token_threshold_breach_call_site_present():
    """`core.py` carries a `_record_orchestrator_event` call passing
    `event_type="token_threshold_breach"`. Required fields: `threshold_tokens`,
    `observed_tokens`.
    """
    text = _read_source("scripts/slice_orchestrator/core.py")
    assert '"token_threshold_breach"' in text or "'token_threshold_breach'" in text, (
        "core.py must wire a token_threshold_breach emission (intent §Emission sites)"
    )
    pattern = re.compile(
        r"_record_orchestrator_event\([^)]*token_threshold_breach", re.DOTALL
    )
    assert pattern.search(text), (
        "token_threshold_breach must be emitted via _record_orchestrator_event"
    )
    assert "threshold_tokens" in text, (
        "core.py emission must carry `threshold_tokens` (intent §Emission sites)"
    )
    assert "observed_tokens" in text, (
        "core.py emission must carry `observed_tokens` (intent §Emission sites)"
    )


def test_t2e_agent_timeout_call_site_present():
    """`dispatch.py` carries a `_record_orchestrator_event` call passing
    `event_type="agent_timeout"` somewhere in the same module that owns the
    `subprocess.TimeoutExpired` catch site. Required fields: `phase`,
    `timeout_seconds`.
    """
    text = _read_source("scripts/slice_orchestrator/dispatch.py")
    assert '"agent_timeout"' in text or "'agent_timeout'" in text, (
        "dispatch.py must wire an agent_timeout emission "
        "(intent §Emission sites — TimeoutExpired catch site)"
    )
    pattern = re.compile(r"_record_orchestrator_event\([^)]*agent_timeout", re.DOTALL)
    assert pattern.search(text), (
        "agent_timeout must be emitted via _record_orchestrator_event"
    )
    assert "timeout_seconds" in text, (
        "dispatch.py emission must carry `timeout_seconds` (intent §Emission sites)"
    )


def test_t2f_helper_call_site_count_at_least_six():
    """Defence in depth: intent §closes-when says
    `grep -n _record_orchestrator_event scripts/slice_orchestrator/{core,lifecycle,dispatch}.py`
    returns >=6 lines (1 def in core.py + 5 call sites — phase_redispatch,
    redispatch_cap_exceeded in lifecycle.py; cost/token threshold breach in
    core.py; agent_timeout in dispatch.py).
    """
    bodies = [
        _read_source(f"scripts/slice_orchestrator/{name}.py")
        for name in ("core", "lifecycle", "dispatch")
    ]
    total = sum(b.count("_record_orchestrator_event") for b in bodies)
    # 1 def + 5 call sites + each call site appears once more on the
    # invocation line; count tokens, not lines, so floor at >=6.
    assert total >= 6, (
        f"_record_orchestrator_event must appear >=6 times across "
        f"core/lifecycle/dispatch (1 def + 5 call sites); got {total}"
    )


# --- t3: archival pipeline -------------------------------------------------


def test_t3a_artifact_relpaths_includes_events_jsonl():
    """`_ARTIFACT_RELPATHS` MUST contain the new events-jsonl entry so the
    pre-wipe snapshot under `.claude/sweep-results/<slug>/artifacts/` carries
    the record (ADR slice-artifact-preservation D2).
    """
    from slice_orchestrator import lifecycle

    assert "integration/orchestrator-events.jsonl" in lifecycle._ARTIFACT_RELPATHS, (
        f"_ARTIFACT_RELPATHS must include 'integration/orchestrator-events.jsonl'; "
        f"got {lifecycle._ARTIFACT_RELPATHS!r}"
    )


def test_t3b_lifecycle_archives_events_jsonl(populated_current_slice):
    """`_copy_artifacts_to_sweep_results` snapshots a populated events file
    byte-identically into the sweep-results artifacts tree.
    """
    from slice_orchestrator import lifecycle

    pre_close_yaml = f"id: {SLICE_ID}\nstatus: in-progress\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)

    slug = SLICE_ID.replace("/", "-")
    target = Path(".claude/sweep-results") / slug / "artifacts"
    src = populated_current_slice / "integration" / "orchestrator-events.jsonl"
    dst = target / "integration" / "orchestrator-events.jsonl"
    assert dst.is_file(), (
        f"events file must be archived under {dst}; got missing target"
    )
    assert dst.read_bytes() == src.read_bytes(), (
        "archived events file must be byte-identical to the source"
    )


def test_t3c_lifecycle_tolerates_missing_events_jsonl(tmp_path, monkeypatch):
    """A slice that emitted no orchestrator events does NOT fail the close
    (intent §Archival wiring — F5-tolerant per ADR slice-artifact-preservation
    D6b). Missing source file → silent skip.
    """
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    (cs / "integration").mkdir()
    # Only sweep-notes present; events-jsonl deliberately absent.
    (cs / "integration" / "sweep-notes.md").write_text("notes\n")

    from slice_orchestrator import lifecycle

    # MUST NOT raise.
    lifecycle._copy_artifacts_to_sweep_results(
        SLICE_ID, f"id: {SLICE_ID}\nstatus: in-progress\n"
    )
    slug = SLICE_ID.replace("/", "-")
    target = Path(".claude/sweep-results") / slug / "artifacts"
    assert (target / "integration" / "sweep-notes.md").exists()
    assert not (target / "integration" / "orchestrator-events.jsonl").exists()

"""Contract for the using-cairn SessionStart carrier (ADR using-cairn-carrier-contract, Approach D).

Pins the carrier's mechanical surface:
  - fired-detection: first stdout line is the machine marker CAIRN_CARRIER_FIRED (D2);
  - never gates: exit 0 on every path (D4);
  - dynamic emission: an active-intent pointer on resume, a no-intent statement otherwise (D2);
  - state-aware: only an intent thread marked `open` in the handoff is emitted as active (D5, INV-002);
  - neutral: NO imperative instruction prose — the verified L-012 hard-refusal hazard (D5);
  - budget: emission byte-clamped, env-overridable (D3);
  - cairn-internal: registered in local .claude/settings.json SessionStart, NOT the shipped template (D6).

Render-tested only: this proves the script emits correctly when invoked, NOT that Claude Code
injects it on a host — "fired on host" is a Trial-E integration observation (D2). Subprocess +
stdlib; no module under test (honest-minimal — the carrier is a bash hook like the surviving guards).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
CARRIER = CAIRN_ROOT / "checks" / "using-cairn-carrier.sh"
SETTINGS = CAIRN_ROOT / ".claude" / "settings.json"

FIRED_MARKER = "CAIRN_CARRIER_FIRED"

# Imperative instruction shapes that re-create the L-012 tier-sensitive hard-refusal hazard.
BANNED_IMPERATIVES = (
    "run the",
    "you must",
    "must run",
    "do not proceed",
    "cannot run",
    "/start",
)


def _run_carrier(project_dir: Path, *, env_extra: dict | None = None) -> str:
    if not CARRIER.is_file():
        pytest.fail(f"carrier script missing at {CARRIER}")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)}
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        ["bash", str(CARRIER)],
        input=json.dumps({"hook_event_name": "SessionStart", "source": "startup"}),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir),
    )
    assert proc.returncode == 0, (
        f"carrier exited {proc.returncode}; stderr={proc.stderr}"
    )
    return proc.stdout


def _handoff(project_dir: Path, *lines: str) -> None:
    h = project_dir / ".claude" / "handoff.md"
    h.parent.mkdir(parents=True, exist_ok=True)
    h.write_text("\n".join(lines) + "\n")


def _intent(project_dir: Path, feature: str) -> str:
    d = project_dir / ".claude" / "skill-runs" / feature
    d.mkdir(parents=True, exist_ok=True)
    (d / "intent.md").write_text(f"---\nid: {feature}\n---\n\n## What\nDemo.\n")
    return f".claude/skill-runs/{feature}/intent.md"


# --- D2: fired-detection + D4: never gates --------------------------------------


def test_carrier_first_line_is_the_fired_marker(tmp_path):
    assert _run_carrier(tmp_path).splitlines()[0] == FIRED_MARKER


def test_carrier_never_exits_nonzero_so_it_never_gates(tmp_path):
    # No handoff, no intent, JSON on stdin — still exits 0 and fires.
    assert FIRED_MARKER in _run_carrier(tmp_path)


# --- D2: dynamic emission — resume vs no-intent ---------------------------------


def test_carrier_emits_no_intent_signal_when_none_active(tmp_path):
    assert "no active intent" in _run_carrier(tmp_path).lower()


def test_carrier_emits_intent_pointer_on_open_thread(tmp_path):
    pointer = _intent(tmp_path, "demo")
    _handoff(tmp_path, f"- {pointer} open demo-thread")
    out = _run_carrier(tmp_path)
    assert pointer in out
    assert "no active intent" not in out.lower()


# --- D5: state-aware — a non-open thread is not active ---------------------------


def test_carrier_ignores_non_open_intent_thread(tmp_path):
    pointer = _intent(tmp_path, "old")
    _handoff(tmp_path, f"- {pointer} deferred legacy-thread")
    out = _run_carrier(tmp_path)
    assert pointer not in out
    assert "no active intent" in out.lower()


# --- D5: neutral emission — the L-012 hazard guard ------------------------------


def test_carrier_emits_no_imperative_prose_no_intent(tmp_path):
    out = _run_carrier(tmp_path).lower()
    for phrase in BANNED_IMPERATIVES:
        assert phrase not in out, (
            f"carrier no-intent emission contains imperative prose: {phrase!r} (L-012)"
        )


def test_carrier_emits_no_imperative_prose_on_resume(tmp_path):
    pointer = _intent(tmp_path, "demo")
    _handoff(tmp_path, f"- {pointer} open demo-thread")
    out = _run_carrier(tmp_path).lower()
    for phrase in BANNED_IMPERATIVES:
        assert phrase not in out, (
            f"carrier resume emission contains imperative prose: {phrase!r} (L-012)"
        )


# --- D3: byte-budget clamp ------------------------------------------------------


def test_carrier_clamps_payload_to_budget(tmp_path):
    out = _run_carrier(tmp_path, env_extra={"CAIRN_CARRIER_BUDGET_BYTES": "32"})
    assert len(out.encode()) <= 32, (
        f"budget clamp failed: emitted {len(out.encode())} bytes for a 32-byte cap"
    )


def test_carrier_default_budget_is_within_2k_token_proxy(tmp_path):
    assert len(_run_carrier(tmp_path).encode()) <= 8000


# --- D6: cairn-internal registration (local settings, NOT the shipped template) --


def test_carrier_registered_in_local_settings_sessionstart():
    data = json.loads(SETTINGS.read_text())
    sessionstart = data.get("hooks", {}).get("SessionStart")
    assert sessionstart, (
        ".claude/settings.json must declare a SessionStart entry for the carrier"
    )
    commands = [
        h.get("command", "")
        for entry in sessionstart
        for h in (entry.get("hooks") or [])
    ]
    assert any("using-cairn-carrier.sh" in c for c in commands), (
        "SessionStart must invoke the carrier"
    )


def test_carrier_not_shipped_to_consumers():
    # D6 cairn-internal-first: the carrier must NOT be in the build_dist allow-list
    # (it would ship to every consumer). Consumer shipping is deferred to the D7 ADR.
    build = (CAIRN_ROOT / "scripts" / "build_dist.py").read_text()
    assert "using-cairn-carrier.sh" not in build, (
        "carrier must stay cairn-internal until the D7 retirement ADR (ADR using-cairn-carrier-contract D6)"
    )

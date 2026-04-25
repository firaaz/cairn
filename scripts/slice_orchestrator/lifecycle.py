"""Phase loop, slice initialization, slice close, signal/atexit integration.

INV-008 slice-close-contract: ``close_slice`` is the sole producer of the
``slice: <id> — complete`` commit. ``run_phase_loop`` skips the Phase-4
boundary handoff commit so that contract holds.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
from pathlib import Path

import yaml

from . import dispatch as _dispatch_mod
from .core import (
    ROLE_FOR_PHASE,
    SLICE_YAML,
    _iso_now,
    _resolve_timeout,
    is_valid_slice_id,
    _normalize_slice_id,
)
from .dispatch import (
    dispatch_phase_3,
    dispatch_phase_agent,
    dispatch_triager,
)
from .git import _git, _git_head_safe
from .resume import (
    _current_phase,
    _persist_current_phase,
    _persist_redispatch,
    _slice_brief,
    _slice_id,
    _write_slice_state,
    read_slice_state,
)
from .telemetry import (
    _persist_state,
    _state,
    _update_state,
    _write_result_md,
)


def _bundle_handoff_md():
    """Concatenate the four phase handoffs (+ sweep-notes) into .claude/handoff.md."""
    handoff = Path(".claude/handoff.md")
    handoff.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for n in range(1, 5):
        p = Path(f".claude/current-slice/handoff-phase-{n}.md")
        if p.exists():
            parts.append(p.read_text())
    sweep = Path(".claude/current-slice/integration/sweep-notes.md")
    if sweep.exists():
        parts.append(sweep.read_text())
    handoff.write_text("\n---\n".join(parts) if parts else "")
    return handoff


def _wipe_current_slice():
    """Delete everything under .claude/current-slice/ except slice.yaml (DC-5).

    - FileNotFoundError is tolerated (F5 operator-rebase corner).
    - Other OSError propagates as RuntimeError.
    """
    slice_dir = Path(".claude/current-slice")
    if not slice_dir.exists():
        return

    # Walk deepest-first so directories become empty before rmdir.
    paths = sorted(slice_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for p in paths:
        if p.is_file() or p.is_symlink():
            if p.name == "slice.yaml" and p.parent == slice_dir:
                continue
            try:
                os.unlink(str(p))
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise RuntimeError(f"wipe failed for {p}: {exc}") from exc
        elif p.is_dir():
            try:
                p.rmdir()
            except FileNotFoundError:
                continue
            except OSError:
                # Non-empty (e.g. slice.yaml parent) — leave in place.
                continue


def _is_slice_already_closed(state=None):
    """DC-3 precondition check — all four signals must be satisfied."""
    # Signal 1: slice.yaml exists and status=complete
    if not SLICE_YAML.exists():
        return False
    try:
        sy = read_slice_state(SLICE_YAML)
    except yaml.YAMLError:
        return False
    if not isinstance(sy, dict) or sy.get("status") != "complete":
        return False

    # Signal 2: handoff.md present and non-empty
    handoff = Path(".claude/handoff.md")
    if not handoff.exists():
        return False
    try:
        if not handoff.read_text().strip():
            return False
    except OSError:
        return False

    # Signal 3: current-slice/ contains only slice.yaml (files)
    slice_dir = Path(".claude/current-slice")
    if slice_dir.exists():
        files = sorted(
            p.relative_to(slice_dir).as_posix()
            for p in slice_dir.rglob("*")
            if p.is_file()
        )
        if files != ["slice.yaml"]:
            return False

    # Signal 4: HEAD subject matches `slice: <id> — complete` (B5 tightened) or
    # the legacy `slice: complete` shape (backward-compat for fixtures /
    # operator-rebased histories).
    try:
        proc = _git("log", "-1", "--format=%s")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    subject = (proc.stdout or "").strip()
    if subject != "slice: complete" and not re.match(
        r"^slice: .+ — complete$", subject
    ):
        return False

    return True


def commit_phase_handoff(phase, summary, commit_hash):
    """Stage + commit the phase agent's handoff-phase-N.md.

    Intentionally does NOT overwrite file content — the phase agent owns that
    body. Uses --allow-empty so the orchestrator records the phase boundary
    even if the agent already committed the handoff file itself. B11.
    """
    path = Path(f".claude/current-slice/handoff-phase-{phase}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _git("add", str(path))
    # Stage phase-1-writer's full declared write surface
    # (.claude/agents/phase-1-writer.md:9) at the handoff boundary.
    # Guarded by path.exists() so Phases 2/3/4 (which do not touch
    # either path) are no-ops — preserves INV-008 DC-4.
    intent_path = Path(".claude/current-slice/intent.md")
    if intent_path.exists():
        _git("add", str(intent_path))
    feature_id = _slice_id().split("/", 1)[0]
    feature_path = Path(f".claude/features/{feature_id}.yaml")
    if feature_path.exists():
        _git("add", str(feature_path))
    _git("commit", "--allow-empty", "-m", f"handoff: phase {phase} complete")


def _dispatch_for_phase(phase, role, inputs, envelope, timeout):
    if phase == 3:
        return dispatch_phase_3(_slice_id())
    return dispatch_phase_agent(role, inputs, envelope, timeout)


def _clean_shutdown(signum, frame):
    """B13: SIGINT/SIGTERM handler — terminate active child, then exit.

    Slice 3 D6 integration: before exiting, records `status=SIGNALED` +
    `exit_code` on the module-level `_state` so the atexit terminal writer
    persists the signal-caused terminal state.
    """
    grace = int(os.environ.get("CAIRN_SHUTDOWN_GRACE_S", "5"))
    child = _dispatch_mod._active_child
    if child is not None:
        try:
            child.terminate()
        except Exception:
            pass
        try:
            child.wait(timeout=grace)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass
    exit_code = 130 if signum == signal.SIGINT else 143
    try:
        if _state and _state.get("slice_id"):
            _update_state(status="SIGNALED", exit_code=exit_code, ended_at=_iso_now())
    except Exception:
        pass
    sys.exit(exit_code)


def _register_signal_handlers():
    try:
        signal.signal(signal.SIGINT, _clean_shutdown)
        signal.signal(signal.SIGTERM, _clean_shutdown)
    except (ValueError, OSError):
        # non-main thread or platform without these signals
        pass


def run_phase_loop(max_phase=4):
    _register_signal_handlers()
    phase = _current_phase()
    redispatch_count: dict[int, int] = {}
    while 1 <= phase <= max_phase:
        role = ROLE_FOR_PHASE[phase]
        inputs = {"phase": phase, "role": role, "slice_id": _slice_id()}
        brief = _slice_brief()
        if brief:
            inputs["brief"] = brief
        envelope = None
        timeout = _resolve_timeout(role, None)
        result = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
        status = result.get("status", "")

        if status == "OK":
            # DC-4 code layer: suppress the per-phase handoff commit at the
            # Phase-4 boundary; close_slice is the sole source of the final
            # `slice: complete` commit.
            if phase < max_phase:
                commit_phase_handoff(
                    phase,
                    result.get("summary", ""),
                    result.get("commit_hash", ""),
                )
                _persist_current_phase(phase + 1)
            phase += 1
            continue

        if status == "FAILED":
            retry = _dispatch_for_phase(phase, role, inputs, envelope, timeout)
            if retry.get("status") == "OK":
                if phase < max_phase:
                    commit_phase_handoff(
                        phase,
                        retry.get("summary", ""),
                        retry.get("commit_hash", ""),
                    )
                    _persist_current_phase(phase + 1)
                phase += 1
                continue
            print(
                f"orchestrator: phase {phase} failed twice; escalating",
                file=sys.stderr,
            )
            return 1

        if status == "RAISE_ISSUE":
            # B15: cap re-dispatch from the same source phase to 1.
            if redispatch_count.get(phase, 0) >= 1:
                print(
                    f"orchestrator: phase {phase} re-dispatched twice; "
                    f"escalating per design §6.1",
                    file=sys.stderr,
                )
                return 1
            triager = dispatch_triager(
                issue_hash=result.get("commit_hash", ""),
                phase=phase,
                slice_id=_slice_id(),
            )
            action = triager.get("action") or triager.get("decision") or ""
            if action == "ESCALATE_TO_USER":
                print(
                    "orchestrator: triager escalated to user",
                    file=sys.stderr,
                )
                return 1
            if action == "RE_DISPATCH":
                target = triager.get("target_phase")
                if not isinstance(target, int) or not (1 <= target <= max_phase):
                    print(
                        f"orchestrator: invalid target_phase {target!r}; aborting",
                        file=sys.stderr,
                    )
                    return 1
                try:
                    _persist_redispatch(phase, target)
                except subprocess.CalledProcessError as exc:
                    print(
                        f"orchestrator: redispatch persist failed: {exc}",
                        file=sys.stderr,
                    )
                    return 1
                redispatch_count[phase] = redispatch_count.get(phase, 0) + 1
                phase = target
                continue
            if action == "ABORT":
                _abort_slice()
                return 1
            print(
                f"orchestrator: triager returned unknown action {action!r}",
                file=sys.stderr,
            )
            return 1

        print(
            f"orchestrator: phase {phase} returned unknown status {status!r}",
            file=sys.stderr,
        )
        return 1

    if SLICE_YAML.exists():
        try:
            close_slice(read_slice_state(SLICE_YAML))
        except (OSError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
            print(
                f"orchestrator: close_slice failed: {exc}",
                file=sys.stderr,
            )
            return 1
    return 0


def _abort_slice():
    if not SLICE_YAML.exists():
        return
    try:
        state = read_slice_state(SLICE_YAML)
    except yaml.YAMLError:
        state = {}
    if not isinstance(state, dict):
        state = {}
    state["status"] = "aborted"
    _write_slice_state(state)
    try:
        _git("add", str(SLICE_YAML))
        _git("commit", "--allow-empty", "-m", "slice: aborted by triager")
    except subprocess.CalledProcessError:
        pass


def init_new_slice(brief):
    result = dispatch_phase_agent(
        "phase-1-writer",
        {
            "phase": 1,
            "role": "phase-1-writer",
            "slice_id": "unknown/unknown",
            "brief": brief,
            "ask": "propose_slice_id",
        },
    )
    proposed = result.get("proposed_slice_id", "") if isinstance(result, dict) else ""
    proposed = _normalize_slice_id(proposed)
    if not is_valid_slice_id(proposed):
        # Fallback: record the brief even when the writer did not propose an id;
        # the operator (or a follow-up phase-1 run) can rename the slice later.
        proposed = "pending/slice"
    SLICE_YAML.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "id": proposed,
        "name": proposed,
        "status": "in-progress",
        "current_phase": 1,
        "brief": brief,
    }
    _write_slice_state(state)
    try:
        _git("add", str(SLICE_YAML))
        _git("commit", "--allow-empty", "-m", f"slice: {proposed} — init")
    except subprocess.CalledProcessError:
        pass
    return read_slice_state(SLICE_YAML)


def close_slice(state=None):
    """INV-008 slice-close contract: DC-3 idempotent, DC-4 sole commit source,
    DC-5 explicit wipe, DC-7 slug-keyed observability persistence.

    Order: sweep-notes presence check → slice.yaml → bundle → wipe → commit
    `slice: complete`.
    """
    if _is_slice_already_closed(state):
        return

    # Step 0: D2 presence check — sweep-notes.md must exist before any state
    # mutation (slice.yaml write, bundle, wipe, commit). Compression §8 D2
    # elevates "committed-artifact-first" to principle; INV-008 DC-4 keeps
    # close_slice as the sole `slice: complete` commit site. Abort with
    # FAILED-terminal observability and non-zero exit when missing.
    sweep_notes = Path(".claude/current-slice/integration/sweep-notes.md")
    if not sweep_notes.is_file():
        reason = "sweepnotes-missing-at-close"
        print(
            f"orchestrator: close aborted — {sweep_notes} absent; "
            "INV-008 DC-4 / compression §8 D2 require sweep-notes.md before "
            "`slice: <id> — complete`",
            file=sys.stderr,
        )
        if _state and _state.get("slice_id"):
            _update_state(
                status="FAILED",
                exit_code=1,
                ended_at=_iso_now(),
                reason=reason,
            )
            try:
                _persist_state(_state)
            except SystemExit:
                raise
            except Exception as exc:
                print(
                    f"orchestrator: FAILED-branch persist_state failed: {exc}",
                    file=sys.stderr,
                )
        sys.exit(1)

    # Step 1: slice.yaml → status=complete, current_phase=max_phase.
    try:
        sy = read_slice_state(SLICE_YAML) if SLICE_YAML.exists() else {}
    except yaml.YAMLError:
        sy = {}
    if not isinstance(sy, dict):
        sy = {}
    sy["status"] = "complete"
    sy["current_phase"] = 4
    _write_slice_state(sy)

    # Step 2: bundle handoff.md before wipe removes the inputs.
    handoff = _bundle_handoff_md()

    # Drift detector (DC-4 layer 3): last commit must NOT be a phase-4 handoff.
    try:
        prior = _git("log", "-1", "--format=%s").stdout.strip()
        if prior == "handoff: phase 4 complete":
            print(
                "orchestrator: drift — HEAD is `handoff: phase 4 complete`; "
                "Phase-4 agent committed directly (DC-4 anti-behavior).",
                file=sys.stderr,
            )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Step 3: wipe current-slice (DC-5 strict; F5-tolerant).
    _wipe_current_slice()

    # Step 4: sole `slice: <id> — complete` commit (DC-4 + B5-tightened).
    slice_id_for_subject = sy.get("id") or "unknown/unknown"
    _git("add", "-f", str(SLICE_YAML), str(handoff))
    try:
        _git("add", "-u", ".claude/current-slice")
    except subprocess.CalledProcessError:
        pass
    # Extended add surface: every path phase-4-integrator is contracted to
    # write (.claude/agents/phase-4-integrator.md:9). Staging here, not in a
    # new commit site — INV-008 DC-4 preserved.
    for extra in (Path(".claude/sweep.yaml"), Path(".claude/handoff.md")):
        if extra.exists():
            try:
                _git("add", "-f", str(extra))
            except subprocess.CalledProcessError:
                pass
    sweep_results = Path(".claude/sweep-results")
    if sweep_results.is_dir():
        try:
            _git("add", "-A", str(sweep_results))
        except subprocess.CalledProcessError:
            pass
    _git(
        "commit",
        "--allow-empty",
        "-m",
        f"slice: {slice_id_for_subject} — complete",
    )

    # Step 5: persist terminal observability state.
    if _state and _state.get("slice_id"):
        head = _git_head_safe()
        _update_state(
            status="OK",
            exit_code=0,
            ended_at=_iso_now(),
            final_commit=head,
            summary=_state.get("summary") or "slice closed",
        )
        try:
            _persist_state(_state)
        except SystemExit:
            raise
        except Exception as exc:
            print(
                f"orchestrator: close-time persist_state failed: {exc}",
                file=sys.stderr,
            )
        try:
            _write_result_md(_state)
        except Exception as exc:
            print(
                f"orchestrator: close-time write_result_md failed: {exc}",
                file=sys.stderr,
            )


def legacy_start_slice():
    print(
        "orchestrator: --legacy invoked; follow commands/claude-code/start-slice-legacy.md "
        "manually for the prose-protocol path."
    )
    return 0

"""Phase 2 RED — compression/phase-1-handoff-stage-surface.

``scripts/slice_orchestrator.py:commit_phase_handoff`` MUST stage every
path that the Phase-1 writer is contracted to produce
(``.claude/agents/phase-1-writer.md:9``). Specifically the
``handoff: phase N complete`` commit tree, at the Phase-1 boundary, must
pick up:

  * ``.claude/current-slice/intent.md`` — written by phase-1-writer but
    currently orphaned (outside the staging block at lines 1441-1452).
    RED today.
  * ``.claude/features/<feature>.yaml`` — also written by phase-1-writer
    at slice init/amendment; currently orphaned and requires chore-tail
    commits to recover (a8d8f23, dbea33c). RED today.

Each new stage must be guarded by ``if path.exists(): _git("add", ...)``
mirroring the existing ``handoff-phase-{n}.md`` pattern so that at Phases
2/3/4 — where neither path is touched — the stage becomes a no-op by
construction (empty-diff `_git add` on an unchanged file is equivalent
to today's behaviour; a missing file produces no ``add`` call at all).
This preserves INV-008 DC-4: ``commit_phase_handoff`` stays a per-phase
handoff-boundary staging function producing only ``handoff: phase N
complete`` commits; ``close_slice`` remains the sole producer of the
``slice: <id> — complete`` commit.

Tests are RED/guard split:

* R1a / R1b — intent.md and ``.claude/features/<feature>.yaml`` stage
  when present at Phase 1. Today these paths are absent from the add
  list: RED.
* R2a / R2b — neither path is staged when absent. Today this holds
  trivially (no add at all); after the fix the ``path.exists()`` guard
  must preserve it. These are contract-guards against an unguarded
  ``_git("add", ...)`` regression in Phase 3's implementation.

Ambiguity resolution
--------------------
The intent.md draft references ``commit_phase_handoff(phase=1,
state=...)`` and ``_slice_id(state)``; the authoritative orchestrator
public interface (``slice_orchestrator.py:1441`` and ``:1481``) has
signatures ``commit_phase_handoff(phase, summary, commit_hash)`` and
``_slice_id()`` (no state argument; reads ``SLICE_YAML`` directly).
Tests use the real signatures — the intent's ``state=...`` is a
Phase-1 shorthand, not a contract assertion.
"""

from __future__ import annotations

from pathlib import Path


# ---------- fixtures --------------------------------------------------------


def _init_project(tmp_path: Path) -> Path:
    """Seed a minimal ``.claude/current-slice/slice.yaml`` so that
    ``_slice_id()`` can resolve the feature-id (segment before ``/``).
    Slice id ``demo/slice-x`` ⇒ feature-id ``demo`` ⇒ feature-file path
    ``.claude/features/demo.yaml``.
    """
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/slice-x\n"
        'name: "demo/slice-x"\n'
        "status: in-progress\n"
        "current_phase: 1\n"
        'brief: "demo brief"\n'
    )
    return slice_dir


def _patched_so(monkeypatch, tmp_path):
    """Patch the orchestrator module to read SLICE_YAML from the fixture
    and stub out ``_git`` so commits never touch disk.

    Returns ``(so, slice_dir, calls)`` where ``calls`` is a mutable list
    of ``_git`` invocations: each entry is the positional args list.
    """
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)

    calls: list[list[str]] = []

    def fake_git(*args):
        calls.append(list(args))
        return ""

    monkeypatch.setattr(so, "_git", fake_git, raising=True)
    return so, slice_dir, calls


def _adds(calls):
    """Return the list of paths staged via ``_git("add", <path>)``.

    Accepts both the single-path form (``_git("add", str(path))``) and
    the multi-arg form (``_git("add", "-f", str(path))``) defensively.
    """
    staged: list[str] = []
    for c in calls:
        if not c or c[0] != "add":
            continue
        # drop leading flags like ``-f``; collect positional path tokens
        for tok in c[1:]:
            if not tok.startswith("-"):
                staged.append(tok)
    return staged


# ---------- R1a — intent.md stages when present -----------------------------


def test_intent_md_stages_at_phase_1_handoff_when_present(monkeypatch, tmp_path):
    """phase-1-writer declared write ``.claude/current-slice/intent.md``
    must appear in the ``_git("add", ...)`` sequence emitted by
    ``commit_phase_handoff(phase=1, ...)``.

    Today: RED — ``commit_phase_handoff`` stages only
    ``handoff-phase-1.md`` (lines 1441-1452), so intent.md is orphaned.
    """
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path)

    # phase-1-writer's declared writes land on disk before the
    # orchestrator's handoff boundary runs.
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/slice-x\nphase: 1-intent\nenvelope: []\n---\nbody\n"
    )
    (slice_dir / "handoff-phase-1.md").write_text("---\nphase: 1\n---\nphase-1-body\n")

    so.commit_phase_handoff(1, "phase-1 summary", "deadbeef")

    staged = _adds(calls)
    assert ".claude/current-slice/intent.md" in staged, (
        "phase-1-writer declared write `.claude/current-slice/intent.md` "
        "must be staged at the Phase-1 handoff boundary "
        f"(today orphaned — staged paths were {staged!r})"
    )


# ---------- R1b — .claude/features/<feature>.yaml stages when present -------


def test_feature_file_stages_at_phase_1_handoff_when_present(monkeypatch, tmp_path):
    """phase-1-writer declared write ``.claude/features/<feature>.yaml``
    must appear in the ``_git("add", ...)`` sequence emitted by
    ``commit_phase_handoff(phase=1, ...)``.

    Feature-id is resolved from ``slice.yaml`` id (segment before ``/``)
    via the existing ``_slice_id()`` helper; fixture id ``demo/slice-x``
    ⇒ feature-id ``demo`` ⇒ expected path
    ``.claude/features/demo.yaml``.

    Today: RED — the orchestrator's staging block does not reach into
    ``.claude/features/`` at all, leaving feature-file writes orphaned
    (evidenced by a8d8f23 / dbea33c chore-tail commits).
    """
    so, _slice_dir, calls = _patched_so(monkeypatch, tmp_path)

    features_dir = tmp_path / ".claude" / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "demo.yaml").write_text("id: demo\nname: demo\nslices: []\n")

    so.commit_phase_handoff(1, "phase-1 summary", "deadbeef")

    staged = _adds(calls)
    assert ".claude/features/demo.yaml" in staged, (
        "phase-1-writer declared write `.claude/features/demo.yaml` "
        "(feature-id resolved from slice.yaml id `demo/slice-x`) must be "
        "staged at the Phase-1 handoff boundary "
        f"(today orphaned — staged paths were {staged!r})"
    )


# ---------- R2a — no-op when intent.md is absent ----------------------------


def test_intent_md_not_staged_when_absent(monkeypatch, tmp_path):
    """The new intent.md stage must be guarded by ``path.exists()``.

    If intent.md was not written by this phase (the steady-state case
    at Phases 2/3/4 — the Phase-1 boundary should always have it — but
    defensively enforced regardless), ``commit_phase_handoff`` must not
    invoke ``_git("add", ".claude/current-slice/intent.md")`` on a
    non-existent path, and must not raise.

    Contract-guard: today trivially passes (the path is never added).
    After Phase 3, must still pass — i.e., the fix must use
    ``if path.exists(): _git("add", str(path))`` mirroring the existing
    ``handoff-phase-{n}.md`` block. An unguarded fix regresses here.
    """
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path)

    assert not (slice_dir / "intent.md").exists(), (
        "fixture precondition: intent.md must be absent"
    )
    # Seed handoff-phase-1.md so the existing (already-guarded) stage
    # exercises itself — isolates the intent.md guard under test.
    (slice_dir / "handoff-phase-1.md").write_text("---\nphase: 1\n---\nbody\n")

    # Must not raise.
    so.commit_phase_handoff(1, "phase-1 summary", "deadbeef")

    staged = _adds(calls)
    assert ".claude/current-slice/intent.md" not in staged, (
        "intent.md must NOT be staged when absent (guard must hold); "
        f"staged paths were {staged!r}"
    )


# ---------- R2b — no-op when .claude/features/<feature>.yaml is absent ------


def test_feature_file_not_staged_when_absent(monkeypatch, tmp_path):
    """The new feature-file stage must be guarded by ``path.exists()``.

    If ``.claude/features/<feature>.yaml`` is not on disk (e.g. a slice
    predating feature-slice-model D2, or the Phases 2/3/4 boundaries
    where phase-1-writer's feature write already landed upstream but
    may have since moved), ``commit_phase_handoff`` must not invoke
    ``_git("add", ".claude/features/<feature>.yaml")`` on a
    non-existent path, and must not raise.

    Contract-guard: today trivially passes (the path is never added).
    After Phase 3, must still pass — i.e., the fix must use
    ``if path.exists(): _git("add", str(path))``.
    """
    so, _slice_dir, calls = _patched_so(monkeypatch, tmp_path)

    features_file = tmp_path / ".claude" / "features" / "demo.yaml"
    assert not features_file.exists(), (
        "fixture precondition: .claude/features/demo.yaml must be absent"
    )

    # Must not raise.
    so.commit_phase_handoff(1, "phase-1 summary", "deadbeef")

    staged = _adds(calls)
    assert ".claude/features/demo.yaml" not in staged, (
        "feature-file must NOT be staged when absent (guard must hold); "
        f"staged paths were {staged!r}"
    )

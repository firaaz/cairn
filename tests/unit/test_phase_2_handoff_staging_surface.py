"""Phase 2 RED — substrate/phase-2-skeptic-stage-surface (issue #26).

``slice_orchestrator.commit_phase_handoff`` MUST, when ``phase == 2``,
extend its staging set with every path under ``tests/unit/`` whose state
diverges (added or modified) from the Phase-1 boundary commit. Discovery
is diff-based against the Phase-1 boundary SHA — *not* slug-glob — so
the mechanism survives test-naming-convention drift (R2 case below
deliberately mixes slug-named and non-slug-named files).

The Phase-2 boundary commit must remain a single ``handoff: phase 2
complete`` commit; the staging extension is *content widening* on the
existing commit, not a new commit. This preserves INV-008 DC-3
(idempotent close — re-runs against an empty diff stage no extra paths)
and INV-008 DC-4 (no extra commits at the phase boundary). Each new
stage is guarded by ``if path.exists(): _git("add", str(path))`` so a
path enumerated by the diff but absent on disk (e.g. deleted between
RED and the staging call, or a re-run after a downstream cleanup) is a
no-op rather than a hard failure.

Tests are RED/guard split:

* R1 — single slug-named ``tests/unit/`` file, written this phase, must
  stage at the Phase-2 handoff boundary. RED today.
* R2 — three ``tests/unit/`` files written this phase, with mixed
  slug-named and non-slug-named filenames, must all stage. The
  non-slug-named entry pins the contract that discovery is diff-based,
  not glob-by-slice-id. RED today.
* R3 — zero ``tests/unit/`` files written this phase: the Phase-2
  commit shape is unchanged — only ``handoff-phase-2.md`` stages.
  Contract-guard against an unguarded extension that would always stage
  some sentinel ``tests/unit/`` token regardless of diff output.
* R4 — one ``tests/unit/`` file written this phase *and* a modified
  ``handoff-phase-2.md``: both must stage in the same Phase-2 commit
  (the existing handoff stage is preserved alongside the new
  diff-driven stages).

Bisect anchor (intent §Verification): the Phase-2 boundary commit on
this slice itself must contain
``tests/unit/test_phase_2_handoff_staging_surface.py`` — i.e. the
regression test must be staged by the very fix it exercises.

Ambiguity resolution
--------------------
* ``commit_phase_handoff`` public signature is
  ``commit_phase_handoff(phase, summary, commit_hash)`` (verified via
  existing Phase-2 RED test ``test_commit_phase_handoff_stage_surface``
  and orchestrator package re-exports). Tests call the real signature.
* The mechanism by which the Phase-1 boundary SHA is resolved
  (state-file lookup vs. ``git log`` walk vs. caller-supplied) is
  intentionally NOT pinned by these tests — tests stub ``_git`` so any
  ``git diff ...`` invocation returns a configured path list. The
  contract under test is the staging effect, not the SHA-resolution
  step. Phase-3 implementer is free to choose the resolution mechanism.
* ``_git`` is the orchestrator's git wrapper; existing Phase-2 tests
  monkeypatch it as ``so._git`` and observe ``add``/``commit`` calls.
  This file follows the same convention.
"""

from __future__ import annotations

from pathlib import Path


# ---------- fixtures --------------------------------------------------------


def _init_project(tmp_path: Path) -> Path:
    """Seed a minimal ``.claude/current-slice/slice.yaml`` (current_phase=2)
    so ``_slice_id()`` resolves and the handoff path lookup works.
    """
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/phase-2-stage-surface\n"
        'name: "demo/phase-2-stage-surface"\n'
        "status: in-progress\n"
        "current_phase: 2\n"
        'brief: "demo brief"\n'
    )
    return slice_dir


def _patched_so(
    monkeypatch,
    tmp_path,
    diff_paths: list[str] | None = None,
    untracked_paths: list[str] | None = None,
):
    """Patch the orchestrator to read SLICE_YAML from the fixture and stub
    ``_git`` so commits never touch disk.

    ``diff_paths`` is the simulated output of ``git diff --name-only
    <phase-1-boundary> -- tests/unit/`` (one path per line) — discovers
    *tracked* tree changes.

    ``untracked_paths`` is the simulated output of ``git ls-files --others
    --exclude-standard -- tests/unit/`` (one path per line) — discovers
    *untracked* working-tree paths the diff would silently drop. Default
    ``None`` → empty, preserves R1–R4 behaviour (those cases never
    exercised the ls-files arm; the orchestrator returning "" matches the
    pre-fix observable).

    Any ``_git`` invocation whose first arg is ``"diff"`` returns the
    joined diff paths; ``"ls-files"`` returns the joined untracked paths;
    ``"log"`` / ``"rev-parse"`` return a dummy SHA so any boundary-SHA
    resolution path the implementer chooses still gets a well-formed
    answer; everything else returns ``""`` (matching the existing
    fake-git convention).

    Returns ``(so, slice_dir, calls)`` where ``calls`` is a mutable list
    of every ``_git`` invocation as a list of positional args.
    """
    diff_paths = list(diff_paths or [])
    untracked_paths = list(untracked_paths or [])
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)

    calls: list[list[str]] = []

    def fake_git(*args):
        calls.append(list(args))
        if not args:
            return ""
        head = args[0]
        if head == "diff":
            return "\n".join(diff_paths) + ("\n" if diff_paths else "")
        if head == "ls-files":
            return "\n".join(untracked_paths) + ("\n" if untracked_paths else "")
        if head in ("log", "rev-parse"):
            return "deadbee0\n"
        return ""

    monkeypatch.setattr(so, "_git", fake_git, raising=True)
    return so, slice_dir, calls


def _adds(calls):
    """Return the list of paths staged via ``_git("add", <path>)``.

    Accepts both single-path (``_git("add", str(path))``) and multi-arg
    (``_git("add", "-f", str(path))``) forms; flag tokens (``-…``) are
    dropped, positional path tokens collected in order.
    """
    staged: list[str] = []
    for c in calls:
        if not c or c[0] != "add":
            continue
        for tok in c[1:]:
            if not tok.startswith("-"):
                staged.append(tok)
    return staged


def _seed_test_file(tmp_path: Path, relpath: str) -> Path:
    """Materialise a ``tests/unit/...`` file at *relpath* under tmp_path
    so the orchestrator's ``path.exists()`` guard sees it.
    """
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# RED — phase 2 skeptic\n")
    return target


# ---------- R1 — single slug-named test file stages -------------------------


def test_phase_2_stages_single_slug_named_test_file(monkeypatch, tmp_path):
    """When phase-2-skeptic wrote exactly one ``tests/unit/`` file
    (slug-derived filename), ``commit_phase_handoff(2, ...)`` must stage
    it at the Phase-2 handoff boundary alongside ``handoff-phase-2.md``.

    Today: RED — orchestrator's Phase-2 staging block does not enumerate
    ``tests/unit/`` and the file is orphaned into Phase 3.
    """
    seeded = ["tests/unit/test_phase_2_skeptic_stage_surface.py"]
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path, diff_paths=seeded)

    _seed_test_file(tmp_path, seeded[0])
    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    assert seeded[0] in staged, (
        "phase-2-skeptic RED test write "
        f"`{seeded[0]}` must be staged at the Phase-2 handoff boundary "
        f"(today orphaned — staged paths were {staged!r})"
    )


# ---------- R2 — three mixed-naming test files all stage --------------------


def test_phase_2_stages_three_mixed_naming_test_files(monkeypatch, tmp_path):
    """Discovery is diff-based, not slug-glob. When phase-2-skeptic wrote
    three ``tests/unit/`` files — including at least one whose filename
    is NOT derivable from the slice-id slug — all three must stage.

    Files:
      * ``tests/unit/test_phase_2_skeptic_stage_surface.py`` (slug-named)
      * ``tests/unit/test_orchestrator_phase_2_handoff.py`` (related but
        not slug-derived — would be missed by ``test_<slug>*.py`` glob)
      * ``tests/unit/test_zzz_unrelated_naming.py`` (deliberately
        non-slug-named — pins diff-based discovery against slug-glob
        regression)

    Today: RED — none of the three is staged.
    """
    seeded = [
        "tests/unit/test_phase_2_skeptic_stage_surface.py",
        "tests/unit/test_orchestrator_phase_2_handoff.py",
        "tests/unit/test_zzz_unrelated_naming.py",
    ]
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path, diff_paths=seeded)

    for rel in seeded:
        _seed_test_file(tmp_path, rel)
    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    missing = [p for p in seeded if p not in staged]
    assert not missing, (
        "phase-2 diff-based staging must enumerate every path "
        "`git diff --name-only <phase-1-boundary> -- tests/unit/` "
        "produces, regardless of filename naming convention; "
        f"missing from stage list: {missing!r} (staged paths were {staged!r})"
    )


# ---------- R3 — zero test files: commit shape unchanged --------------------


def test_phase_2_zero_test_files_preserves_commit_shape(monkeypatch, tmp_path):
    """When phase-2-skeptic wrote zero ``tests/unit/`` files (e.g. a
    pure-validation slice that authored only ``handoff-phase-2.md``),
    ``commit_phase_handoff(2, ...)`` must stage *only* the existing
    ``handoff-phase-2.md`` — no spurious ``tests/unit/`` token.

    Contract-guard: today trivially passes (the orchestrator does not
    enumerate ``tests/unit/`` at all). After Phase 3, the diff-based
    extension must still produce zero ``tests/unit/`` adds when the
    diff itself is empty — i.e. the implementation must not, e.g.,
    unconditionally add a sentinel directory or hardcode a slug-derived
    path. INV-008 DC-4: no change to commit shape when there is nothing
    to widen.
    """
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path, diff_paths=[])

    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    tests_unit_adds = [p for p in staged if p.startswith("tests/unit/")]
    assert tests_unit_adds == [], (
        "Phase-2 commit must stage zero `tests/unit/` paths when the "
        "diff against the Phase-1 boundary is empty (preserves commit "
        f"shape; INV-008 DC-4); spurious adds were {tests_unit_adds!r} "
        f"(full stage list {staged!r})"
    )


# ---------- R4 — test file + handoff-phase-2.md both stage ------------------


def test_phase_2_stages_test_file_and_handoff_md_together(monkeypatch, tmp_path):
    """When phase-2-skeptic wrote one ``tests/unit/`` file AND modified
    ``handoff-phase-2.md``, both paths must stage in the same Phase-2
    boundary commit (single commit — INV-008 DC-4 preserved; the
    extension widens commit content, not commit count).

    This is the integration of R1 with the existing handoff-md staging
    block. Today: RED — only ``handoff-phase-2.md`` stages.
    """
    seeded = ["tests/unit/test_phase_2_handoff_staging_surface.py"]
    so, slice_dir, calls = _patched_so(monkeypatch, tmp_path, diff_paths=seeded)

    _seed_test_file(tmp_path, seeded[0])
    (slice_dir / "handoff-phase-2.md").write_text(
        "---\nphase: 2\n---\nphase-2 body, modified\n"
    )

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    assert seeded[0] in staged, (
        "phase-2 test file write must stage at the Phase-2 boundary "
        f"alongside `handoff-phase-2.md` (today orphaned — staged paths "
        f"were {staged!r})"
    )
    assert any(p.endswith("handoff-phase-2.md") for p in staged), (
        "existing `handoff-phase-2.md` stage must be preserved by the "
        "extension (must not regress the existing handoff-md stage); "
        f"staged paths were {staged!r}"
    )

    # INV-008 DC-4: at most one `_git("commit", ...)` invocation at the
    # Phase-2 boundary — the extension widens commit content, not count.
    commit_calls = [c for c in calls if c and c[0] == "commit"]
    assert len(commit_calls) <= 1, (
        "Phase-2 boundary must produce at most one git commit "
        "(INV-008 DC-4 — extension widens commit content, not count); "
        f"commit calls observed: {commit_calls!r}"
    )


# ---------- R5 — untracked test file stages (issue #26 residual half) -------


def test_phase_2_stages_untracked_test_file(monkeypatch, tmp_path):
    """When phase-2-skeptic created a brand-new ``tests/unit/`` file that
    is *untracked* at the Phase-1 boundary commit, ``commit_phase_handoff(2,
    ...)`` MUST stage it at the Phase-2 boundary commit.

    ``git diff --name-only <phase-1-sha> -- tests/unit/`` — the discovery
    mechanism currently in tree at ``ae9e6c8`` — silently drops untracked
    paths by design. The skeptic's most common write is a *brand-new*
    RED file; under the current implementation that file is orphaned out
    of the Phase-2 boundary commit (the bisect anchor breaks for
    greenfield tests). The fix is the canonical Git idiom for "all paths
    the working tree adds relative to HEAD": union the diff-based set
    with ``git ls-files --others --exclude-standard -- tests/unit/``.

    Today: RED — the orchestrator never invokes ``ls-files`` and the
    untracked path never reaches ``_git("add", …)``.
    """
    untracked = ["tests/unit/test_brand_new_red_from_skeptic.py"]
    so, slice_dir, calls = _patched_so(
        monkeypatch,
        tmp_path,
        diff_paths=[],
        untracked_paths=untracked,
    )

    _seed_test_file(tmp_path, untracked[0])
    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    assert untracked[0] in staged, (
        "untracked phase-2-skeptic test write "
        f"`{untracked[0]}` must be staged at the Phase-2 handoff boundary "
        "via `git ls-files --others --exclude-standard -- tests/unit/` "
        "(today silently dropped — `git diff` excludes untracked by "
        f"design; staged paths were {staged!r})"
    )

    # INV-008 DC-4: untracked-only path must NOT introduce a second
    # commit at the Phase-2 boundary; widening is over commit content.
    commit_calls = [c for c in calls if c and c[0] == "commit"]
    assert len(commit_calls) <= 1, (
        "Phase-2 boundary must produce at most one git commit "
        "(INV-008 DC-4 — untracked-enumeration widens content, not "
        f"count); commit calls observed: {commit_calls!r}"
    )


# ---------- R6 — untracked + modified-tracked union both stage --------------


def test_phase_2_stages_union_of_untracked_and_modified_tracked(monkeypatch, tmp_path):
    """The Phase-2 staging set is the *union* of (a) ``git diff --name-only
    <phase-1-sha> -- tests/unit/`` (modified-tracked) and (b)
    ``git ls-files --others --exclude-standard -- tests/unit/``
    (untracked). When the skeptic both modifies an existing test and
    writes a new one, both paths must stage at the same Phase-2 boundary
    commit — neither half of the union may shadow the other.

    Today: RED — only the diff-based half is iterated; the untracked
    path is silently dropped.
    """
    modified_tracked = ["tests/unit/test_existing_modified_by_skeptic.py"]
    untracked = ["tests/unit/test_new_file_from_skeptic.py"]
    so, slice_dir, calls = _patched_so(
        monkeypatch,
        tmp_path,
        diff_paths=modified_tracked,
        untracked_paths=untracked,
    )

    for rel in modified_tracked + untracked:
        _seed_test_file(tmp_path, rel)
    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    expected = set(modified_tracked) | set(untracked)
    missing = sorted(expected - set(staged))
    assert not missing, (
        "Phase-2 staging must be the UNION of diff-based (modified-"
        "tracked) and ls-files-based (untracked) discovery against the "
        "Phase-1 boundary; neither half may shadow the other. Missing "
        f"from stage list: {missing!r} (staged paths were {staged!r})"
    )

    commit_calls = [c for c in calls if c and c[0] == "commit"]
    assert len(commit_calls) <= 1, (
        "Phase-2 boundary must produce at most one git commit "
        "(INV-008 DC-4); commit calls observed: {!r}".format(commit_calls)
    )


# ---------- R7 — DC-3 idempotency: ls-files path absent on disk is no-op ----


def test_phase_2_untracked_path_absent_on_disk_is_no_op(monkeypatch, tmp_path):
    """INV-008 DC-3 idempotency precondition. ``git ls-files --others
    --exclude-standard`` reports paths that exist *at discovery time*; a
    re-invocation after a downstream cleanup (or any race in which the
    path is removed between discovery and staging) must be silently
    dropped — not raise — so re-running ``commit_phase_handoff(2, …)``
    against an empty working tree is a no-op.

    Contract: the ``path.exists()`` guard already in tree at
    ``lifecycle.py:242`` must apply uniformly to *both* halves of the
    union (diff-based AND ls-files-based). Pinning this guards against
    a Phase-3 implementation that iterates ls-files output unguarded
    and crashes on a missing path.
    """
    phantom = ["tests/unit/test_path_reported_but_absent.py"]
    so, slice_dir, calls = _patched_so(
        monkeypatch,
        tmp_path,
        diff_paths=[],
        untracked_paths=phantom,
    )

    # Deliberately do NOT seed the file on disk — simulate a path that
    # ls-files reported but that has since been removed.
    (slice_dir / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nbody\n")

    so.commit_phase_handoff(2, "phase-2 summary", "cafef00d")

    staged = _adds(calls)
    assert phantom[0] not in staged, (
        "ls-files-reported path that does not exist on disk must NOT be "
        "staged (DC-3 idempotency precondition — `path.exists()` guard "
        f"applies to the ls-files arm too); staged paths were {staged!r}"
    )

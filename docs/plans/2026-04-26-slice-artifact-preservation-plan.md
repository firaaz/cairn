# Slice Artifact Preservation — Implementation Plan

> **For agentic workers:** This plan is INPUT to cairn's slice pipeline (slice id `compression/slice-artifact-preservation`). Phase 1 derives `intent.md` from §Goal/§Architecture/§Envelope below. Phase 2 writes the tests in each Task's "Tests Phase 2 writes" block (one commit). Phase 3 implements per "Implementation Phase 3 ships" block (one commit). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a copy-before-wipe step to `close_slice` so phase ephemerals (`intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `handoff-phase-{1..4}.md`, `envelope-expansions.log`, pre-close `slice.yaml`) survive the DC-5 wipe by being snapshotted to `.claude/sweep-results/<slice-id>/artifacts/`. Co-lands ADR `slice-artifact-preservation` (drafted in a separate `/decision` session before this slice opens).

**Architecture:** Single new private helper `_copy_artifacts_to_sweep_results(slice_id, pre_close_yaml_text)` in `scripts/slice_orchestrator/lifecycle.py`. `close_slice` captures the pre-close `slice.yaml` content as text *before* Step 1 mutates `status=complete`, then invokes the helper between Step 2 (bundle) and Step 3 (wipe). Two-tier failure handling: missing source files skip silently (D6 F5-tolerance, mirrors `_wipe_current_slice`'s existing `FileNotFoundError` posture); operational errors (disk full, permission denied, target-dir creation fails) raise and abort the close, mirroring Step 0's sweep-notes-missing loud-fail.

**Tech Stack:** stdlib only — `pathlib.Path`, `shutil.copyfile`, `os.makedirs`, `errno`. No new deps.

**Slice id:** `compression/slice-artifact-preservation`
**Feature:** `compression`
**Branch:** `slice/compression-slice-artifact-preservation`
**Worktree:** `.worktrees/slice-artifact-preservation/` (spawned from `feature/compression` at slice open; see parallelization plan `~/.claude/plans/okay-let-us-parallelize-partitioned-mitten.md`)

---

## Sequencing context (from substrate-design §6 + parallelization plan)

- Sibling slice — runs in **parallel** with substrate Slice 1 (`compression/lever-X-knowledge-index`); independent envelopes (Slice 1 touches `scripts/cairn_query/**`, this slice touches `scripts/slice_orchestrator/lifecycle.py`).
- **Recommended close order:** before substrate Slice 2 begins, so Slice 2's first close exercises the new archival path.
- ADR `slice-artifact-preservation` is **drafted by a separate `/decision` session** (run on `feature/compression` in the host worktree before this slice opens). The ADR file sits uncommitted at `docs/adr/slice-artifact-preservation.md` until this slice's Phase-3 commit stages it.
- `parallelism-v1` (provisional, accepted 2026-04-12) governs concurrent-worktree dispatch; first concurrent run is itself the dogfood validation event (`docs/adr/parallelism-v1.md:87`).

**ADR posture in this slice:** Phase 1 records `adrs-created: [slice-artifact-preservation]` and `adrs-referenced: [parallelism-v1]` in `intent.md`. The ADR file is co-landed in this slice's Phase-3 commit alongside the lifecycle change.

---

## Envelope

```yaml
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "tests/unit/test_slice_orchestrator_artifact_preservation.py"
  - "commands/claude-code/start-slice.full.md"
  - ".gitignore"
  - "docs/ARCHITECTURE.md"
  - "docs/adr/slice-artifact-preservation.md"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/{intent.md,validation/approach.md,implementation/notes.md,integration/sweep-notes.md}"
  - ".claude/current-slice/handoff-phase-{1,2,3,4}.md"
out-of-scope:
  - "Any change to scripts/slice_orchestrator/ outside lifecycle.py"
  - "Any extractor or substrate-side change (substrate slices own that)"
  - "Compaction / retention policy for .claude/sweep-results/ (deferred per ADR D4)"
  - "Commit-vs-gitignore reconsideration (deferred to extraction time per ADR D3)"
  - "Any change to existing close_slice test files (test_close_slice_*.py) other than additive imports if needed"
  - "Any change to INV-008's invariant-check grep target (D7 preserves it)"
  - "Any change to .claude/agents/phase-*.md"
  - "Any new ADR beyond slice-artifact-preservation"
```

---

## File Structure

```
scripts/slice_orchestrator/
  lifecycle.py                       # MODIFY: capture pre-close yaml; add helper; wire into close_slice

tests/unit/
  test_slice_orchestrator_artifact_preservation.py   # NEW: 9 RED tests

commands/claude-code/
  start-slice.full.md                # MODIFY: line 210 prose narrowing (D5)

docs/
  ARCHITECTURE.md                    # MODIFY: INV-008 prose amendment (D7)
  adr/slice-artifact-preservation.md # CO-LAND: ADR drafted by /decision; staged at Phase-3 commit

.gitignore                           # MODIFY: add .claude/sweep-results/*/artifacts/
.claude/features/compression.yaml    # APPEND: slice entry (Phase 1 writes)
```

**Notes on file decomposition:**
- All production code lives in `lifecycle.py` — the helper, the pre-close yaml capture, and the wiring are tightly coupled to `close_slice`'s step ordering. Splitting into a separate module would force a circular-ish import (the helper needs `_slice_id`/`SLICE_YAML` from `core`/`resume`, which `lifecycle` already imports).
- All tests live in one file — the 9 RED tests share fixtures (a temp slice dir, a populated `.claude/current-slice/`). One file mirrors the substrate-design's specified test path (`tests/unit/test_slice_orchestrator_artifact_preservation.py`).
- Existing close_slice tests (`test_close_slice_*.py`) are NOT touched. If any of them assert on directory contents post-close that now include the artifacts dir, that's a Phase-3-discovered failure; resolve by extending the existing test's assertion (in-envelope as an additive change, NOT in-scope as part of this plan unless found at Phase 3).

---

## Tasks

### Task 1: `_copy_artifacts_to_sweep_results` helper

**Files:**
- Modify: `scripts/slice_orchestrator/lifecycle.py`
- Test: `tests/unit/test_slice_orchestrator_artifact_preservation.py`

**Tests Phase 2 writes** (in one commit, all RED initially):

```python
# tests/unit/test_slice_orchestrator_artifact_preservation.py
"""ADR slice-artifact-preservation: pre-wipe snapshot of phase ephemerals.

Decisions covered:
  D1 — copy step ordering (between bundle and wipe)
  D2 — snapshot scope (7 artifact types incl. pre-close slice.yaml)
  D3 — gitignored target dir
  D5 — start-slice.full.md prose narrowing
  D6a — idempotency on re-close
  D6b — F5-tolerance for missing source files
  D7 — INV-008 prose amendment
  (c) — operational copy failure loud-fails
"""
from __future__ import annotations

import errno
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.slice_orchestrator import lifecycle


SLICE_ID = "compression/slice-artifact-preservation-test"
SLUG = "compression-slice-artifact-preservation-test"  # forward-slash → dash
ARTIFACT_FILES = [
    "intent.md",
    "validation/approach.md",
    "implementation/notes.md",
    "integration/sweep-notes.md",
    "handoff-phase-1.md",
    "handoff-phase-2.md",
    "handoff-phase-3.md",
    "handoff-phase-4.md",
    "envelope-expansions.log",
]


@pytest.fixture
def populated_current_slice(tmp_path, monkeypatch):
    """Build a .claude/current-slice/ tree with all artifact files populated."""
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    (cs / "validation").mkdir()
    (cs / "implementation").mkdir()
    (cs / "integration").mkdir()
    for rel in ARTIFACT_FILES:
        p = cs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"content of {rel}\n")
    yield cs


# --- D2: snapshot scope, byte-identity per artifact ---

def test_d2_handoff_phase_files_copied_byte_identical(populated_current_slice):
    pre_close_yaml = "id: " + SLICE_ID + "\nstatus: in-progress\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    for n in (1, 2, 3, 4):
        src = populated_current_slice / f"handoff-phase-{n}.md"
        dst = target / f"handoff-phase-{n}.md"
        assert dst.read_bytes() == src.read_bytes()


def test_d2_phase_artifact_files_copied_byte_identical(populated_current_slice):
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    for rel in ("intent.md", "validation/approach.md",
                "implementation/notes.md", "integration/sweep-notes.md",
                "envelope-expansions.log"):
        src = populated_current_slice / rel
        dst = target / rel
        assert dst.read_bytes() == src.read_bytes(), f"mismatch for {rel}"


def test_d2_pre_close_slice_yaml_captured_not_post_close(populated_current_slice):
    """slice.yaml in artifacts/ contains the pre-close text, not status=complete."""
    pre_close_yaml = "id: " + SLICE_ID + "\nstatus: in-progress\ncurrent_phase: 4\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    snapshot = (target / "slice.yaml").read_text()
    assert snapshot == pre_close_yaml
    assert "status: in-progress" in snapshot
    assert "status: complete" not in snapshot


# --- D6b: F5-tolerance for missing source files ---

def test_d6b_missing_source_skips_silently(tmp_path, monkeypatch):
    """Operator-rebase corner: source file gone → skip-and-proceed, no raise."""
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    # Only intent.md exists; the other artifacts are absent.
    (cs / "intent.md").write_text("only intent\n")
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    # Should not raise.
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    assert (target / "intent.md").read_text() == "only intent\n"
    assert not (target / "handoff-phase-1.md").exists()
    assert (target / "slice.yaml").read_text() == pre_close_yaml


# --- (c): operational copy failure loud-fails ---

def test_c_operational_copy_failure_raises(populated_current_slice):
    """Disk-full / permission-denied during copy → propagate, do not silently skip."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"

    def _disk_full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    with patch("scripts.slice_orchestrator.lifecycle.shutil.copyfile",
               side_effect=_disk_full):
        with pytest.raises(OSError) as excinfo:
            lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
        assert excinfo.value.errno == errno.ENOSPC


def test_c_target_dir_creation_failure_raises(populated_current_slice):
    """Permission-denied on target dir creation → propagate, do not silently skip."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"

    def _perm_denied(*args, **kwargs):
        raise OSError(errno.EACCES, "Permission denied")

    with patch("scripts.slice_orchestrator.lifecycle.os.makedirs",
               side_effect=_perm_denied):
        with pytest.raises(OSError) as excinfo:
            lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
        assert excinfo.value.errno == errno.EACCES


# --- D6a: idempotency on re-close (helper level) ---

def test_d6a_helper_idempotent_on_repeat_invocation(populated_current_slice):
    """Second invocation with same slice_id over identical sources is a no-op
    in observable effect: target files unchanged, no raise."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    first = (target / "intent.md").read_bytes()
    # Mutate the source — second call should overwrite with current source
    # (idempotency at helper level = no-error-on-rerun, not freeze-on-first-run;
    # DC-3 short-circuit at close_slice level is what prevents real re-runs).
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    second = (target / "intent.md").read_bytes()
    assert first == second  # source unchanged → target unchanged


# --- D1 ordering: copy populates target BEFORE wipe destroys sources ---

def test_d1_close_slice_copies_before_wipe(populated_current_slice, monkeypatch):
    """Integration: invoke close_slice end-to-end and verify the artifacts dir
    is populated AND the current-slice tree is wiped."""
    # Stub Step 0 sweep-notes presence by pre-populating it (already done in fixture).
    # Stub git invocations — wipe + commit shouldn't actually run git here.
    monkeypatch.setattr(lifecycle, "_git", lambda *a, **kw: _FakeProc())
    monkeypatch.setattr(lifecycle, "_git_head_safe", lambda: "deadbeef")
    # Write a real slice.yaml so close_slice can read it.
    sy_path = populated_current_slice / "slice.yaml"
    sy_path.write_text(
        "id: " + SLICE_ID + "\n"
        "status: in-progress\n"
        "current_phase: 4\n"
    )
    monkeypatch.setattr(lifecycle, "SLICE_YAML", sy_path)

    lifecycle.close_slice()

    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    assert (target / "intent.md").exists()
    assert (target / "slice.yaml").read_text().startswith("id: " + SLICE_ID)
    assert "status: in-progress" in (target / "slice.yaml").read_text()
    # Wipe ran: current-slice/ is empty except slice.yaml.
    survivors = sorted(
        p.relative_to(populated_current_slice).as_posix()
        for p in populated_current_slice.rglob("*")
        if p.is_file()
    )
    assert survivors == ["slice.yaml"]


class _FakeProc:
    stdout = ""
    returncode = 0
```

**Implementation Phase 3 ships:**

Add at the top of `scripts/slice_orchestrator/lifecycle.py` (alongside existing imports):

```python
import shutil
```

Add a new helper between `_wipe_current_slice` (line 67) and `_is_slice_already_closed` (line 99):

```python
# Sources to snapshot at close (paths relative to .claude/current-slice/).
# Mirrors ADR slice-artifact-preservation D2.
_ARTIFACT_RELPATHS = (
    "intent.md",
    "validation/approach.md",
    "implementation/notes.md",
    "integration/sweep-notes.md",
    "handoff-phase-1.md",
    "handoff-phase-2.md",
    "handoff-phase-3.md",
    "handoff-phase-4.md",
    "envelope-expansions.log",
)


def _copy_artifacts_to_sweep_results(slice_id, pre_close_yaml_text):
    """Snapshot phase ephemerals to .claude/sweep-results/<slug>/artifacts/.

    ADR slice-artifact-preservation:
      D1 — invoked between bundle (Step 2) and wipe (Step 3) in close_slice.
      D2 — snapshot scope = the 9 file paths in _ARTIFACT_RELPATHS plus the
           pre-close slice.yaml (passed in by close_slice as text, since
           the on-disk slice.yaml has already been mutated to status=complete
           by Step 1).
      D6 — F5-tolerant: a source file that does not exist is skipped silently
           (matches _wipe_current_slice's FileNotFoundError posture for the
           operator-rebase corner).
      (c) — operational errors (disk-full, permission-denied, target-dir
            creation failure) propagate to the caller, aborting the close.
            Mirrors Step 0's sweep-notes-missing loud-fail posture: a broken
            disk should not silently produce a `slice: complete` commit.
    """
    slug = slice_id.replace("/", "-")
    target = Path(".claude/sweep-results") / slug / "artifacts"
    # Operational errors (EACCES, ENOSPC, etc.) propagate per (c).
    os.makedirs(str(target), exist_ok=True)
    os.makedirs(str(target / "validation"), exist_ok=True)
    os.makedirs(str(target / "implementation"), exist_ok=True)
    os.makedirs(str(target / "integration"), exist_ok=True)

    src_root = Path(".claude/current-slice")
    for rel in _ARTIFACT_RELPATHS:
        src = src_root / rel
        if not src.is_file():
            # D6 F5-tolerance: source missing → skip silently.
            continue
        dst = target / rel
        # shutil.copyfile preserves byte content; metadata is not preserved
        # (D2 specifies content snapshot, not metadata snapshot).
        # Operational errors propagate per (c).
        shutil.copyfile(str(src), str(dst))

    # Pre-close slice.yaml: caller provides the pre-mutation text (D2).
    (target / "slice.yaml").write_text(pre_close_yaml_text)
```

Modify `close_slice` (line 384) — capture pre-close yaml text before Step 1 mutation, then call the helper between Step 2 and Step 3:

```python
def close_slice(state=None):
    """INV-008 slice-close contract: DC-3 idempotent, DC-4 sole commit source,
    DC-5 explicit wipe, DC-7 slug-keyed observability persistence.

    Order: sweep-notes presence check → capture pre-close yaml → slice.yaml
    mutation → bundle → copy artifacts → wipe → commit `slice: complete`.
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
        # ... (existing sweep-notes-missing branch — unchanged)
        ...  # (KEEP the existing code from lines 401-424 verbatim)

    # NEW: Capture pre-close slice.yaml text BEFORE Step 1 mutates it.
    # ADR slice-artifact-preservation D2 requires the snapshot to reflect
    # status=in-progress with envelope intact, not the post-mutation form.
    if SLICE_YAML.is_file():
        try:
            _pre_close_yaml_text = SLICE_YAML.read_text()
        except OSError:
            # If we cannot read it, treat as empty — the copy will write an
            # empty slice.yaml into the artifacts dir; missing-source posture.
            _pre_close_yaml_text = ""
    else:
        _pre_close_yaml_text = ""

    # Step 1: slice.yaml → status=complete, current_phase=max_phase.
    # ... (existing code unchanged — lines 427-435)

    # Step 2: bundle handoff.md before wipe removes the inputs.
    handoff = _bundle_handoff_md()

    # Drift detector (DC-4 layer 3): unchanged — lines 440-450.

    # NEW Step 2.5: copy artifacts to .claude/sweep-results/<slug>/artifacts/.
    # ADR slice-artifact-preservation D1: between bundle (Step 2) and wipe
    # (Step 3). Operational errors propagate per (c) and abort the close
    # before the wipe destroys the originals.
    slice_id_for_copy = sy.get("id") or "unknown/unknown"
    _copy_artifacts_to_sweep_results(slice_id_for_copy, _pre_close_yaml_text)

    # Step 3: wipe current-slice (DC-5 strict; F5-tolerant).
    _wipe_current_slice()

    # Step 4: sole `slice: <id> — complete` commit (DC-4 + B5-tightened).
    # ... (existing code unchanged — lines 456-482)

    # Step 5: persist terminal observability state.
    # ... (existing code unchanged — lines 485-509)
```

- [ ] **Step 1: Phase 2 — write the test file.** Create `tests/unit/test_slice_orchestrator_artifact_preservation.py` with the entire block above. Phase-2-skeptic commits it as a single Phase-2 commit. Run `uv run pytest tests/unit/test_slice_orchestrator_artifact_preservation.py -v`. Expected: all 9 tests FAIL with `AttributeError: module 'scripts.slice_orchestrator.lifecycle' has no attribute '_copy_artifacts_to_sweep_results'` or similar — confirming RED.
- [ ] **Step 2: Phase 3 — add `import shutil` to `lifecycle.py`.** Place alphabetically among existing imports.
- [ ] **Step 3: Phase 3 — add `_ARTIFACT_RELPATHS` and `_copy_artifacts_to_sweep_results` helper** between `_wipe_current_slice` and `_is_slice_already_closed`.
- [ ] **Step 4: Phase 3 — modify `close_slice`** to capture pre-close yaml text before Step 1 and to invoke the helper between Step 2 and Step 3 (per the diff above; preserve existing comment style).
- [ ] **Step 5: Phase 3 — run the new test file.** `uv run pytest tests/unit/test_slice_orchestrator_artifact_preservation.py -v`. Expected: 9/9 PASS.
- [ ] **Step 6: Phase 3 — run the full close_slice test suite.** `uv run pytest tests/unit/test_close_slice_*.py tests/unit/test_slice_orchestrator_*.py -v`. Expected: all green; pre-existing tests are not affected because the new copy step writes to `.claude/sweep-results/<slug>/artifacts/` which lives outside `.claude/current-slice/` (the dir those tests assert on).

---

### Task 2: `.gitignore` D3 directive

**Files:**
- Modify: `.gitignore`

**Tests Phase 2 writes:** None — `.gitignore` is a static prose edit verified by visual inspection during Phase 4 sweep. (A Phase-2 test could read `.gitignore` and assert the line exists, but cairn convention treats gitignore changes as prose-edits, not test-driven; see compression Slice 1 plan's pyproject.toml/gitignore Task 1 — bootstrap-only, no Phase-2 test.)

**Implementation Phase 3 ships:**

Append to `.gitignore`:

```
# slice-artifact-preservation: pre-wipe snapshots of phase ephemerals.
# Derived from .claude/current-slice/ at close; analytical use only.
.claude/sweep-results/*/artifacts/
```

- [ ] **Step 1: Phase 3 — append the three lines above** to the bottom of `.gitignore`. Preserve existing trailing newline.
- [ ] **Step 2: Phase 3 — verify the directive applies.** After Task 1's helper has been wired (i.e. after Task 1 Step 5), trigger a manual close and run `git status` — `.claude/sweep-results/<slug>/artifacts/**` must NOT appear as untracked.

---

### Task 3: `start-slice.full.md` D5 prose narrowing

**Files:**
- Modify: `commands/claude-code/start-slice.full.md` (line 210)

**Tests Phase 2 writes:** None — prose edit. (Same convention as Task 2.)

**Implementation Phase 3 ships:**

Replace line 210 in `commands/claude-code/start-slice.full.md`. Current text:

> When Phase 4 passes, the completion sequence **wipes** every file under `.claude/current-slice/`. This is not optional and there is no archive directory for successful slices — the `status: complete` commit IS the git-history record, and `.claude/learning.md` plus ADRs cover the post-mortem case. Per context-discipline-protocol, leaving residue in `.claude/current-slice/` after close would cause the next slice to inherit stale framing through `/catchup`, defeating the context-isolation boundary this pipeline exists to enforce.

Amended text:

> When Phase 4 passes, the completion sequence **wipes** every file under `.claude/current-slice/`. This is not optional and there is no archive directory **for committed history** — the `status: complete` commit IS the git-history record, and `.claude/learning.md` plus ADRs cover the post-mortem case. Ephemeral artifacts (intent, validation/approach, implementation/notes, sweep-notes, handoff-phase-{1..4}, envelope-expansions.log, pre-close slice.yaml) ARE preserved on-disk at `.claude/sweep-results/<slice-id>/artifacts/` (gitignored) for analytical use — see ADR `slice-artifact-preservation`. Per context-discipline-protocol, leaving residue in `.claude/current-slice/` after close would cause the next slice to inherit stale framing through `/catchup`, defeating the context-isolation boundary this pipeline exists to enforce.

Diff scope:
- Line 210 only. The two changes are: (a) `for successful slices` → `for committed history`; (b) one new sentence inserted before "Per context-discipline-protocol".

- [ ] **Step 1: Phase 3 — apply the edit** to line 210 of `commands/claude-code/start-slice.full.md`. Use a single Edit call with the full pre/post text as `old_string`/`new_string` (the line is long enough to be uniquely identifying).
- [ ] **Step 2: Phase 3 — verify line count** unchanged (`wc -l` before and after — same value), since this is a same-line replacement.

---

### Task 4: `docs/ARCHITECTURE.md` INV-008 D7 prose amendment

**Files:**
- Modify: `docs/ARCHITECTURE.md` (line 75)

**Tests Phase 2 writes:** None — prose edit. The `invariant-check INV-008` block (lines 77-83) is **NOT touched** — D7 explicitly preserves the grep target `def close_slice` in `scripts/slice_orchestrator/lifecycle.py`.

**Implementation Phase 3 ships:**

Replace line 75 in `docs/ARCHITECTURE.md`. The current prose ends with `(slice-close-contract; orchestrator-observability)`. Insert one new sentence before the closing parenthetical, describing the new copy step.

Current text (line 75, abbreviated for diff clarity):

> **INV-008** The orchestrator's slice-close lifecycle satisfies three properties that are separately testable: (a) `close_slice` is idempotent ... (b) ... `close_slice` bundles into `.claude/handoff.md` before wipe; (c) cross-slice artifacts in `.claude/orchestrator-debug/` are isolated by slice-id-slug filenames, with a collision tripwire that refuses loudly when two distinct slice-ids flatten to the same slug. Resume reconciliation via `--resume` is read-first / act-second across a 13-row matrix with default-refuse on unrecognized state-triples and a heartbeat advisory for the multi-instance bridge. (slice-close-contract; orchestrator-observability)

Amended text adds a fourth property `(d)` after `(c)`, describing the new copy step:

> **INV-008** The orchestrator's slice-close lifecycle satisfies four properties that are separately testable: (a) `close_slice` is idempotent ... (b) ... `close_slice` bundles into `.claude/handoff.md` before wipe; (c) cross-slice artifacts in `.claude/orchestrator-debug/` are isolated by slice-id-slug filenames, with a collision tripwire that refuses loudly when two distinct slice-ids flatten to the same slug; (d) phase ephemerals (intent.md, validation/approach.md, implementation/notes.md, integration/sweep-notes.md, handoff-phase-{1..4}.md, envelope-expansions.log, and the pre-close slice.yaml text) are snapshotted via `_copy_artifacts_to_sweep_results` to `.claude/sweep-results/<slug>/artifacts/` between bundle and wipe, with two-tier failure handling (missing source files skip silently per F5-tolerance; operational errors propagate and abort the close before the wipe destroys the originals). Resume reconciliation via `--resume` is read-first / act-second across a 13-row matrix with default-refuse on unrecognized state-triples and a heartbeat advisory for the multi-instance bridge. (slice-close-contract; orchestrator-observability; slice-artifact-preservation)

Diff scope:
- "three properties" → "four properties"
- New `(d)` clause inserted after the `(c)` semicolon (before "Resume reconciliation").
- Closing parenthetical adds `; slice-artifact-preservation`.

- [ ] **Step 1: Phase 3 — apply the edit** to line 75 of `docs/ARCHITECTURE.md`. Use a single Edit call.
- [ ] **Step 2: Phase 3 — run the architecture validator.** `uv run python .slice-system/scripts/validate_architecture.py`. Expected: PASS — the `def close_slice` grep target is unchanged, the new prose passes the same invariant-check block.

---

## Phase 4 verification (sweep-notes content)

The Phase-4 integrator sweep should record:

- **INV-008** PASS — validator's `def close_slice` grep target matches `scripts/slice_orchestrator/lifecycle.py` (the invariant-check block is untouched).
- **Manual end-to-end** — operator opens a throwaway slice on a sibling worktree, closes it, and verifies `.claude/sweep-results/<slug>/artifacts/` contains:
  - 9 source-file snapshots (those that existed in `.claude/current-slice/` at close; missing files skip per F5).
  - `slice.yaml` with `status: in-progress` (the pre-close form, not `status: complete`).
- **Idempotency** — re-running `close_slice` on an already-closed slice short-circuits at `_is_slice_already_closed` (DC-3); the helper is not re-invoked.
- **Operational-error sample** — one mocked `OSError(ENOSPC)` in `shutil.copyfile` propagates and aborts the close (test `test_c_operational_copy_failure_raises` covers this).
- **ADR co-landed** — `docs/adr/slice-artifact-preservation.md` is staged in the Phase-3 commit alongside the `lifecycle.py` change.

---

## Self-review (against §6 + §8.2 + (c))

- §6 envelope (8 paths) → all 8 in §Envelope above ✓
- §6 out-of-scope (3 items) → all 3 in §Envelope `out-of-scope` above ✓
- §6 closes-when (4 conditions) → all 4 covered by Phase-4 verification + Task tests ✓
- §8.2 D1 (copy step ordering: bundle → copy → wipe) → Task 1 implementation + `test_d1_close_slice_copies_before_wipe` ✓
- §8.2 D2 (snapshot scope: 9 files + pre-close slice.yaml) → `_ARTIFACT_RELPATHS` (9 entries) + caller-provided pre-close yaml ✓
- §8.2 D3 (gitignored target) → Task 2 ✓
- §8.2 D4 (compaction parked) → no task (correctly out-of-scope) ✓
- §8.2 D5 (start-slice.full.md amendment) → Task 3 ✓
- §8.2 D6 (idempotency + F5-tolerance) → `test_d6a_helper_idempotent_on_repeat_invocation` + `test_d6b_missing_source_skips_silently` ✓
- §8.2 D7 (INV-008 amendment, grep target unchanged) → Task 4 ✓
- (c) operational copy failure loud-fail → `test_c_operational_copy_failure_raises` + `test_c_target_dir_creation_failure_raises` ✓
- Pre-close slice.yaml capture-timing → `close_slice` patch reads SLICE_YAML.read_text() before Step 1 mutation; passed to helper as `_pre_close_yaml_text` ✓

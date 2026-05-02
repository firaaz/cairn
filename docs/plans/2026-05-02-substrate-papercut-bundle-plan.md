# Substrate paper-cut bundle + issue #26 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Cairn-specific note: each "Slice" below is a `/start-slice` invocation; tasks within a slice map to the four-phase pipeline (Phase 1 intent → Phase 2 RED → Phase 3 GREEN → Phase 4 sweep → close_slice).

**Goal:** Land three substrate paper-cuts (Slice 1) and close S1 issue #26's phase-2-skeptic stage-surface bug (Slice 2).

**Architecture:** Two sequential slices on `feature/compression-followup`. Slice 1 is three single-line fixes in disjoint modules with two regression tests. Slice 2 extends `commit_phase_handoff` to stage Phase-2's test writes via diff-against-Phase-1-boundary, with a four-case regression matrix.

**Tech Stack:** Python (`scripts/slice_orchestrator/`), bash (`checks/scope-guard.sh`, `scripts/verify_handoff.sh`), pytest, the cairn slice pipeline.

**Design reference:** `docs/plans/2026-05-02-substrate-papercut-bundle-design.md`

---

## Slice 1 — `substrate/papercut-bundle`

### Task 1.1: Open the slice (Phase 1 intent)

**Action:** Run `/start-slice substrate/papercut-bundle`.

**Phase-1 writer should produce `.claude/current-slice/intent.md` with the following envelope:**

```yaml
envelope:
  - "checks/scope-guard.sh"
  - "commands/claude-code/integration-sweep.md"
  - "scripts/verify_handoff.sh"
  - "tests/unit/test_scope_guard_admin_allowlist.py"
  - "tests/unit/test_verify_handoff_sweep_subject.py"
```

**ADRs referenced:** none (no architectural decisions; pure bug-fix).
**Invariants touched:** none.

**Step 1: Verify intent committed.** `git log --oneline -1` shows `slice: substrate/papercut-bundle — phase 1 intent`.

---

### Task 1.2: Phase 2 RED — write failing tests

**Files to create:**
- `tests/unit/test_scope_guard_admin_allowlist.py`
- `tests/unit/test_verify_handoff_sweep_subject.py`

**Step 1: Write `tests/unit/test_scope_guard_admin_allowlist.py`:**

```python
"""Phase 2 RED for paper-cut #1: scope-guard admin allowlist must include
.claude/d{1,3}-bypasses.log so Edit/Write hook events on those files exit 0
even with a tight slice envelope (no EXPAND_ENVELOPE=1, no Bash heredoc bypass).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_GUARD = REPO_ROOT / "checks" / "scope-guard.sh"


def _hook_input(file_path: str) -> str:
    return json.dumps({"tool_input": {"file_path": file_path}})


@pytest.fixture
def tight_slice(tmp_path: Path) -> Path:
    """A project with an active slice whose envelope excludes bypass logs."""
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/x\nname: \"demo/x\"\nstatus: in-progress\ncurrent_phase: 3\n"
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/x\nphase: 1-intent\n"
        "envelope:\n  - \"src/only.py\"\n---\nbody\n"
    )
    return tmp_path


@pytest.mark.parametrize("logfile", [".claude/d1-bypasses.log", ".claude/d3-bypasses.log"])
def test_bypass_logs_admin_allowed(tight_slice: Path, logfile: str) -> None:
    target = str(tight_slice / logfile)
    result = subprocess.run(
        ["bash", str(SCOPE_GUARD)],
        input=_hook_input(target),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tight_slice), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, (
        f"scope-guard blocked {logfile} despite admin-allowlist intent.\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
```

**Step 2: Write `tests/unit/test_verify_handoff_sweep_subject.py`:**

```python
"""Phase 2 RED for paper-cut #4: verify_handoff.sh check (c) must accept
'sweep: ' as a fourth subject prefix (joining handoff:, phase-N:,
slice: ... — complete).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "scripts" / "verify_handoff.sh"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def repo_with_sweep_head(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.test")
    _git(repo, "config", "user.name", "t")
    (repo / "f").write_text("x")
    _git(repo, "add", "f")
    _git(repo, "commit", "-q", "-m", "sweep: post-demo — PASS")
    return repo


def test_check_c_accepts_sweep_prefix(repo_with_sweep_head: Path) -> None:
    result = subprocess.run(
        ["bash", str(VERIFIER)],
        cwd=repo_with_sweep_head,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "verify_handoff.sh rejected a 'sweep:' commit subject.\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
```

**Step 3: Run tests; confirm RED.**

Run: `uv run pytest tests/unit/test_scope_guard_admin_allowlist.py tests/unit/test_verify_handoff_sweep_subject.py -v`

Expected: both fail (scope-guard blocks bypass log paths; verify_handoff.sh exits 1 on `sweep:` subject).

**Step 4: Phase 2 commits via the orchestrator.** No manual `git commit` — the slice pipeline commits Phase 2 RED.

---

### Task 1.3: Phase 3 GREEN — minimal implementation

**Step 1: Patch `checks/scope-guard.sh:60`:**

Change the admin-allowlist `case` line from:

```bash
  .claude/current-slice/*|.claude/handoff.md|.claude/sweep.yaml|.claude/features/*) exit 0 ;;
```

to:

```bash
  .claude/current-slice/*|.claude/handoff.md|.claude/sweep.yaml|.claude/features/*) exit 0 ;;
  .claude/d1-bypasses.log|.claude/d3-bypasses.log) exit 0 ;;
```

(Adding a new `case` arm keeps the diff minimal and preserves the existing arm's git blame.)

**Step 2: Patch `scripts/verify_handoff.sh:35-44`:**

After the existing `slice: ... — complete` branch, add a fourth elif:

```bash
elif printf '%s' "$subject" | grep -Eq '^sweep: '; then
  subject_ok=1
```

And update the `expected one of:` error message on line 47 to include the new form:

```bash
err "  expected one of: 'handoff: ...', 'phase-<N>: ...', 'slice: ... — complete', 'sweep: ...'"
```

**Step 3: Patch `commands/claude-code/integration-sweep.md:11`:**

Change:

```
3. Run `python3 scripts/integration_gate.py` — mechanizes invariant checking …
```

to:

```
3. Run `uv run python scripts/integration_gate.py` — mechanizes invariant checking …
```

**Step 4: Re-run the two test files; confirm GREEN.**

Run: `uv run pytest tests/unit/test_scope_guard_admin_allowlist.py tests/unit/test_verify_handoff_sweep_subject.py -v`

Expected: both pass.

**Step 5: Run full suite for regression check.**

Run: `uv run pytest tests/unit/ -q`

Expected: same pass/fail surface as the 2026-05-02 sweep baseline (1160 passed / 2 known fails / 3 skipped / 3 xfailed). No new failures.

---

### Task 1.4: Phase 4 sweep + close_slice

**Step 1:** Phase-4-integrator runs `scripts/integration_gate.py`, `scripts/snapshot_diff.py --diff`, full pytest. Writes `.claude/current-slice/integration/sweep-notes.md`. Commits per orchestrator.

**Step 2:** `close_slice` stages `.claude/current-slice/slice.yaml` + `.claude/handoff.md` per `lifecycle.py:540` and produces the `slice: substrate/papercut-bundle — complete` commit.

**Step 3:** Verify post-close cleanliness.

Run: `git status --short`
Expected: clean (no orphaned phase-4 artifacts; the a8d8f23 fix already covers `sweep.yaml` / `structural-snapshot.json` / `features/<id>.yaml`).

---

## Slice 2 — `substrate/phase-2-skeptic-stage-surface` (issue #26)

### Task 2.1: Open the slice (Phase 1 intent)

**Action:** Run `/start-slice substrate/phase-2-skeptic-stage-surface`.

**Phase-1 writer should produce intent.md with envelope:**

```yaml
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "tests/unit/test_phase_2_handoff_staging_surface.py"
```

**ADRs referenced:** none.
**Invariants touched:** INV-008 (DC-3 idempotency, DC-4 phase-boundary commit shape — preserved, not changed; reference for bisect context).
**Issue link:** #26 (intent.md should include `issue: 26` or similar in frontmatter for traceability).

---

### Task 2.2: Phase 2 RED — four regression cases

**File:** `tests/unit/test_phase_2_handoff_staging_surface.py`

**Step 1: Write the four test cases.** Skeleton follows; each case constructs a tmp project, simulates Phase 1 → Phase 2 transitions, and asserts on the resulting Phase-2 commit's tree.

```python
"""Phase 2 RED for issue #26 — phase-2-skeptic stage surface.

Four regression cases (R1-R4) per issue #26 § Test surface:
  R1: 1 test file written → present in Phase-2 commit
  R2: 3 test files (mixed slug-named + non-slug-named) → all 3 staged
  R3: 0 test files → Phase-2 commit shape unchanged (handoff-phase-2.md only)
  R4: 1 test file + handoff-phase-2.md modification → both staged

INV-008 DC-3 (idempotency) and DC-4 (no extra commits) are asserted via
re-invocation no-op and one-commit-per-phase-boundary checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _init_phase_2_ready(tmp_path: Path, slice_id: str = "demo/skeptic-x") -> Path:
    """Construct a tmp project where Phase 1 has committed; Phase 2 is in progress.
    Returns the project root.
    """
    # Implementer fills in: init repo, write slice.yaml, write intent.md with
    # envelope, write handoff-phase-1.md, commit as 'phase-1: <slice> — intent',
    # then advance current_phase to 2 and write handoff-phase-2.md.
    raise NotImplementedError("fill in fixture")


def _phase_2_files_in_commit(repo: Path) -> set[str]:
    """Return the set of file paths in HEAD's tree (the Phase-2 commit)."""
    raw = _git(repo, "show", "--name-only", "--pretty=", "HEAD")
    return {line for line in raw.splitlines() if line}


# ---------- R1 ----------------------------------------------------------------

def test_R1_single_test_file_staged(tmp_path: Path) -> None:
    repo = _init_phase_2_ready(tmp_path)
    (repo / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "unit" / "test_demo_skeptic_x_one.py").write_text("def test_x(): assert False\n")
    # Invoke commit_phase_handoff for current_phase=2
    # Implementer fills in: orchestrator hook
    files = _phase_2_files_in_commit(repo)
    assert "tests/unit/test_demo_skeptic_x_one.py" in files


# ---------- R2 ----------------------------------------------------------------

def test_R2_multiple_test_files_mixed_naming(tmp_path: Path) -> None:
    repo = _init_phase_2_ready(tmp_path)
    base = repo / "tests" / "unit"
    base.mkdir(parents=True, exist_ok=True)
    (base / "test_demo_skeptic_x_a.py").write_text("def test_a(): assert False\n")
    (base / "test_demo_skeptic_x_b.py").write_text("def test_b(): assert False\n")
    (base / "test_unrelated_naming.py").write_text("def test_c(): assert False\n")
    # invoke commit_phase_handoff
    files = _phase_2_files_in_commit(repo)
    assert "tests/unit/test_demo_skeptic_x_a.py" in files
    assert "tests/unit/test_demo_skeptic_x_b.py" in files
    assert "tests/unit/test_unrelated_naming.py" in files, (
        "non-slug-named test was excluded — discovery mechanism must be diff-based, not glob"
    )


# ---------- R3 ----------------------------------------------------------------

def test_R3_zero_test_files_preserves_existing_shape(tmp_path: Path) -> None:
    repo = _init_phase_2_ready(tmp_path)
    # invoke commit_phase_handoff with no test files written
    files = _phase_2_files_in_commit(repo)
    assert files == {".claude/handoff-phase-2.md"}, (
        f"R3: empty Phase-2 should commit only handoff-phase-2.md; got {files}"
    )


# ---------- R4 ----------------------------------------------------------------

def test_R4_test_file_and_handoff_modification(tmp_path: Path) -> None:
    repo = _init_phase_2_ready(tmp_path)
    # modify handoff-phase-2.md (replace stub content)
    (repo / ".claude" / "handoff-phase-2.md").write_text("---\nphase: 2\n---\nactual notes\n")
    # write a test file
    (repo / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "unit" / "test_demo_skeptic_x_d.py").write_text("def test_d(): assert False\n")
    # invoke commit_phase_handoff
    files = _phase_2_files_in_commit(repo)
    assert "tests/unit/test_demo_skeptic_x_d.py" in files
    assert ".claude/handoff-phase-2.md" in files
```

**Note for the implementer:** the `_init_phase_2_ready` and the orchestrator-hook invocation should mirror the existing harness in `tests/unit/test_orchestrator_bug_fixes.py` (see `_init_project` helper). The implementer must factor out a shared fixture or duplicate verbatim — do not invent a new fixture shape.

**Step 2: Run tests; confirm RED.**

Run: `uv run pytest tests/unit/test_phase_2_handoff_staging_surface.py -v`

Expected: 4 fails (NotImplementedError or AssertionError on each case).

---

### Task 2.3: Phase 3 GREEN — extend `commit_phase_handoff`

**File:** `scripts/slice_orchestrator/lifecycle.py`

**Step 1: Locate `commit_phase_handoff` (~line 1441-1452 per issue #26).**

**Step 2: Add a Phase-2-specific staging branch:**

```python
if current_phase == 2:
    # Issue #26: stage every file under tests/unit/ that diverges from the
    # Phase-1 boundary commit. Diff-based discovery — robust to slug-naming
    # convention drift. INV-008 DC-3 idempotency preserved by `git diff`'s
    # natural no-op behavior on already-staged paths.
    phase_1_boundary = _resolve_phase_boundary_commit(repo, current_phase=1)
    diff_out = subprocess.run(
        ["git", "diff", "--name-only", phase_1_boundary, "--", "tests/unit/"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for path in diff_out.splitlines():
        full = repo / path
        if full.exists():
            _git("add", str(full))
```

**Implementation notes:**
- `_resolve_phase_boundary_commit` may not exist; if not, find Phase-1's commit by `git log --grep='^phase-1:' -n 1 --format=%H` scoped to the current branch since the slice's start commit. Reuse any existing helper if present.
- Guard with `if full.exists():` per issue #26 §1; covers the case where `git diff` reports a deleted file.
- Do not use `git add -A` — issue #26 explicitly forbids it ("mirror Slice E's discipline").

**Step 3: Run the four tests; confirm GREEN.**

Run: `uv run pytest tests/unit/test_phase_2_handoff_staging_surface.py -v`

Expected: 4 passes.

**Step 4: Full suite regression.**

Run: `uv run pytest tests/unit/ -q`

Expected: 1160+4 passes, same 2 known fails, no new fails.

---

### Task 2.4: Phase 4 sweep + close_slice

Same shape as Task 1.4. Phase-4-integrator runs gates, writes sweep-notes.md. close_slice stages slice.yaml + handoff.md.

**Special verification step:** After close, manually exercise the Phase-2 staging fix on a synthetic slice to confirm it works end-to-end (not only in unit tests).

Run:
```bash
git log --pretty=%s -n 5 | grep '^phase-2:'
# For each phase-2 commit found, verify it includes test files:
git show --name-only --pretty= <phase-2-sha> | grep '^tests/unit/'
```
Expected: at least one `tests/unit/...` path per phase-2 commit on this branch henceforth.

---

## Post-slice handoff notes

After Slice 2 closes, the next handoff should record:

- **Resolved:** all four originally-named paper-cuts (#1, #2, #4 via Slice 1; #3 was misdiagnosed and required no fix).
- **Closed issue:** #26.
- **Lesson:** the 2026-05-02 sweep mis-attributed the malformed `sweep.yaml` to a phase-4 staging leak. The real cause was pre-fix data carried through commit `6cfa4d0`. Future sweep authors: verify a "leak" reproduces against current `lifecycle.py` before attributing to the orchestrator.

## Pre-existing failures (not in scope)

These remain after both slices and will be tracked in handoff:

- `test_d3_bypass_log_format::test_every_line_matches_classified_regex` (line 18 malformed; append-only log) — owned by `v1-defense-d3/bypass-log-test-resilience`.
- `test_extractor_slice::test_emits_parent_edge_to_feature` (XPASS-strict on un-squashed close commits) — relax `strict=True` or address in substrate Slice 4 (L-015).

"""Phase 2 validation tests for SLICE-012 — D3 snapshot-diff backstop.

Tests cover:
- Snapshot creation: file scanning, JSON structure, SHA-256 hashing
- Diff mode: detecting new/deleted/changed files, envelope cross-referencing
- Exit codes: 0 (clean), 1 (out-of-envelope changes), 2 (no prior snapshot)
- Falsification: planted out-of-envelope change must be caught (ADR-003 D3)

Tests are mechanism-agnostic — any Phase 3 implementation satisfying the
intent.md specification passes.  Tests exercise the script through subprocess
for consistent testing of exit codes and stdout/stderr.

Ambiguity resolutions (see validation/approach.md for full list):
  A1 — Exit code 2 for first-run (no prior snapshot), not 0.
  A3 — "Under X/" means recursive scan of subdirectories.
  A4 — Script operates on CWD as repo root.
  A5 — JSON entry must contain size (int) and hash (64-char hex); key names
       are implementation choice, verified structurally.
  A7 — No intent.md = no envelope = all changes are out-of-envelope.
  A8 — --diff with no prior snapshot creates one and exits 2.
"""

import json
import hashlib
import subprocess
import sys
import textwrap
from pathlib import Path



CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = CAIRN_ROOT / "scripts" / "snapshot_diff.py"


# --- Helpers ----------------------------------------------------------------


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run snapshot_diff.py with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_project(root: Path, files: dict[str, str] | None = None) -> None:
    """Create a minimal project structure for snapshot testing.

    files: mapping of relative paths to contents.
    """
    if files is None:
        files = {}
    for rel_path, content in files.items():
        p = root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)


def _make_intent(root: Path, envelope: list[str]) -> None:
    """Write a minimal intent.md with the given envelope globs."""
    intent_dir = root / ".claude" / "current-slice"
    intent_dir.mkdir(parents=True, exist_ok=True)
    envelope_yaml = "\n".join(f'  - "{g}"' for g in envelope)
    (intent_dir / "intent.md").write_text(
        textwrap.dedent(f"""\
            ```yaml
            slice: test-slice
            date: 2026-04-14
            phase: 3-implementation
            invariants-touched: []
            adrs-referenced: []
            envelope:
            {envelope_yaml}
            out-of-scope: []
            ```

            ### What and Why
            Test fixture.

            ### Specification Detail
            None.

            ### Verification
            None.
        """)
    )


def _sha256(content: str) -> str:
    """Return the SHA-256 hex digest of content."""
    return hashlib.sha256(content.encode()).hexdigest()


# --- Snapshot creation tests ------------------------------------------------


class TestSnapshotCreation:
    """Tests for `snapshot_diff.py --snapshot`."""

    def test_creates_snapshot_file(self, tmp_path):
        """Running --snapshot creates .claude/structural-snapshot.json."""
        _make_project(
            tmp_path,
            {
                "scripts/foo.py": "# foo",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot_path = tmp_path / ".claude" / "structural-snapshot.json"
        assert snapshot_path.exists(), "Snapshot file was not created"

    def test_snapshot_includes_py_under_scripts(self, tmp_path):
        """Snapshot includes .py files under scripts/."""
        _make_project(
            tmp_path,
            {
                "scripts/validate.py": "# validate",
                "scripts/helper.py": "# helper",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "scripts/validate.py" in snapshot
        assert "scripts/helper.py" in snapshot

    def test_snapshot_includes_py_under_checks(self, tmp_path):
        """Snapshot includes .py files under checks/."""
        _make_project(
            tmp_path,
            {
                "checks/hook.py": "# hook",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "checks/hook.py" in snapshot

    def test_snapshot_includes_py_under_tests(self, tmp_path):
        """Snapshot includes .py files under tests/."""
        _make_project(
            tmp_path,
            {
                "tests/unit/test_foo.py": "# test",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "tests/unit/test_foo.py" in snapshot

    def test_snapshot_includes_md_under_commands(self, tmp_path):
        """Snapshot includes .md files under commands/."""
        _make_project(
            tmp_path,
            {
                "commands/claude-code/start-slice.md": "# start",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "commands/claude-code/start-slice.md" in snapshot

    def test_snapshot_includes_md_under_docs(self, tmp_path):
        """Snapshot includes .md files under docs/."""
        _make_project(
            tmp_path,
            {
                "docs/operational-reference.md": "# ops",
                "docs/adr/003-cliff.md": "# cliff",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "docs/operational-reference.md" in snapshot
        assert "docs/adr/003-cliff.md" in snapshot

    def test_snapshot_recursive_under_subdirs(self, tmp_path):
        """Snapshot scans recursively — files in nested subdirs are included (A3)."""
        _make_project(
            tmp_path,
            {
                "scripts/deep/nested/module.py": "# deep",
                "tests/integration/sub/test_deep.py": "# deep test",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "scripts/deep/nested/module.py" in snapshot
        assert "tests/integration/sub/test_deep.py" in snapshot

    def test_snapshot_excludes_unscoped_files(self, tmp_path):
        """Snapshot excludes files not under the scoped directories."""
        _make_project(
            tmp_path,
            {
                "scripts/in_scope.py": "# in",
                "src/out_of_scope.py": "# out",
                "README.md": "# readme",
                "setup.py": "# setup",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        assert "scripts/in_scope.py" in snapshot
        assert "src/out_of_scope.py" not in snapshot
        assert "README.md" not in snapshot
        assert "setup.py" not in snapshot

    def test_snapshot_entry_has_size_and_hash(self, tmp_path):
        """Each snapshot entry records file size (int) and SHA-256 hash (A5)."""
        content = "hello world"
        _make_project(tmp_path, {"scripts/size_check.py": content})
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        entry = snapshot["scripts/size_check.py"]
        # Entry must be a dict (or list) containing size and hash info.
        # We check structurally: must have an integer matching the byte
        # length, and a string matching the SHA-256 hex digest.
        entry_str = json.dumps(entry)
        assert str(len(content.encode())) in entry_str, (
            f"Expected size {len(content.encode())} in entry"
        )
        expected_hash = _sha256(content)
        assert expected_hash in entry_str, f"Expected SHA-256 {expected_hash} in entry"

    def test_snapshot_keys_sorted(self, tmp_path):
        """Snapshot JSON object keys are sorted by path."""
        _make_project(
            tmp_path,
            {
                "scripts/z_last.py": "# z",
                "scripts/a_first.py": "# a",
                "scripts/m_middle.py": "# m",
            },
        )
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        raw = (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        snapshot = json.loads(raw)
        keys = list(snapshot.keys())
        assert keys == sorted(keys), f"Keys not sorted: {keys}"

    def test_snapshot_hash_is_sha256(self, tmp_path):
        """Hash in each entry is a valid 64-character hex SHA-256 digest."""
        content = "deterministic content"
        _make_project(tmp_path, {"scripts/hash_check.py": content})
        result = _run(tmp_path, "--snapshot")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (tmp_path / ".claude" / "structural-snapshot.json").read_text()
        )
        entry = snapshot["scripts/hash_check.py"]
        entry_str = json.dumps(entry)
        expected = _sha256(content)
        assert expected in entry_str
        # The hash must be exactly 64 hex characters
        assert len(expected) == 64
        assert all(c in "0123456789abcdef" for c in expected)


# --- Diff mode tests -------------------------------------------------------


class TestDiffMode:
    """Tests for `snapshot_diff.py --diff`."""

    def test_no_changes_exits_0(self, tmp_path):
        """--diff after --snapshot with no file changes exits 0."""
        _make_project(tmp_path, {"scripts/stable.py": "# stable"})
        _make_intent(tmp_path, ["scripts/*.py"])
        _run(tmp_path, "--snapshot")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 0, (
            f"Expected exit 0 for no changes, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_in_envelope_change_exits_0(self, tmp_path):
        """--diff ignores changes to files inside the declared envelope."""
        _make_project(
            tmp_path,
            {
                "scripts/gateway.py": "# original",
                "scripts/other.py": "# other",
            },
        )
        _make_intent(tmp_path, ["scripts/gateway.py"])
        _run(tmp_path, "--snapshot")
        # Modify a file that IS in the envelope
        (tmp_path / "scripts" / "gateway.py").write_text("# modified")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 0, (
            f"In-envelope change should not be flagged, got exit {result.returncode}\n"
            f"stdout: {result.stdout}"
        )

    def test_out_of_envelope_change_exits_1(self, tmp_path):
        """--diff detects changes to files outside the declared envelope, exits 1."""
        _make_project(
            tmp_path,
            {
                "scripts/gateway.py": "# gateway",
                "scripts/other.py": "# other",
            },
        )
        _make_intent(tmp_path, ["scripts/gateway.py"])
        _run(tmp_path, "--snapshot")
        # Modify a file NOT in the envelope
        (tmp_path / "scripts" / "other.py").write_text("# sneaky change")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1, (
            f"Expected exit 1 for out-of-envelope change, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_out_of_envelope_change_named_in_output(self, tmp_path):
        """--diff names the specific out-of-envelope file on stdout."""
        _make_project(
            tmp_path,
            {
                "scripts/gateway.py": "# gateway",
                "scripts/leaker.py": "# original",
            },
        )
        _make_intent(tmp_path, ["scripts/gateway.py"])
        _run(tmp_path, "--snapshot")
        (tmp_path / "scripts" / "leaker.py").write_text("# changed")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1
        assert "scripts/leaker.py" in result.stdout, (
            f"Changed file not named in output: {result.stdout}"
        )

    def test_new_file_outside_envelope_flagged(self, tmp_path):
        """--diff flags new files not matched by envelope globs."""
        _make_project(
            tmp_path,
            {
                "scripts/gateway.py": "# gateway",
            },
        )
        _make_intent(tmp_path, ["scripts/gateway.py"])
        _run(tmp_path, "--snapshot")
        # Add a new file outside the envelope
        (tmp_path / "scripts" / "surprise.py").write_text("# new file")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1, (
            f"Expected exit 1 for new out-of-envelope file, got {result.returncode}"
        )
        assert "scripts/surprise.py" in result.stdout

    def test_deleted_file_reported(self, tmp_path):
        """--diff reports files deleted since last snapshot."""
        _make_project(
            tmp_path,
            {
                "scripts/ephemeral.py": "# here today",
                "scripts/keeper.py": "# stable",
            },
        )
        _make_intent(tmp_path, ["scripts/keeper.py"])
        _run(tmp_path, "--snapshot")
        (tmp_path / "scripts" / "ephemeral.py").unlink()
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1, (
            f"Expected exit 1 for deleted file, got {result.returncode}"
        )
        assert "scripts/ephemeral.py" in result.stdout

    def test_no_prior_snapshot_exits_2(self, tmp_path):
        """--diff with no prior snapshot exits 2 and creates the snapshot (A1, A8)."""
        _make_project(tmp_path, {"scripts/first_run.py": "# new"})
        _make_intent(tmp_path, ["scripts/first_run.py"])
        # No --snapshot run first
        result = _run(tmp_path, "--diff")
        assert result.returncode == 2, (
            f"Expected exit 2 for missing snapshot, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Should have created the snapshot as a side effect
        snapshot_path = tmp_path / ".claude" / "structural-snapshot.json"
        assert snapshot_path.exists(), (
            "First-run --diff should create the snapshot file"
        )

    def test_no_intent_means_all_changes_flagged(self, tmp_path):
        """--diff with no intent.md treats all changes as out-of-envelope (A7)."""
        _make_project(tmp_path, {"scripts/orphan.py": "# original"})
        # No intent.md created
        _run(tmp_path, "--snapshot")
        (tmp_path / "scripts" / "orphan.py").write_text("# changed")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1, (
            f"Expected exit 1 when no envelope exists, got {result.returncode}"
        )

    def test_envelope_glob_matching(self, tmp_path):
        """Envelope globs use fnmatch-style patterns to match file paths."""
        _make_project(
            tmp_path,
            {
                "scripts/integration_gate.py": "# gate",
                "scripts/snapshot_diff.py": "# diff",
                "scripts/validate_architecture.py": "# validate",
                "tests/unit/test_gate.py": "# test",
            },
        )
        _make_intent(
            tmp_path,
            [
                "scripts/integration_gate.py",
                "scripts/snapshot_diff.py",
                "tests/unit/test_gate.py",
            ],
        )
        _run(tmp_path, "--snapshot")
        # Change an in-envelope file — should be OK
        (tmp_path / "scripts" / "integration_gate.py").write_text("# v2")
        # Change an out-of-envelope file — should be flagged
        (tmp_path / "scripts" / "validate_architecture.py").write_text("# oops")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1
        assert "scripts/validate_architecture.py" in result.stdout
        assert "scripts/integration_gate.py" not in result.stdout

    def test_wildcard_envelope_glob(self, tmp_path):
        """Envelope globs with wildcards match multiple files."""
        _make_project(
            tmp_path,
            {
                "tests/unit/test_a.py": "# a",
                "tests/unit/test_b.py": "# b",
                "scripts/unrelated.py": "# no",
            },
        )
        _make_intent(tmp_path, ["tests/unit/test_*.py"])
        _run(tmp_path, "--snapshot")
        (tmp_path / "tests" / "unit" / "test_a.py").write_text("# changed")
        (tmp_path / "scripts" / "unrelated.py").write_text("# also changed")
        result = _run(tmp_path, "--diff")
        assert result.returncode == 1
        # test_a.py is in envelope — should NOT be listed
        assert "tests/unit/test_a.py" not in result.stdout
        # unrelated.py is out of envelope — SHOULD be listed
        assert "scripts/unrelated.py" in result.stdout


# --- Falsification test (ADR-003 D3 requirement) ---------------------------


class TestFalsification:
    """D3 falsification: planted violation that snapshot-diff MUST catch.

    ADR-003 requires a pre-specified calibration case that, if the check
    does not flag, causes D3 to be rejected at Phase 4.
    """

    def test_planted_out_of_envelope_change_caught(self, tmp_path):
        """Falsification: modify a file outside the declared envelope.

        Setup:
          - Project with scripts/gateway.py (in envelope) and
            scripts/validate_architecture.py (out of envelope)
          - Take snapshot
          - Modify validate_architecture.py

        Expected: snapshot_diff --diff exits 1 and names the file.
        If this test does not pass, D3 is rejected per ADR-003.
        """
        _make_project(
            tmp_path,
            {
                "scripts/gateway.py": "def gate(): pass",
                "scripts/validate_architecture.py": "def validate(): pass",
                "docs/operational-reference.md": "# Operations",
                "commands/claude-code/start-slice.md": "# Start",
            },
        )
        _make_intent(tmp_path, ["scripts/gateway.py"])
        # Take baseline snapshot
        snap_result = _run(tmp_path, "--snapshot")
        assert snap_result.returncode == 0, (
            f"Snapshot creation failed: {snap_result.stderr}"
        )
        # Plant the violation: modify an out-of-envelope file
        (tmp_path / "scripts" / "validate_architecture.py").write_text(
            "def validate(): return False  # silently broken"
        )
        # D3 must catch this
        diff_result = _run(tmp_path, "--diff")
        assert diff_result.returncode == 1, (
            f"FALSIFICATION FAILURE: out-of-envelope change not detected. "
            f"Exit code: {diff_result.returncode}\n"
            f"stdout: {diff_result.stdout}\nstderr: {diff_result.stderr}"
        )
        assert "scripts/validate_architecture.py" in diff_result.stdout, (
            f"FALSIFICATION FAILURE: changed file not named in output.\n"
            f"stdout: {diff_result.stdout}"
        )

"""Phase 2 validation tests for SLICE-004 — dogfood evaluation substrate.

Verifies intent.md V1–V6 plus ambiguity resolutions from Phase 2
brainstorming: duplicate-entry warnings, unclear-disposition penalty,
cumulative false-positive threshold, baseline from log frontmatter,
sweep.yaml missing behavior.

Tests run the evaluator as a subprocess (same pattern as
test_validate_architecture.py). All tests fail in Phase 2 because
scripts/dogfood_evaluate.py does not exist yet.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
EVALUATOR = CAIRN_ROOT / "scripts" / "dogfood_evaluate.py"


# --- Fixtures --------------------------------------------------------------


def _write_sweep_yaml(root: Path, current_slice_number: int = 4) -> None:
    """Write a minimal sweep.yaml with the given current-slice-number."""
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "sweep.yaml").write_text(
        textwrap.dedent(f"""\
            last-sweep-at-slice: 0
            sweep-interval: 3
            current-slice-number: {current_slice_number}
        """)
    )


def _make_log(
    root: Path,
    entries: list[dict],
    *,
    baseline: int = 2,
    schema_version: int = 1,
) -> None:
    """Write docs/dogfood-log.md with YAML-frontmattered header and entries.

    Each entry dict must have: slice, date, defense, type, description,
    would-manual-have-caught, disposition. Missing keys are left out
    (for malformed-entry tests).
    """
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    lines = [
        "---",
        f"schema-version: {schema_version}",
        f"adr-003-landed-at-slice: {baseline}",
        "---",
        "",
        "# Dogfood Log",
        "",
    ]

    for entry in entries:
        lines.append("```yaml")
        for key in (
            "slice",
            "date",
            "defense",
            "type",
            "description",
            "would-manual-have-caught",
            "disposition",
        ):
            if key in entry:
                lines.append(f"{key}: {entry[key]}")
        lines.append("```")
        lines.append("")

    (docs / "dogfood-log.md").write_text("\n".join(lines))


def _make_empty_log(root: Path, *, baseline: int = 2) -> None:
    """Write a dogfood-log.md with frontmatter but zero entries."""
    _make_log(root, [], baseline=baseline)


def _confirmed_catch(
    *,
    slice_id: str = "SLICE-005",
    date: str = "2026-04-15",
    defense: str = "D1",
    would_manual: str = "no",
    description: str = "caught architecture drift",
) -> dict:
    """Return a single confirmed-catch entry dict."""
    return {
        "slice": slice_id,
        "date": date,
        "defense": defense,
        "type": "catch",
        "description": description,
        "would-manual-have-caught": would_manual,
        "disposition": "confirmed",
    }


def _confirmed_fp(
    *,
    slice_id: str = "SLICE-005",
    date: str = "2026-04-15",
    defense: str = "D1",
    description: str = "false positive on import check",
) -> dict:
    """Return a single confirmed false-positive entry dict."""
    return {
        "slice": slice_id,
        "date": date,
        "defense": defense,
        "type": "false-positive",
        "description": description,
        "would-manual-have-caught": "no",
        "disposition": "confirmed",
    }


def _run(
    cwd: Path,
    env_overrides: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run the evaluator script as a subprocess."""
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(EVALUATOR)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _assert_evaluator_ran(result: subprocess.CompletedProcess) -> None:
    """Guard: confirm the evaluator script actually executed (not Python's own
    'can't open file' exit 2).  The evaluator must produce stdout output."""
    assert "can't open file" not in result.stderr, (
        f"Evaluator script not found — tests are passing for the wrong reason.\n"
        f"stderr:\n{result.stderr}"
    )


# --- V1: Exit 2 on empty log, slice count < 10 ----------------------------


class TestV1InsufficientData:
    """V1 — evaluator exits 2 when log has zero entries and < 10 post-ADR-003 slices."""

    def test_empty_log_under_threshold_exits_2(self, tmp_path):
        """Zero entries, current-slice-number=4, baseline=2 → 2 post-ADR-003 slices → exit 2."""
        _make_empty_log(tmp_path, baseline=2)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_no_log_file_exits_2(self, tmp_path):
        """No dogfood-log.md at all → exit 2."""
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (missing log), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V2: Exit 0 on confirmed automated catch, no FP threshold breach ------


class TestV2PassOnCatch:
    """V2 — evaluator exits 0 when ≥1 confirmed catch with would-manual=no
    and no defense exceeds false-positive threshold."""

    def test_one_confirmed_catch_no_fp_exits_0(self, tmp_path):
        """One confirmed catch, would-manual=no, zero FPs → exit 0."""
        _make_log(tmp_path, [_confirmed_catch()])
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (pass), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_catch_with_below_threshold_fp_exits_0(self, tmp_path):
        """One confirmed catch + 2 FPs for same defense → still exit 0 (threshold is 3)."""
        entries = [
            _confirmed_catch(defense="D1"),
            _confirmed_fp(defense="D1", slice_id="SLICE-006", description="fp one"),
            _confirmed_fp(defense="D1", slice_id="SLICE-007", description="fp two"),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (below FP threshold), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V3: Exit 1 on ≥3 confirmed false positives ---------------------------


class TestV3FalsePositiveThreshold:
    """V3 — evaluator exits 1 when any defense has ≥3 confirmed false positives."""

    def test_three_fp_same_defense_exits_1(self, tmp_path):
        """3 confirmed FPs for D1 → exit 1 regardless of catches."""
        entries = [
            _confirmed_catch(defense="D2"),  # catch exists but on different defense
            _confirmed_fp(defense="D1", slice_id="SLICE-005", description="fp 1"),
            _confirmed_fp(defense="D1", slice_id="SLICE-006", description="fp 2"),
            _confirmed_fp(defense="D1", slice_id="SLICE-007", description="fp 3"),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (FP threshold breached), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_three_fp_across_defenses_no_fail(self, tmp_path):
        """1 FP each for D1, D2, D3 → no single defense breaches threshold → not a FP fail."""
        entries = [
            _confirmed_catch(defense="D1"),
            _confirmed_fp(defense="D1", slice_id="SLICE-005", description="fp d1"),
            _confirmed_fp(defense="D2", slice_id="SLICE-006", description="fp d2"),
            _confirmed_fp(defense="D3", slice_id="SLICE-007", description="fp d3"),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (no single defense at threshold), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V4: Exit 1 on 10+ slices but no automated catch ----------------------


class TestV4NoAutomatedCatch:
    """V4 — evaluator exits 1 when 10+ post-ADR-003 slices but no confirmed automated catch."""

    def test_ten_slices_no_catch_exits_1(self, tmp_path):
        """current-slice-number=12, baseline=2 → 10 post-ADR-003 slices, zero catches → exit 1."""
        _make_empty_log(tmp_path, baseline=2)
        _write_sweep_yaml(tmp_path, current_slice_number=12)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (10+ slices, no catch), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V5: Malformed entries warn and skip -----------------------------------


class TestV5MalformedEntries:
    """V5 — malformed entries (missing required fields) produce stderr warning
    and are skipped, not a crash."""

    def test_malformed_entry_missing_field_skipped(self, tmp_path):
        """Entry missing 'defense' field → stderr warning, no crash."""
        malformed = {
            "slice": "SLICE-005",
            "date": "2026-04-15",
            # "defense" deliberately missing
            "type": "catch",
            "description": "missing defense field",
            "would-manual-have-caught": "no",
            "disposition": "confirmed",
        }
        _make_log(tmp_path, [malformed])
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        # Should not crash (returncode != unexpected error)
        assert result.returncode in (0, 1, 2), (
            f"Unexpected exit code {result.returncode} — possible crash.\n"
            f"stderr:\n{result.stderr}"
        )
        assert "warning" in result.stderr.lower() or "skip" in result.stderr.lower(), (
            f"Expected stderr warning about malformed entry.\nstderr:\n{result.stderr}"
        )

    def test_malformed_entry_among_valid(self, tmp_path):
        """One bad + one good entry → good entry still evaluated, evaluator doesn't crash."""
        malformed = {
            "slice": "SLICE-005",
            "date": "2026-04-15",
            # missing several required fields
            "type": "catch",
        }
        valid = _confirmed_catch(slice_id="SLICE-006")
        _make_log(tmp_path, [malformed, valid])
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        # Valid catch exists → should pass (exit 0) despite malformed entry
        assert result.returncode == 0, (
            f"Expected exit 0 (valid catch present), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "warning" in result.stderr.lower() or "skip" in result.stderr.lower(), (
            f"Expected stderr warning about malformed entry.\nstderr:\n{result.stderr}"
        )


# --- V6: Project-root resolution ------------------------------------------


class TestV6ProjectRoot:
    """V6 — project-root resolution follows same three-step pattern as validate_architecture.py."""

    def test_root_from_env_var(self, tmp_path):
        """CLAUDE_PROJECT_DIR set → used as project root."""
        _make_empty_log(tmp_path, baseline=2)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        # Should run without root-resolution error (exit 2 = insufficient data, not root failure)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "cannot identify project root" not in result.stderr.lower()

    def test_root_from_git(self, tmp_path):
        """CLAUDE_PROJECT_DIR unset, git repo exists → git toplevel used."""
        _make_empty_log(tmp_path, baseline=2)
        _write_sweep_yaml(tmp_path, current_slice_number=4)
        subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)

        result = _run(tmp_path)

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "cannot identify project root" not in result.stderr.lower()

    def test_root_neither_exits_2(self, tmp_path):
        """No CLAUDE_PROJECT_DIR, no git repo → exit 2 with diagnostic."""
        # No log, no sweep, no git — just an empty dir
        result = _run(tmp_path)

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (root resolution failure), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- Ambiguity resolutions ------------------------------------------------


class TestAmbiguityDuplicateEntries:
    """Duplicate entries (same slice+defense+date) produce stderr warning,
    both are counted."""

    def test_duplicate_entries_warn_stderr(self, tmp_path):
        """Two entries same slice+defense+date, different description → warning, both counted."""
        entries = [
            _confirmed_catch(
                slice_id="SLICE-005",
                date="2026-04-15",
                defense="D1",
                description="caught drift in module A",
            ),
            _confirmed_catch(
                slice_id="SLICE-005",
                date="2026-04-15",
                defense="D1",
                description="caught drift in module B",
            ),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        # Both are valid catches → exit 0
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        # Should warn about potential duplicates
        assert "duplicate" in result.stderr.lower(), (
            f"Expected stderr warning about duplicate entries.\nstderr:\n{result.stderr}"
        )


class TestAmbiguityUnclearDisposition:
    """Entries with would-manual-have-caught=unclear count toward catch-rate
    but cause overall fail until resolved."""

    def test_unclear_counts_for_catch_but_overall_fails(self, tmp_path):
        """Entry with would-manual=unclear, disposition=confirmed → catch criterion
        satisfied, but overall exit 1 because unclear is unresolved."""
        entries = [
            _confirmed_catch(would_manual="unclear"),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (unresolved unclear), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert (
            "unclear" in result.stdout.lower() or "unclear" in result.stderr.lower()
        ), (
            f"Expected output to mention unclear entries.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_no_unclear_entries_passes(self, tmp_path):
        """All entries have would-manual=yes or no → no unclear penalty."""
        entries = [
            _confirmed_catch(would_manual="no"),
            _confirmed_catch(
                slice_id="SLICE-006",
                would_manual="yes",
                description="manual would have caught",
            ),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (no unclear penalty), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestAmbiguitySweepYamlMissing:
    """Missing sweep.yaml → exit 2."""

    def test_sweep_yaml_missing_exits_2(self, tmp_path):
        """Log exists but no sweep.yaml → exit 2."""
        _make_empty_log(tmp_path, baseline=2)
        # No _write_sweep_yaml call

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (missing sweep.yaml), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestAmbiguityFPCumulative:
    """False-positive threshold is cumulative across all slices, not windowed."""

    def test_fp_cumulative_across_slices(self, tmp_path):
        """3 FPs for D1 spread across 3 different slices → threshold breached."""
        entries = [
            _confirmed_catch(defense="D2"),  # have a catch so it's not "no catch" fail
            _confirmed_fp(defense="D1", slice_id="SLICE-005", description="fp 1"),
            _confirmed_fp(defense="D1", slice_id="SLICE-008", description="fp 2"),
            _confirmed_fp(defense="D1", slice_id="SLICE-011", description="fp 3"),
        ]
        _make_log(tmp_path, entries)
        _write_sweep_yaml(tmp_path, current_slice_number=4)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (cumulative FP threshold), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestAmbiguityBaselineFromFrontmatter:
    """Evaluator reads adr-003-landed-at-slice from dogfood-log.md frontmatter."""

    def test_baseline_read_from_log_frontmatter(self, tmp_path):
        """baseline=5, current-slice-number=14 → 9 post-ADR-003 slices → insufficient (< 10).
        If evaluator hardcodes baseline=2, it would compute 12 slices and behave differently."""
        _make_empty_log(tmp_path, baseline=5)
        _write_sweep_yaml(tmp_path, current_slice_number=14)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        # 14 - 5 = 9 slices, empty log → exit 2 (insufficient data)
        assert result.returncode == 2, (
            f"Expected exit 2 (9 slices < 10 threshold), got {result.returncode}.\n"
            f"If exit 1, evaluator may be hardcoding baseline instead of reading frontmatter.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

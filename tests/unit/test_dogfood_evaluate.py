"""Phase 2 validation tests for dogfood evaluation substrate.

Originally the dogfood-evaluator slice (V1-V6 + ambiguity resolutions). Rewritten for
identifier-scheme/slice-and-feature-rename (Phase 2 Part 2) per intent §12:

  - sweep.yaml fixture emits new shape: `sweep-interval` +
    `last-sweep-at-slice-id` only (no `current-slice-number`).
  - Tests that formerly seeded `current-slice-number: N` now stage synthetic
    git history with an ADR `cliff-failure-mode-and-v1-defenses` introducing-commit
    followed by N `^slice: .* — complete$` commits (intent §9 replumbing).
  - `docs/dogfood-log.md` frontmatter no longer carries `adr-003-landed-at-slice:`
    — §9 disposition (C) drop. Baseline is derived purely from git history.
  - New class TestBaselineMissingFallback encodes the §8 fallback philosophy
    (intent §184) as an in-envelope analog: when the baseline-ADR's
    introducing-commit cannot be resolved, the evaluator emits a stderr
    diagnostic and proceeds
    (does not silently skip) — mirroring §8's "sweep due" conservative default
    for `/start-slice complete`. Literal §8 sweep-due logic lives in markdown
    prose (`commands/claude-code/start-slice.full.md`) and is a Phase 4 Auditor
    prose-grep check, not a Phase 2 pytest surface.

RED pre-Phase-3 (fails against the current `_read_sweep_yaml`-based evaluator);
GREEN post-Phase-3 once the git-log counter lands.

Pytest + stdlib only.
"""

import os
import subprocess
import sys
from pathlib import Path


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
EVALUATOR = CAIRN_ROOT / "scripts" / "dogfood_evaluate.py"

ADR_BASELINE_PATH = "docs/adr/cliff-failure-mode-and-v1-defenses.md"


# --- Git-history fixtures --------------------------------------------------


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
    )
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_with_adr_and_slices(
    root: Path,
    *,
    slices_since_adr: int,
    include_adr: bool = True,
) -> None:
    """Stage git history for the new counter.

    Layout:
      1. `initial` seed commit (so HEAD always exists).
      2. If include_adr=True: one commit adding ADR_BASELINE_PATH — this is
         the baseline commit the new counter resolves.
      3. `slices_since_adr` commits with subjects matching
         `^slice: .* — complete$` (the pattern intent §9 tells the counter
         to match).

    If include_adr=False, step 2 is skipped — the evaluator cannot resolve a
    baseline and must exercise the fallback (see TestBaselineMissingFallback).
    """
    _git("init", "--quiet", "-b", "main", cwd=root)

    (root / "README.md").write_text("# test\n")
    _git("add", "README.md", cwd=root)
    _git("commit", "--quiet", "-m", "initial", cwd=root)

    if include_adr:
        adr_dir = root / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "cliff-failure-mode-and-v1-defenses.md").write_text(
            "---\nid: cliff-failure-mode-and-v1-defenses\nstatus: accepted\n---\n"
            "# ADR stub (test fixture)\n"
        )
        _git("add", ADR_BASELINE_PATH, cwd=root)
        _git(
            "commit",
            "--quiet",
            "-m",
            "adr: add cliff-failure-mode-and-v1-defenses",
            cwd=root,
        )

    for i in range(slices_since_adr):
        bump = root / f"slice-{i}.txt"
        bump.write_text(f"bump {i}\n")
        _git("add", bump.name, cwd=root)
        _git(
            "commit",
            "--quiet",
            "-m",
            f"slice: fixture/slice-{i} — complete",
            cwd=root,
        )


def _write_sweep_yaml(
    root: Path,
    *,
    last_sweep_at_slice_id: str | None = None,
    sweep_interval: int = 3,
) -> None:
    """Write sweep.yaml in the post-retirement shape (intent §7).

    Only `sweep-interval` and `last-sweep-at-slice-id` are emitted;
    `current-slice-number` is never written. `last-sweep-at-slice-id: null`
    is the default (no sweep performed yet).
    """
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    if last_sweep_at_slice_id is None:
        pointer_line = "last-sweep-at-slice-id: null"
    else:
        pointer_line = f"last-sweep-at-slice-id: {last_sweep_at_slice_id}"
    (root / ".claude" / "sweep.yaml").write_text(
        f"sweep-interval: {sweep_interval}\n{pointer_line}\n"
    )


def _make_log(
    root: Path,
    entries: list[dict],
    *,
    schema_version: int = 1,
    include_legacy_baseline_key: bool = False,
) -> None:
    """Write docs/dogfood-log.md with YAML-frontmatter header and entries.

    Default frontmatter omits `adr-003-landed-at-slice:` per intent §9 drop.
    Pass include_legacy_baseline_key=True to seed a stale key and assert the
    evaluator ignores it (regression guard for the §9 disposition).
    """
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    frontmatter_lines = [f"schema-version: {schema_version}"]
    if include_legacy_baseline_key:
        frontmatter_lines.append("adr-003-landed-at-slice: 2")

    lines = ["---", *frontmatter_lines, "---", "", "# Dogfood Log", ""]

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


def _make_empty_log(root: Path, **kwargs) -> None:
    """Write a dogfood-log.md with frontmatter but zero entries."""
    _make_log(root, [], **kwargs)


def _confirmed_catch(
    *,
    slice_id: str = "fixture/slice-0",
    date: str = "2026-04-15",
    defense: str = "D1",
    would_manual: str = "no",
    description: str = "caught architecture drift",
) -> dict:
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
    slice_id: str = "fixture/slice-0",
    date: str = "2026-04-15",
    defense: str = "D1",
    description: str = "false positive on import check",
) -> dict:
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
    assert "can't open file" not in result.stderr, (
        f"Evaluator script not found — tests are passing for the wrong reason.\n"
        f"stderr:\n{result.stderr}"
    )


# --- V1: Exit 2 on empty log, slice count < 10 ----------------------------


class TestV1InsufficientData:
    """V1 — evaluator exits 2 when log has zero entries and < 10 post-cliff slices."""

    def test_empty_log_under_threshold_exits_2(self, tmp_path):
        """Zero entries, 2 post-cliff slices → exit 2 (insufficient data)."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_no_log_file_exits_2(self, tmp_path):
        """No dogfood-log.md at all → exit 2."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)

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
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(tmp_path, [_confirmed_catch()])

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (pass), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_catch_with_below_threshold_fp_exits_0(self, tmp_path):
        """One confirmed catch + 2 FPs for same defense → still exit 0 (threshold is 3)."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(defense="D1"),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-1", description="fp one"
                ),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-2", description="fp two"
                ),
            ],
        )

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
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(defense="D2"),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-1", description="fp 1"
                ),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-2", description="fp 2"
                ),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-3", description="fp 3"
                ),
            ],
        )

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (FP threshold breached), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_three_fp_across_defenses_no_fail(self, tmp_path):
        """1 FP each for D1, D2, D3 → no single defense breaches threshold."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(defense="D1"),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-1", description="fp d1"
                ),
                _confirmed_fp(
                    defense="D2", slice_id="fixture/slice-2", description="fp d2"
                ),
                _confirmed_fp(
                    defense="D3", slice_id="fixture/slice-3", description="fp d3"
                ),
            ],
        )

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (no single defense at threshold), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V4: Exit 1 on 10+ slices but no automated catch ----------------------


class TestV4NoAutomatedCatch:
    """V4 — evaluator exits 1 when 10+ post-cliff slices but no confirmed
    automated catch."""

    def test_ten_slices_no_catch_exits_1(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=10)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (10+ slices, no catch), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- V5: Malformed entries warn and skip -----------------------------------


class TestV5MalformedEntries:
    """V5 — malformed entries produce stderr warning and are skipped."""

    def test_malformed_entry_missing_field_skipped(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        malformed = {
            "slice": "fixture/slice-0",
            "date": "2026-04-15",
            # "defense" deliberately missing
            "type": "catch",
            "description": "missing defense field",
            "would-manual-have-caught": "no",
            "disposition": "confirmed",
        }
        _make_log(tmp_path, [malformed])

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode in (0, 1, 2), (
            f"Unexpected exit code {result.returncode} — possible crash.\n"
            f"stderr:\n{result.stderr}"
        )
        assert "warning" in result.stderr.lower() or "skip" in result.stderr.lower(), (
            f"Expected stderr warning about malformed entry.\nstderr:\n{result.stderr}"
        )

    def test_malformed_entry_among_valid(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        malformed = {
            "slice": "fixture/slice-0",
            "date": "2026-04-15",
            "type": "catch",
        }
        valid = _confirmed_catch(slice_id="fixture/slice-1")
        _make_log(tmp_path, [malformed, valid])

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (valid catch present), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "warning" in result.stderr.lower() or "skip" in result.stderr.lower(), (
            f"Expected stderr warning about malformed entry.\nstderr:\n{result.stderr}"
        )


# --- V6: Project-root resolution ------------------------------------------


class TestV6ProjectRoot:
    """V6 — project-root resolution follows same pattern as validate_architecture.py."""

    def test_root_from_env_var(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "cannot identify project root" not in result.stderr.lower()

    def test_root_from_git(self, tmp_path):
        """CLAUDE_PROJECT_DIR unset, git repo exists → git toplevel used."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path)

        _assert_evaluator_ran(result)
        assert result.returncode == 2, (
            f"Expected exit 2 (insufficient data), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "cannot identify project root" not in result.stderr.lower()

    def test_root_neither_exits_2(self, tmp_path):
        """No CLAUDE_PROJECT_DIR, no git repo → exit 2 with diagnostic."""
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
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(
                    slice_id="fixture/slice-0",
                    date="2026-04-15",
                    defense="D1",
                    description="caught drift in module A",
                ),
                _confirmed_catch(
                    slice_id="fixture/slice-0",
                    date="2026-04-15",
                    defense="D1",
                    description="caught drift in module B",
                ),
            ],
        )

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "duplicate" in result.stderr.lower(), (
            f"Expected stderr warning about duplicate entries.\nstderr:\n{result.stderr}"
        )


class TestAmbiguityUnclearDisposition:
    """Entries with would-manual-have-caught=unclear count toward catch-rate
    but cause overall fail until resolved."""

    def test_unclear_counts_for_catch_but_overall_fails(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(tmp_path, [_confirmed_catch(would_manual="unclear")])

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
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(would_manual="no"),
                _confirmed_catch(
                    slice_id="fixture/slice-1",
                    would_manual="yes",
                    description="manual would have caught",
                ),
            ],
        )

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (no unclear penalty), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestAmbiguitySweepYamlIrrelevant:
    """Post-§9 replumbing: dogfood_evaluate.py no longer reads sweep.yaml.

    Previously a missing sweep.yaml meant a missing `current-slice-number`
    → exit 2. Under the git-log counter, sweep.yaml is irrelevant to the
    evaluator — it evaluates on git history + dogfood log alone.
    """

    def test_missing_sweep_yaml_does_not_affect_evaluator(self, tmp_path):
        """No sweep.yaml written → evaluator still evaluates from git history."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _make_log(tmp_path, [_confirmed_catch()])
        # Deliberately no _write_sweep_yaml call.

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 0, (
            f"Expected exit 0 (catch present, sweep.yaml irrelevant), "
            f"got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestAmbiguityFPCumulative:
    """False-positive threshold is cumulative across all slices, not windowed."""

    def test_fp_cumulative_across_slices(self, tmp_path):
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=2)
        _write_sweep_yaml(tmp_path)
        _make_log(
            tmp_path,
            [
                _confirmed_catch(defense="D2"),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-1", description="fp 1"
                ),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-2", description="fp 2"
                ),
                _confirmed_fp(
                    defense="D1", slice_id="fixture/slice-3", description="fp 3"
                ),
            ],
        )

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (cumulative FP threshold), got {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- §9 disposition (drop adr-003-landed-at-slice) -------------------------


class TestFrontmatterBaselineKeyIgnored:
    """Intent §9 disposition (C) — the `adr-003-landed-at-slice` frontmatter
    key is dropped. The evaluator MUST NOT read it; baseline comes purely from
    git history (the ADR introducing-commit). Regression guard against a
    future reintroduction of the frontmatter-read codepath.
    """

    def test_stale_frontmatter_key_does_not_override_git_baseline(self, tmp_path):
        """Stale `adr-003-landed-at-slice: 2` present in frontmatter but git
        history has 10 slice-complete commits since the ADR introducing-commit
        → exit 1 (no catch with ≥10 slices), matching git-based baseline.

        If the evaluator reread the frontmatter, baseline would be 2 (mismatched
        with git); the counter semantics are undefined in that case. This test
        asserts the field is ignored regardless of value.
        """
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=10)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path, include_legacy_baseline_key=True)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode == 1, (
            f"Expected exit 1 (10 slices since ADR, no catch), "
            f"got {result.returncode}. Stale frontmatter key may be leaking "
            f"into baseline computation.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# --- §8-analog fallback (intent §184) --------------------------------------


class TestBaselineMissingFallback:
    """§8-analog fallback (intent §184).

    §8 says `/start-slice complete` falls back to 'sweep due' + stderr
    diagnostic when `last-sweep-at-slice-id:` is unresolvable — conservative
    default so sweeps aren't silently skipped. The dogfood evaluator carries
    the analogous concern: if the ADR `cliff-failure-mode-and-v1-defenses`
    introducing-commit cannot be resolved, the evaluator MUST NOT silently
    succeed (exit 0) — it must emit a stderr diagnostic and proceed with a
    conservative default.

    This test asserts the structural properties of the fallback without
    pinning a specific exit code (Phase 3 chooses between "proceed with
    first-commit baseline" and "exit 2 with diagnostic" — either is
    §8-spirit-compliant so long as silent-pass is precluded).
    """

    def test_missing_adr_baseline_emits_stderr_diagnostic(self, tmp_path):
        """ADR introducing-commit absent from git history → stderr contains
        a baseline-missing diagnostic."""
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=5, include_adr=False)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        stderr_lower = result.stderr.lower()
        assert (
            "baseline" in stderr_lower
            or "cliff" in stderr_lower
            or "adr" in stderr_lower
        ), (
            f"Expected stderr diagnostic mentioning baseline/cliff/adr "
            f"when the ADR introducing-commit is unresolvable.\n"
            f"stderr:\n{result.stderr}"
        )

    def test_missing_adr_baseline_does_not_silent_pass(self, tmp_path):
        """ADR introducing-commit absent + empty dogfood log → evaluator
        does NOT return exit 0 (silent pass). Must return 1 or 2, mirroring
        §8's 'don't silently skip' philosophy.
        """
        _init_git_with_adr_and_slices(tmp_path, slices_since_adr=5, include_adr=False)
        _write_sweep_yaml(tmp_path)
        _make_empty_log(tmp_path)

        result = _run(tmp_path, env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)})

        _assert_evaluator_ran(result)
        assert result.returncode != 0, (
            f"Baseline-missing + empty log MUST NOT silent-pass (exit 0).\n"
            f"Got exit {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert result.returncode in (1, 2), (
            f"Expected exit 1 (proceed with conservative baseline) or exit 2 "
            f"(diagnostic + skip), got {result.returncode}.\n"
            f"stderr:\n{result.stderr}"
        )

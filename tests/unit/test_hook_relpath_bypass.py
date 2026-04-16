"""Phase 2 validation tests for SLICE-018 — reversibility-guard path normalization.

reversibility-guard.sh today applies its ADR append-only patterns
`*/docs/adr/index.md` (exempt) and `*/docs/adr/*.md` (deny) directly against
`tool_input.file_path`. The leading `*/` requires at least one path segment
before `docs/`, so bare-relative paths like `docs/adr/identifier-scheme.md`
match nothing and fall through to `exit 0`. Reproduced pre-slice: bare-relative
Write and body-Edit on an existing flat-slug ADR both return exit 0 today.

This slice normalizes `$FILE` to a project-root-relative canonical form
before pattern matching so that three input shapes — absolute, bare-relative,
`.slice-system/`-prefixed — produce one deny/allow verdict per tool semantics.

Tests invoke the hook via subprocess with synthesized JSON payloads (the same
shape the Claude Code PreToolUse harness sends).

Hook interface: JSON on stdin with tool_name + tool_input. Exit 0 = allow,
exit 2 = deny (with JSON deny reason on stdout).

RED (currently fail; Phase 3 must make green):
  V1  — bare-relative flat-slug Write / body Edit blocked
  V2  — bare-relative legacy Write / body Edit blocked
  V7  — bare-relative editorial-fix writes a log entry
  V12 — verdict symmetry across shapes (bare-relative diverges today)

GREEN (regression guards; must stay green):
  V3  — `.slice-system/`-prefixed shapes deny
  V4  — frontmatter Edit allowed across all shapes (flat + legacy)
  V5  — new-ADR Write allowed across all shapes
  V6  — index.md exempt across all shapes
  V8  — `.env` and lockfile denies unchanged
  V10 — missing jq returns exit 0 with warning
  V11 — no-crash under indeterminate project root

V9 (test_hook_tolerance.py staying green unmodified) is a Phase 4 full-suite
check, not a unit-test assertion in this file.

Pytest + stdlib only.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
REVERSIBILITY_GUARD = CAIRN_ROOT / "checks" / "reversibility-guard.sh"

FLAT_SLUG_ABS = str(CAIRN_ROOT / "docs/adr/identifier-scheme.md")
FLAT_SLUG_REL = "docs/adr/identifier-scheme.md"
FLAT_SLUG_SS = ".slice-system/docs/adr/identifier-scheme.md"

LEGACY_ABS = str(CAIRN_ROOT / "docs/adr/006-feature-slice-model.md")
LEGACY_REL = "docs/adr/006-feature-slice-model.md"
LEGACY_SS = ".slice-system/docs/adr/006-feature-slice-model.md"

NEW_FLAT_ABS = str(CAIRN_ROOT / "docs/adr/future-unused.md")
NEW_FLAT_REL = "docs/adr/future-unused.md"
NEW_FLAT_SS = ".slice-system/docs/adr/future-unused.md"
NEW_LEGACY_ABS = str(CAIRN_ROOT / "docs/adr/999-future.md")
NEW_LEGACY_REL = "docs/adr/999-future.md"
NEW_LEGACY_SS = ".slice-system/docs/adr/999-future.md"

INDEX_ABS = str(CAIRN_ROOT / "docs/adr/index.md")
INDEX_REL = "docs/adr/index.md"
INDEX_SS = ".slice-system/docs/adr/index.md"

WRITE_BLOCK_MSG = "REVERSIBILITY GUARD: ADRs are append-only"
EDIT_BLOCK_MSG = "REVERSIBILITY GUARD: ADR body is append-only"
ENV_BLOCK_MSG = "REVERSIBILITY GUARD: blocked write to env file"
LOCK_BLOCK_MSG = "REVERSIBILITY GUARD: lock files are auto-generated"
JQ_MISSING_MSG = "jq not found in PATH"
EDITORIAL_LOG = ".claude/adr-editorial-fixes.log"

FRONTMATTER_PREFIXES = ["status:", "firmness:", "superseded-by:", "superseded_by:"]

FLAT_BODY_OLD = "This ADR introduces a two-field identity model"
FLAT_BODY_NEW = "BYPASS"
LEGACY_BODY_OLD = "Every piece of work decomposes into a feature"
LEGACY_BODY_NEW = "BYPASS"


def _run_hook(
    tool_name: str,
    tool_input: dict,
    *,
    env_override: dict | None = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    env = os.environ.copy()
    if env_override is not None:
        for key, value in env_override.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return subprocess.run(
        ["bash", str(REVERSIBILITY_GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=cwd if cwd is not None else str(CAIRN_ROOT),
        env=env,
    )


# ---------------------------------------------------------------------------
# V1 — Bare-relative flat-slug ADR bypass closes
# ---------------------------------------------------------------------------


class TestV1BareRelativeFlatSlugBlocked:
    """RED: bare-relative `docs/adr/<flat-slug>.md` must deny Write + body Edit."""

    def test_write_bare_relative_flat_slug_blocked(self):
        result = _run_hook(
            "Write",
            {"file_path": FLAT_SLUG_REL, "content": "overwrite"},
        )
        assert result.returncode == 2, (
            f"bypass still open: Write bare-relative flat-slug ADR returned "
            f"exit {result.returncode} (expected 2); stdout={result.stdout!r}"
        )
        assert WRITE_BLOCK_MSG in result.stdout, (
            f"expected '{WRITE_BLOCK_MSG}' in stdout deny JSON, got {result.stdout!r}"
        )

    def test_edit_body_bare_relative_flat_slug_blocked(self):
        result = _run_hook(
            "Edit",
            {
                "file_path": FLAT_SLUG_REL,
                "old_string": FLAT_BODY_OLD,
                "new_string": FLAT_BODY_NEW,
            },
        )
        assert result.returncode == 2, (
            f"bypass still open: Edit body bare-relative flat-slug ADR returned "
            f"exit {result.returncode} (expected 2); stdout={result.stdout!r}"
        )
        assert EDIT_BLOCK_MSG in result.stdout, (
            f"expected '{EDIT_BLOCK_MSG}' in stdout deny JSON, got {result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V2 — Bare-relative legacy-shape ADR bypass closes
# ---------------------------------------------------------------------------


class TestV2BareRelativeLegacyBlocked:
    """RED: bare-relative `docs/adr/NNN-<slug>.md` must deny Write + body Edit."""

    def test_write_bare_relative_legacy_blocked(self):
        result = _run_hook(
            "Write",
            {"file_path": LEGACY_REL, "content": "overwrite"},
        )
        assert result.returncode == 2, (
            f"bypass still open: Write bare-relative legacy ADR returned "
            f"exit {result.returncode} (expected 2); stdout={result.stdout!r}"
        )
        assert WRITE_BLOCK_MSG in result.stdout, (
            f"expected '{WRITE_BLOCK_MSG}' in stdout deny JSON, got {result.stdout!r}"
        )

    def test_edit_body_bare_relative_legacy_blocked(self):
        result = _run_hook(
            "Edit",
            {
                "file_path": LEGACY_REL,
                "old_string": LEGACY_BODY_OLD,
                "new_string": LEGACY_BODY_NEW,
            },
        )
        assert result.returncode == 2, (
            f"bypass still open: Edit body bare-relative legacy ADR returned "
            f"exit {result.returncode} (expected 2); stdout={result.stdout!r}"
        )
        assert EDIT_BLOCK_MSG in result.stdout, (
            f"expected '{EDIT_BLOCK_MSG}' in stdout deny JSON, got {result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V3 — `.slice-system/`-prefixed shapes deny (regression guard)
# ---------------------------------------------------------------------------


class TestV3SliceSystemPrefixedDeniesConsistently:
    """GREEN: `.slice-system/` symlink-shape must continue to deny."""

    @pytest.mark.parametrize(
        "path, expected_msg",
        [
            (FLAT_SLUG_SS, WRITE_BLOCK_MSG),
            (LEGACY_SS, WRITE_BLOCK_MSG),
        ],
        ids=["flat_slug", "legacy"],
    )
    def test_write_slice_system_prefixed_blocked(self, path, expected_msg):
        result = _run_hook(
            "Write",
            {"file_path": path, "content": "overwrite"},
        )
        assert result.returncode == 2, (
            f"Write {path} returned exit {result.returncode} (expected 2); "
            f"stdout={result.stdout!r}"
        )
        assert expected_msg in result.stdout

    def test_edit_body_slice_system_flat_slug_blocked(self):
        result = _run_hook(
            "Edit",
            {
                "file_path": FLAT_SLUG_SS,
                "old_string": FLAT_BODY_OLD,
                "new_string": FLAT_BODY_NEW,
            },
        )
        assert result.returncode == 2, (
            f"Edit body {FLAT_SLUG_SS} returned exit {result.returncode} "
            f"(expected 2); stdout={result.stdout!r}"
        )
        assert EDIT_BLOCK_MSG in result.stdout


# ---------------------------------------------------------------------------
# V4 — Frontmatter-only Edit allowed on every input shape (regression guard)
# ---------------------------------------------------------------------------


FRONTMATTER_PATHS = [
    pytest.param(FLAT_SLUG_ABS, id="flat_abs"),
    pytest.param(FLAT_SLUG_REL, id="flat_rel"),
    pytest.param(FLAT_SLUG_SS, id="flat_ss"),
    pytest.param(LEGACY_ABS, id="legacy_abs"),
    pytest.param(LEGACY_REL, id="legacy_rel"),
    pytest.param(LEGACY_SS, id="legacy_ss"),
]


class TestV4FrontmatterEditAllowedAllShapes:
    """GREEN: frontmatter-prefixed old_string must allow Edit on every shape."""

    @pytest.mark.parametrize("prefix", FRONTMATTER_PREFIXES)
    @pytest.mark.parametrize("path", FRONTMATTER_PATHS)
    def test_frontmatter_edit_allowed(self, path, prefix):
        result = _run_hook(
            "Edit",
            {
                "file_path": path,
                "old_string": f"{prefix} accepted",
                "new_string": f"{prefix} draft",
            },
        )
        assert result.returncode == 0, (
            f"frontmatter Edit ('{prefix}') on {path} blocked: "
            f"exit={result.returncode}, stdout={result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V5 — New-ADR Write allowed on every input shape (regression guard)
# ---------------------------------------------------------------------------


NEW_ADR_PATHS = [
    pytest.param(NEW_FLAT_ABS, id="flat_abs"),
    pytest.param(NEW_FLAT_REL, id="flat_rel"),
    pytest.param(NEW_FLAT_SS, id="flat_ss"),
    pytest.param(NEW_LEGACY_ABS, id="legacy_abs"),
    pytest.param(NEW_LEGACY_REL, id="legacy_rel"),
    pytest.param(NEW_LEGACY_SS, id="legacy_ss"),
]


class TestV5NewAdrWriteAllowedAllShapes:
    """GREEN: Write to non-existent ADR must pass through on every shape."""

    @pytest.mark.parametrize("path", NEW_ADR_PATHS)
    def test_write_new_adr_allowed(self, path):
        result = _run_hook(
            "Write",
            {"file_path": path, "content": "---\nid: future\n---\n"},
        )
        assert result.returncode == 0, (
            f"Write new ADR {path} blocked: "
            f"exit={result.returncode}, stdout={result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V6 — index.md exempt on every input shape (regression guard)
# ---------------------------------------------------------------------------


INDEX_PATHS = [
    pytest.param(INDEX_ABS, id="abs"),
    pytest.param(INDEX_REL, id="rel"),
    pytest.param(INDEX_SS, id="ss"),
]


class TestV6IndexExemptAllShapes:
    """GREEN: docs/adr/index.md must remain exempt on every shape."""

    @pytest.mark.parametrize("path", INDEX_PATHS)
    def test_write_index_not_blocked(self, path):
        result = _run_hook(
            "Write",
            {"file_path": path, "content": "regenerated index"},
        )
        assert result.returncode == 0, (
            f"Write to index at {path} blocked: "
            f"exit={result.returncode}, stdout={result.stdout!r}"
        )

    @pytest.mark.parametrize("path", INDEX_PATHS)
    def test_edit_index_not_blocked(self, path):
        result = _run_hook(
            "Edit",
            {
                "file_path": path,
                "old_string": "old content",
                "new_string": "new content",
            },
        )
        assert result.returncode == 0, (
            f"Edit on index at {path} blocked: "
            f"exit={result.returncode}, stdout={result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V7 — Editorial-fix escape hatch covers canonical forms
# ---------------------------------------------------------------------------


class TestV7EditorialFixCoversCanonicalForms:
    """Mixed: bare-relative log assertion RED; `.slice-system/` GREEN."""

    def _edit_with_editorial_fix(self, path: str):
        return _run_hook(
            "Edit",
            {
                "file_path": path,
                "old_string": FLAT_BODY_OLD,
                "new_string": f"{FLAT_BODY_OLD} (typo fix)",
            },
            env_override={"ADR_EDITORIAL_FIX": "1"},
        )

    def _snapshot_and_run(
        self, path: str
    ) -> tuple[subprocess.CompletedProcess, list[str]]:
        log_path = CAIRN_ROOT / EDITORIAL_LOG
        before = log_path.read_text().splitlines() if log_path.exists() else []
        result = self._edit_with_editorial_fix(path)
        after = log_path.read_text().splitlines() if log_path.exists() else []
        return result, after[len(before) :]

    def test_bare_relative_editorial_fix_exits_0(self):
        result, _ = self._snapshot_and_run(FLAT_SLUG_REL)
        assert result.returncode == 0, (
            f"ADR_EDITORIAL_FIX body Edit on bare-relative flat-slug "
            f"returned exit {result.returncode}; stdout={result.stdout!r}"
        )

    def test_bare_relative_editorial_fix_logs_bypass(self):
        """RED: today the pattern misses bare-relative entirely — no log line."""
        _, new_lines = self._snapshot_and_run(FLAT_SLUG_REL)
        assert any("identifier-scheme" in line for line in new_lines), (
            f"no log entry referencing identifier-scheme after bare-relative "
            f"editorial-fix Edit; new_lines={new_lines!r}"
        )

    def test_slice_system_editorial_fix_exits_0(self):
        result, _ = self._snapshot_and_run(FLAT_SLUG_SS)
        assert result.returncode == 0, (
            f"ADR_EDITORIAL_FIX body Edit on .slice-system/ flat-slug "
            f"returned exit {result.returncode}; stdout={result.stdout!r}"
        )

    def test_slice_system_editorial_fix_logs_bypass(self):
        _, new_lines = self._snapshot_and_run(FLAT_SLUG_SS)
        assert any("identifier-scheme" in line for line in new_lines), (
            f"no log entry referencing identifier-scheme after .slice-system/ "
            f"editorial-fix Edit; new_lines={new_lines!r}"
        )


# ---------------------------------------------------------------------------
# V8 — `.env` and lockfile denies unchanged (regression guard)
# ---------------------------------------------------------------------------


class TestV8EnvAndLockfileRegressions:
    """GREEN: env/lockfile patterns already match bare-relative; must stay so."""

    @pytest.mark.parametrize(
        "path",
        [".env", ".env.local", str(CAIRN_ROOT / ".env")],
        ids=["bare_env", "bare_env_local", "abs_env"],
    )
    def test_env_write_blocked(self, path):
        result = _run_hook(
            "Write",
            {"file_path": path, "content": "SECRET=shh"},
        )
        assert result.returncode == 2, (
            f"env Write {path} not blocked: exit={result.returncode}, "
            f"stdout={result.stdout!r}"
        )
        assert ENV_BLOCK_MSG in result.stdout

    @pytest.mark.parametrize(
        "path",
        [
            "uv.lock",
            "package-lock.json",
            "poetry.lock",
            str(CAIRN_ROOT / "uv.lock"),
        ],
        ids=["bare_uv", "bare_npm", "bare_poetry", "abs_uv"],
    )
    def test_lockfile_write_blocked(self, path):
        result = _run_hook(
            "Write",
            {"file_path": path, "content": "regenerated"},
        )
        assert result.returncode == 2, (
            f"lockfile Write {path} not blocked: exit={result.returncode}, "
            f"stdout={result.stdout!r}"
        )
        assert LOCK_BLOCK_MSG in result.stdout


# ---------------------------------------------------------------------------
# V10 — Missing jq contract (regression guard; conditional skip)
# ---------------------------------------------------------------------------


class TestV10MissingJqContract:
    """GREEN: hook exits 0 with stderr warning when jq is missing."""

    def test_missing_jq_returns_exit_0_with_warning(self):
        minimal_path = "/usr/bin:/bin"
        probe = subprocess.run(
            ["bash", "-c", "command -v jq || true"],
            env={"PATH": minimal_path},
            capture_output=True,
            text=True,
            timeout=5,
        )
        if probe.stdout.strip():
            pytest.skip(
                "jq is reachable via a minimal PATH in this environment — "
                "cannot strip cleanly to exercise the missing-jq contract"
            )

        result = _run_hook(
            "Write",
            {"file_path": FLAT_SLUG_REL, "content": "x"},
            env_override={"PATH": minimal_path},
        )
        assert result.returncode == 0, (
            f"missing-jq path returned exit {result.returncode} "
            f"(expected 0); stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert JQ_MISSING_MSG in result.stderr, (
            f"expected '{JQ_MISSING_MSG}' in stderr, got {result.stderr!r}"
        )


# ---------------------------------------------------------------------------
# V11 — No-crash contract under indeterminate project root
# ---------------------------------------------------------------------------


class TestV11NoCrashUnderIndeterminateProjectRoot:
    """GREEN: hook terminates cleanly with CLAUDE_PROJECT_DIR unset + no git."""

    def test_hook_does_not_crash_outside_git_repo(self, tmp_path):
        result = _run_hook(
            "Write",
            {"file_path": FLAT_SLUG_REL, "content": "x"},
            env_override={"CLAUDE_PROJECT_DIR": None},
            cwd=str(tmp_path),
        )
        assert result.returncode in (0, 2), (
            f"hook crashed under indeterminate project root: "
            f"exit={result.returncode}, stderr={result.stderr!r}"
        )
        assert "Traceback" not in result.stderr, (
            f"Python-style traceback surfaced on stderr: {result.stderr!r}"
        )
        # Detect bash error prefix (`reversibility-guard.sh: line N: ...`) while
        # letting the legitimate jq-missing warning through.
        for line in result.stderr.splitlines():
            if JQ_MISSING_MSG in line:
                continue
            assert "reversibility-guard.sh: line" not in line, (
                f"bash error surfaced on stderr under set -euo pipefail: "
                f"{result.stderr!r}"
            )


# ---------------------------------------------------------------------------
# V12 — Verdict symmetry across input shapes
# ---------------------------------------------------------------------------


def _build_scenarios():
    shapes = {
        "absolute": FLAT_SLUG_ABS,
        "bare_relative": FLAT_SLUG_REL,
        "slice_system": FLAT_SLUG_SS,
    }
    # Factory returns (tool_name, tool_input, env_override) for a given file_path.
    scenarios = [
        (
            "write_existing",
            lambda fp: (
                "Write",
                {"file_path": fp, "content": "overwrite"},
                None,
            ),
        ),
        (
            "edit_frontmatter",
            lambda fp: (
                "Edit",
                {
                    "file_path": fp,
                    "old_string": "status: accepted",
                    "new_string": "status: draft",
                },
                None,
            ),
        ),
        (
            "edit_body",
            lambda fp: (
                "Edit",
                {
                    "file_path": fp,
                    "old_string": FLAT_BODY_OLD,
                    "new_string": FLAT_BODY_NEW,
                },
                None,
            ),
        ),
        (
            "edit_body_editorial",
            lambda fp: (
                "Edit",
                {
                    "file_path": fp,
                    "old_string": FLAT_BODY_OLD,
                    "new_string": f"{FLAT_BODY_OLD} (typo fix)",
                },
                {"ADR_EDITORIAL_FIX": "1"},
            ),
        ),
        (
            "write_non_existent",
            lambda fp: (
                "Write",
                {
                    "file_path": fp.replace("identifier-scheme", "future-unused"),
                    "content": "---\nid: future\n---\n",
                },
                None,
            ),
        ),
    ]
    return shapes, scenarios


class TestV12VerdictSymmetry:
    """RED: exit code must be identical across three shapes per scenario."""

    @pytest.mark.parametrize(
        "scenario_id, factory",
        _build_scenarios()[1],
        ids=[s[0] for s in _build_scenarios()[1]],
    )
    def test_exit_code_identical_across_shapes(self, scenario_id, factory):
        shapes, _ = _build_scenarios()
        exit_codes = {}
        for shape_id, file_path in shapes.items():
            tool_name, tool_input, env_override = factory(file_path)
            result = _run_hook(tool_name, tool_input, env_override=env_override)
            exit_codes[shape_id] = result.returncode

        distinct = set(exit_codes.values())
        assert len(distinct) == 1, (
            f"scenario {scenario_id}: exit codes diverge across input shapes: "
            f"{exit_codes} (all three must match for verdict symmetry)"
        )

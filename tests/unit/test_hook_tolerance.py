"""Phase 2 validation tests for SLICE-016 — hook tolerance for flat-slug ADRs.

Verifies intent.md V1–V6 against reversibility-guard.sh, scope-guard.sh, and
reality-check.sh. Tests invoke hooks via subprocess with synthesized JSON payloads.

Hook interface: JSON on stdin with tool_name + tool_input. Exit 0 = allow,
exit 2 = deny (with JSON deny reason on stdout).

reversibility-guard.sh uses case patterns like */docs/adr/[0-9]* — the leading
*/ requires a path prefix, so all reversibility-guard payloads use absolute paths
(matching what the Claude Code harness actually sends).

RED tests (fail until Phase 3 widens the reversibility-guard glob):
  V1  — Write to existing flat-slug ADR blocked (exit 2)
  V3p — Edit body prose on flat-slug ADR blocked (exit 2)
  V4p — Editorial-fix bypass on flat-slug ADR logs entry

GREEN regression tests (pass on current code, must not regress):
  V2  — Write to existing legacy ADR still blocked
  V3r — Frontmatter Edit on both forms allowed; body Edit on legacy blocked
  V4r — Editorial-fix bypass on legacy ADR exits 0
  V5  — Write to non-existent ADR allowed for both shapes
  V6  — Scope-guard and reality-check coexist with flat-slug filenames

FAILS until Phase 3 modifies reversibility-guard.sh.
Pytest + stdlib only.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
REVERSIBILITY_GUARD = CAIRN_ROOT / "checks" / "reversibility-guard.sh"
SCOPE_GUARD = CAIRN_ROOT / "checks" / "scope-guard.sh"
REALITY_CHECK = CAIRN_ROOT / "checks" / "reality-check.sh"

FLAT_SLUG_ADR = str(CAIRN_ROOT / "docs/adr/identifier-scheme.md")
LEGACY_ADR = str(CAIRN_ROOT / "docs/adr/006-feature-slice-model.md")
NEW_FLAT_SLUG_ADR = str(CAIRN_ROOT / "docs/adr/future-flat-slug.md")
NEW_LEGACY_ADR = str(CAIRN_ROOT / "docs/adr/100-future-slug.md")
INDEX_FILE = str(CAIRN_ROOT / "docs/adr/index.md")

FLAT_SLUG_ADR_REL = "docs/adr/identifier-scheme.md"

WRITE_BLOCK_MSG = "REVERSIBILITY GUARD: ADRs are append-only"
EDIT_BLOCK_MSG = "REVERSIBILITY GUARD: ADR body is append-only"
EDITORIAL_LOG = ".claude/adr-editorial-fixes.log"


def _run_hook(
    hook: Path,
    tool_name: str,
    tool_input: dict,
    *,
    env_override: dict | None = None,
) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", str(hook)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(CAIRN_ROOT),
        env=env,
    )


def _run_reversibility_guard(
    tool_name: str, tool_input: dict, *, env_override: dict | None = None
) -> subprocess.CompletedProcess:
    return _run_hook(
        REVERSIBILITY_GUARD, tool_name, tool_input, env_override=env_override
    )


# ---------------------------------------------------------------------------
# V1 — Bootstrap-window gap closes (flat-slug Write blocked)
# ---------------------------------------------------------------------------


class TestV1BootstrapWindowGapCloses:
    """RED: reversibility-guard must block Write to existing flat-slug ADRs."""

    def test_write_existing_flat_slug_adr_blocked(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": FLAT_SLUG_ADR, "content": "overwrite attempt"},
        )
        assert result.returncode == 2, (
            f"Write to existing flat-slug ADR was not blocked "
            f"(exit {result.returncode}, expected 2)"
        )

    def test_write_block_emits_append_only_message(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": FLAT_SLUG_ADR, "content": "overwrite attempt"},
        )
        assert WRITE_BLOCK_MSG in result.stdout, (
            f"Expected '{WRITE_BLOCK_MSG}' in stdout deny JSON, "
            f"got stdout={result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V2 — Legacy ADR protection unchanged
# ---------------------------------------------------------------------------


class TestV2LegacyAdrProtectionUnchanged:
    """GREEN: Write to existing legacy ADR still blocked."""

    def test_write_existing_legacy_adr_blocked(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": LEGACY_ADR, "content": "overwrite attempt"},
        )
        assert result.returncode == 2, (
            f"Write to existing legacy ADR was not blocked "
            f"(exit {result.returncode}, expected 2)"
        )

    def test_write_block_message_matches(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": LEGACY_ADR, "content": "overwrite attempt"},
        )
        assert WRITE_BLOCK_MSG in result.stdout, (
            f"Expected '{WRITE_BLOCK_MSG}' in stdout deny JSON for legacy ADR, "
            f"got stdout={result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# V3 — Frontmatter-only Edit permitted on both forms
# ---------------------------------------------------------------------------


class TestV3FrontmatterEditBothForms:
    """Mixed RED/GREEN: frontmatter Edit allowed; body Edit blocked on both."""

    @pytest.mark.parametrize(
        "prefix",
        ["status:", "firmness:", "superseded-by:", "superseded_by:"],
        ids=["status", "firmness", "superseded-by", "superseded_by"],
    )
    def test_edit_frontmatter_flat_slug_allowed(self, prefix):
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR,
                "old_string": f"{prefix} accepted",
                "new_string": f"{prefix} draft",
            },
        )
        assert result.returncode == 0, (
            f"Frontmatter Edit ('{prefix}') on flat-slug ADR was blocked: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    @pytest.mark.parametrize(
        "prefix",
        ["status:", "firmness:", "superseded-by:", "superseded_by:"],
        ids=["status", "firmness", "superseded-by", "superseded_by"],
    )
    def test_edit_frontmatter_legacy_allowed(self, prefix):
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": LEGACY_ADR,
                "old_string": f"{prefix} accepted",
                "new_string": f"{prefix} draft",
            },
        )
        assert result.returncode == 0, (
            f"Frontmatter Edit ('{prefix}') on legacy ADR was blocked: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    def test_edit_body_flat_slug_blocked(self):
        """RED: body prose Edit on flat-slug ADR must be blocked."""
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR,
                "old_string": "This ADR introduces a two-field identity model",
                "new_string": "This ADR removes the identity model",
            },
        )
        assert result.returncode == 2, (
            f"Body prose Edit on flat-slug ADR was not blocked "
            f"(exit {result.returncode}, expected 2)"
        )

    def test_edit_body_flat_slug_emits_message(self):
        """RED: body Edit block must emit the deny reason."""
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR,
                "old_string": "This ADR introduces a two-field identity model",
                "new_string": "This ADR removes the identity model",
            },
        )
        assert EDIT_BLOCK_MSG in result.stdout, (
            f"Expected '{EDIT_BLOCK_MSG}' in stdout deny JSON, "
            f"got stdout={result.stdout!r}"
        )

    def test_edit_body_legacy_blocked(self):
        """GREEN: body prose Edit on legacy ADR already blocked."""
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": LEGACY_ADR,
                "old_string": "Every piece of work decomposes into a feature",
                "new_string": "Work does not decompose",
            },
        )
        assert result.returncode == 2, (
            f"Body prose Edit on legacy ADR was not blocked "
            f"(exit {result.returncode}, expected 2)"
        )


# ---------------------------------------------------------------------------
# V4 — ADR_EDITORIAL_FIX=1 escape hatch operates on both forms
# ---------------------------------------------------------------------------


class TestV4EditorialFixEscapeHatch:
    """RED (flat-slug log) / GREEN (legacy): editorial bypass allows body Edits."""

    def test_editorial_fix_flat_slug_body_edit_allowed(self):
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR,
                "old_string": "This ADR introduces a two-field identity model",
                "new_string": "This ADR introduces a two-field identity model (typo fix)",
            },
            env_override={"ADR_EDITORIAL_FIX": "1"},
        )
        assert result.returncode == 0, (
            f"Editorial fix bypass did not allow body Edit on flat-slug ADR: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    def test_editorial_fix_legacy_body_edit_allowed(self):
        """GREEN: bypass already works on legacy ADRs."""
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": LEGACY_ADR,
                "old_string": "Every piece of work decomposes into a feature",
                "new_string": "Every piece of work decomposes into a feature (typo fix)",
            },
            env_override={"ADR_EDITORIAL_FIX": "1"},
        )
        assert result.returncode == 0, (
            f"Editorial fix bypass did not allow body Edit on legacy ADR: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    def test_editorial_fix_flat_slug_logs_bypass(self):
        """RED: bypass on flat-slug ADR must log to adr-editorial-fixes.log."""
        log_path = CAIRN_ROOT / EDITORIAL_LOG
        lines_before = log_path.read_text().splitlines() if log_path.exists() else []

        _run_reversibility_guard(
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR,
                "old_string": "This ADR introduces a two-field identity model",
                "new_string": "This ADR introduces a two-field identity model (log test)",
            },
            env_override={"ADR_EDITORIAL_FIX": "1"},
        )

        assert log_path.exists(), (
            f"Expected {EDITORIAL_LOG} to exist after editorial-fix bypass"
        )
        lines_after = log_path.read_text().splitlines()
        new_lines = lines_after[len(lines_before) :]
        assert any("identifier-scheme" in line for line in new_lines), (
            f"No log entry referencing identifier-scheme in new lines: {new_lines}"
        )


# ---------------------------------------------------------------------------
# V5 — New-ADR Write allowed for both shapes
# ---------------------------------------------------------------------------


class TestV5NewAdrWriteAllowed:
    """GREEN: Write to non-existent ADR paths passes through for both shapes."""

    def test_write_new_flat_slug_adr_allowed(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": NEW_FLAT_SLUG_ADR, "content": "---\nid: future\n---\n"},
        )
        assert result.returncode == 0, (
            f"Write to new flat-slug ADR was blocked: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    def test_write_new_legacy_adr_allowed(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": NEW_LEGACY_ADR, "content": "---\nid: ADR-100\n---\n"},
        )
        assert result.returncode == 0, (
            f"Write to new legacy ADR was blocked: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )


# ---------------------------------------------------------------------------
# V6 — Scope-guard and reality-check coexistence
# ---------------------------------------------------------------------------


class TestV6ScopeGuardCoexistence:
    """GREEN: scope-guard allows ADR file access regardless of naming shape."""

    def test_scope_guard_allows_flat_slug_adr_write(self):
        result = _run_hook(
            SCOPE_GUARD,
            "Write",
            {"file_path": FLAT_SLUG_ADR_REL, "content": "test"},
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Write to flat-slug ADR: "
            f"exit={result.returncode}, stderr={result.stderr}"
        )

    def test_scope_guard_allows_flat_slug_adr_edit(self):
        result = _run_hook(
            SCOPE_GUARD,
            "Edit",
            {
                "file_path": FLAT_SLUG_ADR_REL,
                "old_string": "old",
                "new_string": "new",
            },
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Edit on flat-slug ADR: "
            f"exit={result.returncode}, stderr={result.stderr}"
        )


class TestV6RealityCheckCoexistence:
    """GREEN: reality-check does not error on non-Python ADR files."""

    def test_reality_check_ignores_flat_slug_adr(self):
        result = _run_hook(
            REALITY_CHECK,
            "Write",
            {"file_path": FLAT_SLUG_ADR_REL, "content": "test"},
        )
        assert result.returncode == 0, (
            f"reality-check errored on flat-slug ADR file: "
            f"exit={result.returncode}, stderr={result.stderr}"
        )


# ---------------------------------------------------------------------------
# Regression — index.md must not be caught by widened pattern
# ---------------------------------------------------------------------------


class TestIndexFileNotCaught:
    """GREEN: docs/adr/index.md must remain unprotected by reversibility-guard."""

    def test_write_index_not_blocked(self):
        result = _run_reversibility_guard(
            "Write",
            {"file_path": INDEX_FILE, "content": "regenerated index"},
        )
        assert result.returncode == 0, (
            f"Write to index.md was blocked by reversibility-guard — "
            f"the widened glob must not catch non-ADR files: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

    def test_edit_index_not_blocked(self):
        result = _run_reversibility_guard(
            "Edit",
            {
                "file_path": INDEX_FILE,
                "old_string": "old content",
                "new_string": "new content",
            },
        )
        assert result.returncode == 0, (
            f"Edit on index.md was blocked by reversibility-guard: "
            f"exit={result.returncode}, stdout={result.stdout}"
        )

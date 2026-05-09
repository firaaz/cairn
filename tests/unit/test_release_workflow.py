"""RED tests for cairn-m7-plugin-deployment-pattern S3/S4 — release-publish.yml shape lint.

Pins (per intent.md §S4, ADR `m5-plugin-deployment-pattern` D5/D6/D8):

1. `.github/workflows/release-publish.yml` exists.
2. Parsed YAML's `on` mapping contains `workflow_dispatch`, and
   `on.workflow_dispatch.inputs` contains `version` (D5).
3. File text contains `--force-with-lease` AND does NOT contain the bare
   token `git push --force ` (trailing space) or `git push --force\\n`
   — the `--force-with-lease` literal must not produce a false positive
   (D6 / FLI-3).
4. File text contains `chore: release` (literal commit-message prefix;
   S5 / INV-001 binding via _FALLBACK_REGISTRY / FLI-5).

Tests MUST FAIL at HEAD with FileNotFoundError (and downstream errors)
because `.github/workflows/release-publish.yml` does not yet exist.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release-publish.yml"


def test_release_workflow_exists() -> None:
    """S4.1 / M7.2 — release-publish.yml is present at the canonical path.

    Phase 2 RED defense for M7.2 (release-publish.yml syntax error blocks
    first release): existence + YAML-parse establishes the file.
    """
    assert WORKFLOW_PATH.exists(), (
        f"release-publish.yml missing at {WORKFLOW_PATH.relative_to(REPO_ROOT)}"
    )


def test_release_workflow_has_workflow_dispatch_with_version_input() -> None:
    """S4.2 / ADR D5 — `workflow_dispatch` trigger with required `version` input.

    The workflow must be operator-triggerable via the GitHub Actions UI
    (audit check 9 prerequisite), and must accept a `version` input that
    is cross-checked against the built `plugin.json:version` before any
    push (FLI-2).
    """
    parsed = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on:` as Python True (YAML 1.1 boolean);
    # tolerate either spelling so the assertion targets the semantic shape.
    on_block = parsed.get("on") if "on" in parsed else parsed.get(True)
    assert on_block is not None, "workflow must declare an `on:` trigger block"
    assert "workflow_dispatch" in on_block, (
        "workflow_dispatch must be declared as a trigger (D5)"
    )
    inputs = on_block["workflow_dispatch"].get("inputs") or {}
    assert "version" in inputs, (
        "workflow_dispatch.inputs.version is required by ADR D5 cross-check"
    )


def test_release_workflow_uses_force_with_lease_only() -> None:
    """S4.3 / ADR D6 / FLI-3 — `--force-with-lease` only; no bare `git push --force`.

    Cairn's force-push policy applies to CI as well as humans
    (CLAUDE.md "Force-push policy"). The `--force-with-lease` literal
    must not produce a false positive on the bare-force scan: we
    explicitly reject the `git push --force ` (trailing space) and
    `git push --force\\n` (trailing newline) tokens only.
    """
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "--force-with-lease" in text, (
        "release-publish.yml must use `git push --force-with-lease` (D6)"
    )
    # FLI-3: bare `git push --force` (with trailing space OR newline) is forbidden.
    assert "git push --force " not in text, (
        "bare `git push --force ` (trailing space) is forbidden by FLI-3"
    )
    assert "git push --force\n" not in text, (
        "bare `git push --force\\n` (trailing newline) is forbidden by FLI-3"
    )


def test_release_workflow_commit_prefix_is_chore() -> None:
    """S4.4 / S5 / INV-001 / FLI-5 — release commit uses `chore: release ` prefix.

    `chore` is in `_FALLBACK_REGISTRY` at scripts/validate_architecture.py:279;
    using any other prefix breaks the INV-001 commit-prefix binding when
    the release commit later flows back into the validator's git-log walk.
    """
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "chore: release" in text, (
        "release-sync commit message must begin with `chore: release ` "
        "(S5 / INV-001 _FALLBACK_REGISTRY binding / FLI-5)"
    )

"""RED gate tests for slice `compression/lever-2-orchestrator-split`.

Encodes V2-V6 from `.claude/current-slice/intent.md` (Phase-1 contract). These
tests MUST fail RED today (pre-split) and pass GREEN after Phase 3 lands the
package split. The Skeptic does not read source; gates are written against the
intent.md contract alone.

Gate map:
- V2  test_v2_public_surface_reexport            -> §S3 + intent.md:81-90, 133
- V3a test_v3_cli_dash_m_legacy_exits_zero       -> intent.md:94-97, 135
- V3b test_v3_cli_main_path_legacy_exits_zero    -> intent.md:94-97, 135
- V3c test_v3_cli_brief_argparse_no_error        -> intent.md:94-97, 135
- V4  test_v4_filesystem_shape                   -> intent.md:137
- V5  test_v5_architecture_validator_post_split  -> intent.md:139 (inverted; see
      docstring on that test)
- V6  test_v6_path_string_sweep                  -> intent.md:141

Anti-behavior compliance:
- No source-file reads of `scripts/slice_orchestrator.py` or the unborn
  package; the public-surface list is iterated verbatim from §S3.
- `slice_orchestrator.<name>` resolution only (per §S3 drift clause,
  intent.md:79); no submodule-pathed assertions.
- ADRs are exempt from V6 (intent.md:141); `docs/adr/` is NOT in the grep target
  list.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Repo-root resolution: this test file lives at
# `<repo>/tests/unit/test_slice_orchestrator_package_split.py`. Two parents up
# from `tests/unit/` is the repo root.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "slice_orchestrator"
LEGACY_FILE = SCRIPTS_DIR / "slice_orchestrator.py"


def _subprocess_env() -> dict[str, str]:
    """Return env with `scripts/` on PYTHONPATH so `import slice_orchestrator`
    works from a child process. Mirrors the `[tool.pytest.ini_options]
    pythonpath = ["scripts"]` setting in pyproject.toml.
    """
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    pieces = [str(SCRIPTS_DIR)]
    if existing:
        pieces.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pieces)
    return env


# ---------------------------------------------------------------------------
# §S3 public surface (intent.md:83-90). The PRICING_TABLE_<date> set is
# operator-dismissed for enumeration (Phase-2 brief OQ resolution): we test
# the lexical pattern instead — at least one `PRICING_TABLE_` prefixed
# attribute must exist on the package facade.
# ---------------------------------------------------------------------------

# Top-level public defs/classes (intent.md:84):
S3_PUBLIC_DEFS = [
    "is_valid_slice_id",
    "read_slice_state",
    "dispatch_phase_agent",
    "dispatch_triager",
    "dispatch_phase_3",
    "detect_superseded_test_signal",
    "commit_phase_handoff",
    "run_phase_loop",
    "init_new_slice",
    "close_slice",
    "legacy_start_slice",
    "main",
    "_HeartbeatDaemon",
]

# Module constants (intent.md:87):
S3_CONSTANTS = [
    "AGENT_MODEL_CONFIG",
    "INV_009_COST_THRESHOLD_USD",
    "INV_009_TOKEN_THRESHOLD",
    "ROLE_FOR_PHASE",
    "ROLE_TO_PHASE",
    "DEBUG_DIR",
    "DEFAULT_TIMEOUT_HARD",
    "PERMISSION_MODE",
    "VALID_TRIAGER_ACTIONS",
    "SLICE_ID_REGEX",
]

# Underscore helpers (intent.md:90 — the audit-by-grep set):
S3_UNDERSCORE_HELPERS = [
    "_resolve_model_config",
    "_classify_failure",
    "_parse_structured_tail",
    "_parse_usage_envelope",
    "_extract_agent_result_text",
    "_extract_envelope_model",
    "_cost_for_tokens",
    "_record_phase_cost",
    "_active_pricing_table",
    "_active_pricing_table_name",
    "_resolve_timeout",
    "_normalize_slice_id",
    "_slice_id_slug",
    "_utc_timestamp",
    "_iso_now",
    "_init_state_dict",
    "_default_observability_errors",
    "_update_state",
    "_observability_paths",
    "_atomic_write",
    "_persist_state",
    "_generate_result_md",
    "_write_result_md",
    "_append_index_entry",
    "_start_heartbeat",
    "_check_heartbeat_alive",
    "_handle_heartbeat_death",
    "_bundle_handoff_md",
    "_wipe_current_slice",
    "_is_slice_already_closed",
    "_reconcile_resume_state",
    "_is_slice_complete_subject",
    "_head_subject_safe",
    "_refuse_resume",
    "_final_persist_and_md",
    "_register_atexit_terminal_writer",
    "_write_phase_log",
    "_git",
    "_git_head_safe",
    "_run_with_live_stderr",
    "_resolve_phase_and_slice",
    "_dispatch_once",
    "_log_retry_attempt",
    "_resolve_supersession_hint",
    "_load_clusters",
    "_parse_clusters",
    "_intent_envelope",
    "_phase3_dispatch_with_log",
    "_write_cluster_log",
    "_dispatch_for_phase",
    "_current_phase",
    "_persist_current_phase",
    "_persist_redispatch",
    "_clean_shutdown",
    "_register_signal_handlers",
    "_slice_id",
    "_slice_brief",
    "_abort_slice",
    "_read_slice_state_strict",
    "_write_slice_state",
]

S3_ALL_NAMES = S3_PUBLIC_DEFS + S3_CONSTANTS + S3_UNDERSCORE_HELPERS


# ===========================================================================
# V2 — Public-surface re-export
# ===========================================================================


@pytest.mark.parametrize("name", S3_ALL_NAMES)
def test_v2_public_surface_reexport(name: str) -> None:
    """V2 (intent.md:133): every §S3 name resolves as `slice_orchestrator.<name>`.

    Per §S3 drift clause (intent.md:79), Phase 3 may relocate helpers between
    submodules — the public-surface contract is the package facade
    (`__init__.py` re-exports), NOT the internal submodule layout. This test
    asserts top-level resolution only, never `slice_orchestrator.<sub>.<name>`.

    Pre-split state: PASSES today because the single-file
    `scripts/slice_orchestrator.py` defines all these names directly. The gate
    encodes the post-split contract that the names remain reachable through
    `import slice_orchestrator as so; so.<name>` AFTER the file is replaced by
    a package directory whose `__init__.py` does the re-exports. In Phase 3,
    if `__init__.py` forgets to re-export any name, this test FAILS RED. To
    make this test fail RED today, we additionally assert that the
    facade is a package (i.e. has `__path__`) — which it is NOT pre-split.
    """
    # Force-reload to defeat module cache between tests if any prior test
    # imported slice_orchestrator.
    if "slice_orchestrator" in sys.modules:
        importlib.reload(sys.modules["slice_orchestrator"])
    so = importlib.import_module("slice_orchestrator")

    # Inversion clause: pre-split, `slice_orchestrator` is a single-file
    # module and has no `__path__` attribute. Post-split, it MUST be a
    # package (intent.md S1) and therefore have `__path__`. This makes the
    # test RED today regardless of name resolution.
    assert hasattr(so, "__path__"), (
        "slice_orchestrator must be a package (have __path__) post-split; "
        "pre-split it is a single-file module."
    )

    # The actual public-surface contract (S3):
    assert hasattr(so, name), (
        f"slice_orchestrator.{name} must be reachable via the package facade "
        f"(intent.md §S3); missing means __init__.py forgot to re-export it "
        f"or the symbol was deliberately retired without rationale "
        f"(implementation/notes.md)."
    )
    value = getattr(so, name)
    # INV-009 thresholds are deliberately ``None`` at introduction (intent §S7,
    # docs/adr/cost-per-slice-budget.md, and tests/unit/test_slice_orchestrator_cost.py
    # ``test_inv_009_thresholds_default_to_none``). For these two names the
    # reachability check above is sufficient — getattr returning the literal
    # ``None`` proves the re-export points at the actual definition.
    if name not in ("INV_009_COST_THRESHOLD_USD", "INV_009_TOKEN_THRESHOLD"):
        assert value is not None, (
            f"slice_orchestrator.{name} resolved but is None — re-export must "
            f"point at the actual definition."
        )


def test_v2_pricing_table_lexical_pattern() -> None:
    """V2 lexical pattern (intent.md:87 — operator-dismissed for enumeration,
    optional pattern check accepted).

    At least one attribute matching `^PRICING_TABLE_\\d{4}_\\d{2}_\\d{2}$` must
    be reachable through `slice_orchestrator.<name>` so the dated-pricing-table
    convention (docs/operational-reference.md:339) survives the split. Phase 3
    must re-export every dated PRICING_TABLE_ constant currently present.
    """
    if "slice_orchestrator" in sys.modules:
        importlib.reload(sys.modules["slice_orchestrator"])
    so = importlib.import_module("slice_orchestrator")

    # Inversion clause (mirrors test_v2_public_surface_reexport): forces RED
    # today because slice_orchestrator is a file-module pre-split.
    assert hasattr(so, "__path__"), (
        "slice_orchestrator must be a package post-split; pre-split it is a "
        "single-file module without __path__."
    )

    pat = re.compile(r"^PRICING_TABLE_\d{4}_\d{2}_\d{2}$")
    matches = [n for n in dir(so) if pat.match(n)]
    assert matches, (
        "slice_orchestrator must expose at least one "
        "PRICING_TABLE_<YYYY>_<MM>_<DD> constant (intent.md:87)."
    )


# ===========================================================================
# V3 — CLI invocation parity
# ===========================================================================


def test_v3_cli_dash_m_legacy_exits_zero() -> None:
    """V3 form 1 (intent.md:96, 135): `python -m slice_orchestrator --legacy`
    exits 0 post-split. Pre-split this form already works against the single
    file; the gate is that it CONTINUES to work after the package split makes
    the import name resolve to a directory (with `__main__.py`).
    """
    # Inversion clause: assert that the package directory is what's resolved.
    # Pre-split, `python -m slice_orchestrator` runs the file's top-level code
    # and would still exit 0 — but the gate post-split requires a
    # __main__.py file inside the package directory. We make this test RED
    # today by asserting the package's __main__.py exists at the expected
    # filesystem path BEFORE running the CLI.
    main_py = PACKAGE_DIR / "__main__.py"
    assert main_py.is_file(), (
        f"{main_py} must exist post-split (intent.md S1); pre-split it does not."
    )

    result = subprocess.run(
        [sys.executable, "-m", "slice_orchestrator", "--legacy"],
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`python -m slice_orchestrator --legacy` must exit 0 "
        f"(intent.md:96, 135). Got rc={result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_v3_cli_main_path_legacy_exits_zero() -> None:
    """V3 form 2 (intent.md:97, 135): direct path
    `python scripts/slice_orchestrator/__main__.py --legacy` exits 0.

    Pre-split this fails RED because the path does not exist (the package
    directory has not been created). Operator-resolved (OQ2): both forms MUST
    be tested.
    """
    main_py = PACKAGE_DIR / "__main__.py"
    # Pre-condition assertion (also makes the test RED on its own pre-split):
    assert main_py.is_file(), f"{main_py} must exist post-split (intent.md S1)."

    result = subprocess.run(
        [sys.executable, str(main_py), "--legacy"],
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`python {main_py} --legacy` must exit 0 (intent.md:97, 135). "
        f"Got rc={result.returncode}. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


def test_v3_cli_brief_argparse_no_error() -> None:
    """V3 arg-parse contract (intent.md:135): `--brief`, `--resume`, and
    `--legacy` flags are registered on the CLI parser and parse without
    ArgumentError.

    Dry-run strategy: invoke `python -m slice_orchestrator --help`. argparse
    always exits 0 on `--help` and dumps the flag list to stdout, allowing us
    to assert each load-bearing flag is present without spawning a real slice
    (no `git restore`/`git clean` rollback needed). Avoids leaving a transient
    slice committed.
    """
    main_py = PACKAGE_DIR / "__main__.py"
    # Inversion: forces RED pre-split.
    assert main_py.is_file(), f"{main_py} must exist post-split (intent.md S1)."

    result = subprocess.run(
        [sys.executable, "-m", "slice_orchestrator", "--help"],
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`python -m slice_orchestrator --help` must exit 0; got "
        f"rc={result.returncode}. stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    for flag in ("--brief", "--resume", "--legacy"):
        assert flag in combined, (
            f"argparse `{flag}` flag missing from --help output "
            f"(intent.md:94, 135). Output was: {combined!r}"
        )


# ===========================================================================
# V4 — Filesystem shape
# ===========================================================================


def test_v4_filesystem_shape() -> None:
    """V4 (intent.md:137): the single file is gone; the package directory
    exists with exactly the eight required files.

    Pre-split: `scripts/slice_orchestrator.py` exists and the directory does
    not — both halves of this test fail RED today.
    """
    # Half A: legacy file is deleted.
    assert not LEGACY_FILE.exists(), (
        f"{LEGACY_FILE} must NOT exist post-split (intent.md:137); the "
        f"single file is replaced by the package directory in the same "
        f"Phase 3 commit."
    )

    # Half B: package directory exists.
    assert PACKAGE_DIR.is_dir(), (
        f"{PACKAGE_DIR} must exist as a directory post-split (intent.md:137)."
    )

    # Half C: every required file exists.
    required_files = [
        "__init__.py",
        "__main__.py",
        "core.py",
        "dispatch.py",
        "lifecycle.py",
        "resume.py",
        "telemetry.py",
        "git.py",
    ]
    for fname in required_files:
        path = PACKAGE_DIR / fname
        assert path.is_file(), (
            f"{path} must exist post-split (intent.md:137 — eight files required)."
        )


# ===========================================================================
# V5 — Architecture validator
# ===========================================================================


def test_v5_architecture_validator_post_split() -> None:
    """V5 (intent.md:139): `validate_architecture.py` exits 0 post-split AND
    every `invariant-check` `target:` previously naming
    `scripts/slice_orchestrator.py` resolves to a real submodule path.

    INVERSION STRATEGY (operator-flagged in Phase-2 brief): the validator
    currently exits 0 PRE-SPLIT (verified manually: `uv run python
    .slice-system/scripts/validate_architecture.py` returns rc=0 with 9
    invariants verified, 15 ADRs checked). A naive `rc == 0` assertion would
    therefore be GREEN today — wrong-side-of-RED.

    To force RED until Phase 3 actually splits the file, we additionally
    assert that `scripts/slice_orchestrator/` is a real directory AND that
    `scripts/slice_orchestrator.py` is gone. This couples V5's pass-state to
    V4's filesystem shape: the validator must STILL exit 0 (proving
    `target:` updates in `docs/ARCHITECTURE.md` resolve), but only AFTER the
    package replaces the single file. Pre-split, the directory check fails;
    the validator's standalone exit 0 is not sufficient.
    """
    # Inversion: force RED pre-split via filesystem shape.
    assert PACKAGE_DIR.is_dir(), (
        f"{PACKAGE_DIR} must exist; V5's validator-pass requires the package "
        f"to be in place (otherwise `target:` updates in ARCHITECTURE.md "
        f"have nothing to resolve to). Pre-split, this assertion fails RED."
    )
    assert not LEGACY_FILE.exists(), (
        f"{LEGACY_FILE} must be gone for V5; ARCHITECTURE.md `target:` fields "
        f"must point at the new submodule paths (intent.md S5/V5)."
    )

    validator = REPO_ROOT / ".slice-system" / "scripts" / "validate_architecture.py"
    assert validator.is_file(), f"validator script not found at {validator}"

    result = subprocess.run(
        ["uv", "run", "python", str(validator)],
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert result.returncode == 0, (
        f"`uv run python .slice-system/scripts/validate_architecture.py` "
        f"must exit 0 post-split (intent.md:139). Got rc={result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


# ===========================================================================
# V6 — Path-string sweep
# ===========================================================================


def test_v6_path_string_sweep() -> None:
    """V6 (intent.md:141): zero literal occurrences of
    `scripts/slice_orchestrator.py` in `commands/`, `docs/ARCHITECTURE.md`,
    `docs/operational-reference.md`. ADRs (`docs/adr/**`) are EXEMPT
    (intent.md:141 — append-only historical citations).

    Pre-split this finds many hits (those strings exist by definition today
    in start-slice.md, start-slice-legacy.md, the env-var Source column, the
    pricing-table paragraph, ARCHITECTURE.md `target:` fields, etc.). The
    test fails RED until Phase 3 sweeps every in-envelope occurrence.
    """
    targets = [
        REPO_ROOT / "commands",
        REPO_ROOT / "docs" / "ARCHITECTURE.md",
        REPO_ROOT / "docs" / "operational-reference.md",
    ]
    # Confirm targets exist (sanity guard against silent target loss):
    for t in targets:
        assert t.exists(), f"V6 target {t} missing — cannot perform sweep."

    cmd = ["grep", "-rn", r"scripts/slice_orchestrator\.py", *(str(t) for t in targets)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    # grep exit codes: 0 = found, 1 = no match, 2 = error. We want NO matches.
    hits = result.stdout.strip()
    assert result.returncode == 1 and not hits, (
        f"V6 path-string sweep found `scripts/slice_orchestrator.py` "
        f"references that must be updated to the new package paths "
        f"(intent.md S5/V6). ADRs are exempt; these hits live in "
        f"in-envelope files:\n{hits}"
    )

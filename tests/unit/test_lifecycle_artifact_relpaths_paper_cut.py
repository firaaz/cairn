"""Phase 2 RED — compression/lever-Z-fixup §S4.a.

Asserts that ``scripts/slice_orchestrator/lifecycle.py``'s
``_ARTIFACT_RELPATHS`` tuple has the bare ``"envelope-expansions.log"``
entry replaced by the orchestrator-bundle-actual path
``"integration/envelope-expansions.log"``.

Two-sided assertion (presence of the new path AND absence of the old) —
both forms living together would re-introduce the silent-skip pattern the
fix is intended to prevent (the existing
``_copy_artifacts_to_sweep_results`` iterates entries; a stale bare-string
entry would silently fall through to the missing-source skip path while
the new entry is also picked up, masking the divergence).

Per ``.claude/current-slice/intent.md`` §S4.a + §S5.

Imports use ``slice_orchestrator`` (not ``scripts.slice_orchestrator``)
because ``pyproject.toml [tool.pytest.ini_options]`` declares
``pythonpath = ["scripts"]``, making ``slice_orchestrator`` the
top-level package on ``sys.path``.

Expected at Phase 2 (RED): FAILS — ``_ARTIFACT_RELPATHS`` currently
contains the bare ``"envelope-expansions.log"`` entry and lacks the
``"integration/envelope-expansions.log"`` form.
"""

from __future__ import annotations


def test_s4a_relpaths_includes_integration_envelope_expansions_log():
    """intent §S4.a — `_ARTIFACT_RELPATHS` MUST include the
    `integration/envelope-expansions.log` path so the pre-wipe snapshot
    under `.claude/sweep-results/<slug>/artifacts/` carries the file from
    where the orchestrator's bundle code actually writes it.
    """
    from slice_orchestrator import lifecycle

    assert "integration/envelope-expansions.log" in lifecycle._ARTIFACT_RELPATHS, (
        "intent §S4.a — `_ARTIFACT_RELPATHS` must include "
        "'integration/envelope-expansions.log'; got "
        f"{lifecycle._ARTIFACT_RELPATHS!r}"
    )


def test_s4a_relpaths_excludes_bare_envelope_expansions_log():
    """intent §S4.a — bare `"envelope-expansions.log"` entry MUST NOT
    coexist with the integration-prefixed entry.

    intent.md §S4.a: "the bare-string variant must NOT remain — both forms
    living together would re-introduce the silent-skip pattern". This is
    the negative half of the two-sided assertion.
    """
    from slice_orchestrator import lifecycle

    assert "envelope-expansions.log" not in lifecycle._ARTIFACT_RELPATHS, (
        "intent §S4.a — bare 'envelope-expansions.log' entry MUST be "
        "removed from `_ARTIFACT_RELPATHS` so the integration-prefixed "
        "entry is the sole canonical path; got "
        f"{lifecycle._ARTIFACT_RELPATHS!r}"
    )

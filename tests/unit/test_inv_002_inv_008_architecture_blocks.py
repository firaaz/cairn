"""Phase 2 RED tests pinning the ARCHITECTURE.md INV-002 + INV-008 block flips.

Slice v1-defense-d2/inv-002-binding-implementation per ADR
``invariant-binding-strategy`` D4–D6:

  - INV-002 assertion block becomes ``type: structural-parser`` targeting
    ``.claude/handoff.md`` with ``binding-effective-from`` set to the
    placeholder pre-close (substituted post-close).
  - INV-008 assertion block becomes ``type: test-ref`` pointing at
    ``tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop``
    — the D6 piggyback that also covers INV-002 sub-clause (c).
  - Both legacy grep proxies are GONE from ARCHITECTURE.md
    (``Token budget: 150 to 400 tokens`` and ``def close_slice``).

Anti-revert guards (slice-1 ``phase_3_revert_under_red_pressure`` lesson):
the legacy-string ABSENCE assertions stop Phase 3 from silently restoring
either grep proxy when a downstream string-match test breaks. The proxy
must die for D2 to close.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = CAIRN_ROOT / "docs" / "ARCHITECTURE.md"
CLOSE_SLICE_TEST_REL = (
    "tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop"
)
CLOSE_SLICE_TEST_FILE_REL = "tests/unit/test_close_slice_hardened.py"
HANDOFF_TARGET = ".claude/handoff.md"


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)


def _block_for(inv_id: str) -> str:
    """Return the body of the ``invariant-check <inv_id>`` fenced block."""
    text = ARCHITECTURE.read_text()
    pat = re.compile(
        r"^```invariant-check\s+" + re.escape(inv_id) + r"\b(.*?)^```",
        re.DOTALL | re.MULTILINE,
    )
    m = pat.search(text)
    assert m, f"invariant-check block for {inv_id} not found in ARCHITECTURE.md"
    return m.group(1)


# === T1 — INV-002 block uses structural-parser ==============================


def test_inv_002_block_type_is_structural_parser():
    """INV-002's ``type:`` is ``structural-parser`` post-flip."""
    body = _block_for("INV-002")
    assert re.search(r"^\s*type:\s*structural-parser\b", body, re.MULTILINE), (
        "INV-002 assertion block must declare type: structural-parser. "
        "Brief: 'Flip INV-002 assertion block in docs/ARCHITECTURE.md to "
        "type: structural-parser'. Got block body:\n" + body
    )


def test_inv_002_block_targets_handoff_md():
    """INV-002's structural-parser targets ``.claude/handoff.md``."""
    body = _block_for("INV-002")
    assert HANDOFF_TARGET in body, (
        f"INV-002 block must target {HANDOFF_TARGET!r}. Got: {body!r}"
    )


def test_inv_002_block_carries_binding_effective_from():
    """INV-002 carries ``binding-effective-from`` (placeholder pre-close)."""
    body = _block_for("INV-002")
    assert re.search(r"binding-effective-from\s*:", body), (
        "INV-002 block must declare binding-effective-from "
        "(placeholder pre-close, substituted post-close per ADR D3 / "
        "INV-001 precedent fd1823e). Got body:\n" + body
    )


def test_inv_002_legacy_grep_proxy_string_is_gone():
    """Slice-1 grep proxy ``Token budget: 150 to 400 tokens`` must be gone.

    Anti-revert guard: if Phase 3 reverts to the grep proxy under RED
    pressure (slice-1 lesson ``phase_3_revert_under_red_pressure``),
    this test catches it. The proxy must die for D2 to close.
    """
    text = ARCHITECTURE.read_text()
    assert "Token budget: 150 to 400 tokens" not in text, (
        "Legacy INV-002 grep proxy 'Token budget: 150 to 400 tokens' "
        "must be removed from ARCHITECTURE.md. Brief substrate landmine "
        "#2: this string is the slice-1 revert escape hatch."
    )


# === T2 — INV-008 block flips to test-ref (D6 piggyback) ====================


def test_inv_008_block_type_is_test_ref():
    """INV-008's ``type:`` becomes ``test-ref`` (D6 piggyback)."""
    body = _block_for("INV-008")
    assert re.search(r"^\s*type:\s*test-ref\b", body, re.MULTILINE), (
        "INV-008 assertion block must declare type: test-ref per ADR D6. "
        "Got block body:\n" + body
    )


def test_inv_008_block_points_at_close_slice_hardened_test():
    """INV-008's test-ref names the close_slice_hardened test path.

    The pointer must include ``tests/unit/test_close_slice_hardened.py`` so
    the validator's ``_run_test_ref_assertion`` can resolve the file. The
    full ``::test_close_slice_twice_is_noop`` qualifier SHOULD also appear
    so the binding intent is unambiguous (per ADR D6 + slice intent).
    """
    body = _block_for("INV-008")
    assert CLOSE_SLICE_TEST_FILE_REL in body, (
        f"INV-008 block must reference {CLOSE_SLICE_TEST_FILE_REL!r}. Got body:\n{body}"
    )
    assert "test_close_slice_twice_is_noop" in body, (
        "INV-008 block must name the specific test "
        "test_close_slice_twice_is_noop per ADR D6 piggyback intent."
    )


def test_inv_008_legacy_grep_proxy_string_is_gone():
    """Slice-1 grep proxy ``def close_slice`` must be gone from INV-008 block.

    Anti-revert guard. The literal ``def close_slice`` may still appear in
    other parts of ARCHITECTURE.md (e.g. boundary prose) — this assertion
    is scoped to the INV-008 invariant-check block body.
    """
    body = _block_for("INV-008")
    assert "def close_slice" not in body, (
        "INV-008 invariant-check block must not retain the legacy "
        "grep proxy on 'def close_slice'. Brief substrate landmine #3: "
        "this string is the slice-1 revert escape hatch."
    )
    # The block must also no longer declare type: grep
    assert not re.search(r"^\s*type:\s*grep\b", body, re.MULTILINE), (
        "INV-008 must no longer declare type: grep — D6 mandates test-ref."
    )


# === T3 — Pointed-at test exists and contains the named test function =======


def test_close_slice_hardened_test_function_exists():
    """The piggyback target ``test_close_slice_twice_is_noop`` exists.

    Validator's ``_run_test_ref_assertion`` checks file existence only;
    this test extends that to function-name presence so a typo in the
    INV-008 block surfaces here (Phase 2), not at sweep.
    """
    test_file = CAIRN_ROOT / CLOSE_SLICE_TEST_FILE_REL
    assert test_file.exists(), (
        f"piggyback test file {CLOSE_SLICE_TEST_FILE_REL} missing"
    )
    src = test_file.read_text()
    assert "def test_close_slice_twice_is_noop(" in src, (
        "Function test_close_slice_twice_is_noop missing from "
        f"{CLOSE_SLICE_TEST_FILE_REL}. ADR D6 binding target broken."
    )


# === T4 — Cross-block invariants: validator self-dogfood still passes =======


def test_full_invariant_set_unchanged():
    """Block flip does not add or remove any invariant-check fences.

    INV-001..INV-010 must each still carry exactly one assertion block.
    """
    text = ARCHITECTURE.read_text()
    headers = re.findall(r"^```invariant-check\s+(INV-\d+)", text, re.MULTILINE)
    seen: dict[str, int] = {}
    for h in headers:
        seen[h] = seen.get(h, 0) + 1
    expected = {f"INV-{n:03d}" for n in range(1, 11)}
    missing = expected - set(seen.keys())
    extra = set(seen.keys()) - expected
    duplicated = {k: v for k, v in seen.items() if v > 1}
    assert not missing, f"Missing invariant-check blocks: {sorted(missing)}"
    assert not extra, f"Unexpected invariant-check blocks: {sorted(extra)}"
    assert not duplicated, f"Duplicated invariant-check blocks: {duplicated}"

"""Regression tests pinning the current ARCHITECTURE.md INV-002 binding.

Trial A (interaction-protocol reframe, 2026-05-13) replaced the old
sectioned-narrative handoff with a frontmatter ``contract:`` block and
pointer-only body. INV-002 now delegates to the handoff contract test suite:

  - ``type: test-ref``
  - ``pattern: tests/unit/test_handoff_contract.py``

Legacy structural-parser and grep-proxy expectations are stale.

INV-008 was retired in M4 cairn-shrink (2026-05-07) by ADR
``slice-close-contract-superseded``; its test-ref binding block no longer
exists. INV-008 tests dropped from this file at that point.

Anti-revert guards (slice-1 ``phase_3_revert_under_red_pressure`` lesson):
the legacy-string ABSENCE assertions stop Phase 3 from silently restoring
the grep proxy when a downstream string-match test breaks. The proxy
must die for D2 to close.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = CAIRN_ROOT / "docs" / "ARCHITECTURE.md"
HANDOFF_CONTRACT_TEST = "tests/unit/test_handoff_contract.py"


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


# === T1 — INV-002 delegates to the handoff contract test suite ===============


def test_inv_002_block_type_is_test_ref():
    """INV-002's ``type:`` is ``test-ref`` after Trial A."""
    body = _block_for("INV-002")
    assert re.search(r"^\s*type:\s*test-ref\b", body, re.MULTILINE), (
        "INV-002 assertion block must declare type: test-ref. Got block body:\n"
        + body
    )


def test_inv_002_block_points_to_handoff_contract_test():
    """INV-002's ``test-ref`` points at tests/unit/test_handoff_contract.py."""
    body = _block_for("INV-002")
    assert re.search(
        rf"^\s*pattern:\s*[\"']?{re.escape(HANDOFF_CONTRACT_TEST)}[\"']?\s*$",
        body,
        re.MULTILINE,
    ), (
        f"INV-002 block must reference {HANDOFF_CONTRACT_TEST!r}. "
        f"Got: {body!r}"
    )


def test_inv_002_block_does_not_reintroduce_structural_parser_fields():
    """Trial A retired the structural-parser-shaped INV-002 block."""
    body = _block_for("INV-002")
    stale_fields = ["target:", "required-sections:", "binding-effective-from:"]
    found = [field for field in stale_fields if field in body]
    assert not found, f"INV-002 block still has structural-parser fields: {found}"


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

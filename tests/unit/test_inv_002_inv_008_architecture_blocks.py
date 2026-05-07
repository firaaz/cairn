"""Phase 2 RED tests pinning the ARCHITECTURE.md INV-002 block flips.

Slice v1-defense-d2/inv-002-binding-implementation per ADR
``invariant-binding-strategy`` D4–D6:

  - INV-002 assertion block becomes ``type: structural-parser`` targeting
    ``.claude/handoff.md`` with ``binding-effective-from`` set to the
    placeholder pre-close (substituted post-close).
  - Legacy grep proxy is GONE from ARCHITECTURE.md
    (``Token budget: 150 to 400 tokens``).

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

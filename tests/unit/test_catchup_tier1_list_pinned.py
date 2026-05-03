"""Phase 2 RED test for slice v1-defense-d2/inv-002-binding-implementation.

Pins INV-002(b) per ADR ``invariant-binding-strategy`` D5: the literal
five-item Tier-1 read list in ``commands/claude-code/catchup.full.md``
must appear verbatim and in declared order; the three Tier-2 admission
criteria must remain documented (structural-only — Tier-2 runtime
LLM-judgment binding is explicitly v2 per D5).

Anti-revert guards: this test file is the binding for INV-002(b).
``commands/claude-code/catchup.full.md`` carries a load-bearing list whose
verbatim shape IS the invariant. Any drift renames or reorders are
substrate violations, not test bugs.
"""

from __future__ import annotations

from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
CATCHUP_FULL = CAIRN_ROOT / "commands" / "claude-code" / "catchup.full.md"


# Per ADR D5 — the five Tier-1 items in declared order.
TIER1_FIVE_ITEMS = [
    ".claude/handoff.md",
    ".claude/current-slice/slice.yaml",
    ".claude/sweep.yaml",
    "git log --oneline -5",
    "git status --short",
]


# --- Defensive isolation ----------------------------------------------------


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)


# === T1 — Verbatim five-item Tier-1 pin =====================================


def test_tier1_five_items_verbatim():
    """Five Tier-1 items appear verbatim and in declared order in catchup.full.md.

    Verbatim: every item appears as a literal substring (each Tier-1 item is
    quoted unambiguously in the file — backticks for paths, plain for shell
    commands).
    Order: each item appears at a strictly increasing offset from the
    previous one, so reordering or substituting items breaks the test.
    """
    assert CATCHUP_FULL.exists(), (
        f"catchup.full.md missing at {CATCHUP_FULL} — substrate broken"
    )
    text = CATCHUP_FULL.read_text()

    last_offset = -1
    for item in TIER1_FIVE_ITEMS:
        offset = text.find(item, last_offset + 1)
        assert offset != -1, (
            f"Tier-1 item {item!r} missing or out of order in "
            f"commands/claude-code/catchup.full.md. Previous offset: "
            f"{last_offset}. Either the substrate drifted or the binding "
            f"shape changed — fix the file, not the list."
        )
        last_offset = offset


def test_tier1_items_appear_inside_tier1_section():
    """The five-item list lives in the ``## Tier 1`` section, not elsewhere.

    Guards against the items being deleted from the binding section but
    surviving as incidental mentions in prose elsewhere.
    """
    text = CATCHUP_FULL.read_text()
    tier1_start = text.find("## Tier 1")
    assert tier1_start != -1, "## Tier 1 section heading missing from catchup.full.md"
    next_h2 = text.find("\n## ", tier1_start + len("## Tier 1"))
    section = text[tier1_start : next_h2 if next_h2 != -1 else len(text)]

    for item in TIER1_FIVE_ITEMS:
        assert item in section, (
            f"Tier-1 item {item!r} present in file but missing from the "
            f"## Tier 1 section. Binding shape requires the items live "
            f"inside the section that names them."
        )


# === T2 — Three Tier-2 admission criteria documented ========================


def test_tier2_three_admission_criteria_documented():
    """Three Tier-2 admission criteria appear as enumerated items in the file.

    Per ADR D5 these are documented-only at v1 (LLM-judgment runtime binding
    is explicitly deferred). The structural assertion catches deletion of any
    one of the three numbered conditions.
    """
    text = CATCHUP_FULL.read_text()

    # The ADR refers to "the three Tier-2 admission criteria". The catchup
    # full reference enumerates them under a DISPATCH block. We pin three
    # numbered conditions inside a Tier-2 DISPATCH block.
    tier2_start = text.find("## Tier 2")
    assert tier2_start != -1, "## Tier 2 section heading missing from catchup.full.md"
    next_h2 = text.find("\n## ", tier2_start + len("## Tier 2"))
    section = text[tier2_start : next_h2 if next_h2 != -1 else len(text)]

    for n in ("1.", "2.", "3."):
        assert n in section, (
            f"Tier-2 admission criterion enumerator '{n}' missing from the "
            f"## Tier 2 section. ADR D5 binds three documented criteria; "
            f"deletion of any breaks the structural binding."
        )

    # Anchor on the DISPATCH block that ADR D5 references; criteria must
    # live under a DISPATCH directive (vs. being listed elsewhere).
    assert "DISPATCH" in section, (
        "Tier-2 admission criteria must be grouped under a DISPATCH "
        "directive per the catchup.full.md shape ADR D5 binds against."
    )


# === T3 — Tier-2 LLM-judgment binding deferral marker still documented ======


def test_tier2_runtime_judgment_remains_v1_documented_only():
    """No Tier-2 runtime ENFORCEMENT — only documentation. Sentinel: condition language.

    Per ADR D5: ``Tier-2 admission criteria are NOT bound at v1 — they
    describe runtime LLM judgment, not file state.`` Catchup.full.md
    must continue to phrase the criteria as conditions / DISPATCH guards
    (operator-following text), not as machine-enforced rules. Sentinel:
    the file uses "if and only if" or "DISPATCH" framing, not "must
    pass" or "validator-enforced" framing.
    """
    text = CATCHUP_FULL.read_text()
    assert "if and only if" in text or "DISPATCH" in text, (
        "Tier-2 admission language must remain operator-following "
        "(documented, not machine-enforced) per ADR D5 v1 deferral."
    )
    assert "validator-enforced" not in text, (
        "Tier-2 must NOT be machine-enforced at v1 — D5 explicitly defers "
        "runtime LLM-judgment binding to v2."
    )

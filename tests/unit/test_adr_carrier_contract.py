"""Check F (INV-013 D5): every non-superseded ADR declares its carrier tier.

A live-constraint ADR carries a `contract:` frontmatter block naming its
level 1-4 mechanical carrier; a rationale/history ADR carries
`carrier: rationale-only`. Neither → validation fails. Superseded ADRs are
exempt (append-only stands).
"""

from __future__ import annotations

from pathlib import Path

from validate_architecture import check_adr_carrier, parse_adr

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_DIR = CAIRN_ROOT / "docs" / "adr"


def _adr(**kw) -> dict:
    base = {
        "key": "test-adr",
        "title": "Test ADR",
        "status": "accepted",
        "firmness": "firm",
        "superseded_by": None,
        "invariants_touched": [],
        "has_contract": False,
        "carrier": None,
        "path": "docs/adr/test-adr.md",
    }
    base.update(kw)
    return base


def test_missing_declaration_fails():
    failures = check_adr_carrier({"test-adr": _adr()})
    assert len(failures) == 1
    assert "Check F" in failures[0]
    assert "test-adr" in failures[0]


def test_contract_block_passes():
    assert check_adr_carrier({"a": _adr(has_contract=True)}) == []


def test_rationale_only_passes():
    assert check_adr_carrier({"a": _adr(carrier="rationale-only")}) == []


def test_superseded_is_exempt():
    adr = _adr(status="superseded", superseded_by="replacement-adr")
    assert check_adr_carrier({"a": adr}) == []


def test_unknown_carrier_value_fails():
    failures = check_adr_carrier({"a": _adr(carrier="vibes")})
    assert len(failures) == 1
    assert "Check F" in failures[0]


def test_live_corpus_passes():
    """Every non-superseded ADR in the repo declares its tier (the backfill)."""
    adrs = {}
    for f in sorted(ADR_DIR.glob("*.md")):
        adr = parse_adr(f)
        if adr is not None:
            adrs[adr["key"]] = adr
    assert adrs, "no ADRs parsed"
    failures = check_adr_carrier(adrs)
    assert failures == [], "\n".join(failures)

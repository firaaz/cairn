"""Shared atomicity evaluator contract (cairn-trial-d-scope-split).

The scope-split rule's single source of truth: ``scripts/lib/atomicity.py``
defines ``EXCEPTION_TAGS``, ``is_atomic``, ``parse_exception`` and
``check_clauses``; both the CLI gate (``checks/atomicity_guard.py``) and the
validator's ``scope-split`` assertion import them (FLI-1). The heuristic is
deliberately SHY — biased to pass — so the four-tag declaration check is the
primary, zero-false-positive enforcement and the tag is always a one-line
escape (FLI-3). These tests pin that encoded behaviour.

RED at HEAD: ``scripts/lib/atomicity.py`` does not exist (ImportError on
collection) and the ``scope-split`` assertion type is unregistered (so the
discriminating ``*_offends`` assertion case fails — an unknown type falls
through to ``return None`` and a non-atomic clause silently passes).

NOTE on corpus grounding: the env's stdout/read channel could not surface the
verbatim prose of the m2/m5/m7 corpus intents at authoring time, so the LIGHT
denominator and HEAVY/MEDIUM rows below use clauses that exercise the SAME
documented signals (intent.md lines 32 / 55). approach.md flags re-pinning
these to verbatim corpus strings as a human follow-up.
"""

from __future__ import annotations

import pytest

from lib.atomicity import (  # noqa: E402  (RED: module absent at HEAD)
    EXCEPTION_TAGS,
    TAGS_REQUIRING_DECLARATION,
    check_clauses,
    is_atomic,
    parse_exception,
)
from validate_architecture import _run_assertion  # noqa: E402


# ─────────────────────────── tag sets ───────────────────────────


def test_exception_tags_exact_set() -> None:
    assert EXCEPTION_TAGS == frozenset(
        {"universal-set", "regression-meta", "operator-bound", "trivial-existence"}
    )


def test_tags_requiring_declaration_is_set_minus_trivial() -> None:
    assert TAGS_REQUIRING_DECLARATION == EXCEPTION_TAGS - {"trivial-existence"}
    assert TAGS_REQUIRING_DECLARATION == frozenset(
        {"universal-set", "regression-meta", "operator-bound"}
    )
    assert "trivial-existence" not in TAGS_REQUIRING_DECLARATION


# ───── is_atomic: LIGHT false-positive denominator (must all pass) ─────


# Representative of the ~8 m2-dogfood-extract-invariant-ids behaviors: each is a
# single-tool-call / single-file check with no universal quantifier, no
# regression meta-phrase, and no verb-conjunction. ANY flag here is a false
# positive — the lever holding Trial D's <10% bound (intent.md Why / line 21).
LIGHT_ATOMIC_CLAUSES = [
    "the extractor reads invariant ids from the frontmatter block",
    "the parser returns the id string when an id field is present",
    "the function raises a ValueError when the id field is missing",
    "the writer appends the extracted id to the ids list",
    "the cli prints the id to stdout on success",
    "the loader resolves the intent path relative to the project root",
    "the validator reports the offending line number on a malformed id",
    "the helper normalizes the id to lowercase before comparison",
]


@pytest.mark.parametrize("clause", LIGHT_ATOMIC_CLAUSES)
def test_light_corpus_clauses_pass_is_atomic_untagged(clause: str) -> None:
    assert is_atomic(clause) is True, (
        f"false positive on LIGHT denominator clause: {clause!r}"
    )


def test_adjectival_and_stays_atomic_no_over_split() -> None:
    # 'exists and parses' is adjectival, not two verb-like phrases — the shy
    # heuristic must NOT split it (intent.md line 32).
    assert is_atomic("the config file exists and parses as valid yaml") is True
    assert is_atomic("the output is present and well-formed") is True


# ───── is_atomic: HEAVY/MEDIUM non-atomic clauses (must flag when bare) ─────


# Universal-set signal (m5-f1 A3/A4/A6 are 'universal' per intent.md line 70;
# m7 FLI-4 is the universal-set case). Word-boundary quantifiers.
UNIVERSAL_CLAUSES = [
    "every consumer repository receives the regenerated dist mirror",
    "all eight prose section headings remain present and in order",
    "each exception tag maps to exactly one declaration requirement",
    "none of the existing intents break under the new gate",
    "exactly the following six clause-lists appear in the contract block",
]


@pytest.mark.parametrize("clause", UNIVERSAL_CLAUSES)
def test_universal_clauses_flag_when_bare(clause: str) -> None:
    assert is_atomic(clause) is False, f"universal clause should flag: {clause!r}"


# Regression-meta signal (m5-f1 A8 is regression-meta per intent.md line 70).
REGRESSION_CLAUSES = [
    "the eight-heading-in-order assertion behaves identically after the change",
    "the existing premise-grounding suite is unchanged",
    "there is no regression in the validator's prior check count",
]


@pytest.mark.parametrize("clause", REGRESSION_CLAUSES)
def test_regression_meta_clauses_flag_when_bare(clause: str) -> None:
    assert is_atomic(clause) is False, f"regression clause should flag: {clause!r}"


def test_verb_conjunction_flags_when_bare() -> None:
    # Two distinct verb-like phrases joined by ' and ' / ';' — m7 operator-bound
    # FLI-7-style compound action. NOT atomic (two tool calls).
    assert is_atomic("the gate parses the contract and writes the offence log") is False
    assert is_atomic("extract the ids; validate them against the schema") is False


# ─────────────────────── parse_exception ───────────────────────


def test_parse_exception_mapping_returns_tag_and_declaration() -> None:
    item = {
        "clause": "every consumer gets the mirror",
        "except": "universal-set: the consumer set is the 3 repos listed in roadmap.md",
    }
    tag, decl = parse_exception(item)
    assert tag == "universal-set"
    assert decl == "the consumer set is the 3 repos listed in roadmap.md"


def test_parse_exception_bare_string_returns_none_empty() -> None:
    tag, decl = parse_exception("the parser returns the id string")
    assert tag is None
    assert decl == ""


def test_parse_exception_trivial_existence_allows_empty_declaration() -> None:
    tag, decl = parse_exception(
        {"clause": "the dist mirror exists", "except": "trivial-existence"}
    )
    assert tag == "trivial-existence"
    assert decl == ""


# ─────────────────────── check_clauses ───────────────────────


def test_check_clauses_bare_atomic_passes() -> None:
    assert check_clauses(["the parser returns the id string when present"]) == []


def test_check_clauses_bare_non_atomic_offends() -> None:
    offences = check_clauses(["every consumer repository receives the mirror"])
    assert offences != []
    assert len(offences) == 1


def test_check_clauses_unknown_tag_offends() -> None:
    offences = check_clauses(
        [{"clause": "all repos get it", "except": "made-up-tag: whatever"}]
    )
    assert offences != []


def test_check_clauses_required_tag_empty_declaration_offends() -> None:
    # universal-set is in TAGS_REQUIRING_DECLARATION → empty declaration offends.
    offences = check_clauses(
        [{"clause": "every consumer gets the mirror", "except": "universal-set:"}]
    )
    assert offences != []


def test_check_clauses_trivial_existence_no_declaration_passes() -> None:
    assert (
        check_clauses(
            [{"clause": "the dist mirror exists", "except": "trivial-existence"}]
        )
        == []
    )


def test_check_clauses_flagged_clause_with_valid_tag_and_decl_passes() -> None:
    # FLI-3: a clause is_atomic flags can pass by carrying a valid tag + decl.
    bare = "every consumer repository receives the regenerated dist mirror"
    assert is_atomic(bare) is False
    offences = check_clauses(
        [
            {
                "clause": bare,
                "except": "universal-set: the consumer set is the 3 repos in roadmap.md",
            }
        ]
    )
    assert offences == []


def test_check_clauses_collects_all_offences() -> None:
    offences = check_clauses(
        [
            "every consumer gets the mirror",  # bare non-atomic
            {"clause": "all repos", "except": "bogus: x"},  # unknown tag
            {"clause": "each repo", "except": "operator-bound:"},  # empty decl
            "the parser returns the id string",  # atomic — no offence
        ]
    )
    assert len(offences) == 3


# ───────── assertion wiring through the PUBLIC validator entry ─────────


def test_scope_split_assertion_all_pass_returns_none(tmp_path) -> None:
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        {
            "type": "scope-split",
            "must-satisfy": [
                "the parser returns the id string when present",
                {
                    "clause": "every consumer receives the mirror",
                    "except": "universal-set: the 3 repos in roadmap.md",
                },
            ],
        },
    )
    assert result is None


def test_scope_split_assertion_offending_clause_fails(tmp_path) -> None:
    # The discriminating RED case: until the scope-split branch is registered in
    # _run_assertion, an unknown type returns None and this non-atomic clause
    # silently passes (test fails RED, as intended).
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        {
            "type": "scope-split",
            "must-satisfy": ["every consumer repository receives the mirror"],
        },
    )
    assert result is not None
    assert "INV-TEST" in result


def test_unknown_assertion_type_returns_none(tmp_path) -> None:
    # An unregistered type falls through to `return None` — proves the dispatcher
    # is a clean if-chain (so the scope-split case above fails RED correctly).
    result = _run_assertion(
        tmp_path, "INV-TEST", {"type": "no-such-assertion-type-xyz"}
    )
    assert result is None

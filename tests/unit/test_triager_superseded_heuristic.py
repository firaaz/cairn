"""Phase 2 RED — compression/triager-superseded-test-heuristic.

Pins intent.md S1 (pure-function signal detector) and S2 (dispatch_triager
threads the hint into the triager child-process JSON payload).

Expected at Phase 2: all tests FAIL — `detect_superseded_test_signal`
does not exist; `dispatch_triager` does not read intent.md / git log /
inject `supersession_hint` into its inputs.
"""

from __future__ import annotations


# --- S1 — pure-function signal detector -----------------------------------


def _detect():
    from lib.superseded_test_signal import detect_superseded_test_signal

    return detect_superseded_test_signal


def test_s1_case_1_superseded_keyword_fires():
    """Verification case 1 — `superseded` keyword returns a signal dict
    whose evidence list contains the matched token."""
    detect = _detect()
    result = detect(
        raise_issue_summary=(
            "Pre-existing test_v6_four_phase_handoff_commits_present "
            "encodes behavior superseded by DC-4."
        ),
        current_slice_intent="",
    )
    assert isinstance(result, dict), (
        f"superseded keyword must produce dict, got {result!r}"
    )
    assert result.get("hint") == "likely_superseded", (
        f"hint must equal 'likely_superseded'; got {result!r}"
    )
    evidence = result.get("evidence")
    assert isinstance(evidence, list) and evidence, (
        f"evidence must be a non-empty list; got {evidence!r}"
    )
    assert any("supersede" in tok.lower() for tok in evidence), (
        f"evidence must name the matched token; got {evidence!r}"
    )


def test_s1_case_2_supersede_root_form_fires():
    """Verification case 2 — the root `supersede` alone fires."""
    detect = _detect()
    result = detect(
        raise_issue_summary="These three tests supersede the earlier contract.",
        current_slice_intent="",
    )
    assert result is not None and result.get("hint") == "likely_superseded"


def test_s1_case_3_inv_code_fires_without_intent():
    """Verification case 3 — `INV-008` in summary fires regardless of intent text."""
    detect = _detect()
    result = detect(
        raise_issue_summary="Tests encode behavior INV-008 now forbids.",
        current_slice_intent="",  # explicitly empty — no AND-gate on INV
    )
    assert result is not None, "INV-\\d{3} must fire regardless of intent text"
    assert result.get("hint") == "likely_superseded"
    assert any("INV-008" in tok for tok in result["evidence"]), (
        f"INV-008 must appear in evidence; got {result['evidence']!r}"
    )


def test_s1_case_4_dc_code_in_summary_and_intent_fires():
    """Verification case 4 — `DC-4` in both summary and intent fires."""
    detect = _detect()
    result = detect(
        raise_issue_summary="Test contradicts DC-4 of this slice.",
        current_slice_intent=(
            "## Decision points\n- DC-4: close commit forbids wipe-after\n"
        ),
    )
    assert result is not None, "DC-<n> AND-gate must pass when token is in intent"
    assert result.get("hint") == "likely_superseded"
    assert any("DC-4" in tok for tok in result["evidence"])


def test_s1_case_5_dc_code_in_summary_only_does_not_fire():
    """Verification case 5 — `DC-4` in summary but NOT in intent returns None
    (AND-gate closed)."""
    detect = _detect()
    result = detect(
        raise_issue_summary="Author quotes DC-4 from somebody else's ADR.",
        current_slice_intent="This slice has no decision-point references.\n",
    )
    assert result is None, (
        f"DC-<n> AND-gate must be closed when token absent from intent; got {result!r}"
    )


def test_s1_case_6_no_tokens_returns_none():
    """Verification case 6 — summary with none of the trigger tokens."""
    detect = _detect()
    result = detect(
        raise_issue_summary=(
            "Implementation defect: the new assertion misaligned "
            "with the RED suite's fixture path."
        ),
        current_slice_intent="DC-4\nDC-5\nINV-008\n",
    )
    assert result is None, f"ordinary defect text must not fire; got {result!r}"


def test_s1_case_7a_supersedes_does_not_fire_word_boundary():
    """Verification case 7 — word-boundary semantics: `supersedes` (plural,
    trailing `s`) does NOT match. Regex is `\\bsuperseded?\\b`."""
    detect = _detect()
    result = detect(
        raise_issue_summary="The new contract supersedes the old one.",
        current_slice_intent="",
    )
    assert result is None, (
        f"supersedes (trailing s) must not match \\bsuperseded?\\b; got {result!r}"
    )


def test_s1_case_7b_undersuperseded_does_not_fire_word_boundary():
    """Word-boundary on the left — `undersuperseded` must not match."""
    detect = _detect()
    result = detect(
        raise_issue_summary="This is undersuperseded in the literature.",
        current_slice_intent="",
    )
    assert result is None, (
        f"undersuperseded must not match (no left word boundary); got {result!r}"
    )


def test_s1_case_8_case_insensitive():
    """Verification case 8 — `SUPERSEDED`, `Inv-008`, `dc-4` all fire."""
    detect = _detect()

    upper = detect(
        raise_issue_summary="Behavior is SUPERSEDED.",
        current_slice_intent="",
    )
    assert upper is not None, "SUPERSEDED must fire (case-insensitive)"

    mixed_inv = detect(
        raise_issue_summary="See Inv-008 for details.",
        current_slice_intent="",
    )
    assert mixed_inv is not None, "Inv-008 must fire (case-insensitive)"

    lower_dc = detect(
        raise_issue_summary="dc-4 applies here.",
        current_slice_intent="DC-4 is defined.",
    )
    assert lower_dc is not None, (
        "dc-4 must fire when DC-4 is in intent (case-insensitive)"
    )


def test_s1_case_9_empty_inputs_returns_none():
    """Verification case 9 — empty inputs return None (no crash, no signal)."""
    detect = _detect()
    assert detect(raise_issue_summary="", current_slice_intent="") is None
    assert detect(raise_issue_summary="", current_slice_intent="DC-4") is None


def test_s1_case_10_evidence_is_deduped_and_ordered():
    """Verification case 10 — evidence is a list, deduped, in first-match
    order. Skeptic's contract: implementer must honor this shape."""
    detect = _detect()
    summary = "Tests superseded by DC-4. Again superseded per DC-4. INV-008 also."
    result = detect(
        raise_issue_summary=summary,
        current_slice_intent="DC-4 is decided here.\n",
    )
    assert result is not None
    evidence = result["evidence"]
    assert isinstance(evidence, list)
    # Dedup: each distinct matched token appears at most once.
    lowered = [tok.lower() for tok in evidence]
    assert len(lowered) == len(set(lowered)), (
        f"evidence must be deduped; got {evidence!r}"
    )

    # First-match order: `supersede*` appears before `DC-4` which appears
    # before `INV-008` in the summary.
    def _idx(needle: str) -> int:
        for i, tok in enumerate(lowered):
            if needle in tok:
                return i
        return -1

    sup_i = _idx("supersede")
    dc_i = _idx("dc-4")
    inv_i = _idx("inv-008")
    assert sup_i != -1 and dc_i != -1 and inv_i != -1, (
        f"all three tokens must be in evidence; got {evidence!r}"
    )
    assert sup_i < dc_i < inv_i, (
        f"evidence must follow first-match order of summary; got {evidence!r}"
    )

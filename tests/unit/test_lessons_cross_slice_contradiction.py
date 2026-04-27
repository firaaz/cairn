"""Phase 2 RED — compression/lever-Z-fixup §S3.

Asserts that ``docs/lessons.md`` gains entry **L-014** with the
load-bearing directive sentence about Phase-2 pre-grepping the existing
test corpus for assertions that would be inverted by the slice's
enforcement-set widening.

Per ``.claude/current-slice/intent.md`` §S3 + §S5. The intent permits
Phase-3 to rephrase the lesson body, but mandates that the stable token
``pre-grep the existing test corpus`` (or its preserved-semantics
equivalent) appear in the entry.

Expected at Phase 2 (RED): FAILS — current ``docs/lessons.md`` ends at
L-013 and contains no L-014 entry.
"""

from __future__ import annotations

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
LESSONS = CAIRN_ROOT / "docs" / "lessons.md"


def _read_lessons() -> str:
    assert LESSONS.is_file(), (
        f"intent §S3 — `docs/lessons.md` must exist; missing at {LESSONS}"
    )
    return LESSONS.read_text()


def test_s3_l014_heading_present():
    """intent §S3 — L-014 heading exists in `docs/lessons.md`.

    Accepts both `## L-014:` (Markdown H2 form used by L-001..L-013) and
    `### L-014:` for safety, but the H2 form is what the file's existing
    convention uses.
    """
    body = _read_lessons()
    pattern = re.compile(r"^#{2,3}\s*L-014\b", re.MULTILINE)
    assert pattern.search(body), (
        "intent §S3 — `docs/lessons.md` must contain an L-014 heading "
        "(Markdown `## L-014:` per existing L-001..L-013 convention)"
    )


def test_s3_l014_directive_stable_token_present():
    """intent §S3 — load-bearing directive token preserved.

    intent.md §S3: "Phase-3 may rephrase, but the test asserts the stable
    token 'pre-grep the existing test corpus' appears." This token is the
    single load-bearing signal that the Phase-2 actionable directive made
    it into the lesson body, regardless of Phase-3's prose styling.
    """
    body = _read_lessons()
    assert "pre-grep the existing test corpus" in body, (
        "intent §S3 — L-014 entry must contain the stable directive token "
        '"pre-grep the existing test corpus" (Phase-3 may rephrase the '
        "surrounding sentence but this token is load-bearing per intent.md)"
    )


def test_s3_l014_names_phase_2_skeptic_actor():
    """intent §S3 — directive sentence names Phase-2 as the actor.

    The lesson is actionable only if it tells the reader WHO performs the
    pre-grep. intent.md §S3 directive: "Phase-2 skeptic SHOULD pre-grep ...".
    Stable token: case-insensitive substring `phase-2` MUST appear WITHIN
    the L-014 entry body (scoped between the L-014 heading and the next
    L-NNN heading, or end of file). A bare file-scope grep would pass
    vacuously thanks to other lesson entries that already mention Phase-2,
    masking a Phase-3 rephrasing that drops the actor.
    """
    body = _read_lessons()
    l014_match = re.search(r"^#{2,3}\s*L-014\b", body, re.MULTILINE)
    assert l014_match is not None, (
        "intent §S3 precondition — L-014 heading must be present (also "
        "covered by test_s3_l014_heading_present)"
    )
    # Slice the L-014 entry body: from end of L-014 heading line to start
    # of next L-NNN heading (or end of file).
    start = l014_match.end()
    next_match = re.search(r"^#{2,3}\s*L-\d+\b", body[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(body)
    entry_body = body[start:end].lower()
    assert "phase-2" in entry_body or "phase 2" in entry_body, (
        "intent §S3 — L-014 entry body MUST name the Phase-2 skeptic as "
        "the actor of the pre-grep directive (without a named actor the "
        "lesson is unactionable); scoped to L-014 entry to prevent vacuous "
        "match against unrelated lesson entries that already mention Phase-2"
    )


def test_s3_l014_appended_after_l013():
    """intent §S3 — L-014 inserted after L-013 (entries are ordered).

    intent.md: "Entry inserted as `L-014` after `L-013` in `docs/lessons.md`
    (currently 13 entries through L-013)." Asserts L-013 heading appears
    before L-014 heading in source order.
    """
    body = _read_lessons()
    l013_match = re.search(r"^#{2,3}\s*L-013\b", body, re.MULTILINE)
    l014_match = re.search(r"^#{2,3}\s*L-014\b", body, re.MULTILINE)
    assert l013_match is not None, (
        "intent §S3 precondition — L-013 must remain present in lessons.md"
    )
    assert l014_match is not None, (
        "intent §S3 — L-014 heading must be present (covered by "
        "test_s3_l014_heading_present; co-asserted here for ordering "
        "diagnostic clarity)"
    )
    assert l013_match.start() < l014_match.start(), (
        "intent §S3 — L-014 must appear AFTER L-013 in source order; "
        f"got L-013@{l013_match.start()} L-014@{l014_match.start()}"
    )

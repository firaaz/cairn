"""Phase 2 RED — compression/learnings-capture (retry).

The retry's distinguishing constraint, called out by the prior failed slice's
post-mortem (root cause: `cluster-no-RED-test`):

  > Phase 3's prompt-amendment cluster observed GREEN test status and
  > reported OK without editing `.claude/agents/phase-4-integrator.md`,
  > because the prior intent excluded prompt-content tests as "brittle."

This file re-introduces a string-presence assertion against the agent file,
explicitly accepting brittleness as the price of a RED progress signal binding
the prompt-amendment cluster. Without these tests the cluster is vacuous —
Phase 3 sees GREEN, declares OK, ships nothing.

Bound to the `phase4-prompt-amendment` cluster (envelope:
`.claude/agents/phase-4-integrator.md`).

Spec sources:
  - `.claude/current-slice/intent.md` §Phase-4 integrator prompt amendment,
    §Verification (t4a, t4b).
  - Anti-pattern: see prior failed slice
    `.claude/completed-slices/compression-learnings-capture-failed/`
    (slice.yaml failure-reason names the gap; sweep-notes.md row 19 names
    the missing section).

Expected at Phase 2 (RED): both tests fail — the live agent file is 19 lines
and contains no `## Learnings observed` heading until Phase 3 lands the
amendment.
"""

from __future__ import annotations

from pathlib import Path

import pytest


PROMPT_PATH = Path(".claude/agents/phase-4-integrator.md")


@pytest.fixture
def prompt_text():
    assert PROMPT_PATH.is_file(), (
        f"phase-4-integrator prompt missing at {PROMPT_PATH} — envelope misconfigured"
    )
    return PROMPT_PATH.read_text()


def test_t4a_phase4_integrator_prompt_has_learnings_section(prompt_text):
    """Literal substring `## Learnings observed` must appear somewhere in the
    Phase-4 integrator prompt (intent §Phase-4 integrator prompt amendment).

    Brittleness explicitly accepted — the alternative is no progress signal,
    which is the failure mode that closed the predecessor slice (FAILED at
    B15 cap with the prompt-amendment cluster vacuous-GREEN).
    """
    assert "## Learnings observed" in prompt_text, (
        "phase-4-integrator.md must contain a `## Learnings observed` "
        "subsection in its sweep-notes.md template guidance "
        "(intent §Phase-4 integrator prompt amendment)"
    )


def test_t4b_phase4_integrator_prompt_marks_learnings_optional(prompt_text):
    """The `## Learnings observed` heading must be framed as optional (intent
    §Phase-4 integrator prompt amendment: "free-form, empty by default").

    Defends against a regression where Phase 3 lands the section but presents
    it as required, which would silently change the Phase-4 contract — empty
    sweep-notes would suddenly fail closes-when. Asserts the literal token
    `optional` appears on the same line as the `## Learnings observed`
    heading (or in the immediately-following framing).
    """
    lines = prompt_text.splitlines()
    heading_idx = None
    for i, line in enumerate(lines):
        if "## Learnings observed" in line:
            heading_idx = i
            break
    assert heading_idx is not None, (
        "precondition: t4a should have failed first if the heading is absent"
    )
    # Accept `optional` either on the heading line itself (the canonical form
    # `## Learnings observed (optional)`) or on the immediate next non-empty
    # line of framing prose, but NOT later — the marker must travel with the
    # heading so a casual reader cannot miss it.
    heading_line = lines[heading_idx]
    next_line = lines[heading_idx + 1] if heading_idx + 1 < len(lines) else ""
    combined = f"{heading_line}\n{next_line}".lower()
    assert "optional" in combined, (
        "phase-4-integrator.md `## Learnings observed` heading must mark the "
        "section optional (intent: 'free-form, empty by default'); got "
        f"heading line {heading_line!r} and next line {next_line!r}"
    )

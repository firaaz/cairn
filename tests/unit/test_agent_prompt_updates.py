"""Phase 2 RED — phase-agent prompt edits (P1 heredoc note, P2 no-preemptive-
refuse, DC-4 Phase-4 anti-self-commit).

Spec: intent.md §DC-4 three-layer enforcement (prompt layer) + §Artifact
inventory. Every phase agent prompt must carry:
 - **P1**: a note on the Bash-heredoc escape for sensitive-file writes.
 - **P2**: a rule that agents must attempt the tool call and not refuse
   preemptively based on prior-art docs.
Phase-4 integrator additionally must carry an explicit "do not issue `git
commit` in Phase 4" anti-behavior clause (DC-4).

Expected at Phase 2: every test FAILS — the current prompts do not yet
contain the required clauses. The grep is intentionally loose so minor
phrasing variations in Phase 3 still pass, but the required keywords must be
present.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


AGENT_DIR = Path(".claude/agents")

PHASE_PROMPT = {
    1: AGENT_DIR / "phase-1-writer.md",
    2: AGENT_DIR / "phase-2-skeptic.md",
    3: AGENT_DIR / "phase-3-implementer.md",
    4: AGENT_DIR / "phase-4-integrator.md",
}


def _text(path: Path) -> str:
    assert path.exists(), f"phase-agent prompt missing: {path}"
    return path.read_text()


def _has_heredoc_note(text: str) -> bool:
    # "heredoc" anywhere (case-insensitive) plus a mention of a sensitive-file
    # / bash escape context — loose so Phase 3 has phrasing freedom.
    t = text.lower()
    if "heredoc" not in t:
        return False
    return ("bash" in t) and any(
        kw in t for kw in ("sensitive", ".claude/", "escape", "write-escape")
    )


def _has_no_preemptive_refuse_rule(text: str) -> bool:
    t = text.lower()
    # Needs to tell the agent to attempt the call and not refuse based on
    # prior-art / docs alone.
    if "refuse" not in t and "refus" not in t:
        return False
    return any(
        kw in t
        for kw in (
            "preemptive",
            "pre-emptive",
            "prior-art",
            "attempt the tool",
            "attempt the call",
            "do not refuse",
            "don't refuse",
        )
    )


@pytest.mark.parametrize("phase", [1, 2, 3, 4])
def test_phase_prompt_mentions_bash_heredoc_escape(phase):
    text = _text(PHASE_PROMPT[phase])
    assert _has_heredoc_note(text), (
        f"phase-{phase} prompt must carry the P1 Bash-heredoc sensitive-file note"
    )


def test_all_phase_prompts_have_do_not_refuse_preemptively_rule():
    offenders = [
        p
        for phase, p in PHASE_PROMPT.items()
        if not _has_no_preemptive_refuse_rule(_text(p))
    ]
    assert not offenders, (
        f"P2 no-preemptive-refuse rule missing from: {[str(p) for p in offenders]!r}"
    )


def test_phase_4_prompt_explicitly_forbids_self_commit():
    text = _text(PHASE_PROMPT[4]).lower()
    assert "git commit" in text, (
        "phase-4 prompt must reference `git commit` so the anti-behavior is explicit"
    )
    # Must contain a negation: "do not", "never", "forbidden", "must not".
    negation = re.search(
        r"(do not|don't|never|must not|forbidden|do not issue)[^.\n]{0,60}(commit|git commit)",
        text,
    )
    assert negation, (
        "phase-4 prompt must forbid issuing `git commit` in Phase 4 (DC-4 prompt layer)"
    )
    assert "close_slice" in text or "slice: complete" in text, (
        "phase-4 prompt must point the agent to close_slice as the sole commit source"
    )

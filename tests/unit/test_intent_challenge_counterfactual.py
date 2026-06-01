"""Acceptance gate for the intent-challenge subagent (ADR intent-management-loop
D9): it proves *why* the agent is load-bearing rather than asserting its verdict.

This is a CHARACTERIZATION test of premise_guard's blind spot, not a red→green
driver — premise_guard already exists, and its actual blocking of slice-#25 by
the agent is the Trial-E integration gate, not a unit test (no honest mechanical
detector exists; trials plan §1.3). It complements
test_premise_guard.py::test_slice25_wrong_premise_exits_1, which covers the
variant where the lie lives in the quoted span. Here the lie lives in the
`label:` / dependent claim — the surface premise_guard never reads
(checks/premise_guard.py only inspects `source` and `quote`). That variant is
exactly what the intent-challenge agent owns semantically.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUARD = PROJECT_ROOT / "checks" / "premise_guard.py"

# Live source: _REPO_ROOT feeds sys.path only — never DB or corpus paths.
_SOURCE = '_REPO_ROOT = "/repo"\nsys.path.insert(0, _REPO_ROOT)\n'


def _run(intent_path, project_dir):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CAIRN_PREMISE_FIX", None)
    return subprocess.run(
        [sys.executable, str(GUARD), str(intent_path)],
        capture_output=True,
        text=True,
        env=env,
    )


def _intent(tmp_path, yaml_body):
    intent = tmp_path / "intent.md"
    intent.write_text(f"# Intent\n\n## Premise Grounding\n\n```yaml\n{yaml_body}```\n")
    return intent


def test_premise_guard_passes_grounded_quote_with_lying_label(tmp_path):
    # The quote is verbatim-present, so premise_guard exits 0 — even though the
    # label asserts a DB/corpus role the source never plays. premise_guard never
    # reads `label:`, so the wrong-model claim passes the mechanical gate clean.
    (tmp_path / "root.py").write_text(_SOURCE)
    intent = _intent(
        tmp_path,
        "premises:\n"
        "  - source: root.py\n"
        "    quote: |\n"
        "      sys.path.insert(0, _REPO_ROOT)\n"
        '    label: "_REPO_ROOT resolves sys.path AND the DB and corpus paths"\n',
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr  # the gap the intent-challenge agent covers


def test_premise_guard_blocks_only_when_the_lie_is_in_the_quote(tmp_path):
    # Move the same wrong-model claim into the quoted span: now it is absent from
    # the source, so verbatim grounding catches it (exit 1). This pins that
    # premise_guard defends the quote, not the claim — the boundary of its reach.
    (tmp_path / "root.py").write_text(_SOURCE)
    intent = _intent(
        tmp_path,
        "premises:\n"
        "  - source: root.py\n"
        "    quote: |\n"
        "      _REPO_ROOT resolves sys.path and the DB and corpus paths\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "root.py" in r.stderr

"""CLI exit-code contract for checks/atomicity_guard.py (cairn-trial-d-scope-split).

The gate runs the scope-split (atomicity) check on an intent's ``## Contract``
``must-satisfy`` clauses at the Phase-1→Phase-2 boundary, mirroring
``premise_guard.py``. Exercised end-to-end via subprocess against real exit
codes — no mocks (FLI-1: the gate and the validator assertion route through the
same ``lib.atomicity.check_clauses``, so faking the checker would hide
divergence).

Exit-code contract (intent.md line 46 / FLI-2, FLI-3, FLI-4):
  0 = no ``## Contract`` block (fail-open + visible stderr notice unless
      CAIRN_CONTRACT_REQUIRED), or all clauses atomic-or-validly-tagged,
      or CAIRN_ATOMICITY_FIX=1 bypass.
  1 = one+ check_clauses offences, or absence under CAIRN_CONTRACT_REQUIRED.
  2 = intent unreadable, malformed YAML, or a ``## Contract`` heading present
      but no parseable block (fail-closed backstop).

RED at HEAD: checks/atomicity_guard.py and scripts/lib/atomicity.py do not
exist, so every subprocess invocation fails (the gate is missing / cannot
import its lib) and no assertion on a 0/1/2 contract holds.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUARD = PROJECT_ROOT / "checks" / "atomicity_guard.py"


def _run(intent_path, project_dir, env_extra=None):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CAIRN_ATOMICITY_FIX", None)
    env.pop("CAIRN_CONTRACT_REQUIRED", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(GUARD), str(intent_path)],
        capture_output=True,
        text=True,
        env=env,
    )


def _contract_intent(tmp_path, yaml_body, intro="Intent body.\n\n"):
    intent = tmp_path / "intent.md"
    intent.write_text(f"# Intent\n\n{intro}## Contract\n\n```yaml\n{yaml_body}```\n")
    return intent


# ───────────────────────── exit 0 ─────────────────────────


def test_absent_contract_block_fail_open_exits_0_with_notice(tmp_path):
    intent = tmp_path / "intent.md"
    intent.write_text("# Intent\n\nNo contract block here.\n")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip()  # visible 'atomicity unchecked' notice (never silent)
    assert "unchecked" in r.stderr.lower() or "no contract" in r.stderr.lower()


def test_all_atomic_or_validly_tagged_exits_0(tmp_path):
    intent = _contract_intent(
        tmp_path,
        "must-satisfy:\n"
        "  - the parser returns the id string when present\n"
        "  - clause: every consumer receives the mirror\n"
        "    except: 'universal-set: the 3 repos in roadmap.md'\n"
        "  - clause: the dist mirror exists\n"
        "    except: trivial-existence\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_atomicity_fix_env_bypasses_exits_0(tmp_path):
    # A bare non-atomic clause that would otherwise exit 1 — CAIRN_ATOMICITY_FIX=1
    # bypasses with a one-line stderr notice (mirrors CAIRN_PREMISE_FIX).
    intent = _contract_intent(
        tmp_path,
        "must-satisfy:\n  - every consumer repository receives the mirror\n",
    )
    r = _run(intent, tmp_path, env_extra={"CAIRN_ATOMICITY_FIX": "1"})
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip()


# ───────────────────────── exit 1 ─────────────────────────


def test_bare_non_atomic_clause_exits_1(tmp_path):
    intent = _contract_intent(
        tmp_path,
        "must-satisfy:\n  - every consumer repository receives the mirror\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert (r.stdout + r.stderr).strip()


def test_unknown_tag_exits_1(tmp_path):
    intent = _contract_intent(
        tmp_path,
        "must-satisfy:\n"
        "  - clause: all repos get it\n"
        "    except: 'made-up-tag: whatever'\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout


def test_required_tag_empty_declaration_exits_1(tmp_path):
    intent = _contract_intent(
        tmp_path,
        "must-satisfy:\n"
        "  - clause: every consumer gets the mirror\n"
        "    except: 'universal-set:'\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout


def test_absent_block_under_contract_required_exits_1(tmp_path):
    intent = tmp_path / "intent.md"
    intent.write_text("# Intent\n\nNo contract block here.\n")
    r = _run(intent, tmp_path, env_extra={"CAIRN_CONTRACT_REQUIRED": "1"})
    assert r.returncode == 1, r.stdout
    assert (r.stdout + r.stderr).strip()


# ───────────────────────── exit 2 ─────────────────────────


def test_missing_intent_file_exits_2(tmp_path):
    r = _run(tmp_path / "nope.md", tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()


def test_malformed_yaml_block_exits_2(tmp_path):
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Contract\n\n"
        "```yaml\nmust-satisfy:\n  - clause: x\n   except: bad-indent\n```\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()
    assert "Traceback" not in r.stderr


def test_contract_heading_present_but_unparseable_exits_2(tmp_path):
    # FLI-2 fail-closed backstop: a '## Contract' heading with prose declaring
    # must-satisfy but yielding no extractable yaml block → exit 2, never a
    # silent fail-open.
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Contract\n\n"
        "must-satisfy: this section mentions must-satisfy but has no yaml fence.\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()
    assert "Traceback" not in r.stderr


# ───── silent-bypass hazards: each PAIRED (passes-0 AND non-atomic-fails-1) ─────
#
# Each hazard could let the fence extractor return None or truncate the block,
# silently dropping a real offence (fail OPEN). The paired test proves the
# hazard cannot swallow a genuine non-atomic clause: the clean variant exits 0
# and the offending variant still exits 1 (or 2 for the unparseable backstop).


# Hazard 1: a flush-left '## ' heading inside a fenced clause scalar.
def _heading_in_clause_intent(tmp_path, extra_clause):
    return _contract_intent(
        tmp_path,
        "must-satisfy:\n"
        "  - clause: |\n"
        "      the loader handles a quoted markdown heading\n"
        "## Not A Real Section\n"
        "    except: trivial-existence\n"
        f"{extra_clause}",
    )


def test_heading_in_clause_scalar_clean_exits_0(tmp_path):
    intent = _heading_in_clause_intent(tmp_path, "")
    r = _run(intent, tmp_path)
    assert r.returncode in (0, 2), r.stdout  # parsed-or-backstop, never silent 0-drop
    if r.returncode == 0:
        assert not r.stdout.strip() or "offence" not in r.stdout.lower()


def test_heading_in_clause_scalar_does_not_swallow_offence_exits_nonzero(tmp_path):
    # A real non-atomic clause BELOW the heading-bearing scalar must still be
    # reached and flagged — never silently dropped by truncation.
    intent = _heading_in_clause_intent(
        tmp_path, "  - every consumer repository receives the mirror\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode != 0, (
        f"hazard swallowed a real offence: silent fail-open. {r.stdout} {r.stderr}"
    )


# Hazard 2: a fenced code block inside a clause scalar (inner ``` at deeper indent).
def _fenced_code_in_clause_intent(tmp_path, extra_clause):
    return _contract_intent(
        tmp_path,
        "must-satisfy:\n"
        "  - clause: |\n"
        "      the doc shows the snippet\n"
        "      ```python\n"
        "      x = 1\n"
        "      ```\n"
        "    except: trivial-existence\n"
        f"{extra_clause}",
    )


def test_fenced_code_in_clause_clean_exits_0(tmp_path):
    intent = _fenced_code_in_clause_intent(tmp_path, "")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_fenced_code_in_clause_does_not_drop_offence_exits_1(tmp_path):
    # The inner ``` must NOT truncate the yaml block — the fabricated non-atomic
    # clause after it has to be reached and DENIED (exit 1), not silently 0.
    intent = _fenced_code_in_clause_intent(
        tmp_path, "  - every consumer repository receives the mirror\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, f"inner fence truncated the block: {r.stdout} {r.stderr}"


# Hazard 3: a non-yaml fence appearing BEFORE the real yaml Contract block.
def _nonyaml_fence_before_yaml_intent(tmp_path, clause):
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Contract\n\n"
        "```text\nillustrative example, not the contract block\n```\n\n"
        "```yaml\n"
        f"must-satisfy:\n  - {clause}\n"
        "```\n"
    )
    return intent


def test_nonyaml_fence_before_yaml_clean_exits_0(tmp_path):
    intent = _nonyaml_fence_before_yaml_intent(
        tmp_path, "the parser returns the id string when present"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_nonyaml_fence_before_yaml_still_flags_offence_exits_1(tmp_path):
    # The state machine must use the real yaml block, not the ```text one — a
    # non-atomic clause in it must still be DENIED (exit 1).
    intent = _nonyaml_fence_before_yaml_intent(
        tmp_path, "every consumer repository receives the mirror"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, f"wrong block extracted / offence dropped: {r.stdout}"


# Hazard 4: a stray unbalanced bare fence before the real yaml block.
def _stray_fence_intent(tmp_path, clause):
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Contract\n\n"
        "```\nleftover\n```yaml\n"
        f"must-satisfy:\n  - {clause}\n"
        "```\n"
    )
    return intent


def test_stray_fence_clean_does_not_silently_pass(tmp_path):
    # An all-atomic body behind a stray fence must NOT silently fail-open as a
    # clean 0 by dropping the block: either the block extracts (0) or the
    # backstop fires (2) — never a silent drop of an authored must-satisfy.
    intent = _stray_fence_intent(
        tmp_path, "the parser returns the id string when present"
    )
    r = _run(intent, tmp_path)
    assert r.returncode in (0, 2), r.stdout


def test_stray_fence_does_not_swallow_offence(tmp_path):
    # With a real non-atomic clause behind the stray fence, the gate must NOT
    # exit 0: the offence is either flagged (1) or the backstop fires (2).
    intent = _stray_fence_intent(
        tmp_path, "every consumer repository receives the mirror"
    )
    r = _run(intent, tmp_path)
    assert r.returncode != 0, (
        f"stray fence swallowed an authored offence: silent fail-open. "
        f"{r.stdout} {r.stderr}"
    )
    assert "Traceback" not in r.stderr

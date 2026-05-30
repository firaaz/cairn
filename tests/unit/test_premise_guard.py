"""CLI exit-code contract for checks/premise_guard.py (Slice 2, Trial C).

The gate diffs an intent's verbatim source-quotes against live source and blocks
Phase-2 dispatch on a stale/fabricated/missing premise. Exercised end-to-end via
subprocess against real exit codes — no mocks (FLI-1: the gate and the validator
assertion must route through the same lib.premise_match.grounded, so faking the
matcher would hide divergence). The slice-#25 re-probe reproduces the wrong-model
pattern: a docstring-style premise whose claim contradicts the live source body.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUARD = PROJECT_ROOT / "checks" / "premise_guard.py"


def _run(intent_path, project_dir, env_extra=None):
    import os

    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CAIRN_PREMISE_FIX", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(GUARD), str(intent_path)],
        capture_output=True,
        text=True,
        env=env,
    )


def _intent(body):
    return body


def _premise_intent(tmp_path, yaml_body, intro="Intent body.\n\n"):
    intent = tmp_path / "intent.md"
    intent.write_text(
        f"# Intent\n\n{intro}## Premise Grounding\n\n```yaml\n{yaml_body}```\n"
    )
    return intent


# ───────────────────────── exit 0 ─────────────────────────


def test_all_grounded_exits_0(tmp_path):
    (tmp_path / "src.py").write_text("def resolve_root():\n    return Path.cwd()\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: src.py\n    quote: |\n      def resolve_root():\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_absent_section_exits_0(tmp_path):
    intent = tmp_path / "intent.md"
    intent.write_text("# Intent\n\nNo premise grounding section here.\n")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_empty_premises_exits_0(tmp_path):
    intent = _premise_intent(tmp_path, "premises: []\n")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_premise_fix_env_bypasses_exits_0(tmp_path):
    # A stale premise that would otherwise exit 1 — CAIRN_PREMISE_FIX=1 bypasses.
    (tmp_path / "src.py").write_text("def other():\n    pass\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: src.py\n    quote: |\n      def resolve_root():\n",
    )
    r = _run(intent, tmp_path, env_extra={"CAIRN_PREMISE_FIX": "1"})
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip()  # one-line bypass notice on stderr


# ───────────────────────── exit 1 ─────────────────────────


def test_stale_quote_exits_1(tmp_path):
    (tmp_path / "src.py").write_text("def resolve_root(start):\n    return start\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: src.py\n    quote: |\n      def resolve_root():\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "src.py" in r.stderr


def test_fabricated_quote_exits_1(tmp_path):
    (tmp_path / "src.py").write_text("ALPHA = 1\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: src.py\n    quote: |\n      NEVER_WRITTEN = 42\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "src.py" in r.stderr


def test_missing_source_exits_1(tmp_path):
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: gone.py\n    quote: anything\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "gone.py" in r.stderr
    assert "not found" in r.stderr


def test_unreadable_source_exits_1(tmp_path):
    # A directory at the cited path raises OSError on read_text → unreadable.
    (tmp_path / "adir").mkdir()
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: adir\n    quote: anything\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "adir" in r.stderr
    assert "unreadable" in r.stderr


def test_multi_premise_one_stale_exits_1(tmp_path):
    (tmp_path / "a.py").write_text("ALPHA = 1\n")
    (tmp_path / "b.py").write_text("BETA = 2\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n"
        "  - source: a.py\n    quote: ALPHA = 1\n"
        "  - source: b.py\n    quote: BETA = 99\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "b.py" in r.stderr
    assert "a.py" not in r.stderr  # only the stale premise is reported


# ───────────────────────── exit 2 ─────────────────────────


def test_missing_intent_file_exits_2(tmp_path):
    r = _run(tmp_path / "nope.md", tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()


def test_malformed_yaml_block_exits_2(tmp_path):
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Premise Grounding\n\n"
        "```yaml\npremises:\n  - source: x.py\n   quote: bad-indent\n```\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()


def test_non_string_quote_exits_2(tmp_path):
    # A parseable-but-malformed premise: quote is an int → clean exit 2, not a
    # raw AttributeError traceback from normalize(42, ext).
    (tmp_path / "src.py").write_text("ALPHA = 1\n")
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: src.py\n    quote: 42\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()
    assert "Traceback" not in r.stderr


def test_non_string_source_exits_2(tmp_path):
    # source as a YAML list → clean exit 2, not a crash at PROJECT_ROOT / source.
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source:\n      - a.py\n    quote: anything\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()
    assert "Traceback" not in r.stderr


def test_bad_args_exits_2(tmp_path):
    import os

    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    env.pop("CAIRN_PREMISE_FIX", None)
    r = subprocess.run(
        [sys.executable, str(GUARD)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()


# ─────────────── slice-#25 wrong-premise re-probe ───────────────


# The slice-#25 pattern: an intent's premise asserts existing source does X, but
# the live source only does Y. The literal M4-era files are gone, so reproduce
# the PATTERN — a docstring-style premise contradicted by the function body.
_CORRECTED_SOURCE = '''\
def project_root():
    """Resolve repo root for sys.path injection only."""
    import sys
    sys.path.insert(0, "..")
'''


def test_slice25_wrong_premise_exits_1(tmp_path):
    # The intent's premise quotes a docstring claiming "and DB/corpus paths", but
    # the live source body only injects sys.path → premise no longer grounded.
    (tmp_path / "root.py").write_text(_CORRECTED_SOURCE)
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: root.py\n    quote: |\n"
        '      """Resolve repo root for sys.path injection and DB/corpus paths."""\n',
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "root.py" in r.stderr


def test_slice25_corrected_premise_exits_0(tmp_path):
    (tmp_path / "root.py").write_text(_CORRECTED_SOURCE)
    intent = _premise_intent(
        tmp_path,
        "premises:\n  - source: root.py\n    quote: |\n"
        '      """Resolve repo root for sys.path injection only."""\n',
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


# ───────── fail-open regression: '## ' inside the fenced block ─────────


# A markdown heading pasted flush-left inside the fence (here a `## ` line above
# the premise it documents) is a column-0 line. The pre-fix extractor pre-truncated
# the section body at the next `## `, so the closing fence fell outside the body,
# the fence regex missed, the function returned None — and the gate silently failed
# OPEN (exit 0), dropping the real, checkable premise below the heading line.
def _heading_in_fence_intent(tmp_path, source_name):
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Premise Grounding\n\n```yaml\n"
        "premises:\n"
        "## Architecture Decision\n"
        f"- source: {source_name}\n"
        "  quote: |\n"
        "    ## Architecture Decision\n"
        "```\n"
    )
    return intent


def test_heading_in_fence_grounded_exits_0(tmp_path):
    # The quoted markdown heading is genuinely present in the cited .md source:
    # the premise is parsed and grounded (exit 0), NOT silently dropped.
    (tmp_path / "doc.md").write_text("# Doc\n\n## Architecture Decision\n\nbody\n")
    intent = _heading_in_fence_intent(tmp_path, "doc.md")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_heading_in_fence_stale_exits_1(tmp_path):
    # Same quoted heading, but the live .md no longer contains it → the gate must
    # parse, check, and DENY (exit 1) — never fail open by dropping the premise.
    (tmp_path / "doc.md").write_text("# Doc\n\n## Different Decision\n\nbody\n")
    intent = _heading_in_fence_intent(tmp_path, "doc.md")
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "doc.md" in r.stderr


# ───── fail-open regression: fenced code block inside a quote scalar ─────


# A `quote: |` block scalar that quotes a fenced code block contains bare ``` lines
# at a DEEPER indent than the outer ```yaml fence. The pre-fix extractor closed on
# the first inner ```, truncating the YAML mid-block — silently dropping every
# premise below it (fail OPEN, exit 0) or grounding a stale quote on a prefix. The
# fence state machine treats deeper-indented ``` lines as body, not a close.
def _fenced_code_in_quote_intent(tmp_path, premises_body):
    intent = tmp_path / "intent.md"
    intent.write_text(
        f"# Intent\n\n## Premise Grounding\n\n```yaml\n{premises_body}```\n"
    )
    return intent


def test_fenced_code_in_quote_does_not_drop_premises(tmp_path):
    # First premise quotes a fenced python block genuinely in design.md; the second
    # premise is fabricated. The inner ``` lines must NOT truncate the block — the
    # fabricated second premise has to be reached and DENIED (exit 1), not silently 0.
    (tmp_path / "design.md").write_text("# Design\n\n```python\nreal = 1\n```\n")
    (tmp_path / "b.py").write_text("ACTUAL = 99\n")
    intent = _fenced_code_in_quote_intent(
        tmp_path,
        "premises:\n"
        "  - source: design.md\n"
        "    quote: |\n"
        "      ```python\n"
        "      real = 1\n"
        "      ```\n"
        "  - source: b.py\n"
        "    quote: FABRICATED_NEVER_IN_SOURCE = 42\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "b.py" in r.stderr


def test_fenced_code_in_quote_grounds_when_present(tmp_path):
    # A single premise quoting a fenced code block that genuinely exists in the .md
    # source: the block is extracted whole, the quote is grounded → exit 0.
    (tmp_path / "design.md").write_text("# Design\n\n```python\nreal = 1\n```\n")
    intent = _fenced_code_in_quote_intent(
        tmp_path,
        "premises:\n"
        "  - source: design.md\n"
        "    quote: |\n"
        "      ```python\n"
        "      real = 1\n"
        "      ```\n",
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_yaml_block_after_non_yaml_fence(tmp_path):
    # A ```text example fence precedes the real ```yaml premise block. The state
    # machine skips the non-yaml fence and uses the real one — a stale premise in
    # it must still be DENIED (exit 1), proving the right block was extracted.
    (tmp_path / "src.py").write_text("ALPHA = 1\n")
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Premise Grounding\n\n"
        "```text\nthis is an illustrative example, not the premise block\n```\n\n"
        "```yaml\n"
        "premises:\n  - source: src.py\n    quote: STALE_NOT_PRESENT = 7\n"
        "```\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "src.py" in r.stderr


# ── fail-closed backstop: premises authored but no extractable yaml block ──


# A stray/unbalanced bare ``` fence in the section prose BEFORE the real ```yaml
# acts as a phantom (empty-info) opener: its bare close matches the real block's
# closing fence, swallowing it as body, so _extract_premise_block returns None and
# the gate would silently fail OPEN despite an authored `premises:` block. The
# backstop fires on extraction-None + a `premises:` key in the section → exit 2.
def test_stray_fence_before_yaml_exits_2(tmp_path):
    (tmp_path / "a.py").write_text("ACTUAL = 99\n")
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Premise Grounding\n\n"
        "```\nleftover\n```yaml\n"
        "premises:\n  - source: a.py\n    quote: FABRICATED = 1\n"
        "```\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 2, r.stdout
    assert r.stderr.strip()
    assert "Traceback" not in r.stderr


def test_section_prose_only_no_premises_exits_0(tmp_path):
    # A '## Premise Grounding' section with only prose and no `premises:` key is
    # genuine absence (the operator made no source-behaviour claim) → exit 0.
    intent = tmp_path / "intent.md"
    intent.write_text(
        "# Intent\n\n## Premise Grounding\n\n"
        "This intent makes no verbatim source claims.\n"
    )
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr


def test_empty_premises_list_does_not_trip_backstop_exits_0(tmp_path):
    # A valid block IS extracted and yields `premises: []` — the backstop only fires
    # when extraction returned None, so the empty-but-valid path stays exit 0.
    intent = _premise_intent(tmp_path, "premises: []\n")
    r = _run(intent, tmp_path)
    assert r.returncode == 0, r.stderr

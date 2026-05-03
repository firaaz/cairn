"""Phase 2 RED — compression/upgrade-doc-bug-fixes.

Asserts the seven verification checks from
``.claude/current-slice/intent.md`` §Verification against
``docs/upgrading-from-pre-compression.md``:

  1. Delta-1 prose: bad path ``scripts/role-cheatsheet.sh`` is absent.
  2. Delta-1 prose: corrected path ``checks/role-cheatsheet.sh`` appears
     in at least two locations.
  3. Delta-2 §2 JSON config: bare ``"command": "python"`` is gone.
  4. Delta-2 §2 JSON config: corrected ``"command": "uv"`` with the
     exact args list is present.
  5. Delta-1 Verify snippet runtime-invokes successfully (rc=0, first
     stdout line parses as JSON).
  6. Delta-2 Verify snippet runtime-invokes successfully (rc=0).
  7. Deltas 3/4/5 verify-section bytes are unchanged (SHA-256 baseline
     pinned at slice open against the current pre-fix doc).

Tests 1-6 are RED at Phase 2 (the doc still has the unfixed bugs).
Test 7 is GREEN at Phase 2 by construction (baseline captured against
the current bytes); it turns RED only if Phase 3 accidentally edits
sections it must not touch.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = CAIRN_ROOT / "docs" / "upgrading-from-pre-compression.md"

# Pinned at slice open (Phase 2, 2026-05-02) against the current bytes of
# `docs/upgrading-from-pre-compression.md` from `## 3. Python dependencies`
# through end-of-file. Any future edit to Deltas 3/4/5 will fail Test 7,
# forcing the change to be intentional (per intent §Verification item 7).
DELTAS_3_4_5_SHA256 = "b136326efbe6be623e0c95df02cfe7c1e2cfcb77e04b3a715fea608ce9743d2b"
DELTAS_3_4_5_MARKER = b"## 3. Python dependencies"


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _section(heading_prefix: str) -> str:
    """Return the text of the H2 section whose heading line starts with
    ``heading_prefix`` (e.g. ``"## 1."``), bounded by the next H2 heading or
    EOF."""
    text = _doc_text()
    pattern = re.compile(
        rf"^{re.escape(heading_prefix)}.*?(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(text)
    assert match, f"could not locate section starting with {heading_prefix!r}"
    return match.group(0)


def _first_fenced_block(section_text: str, lang: str) -> str:
    """Return the contents of the first ```<lang> ... ``` block in section."""
    pattern = re.compile(
        rf"```{re.escape(lang)}\n(.*?)\n```",
        re.DOTALL,
    )
    match = pattern.search(section_text)
    assert match, f"no ```{lang} block found in section"
    return match.group(1)


def _verify_snippet(section_text: str) -> str:
    """Extract the bash command between the ``**Verify:**`` heading and the
    next ``---`` rule, returning the trimmed shell command body."""
    after_verify_idx = section_text.find("**Verify:**")
    assert after_verify_idx != -1, "no **Verify:** heading in section"
    next_hr_idx = section_text.find("\n---", after_verify_idx)
    assert next_hr_idx != -1, "no `---` rule after **Verify:** in section"
    region = section_text[after_verify_idx:next_hr_idx]
    return _first_fenced_block(region, "sh").strip()


# ---------------------------------------------------------------------------
# Test 1 — Delta 1 prose corrected (bad path absent)
# ---------------------------------------------------------------------------


def test_delta1_bad_path_absent():
    """intent §Verification 1 — `scripts/role-cheatsheet.sh` MUST NOT appear
    anywhere in the upgrade doc (the authoritative path is `checks/`)."""
    matches = re.findall(r"scripts/role-cheatsheet\.sh", _doc_text())
    assert matches == [], (
        "intent §Verification 1 — found `scripts/role-cheatsheet.sh` "
        f"({len(matches)} occurrence(s)); doc must use `checks/` path. "
        "Pre-fix RED: matches the bullet at §1 line ~30 and the paragraph "
        "at §1 line ~36."
    )


# ---------------------------------------------------------------------------
# Test 2 — Delta 1 prose corrected (good path present, ≥2 occurrences)
# ---------------------------------------------------------------------------


def test_delta1_good_path_present_at_least_twice():
    """intent §Verification 2 — `checks/role-cheatsheet.sh` MUST appear in
    at least two places (one in §1 prose, one in the §1 paragraph beneath
    the bullets)."""
    matches = re.findall(r"checks/role-cheatsheet\.sh", _doc_text())
    assert len(matches) >= 2, (
        "intent §Verification 2 — `checks/role-cheatsheet.sh` must appear "
        f">= 2 times; found {len(matches)}. Pre-fix RED: doc still uses "
        "`scripts/role-cheatsheet.sh` in those locations."
    )


# ---------------------------------------------------------------------------
# Test 3 — Delta 2 prose corrected (bare `python` MCP command absent)
# ---------------------------------------------------------------------------


def _section_2_mcp_config() -> dict:
    """Parse the first ```json fenced block in §2 as a dict."""
    section = _section("## 2.")
    raw = _first_fenced_block(section, "json")
    return json.loads(raw)


def test_delta2_bare_python_command_eliminated():
    """intent §Verification 3 — the §2 JSON example MUST NOT register the
    cairn-knowledge MCP server with `command: "python"` and args invoking
    the package by `-m mcp_servers.cairn_knowledge` (bare `python` is not
    on PATH inside Claude Code's MCP subprocess environment)."""
    config = _section_2_mcp_config()
    entry = config.get("mcpServers", {}).get("cairn-knowledge", {})
    is_bare_python = entry.get("command") == "python" and (
        "-m" in entry.get("args", [])
        and "mcp_servers.cairn_knowledge" in entry.get("args", [])
    )
    assert not is_bare_python, (
        "intent §Verification 3 — §2 JSON config still uses bare "
        f'`"command": "python"` with args {entry.get("args")!r}. '
        "Pre-fix RED: the doc has not been corrected yet."
    )


# ---------------------------------------------------------------------------
# Test 4 — Delta 2 prose corrected (uv command present, exact args)
# ---------------------------------------------------------------------------


def test_delta2_uv_command_present_with_exact_args():
    """intent §Verification 4 — the §2 JSON example MUST register the
    server via `command: "uv"` with the exact args list, in order:
    `["run", "--directory", ".slice-system", "python", "-m",
    "mcp_servers.cairn_knowledge"]`."""
    config = _section_2_mcp_config()
    entry = config.get("mcpServers", {}).get("cairn-knowledge", {})
    expected_args = [
        "run",
        "--directory",
        ".slice-system",
        "python",
        "-m",
        "mcp_servers.cairn_knowledge",
    ]
    assert entry.get("command") == "uv", (
        "intent §Verification 4 — §2 JSON config must have "
        f'`"command": "uv"`; got {entry.get("command")!r}.'
    )
    assert entry.get("args") == expected_args, (
        "intent §Verification 4 — §2 JSON config args mismatch.\n"
        f"  expected: {expected_args!r}\n"
        f"  got:      {entry.get('args')!r}"
    )


# ---------------------------------------------------------------------------
# Test 5 — §1 Verify snippet runtime-invokes
# ---------------------------------------------------------------------------


DELTA1_CORRECTED_SNIPPET = (
    "bash .slice-system/checks/role-cheatsheet.sh </dev/null | head -1"
)


def test_delta1_verify_snippet_runtime_invokes():
    """intent §Verification 5 — the §1 Verify snippet MUST (a) be the
    corrected form documented in intent.md §Specification Detail (the old
    structural-only ``jq -e ...`` snippet must be gone) AND (b) run
    cleanly (rc=0) with a first stdout line that parses as JSON.

    The text-equality leg discriminates the bug inside cairn itself
    (cairn dogfoods its own hooks, so the OLD ``jq`` snippet returns rc=0
    with a JSON-parseable line — runtime-invocation alone cannot tell
    fixed from unfixed in this environment). See approach.md
    §Ambiguity-Resolution for context."""
    snippet = _verify_snippet(_section("## 1."))
    assert snippet == DELTA1_CORRECTED_SNIPPET, (
        "intent §Verification 5 — §1 Verify snippet text mismatch.\n"
        f"  expected: {DELTA1_CORRECTED_SNIPPET!r}\n"
        f"  got:      {snippet!r}\n"
        "Pre-fix RED: doc still has the structural-only `jq -e ...` form."
    )
    result = subprocess.run(
        snippet,
        shell=True,
        capture_output=True,
        cwd=CAIRN_ROOT,
        text=True,
    )
    assert result.returncode == 0, (
        "intent §Verification 5 — §1 Verify snippet failed.\n"
        f"  snippet:    {snippet!r}\n"
        f"  returncode: {result.returncode}\n"
        f"  stdout:     {result.stdout!r}\n"
        f"  stderr:     {result.stderr!r}"
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    try:
        json.loads(first_line)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "intent §Verification 5 — §1 Verify snippet stdout first line "
            f"does not parse as JSON: {first_line!r} ({exc})"
        ) from exc


# ---------------------------------------------------------------------------
# Test 6 — §2 Verify snippet runtime-invokes
# ---------------------------------------------------------------------------


DELTA2_CORRECTED_SNIPPET = (
    'uv run --directory .slice-system python -c "import mcp_servers.cairn_knowledge"'
)


def test_delta2_verify_snippet_runtime_invokes():
    """intent §Verification 6 — the §2 Verify snippet MUST (a) be the
    corrected form documented in intent.md §Specification Detail (the old
    structural-only ``jq -e ...`` snippet must be gone) AND (b) run
    cleanly (rc=0).

    The text-equality leg discriminates the bug inside cairn itself
    (cairn dogfoods its own MCP wiring, so the OLD ``jq`` snippet returns
    rc=0 — runtime-invocation alone cannot tell fixed from unfixed in
    this environment). See approach.md §Ambiguity-Resolution for
    context."""
    snippet = _verify_snippet(_section("## 2."))
    assert snippet == DELTA2_CORRECTED_SNIPPET, (
        "intent §Verification 6 — §2 Verify snippet text mismatch.\n"
        f"  expected: {DELTA2_CORRECTED_SNIPPET!r}\n"
        f"  got:      {snippet!r}\n"
        "Pre-fix RED: doc still has the structural-only `jq -e ...` form."
    )
    result = subprocess.run(
        snippet,
        shell=True,
        capture_output=True,
        cwd=CAIRN_ROOT,
        text=True,
    )
    assert result.returncode == 0, (
        "intent §Verification 6 — §2 Verify snippet failed.\n"
        f"  snippet:    {snippet!r}\n"
        f"  returncode: {result.returncode}\n"
        f"  stdout:     {result.stdout!r}\n"
        f"  stderr:     {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Test 7 — Deltas 3/4/5 unchanged (SHA-256 baseline pin)
# ---------------------------------------------------------------------------


def test_deltas_3_4_5_bytes_unchanged():
    """intent §Verification 7 — bytes from `## 3. Python dependencies`
    through EOF MUST hash to the baseline pinned at slice open. Any
    accidental edit to Deltas 3/4/5 by Phase 3 will trip this."""
    data = DOC_PATH.read_bytes()
    idx = data.find(DELTAS_3_4_5_MARKER)
    assert idx != -1, (
        f"could not find marker {DELTAS_3_4_5_MARKER!r} in "
        f"{DOC_PATH}; doc structure has changed unexpectedly."
    )
    chunk = data[idx:]
    actual = hashlib.sha256(chunk).hexdigest()
    assert actual == DELTAS_3_4_5_SHA256, (
        "intent §Verification 7 — Deltas 3/4/5 byte-range hash drifted.\n"
        f"  expected: {DELTAS_3_4_5_SHA256}\n"
        f"  actual:   {actual}\n"
        f"  bytes:    {len(chunk)} (from byte {idx})\n"
        "Phase 3 must not edit Deltas 3/4/5; if an edit is intentional, "
        "re-pin the baseline in this test in a separate commit."
    )

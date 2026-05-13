"""Trial A: .claude/handoff.md must conform to a frontmatter contract.

See docs/plans/2026-05-13-cairn-as-interaction-protocol.md §Trial A.

The handoff is agent-to-agent communication: the outgoing session emits
pointer-only entries; the incoming session reads them without needing
narrative summary. This test enforces the contract.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HANDOFF = CAIRN_ROOT / ".claude" / "handoff.md"

POINTER_GH = re.compile(r"^gh:[\w.-]+/[\w.-]+#(\d+)\b")
POINTER_FILE = re.compile(r"^(docs/[\w/.-]+\.md)\b")
POINTER_COMMIT = re.compile(r"^([0-9a-f]{7,40})\b")
STATE_KEYWORD = re.compile(r"\b(open|blocked|deferred)\b")


def _parse_handoff(text: str) -> tuple[dict, list[str], str]:
    """Split YAML frontmatter from body. Return (frontmatter, body_lines, body_raw)."""
    if not text.startswith("---\n"):
        raise ValueError("handoff: missing leading frontmatter marker")
    rest = text[4:]
    end = rest.find("\n---\n")
    if end < 0:
        raise ValueError("handoff: missing frontmatter closing ---")
    front = yaml.safe_load(rest[:end])
    body_raw = rest[end + 5 :]
    body_lines = [ln for ln in body_raw.splitlines() if ln.strip()]
    return front, body_lines, body_raw


def _entry_text(line: str) -> str:
    """Strip leading bullet marker."""
    return re.sub(r"^[-*]\s+", "", line).strip()


# ---------------------------------------------------------------------------
# Test 1: contract block present and well-formed
# ---------------------------------------------------------------------------


def test_frontmatter_contract_present():
    front, _, _ = _parse_handoff(HANDOFF.read_text())
    assert "contract" in front, "handoff frontmatter missing `contract:` key"
    contract = front["contract"]
    for required in ("must-satisfy", "must-not-violate", "wrong-if", "evidence"):
        assert required in contract, f"contract missing `{required}`"


# ---------------------------------------------------------------------------
# Test 2: no narrative prose
# ---------------------------------------------------------------------------


def test_no_narrative_prose():
    text = HANDOFF.read_text()
    _, body, body_raw = _parse_handoff(text)
    for line in body:
        assert len(line) <= 120, f"body line too long ({len(line)} chars): {line!r}"
        if re.search(r"\.\s+[A-Z]", line):
            pytest.fail(f"multi-sentence body line (prose smell): {line!r}")
    blocks = [b for b in body_raw.strip().split("\n\n") if b.strip()]
    assert len(blocks) == 1, (
        f"body has {len(blocks)} paragraph blocks; expected one continuous "
        f"bullet list (no blank-line separators)"
    )


# ---------------------------------------------------------------------------
# Test 3: pointers resolve
# ---------------------------------------------------------------------------


def _resolve_gh(num: str) -> bool:
    r = subprocess.run(
        ["gh", "issue", "view", num, "--json", "number"],
        capture_output=True,
        cwd=CAIRN_ROOT,
    )
    if r.returncode == 0:
        return True
    r = subprocess.run(
        ["gh", "pr", "view", num, "--json", "number"],
        capture_output=True,
        cwd=CAIRN_ROOT,
    )
    return r.returncode == 0


def _resolve_file(path: str) -> bool:
    return (CAIRN_ROOT / path).exists()


def _resolve_commit(sha: str) -> bool:
    r = subprocess.run(
        ["git", "cat-file", "-e", sha],
        capture_output=True,
        cwd=CAIRN_ROOT,
    )
    return r.returncode == 0


def test_pointers_resolve():
    _, body, _ = _parse_handoff(HANDOFF.read_text())
    for line in body:
        entry = _entry_text(line)
        if m := POINTER_GH.match(entry):
            assert _resolve_gh(m.group(1)), f"gh:#{m.group(1)} does not resolve"
        elif m := POINTER_FILE.match(entry):
            assert _resolve_file(m.group(1)), f"file {m.group(1)} does not exist"
        elif m := POINTER_COMMIT.match(entry):
            assert _resolve_commit(m.group(1)), f"commit {m.group(1)} not reachable"
        else:
            pytest.fail(f"line has no recognized pointer: {line!r}")
        assert STATE_KEYWORD.search(line), (
            f"line missing state keyword (open|blocked|deferred): {line!r}"
        )


# ---------------------------------------------------------------------------
# Test 4: coverage — every open GH issue appears
# ---------------------------------------------------------------------------


def _live_open_issues() -> set[int]:
    r = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--json",
            "number",
            "--limit",
            "200",
        ],
        capture_output=True,
        text=True,
        cwd=CAIRN_ROOT,
    )
    assert r.returncode == 0, f"gh issue list failed: {r.stderr}"
    return {item["number"] for item in json.loads(r.stdout)}


def _handoff_gh_pointers() -> set[int]:
    _, body, _ = _parse_handoff(HANDOFF.read_text())
    out = set()
    for line in body:
        if m := POINTER_GH.search(_entry_text(line)):
            out.add(int(m.group(1)))
    return out


def test_coverage_open_issues():
    open_issues = _live_open_issues()
    in_handoff = _handoff_gh_pointers()
    missing = open_issues - in_handoff
    assert not missing, (
        f"open GitHub issues not represented in handoff: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Test 5: coverage — every provisional ADR appears
# ---------------------------------------------------------------------------


def _provisional_adrs() -> set[str]:
    adr_dir = CAIRN_ROOT / "docs" / "adr"
    if not adr_dir.exists():
        return set()
    result = set()
    for f in sorted(adr_dir.glob("*.md")):
        text = f.read_text()
        if not text.startswith("---\n"):
            continue
        rest = text[4:]
        end = rest.find("\n---\n")
        if end < 0:
            continue
        front = rest[:end]
        for line in front.splitlines():
            if line.startswith("status:") and "provisional" in line:
                result.add(f.name)
                break
    return result


def _handoff_adr_pointers() -> set[str]:
    _, body, _ = _parse_handoff(HANDOFF.read_text())
    pat = re.compile(r"docs/adr/([\w.-]+\.md)")
    out = set()
    for line in body:
        if m := pat.search(line):
            out.add(m.group(1))
    return out


def test_coverage_provisional_adrs():
    provisional = _provisional_adrs()
    in_handoff = _handoff_adr_pointers()
    missing = provisional - in_handoff
    assert not missing, (
        f"provisional ADRs not represented in handoff: {sorted(missing)}"
    )

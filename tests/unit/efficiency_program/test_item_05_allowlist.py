"""Phase 2 validation for efficiency-program/all-seven Item 5 — Tier-1 read-only allowlist.

Verifies intent.md Item 5 acceptance:
  - jq '.permissions.allow | length' .claude/settings.json  >= 10
  - jq -r '.permissions.allow[]' must contain all ten explicitly-required
    patterns from the spec.
  - No entry matches ^Bash\\((python3|uv run)\\s\\*\\)$  (no broad-wildcard
    language/tool entries).

RED phase: .claude/settings.json currently has no `permissions.allow` list.
Pytest + stdlib only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"

REQUIRED_PATTERNS = (
    "Bash(sed -n *)",
    "Bash(awk *)",
    "Bash(git diff *)",
    "Bash(git show *)",
    "Bash(git log *)",
    "Bash(git status *)",
    "Bash(uv run pytest *)",
    "Bash(uv run ruff *)",
    "Bash(shellcheck *)",
    "Bash(jq *)",
)

FORBIDDEN_WILDCARD_RE = re.compile(r"^Bash\((python3|uv run)\s\*\)$")


def _allowlist() -> list[str]:
    data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    permissions = data.get("permissions")
    assert permissions is not None, (
        ".claude/settings.json must define a top-level `permissions` object "
        "(intent Item 5)"
    )
    allow = permissions.get("allow")
    assert allow is not None, (
        ".claude/settings.json `permissions` must include an `allow` list"
    )
    assert isinstance(allow, list), (
        "`permissions.allow` must be a JSON array of strings"
    )
    return allow


class TestAllowlistShape:
    def test_allowlist_has_ten_or_more_entries(self):
        allow = _allowlist()
        assert len(allow) >= 10, (
            f"permissions.allow must carry >=10 entries (got {len(allow)})"
        )

    def test_all_required_patterns_present(self):
        allow = _allowlist()
        missing = [p for p in REQUIRED_PATTERNS if p not in allow]
        assert missing == [], f"permissions.allow missing required patterns: {missing}"

    def test_no_broad_wildcards(self):
        allow = _allowlist()
        violations = [p for p in allow if FORBIDDEN_WILDCARD_RE.match(p)]
        assert violations == [], (
            f"permissions.allow contains forbidden broad-wildcard entries: "
            f"{violations} (intent Item 5: deliberately specific, no "
            f"unrestricted python3 * / uv run *)"
        )

    def test_entries_are_strings(self):
        allow = _allowlist()
        non_strings = [e for e in allow if not isinstance(e, str)]
        assert non_strings == [], (
            f"permissions.allow entries must be strings; got non-strings: {non_strings}"
        )

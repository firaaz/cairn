"""Schema-shape lint for `.claude-plugin/marketplace.json`.

Pins (per ADR `plugin-payload-transport-a1` D4, superseding
`marketplace-source-url-amend` D7-revised after V-3 attempt 3 confirmed
the `sha:` shape works empirically and the `ref:` shape was falsified):

1. `plugins[0].source.source == "url"`                       [retained]
2. `plugins[0].source.url == "https://github.com/firaaz/cairn.git"` [retained]
3. `plugins[0].source.sha` matches `^[0-9a-f]{40}$`          [NEW; replaces ref]
4. `"ref" not in plugins[0].source`                          [NEW defensive]
5. `"version" not in plugins[0]`                             [retained]
6. `"type" not in plugins[0].source`                         [retained]

The `ref:` field's absence is load-bearing: re-introducing it routes
Claude Code's resolver back through the broken `case 'github':` SSH-clone
code path that falsified V-3 attempts 1+2. The `sha:` shape (which 82/82
of Anthropic's `claude-plugins-official` `url`-source plugins use) takes
a fetch-by-commit branch over HTTPS and bypasses the SSH-coercion bug.
See `docs/adr/plugin-payload-transport-a1.md` and
`.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md`
2026-05-12 closure block for the empirical record.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _load_first_plugin() -> dict:
    data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    plugins = data["plugins"]
    assert plugins, "marketplace.json must declare at least one plugin entry"
    return plugins[0]


def test_marketplace_source_source_is_url() -> None:
    """plugin-payload-transport-a1/D1 — source discriminator is the literal 'url'."""
    plugin = _load_first_plugin()
    assert plugin["source"]["source"] == "url"


def test_marketplace_source_url_is_https_cairn_git() -> None:
    """plugin-payload-transport-a1/D1 — explicit HTTPS URL.

    The `url` field is preserved as the canonical HTTPS form to match
    Anthropic-marketplace convention; the `sha:` pinning is what actually
    gates the resolver branch (not the URL scheme), but the literal HTTPS
    form is documentation for human readers.
    """
    plugin = _load_first_plugin()
    assert plugin["source"]["url"] == "https://github.com/firaaz/cairn.git"


def test_marketplace_source_sha_is_40_hex() -> None:
    """plugin-payload-transport-a1/D1 + D4 — sha pins consumer install to a release HEAD.

    The 40-char hex SHA is the load-bearing field for A1's transport
    bypass: Claude Code's resolver, given `url`-source + `sha:`, takes a
    fetch-by-commit branch over HTTPS that does not enter the
    `case 'github':` SSH-coercion path (V-3 attempt 3 empirical
    confirmation, M7 close commit 3df4a53).
    """
    plugin = _load_first_plugin()
    sha = plugin["source"].get("sha")
    assert isinstance(sha, str), (
        f"source.sha must be a string, got {type(sha).__name__}"
    )
    assert _SHA_RE.match(sha), (
        f"source.sha must match ^[0-9a-f]{{40}}$ (40-char lowercase hex commit SHA); "
        f"got {sha!r}"
    )


def test_marketplace_source_omits_ref_field() -> None:
    """plugin-payload-transport-a1/D4 — defensive: ref re-introduction breaks A1.

    V-3 attempts 1 + 2 falsified the `ref:` shape: Claude Code's resolver
    routes `url + ref:` against github.com URLs through the
    `case 'github':` SSH-clone handler, which fails on consumer machines
    without GitHub SSH keys. Re-introducing `ref:` would silently regress
    every consumer install. This test is the per-PR firewall against that
    regression.
    """
    plugin = _load_first_plugin()
    assert "ref" not in plugin["source"], (
        "marketplace.json source must not carry 'ref:' — A1 transport "
        "requires sha-pinning. Adding 'ref:' routes the resolver back "
        "through the SSH-clone failure mode (V-3 attempts 1+2 falsified)."
    )


def test_marketplace_plugin_entry_omits_version() -> None:
    """m5-plugin-deployment-pattern/D3 — plugin.json:version is the single source of truth.

    A marketplace-level `version` field is silently overridden by
    `dist/.claude-plugin/plugin.json:version`, producing operator-misleading
    drift.
    """
    plugin = _load_first_plugin()
    assert "version" not in plugin


def test_marketplace_source_omits_legacy_type_field() -> None:
    """Regression — broken `"type": "git"` discriminator must not return."""
    plugin = _load_first_plugin()
    assert "type" not in plugin["source"]

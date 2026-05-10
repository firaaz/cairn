"""Schema-shape lint for `.claude-plugin/marketplace.json`.

Pins (per ADR `marketplace-source-url-amend` D2-revised/D7-revised,
amending `m5-plugin-deployment-pattern` D2/D7 after V-3 falsification on
2026-05-10):

1. `plugins[0].source.source == "url"` (D2-revised)        [FLI-1]
2. `plugins[0].source.url == "https://github.com/firaaz/cairn.git"` (D2-revised)
3. `plugins[0].source.ref == "release"` (D2 + D7, unchanged)  [defends S7]
4. `"version" not in plugins[0]` (ADR D3)                  [FLI-6]
5. `"type" not in plugins[0].source` (regression)          [defends FLI-1]

These five assertions are the per-PR shape lint defending the amended
manifest shape (`source: "url"` + explicit HTTPS URL + `ref: "release"`).
The pivot from `source: "github"` to `source: "url"` was forced by V-3
empirical evidence: Claude Code's resolver constructs SSH-protocol clones
for `source: "github"`, breaking HTTPS-default consumers — see
`docs/adr/marketplace-source-url-amend.md` for the falsification record
and the rationale for `url` over `git-subdir`.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def _load_first_plugin() -> dict:
    data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    plugins = data["plugins"]
    assert plugins, "marketplace.json must declare at least one plugin entry"
    return plugins[0]


def test_marketplace_source_source_is_url() -> None:
    """ADR D2-revised / FLI-1 — source discriminator is the literal 'url'.

    Risk Surface coverage: this test plus test_marketplace_source_ref_is_release
    are the CI-time defense closest to M7.5. Pre-amendment this asserted
    'github'; V-3 falsified that choice (SSH-protocol resolver behavior on
    HTTPS-default consumers — see docs/adr/marketplace-source-url-amend.md).
    """
    plugin = _load_first_plugin()
    assert plugin["source"]["source"] == "url"


def test_marketplace_source_url_is_https_cairn_git() -> None:
    """ADR D2-revised — explicit HTTPS URL forces HTTPS-protocol clone.

    The `url` source-type's `url` field accepts both 'https://' and 'git@'
    forms; we pin 'https://' to avoid the SSH-default failure mode that
    falsified the original `source: "github"` choice on 2026-05-10.
    """
    plugin = _load_first_plugin()
    assert plugin["source"]["url"] == "https://github.com/firaaz/cairn.git"


def test_marketplace_source_ref_is_release() -> None:
    """ADR D2 + D7 — ref pins to the dist-only `release` branch.

    Defends Phase 1 S7 (D2 stability stance violated by ref-omission) and
    is the second leg of M7.5 risk-surface coverage.
    """
    plugin = _load_first_plugin()
    assert plugin["source"]["ref"] == "release"


def test_marketplace_plugin_entry_omits_version() -> None:
    """ADR D3 / FLI-6 — plugin.json:version is the single source of truth.

    Defends the silent-mask trap noted in Phase 0.5 Evidence 9: a
    marketplace-level `version` field is silently overridden by
    plugin.json:version, producing operator-misleading drift.
    """
    plugin = _load_first_plugin()
    assert "version" not in plugin


def test_marketplace_source_omits_type_field() -> None:
    """Regression — broken `"type": "git"` discriminator must not return.

    The current marketplace.json carries this invalid field; the M7
    rewrite must drop it entirely (FLI-1 atomicity — partial rewrite
    leaving both old and new keys is forbidden).
    """
    plugin = _load_first_plugin()
    assert "type" not in plugin["source"]

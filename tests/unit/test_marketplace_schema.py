"""RED tests for cairn-m7-plugin-deployment-pattern S1/S2 — marketplace.json schema lint.

Pins (per intent.md §S2, ADR `m5-plugin-deployment-pattern` D2/D3/D7):

1. `plugins[0].source.source == "github"` (ADR D2)         [FLI-1]
2. `plugins[0].source.repo == "firaaz/cairn"` (ADR D2)
3. `plugins[0].source.ref == "release"` (ADR D2 + D7)      [defends S7]
4. `"version" not in plugins[0]` (ADR D3)                  [FLI-6]
5. `"type" not in plugins[0].source` (regression)          [defends FLI-1]

These five assertions are the per-PR shape lint that defends ADR D2's
literal `source.source: "github"` + `repo: "firaaz/cairn"` + `ref: "release"`
shape. They are the closest CI-time defense for Risk Surface item M7.5
(Anthropic resolver-follow assumption), which is otherwise empirically
verifiable only via audit check 9 (manual round-trip install — D9).

Tests MUST FAIL at HEAD because the live `.claude-plugin/marketplace.json`
carries the schema-invalid `"type": "git"` discriminator (see
intent.md:21 "consumer-broken").
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


def test_marketplace_source_source_is_github() -> None:
    """ADR D2 / FLI-1 — source discriminator is the literal 'github'.

    Risk Surface coverage: this test plus test_marketplace_source_ref_is_release
    are the CI-time defense closest to M7.5 (intent.md:110). The empirical
    residual is offloaded to audit check 9 (intent.md:94, NON-SKIPPABLE).
    """
    plugin = _load_first_plugin()
    assert plugin["source"]["source"] == "github"


def test_marketplace_source_repo_is_firaaz_cairn() -> None:
    """ADR D2 — repo coordinate is `firaaz/cairn`."""
    plugin = _load_first_plugin()
    assert plugin["source"]["repo"] == "firaaz/cairn"


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

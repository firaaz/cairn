"""RED tests for cairn-m5-f1-packaging A1, A2 — plugin manifests.

Pins:
- A1 — `.claude-plugin/marketplace.json` shape (D1).
- A2 — Plugin manifest with explicit version (D1, D2). Both the canonical
  source `.claude-plugin/plugin-template.json` and the post-build artifact
  `dist/.claude-plugin/plugin.json` (after `build_dist` is invoked) must
  declare `name == "cairn"` and `version == "0.1.0"` (literal string).

Per intent.md A1/A2 + operator-confirmed envelope amendment (SHA e18dfd7),
both `plugin-template.json` and `hooks-template.json` are canonical sources.
The post-build artefact assertions for A2 invoke `scripts/build_dist.py`
into a tmp output dir.

Note: A1's `source.type == 'git'` + `source.path == 'dist/'` shape (the
F1-era assertion at A1) is SUPERSEDED by ADR `m5-plugin-deployment-pattern/D2`,
which mandates `source.source: 'github'` + `repo: 'firaaz/cairn'` +
`ref: 'release'`. The shape-pinning test was retired as part of feature
`cairn-m7-plugin-deployment-pattern` (Phase 2 amendment). The remaining A1
tests (`exists_and_parses`, `has_exactly_one_cairn_plugin_entry`,
`accepts_optional_ref_or_sha_fields`) remain valid post-supersession.

Tests must FAIL at HEAD because:
- `.claude-plugin/` does not exist.
- `scripts/build_dist.py` does not exist.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_TEMPLATE_PATH = REPO_ROOT / ".claude-plugin" / "plugin-template.json"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_dist.py"


# ---------------------------------------------------------------------------
# A1 — Marketplace manifest (D1)
# ---------------------------------------------------------------------------


def test_a1_marketplace_manifest_exists_and_parses():
    """`.claude-plugin/marketplace.json` exists and parses as JSON."""
    assert MARKETPLACE_PATH.is_file(), (
        f"A1: marketplace manifest not found at {MARKETPLACE_PATH}"
    )
    data = json.loads(MARKETPLACE_PATH.read_text())
    assert isinstance(data, dict), "A1: marketplace.json top-level must be an object"


def test_a1_marketplace_has_exactly_one_cairn_plugin_entry():
    """`plugins` array has exactly one entry whose `name` is `cairn`."""
    data = json.loads(MARKETPLACE_PATH.read_text())
    plugins = data.get("plugins")
    assert isinstance(plugins, list), "A1: marketplace.plugins must be a list"
    assert len(plugins) == 1, (
        f"A1: marketplace must declare exactly one plugin entry; got {len(plugins)}"
    )
    assert plugins[0].get("name") == "cairn", (
        f"A1: plugin entry name must be 'cairn'; got {plugins[0].get('name')!r}"
    )


def test_a1_marketplace_accepts_optional_ref_or_sha_fields():
    """The manifest's source object accepts (does not reject) `ref` or `sha`
    optional pin fields. We assert that if either is present it is a string,
    and that the schema does not forbid them by extra-key validation. Since
    JSON has no schema enforcement at parse time, we only assert that the
    parser tolerates a manifest containing those keys when they exist (or
    that they are absent — both are acceptable per intent.md A1).
    """
    data = json.loads(MARKETPLACE_PATH.read_text())
    src = data["plugins"][0]["source"]
    for key in ("ref", "sha"):
        if key in src:
            assert isinstance(src[key], str), (
                f"A1: source.{key} must be a string when present; got {type(src[key])}"
            )


# ---------------------------------------------------------------------------
# A2 — Plugin manifest with explicit version (D1, D2) — canonical source
# ---------------------------------------------------------------------------


def test_a2_canonical_plugin_template_exists_and_parses():
    """Canonical source `.claude-plugin/plugin-template.json` parses as JSON."""
    assert PLUGIN_TEMPLATE_PATH.is_file(), (
        f"A2: plugin-template.json not found at {PLUGIN_TEMPLATE_PATH}"
    )
    data = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    assert isinstance(data, dict), "A2: plugin-template.json top-level must be object"


def test_a2_canonical_plugin_template_name_is_cairn():
    """`plugin-template.json.name == "cairn"`."""
    data = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    assert data.get("name") == "cairn", (
        f"A2: plugin name must be 'cairn'; got {data.get('name')!r}"
    )


def test_a2_canonical_plugin_template_version_literal_0_1_0():
    """`version` is the literal string `"0.2.0"` per D2 (explicit, not derived)."""
    data = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    version = data.get("version")
    assert isinstance(version, str), (
        f"A2: version must be a string; got {type(version)}"
    )
    assert version == "0.2.0", (
        f"A2: version must be the literal string '0.2.0' per D2; got {version!r}"
    )


def test_a2_canonical_plugin_template_description_nonempty():
    """`description` is non-empty."""
    data = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), (
        f"A2: description must be non-empty string; got {desc!r}"
    )


def test_a2_marketplace_and_plugin_names_agree():
    """The two manifests' `name` fields agree."""
    market = json.loads(MARKETPLACE_PATH.read_text())
    plugin = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    assert market["plugins"][0]["name"] == plugin["name"], (
        f"A2: marketplace plugin name {market['plugins'][0]['name']!r} must "
        f"match plugin manifest name {plugin['name']!r}"
    )


# ---------------------------------------------------------------------------
# A2 — built artefact at dist/.claude-plugin/plugin.json (post-build)
# ---------------------------------------------------------------------------


def _run_build_into(tmp_path: Path) -> None:
    """Invoke build_dist.py to populate tmp_path/dist as the dist root."""
    dist_root = tmp_path / "dist"
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--repo-root",
            str(REPO_ROOT),
            "--dist-root",
            str(dist_root),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, (
        f"A2: build_dist.py failed with rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_a2_built_plugin_json_exists_and_matches_template(tmp_path):
    """After build, `dist/.claude-plugin/plugin.json` exists and equals the
    canonical template."""
    if not BUILD_SCRIPT.is_file():
        pytest.fail(f"A2: build_dist.py not found at {BUILD_SCRIPT}")
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / ".claude-plugin" / "plugin.json"
    assert built.is_file(), f"A2: built plugin.json not found at {built}"
    built_data = json.loads(built.read_text())
    canonical_data = json.loads(PLUGIN_TEMPLATE_PATH.read_text())
    assert built_data == canonical_data, (
        f"A2: built plugin.json must equal canonical template; "
        f"built={built_data!r} canonical={canonical_data!r}"
    )


def test_a2_built_plugin_json_carries_explicit_version(tmp_path):
    """Built artefact carries `version == "0.2.0"` literal."""
    if not BUILD_SCRIPT.is_file():
        pytest.fail(f"A2: build_dist.py not found at {BUILD_SCRIPT}")
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / ".claude-plugin" / "plugin.json"
    data = json.loads(built.read_text())
    assert data.get("version") == "0.2.0", (
        f"A2: built plugin.json version must be '0.2.0'; got {data.get('version')!r}"
    )


# ---------------------------------------------------------------------------
# cairn-intent loop ships in the payload (Part A1)
# ---------------------------------------------------------------------------


def test_cairn_intent_loop_ships_in_dist(tmp_path):
    """The build emits a working cairn-intent loop: the skill, both
    fresh-context decorrelation agents, and the intent template. Regression
    pin so a future allow-list change can't silently drop the loop."""
    if not BUILD_SCRIPT.is_file():
        pytest.fail(f"cairn-intent: build_dist.py not found at {BUILD_SCRIPT}")
    _run_build_into(tmp_path)
    dist = tmp_path / "dist"
    expected = [
        dist / "skills" / "cairn-intent" / "SKILL.md",
        dist / "agents" / "intent-challenge.md",
        dist / "agents" / "intent-review.md",
        dist / "templates" / "intent.md",
    ]
    missing = [str(p.relative_to(dist)) for p in expected if not p.is_file()]
    assert not missing, (
        f"cairn-intent: build_dist must ship the loop; missing from dist: {missing}"
    )

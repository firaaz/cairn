"""Codex plugin surface tests for the repo-owned Cairn plugin."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "cairn"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
HOOKS_MANIFEST = PLUGIN_ROOT / "hooks" / "hooks.json"

REQUIRED_SKILLS = (
    "using-cairn",
    "cairn-catchup",
    "cairn-handoff",
    "cairn-decision",
    "cairn-new-adr",
    "cairn-tdd-feature",
    "cairn-intent",
)


def _load_json(path: Path) -> dict:
    assert path.is_file(), f"missing JSON file: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a JSON object"
    return data


def _frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill_md} must start with YAML frontmatter"
    try:
        raw = text.split("\n---\n", 1)[0][4:]
    except ValueError:
        raise AssertionError(f"{skill_md} frontmatter is not closed")
    data = yaml.safe_load(raw)
    assert isinstance(data, dict), f"{skill_md} frontmatter must be a mapping"
    return data


def test_codex_marketplace_points_to_repo_owned_cairn_plugin() -> None:
    data = _load_json(MARKETPLACE_PATH)

    assert data["name"] == "cairn-local"
    assert data["interface"]["displayName"] == "Cairn Local"

    plugins = data["plugins"]
    assert isinstance(plugins, list)
    cairn_entries = [entry for entry in plugins if entry.get("name") == "cairn"]
    assert len(cairn_entries) == 1

    entry = cairn_entries[0]
    assert entry["source"] == {"source": "local", "path": "./plugins/cairn"}
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Developer Tools"


def test_codex_plugin_manifest_exposes_skills_and_hooks() -> None:
    data = _load_json(PLUGIN_MANIFEST)

    assert data["name"] == "cairn"
    assert data["version"] == "0.1.0"
    assert data["skills"].rstrip("/") == "./skills"
    assert data["hooks"] == "./hooks/hooks.json"
    assert "apps" not in data
    assert "mcpServers" not in data
    assert data["interface"]["displayName"] == "Cairn"
    assert "defaultPrompt" in data["interface"]


def test_codex_hooks_manifest_exists_and_parses() -> None:
    data = _load_json(HOOKS_MANIFEST)
    hooks = data.get("hooks")
    assert isinstance(hooks, dict)
    assert "PreToolUse" in hooks
    assert "PostToolUse" in hooks


def test_codex_hooks_manifest_uses_plugin_root_wrapper_adapters() -> None:
    data = _load_json(HOOKS_MANIFEST)
    commands = [
        hook.get("command", "")
        for entries in data["hooks"].values()
        for entry in entries
        for hook in entry.get("hooks", [])
    ]

    assert commands
    assert all("${PLUGIN_ROOT}" in command for command in commands)
    assert all("${CLAUDE_PLUGIN_ROOT}" not in command for command in commands)
    assert any("codex_pretool_guard.py" in command for command in commands)
    assert any("codex_posttool_reality.py" in command for command in commands)
    assert not any("using-cairn-carrier.sh" in command for command in commands)

    pretool_entries = data["hooks"]["PreToolUse"]
    pretool_matchers = " ".join(entry.get("matcher", "") for entry in pretool_entries)
    assert "exec_command" in pretool_matchers
    assert "apply_patch" in pretool_matchers

    posttool_entries = data["hooks"]["PostToolUse"]
    posttool_matchers = " ".join(entry.get("matcher", "") for entry in posttool_entries)
    assert "apply_patch" in posttool_matchers


def test_codex_plugin_scaffold_has_required_support_surfaces() -> None:
    required_dirs = (
        ".codex-plugin",
        "skills",
        "scripts",
        "scripts/lib",
        "checks",
        "hooks",
        "templates",
        "workflows",
        "references",
    )
    missing = [path for path in required_dirs if not (PLUGIN_ROOT / path).is_dir()]
    assert not missing, f"missing Codex plugin directories: {missing}"


def test_required_codex_skills_exist_with_valid_frontmatter() -> None:
    for skill_name in REQUIRED_SKILLS:
        skill_md = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        assert skill_md.is_file(), f"missing skill: {skill_name}"
        frontmatter = _frontmatter(skill_md)
        assert frontmatter["name"] == skill_name
        assert isinstance(frontmatter["description"], str)
        assert frontmatter["description"].strip()


def test_codex_tdd_skill_bundles_phase_agent_references() -> None:
    reference_root = PLUGIN_ROOT / "skills" / "cairn-tdd-feature" / "references"
    required_refs = (
        "phase-1-tdd.md",
        "phase-2-tdd.md",
        "phase-3-tdd.md",
        "phase-4-tdd.md",
        "triager-tdd.md",
        "role-topology.yaml",
    )
    missing = [name for name in required_refs if not (reference_root / name).is_file()]
    assert not missing, f"missing phase-agent prompt references: {missing}"


def test_codex_plugin_bundles_selected_canonical_references() -> None:
    required_files = (
        "checks/atomicity_guard.py",
        "checks/premise_guard.py",
        "checks/reality-check.sh",
        "checks/reversibility-guard.sh",
        "checks/role_guard.py",
        "checks/codex_pretool_guard.py",
        "checks/codex_posttool_reality.py",
        "hooks/hooks.json",
        "scripts/validate_architecture.py",
        "scripts/lib/codex_workflow_executor.py",
        "scripts/lib/workflow_registry.py",
        "templates/handoff.md",
        "templates/intent.md",
        "workflows/cairn-intent.yaml",
        "references/decision.md",
        "references/decision.full.md",
        "references/guards.md",
        "references/new-adr.md",
        "references/new-adr.full.md",
    )
    missing = [path for path in required_files if not (PLUGIN_ROOT / path).is_file()]
    assert not missing, f"missing bundled Codex plugin references: {missing}"


def test_cairn_guards_are_reference_material_not_public_skill() -> None:
    assert not (PLUGIN_ROOT / "skills" / "cairn-guards" / "SKILL.md").exists(), (
        "cairn-guards must not be exposed as a public Codex skill"
    )

    chooser_text = (PLUGIN_ROOT / "skills" / "using-cairn" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "cairn-guards" not in chooser_text
    assert "references/guards.md" in chooser_text

    text = (PLUGIN_ROOT / "references" / "guards.md").read_text(encoding="utf-8")
    lower = text.lower()

    assert "codex plugin registers automatic hooks" in lower
    assert (
        "guards are hook-backed where supported and script-backed as fallback" in lower
    )
    assert "claude plugin path remains hook-backed where supported" in lower
    assert (
        "sessionstart carrier is not shipped through the codex plugin hook manifest"
        in lower
    )


def test_codex_workflow_skills_point_to_guard_reference() -> None:
    for skill_name in ("cairn-tdd-feature", "cairn-intent"):
        text = (PLUGIN_ROOT / "skills" / skill_name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "references/guards.md" in text
        assert "explicit guard commands" in text


def test_consumer_docs_include_codex_install_flow() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "CONSUMER.md").read_text(encoding="utf-8"),
        ]
    )

    assert (
        "codex plugin marketplace add "
        "/Users/firaazfarook/Developer/github.com/firaaz/cairn"
    ) in docs
    assert "codex plugin add cairn@cairn-local" in docs
    assert "start a new Codex thread" in docs
    assert "review and trust the plugin hook registration" in docs.lower()

# Cairn

A slice-based development methodology for complex AI-assisted software engineering.

A cairn is a stack of stones marking a path on a long journey. Each slice adds a stone. The cairn is the cumulative substrate. Fresh sessions pause at waymarks. Discipline is cumulative.

## Status

Solo development, pre-v1. Not yet ready for adoption by other projects or teams. See `docs/roadmap.md` for work required to reach v1.

## What this is

Cairn is a methodology tool — a repository of protocols, checks, commands, and documentation for a four-phase slice pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and a mechanical substrate validator. It is designed for complex, long-horizon, AI-assisted software engineering where correlated errors and role contamination are real failure modes.

It is **not** for simple software. See `docs/spec-v1.md` §1 for scope.

## How to consume cairn from another project

During solo dev, consumption is via symlink:

```bash
cd /path/to/your/project
ln -s ~/Developer/lab/cairn .slice-system
echo ".slice-system" >> .gitignore
```

Your project's hook configuration (e.g., `.claude/settings.json` for Claude Code) references scripts via `.slice-system/checks/<name>.sh`. Your project's slash commands live in `.claude/commands/` but reference cairn documentation and scripts via `.slice-system/docs/` and `.slice-system/scripts/`.

Post-v1, the symlink converts to a git submodule pinned at a tagged version.

## Documentation

- `docs/vision.md` — the six commitments for v1 and success criteria
- `docs/roadmap.md` — ordered slice sequence toward v1
- `docs/spec-v1.md` — canonical spec (Layer 2, not auto-loaded)
- `docs/operational-reference.md` — quick operational reference (Layer 1)

## Cairn-internal dev aids

`commands/claude-code/.local/` holds personal tooling for developing cairn (e.g. `/dev-mode` morning briefing) that is not part of cairn-the-methodology and does not ship to consumers. Files there require a one-time per-machine setup (symlink into `~/.claude/commands/`). See `commands/claude-code/.local/README.md` for the carve-out rationale and setup steps.

## Versioning

See `CHANGELOG.md`. v0.1.0 is the initial extraction.

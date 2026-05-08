# Cairn

A slice-based development methodology for complex AI-assisted software engineering.

A cairn is a stack of stones marking a path on a long journey. Each slice adds a stone. The cairn is the cumulative substrate. Fresh sessions pause at waymarks. Discipline is cumulative.

## Status

Solo development, pre-v1. Not yet ready for adoption by other projects or teams. See `docs/roadmap.md` for work required to reach v1.

## What this is

Cairn is a methodology tool — a repository of protocols, checks, commands, and documentation for a four-phase slice pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and a mechanical substrate validator. It is designed for complex, long-horizon, AI-assisted software engineering where correlated errors and role contamination are real failure modes.

It is **not** for simple software. See `docs/spec-v1.md` §1 for scope.

## How to consume cairn from another project

The canonical install path is via the M5 plugin payload — see `CONSUMER.md` for the install flow, the post-install validator step, and a 10-minute first-dispatch walkthrough.

<!-- F1-followup: marketplace git URL + post-install validator stdout literal land in F1. -->

Symlink-based consumption is kept as a fallback while the plugin marketplace stabilises:

```bash
cd /path/to/your/project
ln -s ~/Developer/lab/cairn .slice-system
echo ".slice-system" >> .gitignore
```

Your project's hook configuration (e.g., `.claude/settings.json` for Claude Code) references scripts via `.slice-system/checks/<name>.sh`. Your project's slash commands live in `.claude/commands/` but reference cairn documentation and scripts via `.slice-system/docs/` and `.slice-system/scripts/`.

<!-- F3-followup: remove the symlink instruction once the `complex-rag-analysis` migration lands and the D8 self-symlink-only stance is publicly stable. -->

## Reading order

1. README.md (you are here) — what cairn is, at a glance
2. CONSUMER.md — install, dispatch, troubleshooting (start here if consuming cairn)
3. docs/operational-reference.md — how cairn works (Layer 1)
4. docs/spec-v1.md — why cairn is shaped this way (Layer 2; pull in deliberately)

## Other docs

- `docs/why-cairn.md`, `docs/vision.md`, `docs/roadmap.md`
- `docs/adoptable-disciplines.md` — partial adoption menu
- `docs/phase-skill-mapping.md` — phase → Superpowers skill map

## Cairn-internal dev aids

`commands/claude-code/.local/` holds personal tooling for developing cairn (e.g. `/dev-mode` morning briefing) that is not part of cairn-the-methodology and does not ship to consumers. Files there require a one-time per-machine setup (symlink into `~/.claude/commands/`). See `commands/claude-code/.local/README.md` for the carve-out rationale and setup steps.

## Versioning

See `CHANGELOG.md`. v0.1.0 is the initial extraction.

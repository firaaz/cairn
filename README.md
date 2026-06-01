# Cairn

A slice-based development methodology for complex AI-assisted software engineering.

A cairn is a stack of stones marking a path on a long journey. Each slice adds a stone. The cairn is the cumulative substrate. Fresh sessions pause at waymarks. Discipline is cumulative.

## Status

Solo development, pre-v1. Not yet ready for adoption by other projects or teams. See `docs/roadmap.md` for work required to reach v1.

## What this is

Cairn is a methodology tool — a repository of protocols, checks, commands, and documentation for a four-phase slice pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and a mechanical substrate validator. It is designed for complex, long-horizon, AI-assisted software engineering where correlated errors and role contamination are real failure modes.

It is **not** for simple software. See `docs/spec-v1.md` §1 for scope.

## How to consume cairn from another project

- **First-time consumers.** Run `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. See `CONSUMER.md` for the full quickstart, post-install validator, and a 10-minute first-dispatch walkthrough.
- **Codex local plugin.** From this repo, run `codex plugin marketplace add /Users/firaazfarook/Developer/github.com/firaaz/cairn`, then `codex plugin add cairn@cairn-local`, then start a new Codex thread before testing Cairn skills.
- **Migrating from a `.slice-system` symlink.** If you currently consume cairn via a `.slice-system → cairn` symlink, see the migration runbook at `docs/upgrading-from-symlink.md`.
- **Maintainer carve-out.** Cairn-the-repo itself retains a `.slice-system → .` self-symlink for maintainer dogfooding (INV-011, `docs/ARCHITECTURE.md`). This is a one-repo exemption — downstream consumers must NOT recreate it.

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

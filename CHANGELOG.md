# Changelog

All notable changes to cairn. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Bootstrap scaffolding for cairn self-consumption: `.slice-system → .` self-symlink, `.claude/commands → ../commands/claude-code` symlink, hooks wired in `.claude/settings.json`, `docs/ARCHITECTURE.md` with INV-001, ADR-001 (bootstrap exception, firm), `docs/adr/index.md`, `docs/lessons.md`, `.claude/sweep.yaml`, `tests/.gitkeep`.
- CLAUDE.md updated to describe self-consumption and the scope-guard `.slice-system/` path caveat.

### Fixed
- Dead reference `docs/development-system-spec-v1.md` in `docs/operational-reference.md:3` corrected to `docs/spec-v1.md`.

### Changed
- `.gitignore` no longer excludes `.claude/current-slice/` (required for the phase-gate mechanism to show committed slice artifacts in `git log`). `.claude/adr-editorial-fixes.log` added to the ignore list.

## [0.1.0] — 2026-04-11

### Added
- Initial extraction from `complex-rag-analysis`.
- Four-phase slice pipeline (Intent, Validation, Implementation, Integration).
- Decision protocol with adversarial review.
- Three enforcement hooks: reversibility-guard, scope-guard, reality-check.
- Substrate validator: `scripts/validate_architecture.py`.
- Layer 1 operational reference: `docs/operational-reference.md`.
- Layer 2 canonical spec: `docs/spec-v1.md`.
- Vision and roadmap documents scoped to the path to v1.
- Claude Code slash commands in `commands/claude-code/`.

### Known limitations (addressed by roadmap)
- Not yet agent-portable (Claude Code only; Windsurf pending).
- Assumes one active slice globally (parallelism not supported yet).
- Phase decomposition is unreviewed (phase rethink pending).
- No explicit cognitive role per phase (role definitions pending).
- Protocols live in skill prose rather than plain markdown (protocol extraction pending).

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

### Known issues
- **Validator follows `.slice-system` symlink to the wrong project root.** `scripts/validate_architecture.py:22` uses `Path(__file__).resolve().parent.parent` to locate the project root. When a consumer project invokes the script as `.slice-system/scripts/validate_architecture.py`, `.resolve()` canonicalizes the symlink back to the cairn install directory — so the validator reads cairn's own `docs/ARCHITECTURE.md` and `docs/adr/` instead of the consumer's. Discovered from a real consumer project where manual consistency verification passed but the validator was silently checking cairn's substrate. Latent for cairn's own self-consumption (cairn's docs are the correct answer either way), actively wrong for every other consumer. Fix direction: determine project root from `$CLAUDE_PROJECT_DIR`, then fall back to `git rev-parse --show-toplevel` against the process cwd, and only as a last resort fall back to `Path(__file__).resolve().parent.parent`. Fix belongs in cairn, not in consumer projects.

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

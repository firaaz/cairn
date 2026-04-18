# Changelog

All notable changes to cairn. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### ADR identifier migration (Phase 2 Part 1)

Per ADR `identifier-scheme` D7, the 9 numeric-prefix ADR files in `docs/adr/` have been renamed to flat-slug filenames; their frontmatter `id:` migrated from the legacy `ADR-NNN` form to the flat semantic slug (the filename tail after the `NNN-` prefix, preserved verbatim). Live-tree cross-references have been swept to the flat-slug form. `git mv` was used for each rename so `git log --follow` continues to track pre-rename history.

The 9 renamed ADRs (all `firm/accepted`):

| New filename | New `id:` | Title |
|---|---|---|
| `docs/adr/bootstrap-exception.md` | `bootstrap-exception` | Bootstrap Exception |
| `docs/adr/context-discipline-protocol.md` | `context-discipline-protocol` | Context Discipline Protocol |
| `docs/adr/cliff-failure-mode-and-v1-defenses.md` | `cliff-failure-mode-and-v1-defenses` | Cliff Failure Mode and V1 Defenses |
| `docs/adr/phase-lock-and-role-declaration.md` | `phase-lock-and-role-declaration` | Four-Phase Pipeline Lock and Role Declaration |
| `docs/adr/semantic-identity.md` | `semantic-identity` | Semantic Identity |
| `docs/adr/feature-slice-model.md` | `feature-slice-model` | Feature-Slice Model |
| `docs/adr/parallelism-v1.md` | `parallelism-v1` | Parallelism v1 |
| `docs/adr/context-tiers-integration.md` | `context-tiers-integration` | Context Tiers Integration for Feature-Slice Model |
| `docs/adr/phase-pipeline-evaluation.md` | `phase-pipeline-evaluation` | Phase Pipeline Evaluation — Confirmation of Four-Phase Structure |

**Consumer impact.** No mechanical breakage: hook scripts, slash-command files, and helper scripts under `scripts/` keep their paths unchanged. Consumer repositories that cite cairn ADRs by the legacy numeric-prefix form (inline prose, doc links, or slug mentions) will not break mechanically but will drift — the old names no longer exist in cairn, so citations point at deleted files. A known downstream consumer is `complex-rag-analysis`; downstream repositories should run a self-directed grep for the legacy token pattern and update their own references. Cairn announces the rename via this CHANGELOG entry; the sweep does not extend to consumer repos.

See ADR `identifier-scheme` D7 (the Phase 1 / Phase 2 migration plan) for context.

### Added
- Bootstrap scaffolding for cairn self-consumption: `.slice-system → .` self-symlink, `.claude/commands → ../commands/claude-code` symlink, hooks wired in `.claude/settings.json`, `docs/ARCHITECTURE.md` with INV-001, bootstrap-exception (bootstrap exception, firm), `docs/adr/index.md`, `docs/lessons.md`, `.claude/sweep.yaml`, `tests/.gitkeep`.
- CLAUDE.md updated to describe self-consumption and the scope-guard `.slice-system/` path caveat.

### Fixed
- Dead reference `docs/development-system-spec-v1.md` in `docs/operational-reference.md:3` corrected to `docs/spec-v1.md`.
- **Validator project-root resolution across `.slice-system` symlinks** (SLICE-001 `validator-symlink-fix`). `scripts/validate_architecture.py` no longer uses `Path(__file__).resolve().parent.parent` — that path canonicalized through the consumer project's `.slice-system` symlink back to the cairn install, making every consumer silently validate cairn's own substrate instead of their own. Resolution now tries `$CLAUDE_PROJECT_DIR`, then `git rev-parse --show-toplevel` from the current working directory, and exits with code `2` plus a stderr diagnostic if neither succeeds. No silent fallback to the script's own install path: a loud failure is strictly better than a false-green on the wrong project. Regression tests covering cairn self-dogfood, consumer via symlink with and without the env var, invocation from a subdirectory, a broken consumer substrate, and an unresolvable root live in `tests/unit/test_validate_architecture.py`.

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

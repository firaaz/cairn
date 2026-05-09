# Changelog

All notable changes to cairn. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### M7 — Plugin Deployment Pattern (release branch)

Operationalizes ADR `m5-plugin-deployment-pattern` D1–D9. `.claude-plugin/marketplace.json` now uses the documented `source.source: "github"` + `repo: "firaaz/cairn"` + `ref: "release"` shape — replacing the schema-invalid `"type": "git"` discriminator. Adds `.github/workflows/release-publish.yml` as the operator-triggered publish step (workflow_dispatch with `version` cross-check against built `plugin.json:version`; force-with-leases the `release` branch tree to match `/tmp/dist-out`; conditionally pushes `v${VERSION}` tag).

The `release` branch is **CI-only**:

- It is created and updated exclusively by `release-publish.yml` (via `git push --force-with-lease`).
- Do **not** push to `release` manually; do not merge into it; do not branch from it.
- The branch's tree intentionally does NOT match `dev`'s — its root is the dist-output payload (`scripts/build_dist.py`'s allow-listed contents) per ADR D1 shape-(i). Maintainers checking out `release` will see a different file layout from `dev`; this is by design (decoupled per ADR D2 + D4).
- Default branch remains `dev`; `release` is consumed only by Anthropic's marketplace resolver via `marketplace.json`'s `ref: "release"` pin.

`docs/adr/m5-plugin-deployment-pattern.md` is the canonical character document.

### Compression program merged to dev (2026-04-27)

Squash-merges `feature/compression` (335 commits across the substrate v1, lever-1 cost discipline, lever-Z substrate-full-pipeline, doc-cleanup-tail, and lever-Z-fixup slices, plus the orchestrator and per-phase agents). **Upgrade guide for downstream consumers: [`docs/upgrading-from-pre-compression.md`](docs/upgrading-from-pre-compression.md)** — one Verify snippet per delta.

#### Added

- **Knowledge substrate v1**: `cairn-knowledge` MCP server (stdio transport per ADR `cairn-substrate-and-fastmcp` D6), `scripts/cairn_query/` package backing four query tools (`lookup`, `search`, `path_bindings`, `cypher`), kuzu graph store. Read-only (mutation surface deferred per D7).
- **Slice-pipeline orchestrator** at `scripts/slice_orchestrator/`: four-phase Intent → Validation → Implementation → Integration loop with per-phase agents (`.claude/agents/phase-{1-writer,2-skeptic,3-implementer,4-integrator}.md`), CLI at `PYTHONPATH=scripts uv run python -m slice_orchestrator --brief|--resume|--legacy`, sweep-results artifact preservation, resume reconciliation.
- **Role-keyed enforcement** (`checks/role_guard.py`): canonical-knowledge read-class lockdown across all four phase roles; envelope-bound write enforcement for `phase-3-implementer`. Bash-token extraction (`_bash_path_tokens`) covers `cat`/`head`/`grep` paths.
- **Cost discipline**: per-phase model config (`AGENT_MODEL_CONFIG`) with extended-thinking budgets; Track-0 telemetry; lever-1 retune complete (~$18.71 baseline).
- Lessons L-001 through L-015 (`docs/lessons.md`). L-015 (squash-merge / extractor coupling) added in the post-merge closeout commit.
- `docs/upgrading-from-pre-compression.md` — 5-delta consumer upgrade guide.
- [`docs/features/compression.md`](docs/features/compression.md) — feature closeout (post-merge per merge-protocol step 9).

#### Changed

- ADR `cairn-substrate-and-fastmcp` formally retires the **stdlib-only constraint** (D3) and the **Rust-mapping end-of-v1 target** (D4). cairn's own `CLAUDE.md:26` updated to the v1-standing-dep-set wording in the closeout commit; downstream consumers should retire those constraints slice-by-slice.
- Orchestrator close: `_ARTIFACT_RELPATHS` now uses `integration/envelope-expansions.log` (was bare path).
- `phase-1-writer.md` frontmatter restored to `tools: Write, Edit, Bash` — re-enables the documented Bash-heredoc escape under Claude Code's sensitive-file gate (Slice-2-fixup over-hardening reversal). `Grep`/`Glob` remain absent (canonical-knowledge hardening preserved via `_bash_path_tokens`).

#### Migration required (consumer action)

Consumers symlinking cairn via `.slice-system → .` MUST apply five wiring deltas before the new orchestrator works. **Full guide: [`docs/upgrading-from-pre-compression.md`](docs/upgrading-from-pre-compression.md)**. Summary:

1. **Hook registration** in consumer's `.claude/settings.json` — `checks/role_guard.py` as `PreToolUse` on `Write|Edit|MultiEdit|NotebookEdit`. Without this, role-keyed enforcement silently no-ops; slice envelope is unenforced.
2. **MCP server registration** in consumer's `.mcp.json` — `cairn-knowledge` stdio. Without this, every phase agent's "query-first" directive errors at first call.
3. **Python deps** for the substrate (`pydantic`, `kuzu`, `mistune`, `typer`, `fastmcp`): `cd .slice-system && uv sync` (shared venv) or vendor into consumer's `pyproject.toml`.
4. **Agent + slash-command symlinks**: `.claude/agents → .slice-system/.claude/agents`, `.claude/commands → .slice-system/.claude/commands`.
5. **Consumer `CLAUDE.md`**: retire stdlib-only / Rust-mapping language (now formally retired in cairn).

Each delta in the upgrade doc has a one-line `Verify` snippet that confirms it landed.

#### Deferred / Open findings

- **Future-lesson candidate** (parallel-race): in-session phase-3 fan-out can race on shared git index — caused the audit-trail muddle in feature-branch commit `fd88b95` (S3 message, S4.a content). Mitigation: sequence cluster commits or use per-cluster worktrees. Promotion to a formal lesson deferred to next recurrence.
- **F2** (scope-guard): `checks/scope-guard.sh:118` writes to bare `envelope-expansions.log`; post-S4.a, only the `integration/`-prefixed path is bundled at slice close. Audit-trail gap if `EXPAND_ENVELOPE=1` ever fires via the Edit hook (not via Python heredoc). Out-of-scope for the closing slice; future paper-cut surface.
- One pre-existing OOS test failure: `test_inv004_turn1_token_budget` (env-dependent CC token measurement); not introduced by this merge.
- **Substrate Slice 4 — SliceExtractor disk fallback** (post-merge surfaced). `scripts/cairn_query/extractors/slice.py:74` greps git log for slice-close commits with no disk fallback; the squash collapses those commits, leaving 4 of 5 `tests/unit/test_extractor_slice.py` tests RED on dev. Forward-fixed via `xfail(strict=True)` markers in the closeout commit; structural fix tracked as substrate Slice 4 (read from `.claude/sweep-results/` + `.claude/completed-slices/` in addition to git log). See L-015 + merge-protocol §Structural test-design mismatches.

Phase-4 verification at slice close (feature-branch HEAD `7eaab1a`): 1065/1066 pytest pass (single OOS above); `validate_architecture.py` exit 0 (10 invariants verified); INV-003 + INV-008 PASS via substrate query; Closes-when items 1-12 PASS; item 13 (soft Phase-4 dogfood) SKIPPED per intent.

#### Post-merge closeout (forward-fix on dev, 2026-04-27)

- **`chore:` commit** — reset stale `.claude/current-slice/slice.yaml` to `id/name/status: none` stub; `git rm --cached .claude/handoff.md` (gitignored grandfather, per merge-protocol §Tree cleanup line 116).
- **`docs:` closeout commit** — `docs/features/compression.md`; CLAUDE.md:26 line replaced with v1-standing-dep-set wording (ADR-mandated propagation); L-015 added; merge-protocol amended with §Structural test-design mismatches; ruff carry-over cleaned (24 → 0 errors); 4 `tests/unit/test_extractor_slice.py` tests `xfail(strict=True)`.
- **Branches:** `feature/compression` renamed to `archive/compression` post-closeout; both `dev` and `archive/compression` pushed to origin.

### Identifier scheme merged to dev (2026-04-18)

First feature→dev merge under the new merge protocol (`docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`). Feature closeout: [`docs/features/identifier-scheme.md`](docs/features/identifier-scheme.md).

#### Changed
- Identifier scheme: every ADR, slice, feature, and decision point now carries both `id:` (immutable) and `name:` (mutable). Prose uses `name`; cross-references, filenames, and hook inputs use `id`. See `docs/features/identifier-scheme.md` for the full feature closeout.
- ADR filenames migrated from `adr-NNN-<slug>.md` to `<semantic-slug>.md`.
- Slice and feature namespaces adopt feature-scoped slugs (`<feature>/<slice-slug>`).

#### Added
- `docs/features/identifier-scheme.md` — first feature closeout under the new merge protocol.
- `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` — feature→dev merge protocol (first-instance precedent).
- `.gitmessage-phase-{1..4}` — commit-message templates for slice phases.
- `docs/lessons.md` L-006 — identifier renames are feature-scoped.

#### Deprecated / Internal
- `.claude/handoff.md` and `.claude/adr-editorial-fixes.log` removed from tracking (`.gitignore` now authoritative).
- `archive/identifier-scheme` will preserve the pre-squash feature-branch commits (rename pending in Dispatch E).

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

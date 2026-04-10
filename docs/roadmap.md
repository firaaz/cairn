# Cairn — Roadmap to v1

*Ordered slice sequence. Each entry is a candidate slice; exact ordering and batching gets decided by future sessions as dependencies and friction surface.*

## Must-land-before-v1

### 1. `/decision`: phase rethink + role assignment

Single decision protocol run producing one ADR that locks phase count, boundaries, names, and role per phase. Prerequisite for most other work because role purity shapes how protocols are authored.

### 2. Protocol extraction to plain markdown

Move phase protocols out of skill prose into `protocols/phase-N-<role>.md`. `/catchup` learns to inject the current phase's protocol into context based on state.

### 3. `state.json` + SHA-based catchup

Replace narrative-only handoff with structured state file carrying commit SHA. Catchup reads `state.json`, compares SHA against `git rev-parse HEAD`, skips investigation on match.

### 4. AGENTS.md migration

Rename CLAUDE.md conventions to AGENTS.md. Consumer projects migrate their CLAUDE.md at consumer timing, not as part of cairn v1.

### 5. Branch-local slice state

Refactor `.claude/current-slice/` so it exists only on slice branches, absent on `dev`. Enables slice exit via branch switching.

### 6. Parallelism support

Ensure multiple concurrent slices in separate worktrees don't interfere. Hooks read slice metadata from the current working tree. No global "active slice" pointer. Depends on (5).

### 7. Windsurf command/workflow port

Create `commands/windsurf/` mirror of `commands/claude-code/`. Validate both agents run at least one slice end-to-end. Depends on (2), (3).

### 8. Mid-slice agent handoff validation

One slice where Phase 1-2 runs on Claude Code and Phase 3+ runs on Windsurf, with clean handoff via `state.json`. Depends on (7).

### 9. Two-concurrent-slice validation

Two slices run in parallel on separate worktrees, both complete cleanly, no scope-guard interference. Depends on (5), (6).

### 10. Dogfood log infrastructure

`docs/dogfood-log.md` with structured entries (date, slice ID, friction observed, fix or follow-up). Populated over prior slices retroactively, then maintained going forward.

## May-land-before-v1 (bonus)

- Template extraction — `intent.md`, `slice.yaml`, ADR frontmatter extracted to `templates/`
- Check-script extraction — hooks become pure shell with thin per-agent wrappers
- Example slice walkthroughs — at least one worked example in `examples/`
- Mechanical validator auto-enforcement — `scripts/validate_architecture.py` runs as pre-commit on ADR file changes

## Not for v1 (post-release)

- Jira/Confluence integration
- Confluence publishing of ADRs
- Multi-dev concurrent slice merge protocol
- Per-slice branch protection rules in GitLab
- Cross-family verification automation
- Distribution via package managers
- Other agent integrations beyond Claude Code + Windsurf
- Dependency graph automation / topological slice ordering

## First slice suggestion

The first cairn slice should address **(1) phase rethink + role assignment** via the `/decision` protocol, because (a) it is a prerequisite for (2) protocol extraction, and (b) it tests whether the meta-dogfood loop works — cairn using itself for its own architectural decision.

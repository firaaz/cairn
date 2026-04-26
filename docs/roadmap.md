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

### 11. L-011 structural fix — phase-handoff commit gap

Promoted from L-011's "deferred pending recurrence" stance after 3 documented recurrences inside ~24h (R1: `cost-discipline/lever-1-tier-retune`; R2: `compression/learnings-capture` failed; R3: `compression/learnings-capture` retry). Each recurrence cost re-dispatch cycles + operator-side commit fixup. Two candidate fixes (per L-011): (a) tighten phase-agent prompts + orchestrator-side `git diff <handoff>~..<handoff>` non-empty assertion for content-bearing phases (cheaper); (b) move content commits to the orchestrator, forbid agent-side commits (structurally correct). The R2/R3 pattern points at Phase-3 cluster fan-out workers as the most fragile seam, favoring (b). Slice should pick a direction and ship a closed-loop fix; orchestrator-events.jsonl now captures `phase_redispatch` + `redispatch_cap_exceeded` so the recurrence rate is measurable post-fix. Docs ref: `docs/lessons.md` §L-011.

## May-land-before-v1 (bonus)

- Template extraction — `intent.md`, `slice.yaml`, ADR frontmatter extracted to `templates/`
- Check-script extraction — hooks become pure shell with thin per-agent wrappers
- Example slice walkthroughs — at least one worked example in `examples/`
- Mechanical validator auto-enforcement — `scripts/validate_architecture.py` runs as pre-commit on ADR file changes

## Gated — sequenced after specific milestones

*High-value items deferred behind specific work. Each entry names what it's waiting on so they don't slip silently — they unblock when their gate fires.*

- **Agent-managed planning substrate** — gated on substrate Slices 1+2 shipping. Run `/decision agent-managed-planning-substrate` + ADR covering: GitHub MCP adoption (or alternative), `.mcp.json` registration, credential posture (PAT vs OAuth, scope, rotation), agent-context-discipline implications, tool-count budget, supersession path. Required by §8.1 D2 of the knowledge-substrate design (any new credentialed external dependency needs deliberate ADR). Until then, `.claude/features/compression.yaml` + `.claude/handoff.md` carry planning state. See `docs/plans/2026-04-25-knowledge-substrate-design.md` §9:579.

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

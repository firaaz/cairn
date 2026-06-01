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

> **Re-anchored by `git-workflow-v1` (2026-05-31).** The slice unit and `.claude/current-slice/` retired at M4; the feature is the unit and work lives on a `feat/<feature-id>` branch. The "branch-local state" goal is met by branch-per-feature (D1). Largely addressed.

### 6. Parallelism support

Ensure multiple concurrent slices in separate worktrees don't interfere. Hooks read slice metadata from the current working tree. No global "active slice" pointer. Depends on (5).

> **Re-anchored by `git-workflow-v1` (2026-05-31).** "Slices" → features. The concurrent-feature lifecycle (worktree create/cleanup, per-worktree envelope copy, out-of-order merge ordering, handoff-append collision) is recorded as `git-workflow-v1` D4/D5, gated on the first real concurrent feature.

### 7. Windsurf command/workflow port

Create `commands/windsurf/` mirror of `commands/claude-code/`. Validate both agents run at least one slice end-to-end. Depends on (2), (3).

### 8. Mid-slice agent handoff validation

One slice where Phase 1-2 runs on Claude Code and Phase 3+ runs on Windsurf, with clean handoff via `state.json`. Depends on (7).

### 9. Two-concurrent-slice validation

Two slices run in parallel on separate worktrees, both complete cleanly, no scope-guard interference. Depends on (5), (6).

> **Re-anchored by `git-workflow-v1` (2026-05-31).** Now "two concurrent **features** merge `--no-ff` into `dev` cleanly." This is the validation event that fires `git-workflow-v1` D4/D5; the single-feature `--no-ff` dogfood (D2) is the prerequisite first step.

### 10. Dogfood log infrastructure

`docs/dogfood-log.md` with structured entries (date, slice ID, friction observed, fix or follow-up). Populated over prior slices retroactively, then maintained going forward.

### 11. L-011 structural fix — phase-handoff commit gap

Promoted from L-011's "deferred pending recurrence" stance after 3 documented recurrences inside ~24h (R1: `cost-discipline/lever-1-tier-retune`; R2: `compression/learnings-capture` failed; R3: `compression/learnings-capture` retry). Each recurrence cost re-dispatch cycles + operator-side commit fixup. Two candidate fixes (per L-011): (a) tighten phase-agent prompts + orchestrator-side `git diff <handoff>~..<handoff>` non-empty assertion for content-bearing phases (cheaper); (b) move content commits to the orchestrator, forbid agent-side commits (structurally correct). The R2/R3 pattern points at Phase-3 cluster fan-out workers as the most fragile seam, favoring (b). Slice should pick a direction and ship a closed-loop fix; orchestrator-events.jsonl now captures `phase_redispatch` + `redispatch_cap_exceeded` so the recurrence rate is measurable post-fix. Docs ref: `docs/lessons.md` §L-011.

### 12. compression/lever-Y-mcp-substrate-fixup — complete the MCP substrate

Substrate Slice 2 (`compression/lever-Y-mcp-substrate`, closed `305cd02`) shipped the structural pieces but the MCP server is a stub. Three defects: (a) `mcp_servers/cairn_knowledge/server.py:_stdin_reader` discards stdin instead of dispatching JSON-RPC — the tool functions in `tools.py` work in-process but are not exposed via MCP transport; (b) `fastmcp` package missing from `pyproject.toml` despite ADR `cairn-substrate-and-fastmcp` D1 listing it as a v1 standing dep; (c) `checks/role_guard.py:22` `READ_CLASS_TOOLS = {"Read"}` — Grep/Glob bypass the lockdown unchallenged, so phase-1-writer can still extract canonical-source content via Grep. Pytest closed clean because Phase-2 tests under-stated intent V2/V3 — they verify "process boots" and "source contains literals", not JSON-RPC round-trip. **Gates next slice opening:** the first phase-1-writer dispatch after Slice 2 will hit the broken substrate (frontmatter trimmed, ROLE_DENY_READ active, MCP non-functional). Fixup scope: ship a real JSON-RPC dispatcher in `server.py`, add `fastmcp` to `pyproject.toml` (or document hand-rolled choice via ADR amendment), extend `READ_CLASS_TOOLS` to include Grep+Glob, harden Phase-2 tests to verify JSON-RPC round-trip not just boot-liveness. **Status: closed** at `9b71cfa`; superseded operationally by §13 below.

### 13. compression/lever-Z-fixup — stabilization slice (gates `feature/compression → dev` merge)

Bundles the post-Slice-3 gating fixes surfaced during `compression/lever-Z-substrate-full-pipeline` (closed `003d9ad`). **(a) Phase-1 dispatch defect — primary blocker.** Built-in CC sensitive-file gate denies `Write` to `.claude/current-slice/intent.md` and `.claude/features/<feature>.yaml` even under `bypassPermissions`; Slice-2-fixup hardening removed `Bash` from `.claude/agents/phase-1-writer.md:4` frontmatter (`tools: Write, Edit`), so the documented P1 Bash-heredoc escape is unreachable. The first orchestrator-driven `/start-slice` after the merge will fail the same way Lever-Z's did (three retries + triager-escalate). Fix: restore `Bash` to phase-1-writer's frontmatter. Steelman against the obvious "this undoes the Slice-2-fixup hardening": `_bash_path_tokens` in `role_guard.py` already extracts `cat`/`head`/`grep` token paths from Bash commands and routes them through the same canonical-knowledge deny — restoring Bash does NOT reopen the canonical-knowledge bypass; only the `.claude/**` escape is restored. Phase-2 RED: orchestrator-driven phase-1-writer dispatch successfully commits `intent.md` on a trivial brief. **(b) Consumer migration documentation.** Cairn is consumed via `.slice-system → .` symlink; updating the symlink alone does NOT make the new compression features work for an existing consumer. Write `docs/upgrading-from-pre-compression.md` enumerating 5 wiring deltas: `.claude/settings.json` hook entries (`role_guard.py` PreToolUse on `Write|Edit|MultiEdit|NotebookEdit`; `role-cheatsheet.sh` SessionStart); `.mcp.json` cairn-knowledge registration plus the unresolved PYTHONPATH/cwd resolution for non-self-symlinked consumers (`python -m mcp_servers.cairn_knowledge` only resolves when CWD is cairn root); Python deps (pydantic / kuzu / mistune / typer / fastmcp) via either `cd .slice-system && uv sync` and orchestrator-under-cairn-venv or vendored into consumer's `pyproject.toml`; agent + slash-command discoverability (CC reads consumer's `.claude/agents/` and `.claude/commands/`, NOT `.slice-system/.claude/...`) — whole-directory symlinks are the cleanest path; `CLAUDE.md` updates for retired stdlib-only constraint (ADR D3) and Rust-mapping target (ADR D4). **(c) Cross-slice contradiction lesson** → `docs/lessons.md`. Three confirmed instances now (G7 in Slice-2-fixup `8fc0133`; G7-again, `test_v4_other_roles_unaffected_by_read_denylist`, and `test_bootstrap_scope_read_tool_ignored` in Lever-Z, resolved by envelope expansions `2713662` and `a79f609`). Lesson text: when a slice widens an enforcement set (e.g., `ROLE_DENY_READ`), Phase-2 skeptic should pre-grep the existing test corpus for assertions depending on the OLD set membership and surface those as candidate envelope expansions before Phase 3 dispatches; surfaces inversion candidates structurally rather than discovering them at Phase-3 RAISE_ISSUE time. **(d) Operational paper-cuts.** `_ARTIFACT_RELPATHS` in `scripts/slice_orchestrator/lifecycle.py:101` expects `envelope-expansions.log` at top-level but the in-session execution path used `integration/envelope-expansions.log` (manually copied at Slice-3 close to avoid loss); reconcile by updating `_ARTIFACT_RELPATHS` to expect `integration/envelope-expansions.log` (preferred — matches where the orchestrator writes it via the bundle path) and add a regression test. Phase-4-integrator prompt clarifications from Slice-3 dogfood rough edges: name `lookup`'s required `entity_type` param explicitly; document typed-record attribute access (`record.statement`) vs subscript; flag stdio-only constraint of cairn-knowledge MCP for in-process audit paths. **Out of scope** (each warrants its own slice): `_reconcile_resume_state` wiring (`scripts/slice_orchestrator/resume.py:154` orphan — needs resume state-machine design pass); cost-telemetry methodology gap (re-measurement against $18.71 Lever-1 baseline requires (a) above to land first so Track-0 telemetry runs end-to-end again).

## May-land-before-v1 (bonus)

- Template extraction — `intent.md`, `slice.yaml`, ADR frontmatter extracted to `templates/`
- Check-script extraction — hooks become pure shell with thin per-agent wrappers
- Example slice walkthroughs — at least one worked example in `examples/`
- Mechanical validator auto-enforcement — `scripts/validate_architecture.py` runs as pre-commit on ADR file changes

## Gated — sequenced after specific milestones

*High-value items deferred behind specific work. Each entry names what it's waiting on so they don't slip silently — they unblock when their gate fires.*

- **Agent-managed planning substrate** — gated on substrate Slices 1+2 shipping. Run `/decision agent-managed-planning-substrate` + ADR covering: GitHub MCP adoption (or alternative), `.mcp.json` registration, credential posture (PAT vs OAuth, scope, rotation), agent-context-discipline implications, tool-count budget, supersession path. Required by §8.1 D2 of the knowledge-substrate design (any new credentialed external dependency needs deliberate ADR). Until then, `.claude/features/compression.yaml` + `.claude/handoff.md` carry planning state. See `docs/plans/2026-04-25-knowledge-substrate-design.md` §9:579.
- **F1.1 / post-install validator stdout literal** — gated on first real consumer-side `/plugin install` data. The post-install validator stdout shape (`scripts/postinstall_validate.py` / `scripts/validate_plugin_install.py`) is a separately tracked F1-followup; the literal stdout/stderr lines the validator prints land in F1.1 once a real downstream `/plugin install` against the cairn marketplace produces a stable observable shape. The placeholder context lives at `CONSUMER.md:20–22` (the comment plus the `uv run python scripts/validate_plugin_install.py` invocation); F3's sweep notes at `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` record the dual-state-by-design under the replace branch.

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

# Cairn Shrink — Design

```
firmness: provisional
status: design — not an ADR; not a slice; brainstorm output
date: 2026-05-06
brainstorm-source: live session — operator framing + claude-opus-4-7 brainstorming skill
authoring-mode: collaborative
scope: Claude Code only (Windsurf deferred per Approach A)
```

---

## 1. Context

Cairn's slice methodology has accumulated significant maintenance overhead. Day-to-day work increasingly happens through `superpowers:*` skills (TDD, brainstorming, writing-plans, executing-plans), not through the slice pipeline. Anthropic's Agent Teams (experimental, Claude Code 2.1.32+) covers the multi-agent coordination shape natively, with first-party reliability.

This design re-shapes cairn around what's *unique to it* (document discipline, invariant binding, append-only ADRs, phase context isolation as a TDD pattern) while shedding what is now duplicated by Anthropic primitives (subagent dispatch, parallel fan-out, cost telemetry, retry/backoff, signal handling).

### 1.1 Trigger signals (2026-05-06)

- INV-002 binding **non-functional in production** (parser flat, can't read nested YAML)
- `close_slice` bundling bug ate INV-002's own budget on the slice that introduced it
- Three open meta-threads in memory: phase-2-skeptic write-timing on redispatch (#26), Phase-3 reverts under RED pressure, slice system propagates wrong models faithfully
- 23 slice-completes overdue for sweep
- 135-finding methodology audit (#1) untouched
- "Day-to-day work using superpowers works better than cairn's slice machinery" — operator observation
- Anthropic shipping Agent Teams in 2.1.32 with native parallel teammates, shared task lists, hooks, plan-approval gates

### 1.2 Substrate cost case re-examined

The substrate (`scripts/cairn_query/` + KuzuDB + FastMCP server) was justified by a Part-8 audit measurement: $18.71/slice, dominated by `cache_creation` from each phase agent reading the same large markdown corpus afresh. That cost was real.

The substrate replaced large markdown re-reads with smaller typed-record queries. **Equivalent savings are recoverable without the substrate's complexity**, via three mechanisms:

1. **Targeted reads** — phase agents `Read` only the relevant section of `ARCHITECTURE.md` (e.g., a single invariant block) using `offset:` / `limit:`, not the whole file.
2. **In-brief context** — the dispatch skill quotes relevant ADR / invariant snippets directly in the spawn prompt, so the agent doesn't need to re-discover.
3. **Per-phase scoped allowlists** — `role_guard`'s per-phase read patterns prevent agents from pulling in canonical sources they don't need.

The substrate's secondary value (typed records can't be paraphrased; structural isolation at the MCP boundary) is real but not load-bearing for solo-dev TDD. It can be re-introduced if a real graph-class query emerges that grep can't satisfy.

---

## 2. The 4-layer model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4 — Distribution                                   │
│   Claude Code plugin packaging                           │
├─────────────────────────────────────────────────────────┤
│ Layer 3 — Protocol                                       │
│   Phase-N subagent defs + thin dispatch skill            │
├─────────────────────────────────────────────────────────┤
│ Layer 2 — Enforcement                                    │
│   reversibility-guard + role_guard + validate_arch       │
├─────────────────────────────────────────────────────────┤
│ Layer 1 — Document                                       │
│   ARCHITECTURE.md, ADRs, lessons.md, plans, features     │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Layer 1 — Document

**What it is:** canonical markdown sources. Authoritative. Universal across platforms.

**Files in scope:**

- `docs/ARCHITECTURE.md` — invariants + system design
- `docs/adr/*.md` — append-only decision log
- `docs/lessons.md` — learning ritual
- `docs/spec-v1.md` — canonical spec
- `docs/operational-reference.md` — operational rules
- `docs/plans/*.md` — per-feature design docs and plans
- `.claude/features/*.yaml` — feature registry
- `.claude/handoff.md` — cross-session interface (slice-independent)
- `~/.claude/projects/.../memory/` — operator memory (out of repo; out of agent surface)

**Boundary:** the Document Layer does not depend on the orchestrator, the substrate, or any specific dispatch mechanism. Documents survive as authoritative artifacts regardless of how phases are dispatched.

### 2.2 Layer 2 — Enforcement

**What it is:** hooks and validators that protect document invariants.

**Components:**

| Component | Job | Notes |
|---|---|---|
| `reversibility-guard.sh` | Append-only ADRs (`Write` blocked on existing; `Edit` only on frontmatter `status:`/`superseded-by:`/`firmness:`) | Slice-independent. `ADR_EDITORIAL_FIX=1` typo escape preserved. |
| `role_guard.py` (simplified) | Per-phase read/write path allowlist via `AGENT_ROLE` env var | Drops MCP-forcing (no MCP). Preserves `READ_CLASS_TOOLS = {Read, Grep, Glob}` and envelope-grant escape (D9). |
| `validate_architecture.py` | Invariant binding checker | Currently broken (parser flat; INV-002 non-functional). Parser fix is in scope for the migration. |
| `prepare-commit-msg.sh` | Conventional commits prefix injection | Unchanged. |
| `reality-check.sh` | `ruff format && ruff check --fix` on Python edits | Unchanged. |

**Removed:**

- `scope-guard.sh` — slice-envelope checks subsumed by `role_guard`'s per-phase allowlists.

**Properties:** hooks are fast (sub-100ms); fail-closed on missing deps (`jq`, `ruff`); read-only on filesystem.

### 2.3 Layer 3 — Protocol

**What it is:** the TDD-by-construction phase isolation discipline.

**Components:**

**Phase-N subagent definitions** (`.claude/agents/phase-{1,2,3,4}-*.md`):

| Role | Tool allowlist (sketch) | Job |
|---|---|---|
| `phase-1-writer` (Reader) | Read on `docs/{ARCHITECTURE.md,adr,spec-v1.md}`; Write on `intent.md` | Writes intent doc from arch+ADR context only. |
| `phase-2-skeptic` (Skeptic) | Read on `intent.md`; Write on `tests/`; Bash for pytest | Writes failing tests from intent.md alone. |
| `phase-3-implementer` (Builder) | Read on `intent.md` + `tests/` + `src/`; Write on `src/`; Bash | Implements GREEN. Cannot read Phase-2 reasoning. |
| `phase-4-integrator` (Auditor) | Full read; Write on `sweep-notes.md`; Bash for pytest + validator | Audits with full context. |
| `issue-triager` | Read on git history; no Write | Classifies RAISE_ISSUE; superseded-test heuristic preserved. |

**Dispatch skill** — new file `.claude/skills/cairn-tdd-feature/SKILL.md` (skill folder per Anthropic's progressive-disclosure format):

- ~50–100 lines of skill prose.
- Frontmatter: `name: cairn-tdd-feature`, `description: <one-line invocation hint>`.
- Input: a brief (path to `docs/plans/<feature>.md` or inline prompt).
- Steps: dispatch phase-1-writer → verify intent.md committed → dispatch phase-2-skeptic with intent.md path → verify RED tests → dispatch phase-3-implementer → verify GREEN → dispatch phase-4-integrator → run validator → final commit.
- State: per-phase commits; **no `slice.yaml`**. The git history IS the state. The per-feature plan doc at `docs/plans/<feature>.md` is the durable artifact.
- Optional: a `clusters.yaml` contract for Phase-3 fan-out via parallel Agent tool calls in one message.

**Cross-platform note.** `.claude/skills/` is in Windsurf's documented cross-agent-compatibility discovery list (alongside `.agents/skills/`). The skill *prose* is therefore portable to Windsurf when its compat-discovery is enabled. The skill's *executable contract* — "spawn a subagent of type X via the Agent tool" — still requires the Claude Code Agent-tool primitive; Windsurf does not yet have a verified parity primitive (cf. §6).

**Phase isolation mechanism:**

1. **Independent context window per phase** — Agent tool gives this for free.
2. **Per-phase `tools:` allowlist** in subagent frontmatter — restricts tool surface.
3. **Per-phase read/write path patterns** in `role_guard.py` — denies tool calls outside the role's scope; envelope-grant escape preserved.
4. **The brief** — controlled by the dispatch skill; only the inputs the phase should see.
5. **Snapshot pinning (lightweight)** — dispatch skill captures `git rev-parse HEAD` at phase start; passes via prompt for invariant-validator runs.

**Removed (dies with orchestrator):**

- `scripts/slice_orchestrator/` package (3000 LOC across 8 modules)
- `slice.yaml` lifecycle (status digit, init, advance, close)
- `current-slice/` directory structure
- `sweep.yaml`, `sweep-interval`, `sweep-results/`, `/integration-sweep`
- `close_slice` ceremony (and the bundling bug)
- `commit_phase_handoff` (replaced by per-phase git commits in dispatch skill)
- 13-state-triple resume matrix
- Heartbeat daemon
- Cluster-yaml fan-out via `ThreadPoolExecutor` (replaced by parallel Agent tool calls)
- INV-009 cost-threshold trip in orchestrator (cost data still available natively)
- `_MirroringModule` test scaffolding
- `commands/claude-code/start-slice*.md`
- `commands/claude-code/integration-sweep*.md`
- `.claude/completed-slices/` failed-slice archive

### 2.4 Layer 4 — Distribution

**What it is:** how cairn ships to consumers.

**Today:** `.slice-system → .` symlink installed in consumer projects (e.g., complex-rag-analysis). Fragile (recursive symlink loop), forces scope-guard prefix-stripping logic, requires consumer projects to git-ignore the symlink.

**Target:** Claude Code plugin packaging. Consumers `claude plugin install cairn`. Skills + subagent definitions + hook scripts ship cleanly.

**Cross-platform side-effect.** Once skills live at `.claude/skills/`, Windsurf's compat-discovery picks them up automatically (when enabled). This means the dispatch skill's prose is shared across platforms even though the underlying primitive isn't yet. Subagent definitions at `.claude/agents/*.md` don't have a documented Windsurf cross-discovery; that's a Claude-Code-side artifact for now.

**Removed (dies with symlink):**

- `.slice-system → .` directory entry
- `scope-guard.sh:53` `.slice-system/` prefix-stripping logic
- Documentation about the symlink hazard

**Migration:** consumer projects (complex-rag-analysis is the known one) need a separate migration program — not in scope for the primary shrink.

---

## 3. What stays, what dies

### 3.1 Stays (carries forward)

| Element | Layer | Why |
|---|---|---|
| `docs/ARCHITECTURE.md` | 1 | Living architecture doc; invariant declarations |
| `docs/adr/*.md` | 1 | Append-only decision log |
| `docs/lessons.md` | 1 | Learning ritual |
| `docs/spec-v1.md` | 1 | Canonical spec |
| `docs/operational-reference.md` | 1 | Operational rules |
| `docs/plans/*.md` | 1 | Design docs / per-feature plans |
| `.claude/features/*.yaml` | 1 | Feature registry |
| `.claude/handoff.md` | 1 | Cross-session interface (slice-independent) |
| `reversibility-guard.sh` | 2 | ADR append-only enforcement |
| `role_guard.py` (simplified) | 2 | Per-phase tool/path allowlists |
| `validate_architecture.py` | 2 | Invariant binding (after parser fix) |
| `prepare-commit-msg.sh`, `reality-check.sh` | 2 | Conventional commit + lint hooks |
| `phase-{1,2,3,4}-*` agent defs | 3 | Role contracts (Reader / Skeptic / Builder / Auditor) |
| `issue-triager` agent def | 3 | RAISE_ISSUE classification + superseded-test heuristic |
| `cairn:tdd-feature` skill (NEW) | 3 | Dispatch skill (~50–100 lines) |
| `commands/claude-code/decision*.md` | n/a | `/decision` is independent of slices |
| `commands/claude-code/new-adr*.md` | n/a | ADR creation flow |
| `commands/claude-code/.local/dev-mode*.md` | n/a | Cairn-internal briefing |
| Memory system (operator-side) | n/a | `~/.claude/projects/.../memory/` — independent |

### 3.2 Dies (with rationale)

| Element | Why safe to drop |
|---|---|
| `scripts/slice_orchestrator/` (3000 LOC) | Anthropic Agent tool + Skill primitive cover dispatch; signal handling, retries, telemetry are native |
| `scripts/cairn_query/` (1900 LOC) | Substrate cost case dissolves with targeted reads + in-brief context; typed-records value not load-bearing |
| `mcp_servers/cairn_knowledge/` | No substrate → no MCP wrapper |
| `kuzu` dep | No graph backend needed |
| `fastmcp` dep | No MCP server in scope |
| `slice.yaml` + lifecycle | Git history is the state; `docs/plans/<feature>.md` is the per-feature artifact |
| `current-slice/` directory | No slice unit-of-work |
| `sweep.yaml` + `sweep-results/` + `/integration-sweep` | Sweep ritual; pre-commit/CI runs validator instead |
| `close_slice` ceremony | No slice close; per-phase commits |
| `commit_phase_handoff` | Replaced by dispatch-skill commit step |
| 13-state resume matrix | Manual re-run on crash; phases are file-based and idempotent |
| Heartbeat daemon | Native subagent return; no silent-death case |
| Phase-3 cluster `ThreadPoolExecutor` | Parallel Agent tool calls in one message |
| INV-009 cost-threshold trip in orchestrator | Cost data native; advisory only anyway |
| `_MirroringModule` test scaffolding | No `slice_orchestrator` package to monkeypatch |
| `commands/claude-code/start-slice*.md` | Replaced by dispatch skill |
| `commands/claude-code/integration-sweep*.md` | No sweep ritual |
| `commands/claude-code/handoff*.md` | Handoff becomes dispatch-skill side-effect |
| `commands/claude-code/catchup*.md` | Replaced by reading `docs/plans/<feature>.md` + git log |
| `commands/claude-code/refresh-architecture*.md` | Manual ritual run before merging; no slash command needed |
| `commands/claude-code/status*.md` (and `render_status.sh`) | Slice-machinery; rebuild lite version against new state if needed |
| `scope-guard.sh` | role_guard's per-phase allowlists subsume slice-envelope checks |
| `structural-snapshot.json` | Subsumed into git's natural file tracking; no D3 gate |
| `d1-bypasses.log`, `d3-bypasses.log` | No D1/D3 gates; pre-commit validator + manual operator judgment |
| `dogfood_evaluate.py`, `integration_gate.py`, `lint_paths.py`, `verify_handoff.sh`, `snapshot_diff.py` | Slice-machinery utilities |
| `.slice-system → .` symlink | Plugin distribution replaces it |

---

## 4. Phase isolation mechanism (post-orchestrator)

What makes cairn cairn: phase agents see only what they're supposed to see. Without the orchestrator constructing briefs and enforcing scope via slice-bound hooks, this becomes:

1. **Independent context window per phase.** `Agent({subagent_type: "phase-2-skeptic", prompt: "..."})` spawns a fresh context with no conversation memory. Phase 1's reasoning is unrecoverable by Phase 2 — by mechanism, not by discipline.

2. **Per-phase `tools:` allowlist.** The subagent's frontmatter declares which tools are available. Read/Write/Edit/Bash/Grep/Glob can be enabled or denied per role. This is the *first* line of restriction.

3. **Per-phase read/write path patterns.** `role_guard.py` (simplified) denies tool calls outside the role's allowed paths. Example: `phase-2-skeptic` can `Read` `intent.md` and `Write` `tests/`; denied elsewhere. Per-role policies live in `role_guard.py`'s `ROLE_POLICIES` table. This is the *second* line — even if a tool is allowed, the path must match.

4. **The brief.** Constructed by the dispatch skill. Includes only the inputs the phase should see (intent.md path for Phase 2; intent.md + tests/ paths for Phase 3; full context for Phase 4). The dispatch skill is a small Markdown file under `commands/claude-code/`; ~50-100 lines.

5. **Snapshot pinning (lightweight).** Dispatch skill captures `git rev-parse HEAD` at phase start; passes via prompt. If a phase's queries return data from a different snapshot, the agent should raise. Mostly useful when Phase 4 runs the validator.

What changes vs the orchestrator era:

- No `AGENT_ENVELOPE` JSON object passed via env var (replaced by inline prompt content + `AGENT_ROLE`).
- No MCP-forcing (no MCP). Agents read canonical sources directly within their allowed paths.
- No `scope-guard.sh` evaluating slice-envelope globs (`role_guard` does the same job per-role).
- No `close_slice` wipe (no `current-slice/` to wipe).
- No 4-phase commit ceremony as a separate concept; the dispatch skill commits each phase's writes naturally.

---

## 5. Don't-regress checklist

Past slices fixed real issues. The shrink must carry these forward or accept loss with explicit reasoning.

| Fix | Origin | In new architecture |
|---|---|---|
| `role_guard` `READ_CLASS_TOOLS = {Read, Grep, Glob}` | Slice 2 fixup | **Carries forward** — critical; without it, agents bypass canonical lockdown via Grep/Glob |
| `role_guard` envelope-grant escape (D9) | Slice 2 | **Carries forward** — agents that legitimately need direct access declare it in envelope/brief |
| Triager superseded-test heuristic (`detect_superseded_test_signal`) | compression/triager-superseded-test-heuristic | **Carries forward** — pure function; lives in dispatch skill or as a standalone helper invoked by triager |
| YAML safety in `coupling-clusters.yaml` (single-quoted regex) | phase-2-skeptic agent doc | **Carries forward** — guidance stays in the agent-def prompt |
| `ADR_EDITORIAL_FIX=1` typo escape | reversibility-guard.sh | **Carries forward** — reversibility-guard unchanged |
| Phase-2-skeptic write-timing fix (issue #26 ae9e6c8) | issue #26 | **Re-evaluate** — the original failure is orchestrator-bound (`git diff` excluded untracked files at P2 boundary). The dispatch skill commits each phase's writes natively, so the failure mode may not exist; verify in M3 audit. |
| B9 post-Timeout HEAD reconciliation | compression/slice-2-state-machine | **Dies with orchestrator** — no orchestrator timeout; native subagent returns or doesn't |
| B13 `_active_child` for signal handlers | compression/slice-2 | **Dies with orchestrator** — no Python subprocess to signal |
| B15 max-1 redispatch-per-phase cap | compression/slice-2 | **Dies with orchestrator** — manual re-run; no automated redispatch |
| Slice-artifact-preservation copy-before-wipe | compression/slice-artifact-preservation | **Dies with `close_slice`** — no wipe to preserve from |
| Phase-1-handoff-stage-surface, Phase-4-sweepnotes-required staging | compression/phase-1-handoff-stage-surface, phase-4-sweepnotes-required | **Dies with `commit_phase_handoff`/`close_slice`** — dispatch skill commits per-phase writes natively |
| `_copy_artifacts_to_sweep_results` (ADR slice-artifact-preservation) | compression/slice-artifact-preservation | **Dies with sweep ritual** — git history of merged branches preserves equivalent forensic surface |
| 23-slice-overdue sweep | sweep ritual | **Dies with sweep ritual** — pre-commit/CI runs validator; no periodic sweep |
| INV-002 binding non-functional (parser flat) | open issue | **In scope for migration** — fix the parser as part of `validate_architecture.py` carry-forward |
| INV-009 cost-threshold trip | cost-discipline feature | **Dropped (advisory only)** — re-introduce if cost becomes load-bearing |
| Failed-slice archive (`completed-slices/<id>-failed/`) | start-slice.full Step 8 | **Dies with slice machinery** — git history of failed branches serves the same purpose |
| `V1_ASSERTION_TYPES` allowlist hardcoded in tests | open issue | **Re-evaluate in M3** — if validator stays, the allowlist stays; tests carry forward |

**Bathwater audit.** I've classified categories above. A slice-by-slice "did this fix a real issue, does it survive" pass is a Phase-1 task in the migration writing-plans (M3). Cheap insurance before any code moves.

---

## 6. Windsurf scope

**Decision:** Approach A — Claude Code only for now.

**Rationale:** per the existing `/decision` analysis (`docs/plans/2026-04-21-windsurf-port-decision.md`) and the in-flight feasibility spike, the remaining lock-in primitive is **subagent dispatch with tool scoping**. Claude Code has it via the Agent tool + `.claude/agents/*.md`. Windsurf's rule and skill systems are prompt-injection layers, not separate-context-window agents. Until Windsurf ships parity (or a documented adapter that maps `.claude/agents/*.md` to Windsurf's runtime), the Protocol-layer dispatch logic is Claude-bound.

**What Windsurf can use today (refined 2026-05-06):**

- **Document Layer** — markdown is universal. Ports trivially.
- **Enforcement Layer** — when Cascade Hooks become accessible in the user's build (Q1 spike pending; user-reported "not visible in Windsurf Settings" 2026-04-21). Hook bodies (`reversibility-guard.sh`, `role_guard.py`) are platform-neutral shell/Python; only the registration shape differs.
- **Skill prose at `.claude/skills/`** — Windsurf's documented cross-agent-compatibility discovery list includes `.claude/skills/` and `~/.claude/skills/`. The dispatch skill's prose is therefore readable on both platforms once Windsurf compat-discovery is enabled. The body of the skill executes on whichever runtime invokes it; Claude Code's Agent tool is referenced inside the prose, so on Windsurf the skill describes the protocol but cannot dispatch subagents until parity primitives ship. (Confirmed by Windsurf docs at `docs.windsurf.com/windsurf/cascade/skills`.)
- **Subagent definitions at `.claude/agents/`** — no documented Windsurf cross-discovery. Claude-Code-only for now.

**Re-evaluation conditions:**

1. Q1 spike resolves ✓ (Windsurf hooks accessible AND deny-with-reason contract verified).
2. AND Q2 spike resolves ✓ (subagent-with-tool-scoping primitive verified — or Windsurf adds documented `.claude/agents/` cross-discovery).
3. THEN open a slice to extend the dispatch skill's runtime adapters or wire a Windsurf workflow alongside.

**Until then:** the rethink ships Claude-Code-native. Existing partial Windsurf scaffold (`.windsurf/workflows/` directory) stays as-is; no new Windsurf-specific work in scope. The doc layer ports trivially because it's just markdown; the skill prose ports semi-automatically via cross-agent-compatibility discovery; only the dispatch *execution* requires Claude.

---

## 7. Migration shape

This is a **multi-slice program**, not one slice. ADR supersessions are needed. Sketch only — actual ordering and contents decided in writing-plans for each migration slice.

### M1 — Branch + freeze

- Already done: `design/cairn-shrink` branch.
- Stop opening cairn slices on `dev` until shrink lands or is abandoned.
- This design doc is the only artifact of M1.

### M2 — Build the dispatch skill

- Write `.claude/skills/cairn-tdd-feature/SKILL.md` (~50-100 lines) — or fold into `superpowers:executing-plans` with cairn-specific phase-N rules.
- Skill folder format (per Anthropic progressive-disclosure): `SKILL.md` plus optional supporting resources.
- Test by dispatching phase-N agents on a toy feature (no real production work).
- **No deletes yet.** Dispatch skill coexists with orchestrator.
- Deliverable: working dispatch skill + dogfood evidence.

### M3 — Bathwater audit + INV-002 parser fix

- Slice-by-slice review of past fixes (cf. §5). Classify carry-forward / orchestrator-bound / substrate-bound.
- Fix `validate_architecture.py` parser gap so INV-002 binding is functional.
- Document the `role_guard` simplification (drop MCP-forcing; preserve `READ_CLASS_TOOLS = {Read, Grep, Glob}` and envelope-grant).
- Deliverable: migration plan with explicit "do not regress" commitments + INV-002 binding live.

### M4 — Delete orchestrator + substrate

- Drop `scripts/slice_orchestrator/`, `scripts/cairn_query/`, `mcp_servers/cairn_knowledge/`.
- Drop `kuzu` and `fastmcp` deps from `pyproject.toml`; regenerate `uv.lock`.
- Drop slice machinery: `slice.yaml`, `current-slice/`, `sweep.yaml`, `close_slice`, `start-slice*` commands, `integration-sweep*` commands.
- Drop `scope-guard.sh` (subsumed by `role_guard`).
- Update `.claude/settings.json` hook registration accordingly.
- Drop tests targeting the deleted code (slice_orchestrator tests, cairn_query tests, mcp_cairn_knowledge tests).
- Run full test suite; expect deletions but no regressions in surviving code.
- Deliverable: cairn at one third its current size; everything still works; dispatch skill is the only path.

### M5 — Plugin packaging

- Re-shape cairn as a Claude Code plugin.
- Test installation in a clean project.
- Document install path for consumers.
- Deliverable: `claude plugin install cairn` working.

### M6 (deferred) — Consumer migration

- Migrate complex-rag-analysis (and any other downstream consumers) from `.slice-system → .` symlink to plugin install.
- Separate slice/program; not in primary shrink scope.

### ADR supersessions needed

Authored in M3 or M4 (one supersession ADR per affected ADR; append-only).

| ADR | Disposition |
|---|---|
| `cairn-substrate-and-fastmcp` | **Superseded** — substrate retired |
| `orchestrator-observability` | **Superseded** — orchestrator retired |
| `slice-close-contract` | **Superseded** — slice machinery retired |
| `slice-artifact-preservation` | **Superseded** — slice machinery retired; git history serves forensic role |
| `d3-bypass-classification` | **Superseded** — no D3 gates |
| `cost-per-slice-budget` | **Amended** — INV-009 retired or marked deprecated; cost data still observable natively |
| `compression-infrastructure-bootstrap` | **Superseded** — compression program retired |
| `parallelism-v1` | **Partial supersession** — within-slice parallelism retained as parallel Agent tool calls; concurrent-worktree provisions retained |
| `pipeline-substrate-naming` | **Superseded** |
| `phase-pipeline-evaluation` | **Amended** — phases survive; pipeline machinery retires |
| `feature-slice-model` | **Amended** — features survive; slices retire |
| `context-tiers-integration` | **Amended** — Tier-1 catchup folds into reading `docs/plans/<feature>.md` |
| `invariant-binding-strategy` | **Stays** — strategy survives; structural-parser type stays |
| `phase-lock-and-role-declaration` | **Stays** — phase roles survive intact |
| `context-discipline-protocol` | **Stays** — handoff token budget survives |
| `cliff-failure-mode-and-v1-defenses` | **Stays** — D4 (Windsurf deferral) unchanged |
| `bootstrap-exception` | **Stays** — INV-001 still applies |
| `identifier-scheme` | **Amended** — id/name two-field model survives; slice ids retire; feature ids stay |
| `semantic-identity` | **Stays** |
| `board-as-roadmap-substrate` | **Stays** — GH project board independent of slices |

---

## 8. Out of scope for this design

- **Consumer migration** (complex-rag-analysis et al.) — separate program post-shrink (M6).
- **Windsurf re-port** — deferred; reopened when Q1+Q2 spikes resolve ✓.
- **Re-introducing typed-knowledge graph** — only if a real cypher-class query emerges that grep can't satisfy.
- **Re-introducing INV-009 cost-threshold trip** — only if cost becomes load-bearing again.
- **Plugin packaging details** — handled in M5.
- **GH project board re-organization** — independent; the board survives as a roadmap surface.
- **Memory system** — operator-side; independent of cairn architecture.
- **`/refresh-architecture` and `/status` re-implementation** — re-evaluate in M3; small skills if useful, drop if not.

---

## 9. Open questions for follow-up sessions

1. **Dispatch skill API.** Does it take a brief (string) or a path to `docs/plans/<feature>.md`? Both? A typer CLI flag?
2. **Phase-3 cluster fan-out.** Keep `clusters.yaml` as a contract for parallel Agent tool calls, or drop entirely and rely on the dispatch skill spawning N parallel `phase-3-implementer` subagents in one message?
3. **`role_guard.py` simplification.** Rewrite from scratch (cleaner) or strip down in place (safer)?
4. **INV-009 retirement.** Amend the ADR to mark advisory-only-and-deprecated, or supersede entirely?
5. **Branch strategy for the migration.** Single `design/cairn-shrink` branch with sequential commits across M1-M5, or one branch per migration phase?
6. **Test surface for the dispatch skill.** Cairn currently has heavy test coverage on `slice_orchestrator` (~750 tests). The dispatch skill is markdown — what's the right verification level? Dogfood-only, or some structural lint?
7. **Handoff.md fate.** Currently lifecycle-bound (per-slice handoff at phase boundaries). In the new world, is `handoff.md` still load-bearing or does the per-feature plan doc subsume it?

---

## 10. Concise summary

- **Drop:** orchestrator (3000 LOC), substrate (1900 LOC), slice machinery, kuzu+fastmcp deps, scope-guard, sweep ritual, slice commands. Keep ADRs/lessons/architecture/spec/op-ref untouched.
- **Build:** one dispatch skill (~50-100 lines, at `.claude/skills/cairn-tdd-feature/SKILL.md`), simplify `role_guard.py`, fix `validate_architecture.py` parser.
- **Why safe:** Anthropic primitives now cover dispatch, telemetry, parallel fan-out, signal handling. Phase isolation is achieved by independent context windows + per-phase tool/path allowlists. Substrate's cost case is recoverable via targeted reads + in-brief context.
- **Windsurf:** Approach A — Claude-Code-bound for the dispatch primitive; Document Layer + skill prose port automatically (Windsurf scans `.claude/skills/` for cross-agent compatibility); Enforcement Layer ports when Cascade Hooks become accessible.
- **Result:** cairn shrinks to ~1/3 its current footprint. Day-to-day work runs through Anthropic primitives + a thin cairn skill. Document discipline and invariant binding are preserved as the actual cairn-unique value.

# Phase 0.5 — User-Journey Trace (delivery-mechanism-friction)

## J1 — Fresh machine → first slice dispatched

| Step | Today (mechanism) | Missing / paid out-of-band | Class |
|------|-------------------|----------------------------|-------|
| Discover cairn exists | GitHub: firaaz/cairn README + CONSUMER.md link | No ambient plugin discovery; SOP is "someone told me about it" or I found it in a README | incidental |
| Install via marketplace | `/plugin marketplace add https://github.com/firaaz/cairn` + `/plugin install cairn@cairn-marketplace` (CONSUMER.md §Install) | No Substrate knowledge injected at install; operator must read CONSUMER.md actively to get next steps | incidental |
| Session opens post-install | No SessionStart hook wired (checked `.claude/settings.json` — no `hooks.SessionStart`); operator opens Claude Code, no affordance surfaces cairn context | SessionStart could auto-dispatch a `using-cairn` bootstrap skill (issue #33-1) — today missing entirely | incidental |
| Discover available slash commands | Operator must read CONSUMER.md or know to try `/`. The 5 commands (`/catchup`, `/decision`, `/new-adr`, etc.) are shipping in M5.1 per CONSUMER.md §What You Get — not yet live in F1 plugin | No discovery UX; no hint that these exist beyond reading CONSUMER.md prose | incidental |
| Discover four-phase TDD | Operator must navigate: CONSUMER.md → `docs/operational-reference.md` (reading order per CONSUMER.md §Where To Next) → `docs/spec-v1.md` (cited as "Layer 2; pull in deliberately") | **No auto-orientation.** Operator reads prose sequentially; no affordance surfaces the Four Phases entry point or why they matter | incidental |
| Write per-feature plan | Operator copies `templates/feature-plan.md` to `docs/plans/<date>-<id>.md` and fills frontmatter + four sections (CONSUMER.md §First Dispatch step 1) | Plan-doc shape is described in prose; no template inline hint re: invariants touched, envelope regex correctness | incidental |
| Copy `active-envelope.yaml` | Operator copies `templates/active-envelope.yaml` to `.claude/active-envelope.yaml`, flips `mode: off` → `mode: operator`, adds regex list (CONSUMER.md §First Dispatch step 2) | **Envelope concept is complex.** Operator must read CLAUDE.md §Operator Envelope *and* operational-reference.md §Operator Envelope (two sources of truth); risk of malformed YAML or incorrect regex → enforcement fails silently per CLAUDE.md rule | substrate-essential (but discovery is incidental) |
| Run `/cairn-tdd-feature` | Invoke Skill tool: `/cairn-tdd-feature docs/plans/<date>-<id>.md` (inferred from operational-reference.md §cairn-tdd-feature dispatch skill; the actual Skill name must match `.claude/skills/`) | **Skill tool invocation syntax is not obvious.** Operator must know Skill tool exists + syntax + that `/cairn-tdd-feature` is the correct slug from `.claude/skills/` directory name (not `/dispatch` or `/start-slice`) | incidental |
| Phase 1–4 execute as subagents | Each phase dispatches via Agent tool in `.claude/agents/phase-{1..4}-tdd.md`; session context is isolated; artifacts cross phases via git commits only (operational-reference.md §Phase gate enforcement) | **Critical dependency: agent definitions must load at session start.** If operator starts Phase 1 mid-session after modifying agents, Agent tool cannot discover `phase-{1..4}-tdd` subagent_type — skill aborts. Documented in SKILL.md §Pre-flight conventions but not surfaced in CONSUMER.md | substrate-essential |
| Operator reviews artifacts | Commits land at: Phase 1 `intent.md`, Phase 2 tests + `validation/approach.md`, Phase 3 source, Phase 4 `sweep-notes.md`. Operator reads via `git log`, opens files (CONSUMER.md §First Dispatch step 6) | **No context tie-in.** Operator opens files individually; no summary view of whether phases succeeded or what next steps are. Error diagnosis requires re-reading operational-reference.md §The Four Phases + phase agent prompts | incidental |
| Slice closes | Operator commits + pushes (inferred; no explicit close-slice ceremony documented in CONSUMER.md for F1) | **Closure state ambiguous.** No `.slice.yaml` or `.claude/active-slice/` record (per SKILL.md §Output: "The git log is the durable record; no slice.yaml"). Operator must infer completion from commit graph | incidental |

## J2 — Returning operator, mid-slice, new session

| Step | Today (mechanism) | Missing / paid out-of-band | Class |
|------|-------------------|----------------------------|-------|
| Session opens in same worktree | No SessionStart hook wires context (checked `.claude/settings.json` — no `hooks.SessionStart`). Blank canvas; operator must orient manually | SessionStart could read `.claude/handoff.md` + git state, but today it doesn't | incidental |
| Operator types "status?" or similar | Model has no context re: current phase, prior commits, plan-doc, or substrate rules | `/catchup` slash command exists (commands/claude-code/catchup.md) and explicitly reads: `.claude/handoff.md`, `git log --oneline -10`, `git status -s`, `.claude/active-envelope.yaml` — **Operator must know to type `/catchup`; it's not auto-invoked** | incidental |
| Operator runs `/catchup` (if they find it) | Reads four sources in order (catchup.md §Rules step 1). Stops. Operator drives next | **Missing: `/catchup` is not in F1 plugin (shipping M5.1).** Operator in F1 cannot run it; must manually read four sources | incidental |
| Operator decides next phase or re-runs current | Handoff's `next:` field (if populated) guides; operator infers phase from commit graph. If mid-Phase 3, operator resumes via git worktree + `/cairn-tdd-feature` with the same plan doc — **re-dispatch restarts from Phase 1 unless skill checks `git log` for prior phase commits** | **Skill state-resumption is not auto.** If Phase 3 crashes, operator must: (a) diagnose which phase crashed, (b) manually check git for prior commits, (c) invoke Skill with same plan-doc, (d) Skill must detect prior Phase 1/2/3 commits and skip-or-re-dispatch. Mechanism unclear from SKILL.md steps 4–11 | substrate-essential |
| Operator reads diagnostic errors | If Phase N fails, no direct summary of why; operator must: (a) read phase agent prompt at `.claude/agents/phase-<N>-tdd.md`, (b) read the RAISE_ISSUE logic (SKILL.md §RAISE_ISSUE handling), (c) manually run triager-tdd or escalate | **No automated triage feedback.** Phase failures produce git commits with body text; operator must parse these manually | incidental |

## J3 — Operator wants to make an architectural decision (`/decision`)

| Step | Today (mechanism) | Missing / paid out-of-band | Class |
|------|-------------------|----------------------------|-------|
| Operator types `/decision <question>` | Slash command exists (commands/claude-code/decision.md). Triggers Phase 0 → Phase 0.5 → Phase 1–4 → Phase 5 (independent verification, firm only) → Phase 6 (propagation) | **Complex ceremony; operator must read decision.md to understand 9-step structure.** decision.full.md not mentioned in decision.md itself (requires "Load full" link) — **discovery friction** | incidental |
| Phase 0 runs (Constraint Harvest) | Manual: read ARCHITECTURE.md invariants, relevant ADRs, lessons.md. Produce constraint envelope. No automation wired | **Entirely manual.** Operator must know which ADRs are "relevant"; scope is operator-discretion | incidental |
| Phase 0.5 runs (User-Journey Trace) | Manual: walk enabled workflow end-to-end, identify mechanism gaps. This is the current task | **Entirely manual.** No tool support for tracing; operator reports discoveries in prose | incidental |
| Phase 1–4 execute | Same as J1 (four fresh subagents per phase) | **No difference from 4-phase TDD dispatch.** Same agent-definition pre-flight requirement; same context isolation | substrate-essential |
| ADR lands | Operator runs `/new-adr` (commands/claude-code/new-adr.md); creates `docs/adr/<NNN>-<slug>.md` with YAML frontmatter. Runs `/refresh-architecture` (not documented in new-adr.md but mentioned in new-adr.md step 6) | **`/refresh-architecture` is not in F1 plugin.** Operator must know it exists + will be shipped in M5.1 or later. **No tool that validates the ADR post-creation** (mentioned in new-adr.full.md "if validation fails" but /refresh-architecture is opaque) | substrate-essential (but discoverability is incidental) |
| Operator knows which ADRs are affected | No mechanism surfaces "affected ADRs" when a decision lands. Operator must manually search `docs/adr/` for `supersedes:` / `preceded-by:` references or read lessons.md | **No dependency graph.** `docs/ARCHITECTURE.md:refresh` is mentioned but not automated; operator must run it manually or trust /new-adr did it | incidental |

## J4 — Operator wants a small change (no slice ceremony)

| Step | Today (mechanism) | Missing / paid out-of-band | Class |
|------|-------------------|----------------------------|-------|
| Operator makes a 5-line fix (doc typo, one-file bugfix) | Can edit directly; no dispatch ceremony required. CLAUDE.md §New-code guidance: "Ad-hoc edit" path. But: operator-envelope might be in `mode: operator` from prior slice | If `.claude/active-envelope.yaml` exists with `mode: operator`, write is gated to `paths:` regex list. If fix is outside envelope, write is denied. Operator must: (a) know the envelope file exists, (b) edit it (which itself requires a self-pattern in the regex), or (c) set `mode: off` | incidental (but enforcement is substrate-essential) |
| Operator commits with Conventional Commits prefix | Scripts/validator supports `feat:`, `fix:`, `chore:`, `docs:`, `test:`, etc. (operational-reference.md §Routing: ad-hoc vs decision vs cairn-tdd-feature). No enforcement wired in hooks; operator must know the scheme from reading validators/_FALLBACK_REGISTRY or manual prose | **No UI hint that Conventional Commits are expected.** Operator can commit `git commit -m "oops"` and push without error | incidental |
| Operator does not commit; leaves working tree dirty | No affordance surfaces that ad-hoc state needs commitment. Operator may start a new session and encounter `.claude/active-envelope.yaml` still in `mode: operator` with stale intent | **No session-start check for envelope mode.** Operator must manually reset or delete the file | incidental |

## J5 — pytest fails

| Step | Today (mechanism) | Missing / paid out-of-band | Class |
|------|-------------------|----------------------------|-------|
| Operator runs `uv run pytest`, gets failures | Standard pytest output. No cairn-specific wrapper or triage tool exists | If Phase 3 impl fails tests and Phase 4 is about to dispatch, SKILL.md step 9 verifies: "Run `uv run pytest <new-test-files> -v` and confirm pass." RAISE_ISSUE on failure; triager-tdd called | incidental |
| Operator needs root cause | No automation: operator reads test output, guesses which file is wrong, opens it, reads code, traces to the issue. If during Phase 3, operator may escalate to Phase 4 via RAISE_ISSUE → triager → ESCALATE_TO_USER | **Branch proposes `pytest-triage` agent** (agents/pytest-triage.md on feature/workflow-subagents) — cites `superpowers:systematic-debugging` methodology, uses LSP + ast-grep to navigate code, produces root-cause report. Today: completely manual | incidental |
| Operator fixes and re-runs | If mid-phase, re-run pytest locally; if test is in envelope, Phase 3 will see the fix on next run (if re-dispatched). No automation for "re-dispatch Phase 3 with amendment" — operator must manually invoke Skill again | **Skill does support `RE_DISPATCH` via triager-tdd**, but operator must explicitly escalate (Phase N RAISE_ISSUE) first — cannot auto-trigger from test failures outside phase context | incidental |

## State boundaries where a mechanism MUST exist

- **Session-open**: Today — blank slate (no SessionStart hook). Needed: context injection so model knows it's in a cairn repo, what the current handoff state is, whether envelope is active. Blocked by issue #33-2 (discoverability) + #33-1 (bootstrap skill).

- **Session-close**: `.claude/handoff.md` overwritten (templates/handoff.md shape). Mechanism works for next session's `/catchup` (if operator knows to run it). Missing: post-handoff cleanup of `.claude/active-envelope.yaml` (operator must manually set `mode: off` or delete).

- **Phase-handoff**: Git commit is the boundary. Mechanism works: prior phase's output becomes next phase's input via explicit file paths in SKILL.md. Missing: no summary of "Phase N succeeded, Phase N+1 next" — operator must parse git log + phase agent prompts to infer status.

- **Slice-close**: No explicit slice-close ceremony. Operator commits Phase 4 sweep-notes and that's the boundary. Mechanism: git log is the record (per SKILL.md §Output). Missing: no record of which plan-doc this slice came from, no `.slice.yaml` tracking, operator must infer slice state from commit graph + handoff.

- **Cross-worktree** (new in feature/workflow-subagents): Proposed agents like `slice-status`, `worktree-map`, `adr-context` would read shared state (git log, ADR index, ARCHITECTURE.md) across worktrees. Today — no mechanism; operator must manually query git when switching worktrees.

## Highest-friction transitions (ranked)

1. **J1 step 3–5: Discover → Install → Learn substrate → Write plan.** Magnitude: ~20 min of prose-reading per fresh install. Paid by: operator manually reading CONSUMER.md (§Where To Next) → operational-reference.md → spec-v1.md in sequence. Class: substrate-essential knowledge _presented via incidental UX_. Issue #33-1 proposes `using-cairn` SessionStart skill; would collapse this to 2–3 min auto-briefing.

2. **J1 step 7 & J2 step 2: Pre-flight agent-definition check.** Magnitude: silent skill abortion if agents not pre-loaded; operator may not know why. Documented in SKILL.md §Pre-flight conventions but not surfaced in CONSUMER.md or at install time. Class: substrate-essential. Issue: no post-install validation (CONSUMER.md mentions validator for hook deps but not for agent defs).

3. **J2 step 3: Mid-slice resumption without `/catchup` (F1 limitation).** Magnitude: operator must manually read four sources (handoff, git log, status, envelope) to resume. Class: incidental friction but high repetition cost (paid every session). Issue: `/catchup` ships M5.1 (not F1); SessionStart hook would auto-populate on open.

4. **J3 step 1–4: `/decision` ceremony is heavyweight (9 phases); discovery is prose-only.** Magnitude: operator must read decision.md + decision.full.md to understand structure. Class: incidental. Issue #33-2 proposes better slash-command surfacing. Branch proposes `adr-context` agent for Phase 0 automation (via route-trigger?).

5. **J5: pytest failures → root cause → Phase 3 re-dispatch.** Magnitude: 10–30 min manual debugging + manual phase re-invoke. Class: incidental. Branch proposes `pytest-triage` + `root-cause-hunter` (via route-trigger?); would automate diagnosis but adds setup-surface cost (Pyright, ast-grep, LSP enablement per PREREQS.md).

## Verified vs. believed

**Verified** (read directly):
- No SessionStart hook wired in `.claude/settings.json` (checked; only PreToolUse + PostToolUse).
- Slash commands (`/catchup`, `/decision`, `/new-adr`) documented but `/catchup` not in F1 plugin per CONSUMER.md (ships M5.1).
- Agent definitions at `.claude/agents/phase-{1..4}-tdd.md` + `triager-tdd.md` (exist; 6 files confirmed).
- SKILL.md §Pre-flight conventions requires session-pre-loaded agents; no hook checks this at install or dispatch.
- Operator envelope enforcement wired in `role_guard.py` (checks `.claude/active-envelope.yaml`; confirmed in hooks).
- Feature/workflow-subagents branch proposes 6 new agents (adr-context, handoff-closer, pytest-triage, root-cause-hunter, slice-status, worktree-map) + PREREQS.md listing setup surface (Pyright, ast-grep, LSP, superpowers user-scope install).

**Believed** (inferred; could not verify):
- SessionStart hook would auto-route a `using-cairn` bootstrap skill (issue #33-1 claims this; not yet implemented).
- Skill state-resumption logic checks git for prior phase commits before re-dispatching (SKILL.md §Steps implies this; actual code not read).
- `/refresh-architecture` exists and is called by `/new-adr` (new-adr.md step 6 mentions; not yet in F1).
- Branch's auto-route mechanism for `pytest-triage` / `root-cause-hunter` (mentioned in feature/workflow-subagents framing as "auto-routed phrase-triggered subagents"; implementation details not verified).
- Setup-surface trade-off magnitude: "Pyright + ast-grep + LSP enablement + user-scope superpowers" is "worth it" for parallel worktree agentic development (branch's hypothesis; not tested).

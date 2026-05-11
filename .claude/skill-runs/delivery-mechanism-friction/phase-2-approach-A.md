# Phase 2 — Approach A: Capability-up

## One-paragraph statement

Cairn's delivery surface should grow upward, not shrink. The branch `feature/workflow-subagents` lands substantively as-is: six workflow subagents (slice-status, worktree-map, adr-context, handoff-closer, pytest-triage, root-cause-hunter) plus `docs/PREREQS.md` as the canonical consumer setup spec — Claude Code ≥ 2.0.74, Pyright, ast-grep, `ENABLE_LSP_TOOL=1`, user-scope `superpowers`, Ruff. The bet is that cairn's value-prop is methodology-under-pressure, and methodology is only durable when agents have *real* code intelligence (type-aware navigation, structural search, cited debugging discipline) — not text-grep heuristics. We accept a one-time +4-item install ceremony per consumer machine in exchange for permanent uplift on every dispatch thereafter. The `using-cairn` SessionStart bootstrap is deferred: it is unverified (framing claim 1) and would compound the context-budget pressure that already binds INV-004. Discoverability is solved by slash commands and PREREQS.md, not by auto-injection.

## Concrete shape (what actually lands)

- **Branch state on merge:** `feature/workflow-subagents` merges with one reshape — pre-flight cairn-substrate detection added to `pytest-triage` and `root-cause-hunter` (mitigation for S3). All six agents preserved in `agents/` (per branch's plugin-layout intent, commit 8b680cb).
- **New consumer-side requirements** (all from PREREQS.md):
  - Claude Code ≥ 2.0.74 — needed for native LSP-tool surface.
  - Pyright (pipx/npm) — type-aware navigation; foundation of `root-cause-hunter` find-references.
  - ast-grep — structural search/rewrite; foundation of all three navigation agents and the only non-text rename path (PREREQS §"Code-intelligence stack").
  - `ENABLE_LSP_TOOL=1` in user-scope settings — gates LSP tool availability.
  - `superpowers` plugin at user scope — methodology gate cited by `pytest-triage` (systematic-debugging) and `root-cause-hunter` (systematic-debugging + defense-in-depth).
  - Ruff — already on the cairn dep floor (CLAUDE.md §Hook dependencies); not new.
- **Agent changes to the 6 branch agents:** Add a structural pre-flight to each of the two diagnostic agents (`pytest-triage`, `root-cause-hunter`): refuse cleanly with stderr hint if `.claude/active-envelope.yaml` and `checks/role_guard.py` (or `${CLAUDE_PLUGIN_ROOT}/checks/role_guard.py`) are absent. The four substrate-aware agents (slice-status, worktree-map, adr-context, handoff-closer) already require cairn-shape and are safe.
- **ADR(s) this approach commits:**
  1. `delivery-mechanism-friction` itself (this decision) — firmness *provisional*; locks "setup-surface up via PREREQS.md; capability over ceremony; no SessionStart bootstrap in this slice".
  2. Bundled new-dep declaration per soft-constraint #3 (cairn-substrate-and-fastmcp D2): Pyright/ast-grep/superpowers added to the *consumer-side* dep envelope (distinct from the maintainer standing dep set), with explicit superpowers version-floor and reversal-cost section (S4, S8 mitigations).
- **Out-of-scope from #33's 7 candidates:**
  - #33-1 `using-cairn` SessionStart skill — deferred (S2, S9).
  - #33-3 role_guard heredoc escape removal — orthogonal.
  - #33-4 `/fix-adr-typo` retire `ADR_EDITORIAL_FIX=1` — orthogonal.
  - #33-5 scope id+name to ADRs/slices — orthogonal.
  - #33-6 small-change/exploration path — orthogonal.
  - #33-7 commit-prefix instead of JSON-stdout — orthogonal.
  - #33-2 slash-command discoverability — touched indirectly (PREREQS.md surfaces the agents by name, which is the discovery channel) but not the slash-command surface itself.

## Constraint fit

| Constraint | Fit | Evidence |
|---|---|---|
| H1 Phase-pipeline locked (INV-003) | OK | No change to phase count/names/roles; 6 agents are *adjacent* surface |
| H2 Plugin distribution locked (INV-012, m5-deployment D1/D2) | OK | Branch ships agents under `agents/` consistent with `dist/` curation in m5-distribution D3 |
| H3 Maintainer dogfood (INV-011) | AT RISK → mitigated | S5 hazard real; mitigation = require Pyright/ast-grep config to exclude `.slice-system` (CLAUDE.md §Symlink recursion hazard); ADR consequences section must mandate this |
| H4 Role isolation (role_guard.py) | OK | New agents respect existing envelope; `handoff-closer` is the only writer and is substrate-aware |
| H5 ADRs append-only | OK | This approach lands new ADRs, supersedes nothing |
| H6 Conventional Commits (INV-001) | OK | `handoff-closer` explicitly encodes "stage-by-name, no -A, no amend, no commit-to-dev/main/master, no push" per framing branch facts |
| H7 Fresh-session ≤40k (INV-004) | OK | No SessionStart added; PREREQS.md is read once at install, not per-session; agent prompts load lazily on dispatch |
| H8 Three-tier handoff (context-discipline) | OK | Agents are Tier 2 (on-demand subagent dispatch); PREREQS.md is Tier 1 install-time, not session-time |
| Soft #1 progressive disclosure | OK | Agents dispatch on demand; PREREQS.md is install-time prose, not eager-load |
| Soft #2 audience-tagged CLAUDE.md / CONSUMER.md | OK | PREREQS.md slots into CONSUMER.md `[both]` reading order |
| Soft #3 new deps require ADR | OK by construction | The bundled new-dep ADR is the vehicle |
| Soft #4 structural > prompt enforcement (L-005) | PARTIAL | PREREQS.md is prose; mitigation = post-install validator script `scripts/validate-prereqs.py` that fails loud on missing Pyright/ast-grep/superpowers (S6 mitigation) — included in the slice |
| Soft #5 minimize ceremony | TRADED | Explicit trade: ceremony goes up at install; goes down per-session |
| Soft #6 bootstrap autonomy | TRADED | No SessionStart bootstrap; install-time validator is the structural substitute |

## Pre-mortem exposure

- **S1 Context-budget breach** — HANDLED. No SessionStart; agents lazy-load; PREREQS.md never enters session context. Measurement: token-count current `dist/` payload + agent preambles at session-open baseline; assert ≤40k.
- **S2 SessionStart collision with superpowers** — HANDLED. We ship no SessionStart in this slice. The collision is structurally avoided.
- **S3 Auto-routed agents false-fire across repos** — PARTIAL → HANDLED by reshape. Mitigation built into the slice: `pytest-triage` and `root-cause-hunter` pre-flight check for cairn substrate (`role_guard.py` + envelope template), refuse cleanly with stderr hint if absent. The four substrate-aware agents (slice-status, worktree-map, adr-context, handoff-closer) inherently no-op in non-cairn repos.
- **S4 superpowers drift / unavailability** — PARTIAL. Bundled ADR pins a superpowers version floor (commit SHA or plugin version) and documents reversal cost. Agents fail-closed (refuse to run, stderr hint to install superpowers) — never fail-open into a methodology mock.
- **S5 INV-011 maintainer dogfood breakage** — PARTIAL → HANDLED. Mitigation: PREREQS.md must include an explicit `.slice-system` exclusion stanza for Pyright (`pyrightconfig.json` exclude) and ast-grep (`.ast-grep.yml` ignore). Validator checks both. CLAUDE.md §Safety-critical rules already names the hazard.
- **S6 PREREQS.md shifts friction** — PARTIAL. Mitigation: install-time validator (`scripts/validate-prereqs.py` invoked via `/plugin install` hook or a documented `/cairn-doctor` command) — fails loud with the exact missing piece. Converts prose-only into structural per L-005. Residual: operator can still skip running the validator.
- **S7 Per-worktree LSP daemons stack memory** — EXPOSED. PREREQS.md acknowledges "~150MB per session" but does not cap concurrent daemons. With 4–6 active worktrees (parallelism-v1 + Shape B tmux panes per CLAUDE.md stack), 600MB–1GB Pyright resident + ast-grep is real. Mitigation deferred to a follow-up slice; ADR consequences must declare this as known tax. This is the honest exposure.
- **S8 Reversibility cost of ADR-locking superpowers** — PARTIAL. Bundled ADR explicitly includes "Reversal cost" section per the mitigation; supersession path is sketched. Stickiness of `~/.claude/plugins/superpowers/` is acknowledged, not solved.
- **S9 SessionStart ballooning** — HANDLED. We ship no SessionStart. Future SessionStart would be a separate ADR with its own budget.
- **S10 Operators never learn the surface** — PARTIAL. PREREQS.md names all six agents; agents are discoverable by name in `agents/`. Auto-routing (if kept) must leave a trace ("invoked X because Y") — built into agent prompts as a one-line announcement. Direct invocation by name remains possible.

## Downstream impact

- **On `parallelism-v1`:** Compatible. The `worktree-map` agent is *built for* parallelism-v1 — tabulates worktree × branch × slice × state. This approach actively serves parallelism rather than fighting it. Caveat: S7 memory tax compounds with concurrent worktrees.
- **On `m5-plugin-deployment-pattern`:** Agents go into `dist/agents/` per D3 curation (m5-distribution). `dist/.claude-plugin/plugin.json` version bumps; release workflow unchanged. PREREQS.md ships under `dist/docs/` or remains repo-only and is linked from CONSUMER.md — TBD by slice, low risk either way.
- **On consumer time-to-first-dispatch (J1):** Increases at install by ~10–15 min (one-time Pyright/ast-grep/superpowers install + validator run). Decreases per-session from then on — `pytest-triage` and `root-cause-hunter` collapse J5's "10–30 min manual debugging" into a single dispatch.
- **On returning-operator experience (J2):** Improves via `slice-status` (state-of-the-world on demand) and `handoff-closer` (clean session close). Does not solve J2 step 1 (no SessionStart) — operator still types something to orient. That is deliberate: discoverability via deliberate invocation, not eager injection.
- **On maintainer dogfood loop (INV-011):** Survives if and only if `.slice-system` exclusions ship in PREREQS.md. This is the *single load-bearing mitigation* for the approach.
- **On future slices / #33 items 1, 3–7:** Closes nothing structurally. Opens room for #33-1 (`using-cairn` SessionStart) to land later *as a pointer-not-payload* SessionStart that defers to PREREQS.md / agents already in place. #33-2 (slash-command discoverability) can land cleanly because we did not commit to auto-routing as the only discovery channel.

## Evidence

- **Branch facts:** commit 8b680cb (`feat(agents): add 6 workflow subagents + consumer prereqs`), +334 LOC, 7 files (framing §Branch facts; verified via `git show 8b680cb --stat`).
- **PREREQS.md content:** verified via `git show 8b680cb -- docs/PREREQS.md` — 73 lines, sections {Required (6 items), How to install, Code-intelligence stack rationale, Why not Serena}.
- **Substrate non-negotiables preserved:** framing §"Substrate non-negotiables" (role isolation, append-only ADRs, INV-001..011, Conventional Commits, two-field id+name, reversibility-guard) — none weakened by this approach.
- **INV-004 fresh-session 40k ceiling:** ARCHITECTURE.md:51 via Phase 0 invariants.
- **INV-011 dogfood loop + `.slice-system` symlink hazard:** ARCHITECTURE.md:91 + CLAUDE.md §Safety-critical rules.
- **L-005 prompt-layer enforcement empirically inadequate:** docs/lessons.md referenced in Phase 0 lessons block → motivates the validator mitigation.
- **L-020 non-skippable steps require code, not description:** Phase 0 lessons → motivates `/cairn-doctor` validator.
- **Phase 0.5 J5 (pytest fails):** ~"10–30 min manual debugging" today; `pytest-triage` collapses this.
- **Phase 0.5 J2 step 4 (mid-slice resumption):** `slice-status` agent + `worktree-map` together satisfy the "what state am I in" need without a SessionStart hook.
- **Soft-constraint #3 (new deps require ADR):** Phase 0 soft constraints → motivates the bundled new-dep ADR.

## Why this approach beats the alternatives (steelman)

- **It is the only approach that has already been built.** Six agents + PREREQS.md exist on commit 8b680cb. B (`using-cairn` SessionStart bootstrap) is vapor — framing claim 1 is "author's prior; not verified" per framing §"Load-bearing claims to attack". C (hybrid/split) ships less of A and none of B. Optionality is not free; carrying an unmerged branch costs.
- **It treats setup-surface as a one-time tax, not a recurring one.** B and C add per-session context cost (SessionStart injection competes with the 40k budget forever per S9). A pays once per machine at install and never again. The math favors A for any consumer who runs more than ~3 sessions.
- **It honors L-005.** Real code intelligence (Pyright types, ast-grep AST) is structural enforcement; text-grep heuristics inside agents are the prompt-layer enforcement L-005 says drifts. B and C without A leave diagnostic agents as prose-only and inherit the empirical failure.
- **It buys methodology durability.** Citing `superpowers:systematic-debugging` is a *gate*, not decoration — when context pressure compresses an agent's plan, the cited methodology is the recoverable spine. Removing the cite (C's soft option) means the spine is whatever survives compaction.
- **It keeps cairn's identity honest.** Cairn is a methodology repo for serious agentic work, not an onboarding-optimized starter kit. Operators who need real find-references and structural rewrite already want Pyright + ast-grep; cairn formalizes the floor rather than apologizing for it.

## What this approach asks the operator to accept

- **+4 install steps per fresh machine.** Pyright, ast-grep, `ENABLE_LSP_TOOL=1`, user-scope superpowers. Mitigated by validator, not eliminated.
- **A new external dependency edge (`superpowers`) locked in an ADR.** Reversal requires supersession plus consumer-machine cleanup (S8). The ADR documents the reversal cost; it does not make it free.
- **A latent S7 tax: 4–6 concurrent worktrees × ~150MB Pyright + ast-grep indexer can pin 1GB+.** Not solved in this slice. Operator with Shape B + Glove80 multi-pane workflow is exposed; follow-up slice required if it bites.
- **Discoverability remains operator-initiated, not eager.** Operators who never read PREREQS.md or never type `/cairn-doctor` will never know the surface exists. This is the deliberate counter-bet to #33-1.
- **The `.slice-system` exclusion stanza is load-bearing.** If a maintainer skips it, S5 fires inside cairn-the-repo. The PREREQS.md mitigation is mechanical, but it is one config-line away from breaking.

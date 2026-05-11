# Phase 1 — Pre-Mortem (delivery-mechanism-friction)

## S1 — Context-budget breach from setup-surface-up
**Class:** technical
**Threatens most:** A
**How it manifests:** PREREQS.md + six agent definitions + superpowers-cite preamble per agent get auto-injected (or are read eagerly by operators following docs) on session-open. Aggregate with cairn's existing CLAUDE.md + CONSUMER.md + phase-skill-mapping fragments crosses the 40k fresh-session budget, leaving Phase 1 with degraded headroom for plan-doc + intent.
**Why it's plausible:** INV-004 caps fresh-session orientation at 40k; Phase 0 Tension Watch flags "context budget vs. setup-surface-up" as a direct conflict; J1 step 3–5 already costs ~20 min of prose today.
**Early-warning evidence we'd look for:** Token-count the proposed PREREQS.md + 6 agents + superpowers-cite lines against current fresh-session baseline (measure, do not estimate).
**Mitigations to design into the chosen approach:** Whatever lands must keep fresh-session ingest ≤40k with measurement, not assertion; eager-load surfaces must be on a budget.

## S2 — SessionStart auto-injection collides with superpowers' SessionStart
**Class:** integration
**Threatens most:** B (and C)
**How it manifests:** `superpowers` plugin already ships a SessionStart skill that auto-injects its own context. A new cairn `using-cairn` SessionStart fires alongside it; both load, double-injecting overlapping methodology framing (brainstorming, systematic-debugging) — and stacking context cost on top of S1.
**Why it's plausible:** Branch's agents already cite superpowers as a methodology gate; framing claim 1 ("using-cairn is highest-leverage") is unverified per Phase 0 explicit-gap #1; Phase 0.5 J1 step 3 verified no SessionStart wired today, so the collision is latent until B/C lands.
**Early-warning evidence we'd look for:** Install superpowers + cairn in a clean Claude Code session; capture SessionStart event log; measure combined injected token count and check for semantic overlap.
**Mitigations to design into the chosen approach:** Any SessionStart cairn ships must detect superpowers presence and either yield, dedupe, or compose — not naively prepend.

## S3 — Auto-routed agents false-fire across unrelated repos when cairn is at user scope
**Class:** technical / integration
**Threatens most:** A (and C, if diagnostic two are kept)
**How it manifests:** `pytest-triage` and `root-cause-hunter` route on phrase triggers ("test failed", "root cause"). With cairn installed at user scope (as PREREQS proposes for superpowers), routing fires in non-cairn repos that don't have `.slice-system/`, role_guard envelope, or even pytest — the agent dispatches, pre-flight fails or worse, the agent writes assuming substrate that isn't there.
**Why it's plausible:** PREREQS.md explicitly recommends user-scope superpowers; framing load-bearing claim 3 ("auto-routed > slash") is unargued per framing §4; Phase 0.5 J1 step 7 already flags agent-definition pre-flight as silent-abort risk.
**Early-warning evidence we'd look for:** Dispatch the two diagnostic agents in a non-cairn Python repo and a non-Python repo; check exit behavior and whether they attempt writes.
**Mitigations to design into the chosen approach:** Any cross-repo agent must pre-flight cairn-substrate presence and refuse cleanly (no-op + stderr hint), not silently degrade.

## S4 — `superpowers` plugin drift / unavailability cascades into cairn diagnostic agents
**Class:** integration / reversibility
**Threatens most:** A
**How it manifests:** `pytest-triage` and `root-cause-hunter` cite `superpowers:systematic-debugging` and `:defense-in-depth` as a methodology gate. Upstream renames a skill, bumps a major, or pulls the plugin; cairn diagnostic agents either fail-closed (operator stuck) or fail-open (skip methodology, becoming a mock).
**Why it's plausible:** L-005 explicitly says prompt-only enforcement drifts; framing sub-question 3 names the hard/soft/none coupling as undecided; Phase 0 soft-constraint #3 says new deps require ADR.
**Early-warning evidence we'd look for:** Pin-check: does `feature/workflow-subagents` declare a superpowers version floor? If no, drift is unbounded.
**Mitigations to design into the chosen approach:** Cite-strength must be a decided property (hard/soft/none), not implicit; if hard, supply a pinned version in PREREQS or absorb the methodology in-tree.

## S5 — INV-011 maintainer dogfood breakage from setup-surface-up
**Class:** technical / reversibility
**Threatens most:** A
**How it manifests:** Pyright + ast-grep + `ENABLE_LSP_TOOL=1` configured in user-scope settings start firing inside cairn-the-repo via `.slice-system → .`. LSP daemons follow the symlink loop, ast-grep walks recursively, Pyright tries to index venv/.slice-system; one of: daemon thrash, memory blow-up, or hook side-effects that contaminate maintainer commits.
**Why it's plausible:** CLAUDE.md §Safety-critical rules explicitly flags "Symlink recursion hazard — exclude `.slice-system`"; INV-011 requires the dogfood loop stay intact; Phase 0 hard-constraint #3.
**Early-warning evidence we'd look for:** Run the proposed Pyright + ast-grep + LSP config against cairn-the-repo with `.slice-system` present; measure memory, daemon count, indexer error log.
**Mitigations to design into the chosen approach:** Any new indexer/LSP dep must declare its `.slice-system` exclusion explicitly and be tested against the self-symlink before shipping.

## S6 — PREREQS.md shifts friction rather than reducing it (L-005 / adoption)
**Class:** adoption / human
**Threatens most:** A
**How it manifests:** PREREQS.md is more prose-to-read at install time. Operators under context pressure skip "install Pyright, install ast-grep, set ENABLE_LSP_TOOL=1, install superpowers at user scope" — diagnostic agents then silently degrade or pre-flight-abort, and operators conclude "cairn is flaky" rather than "I skipped step 4".
**Why it's plausible:** L-005 ("prompt-layer enforcement empirically inadequate"); L-020 ("non-skippable steps require code, not description"); J1 highest-friction transition #1 already costs ~20 min of prose-reading per fresh install — PREREQS.md adds, not subtracts.
**Early-warning evidence we'd look for:** Recruit one fresh installer; observe whether they complete PREREQS.md unaided; measure time-to-first-dispatch.
**Mitigations to design into the chosen approach:** Any setup surface beyond `jq` + `ruff` must be either auto-detected with skip-if-unavailable + visible degradation, or structurally enforced (post-install validator that fails loud) — not prose-only.

## S7 — Per-worktree LSP daemons stack memory
**Class:** scale
**Threatens most:** A (and C with diagnostics on)
**How it manifests:** `parallelism-v1` makes multiple concurrent worktrees normal. With `ENABLE_LSP_TOOL=1` and Pyright in user scope, each worktree spawns its own daemon; 4–6 active worktrees = 4–6 Pyright processes + ast-grep indexers, each holding several hundred MB.
**Why it's plausible:** ADR `parallelism-v1` (accepted; provisional) explicitly enables concurrent slices; Phase 0.5 §State boundaries flags cross-worktree as the new mechanism territory; user runs Glove80 + tmux multi-pane Shape B per CLAUDE.md, implying parallel sessions are routine.
**Early-warning evidence we'd look for:** Open 4 worktrees with proposed config; `ps` + RSS sum; observe whether daemons share or stack.
**Mitigations to design into the chosen approach:** New indexer/LSP deps must either be session-local (not per-worktree) or have a documented ceiling on concurrent daemons.

## S8 — Reversibility cost of ADR-locking superpowers as a dep
**Class:** reversibility
**Threatens most:** A
**How it manifests:** Per soft-constraint #3, adding Pyright/ast-grep/superpowers as consumer requirements should be ADR-justified. Once an ADR commits to "superpowers is a cairn dep at user scope," retiring it later requires supersession — and consumer machines that did the install have sticky state (`~/.claude/plugins/superpowers/...`) that does not auto-uninstall.
**Why it's plausible:** Substrate non-negotiable: "ADRs append-only with supersession protocol"; cairn already absorbed a supersession (cairn-substrate-and-fastmcp → -superseded) when kuzudb/mistune/fastmcp were dropped — non-zero cost.
**Early-warning evidence we'd look for:** Sketch the supersession path: if we lock superpowers in an ADR now, what would unwind look like in 3 months?
**Mitigations to design into the chosen approach:** Decisions that bind new consumer-machine deps should ship with explicit reversal cost in the ADR's consequences section.

## S9 — SessionStart skill ballooning past INV-004 as features land
**Class:** scale / reversibility
**Threatens most:** B (and C)
**How it manifests:** A `using-cairn` SessionStart starts at 2–3 min auto-briefing (Phase 0.5 ranking #1) but accretes: each new slash command, each new ADR audience nuance, each new operator-envelope rule wants a line. Six months in, SessionStart injects 15k tokens and competes with phase-skill-mapping + CLAUDE.md for the 40k budget.
**Why it's plausible:** INV-004 is the hard ceiling; soft-constraint #1 already prefers progressive disclosure for exactly this reason; SessionStart skills run on every consumer session — hard to evolve without breaking sessions in flight (Phase 0.5 §State boundaries §session-open).
**Early-warning evidence we'd look for:** Set a token budget for `using-cairn` SessionStart from day one and a CI check that fails if exceeded.
**Mitigations to design into the chosen approach:** SessionStart must obey progressive disclosure — pointer, not payload (mirroring context-discipline-protocol).

## S10 — Operators never learn the surface because auto-routing hides it
**Class:** adoption / human
**Threatens most:** A (and C with diagnostics on)
**How it manifests:** Auto-routed agents fire silently on phrase triggers. Operator never sees `/pytest-triage` or learns that `root-cause-hunter` exists; methodology is invisible. When an agent misfires or is needed in a non-triggering context, operator can't invoke it directly because they don't know the name.
**Why it's plausible:** Framing claim 3 (auto-routed > slash) is implicit and unargued; J3 step 1 already flags `/decision` discovery as prose-only; auto-routing is the opposite direction from #33-2 (better slash-command surfacing).
**Early-warning evidence we'd look for:** After a session that auto-routed an agent, ask the operator to invoke the same agent by name — can they?
**Mitigations to design into the chosen approach:** Auto-routing, if kept, must leave a discoverable trace ("invoked X because Y; invoke directly via Z").

## Cross-cutting failure shapes

- **Prose-only enforcement drift (L-005)** appears in S2, S4, S6, S10: every direction that relies on operators reading docs or methodology cites holding under pressure inherits L-005's empirical failure. Phase 2 must-handle: structural enforcement or visible degradation, not prose.
- **Context-budget pressure (INV-004)** appears in S1, S2, S9: any surface that adds eager-loaded bytes — PREREQS, SessionStart, auto-routed agent preambles — competes for the same 40k. Phase 2 must-handle: measured token budgets per surface, progressive disclosure as default.
- **Cross-boundary pre-flight** appears in S3, S5, S7: agents/LSPs/indexers that follow consumer to user-scope or across worktrees inherit assumptions about the substrate's presence and shape. Phase 2 must-handle: explicit pre-flight check + clean refusal when substrate absent.

## Disqualifiers

None — no scenario above is severe enough to exclude A, B, or C wholesale before Phase 2. S5 (INV-011 dogfood breakage) is the closest to a disqualifier for A but is mitigable with a tested `.slice-system` exclusion; S2 (SessionStart collision) is mitigable for B with detection logic. Phase 2 enumeration should proceed with all three buckets in play, each carrying the cross-cutting must-handle list above.

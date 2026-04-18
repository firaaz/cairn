# Streamlining Cross-Cuts

**Date:** 2026-04-18
**Purpose:** Catch streamlining items from the brainstorm that got folded into multi-part work. Each is named explicitly + cross-referenced to the Part/slice that implements it. Items added here that weren't in the other docs are flagged **[NEW]**.

## Inventory: streamlining items by source

### From A+ expanded (brainstorm turn 3)

| # | Item | Lives in | Status |
|---|---|---|---|
| 1 | Auto-detect phase in `/catchup`, `/handoff`, `/start-slice` | Part 2 E1 | Named |
| 2 | Code-not-prose side effects in `/handoff` + bootstrap | Part 2 E2 | Named |
| 3 | Ship Layer 1 allowlist early (project `settings.json`) | Part -1 #5 + Part 2 E4 | Named |
| 4 | `state.json` + SHA-short-circuit catchup | Part 2 E3 | Named |
| **5** | **`/catchup` runs as subagent, not main session** | Part 1 A1 (context-distiller) — but not called out as a `/catchup` refactor | **Insufficiently named — see §1 below** |
| 6 | Session-start tip | Part -1 #1 + Part 2 E5 | Named |
| 7 | `/start-slice next` canonical advance verb | Part 2 E1 | Named |
| **8** | **In-phase parallelism nudge at Phase 3** | Part 2 E6 + Part 3 phase-3-implementer — but the "nudge" UX isn't spelled out | **Insufficiently named — see §2 below** |

### Additions from later brainstorm turns (quick wins + meta)

| # | Item | Lives in |
|---|---|---|
| 9 | Role cheatsheet at session-start | Part -1 #1 |
| 10 | Measurements-drift hook fix | Part -1 #2 |
| 11 | Read-before-Write preload | Part -1 #3 |
| 12 | `/handoff` post-check verifier | Part -1 #4 |
| 13 | Per-phase commit-message templates | Part -1 #6 |
| 14 | `/status` expansion to one-stop dashboard | Part -1 #7 |
| 15 | Coupling clusters at Phase 2 | Part 2 E6 |
| 16 | Test-impact-analyzer | Part 2 S1 |
| 17 | Parallel-test-orchestrator | Part 2 S2 |
| 18 | Background-precommit | Part 2 S3 |
| 19 | Commit-drafter | Part 2 S4 |
| 20 | Named phase-role agents (pre-F6 = subagents; post-F6 = worker system prompts) | Part 3 |
| 21 | Tier model applied to every skill (not just `/catchup`) | Part 0 P1 |
| 22 | Policy files, not skill prose, for repeated rules | Part 0 P6 |

### Named here for the first time **[NEW]**

| # | Item | Notes |
|---|---|---|
| **23** | **Skill-surface compression.** `commands/claude-code/*.md` = 1136 lines total. Many `.full.md` files have prose that could be tables, checklists, or deferred to an ADR link. | See §3 below. |
| **24** | **Tmux window auto-rename hook.** Dogfood §8.1 #15: tmux base-index surprised the plan; windows stayed numeric. A session-start hook that renames the current window to `<slice-name>:<phase>` makes parallel coordination legible without a coordinator. | See §4 below. |
| **25** | **`context-budget-monitor` hook.** Lightweight session-turn hook that reads recent token usage, prints a stderr warning when approaching the limit, suggests `/handoff`. Prevents surprise-compaction. | See §5 below. |
| **26** | **Skill-duplication audit.** `.md` vs `.full.md` split is good discipline, but some `.full.md` content duplicates the shorter `.md`. A one-time audit + cleanup reduces total surface and removes stale duplicates. | See §6 below. |
| **27** | **`/features` as an alias for `feature-graph-explainer`.** Explicit slash command that humans use to ask "what's ready?" without going through `/status`. Low-cost ergonomic win. | See §7 below. |
| **28** | **Transcript-fed permission-policy learning.** Offline job that reads recent transcripts (like `less-permission-prompts` does today) and proposes `permission-policy.yaml` rule additions as an ADR amendment. Makes Layer 1 self-tuning. | See §8 below. |

---

## §1 — `/catchup` explicitly refactored as subagent-first

**Problem:** Part 1 A1 introduces `context-distiller` as a generic Tier 2 agent. Part 2 doesn't carry a matching skill-side change that routes `/catchup` through it by default.

**Change:**
- `/catchup` base behavior becomes: Tier 1 = five-item read (same as today, cheap), Tier 2 = always dispatched to `context-distiller`, never to main-session reads.
- The ~30k tokens observed in the 2026-04-16 dogfood become ~300 tokens in main (the subagent's bounded return).
- Combined with `state.json` SHA-short-circuit (Part 2 E3), typical inter-phase catchup is: one `state.json` read + ≤200 words if SHA matches, or subagent round-trip if mismatch. Main session context stays lean.

**Add to:** Part 2 as **E7 — Refactor `/catchup` to subagent-first**. Depends on Part 1 A1 + Part 2 E3.

---

## §2 — In-phase parallelism nudge

**Problem:** Within-slice parallel dispatch is ADR-allowed (memory: `parallelism_scope`) but skill prose doesn't nudge the operator toward it. Phase 3 implementers default to serial editing even when the envelope has independent modules.

**Change:**
- Phase 3 skill (pre-agent) or `phase-3-implementer` system prompt (post-agent) includes a prompt-level clause: *"If `coupling-clusters.yaml` has ≥2 clusters, dispatch one subagent per cluster in parallel. Default to parallel; justify serial."*
- UX prompt to human when `/start-slice phase 3` is invoked: *"3 independent clusters detected (c1: auth, c2: helpers, c3: migration). Dispatch in parallel? [Y/n]"*
- Timeout discipline (Part 0 P5) applies per-cluster.

**Add to:** Part 2 as **E8 — Phase 3 parallel-dispatch nudge**. Depends on Part 2 E6 (coupling clusters) + Part 3 phase-3-implementer.

---

## §3 — Skill-surface compression

**Problem:** `commands/claude-code/*.md` has 1136 lines across 15 files. Some is essential context discipline; some is prose that could be tables. A 279-line `start-slice.full.md` forces re-scan to locate anything.

**Change:**
- One-pass audit (candidates for `skill-lint` agent from Part 1 A7): each skill's `.full.md` reviewed for prose that could be tabulated or pushed into an ADR.
- Target: ≤150 lines per `.full.md`; ≤25 lines per `.md`.
- Escalation path: if content genuinely needs more, split into topic-docs linked from the `.full.md`.

**Add to:** Part 2 as **E9 — Skill-surface compression pass**. One slice. Informed by Part 1 A7 `skill-lint` output.

---

## §4 — Tmux window auto-rename

**Problem:** Dogfood §8.1 #15 — tmux base-index surprised the plan and renumbers on kill (cairn:5 → cairn:4 after cairn:4 is killed). Coordinator confusion.

**Change:**
- Session-start hook runs `tmux rename-window "<slice-name>:<phase>"`.
- Feature 6's daemon gains optional tmux discipline: windows named by slice + phase for legibility.

**Cost:** ~30 min of shell hook work.

**Add to:** Part -1 as **#8 — tmux window auto-rename**. Bundle with other afternoon wins.

---

## §5 — `context-budget-monitor` hook

**Problem:** Surprise compaction. A session that burns past the budget gets auto-compressed mid-work. No warning.

**Change:**
- Lightweight hook (post-every-turn) reads `Anthropic-Ratelimit-*` headers or conversation-token-count via Claude Code telemetry (if exposed).
- If approaching limit (e.g., >80% of context budget), print stderr warning + suggestion: *"Consider `/handoff` soon — context at 82%."*
- Never blocks; purely advisory.

**Add to:** Part -1 as **#9 — context-budget-monitor hook**. Or Part 2 if it needs more telemetry than available today.

**Open question:** Does Claude Code expose turn-level token counts to hooks today? If no, this depends on future CC capability — move to Part 5 or external.

---

## §6 — Skill-duplication audit

**Problem:** `.md` vs `.full.md` split is good discipline. But content drift happens — some `.md` files describe behavior that doesn't match the `.full.md`. Also some content is duplicated verbatim across both for no reason.

**Change:**
- One-shot audit: compare each `<skill>.md` against `<skill>.full.md` for: (a) contradictions, (b) verbatim duplication, (c) `.md` carrying content that should only be in `.full.md`.
- Rewrite to canonical form: `.md` ≤30 lines of routing + role surface; `.full.md` the full protocol.

**Add to:** Part 2 as **E10 — Skill-duplication audit**. Bundle with E9.

---

## §7 — `/features` alias

**Problem:** Human asks "what's ready to start?" by either (a) `/status` (terse), (b) reading all `.claude/features/*.yaml` manually, (c) asking Claude to summarize. Three paths; none is canonical.

**Change:**
- `/features` slash command dispatches `feature-graph-explainer` agent (Part 1 A3) with no arguments. Returns the structured four-section output.
- `/features <name>` returns detail on one feature.

**Cost:** ~1 hr once Part 1 A3 exists.

**Add to:** Part 2 as **E11 — `/features` alias command**. Depends on Part 1 A3.

---

## §8 — Transcript-fed permission-policy learning

**Problem:** Layer 1 `permission-policy.yaml` is initially authored. It will drift out of date as new command patterns emerge. Manual updates are reactive — each missed pattern costs `1 Enter` clicks until someone notices.

**Change:**
- Monthly (or on-demand) job reads recent transcripts — the same approach `/less-permission-prompts` uses.
- For each observed permission prompt that hit ≥3 times in the window and is read-only + safe by heuristics, propose a new rule for `permission-policy.yaml`.
- Proposals go to a file for human review; accepted entries become ADR amendments.

**Add to:** Part 4 as a maintenance agent (`policy-learning-auditor`) or Part 5 as meta-evolution infrastructure.

**Rename to:** `permission-policy-learner`. Bundle with Part 4 `adr-drift-auditor` slice.

---

## §9 — Items I'm NOT adding (explicit)

For completeness — things that came up in the brainstorm but are deliberately excluded:

- **Tour/onboarding mode.** Nice-to-have; no urgent cost. Defer indefinitely.
- **GitHub / CI integration.** Seams only; don't build until concrete use case exists.
- **Epic tier formalization.** Keep implicit; avoid new ceremony.
- **Methodology coverage tracking.** Part 5 S1 telemetry subsumes this.
- **Cross-agent-family maintenance discipline (Windsurf/Gemini/Codex)** — reserve the seam, don't activate.
- **`/revise-spec` protocol for spec-v1.md amendments.** Raised as open question #5 in program doc; not in this program's scope.

---

## Updated totals (across all nine docs)

- Part -1: 9 items (7 named originally + #8 tmux rename + #9 context-budget-monitor conditional)
- Part 0: 1 ADR (6 principles, no slices)
- Part 1: 7 agents across ~4 slices (unchanged)
- Part 2: 15 ergonomic/speed items across ~9 slices (was 10 items / 6 slices; adding E7/E8/E9/E10/E11 = 15 items / 9 slices)
- Part 3: 5 agents across ~3 slices (unchanged)
- Part 4: 6 maintenance agents + policy-learner + scheduled-routines infrastructure across ~5 slices (added policy-learner)
- Part 5: 5 meta-evolution items across ~5 slices (unchanged)
- **Part 6 (new)**: 5 auto-advance items across ~5 slices — `/catchup`→auto-start-slice, phase-commit→auto-handoff, next-session-hint + auto-resume, precondition auto-checks, policy-runtime consolidation

Revised total: ~32 slices + 1 ADR. Order of 3-6 months of work.

---

## Where each streamlining item pays off

| Streamlining | Measured in |
|---|---|
| Context saved per session | Items 5, 9, 14, 21, 25 |
| Permission prompts eliminated | Items 3, 11, 28 |
| Cognitive routing load | Items 1, 6, 7, 9, 27 + all of Part 6 |
| Ceremonial side-effects guaranteed | Items 2, 12, 20 + Part 6 AA2 |
| Parallelism enabled where previously serial | Items 8, 15, 17, 20 |
| Feedback-loop speed | Items 16, 17, 18 |
| Doc / skill surface reduced | Items 23, 26 |
| Discoverability | Items 14, 27 |
| Future evidence base | Part 5 S1 telemetry + Part 6 audit log |
| Drift mechanically detectable | Part 0 P6 + Part 5 S3 validator |
| **Keystroke-level wait time eliminated** | **Part 6 entire** — auto-advance where state is unambiguous, saving 5–20 command-typings per slice |

# Cairn Efficiency Program — Spec

**Date:** 2026-04-18
**Status:** Spec-level brainstorm output. NOT YET ANALYZED/PLANNED. Input to future `/decision` + `/start-slice` runs.
**Authored during:** `feature/identifier-scheme` slice; migrated to `docs/plans/2026-04-18-efficiency-program/` at slice close (commit trail: `feature/identifier-scheme`).
**Supersedes / refines:**
- Roadmap items (3) `state.json` + SHA catchup, (6) parallelism support, (10) dogfood log — superset
- L-005 follow-up slices (harden `/handoff`, harden bootstrap, subagent visibility) — absorbed
- Feature 6 (fleet coordinator) — composes with; does not replace

---

## 1. Problem

Cairn feels slow and cumbersome in daily use, and very serial even when the work doesn't need to be.

**Evidence base:**
- `.claude/plans/2026-04-16-dogfood-observations.md` §8.1 — 15 pain points, of which 3 are HIGH severity.
- L-005: *"Parallelism substrate works; skill-level coordination is the actual tax."*
- User-reported (2026-04-18 brainstorm): pain is concentrated in
  - **(a)** per-slice ceremony in single-session serial work — four phase boundaries = four context rebuilds
  - **(c)** permission-prompt density — dozens of `1 Enter` clicks per slice on routine reads
  - **(e)** cognitive routing load — different `/catchup` / `/handoff` variants per phase; Mode A/B/C/D branching; 4 distinct sub-commands in `/start-slice`

**Root cause framing:** the substrate (branches, worktrees, tmux, hooks, merge reconciliation) works. Skill-layer execution is prose-specified, which produces divergence (L-005). Roles are described, not enforced. Context is re-read between phases rather than distilled. Subagent dispatch exists in a few places but is not the default pattern.

## 2. Approaches considered

**Approach A+ (chosen):** Skill self-awareness + shipped-early permission policy + distillation subagents + named role agents + meta-evolution layer. No phase-count change. Evidence-first. Composes with F6.

**Approach B (rejected for now):** Phase compression with slice sizes (tiny/regular/full). Risks the phase 2→3 isolation discipline that spec-v1 §14 incident #4 calls load-bearing. Reopen after F6 audit-log data arrives.

**Approach C (rejected):** Wait for F6. Leaves pain unaddressed for weeks/months. Misses the chance to gather F6-relevant data pre-daemon.

## 3. Scope — Part structure

| Part | Scope | Gating | When |
|---|---|---|---|
| **Part -1** | 7 afternoon wins: role cheatsheet, measurements-drift fix, Read-before-Write preload, `/handoff` post-check verifier, Tier-1 allowlist in `settings.json`, per-phase commit templates, `/status` expansion | None | Week 1 |
| **Part 0** | One ADR codifying: Tier 1/2/3 model universal, named phase roles, bounded subagent returns, coupling clusters at Phase 2, stall-visibility contracts, policy-file-not-prose | Blocks Parts 1–5 | Week 2 |
| **Part 1** | Distillation + verification agents: context-distiller, envelope-scout, feature-graph-explainer, invariant-preflight, sweep-preflight, doc-drift-detector, skill-lint | Part 0 ADR | Weeks 3–4 |
| **Part 2** | Ergonomics + speed: auto-phase-detect (3 commands), code-side-effects, state.json + SHA catchup, `/start-slice next`, Layer 1 allowlist refinement, session-start tip upgrade, coupling-cluster Phase-2 step, test-impact-analyzer, parallel-test-orchestrator, background-precommit, commit-drafter | Part 0 ADR | Weeks 4–6, parallel with Part 1 |
| **Part 3** | Phase-role agents (phase-1-writer, phase-2-skeptic, phase-3-implementer, phase-4-integrator, adr-author) | Part 0 ADR + F6 worker infra | Post-F6 |
| **Part 4** | Maintenance agents (adr-drift, adr-impact, lesson-extractor, merge-conflict-specialist, cross-repo-awareness, dogfood-interpreter) + scheduled routines | F6 daemon | Post-F6 |
| **Part 5** | Meta-evolution: continuous telemetry, invariant registry, methodology validator, doc-tier declarations, decision-note tier, multi-repo slice protocol | S2 (registry) + S4 (doc tiers) pre-F6; rest post-F6 | Mixed |
| **Part 6** | Auto-advance layer: when the next action is obvious from state, take it. `/catchup` → auto-start-slice; phase-commit → auto-handoff; next-session hint + auto-resume; precondition auto-checks; policy-file runtime | Part 0 ADR + Part 2 E2 + Part 2 E3 | Weeks 5–7, parallel with Part 2 tail |

Total: ~32 slices + 1 ADR. Spans months, not a sprint.

## 4. Sequencing rationale

- **Part -1 first** to give fast relief while the structural program is planned. Every item ports into Parts 0–6, zero wasted work.
- **Part 0 next** to capture the principles before agents get authored. Prevents re-deciding the agent contract per slice.
- **Parts 1, 2, and 6 parallel** — Part 1 builds distillation/verification agents (no critical-path dependencies); Part 2 refactors the skill surface; Part 6 (auto-advance) depends on Part 2 E2/E3 but otherwise independent. Run the tails in parallel once the shared dependencies land.
- **Part 3 after F6** because phase-role agents are most valuable as F6 worker system-prompts. Shipping them pre-F6 as subagents (Option B) is possible but diluted; post-F6 deployment (Option A, per `docs/plans/2026-04-17-coordinator-worker-communication-design.md` §3.6) is the clean target.
- **Part 4 after F6** because maintenance agents are most useful as scheduled routines; F6's daemon is the natural trigger.
- **Part 5 mixed** because the registry (S2) and doc-tiering (S4) are static-file changes that can ship anytime; the telemetry (S1) needs F6's event log; the validator (S3) benefits from but doesn't require F6; multi-repo protocol (S5) blocks only on the first breaking change.
- **Part 6 mostly pre-F6.** Its auto-advance policy is the pre-daemon analog of F6's Layer 2 `transitions.yaml`. When F6 ships, the policy file ports into daemon-consumed form with schema compatibility — no wasted work.

## 5. What this explicitly does NOT change

- Four-phase pipeline count. Phase 2→3 isolation. ADR append-only discipline. Worktree mechanics. Branch-local state-of-truth. `/decision` protocol structure.
- Spec-v1's core commitments remain untouched. This program is skill-surface + tooling + agent-role + meta-evolution. Spec revisions are a separate future `/revise-spec` protocol (Part 5 S5 raises this as an open question).

## 6. Risks

- **Scope creep within each part.** Mitigation: per-part docs (files `01` through `07`) fix the boundary. Each part is its own design doc + own set of slices.
- **Premature optimization.** Several agents (parallel-test-orchestrator, maintenance cluster) have effort > value unless the base pain is already measured. Mitigation: Part -1's `/status` + Part 5's telemetry land evidence before these agents are built.
- **Context-bloat from agent proliferation.** Adding 15+ agents to cairn could itself become a cognitive-load issue. Mitigation: Part 5's skill-catalog (auto-generated) keeps discoverability O(1).
- **F6 timing uncertainty.** Parts 3 and 4 gate on F6. If F6 slips, do we ship the post-F6 pieces pre-F6 as degraded versions, or wait? Open question for later planning.

## 7. Success criteria (program-level)

This program is successful when:

1. Per-slice human-touch count drops ≥50% vs 2026-04-16 dogfood baseline (~40 prompts/slice → <20).
2. Inter-phase orientation cost drops ≥75% (30k `/catchup` tokens → <8k).
3. `/handoff` side-effect divergence rate → 0 (L-005 regression impossible by construction).
4. Cognitive routing load measurable drop: user does not type phase numbers, mode letters, or `--advance` flags for canonical flows. One command per phase boundary.
5. Named phase roles are enforceable, not prose-described.
6. Every future structural decision about cairn (phase compression, policy tuning) has telemetry as its evidence base.

## 8. Open questions (for analysis phase)

1. Should Part 5 S5 (multi-repo slice protocol) land before or after the first breaking cairn change? Timing.
2. Is the phase-role agent roster (Part 3) the right abstraction, or should roles be more granular (e.g., `phase-3-refactorer` vs `phase-3-greenfield-implementer`)?
3. Does the coupling-cluster step at Phase 2 (Part 2) need an ADR of its own or is it subsumed by Part 0?
4. Part -1's Tier-1 allowlist goes in `.claude/settings.json` (team-shared). Does this conflict with consumer projects' own permission policies? If yes, is there a "cairn-shipped defaults" file consumers pull in?
5. For `/revise-spec` — does cairn's own spec revision flow need to be `/decision`-class or something lighter?

## 9. Per-part docs

- `01-part-minus-1-afternoon-wins.md`
- `02-part-0-adr-principles.md`
- `03-part-1-distillation-verification.md`
- `04-part-2-ergonomics-speed.md`
- `05-part-3-phase-role-agents.md`
- `06-part-4-maintenance.md`
- `07-part-5-meta-evolution.md`
- `08-streamlining-crosscuts.md` — addendum cross-cutting items named explicitly + new items beyond Parts -1..5
- `09-part-6-auto-advance.md` — auto-advance layer for obvious state transitions

## 10. Migration note

When the `identifier-scheme` slice closes, migrate this directory to `docs/plans/2026-04-18-cairn-efficiency/` (or split into `docs/plans/2026-04-18-cairn-efficiency-program.md` + one doc per part, as the author prefers at that time). The current location (`.claude/current-slice/efficiency-spec/`) is temporary — a consequence of scope-guard preventing writes outside the active slice envelope.

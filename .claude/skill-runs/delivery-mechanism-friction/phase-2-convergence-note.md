# Phase 2 — Convergence Note

## Comparison table

| Axis | A (capability-up) | B (friction-down) | C (hybrid/split) |
|---|---|---|---|
| **Branch disposition** | Merge ~all 6 agents + PREREQS | Defer entire branch (only consider `handoff-closer` cherry-pick) | Merge 4 nav agents + `handoff-closer`; defer 2 diagnostics + PREREQS |
| **`using-cairn` SessionStart** | No (deferred) | Yes (pointer-only, ≤2k tokens) | Yes (pointer-only, ≤2k tokens) |
| **New consumer deps** | +4 (Pyright, ast-grep, ENABLE_LSP_TOOL, user-scope superpowers) | 0 | 0 (this slice); deps slice deferred |
| **superpowers coupling** | Hard, ADR-locked, version-floor | No-cite default | No-hard-coupling-this-slice; deferred decision |
| **ADRs committed** | 2 (this decision + consumer-deps ADR) | 1 (this decision) | 1 (this decision) |
| **INV-004 (40k budget)** | OK (no SessionStart) | OK (budgeted ≤2k) | OK (budgeted ≤2k) |
| **INV-011 dogfood** | AT RISK → mitigated by `.slice-system` exclusion stanza | Untouched | Untouched (no LSP/indexer) |
| **L-005 structural-enforcement** | OK via real code intelligence (Pyright/ast-grep) | OK via SessionStart pointing at hooks | OK for shipped agents; deferred for diagnostics |
| **L-020 mechanize** | `/cairn-doctor` validator | SessionStart auto-fires; existing hooks | Both: SessionStart + agent pre-flight |
| **Phase 0.5 J1 friction (~20 min prose)** | Unchanged (PREREQS adds more prose) | Collapses to ~3 min | Collapses to ~3 min |
| **Phase 0.5 J5 friction (pytest debug 10–30 min)** | Collapses via `pytest-triage` | Unchanged | Unchanged (deferred slice) |
| **S7 LSP memory (4–6 worktrees)** | EXPOSED | HANDLED (no LSP) | HANDLED (no LSP this slice) |
| **S9 SessionStart drift** | N/A (no SessionStart) | PARTIAL (CI budget + vigilance) | PARTIAL (CI budget + vigilance) |
| **Reversibility cost** | High (sticky consumer-machine state) | Near-zero | Low (deferred slice carries the contested deps decision) |
| **Phase 1 scenarios HANDLED** | 5/10 | 9/10 | 9/10 |
| **Phase 1 scenarios PARTIAL** | 4/10 | 1/10 | 1/10 |
| **Phase 1 scenarios EXPOSED** | 1/10 (S7) | 0/10 | 0/10 |

## Pre-mortem coverage scorecard (Phase 1)

| Scenario | A | B | C |
|---|---|---|---|
| S1 context-budget | HANDLED | HANDLED | HANDLED |
| S2 SessionStart collision | HANDLED (no SS) | HANDLED (detect + delta) | HANDLED (detect + delta) |
| S3 auto-route false-fire | PARTIAL (pre-flight) | HANDLED (no auto-route) | HANDLED (no auto-route this slice) |
| S4 superpowers drift | PARTIAL (version pin) | HANDLED (no cite) | HANDLED (no cite this slice) |
| S5 INV-011 dogfood | PARTIAL (exclusion stanza) | HANDLED | HANDLED |
| S6 PREREQS shifts friction | PARTIAL (validator) | HANDLED (no PREREQS) | HANDLED (no PREREQS this slice) |
| S7 LSP memory | EXPOSED | HANDLED | HANDLED |
| S8 ADR-lock reversibility | PARTIAL (reversal section) | HANDLED | HANDLED |
| S9 SessionStart drift | HANDLED (no SS) | PARTIAL (budget + CI) | PARTIAL (budget + CI) |
| S10 surface invisibility | PARTIAL (trace line) | HANDLED (name list) | HANDLED (name list) |

## Leading candidate

**C (hybrid/split)** leads on the constraint envelope. Specifically:

- **Resolves the highest-leverage measured friction** (#33-1 SessionStart, Phase 0.5 J1 #1) — same as B.
- **Captures the substrate-reinforcing and zero-new-dep parts of the branch** (`handoff-closer` + 3 navigators) — work the branch author has already done that has no contested decisions attached.
- **Defers exactly the contested parts** (diagnostic agents + PREREQS + superpowers hard-cite + LSP/ast-grep deps) to a slice where evidence (S7 memory measurement, J5 setup-cost magnitude) can be collected first.
- **Splits along the dep-surface axis**, not the work axis — which means slice 1 (C) and slice 2 (deferred diagnostics) share no contested decisions and can proceed independently.

B is the closest runner-up. B is *cleaner* (lower scope, fewer ADR clauses) but **ships none of the work the branch author has already done**, including `handoff-closer` (which encodes existing CLAUDE.md commit hygiene as automation) and `adr-context` (which directly closes Phase 0.5 J3 "manual Phase 0 harvest" — a friction that B otherwise leaves untouched).

A is rejected as a leader, not as a wrong direction:
- A's value-prop (real code intelligence via Pyright/ast-grep) is real, but its **cost-side evidence is unverified** (S7 memory exposed; setup-cost magnitude not measured per Phase 0 gap #4).
- A locks cairn into a sticky external-plugin coupling (S8) on the basis of capability claims that have not yet been validated against onboarding traces.
- A leaves Phase 0.5 J1 friction (#1 highest-friction) unaddressed — it adds setup surface to the same prose-reading regime that already costs ~20 min.

A is not eliminated as an *eventual* outcome. The diagnostic agents + PREREQS surface remain candidates for a follow-on slice, with their hard questions (auto-routing strategy, superpowers cite-strength, `.slice-system` LSP exclusion, per-worktree daemon ceiling) handled in that slice's own /decision.

## Distinguishing decision point (C vs. picking A-then-B or B-then-A)

The single decision point: **whether `handoff-closer` + 3 navigational agents ship in the same slice as the SessionStart skill.**

C says yes — they share no contested decisions, share one ADR, share one F3 audit, ship together.

"B-then-A" would re-litigate the 4 zero-new-dep agents in slice 2 alongside contested decisions (PREREQS, superpowers cite, LSP).

"A-then-B" would ship the 4 agents under A's contested deps umbrella in slice 1.

C is the only sequence that gives the 4 zero-new-dep agents a clean home with no contested decisions attached.

## Verified vs. believed (load-bearing claims revisited)

Re-checking the 5 load-bearing claims from `framing.md`:

| Claim | Status after Phase 2 |
|---|---|
| 1. "`using-cairn` is highest-leverage" (#33) | **VERIFIED** by Phase 0.5 — J1 #1 is the ~20-min pain point and no SessionStart is wired. |
| 2. "Friction is paid per-machine, every session" | **VERIFIED** — Phase 0.5 confirms zero auto-orientation. |
| 3. "Auto-routed > slash-command discovery" (branch) | **NOT VERIFIED** — and Phase 1 S10 actively counter-argues. |
| 4. "Pyright/ast-grep/superpowers are worth the setup cost" (branch) | **NOT VERIFIED** — S7 memory tax exposed; setup-cost magnitude unmeasured. |
| 5. "Plugin-layout split is a merge-blocker" (analysis) | **NOT YET VERIFIED** — needs check of what `/plugin install cairn@cairn-marketplace` actually ships today. Not load-bearing for C's slice but should be confirmed before merging branch artifacts into `agents/`. |

Claims 1+2 carry approach C and B. Claims 3+4 fail to carry approach A. Claim 5 is a tactical merge-readiness check, not a strategic direction question.

## Open work before Phase 3

Phase 3 adversarial should:
- Attack C specifically — find the weakest joint in its dep-surface-axis split argument.
- Steel-man B — argue that shipping the 4 zero-new-dep agents *with* SessionStart is scope creep, not synergy.
- Audit verified-vs-believed: did Phase 2 over-claim verification for claim 1 ("highest-leverage" is verified as friction, but "highest-leverage relative to alternatives we did not enumerate" is a stronger claim that Phase 0.5 may not fully support).
- Test the assumption that `slice-status`/`worktree-map`/`adr-context`/`handoff-closer` truly have *zero* contested decisions — auto-routing behavior, false-fire risk in non-cairn repos, agent-discovery surface area.

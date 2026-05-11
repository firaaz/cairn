# Phase 3 — Corrections Applied

**Operator decision (2026-05-11):** C-with-corrections leads. The slice ADR will encode the six corrections from Phase 3 §"Corrections required" as normative clauses, not advisory ones.

## Corrections accepted into the slice scope

1. **A1 (load-bearing).** All 4 nav agents (`slice-status`, `worktree-map`, `adr-context`, `handoff-closer`) must add a cairn-substrate pre-flight guard before any output: refuse cleanly (no-op + brief stderr hint) when `.claude/active-envelope.yaml` AND `docs/ARCHITECTURE.md` are absent. Auto-routing trigger phrases in `description:` frontmatter are retained, but every agent body opens with the guard. The slice ADR explicitly *acknowledges* auto-routing as the discovery surface for these 4 agents (correcting Phase 2-C's "no auto-routing this slice" misframing).

2. **A3 (load-bearing).** Substrate pre-flight applies to all 4 nav agents, not just diagnostics. Mitigates S11 (auto-routing trigger phrases collide with operator's natural English in non-cairn worktrees).

3. **A2 (cheap).** `adr-context` strips the `ast-grep`/`sg` cite from its tool-preference block; falls back to built-in `Grep` only. Apply same audit to the other 3 nav agents — strip any name-drop of Pyright, ast-grep, LSP, or `superpowers:*` skills.

4. **S12 (cheap, before-merge).** Rename agents to `cairn-*` prefix: `cairn-slice-status`, `cairn-worktree-map`, `cairn-adr-context`, `cairn-handoff-closer`. Avoids future name collision with superpowers / other plugins / Claude Code itself. Cheap before adoption; expensive after.

5. **A4 / S9 honesty.** CI token-budget check on `using-cairn` SessionStart payload is included as load-bearing in-slice work (not a follow-up). If the slice cannot land the CI check, the slice ADR explicitly demotes S9 to EXPOSED and acknowledges L-005 drift exposure.

6. **A6 / S13 fix.** Slice ADR names the trigger condition that opens the deferred `cairn-diagnostics-with-detection` slice. Provisional trigger: open by 2026-09-01 OR after 3 operator-field-notes entries citing J5-style pytest-debug pain, whichever comes first. Without the trigger, deferral is rejected and the diagnostic 2 agents are honestly closed-as-wontfix on this branch.

## What this changes in the artifacts

- 4 nav agent files: add ~3-line substrate pre-flight prelude; strip any external-tool cites; rename to `cairn-*` prefix.
- 2 diagnostic agent files (`pytest-triage`, `root-cause-hunter`): defer to `cairn-diagnostics-with-detection`. Stay on `feature/workflow-subagents` branch as unmerged work pending the deferred slice; do not migrate to a "stale" branch.
- `docs/PREREQS.md`: deferred to the diagnostics slice. Does not ship in this slice.
- New: `dist/skills/using-cairn/SKILL.md` (or wherever Claude Code resolves the canonical path) with hard ≤2k-token budget.
- New: `.github/workflows/sessionstart-budget.yml` (or merged into `dist-gate.yml`) — token-count check on the SessionStart payload.
- New: `docs/adr/delivery-mechanism-friction.md` — the slice ADR.

## Pre-mortem coverage after corrections

| Scenario | C-as-written | C-with-corrections |
|---|---|---|
| S1 context-budget | HANDLED | HANDLED |
| S2 SessionStart collision | HANDLED | HANDLED |
| S3 auto-route false-fire | HANDLED (false claim) → PARTIAL | **HANDLED** via substrate pre-flight |
| S4 superpowers drift | HANDLED | HANDLED |
| S5 INV-011 dogfood | HANDLED | HANDLED |
| S6 PREREQS shifts friction | HANDLED | HANDLED |
| S7 LSP memory | HANDLED | HANDLED |
| S8 ADR-lock reversibility | HANDLED | HANDLED |
| S9 SessionStart drift | PARTIAL (CI unbuilt) → EXPOSED | **PARTIAL** with in-slice CI check, OR EXPOSED with honest ADR consequences |
| S10 surface invisibility | HANDLED (false claim) | **HANDLED** via trigger-phrase auto-fire + substrate pre-flight stderr hint |
| S11 phrase-trigger non-cairn collision | (new) | **HANDLED** via substrate pre-flight |
| S12 agent-name collision | (new) | **HANDLED** via `cairn-*` namespace |
| S13 deferral indefinite | (new) | **HANDLED** via dated trigger or honest closure |

## Verified-vs-believed final state

| Claim | Final status |
|---|---|
| "`using-cairn` is highest-leverage" | PARTIALLY VERIFIED — friction is verified; the *leverage ranking* is not. ADR consequences must acknowledge this. |
| "Friction is paid per-machine, every session" | VERIFIED |
| "Auto-routed > slash-command discovery" | NOT VERIFIED — C-with-corrections retains auto-routing on the 4 nav agents but does not claim superiority, just utility |
| "Pyright/ast-grep/superpowers worth setup cost" | NOT VERIFIED — defers to `cairn-diagnostics-with-detection` slice |
| "Plugin-layout split is merge-blocker" | NOT YET VERIFIED — needs confirmation; tactical not strategic |
| "Nav agents have no contested decisions" | FALSIFIED → corrected by encoding the contested decisions explicitly in this slice's ADR |

## Confidence after corrections

**HIGH** that C-with-corrections is the right slice. Cracks A1, A3 are converted into ADR-encoded normative requirements. S9 is accepted as the standing exposure with explicit fallback (build CI or accept honest EXPOSED). The diagnostic 2 agents have a real deferral trigger, not a rhetorical one.

The remaining unverified claim ("`using-cairn` is *highest-leverage*") is accepted as a hypothesis the slice tests by shipping. If the SessionStart skill ships and J1 friction does not collapse, the ADR's consequences section commits to revisiting via a follow-up /decision rather than accreting more SessionStart payload.

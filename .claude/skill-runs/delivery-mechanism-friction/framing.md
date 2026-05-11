# Decision Framing — delivery-mechanism-friction

**Date:** 2026-05-11
**Operator:** Firaaz
**Originating artifacts:**
- Issue #33 "Reduce incidental friction in delivery mechanism (keep enforcement substrate)"
- Branch `feature/workflow-subagents` (commit `8b680cb`, ahead of `dev`, unmerged)
- Analysis: `/Users/firaazfarook/.claude/plans/look-at-feature-workflow-subagents-branc-enumerated-hippo.md`

## The decision question

**What is cairn's delivery-mechanism direction-of-travel?**

Sub-questions that fall out of it:

1. **Setup-surface direction**: should cairn's consumer-machine setup surface go *up* (more required deps like Pyright, ast-grep, `ENABLE_LSP_TOOL=1`, user-scope superpowers — as `feature/workflow-subagents` proposes via `docs/PREREQS.md`), or *down* (fewer required deps, in-session bootstrap, friction paid by the substrate only — as #33-1 proposes)?

2. **Discoverability mechanism**: is the right vehicle a SessionStart `using-cairn` meta-skill (#33-1), auto-routed phrase-triggered subagents (`feature/workflow-subagents`), better-surfaced slash commands (#33-2), or some combination?

3. **External-plugin coupling**: should cairn agents take a **hard methodology dependency** on `superpowers:systematic-debugging` / `:defense-in-depth` (as `pytest-triage` and `root-cause-hunter` currently do), a **soft-cite** ("use if available"), or **no external citation** (internalize the methodology)?

4. **Consequence for the branch**: given the above, does `feature/workflow-subagents` merge as-is, get reworked (which parts? PREREQS reshape? superpowers-cites soften?), get split (handoff-closer alone? diagnostics behind a flag?), or set aside until a `using-cairn` bootstrap skill lands first?

## Substrate non-negotiables (do not violate)

From #33's "Essential friction — keep" list:

- Role isolation in phase agents (fabrication-blocking contract)
- Append-only ADRs with supersession protocol
- Machine-checked invariants (INV-001..011)
- Conventional Commits + phase prefixes (INV-001 binding)
- Two-field id+name on ADRs and slices
- `reversibility-guard` on catastrophic ops

Any approach that weakens these is out of scope.

## Load-bearing claims to attack (per `feedback_attack_before_synthesis`)

1. (External brief — #33) "The `using-cairn` SessionStart skill is the highest-leverage item." — author's prior; not verified against actual cairn onboarding traces.
2. (External brief — #33) "Discovery cost is paid by every consumer on every machine." — true in principle; magnitude of practical pain is not measured.
3. (Branch) "Auto-routed subagents are a better discovery mechanism than slash-command surfacing." — implicit, not argued.
4. (Branch) "Pyright LSP / ast-grep / superpowers are worth the setup-surface cost they introduce." — capability claim; trade against #33-1's direction-of-travel.
5. (Analysis) "Plugin-layout split (`.claude/agents/` vs `agents/`) is a merge-blocker." — not yet verified; needs to check what `/plugin install cairn@cairn-marketplace` actually ships today.

## Output structure (mirrors `m5-plugin-decision/`)

- `framing.md` (this file)
- `phase-0-constraints.md`
- `phase-0.5-journey.md`
- `phase-1-pre-mortem.md`
- `phase-2-approach-A.md` (capability-up)
- `phase-2-approach-B.md` (friction-down)
- `phase-2-approach-C.md` (hybrid / split)
- `phase-2-convergence-note.md`
- `phase-3-adversarial.md`
- `phase-3-corrections-applied.md` (if any)
- → ADR at `docs/adr/delivery-mechanism-friction.md` (firmness TBD by Phase 3 outcome)
- `phase-5-independent-verification.md` (only if Phase 4 lands as firm)

## Branch facts (frozen for this run)

- 1 commit, +334 LOC. 6 agents under `agents/`: slice-status, worktree-map, adr-context, handoff-closer, pytest-triage, root-cause-hunter.
- `docs/PREREQS.md` adds: Claude Code ≥ 2.0.74, Pyright, ast-grep, `ENABLE_LSP_TOOL=1`, user-scope `superpowers`, Ruff. Rejects Serena (well-argued).
- `handoff-closer` is the only writer; encodes substrate hygiene (stage-by-name, no -A, no amend, no commit-to-dev/main/master, no push).
- `pytest-triage` + `root-cause-hunter` cite `superpowers:systematic-debugging` as methodology gate.
- `root-cause-hunter` also cites `superpowers:defense-in-depth`.

## Issue #33 facts (frozen)

Seven candidates, leverage-ordered:
1. `using-cairn` SessionStart bootstrap skill (highest)
2. Slash-command discoverability
3. role_guard heredoc escape removal
4. `/fix-adr-typo` retires `ADR_EDITORIAL_FIX=1`
5. Scope id+name to ADRs/slices only
6. `small-change` / `exploration` path alongside 4-phase dispatch
7. Commit-prefix instead of JSON-stdout (debatable)

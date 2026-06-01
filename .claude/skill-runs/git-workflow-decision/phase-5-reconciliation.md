# Phase 5 reconciliation — independent verification vs the lead analysis

**Outcome: CONVERGED.** The independent verifier (fresh context, blind to the lead artifacts and to the operator's pre-decision) independently recommended **branch-per-feature + `git merge --no-ff` into `dev`**, with the *same* decisive justification: `validate_architecture.py:367` runs the INV-001 walk with `--no-merges`, so the un-prefixed merge subject is skipped, while `--no-ff` preserves the 4 phase commits the audit trail + INV-001 per-prefix verifiers depend on. Squash and rebase independently rejected for destroying the phase SHAs / SNAPSHOT_SHA anchor. This is strong evidence against correlated error — two derivations, one conclusion.

## Shared must-pin list (both analyses)
- Pin `--no-ff`; document the merge-commit exemption via `--no-merges` at `validate_architecture.py:367`.
- Supersede `identifier-scheme` D4 → flat feature-level branch name, no slice child.
- Base the branch at SNAPSHOT_SHA; forbid mid-feature rebase/squash.
- Redefine "Complete = feature branch merged `--no-ff` with Phase-4 PASS" (supersede the `feature-slice-model` D4 / INV-006 status-derivation table).
- Supersede all three stale ADRs in frontmatter (or the validator's drift check flags it).
- Copy `.claude/active-envelope.yaml` into any feature worktree (role_guard worktree-scoped, fail-open when absent).

## Two substantive additions from the independent pass (incorporate)

1. **Branch name `feature/<feature-id>`, not `feat/<feature-id>`.** The independent pass chose `feature/`; the repo already uses `feature/*` (`feature/workflow-subagents`, `feature/board-roadmap-integration`, `feature/compression-followup`). Align the taxonomy to the existing convention. (`feat` stays the *commit-type* prefix; `feature/` is the *branch* prefix — no conflict.)

2. **Direct-to-dev must remain LEGAL (not the model, but the legal fast path).** The independent pass flagged that the current `dev` history is 100% linear honest direct commits; a firm rule that *mandates* branching would retroactively invalidate that history and criminalize the honest single-feature fast path. Reconciliation: branch-per-feature + `--no-ff` is the **canonical model** (operator's choice), but the ADR should **keep direct-to-dev legal** for trivial single-feature work so it neither reds the validator nor invalidates existing linear history. This is a refinement to D1's *firmness* (canonical-default vs hard-MUST), not a reversion to Approach C.

## Divergences
None material. The independent pass did not surface the F5 merge-guard gap as sharply (it noted operator-forgets-to-branch but framed it as "keep direct-to-dev legal" rather than "guard the merge") — the lead Phase-1/Phase-3 finding on F5 (no mechanical backstop for `--no-ff`) stands and is the live operator-gate item.

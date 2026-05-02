---
slice: v1-defense-d2/inv-001-binding-implementation
feature: v1-defense-d2
phase: 1
role: phase-1-writer
adrs-referenced:
  - invariant-binding-strategy
  - pipeline-substrate-naming
  - bootstrap-exception
invariants-touched:
  - INV-001
modification-class: public-interfaces-only
inputs:
  - docs/plans/2026-05-02-inv-001-binding-design.md@b73fb83
  - docs/plans/2026-05-02-inv-001-binding-plan.md@03cad19
  - docs/adr/invariant-binding-strategy.md (D1, D2, D3, D8)
  - docs/adr/pipeline-substrate-naming.md (D1–D5)
  - docs/adr/cliff-failure-mode-and-v1-defenses.md (D2)
  - docs/adr/bootstrap-exception.md (cited; unchanged)
slice-of: 2
slice-index: 1
---

# Intent — INV-001 Binding Implementation (Slice 1 of 2)

## What

Bind invariant **INV-001** to a true machine-checkable assertion. A new `git-log-walk` validator type in `scripts/validate_architecture.py` replaces the `file-exists` deletion-detection proxy at `docs/ARCHITECTURE.md:13–19`. Co-creates `.claude/pipeline-substrate-registry.yaml`. INV-002 and INV-008 are explicitly slice-2 territory.

## Why

The present assertion (`type: file-exists`, target `commands/claude-code/start-slice.md`) only catches deletion of one file; it does not assert INV-001's actual content (post-bootstrap commits flow through `/decision`, `/start-slice`, or registered substrate tools). `cliff-failure-mode-and-v1-defenses` D2 mandates a machine-checkable assertion for every firm invariant; `invariant-binding-strategy` D1 elevates the standard from grep/file-exists to typed assertions; D2 specifies `git-log-walk` for INV-001; D3 fixes `binding-effective-from` to the slice-close SHA. `pipeline-substrate-naming` D2/D3 own the registry shape and its nine D3 entries.

## Boundary

**In envelope:** `scripts/validate_architecture.py` (additions only); `.claude/pipeline-substrate-registry.yaml` (new, 9 D3 entries verbatim); `docs/ARCHITECTURE.md` INV-001 assertion block only (lines ~15–19, prose at ~13 unchanged); `docs/lessons.md` L-001:17 single-line closure; `tests/unit/test_inv_001_git_log_walk.py` (new RED, Phase 2 owns).

**Out of envelope:** INV-002 / INV-008 assertion blocks; `templates/handoff.md`; `commands/claude-code/handoff.full.md`; the `structural-parser` validator type; `scripts/slice_orchestrator/`. D3 grandfathering uses a literal `<pending-slice-close-sha>` placeholder treated as no-op-with-notice; substitution happens via a single post-close `docs:` commit (operator step or `/refresh-architecture`) — `close_slice` is **not** modified, resolving F5 self-application by design.

## Specification

**Binding contract (per `invariant-binding-strategy` D1–D3, D8):**

1. INV-001's assertion block declares `type: git-log-walk`, a `binding-effective-from` SHA, and the registry path.
2. The dispatcher in `_run_assertion` routes `git-log-walk` to `_run_git_log_walk_assertion`.
3. The handler reads `binding-effective-from`. If it equals the literal `<pending-slice-close-sha>` (or is empty) it emits an INFO notice and returns no failures (D3 grandfathering, no-op-with-notice).
4. Otherwise the walker runs `git log <effective-from>..HEAD --no-merges --format=%H%x09%s --name-only` plus a separate `--merges` pass for squash-merge classification per `pipeline-substrate-naming` D5.
5. For each commit: extract the prefix (`<word>:`), look it up in the registry. Miss → INV-001 violation cited by short SHA + subject + `prefix not in registry`. Hit → invoke the prefix's verifier from `_SUBSTRATE_VERIFIERS`.
6. Verifiers (per registry notes and ADR D5): `sweep:` requires touching both `.claude/sweep-results/` and `.claude/sweep.yaml`; `fix:` requires all changed files to live under `.claude/sweep-results/`; all other registered prefixes are pass-through (F2/D5 residual, accepted).
7. Failures aggregate (no early-exit) and return as a single newline-joined string; clean range returns `None`.

**Registry shape (per `pipeline-substrate-naming` D2/D3):**

YAML with top-level `entries:` list. Each entry carries required `prefix` (ending in `:`), `tool`, `owner-adr`, `since`; optional `notes`. Nine entries: `slice:`, `handoff:`, `sweep:`, `bootstrap:`, `feat:`, `docs:`, `fix:`, `chore:`, `test:`. `_load_substrate_registry` schema-checks each entry and raises `ValueError` on missing required fields; a missing file returns `{}` so the walker can hard-fail with `INV-001: registry not found`.

**ARCHITECTURE.md INV-001 assertion block becomes:**

```
type: git-log-walk
binding-effective-from: <pending-slice-close-sha>
registry: ".claude/pipeline-substrate-registry.yaml"
description: "True INV-001 binding via authorization-by-name walk over commits since binding-effective-from. Replaces prior file-exists proxy. Placeholder is substituted with the slice-close SHA by a single follow-up `docs:` commit (manual or via /refresh-architecture)."
```

**Public-interfaces-only modification class.** All new symbols (`_load_substrate_registry`, `_SUBSTRATE_VERIFIERS`, `_run_git_log_walk_assertion`, the `_verify_*` helpers) are additive within `scripts/validate_architecture.py`; no existing helper signatures or `_run_assertion` semantics change beyond the one new dispatcher branch.

## Verification

Phase 2 lands the eight RED tests verbatim from `docs/plans/2026-05-02-inv-001-binding-plan.md` §Phase 2 into `tests/unit/test_inv_001_git_log_walk.py`:

1. **T1** — Registry file present, YAML-parseable, schema-checked (`prefix`, `tool`, `owner-adr`, `since` per entry).
2. **T2** — Every registered prefix has a verifier in `_SUBSTRATE_VERIFIERS` (or pass-through marker).
3. **T3** — Walker with `binding-effective-from: <pending-slice-close-sha>` returns `None` and emits a "binding pending effective-from" notice.
4. **T4** — Synthetic repo with an unregistered `wibble:` commit → walker reports the offending SHA with `not in registry`.
5. **T5** — Synthetic `sweep:` commit missing required touches → `sweep verifier: missing .claude/sweep-results/` failure cited by SHA.
6. **T6** — Synthetic `sweep:` commit touching both required paths → walker returns `None`.
7. **T7** — Squash-merge `feat:` accepted on prefix alone (F2 residual documented).
8. **T8** — End-to-end: `uv run python scripts/validate_architecture.py` exits 0 with the placeholder still set (real ARCHITECTURE.md INV-001 block).

Phase 4 PASS verdict requires the eight evidence items from the plan §Phase 4: dispatcher branch citation; `_SUBSTRATE_VERIFIERS` table citation; registry exists with all 9 D3 entries; T1–T8 GREEN; validator end-to-end exit 0; L-001:17 closure citation in `docs/lessons.md`; `git diff --name-only` confirming no `scripts/slice_orchestrator/` change; full suite GREEN minus the documented L-015 XPASS-strict cases.

## Reader anti-behaviors honored

- No proposal of validator types beyond `git-log-walk` (`structural-parser` is slice 2).
- No edit to INV-002 or INV-008 prose or assertion blocks.
- No source-code reads performed; intent derived from arch/ADR context (`docs/plans/...-design.md`, `docs/plans/...-plan.md`, the three referenced ADRs, `docs/ARCHITECTURE.md` INV-001 block) only.

## Open decision points (for Phase 2/3)

- **DP-1 — verifier module placement:** single-file (alongside the walker in `scripts/validate_architecture.py`) vs. extracted `scripts/validate_architecture/substrate_verifiers.py`. Design-doc default is single-file unless line-count exceeds existing module conventions; Phase 3 builder resolves at implementation time.
- **DP-2 — file-shape diff source:** `git show --name-only <SHA>` per-commit vs. parsing aggregate `git log --name-only`. Plan §Phase 3 skeleton (`_git_subjects_in_range`) encodes the latter; Phase 3 builder confirms.

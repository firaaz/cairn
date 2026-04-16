---
slice: identifier-scheme/hook-tolerance
date: 2026-04-15
phase: 1-intent
invariants-touched: [INV-005]
adrs-referenced: [identifier-scheme]
envelope:
  - "checks/reversibility-guard.sh"
  - "checks/scope-guard.sh"
  - "checks/reality-check.sh"
  - "tests/unit/test_hook_tolerance.py"
out-of-scope:
  - "Renaming any existing ADR file from `NNN-slug.md` to `<id>.md` (Phase 2 of the migration; not this slice)."
  - "Renaming any existing slice from `SLICE-NNN` to hierarchical `<feature>/<slice>` (Phase 2 of the migration; not this slice)."
  - "Removing legacy-format regex branches (Phase 3 of the migration; deferred indefinitely per identifier-scheme ADR D7)."
  - "`scripts/validate_architecture.py` widening to recognize non-numeric ADR IDs in `**INV-NNN**` lines (named substrate gap; follow-on slice)."
  - "Updating slash-command surface in `commands/claude-code/` (covered by other identifier-scheme slices)."
  - "Cross-reference sweep across `docs/`, `.claude/` (Phase 2)."
---

### What and Why

Widen the three repository hooks (`reversibility-guard.sh`, `scope-guard.sh`, `reality-check.sh`) so their identifier-shape recognition tolerates both the legacy numeric-prefix forms (`docs/adr/NNN-slug.md`, `SLICE-NNN`) and the new flat-slug ADR / hierarchical slice forms introduced by the `identifier-scheme` ADR. This closes the bootstrap-window gap recorded in that ADR's Consequences section: `docs/adr/identifier-scheme.md` is currently unprotected by `reversibility-guard.sh`'s append-only enforcement because the existing glob `*/docs/adr/[0-9]*` matches only filenames whose first character is a digit. Until this slice lands, the governing ADR for the identifier scheme can be silently overwritten — and no other flat-slug ADR may be authored in the repository.

### Specification Detail

The slice operationalizes the identifier-scheme ADR's D7 Phase 1 "Hook tolerance" commitment. After this slice:

1. **`reversibility-guard.sh` recognizes flat-slug ADR filenames as ADRs.** Both the `Write` clause (currently `checks/reversibility-guard.sh:51`, glob `*/docs/adr/[0-9]*`) and the `Edit` clause (currently `:68`, same glob) MUST match files whose stem is a flat semantic slug per the identifier-scheme ADR's D2 (e.g. `docs/adr/identifier-scheme.md`, `docs/adr/parallelism-v1.md`) **as well as** the existing legacy form `docs/adr/NNN-slug.md`. The append-only enforcement (block overwriting `Write`; allow `Edit` only when `old_string` first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:`; and the `ADR_EDITORIAL_FIX=1` escape hatch) MUST apply unchanged to both forms — the only widening is which filenames count as ADRs in the first place. Files outside `docs/adr/` are unaffected.

2. **`scope-guard.sh` and `reality-check.sh` continue to operate correctly under both identifier conventions.** Where either script keys on the legacy `SLICE-NNN` slice-id format or the legacy `NNN-slug.md` ADR filename format, that recognition MUST also accept the new hierarchical `<feature>/<slice>` slice ids and the new flat-slug ADR filenames. Where neither script keys on identifier shape (i.e. recognition is purely path-based or content-based and does not parse identifier shape), no change is required and the script is left as-is. Pre-existing always-allow paths in `scope-guard.sh` (e.g. `docs/adr/*`, `.claude/current-slice/*`, `.claude/handoff.md`, `.claude/sweep.yaml`, `.claude/features/*`) continue to bypass envelope enforcement unchanged.

3. **No coexistence regressions.** A repository in mixed state — containing both legacy `NNN-slug.md` ADRs and flat-slug ADRs, both `SLICE-NNN` slice ids and hierarchical slice ids — MUST be handled correctly by all three hooks. The legacy regex branches remain present (Phase 3 removal is deferred indefinitely per the governing ADR's D7).

4. **No semantic changes to enforcement logic.** This slice widens *which inputs* the hooks recognize, not *what they do* once recognized. Append-only semantics, scope-guard envelope enforcement, and reality-check formatting/lint behavior are unchanged.

5. **No new dependencies.** The hooks already require `jq` and (for `reality-check.sh`) `ruff`. This slice introduces no new tool requirements.

### Boundary

Out of scope (in addition to the YAML `out-of-scope` block above):

- The `validate_architecture.py` widening that would let INV-005 cite `identifier-scheme` directly instead of via the ADR-006 proxy anchor — explicitly named in `docs/ARCHITECTURE.md` as a follow-on slice.
- Updates to slash-command files in `commands/claude-code/` — those carry their own identifier references and are handled by other slices in the `identifier-scheme` feature.
- Authoring or modifying any ADR. This slice references the `identifier-scheme` ADR as input but creates no ADRs and edits no ADR bodies. (The `slice-yaml-id: SLICE-016` field added to `.claude/features/identifier-scheme.yaml` during slice initialization is a feature-file metadata update, not an ADR change.)

### Verification

1. **Bootstrap-window gap closes.** A `Write` attempt on the existing file `docs/adr/identifier-scheme.md` is blocked by `reversibility-guard.sh` with the same `REVERSIBILITY GUARD: ADRs are append-only` reason currently emitted for `docs/adr/NNN-slug.md` files. Verified by the test suite invoking the hook with a synthesized event payload.

2. **Legacy ADR protection unchanged.** A `Write` attempt on an existing legacy file (e.g. `docs/adr/006-feature-slice-model.md`) is still blocked with the same reason. Append-only protection on numeric-prefix ADRs is not regressed.

3. **Frontmatter-only `Edit` still permitted on both forms.** An `Edit` whose `old_string` first line begins with `status:` is allowed by `reversibility-guard.sh` for both `docs/adr/identifier-scheme.md` and `docs/adr/006-feature-slice-model.md`. An `Edit` whose `old_string` first line is body prose is blocked for both.

4. **`ADR_EDITORIAL_FIX=1` escape hatch operates on both forms.** With the env var set, any `Edit` on either filename shape is allowed and the bypass is logged to `.claude/adr-editorial-fixes.log` (existing behavior, exercised against both filename shapes).

5. **New-ADR `Write` allowed for both shapes.** A `Write` to a non-existent path under `docs/adr/` succeeds with no block, regardless of whether the new filename is `docs/adr/100-future-slug.md` or `docs/adr/future-flat-slug.md`. (The `reversibility-guard.sh` Write clause blocks only existing-file overwrite; new-file writes pass through to default `exit 0`.)

6. **Scope-guard and reality-check coexistence.** Both hooks operate correctly when invoked with tool-input payloads referencing flat-slug ADR filenames and hierarchical slice ids. Specific behavioral assertions (which exact branches each hook needs widened) are deferred to Phase 2 enumeration since the public-surface scan in Phase 1 found no obvious slice-id-shape-matching code in either script — Phase 2 is responsible for confirming the actual gaps and writing tests against them, or recording the absence of any required change for that script.

7. **Hook-script self-test for current state.** The full test suite plus the architecture validator pass, and `git status` shows no out-of-envelope changes.

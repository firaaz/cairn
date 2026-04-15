---
slice: SLICE-015 (identifier-scheme/scheme-adr)
phase: 4-integration
branch: feature/identifier-scheme
as-of: 2026-04-15 7c45854
---

## State
Phase 4 D1 gate complete. ARCHITECTURE.md regenerated (INV-005 rewritten for two-field id+name model, validator-anchored via ADR-006); `test_v2_frontmatter_valid` widened to accept `superseded`. Validator + 202/204 tests pass.

## Next
Run `/integration-sweep` to produce Phase 4 sweep notes with PASS verdict and `file:line` invariant evidence, then `superpowers:requesting-code-review` before slice close.

## Blocked / Pending
- Validator substrate gap: regex parses only `ADR-(\d+)` → cannot cite `identifier-scheme` directly; ADR-006 used as proxy. Widening queued for follow-on slice (NOT `hook-tolerance`).
- Hard ordering: `identifier-scheme/hook-tolerance` MUST be next slice; bootstrap-window gap open → `.claude/features/identifier-scheme.yaml`.
- Pre-existing pathologies still red: `test_v7_envelope_compliance`, `test_v4_envelope_compliance` — noise.
- Pre-existing drift: `docs/plans/measurements/2026-04-12-slice-003.txt`, `uv.lock` → housekeeping slice.
- D3 bypass log 2/3 in rolling window → one more triggers design review.

## Features
- identifier-scheme: SLICE-015 Phase 4 D1 closed; sweep + review pending; hook-tolerance scheduled next.
- v1-defense-d2: complete (SLICE-010, SLICE-011).
- v1-defense-d3: complete (SLICE-012, SLICE-013).

## Pointers
- `docs/ARCHITECTURE.md` — INV-005 + Naming transition paragraph; verify before sweep cites invariants.
- `.claude/current-slice/intent.md` — spec, out-of-scope boundary.
- `.claude/current-slice/implementation/notes.md` — root-cause for the 5 deferred failures (now closed).
- `.claude/features/identifier-scheme.yaml` — bootstrap-window ordering constraint.

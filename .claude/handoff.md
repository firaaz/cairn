---
slice: identifier-scheme/adr-rename-sweep
phase: 1-intent
branch: feature/identifier-scheme
as-of: 2026-04-17 0a63f39
---

## State
Phase 1 intent committed at 0a63f39 (slice #22). Broad-read scope: rename 9 numeric-prefix ADRs to flat-slug filenames + id: frontmatter migration + live cross-reference sweep in one slice.

## Next
Close session; run `/catchup` then `/start-slice phase 2` in a fresh session.

## Blocked / Pending
- Sweep #16 — carries d3-bypass Decision 2 substrate; run `/integration-sweep` after this slice closes.
- Reviewer suggestions (7) → `docs/lessons.md`.
- Rename queue remaining: `slice-and-feature-rename → doc-sweep`.
- `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted — ignore per operator directive.

## Features
- identifier-scheme: adr-rename-sweep Phase 1→2; slice-and-feature-rename + doc-sweep queued
- integration-gate: complete
- housekeeping: complete (SLICE-017/018)
- v1-defense-d2: complete (SLICE-010/011)
- v1-defense-d3: bypass-log-test-resilience complete; Decision 2 substrate queued

## Pointers
- `.claude/current-slice/intent.md` — Phase 2 Skeptic's sole input (plus `docs/adr/identifier-scheme.md`).
- `.claude/current-slice/handoff-phase-1.md` — phase-gate status and Skeptic-resolvable ambiguities.
- `.claude/sweep.yaml` — cadence state (last=20, current=22).

---
slice: coord (manual Axis-B dogfood — all workers merged)
phase: post-merge — coord sweep + refresh pending
branch: feature/identifier-scheme
as-of: 2026-04-16 — post D+B+A+C merge
---

## State
All 4 dogfood workers merged into `feature/identifier-scheme`. ADR-007 D2 (parallel SLICE-ID + sweep-ID safe at merge) **confirmed** across all four branches. No content loss; per-merge reconciliation cost was ~minutes (handoff.md + sweep-13.md + slice.yaml + features-yaml text merges).

| Worker | Branch | Merge commit |
|---|---|---|
| D hook-relpath | `slice/identifier-scheme-hook-relpath` | `e720e6a` |
| B bypass-log-reclass | `slice/v1-defense-d3-log-reclass` | `d8bd246` |
| A stale-22k | `slice/housekeeping-stale-22k` | `4d3d8f6` |
| C validator-flat-slug | `slice/identifier-scheme-validator` | (this merge) |

`sweep.yaml`: `last-sweep-at-slice: 18`. `.claude/sweep-results/2026-04-16-sweep-13.md` holds §D + §B + §A sections (C deferred its sweep to coord).

## Next
1. Coord-level `/integration-sweep` on `feature/identifier-scheme` — covers C's deferred sweep + final post-merge validation of the combined tree.
2. `/refresh-architecture` — reconcile `docs/ARCHITECTURE.md` with merged ADR/invariant changes (C's line 49 re-point, A's line 46 rebaseline wording, D/B substrate changes).
3. Kill worker tmux windows (`cairn:2` A, `cairn:3` C) + `git worktree remove --force` (chronic measurement drift in both).
4. End-of-dogfood writeup: append to `.claude/plans/2026-04-16-dogfood-observations.md` §8; copy closing note to `docs/lessons.md` as `L-005 — manual Axis-B dogfood findings`.
5. ADR-007 graduation decision: provisional → accepted (D2 confirmed; other dimensions partially tested — merge-time reconciliation cost observed but low).

## Blocked / Pending
- Chronic uncommitted `docs/plans/measurements/2026-04-12-slice-003.txt` — user directive: ignore.
- `scripts/snapshot_diff.py` classified-format parser — pending separate slice.
- `commands/claude-code/start-slice.full.md:224` rolling-window rewrite (text still says "3+ bypasses" all-class; should say "false-positive only") — pending separate slice.
- `d3-bypass-classification` Decision 2 `exempt:` syntax slice — pending (retires `.claude/slice-018-d3-oob.md`).
- `docs/ARCHITECTURE.md:116` stale substrate-gap + ADR-006 proxy clauses (C flagged; `/refresh-architecture` target).
- v1-defense-d2 SLICE-010/011 — queued.
- v1-defense-d3 substrate slice — queued.

## Features (post all-merged)
- identifier-scheme: D (hook-relpath) + C (validator-flat-slug) landed; feature fully drained.
- housekeeping: A (stale-22k-cleanup) landed on top of SLICE-017.
- v1-defense-d3: B (bypass-log-reclass) landed; substrate slice still queued.
- v1-defense-d2: SLICE-010/011 queued.

## Pointers
- `.claude/plans/2026-04-16-dogfood-observations.md` — obs log; §6 has `/handoff` side-effect divergence findings.
- `.claude/plans/2026-04-16-manual-parallel-dogfood.md` §7/§8 — merge protocol + success criteria.
- `.claude/sweep-results/2026-04-16-sweep-13.md` — §D + §B + §A sweep reconciliation; coord-level sweep supersedes.
- `.claude/slice-018-d3-oob.md` — one-shot D3 bypass record (B); retirement tied to Decision 2 slice.
- `docs/adr/007-parallelism-v1.md` — contract under test; dogfood graduation pending.
- `/tmp/cairn-fleet/2026-04-16/[ABCD]-*.log` — durable transcripts.

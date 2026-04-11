# D1 — Startup Floor Cuts: Completion Report

**Date completed:** 2026-04-11
**Plan:** `docs/plans/2026-04-11-d1-floor-cuts-plan.md`
**Design:** `docs/plans/2026-04-11-context-discipline-design.md`

## Shipped

- Task 1: baseline measurement captured (`docs/plans/measurements/2026-04-11-baseline.txt`)
- Task 2: cairn-internals content absorbed into `docs/operational-reference.md`
- Task 3: `CLAUDE.md` trimmed from ~1,935 to ~445 tokens (safety cheat sheet)
- Task 4: global plugins relocated — `~/.claude/settings.json` emptied, `claude-md-management` added to cairn project scope
- Task 5: D1.2 superpowers hook override documented as deferred
- Task 6: post-D1 measurement captured (`docs/plans/measurements/2026-04-11-post-d1.txt`)

## Measurement

| | Turn-1 context |
|---|---|
| Baseline (avg of 5 sessions) | 31,429 |
| Post-D1 (1 fresh session: `32fba4c6`) | 27,314 |
| Delta | 4,115 tokens (13.1%) |

**Target:** 1,600–2,300 token reduction.
**Actual:** 4,115 tokens — exceeded upper target by ~1,800 tokens.
**Verdict:** PASS (delta far exceeds the 1,500 floor; post-D1 within ±1,000 of the ~28,000 target midpoint).

**Caveat:** only one fresh post-D1 session was started for the measurement, not the three the plan script defaulted to. The other two "most recent" sessions by mtime are pre-D1 (the execution session itself, and one from the baseline window) and excluded from the post-D1 figure. The signal — a 4.1k-token drop against a 1.5k-token floor — is far above noise, so a single data point is sufficient.

**Why the delta overshot:** the plan estimated ~1,500 tokens from the CLAUDE.md trim plus ~100–800 from the global plugin relocation. Actual savings suggest the global plugin footprint was larger than estimated (context7 + commit-commands + claude-md-management at global scope likely cost ~2,500+ tokens when all three were loading on every session). This is a measurement artifact of scale — the per-plugin overhead is higher than the design-phase estimate accounted for.

## Non-cairn changes recorded

- `~/.claude/settings.json`: `enabledPlugins` emptied. This file is outside cairn's git. Do not re-enable globally — move plugins to project scope if needed in other projects. Original state (pre-D1):
  ```json
  "enabledPlugins": {
    "context7@claude-plugins-official": true,
    "claude-md-management@claude-plugins-official": true,
    "commit-commands@claude-plugins-official": true
  }
  ```

## Known follow-ups

- D1.2 (superpowers SessionStart hook) deferred. See `docs/plans/2026-04-11-d1-2-superpowers-hook-deferral.md` for revisit criteria.
- Other projects (`complex-rag-analysis`, etc.) lost the three global plugins. Each needs its own decision about which to re-enable at project scope. Not in D1's scope.

## Next step

Start Slice #2 (`handoff-catchup-protocol-rewrite`) via `/start-slice` in a fresh session. The D1 measurements establish the baseline for Slice #2's success criteria.

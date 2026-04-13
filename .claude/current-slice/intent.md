---
slice: d1-automated-architecture-refresh
date: 2026-04-13
phase: 1-intent
invariants-touched: [INV-001, INV-002]
adrs-referenced: [ADR-003, ADR-002]
envelope:
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice.full.md"
  - "commands/claude-code/refresh-architecture.md"
  - "commands/claude-code/refresh-architecture.full.md"
  - "scripts/validate_architecture.py"
  - ".claude/d1-bypasses.log"
  - "tests/unit/test_d1_*.py"
out-of-scope:
  - "checks/*.sh (no new hooks — D1 gates via slash command protocol, not shell hooks)"
  - "docs/adr/ (no new ADRs created by this slice)"
  - "docs/ARCHITECTURE.md (modified only by /refresh-architecture itself, not by this slice's implementation)"
---

### What and Why

ADR-003 D1 commits cairn to zero-drift between the ADR corpus and `docs/ARCHITECTURE.md`. Today `/refresh-architecture` runs manually; nothing prevents a slice from closing with stale architecture docs. This slice makes the refresh automatic on slice-close, gated on validator success, with an escape hatch for known false positives. It closes the stale-cached-mind gap (ADR-003 cliff mechanism step 2).

### Specification Detail

**Trigger.** `/start-slice complete` (Step 7 in `start-slice.full.md`) gains a D1 refresh gate between the Phase 4 PASS verdict and the `status: complete` transition. The gate runs `/refresh-architecture` logic and blocks completion if `scripts/validate_architecture.py` exits non-zero.

**Session isolation contract (ADR-003 D1, ADR-002 INV-002).** The refresh reads the full ADR corpus — content that no individual phase session should see. The refresh therefore runs in a **dedicated context**: it loads only `docs/adr/*.md` (excluding `index.md` and `status: superseded` files) and the prior `docs/ARCHITECTURE.md`. It does NOT load slice artifacts (`.claude/current-slice/*`), handoff state, or phase-role context. The commit it produces is a pipeline-substrate commit (class: `docs: refresh ARCHITECTURE.md from ADRs`), authorized under INV-001 per `docs/lessons.md` L-001 Exceptions.

**Escape hatch.** If the validator fails and the failure is a known false positive, the operator may set `ADR_D1_BYPASS=1` on the slice-close invocation. Each bypass is logged to `.claude/d1-bypasses.log` in the format:
```
<slice-id> <YYYY-MM-DD> <one-line-reason>
```
Three bypasses in a rolling 10-slice window triggers a D1 design review (the check is producing more noise than signal).

**Bypass log constraints.** `.claude/d1-bypasses.log` is append-only. It does not exist until the first bypass. The rolling-window check counts entries whose slice-id falls within the last 10 slices (by numeric suffix), not by date.

**Validator failure semantics.** When `scripts/validate_architecture.py` exits non-zero and `ADR_D1_BYPASS` is not set, `/start-slice complete` MUST refuse to transition to `status: complete`. It prints the validator output and instructs the operator to either fix the ADR/architecture inconsistency or use the bypass escape hatch.

**What changes in existing files.**
- `start-slice.full.md` Step 7 gains the D1 gate logic (refresh + validate + bypass check).
- `refresh-architecture.md` / `.full.md` gain a note that D1 invokes them automatically — no behavioral change to the manual command.
- `scripts/validate_architecture.py` is unchanged (already has the right exit codes). If its interface needs adaptation, that is an envelope expansion requiring this intent to be amended.

### Boundary

- This slice does NOT add shell hooks to `.claude/hooks/` or `checks/`. The gate lives in the `/start-slice complete` protocol text, not in a git hook.
- This slice does NOT change the validator's check logic — only the protocol that invokes it.
- This slice does NOT implement D2 or D3. The validator it gates on is the existing one.
- This slice does NOT touch `docs/ARCHITECTURE.md` content — only the protocol that regenerates it.

### Verification

1. `/start-slice complete` with a valid ADR corpus and passing validator: refresh runs, architecture doc regenerated, slice transitions to complete.
2. `/start-slice complete` with a validator failure (simulated by a planted ADR/architecture inconsistency): completion blocked, validator output printed, operator instructed to fix or bypass.
3. `/start-slice complete` with `ADR_D1_BYPASS=1` and a validator failure: completion proceeds, bypass logged to `.claude/d1-bypasses.log` with correct format.
4. Bypass log rolling-window: third bypass within 10 slices triggers a warning message.
5. Session isolation: the refresh context does not load `.claude/current-slice/*` or any phase-role artifacts.
6. The manual `/refresh-architecture` command continues to work unchanged.

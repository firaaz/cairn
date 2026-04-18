# Part 6: Auto-Advance Layer

**Date:** 2026-04-18
**Gates:** Part 0 ADR; Part 2 E2 (code-not-prose side effects); Part 2 E3 (state.json)
**Estimated:** ~5 slices
**Deployment:** Pre-F6 via hooks + skill auto-invocation; post-F6 composes with Layer 2 transitions.

## Intent

When the next action is *obvious from state*, cairn should take it without requiring the human to type a command. "Obvious" = deterministically inferable from slice state, phase status, test results, commit graph, and declared preconditions. No judgment required.

**Problem this names explicitly:**

After `/catchup` in the middle of a slice — say it lands in Mode A and tells you "you are in Phase 2 of X, next: `/start-slice phase 2`" — the human has to type `/start-slice phase 2`. The command is fully determined by the state `/catchup` just printed. This keystroke is pure ceremony.

Same pattern repeats throughout cairn:
- Phase-commit landed → `/handoff` is the only sane next move. Today: 3/8 dogfood boundaries had the operator recommend `/handoff` verbally then stop. The bootstrap-autonomy contract was broken.
- `/handoff` completed → `/clear` is the only sane next move.
- Phase 2 tests all red → advancing to Phase 3 is the only sane next move.
- Phase 3 tests all green, no regressions → Phase 4 is the only sane next move.
- Phase 4 gates pass → slice-complete + sweep prompt is the only sane next move.

Every one of these is a "Y/N" the human types when there's no N case anyone would pick.

## What this part builds

### AA1 — `/catchup` → auto-start-slice for Mode A

**Change:** When `/catchup` detects Mode A (phase entry), after printing the orientation summary, auto-execute `/start-slice phase N` where N is the current slice's next phase. User sees the orientation + gets into phase-N work in one action.

**Safety:** Single-line confirmation with 3s timeout: *"Auto-advance into Phase 3? [Y/n]"*. Default Y. Ctrl-C within 3s aborts.

**Slice:** `part-6-s1-catchup-autochain`.

**Depends:** Part 2 E1 (auto-phase-detect).

---

### AA2 — `/start-slice` phase-artifact-commit → auto-handoff

**Change:** After a phase artifact is committed (Phase 1 intent, Phase 2 tests + approach, Phase 3 implementation, Phase 4 integration), the skill auto-invokes `/handoff`. No verbal recommendation; no waiting.

Pre-conditions that must pass:
- Commit landed with expected message prefix.
- Phase-N artifact files exist at expected paths.
- No lingering uncommitted edits to declared artifacts.

Failure → skill stops, prints specific remediation. Does not auto-advance on unclear state.

**Fixes:** L-005 bootstrap-autonomy-broken finding. Replaces "recommend `/handoff` verbally" with "run it."

**Slice:** `part-6-s2-phase-commit-autohandoff`.

**Depends:** Part 2 E2 (code-side-effects exists); Part -1 #4 (handoff verifier).

---

### AA3 — Next-session hint file + session-start auto-resume

**Problem:** Cross-session continuity currently requires the human to remember "last time I finished Phase 2; next session I should `/catchup` then `/start-slice phase 3`." Even after `/handoff`, there's a fresh-session cognitive tax.

**Change:**
- `/handoff` writes `.claude/next-session.yaml`:
  ```yaml
  version: 1
  sha_at_handoff: af660a5
  slice_id: identifier-scheme/slice-and-feature-rename
  resume_action: /start-slice phase 3
  emitted_at: 2026-04-18T14:23:00Z
  expires_at: 2026-04-19T14:23:00Z
  ```
- Session-start hook reads this file. If exists + not expired + SHA matches + slice still active: print one line *"Auto-resume at Phase 3 of X? [Y]/n (3s)"*. Default Y with timeout.
- Invokes `/catchup` + `/start-slice phase 3` automatically.

**Expiry:** 24h default. Longer risks stale state.

**Slice:** `part-6-s3-session-resume-hint`.

**Depends:** Part 2 E3 (state.json — can share schema with next-session.yaml).

---

### AA4 — Phase-boundary precondition auto-check

**Problem:** Transitions between phases have declared preconditions (Feature 6 transitions.yaml references these):
- 1→2: intent committed, envelope declared, ADRs referenced.
- 2→3: tests red, approach committed, coupling-clusters written.
- 3→4: tests green, scope unchanged, no fork-log entries.
- 4→complete: integration gate passed, snapshot clean.

Today these are prose in the skills. The operator eyeballs them. Fallible under context pressure.

**Change:** Each phase-boundary dispatches a precondition check (script or subagent) before running the side-effects. Auto-runs:
- `scripts/precondition_phase_{N}_to_{N+1}.sh` — exits 0 if preconditions met, non-zero + detailed failure message otherwise.
- Skill runs the script; pass → side-effects fire; fail → surface failure, abort, tell user what to fix.

No human verification step for the common case. Human only intervenes on failure.

**Slice:** `part-6-s4-precondition-autochecks`.

**Depends:** Part 0 P4 (coupling clusters for Phase 2); Part 2 E2 (code-side-effects).

---

### AA5 — Auto-advance policy file + runtime

**Problem:** Ad-hoc auto-advances (AA1-AA4) each live in their own skill. A coherent policy file is missing — no central "what's eligible for auto-advance" catalog.

**Change:** `.claude/auto-advance-policy.yaml`:

```yaml
version: 1
defaults:
  confirmation_timeout_seconds: 3
  audit_log: .claude/auto-advance.log
  global_disable_env: CAIRN_AUTO_ADVANCE

rules:
  - name: catchup-mode-a-to-start-slice
    from_state: catchup-mode-a-completed
    to_action: /start-slice phase {N}
    gate: confirm-default-y
    preconditions: [slice-active, phase-detected, handoff-note-present]

  - name: phase-commit-to-handoff
    from_state: phase-artifact-committed
    to_action: /handoff
    gate: autonomous
    preconditions: [commit-matches-expected-prefix, phase-artifact-present, no-lingering-edits]

  - name: handoff-complete-to-clear-hint
    from_state: handoff-committed
    to_action: emit-next-session-hint
    gate: autonomous
    preconditions: [handoff-verifier-passed]

  - name: session-start-resume
    from_state: session-start-with-valid-hint
    to_action: /catchup + /start-slice phase {N+1}
    gate: confirm-default-y
    preconditions: [hint-not-expired, sha-matches, slice-still-active]

  - name: phase-2-tests-all-red-advance
    from_state: phase-2-tests-written
    to_action: /start-slice phase 3 (offer)
    gate: confirm-default-y
    preconditions: [all-phase-2-tests-red, approach-md-present, coupling-clusters-present]

  - name: phase-3-tests-all-green-advance
    from_state: phase-3-implementation-complete
    to_action: /start-slice phase 4 (offer)
    gate: confirm-default-y
    preconditions: [all-phase-2-tests-green, no-other-test-regressions, envelope-only-touched]

  - name: phase-4-gates-pass-complete
    from_state: phase-4-integration-complete
    to_action: /handoff (slice-complete)
    gate: confirm-default-y
    preconditions: [integration-gate-passed, snapshot-clean]
```

Runtime reads the policy file; matches current state; acts per gate field. Every action logs to the audit file. Every user-visible action prints what it did + what it's about to do before doing it.

**Slice:** `part-6-s5-auto-advance-policy-runtime`.

**Depends:** All other Part 6 slices (this is the consolidation layer).

## Gate vocabulary

Three gate types from F6 Layer 2, reused here:

- **`autonomous`** — act without prompting. Audit-logged. Reserved for purely mechanical side-effects (commits, file writes, hook invocations).
- **`confirm-default-y`** — print action intent, accept Y/Enter/N within 3s. Default Y. Used for user-visible transitions where N would be rare but valid.
- **`confirm-default-n`** — print action intent, accept Y/N, default N. Used for potentially destructive or context-expanding actions.
- **`manual`** — human must type the command. Escape hatch.

## Safety guardrails

1. **Every autonomous action prints what it did.** After the fact, not instead of. Audit-logged to `.claude/auto-advance.log` with structured fields (timestamp, rule name, from-state, to-action, pass/fail, reason).
2. **Global disable.** `CAIRN_AUTO_ADVANCE=0` env var turns off every rule. Defaults to on.
3. **Per-rule disable.** Env var `CAIRN_AUTO_ADVANCE_DISABLE=<rule1>,<rule2>` disables specific rules.
4. **Git-backed reversibility.** Every auto-advance that mutates state produces a commit. `git reset --soft HEAD~` or `git revert` restores.
5. **No auto-advance across sessions without explicit hint file.** Session-start hook does NOT auto-advance unless `.claude/next-session.yaml` exists + fresh. Blank-slate session stays blank.
6. **No auto-advance past a human gate.** Some phase transitions remain manual per Feature 6 v0 autonomous set (phase 1→2, 2→3, 3→4, 4→merge). Part 6 AA4 checks preconditions automatically but does NOT auto-advance past these gates without confirmation. They become `confirm-default-y` here because the preconditions are machine-verified; the human only decides "is this really the right moment."
7. **Failure transparency.** When an auto-advance would fire but a precondition fails, print the specific failure + remediation step. Never silently skip.

## Visibility examples

### Good (current state is clearly surfaced)
```
[auto-advance] /catchup Mode A completed.
  from-state: phase-1-handoff-committed
  next-action: /start-slice phase 2
  preconditions: [slice-active✓, phase-detected✓, handoff-note-present✓]
  proceed [Y/n/e(dit)]? (3s)
```

### Good (autonomous action logged)
```
[auto-advance] Phase 1 intent committed (sha af660a5).
  Auto-running /handoff per rule phase-commit-to-handoff.
  Audit: .claude/auto-advance.log
```

### Never
```
(silent auto-action with no visible output)
```

## Slice breakdown

- **S1** — AA1 (`/catchup` → auto-start-slice). Depends on Part 2 E1.
- **S2** — AA2 (phase-commit → auto-handoff). Depends on Part 2 E2.
- **S3** — AA3 (next-session hint + session-start auto-resume). Depends on Part 2 E3.
- **S4** — AA4 (phase-boundary precondition auto-checks).
- **S5** — AA5 (policy file + runtime consolidation).

## Cross-cutting with other parts

| Item | Composes with |
|---|---|
| AA1 | Part 2 E7 `/catchup` subagent-first — they compose: subagent returns orientation fast, AA1 auto-dispatches next command |
| AA2 | Part -1 #4 handoff-verifier — AA2 gates on the verifier passing |
| AA2 | Part 2 E2 code-side-effects — AA2 is the trigger; E2 provides the mechanism |
| AA4 | Part 0 P4 coupling clusters + Part 2 E6 phase-2 output — preconditions read the output files |
| AA5 | Feature 6 `transitions.yaml` — Part 6 policy is the PRE-daemon layer; post-F6, the daemon consumes the same policy file or a shared schema |
| All of Part 6 | Part 5 S1 telemetry — every auto-advance emits a telemetry event that Part 5 aggregates |

## Composition with Feature 6

Feature 6 defines Layer 2 transitions (daemon-side). Part 6 defines what amounts to **Layer 1.5** — inside-session auto-advance that fires before the daemon sees anything.

- Pre-F6: Part 6 runs entirely in the worker's own skill layer. Hooks + skill prose drive it. Audit log is per-worktree.
- Post-F6: Part 6 emits events to F6's `events.fifo` for visibility. Daemon becomes aware of each auto-advance via the event stream. `transitions.yaml` (daemon's Layer 2) can override Part 6 rules if policy collides — daemon policy wins.

Shape compatibility: `auto-advance-policy.yaml` schema and `transitions.yaml` schema share fields (from_state, gate, preconditions). Port is 1:1 when F6 ships.

## Success criteria

1. A user in the middle of a slice invokes `/catchup`, sees their orientation, and is in the next phase **without typing another command** (unless they want to override).
2. L-005 bootstrap-autonomy broken pattern becomes impossible: phase-commit → handoff is autonomous, not prose-recommended.
3. Session-resume on a fresh day is one keystroke (Enter or timeout) instead of `/catchup` then `/start-slice phase N`.
4. Precondition failures surface immediately + specifically, instead of during integration-sweep days later.
5. Every auto-advance is visible + audited; nothing happens silently.

## Open questions

1. Should phase 2→3 and 3→4 transitions, which are human-gated in F6 v0, become `confirm-default-y` here (because preconditions are machine-verified) or stay manual pre-F6 until we have telemetry? Propose: `confirm-default-y` here; revisit based on audit-log data.
2. Is the 3s confirmation timeout right? Too fast risks accidental auto-advance; too slow defeats the purpose. Propose: 3s with a `CAIRN_CONFIRM_TIMEOUT` env override.
3. Auto-advance across sessions via `next-session.yaml` needs session-start-hook behavior. Does this conflict with existing session-start hooks (measurements-drift, role cheatsheet)? Need a session-start-hook orchestrator that sequences them cleanly. Part 5 territory?
4. Should `/clear` itself be auto-advanced after `/handoff`? Doable but risks context loss if the user wanted to stay in-session. Propose: offer it as `confirm-default-n`.
5. Multi-slice handoff: if you're in a parallel-worker context, does session-resume know *which* slice to resume? Pre-F6 this relies on `cwd` + `.claude/current-slice/`. Post-F6 the daemon knows via worktree association.

## Updated program totals

Adding Part 6: ~27 slices + 1 ADR → ~32 slices + 1 ADR.

Part 6 slices are short (each ~regular slice). Biggest complexity is S5 (policy runtime consolidation); S1–S4 are small.

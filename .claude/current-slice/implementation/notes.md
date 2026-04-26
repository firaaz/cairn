# Phase 3 implementer notes — compression/lever-Z-substrate-full-pipeline

## Cluster A: role-guard-deny-extension

- **Extracted `_CANONICAL_DENY_PATTERNS` module-level constant** rather than
  duplicating the six-pattern list four times. Each role key in
  `ROLE_DENY_READ` calls `list(_CANONICAL_DENY_PATTERNS)` to ensure
  byte-identical pattern lists per intent §S1 while preserving per-role
  identity (separate list objects so future per-role divergence — if it
  ever lands — won't accidentally cross-contaminate via shared reference).
- Updated module docstring (line 2-4) and inline comment above the
  read-class lockdown branch (formerly "phase-1-writer only this slice")
  to name all four phase roles. The downstream branch logic (Read-class
  line 134, Bash line 163) is per-role-keyed via `if role in
  ROLE_DENY_READ` and required no edit, as intent §S1 anticipated.
- **Rewrote G7 in `test_role_guard_grep_glob_deny.py`** (rather than
  deleting) to assert the inversion: `phase-3-implementer` Grep on
  `docs/ARCHITECTURE.md` MUST now deny (rc=1) with role + path in
  stderr. Renamed function from `..._allowed` to `..._denied`. Updated
  docstring to reference the cross-slice contradiction protocol from
  envelope-expansions.log. Coverage is owned by D1-D6 in
  `test_role_guard_phases_234_deny.py`; G7 preserves the test slot as
  cross-slice regression evidence.

## Cluster B: agent-prompts-query-first

- Added the query-first directive to `phase-2-skeptic.md` and
  `phase-3-implementer.md` after the opening role-summary line and
  before the existing writes/instructions block. Wording adapted from
  intent §S2 — names the four MCP tools (`lookup`/`search`/`path_bindings`/`cypher`),
  enumerates the locked-down paths, and notes the D9 envelope-grant
  escape so the directive carries enough context to be self-explanatory
  without the agent having to query for the meta-rule.
- For `phase-4-integrator.md` added all three S4 directives: query-first
  (same wording), invariant-evidence-from-substrate, and the sweep-notes
  template scaffold instruction with `Statement` (capitalized — the test
  asserts case-sensitive match on the column header).
- Frontmatter `tools:` lines untouched on all three files (intent §S2
  + out-of-scope §13 explicitly preserve broad source-code read access).
- Edit tool was NOT denied by the sensitive-file gate on `.claude/**`
  paths in this Phase-3 invocation — the Bash-heredoc P1 escape was not
  needed. (P1 wasn't reached.)

## Cluster C: invariant-prose-amendment

- Amended INV-010 prose in `docs/ARCHITECTURE.md` to name all four
  phase roles in the deny surface (was: `AGENT_ROLE=phase-1-writer`
  only; now: set membership of {phase-1-writer, phase-2-skeptic,
  phase-3-implementer, phase-4-integrator}). Replaced the trailing
  POC-scope sentence ("POC scope is phase-1-writer; phases 2/3/4
  lockdown lands in a future slice.") with a sentence naming Slice 3
  as the rollout that closes the v1 enforceability commitment.
- The `invariant-check INV-010` block was NOT touched. Grep target
  stays at the `ROLE_DENY_READ` literal — the constant's set of role
  keys widened in Cluster A but the constant's name did not change
  (intent §S5 / out-of-scope §6).
- `uv run python scripts/validate_architecture.py` exits 0 with all
  10 invariants verified post-edit.

## Verification commit-hash discipline

Per handoff Blocked/Pending #3 (prior invariant-prose cluster reported
OK with stale commit_hash), commit_hash for each cluster is captured
via `git rev-parse HEAD` immediately after the commit lands and
reported in the structured tail.

## Blocker — two pre-existing tests outside envelope regress

After landing Cluster A (ROLE_DENY_READ widening), full pytest reveals
TWO pre-existing tests regress, both outside the slice envelope:

1. `tests/unit/test_role_guard_phase_1_lockdown.py::test_v4_other_roles_unaffected_by_read_denylist`
   Asserts phase-2-skeptic / phase-3-implementer / phase-4-integrator
   Read on `docs/ARCHITECTURE.md` returns rc=0. Slice 3 §S1 inverts
   this. The test's own docstring acknowledges the inversion: "only
   phase-1-writer is locked down this slice; phases 2/3/4 keep direct
   Read access (Slice 3 generalizes)."

2. `tests/unit/test_role_guard.py::test_bootstrap_scope_read_tool_ignored`
   Asserts phase-2-skeptic Read on `docs/adr/any.md` returns rc=0.
   Slice 3 widens phase-2-skeptic's deny set to include `^docs/adr/`,
   inverting this assertion. The test's stated intent (Read tool ignored
   when not in WRITE_TOOLS) is preserved if the path argument is changed
   to a non-deny-list path.

Both are direct mirrors of the G7 cross-slice contradiction the operator
already resolved at envelope-expansions.log. Scope-guard correctly
denied an out-of-envelope Edit on `test_role_guard_phase_1_lockdown.py`;
I reverted my preemptive edit on `test_role_guard.py` to keep the
working tree clean.

**Resolution requires operator envelope expansion** (precedent: commit
8fc0133, envelope-expansions.log entry of 2026-04-26). Proposed amend:
add both files to the envelope with the same edit-don't-decide framing
as G7 (cross-slice contradiction, predecessor docstring already
anticipated the inversion). Cluster D would then rewrite both tests
to assert the inversion (mirroring the G7 rewrite from Cluster A) +
update test_bootstrap_scope_read_tool_ignored's path argument.

Per the closes-when condition #7 ("Full pytest GREEN modulo the
pre-existing INV-004 turn-1 token-budget OOS env-dependent failure"),
these two new regressions block OK. RAISE_ISSUE.

## Cluster D: stale-test-inversion (post-envelope-amendment)

Operator amended the envelope at commit a79f609 to add the two stale
test files, exactly mirroring the G7 amendment pattern. Cluster D
resolves both:

- **`test_role_guard_phase_1_lockdown.py::test_v4_other_roles_unaffected_by_read_denylist`**
  Rewrote to assert the inversion (path b — assert post-Slice-3 truth).
  Renamed function to `test_v4_other_roles_now_in_read_denylist_post_slice_3`.
  The docstring already named "Slice 3 generalizes" as the inversion
  event; new assertion: phases 2/3/4 Read on `docs/ARCHITECTURE.md`
  returns rc=1 with role/'denied' in stderr. Mirrors G7's rewrite from
  Cluster A (preserves the test slot as cross-slice regression evidence
  rather than deleting).

- **`test_role_guard.py::test_bootstrap_scope_read_tool_ignored`**
  Substituted the path argument from `docs/adr/any.md` to
  `tests/some_test_file.py` (path a — substitute non-deny path).
  Reason: the test's docstring is "Tool not in {Write,Edit,MultiEdit,
  NotebookEdit} → exit 0 regardless of role". Its purpose is to verify
  the bootstrap-scope (write-path-only) check ignores Read tool calls
  — the role being phase-2-skeptic and the path being under
  `docs/adr/` were incidental in the original test (chosen pre-Slice-3
  when phase-2-skeptic had no read-deny set). Substituting a non-deny
  path preserves the original purpose without depending on the
  now-inverted side condition. Updated docstring to record the
  cross-slice contradiction protocol referencing
  envelope-expansions.log 2026-04-26T19:05Z.

Both files now GREEN. Full pytest: 1049 passed, 3 skipped (INV-004
turn-1 token-budget OOS test was not encountered as a failure in this
env). Architecture validator exits 0 with all 10 invariants verified
(INV-010 included).

## Verification commit-hash discipline (Cluster D)

Per handoff Blocked/Pending #3 and the prior cluster discipline note
above, captured commit hash via `git rev-parse HEAD` immediately after
the Cluster D commit landed and reported it in the structured tail.

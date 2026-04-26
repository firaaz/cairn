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

- (to be filled)

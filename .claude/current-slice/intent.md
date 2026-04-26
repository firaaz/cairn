---
slice: compression/lever-Z-substrate-full-pipeline
date: 2026-04-26
phase: 1-intent
invariants-touched: [INV-010]
adrs-referenced: [cairn-substrate-and-fastmcp]
envelope:
  - "checks/role_guard.py"
  - ".claude/agents/phase-2-skeptic.md"
  - ".claude/agents/phase-3-implementer.md"
  - ".claude/agents/phase-4-integrator.md"
  - "docs/ARCHITECTURE.md"
  - "tests/unit/test_role_guard_phases_234_deny.py"
  - "tests/unit/test_phase_2_skeptic_query_first_prompt.py"
  - "tests/unit/test_phase_3_implementer_query_first_prompt.py"
  - "tests/unit/test_phase_4_integrator_query_first_prompt.py"
  # Operator pre-Phase-3 amendment 2026-04-26: Slice-2-fixup's
  # test_g7_phase_3_implementer_grep_on_deny_list_path_allowed asserts
  # phase-3-implementer is NOT in ROLE_DENY_READ — directly inverted by
  # this slice's §S1. Surfaced by Phase 2 skeptic; G7 docstring already
  # anticipates the inversion. Edit-don't-decide per cross-slice
  # contradiction protocol (handoff Blocked/Pending #4, commit 8fc0133
  # precedent). Phase 3 deletes or rewrites G7 alongside the
  # ROLE_DENY_READ extension.
  - "tests/unit/test_role_guard_grep_glob_deny.py"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/slice.yaml"
  - ".claude/features/compression.yaml"
out-of-scope:
  - "Phase-1 dispatch defect (built-in CC sensitive-file gate on .claude/** denies Write; P1 Bash-heredoc escape unreachable post-Slice-2-fixup) — separate fixup slice"
  - "Mutation surface (ADR D7 explicit deferral; v1 substrate stays read-only)"
  - "AGENT_ENVELOPE schema changes (Slice 2 wired; this slice consumes the object shape unchanged)"
  - "Bash read-class deny widening (cat/head/grep tokens already extracted via _bash_path_tokens)"
  - "INV-010 invariant-check `target:` block (grep target stays ROLE_DENY_READ literal — set widens, name does not)"
  - "scripts/cairn_query/** internals (substrate Slice 1 territory)"
  - "mcp_servers/cairn_knowledge/** internals (Slice 2 + Slice 2 fixup territory)"
  - "scripts/slice_orchestrator/dispatch.py AGENT_ENVELOPE construction (Slice 2 already wired phases 1-4)"
  - "Substrate Slice 4+ (not yet designed)"
  - "Per-phase MCP tool surface differentiation (all four phases share the four-tool surface)"
  - "Any new ADR (operationalizes existing D6/D8/D9)"
  - "Cost re-measurement infrastructure changes (uses existing Track-0 result.json)"
  - "phases 2/3/4 frontmatter `tools:` tightening (drop Read/Grep/Glob — phases 2/3/4 need broad source-code read access; lockdown enforced at role_guard layer only)"
---

### What and Why

Substrate Slice 2 (`compression/lever-Y-mcp-substrate`, closed `305cd02`) and the Slice-2 fixup (`compression/lever-Y-mcp-substrate-fixup`, closed `9b71cfa`) shipped the substrate's structural enforceability for `phase-1-writer` only — query-first via the `cairn-knowledge` MCP server, `ROLE_DENY_READ` at the `role_guard.py` hook layer, frontmatter outer gate, real JSON-RPC dispatcher, `fastmcp` standing dep, and `READ_CLASS_TOOLS = {Read, Grep, Glob}`. Slice 3 completes the second-stage rollout per ADR `cairn-substrate-and-fastmcp` D8 by extending the lockdown to `phase-2-skeptic`, `phase-3-implementer`, and `phase-4-integrator`. This is the first slice to dogfood orchestrator-driven query-first dispatch end-to-end across all four phase roles and **closes the substrate program's v1 enforceability commitment**. Cost target: ≥50% total stacked reduction vs the $18.71 Lever-1 baseline (per design doc §348).

Phase 1 of this slice is operator-interactive (hand-rolled in this session). Reason: orchestrator-driven `phase-1-writer` dispatch is currently blocked by Claude Code's built-in sensitive-file gate on `.claude/**` paths, and Slice-2-fixup hardening (Bash dropped from `phase-1-writer.md:4` frontmatter to defense-in-depth the canonical-knowledge lockdown) made the documented P1 Bash-heredoc escape unreachable. That defect is captured as a follow-up slice and is explicitly out of scope here. Phases 2-4 dispatch via in-session subagents (the prior slice's pattern, since the orchestrator `--resume` reconciler `_reconcile_resume_state` is still exported-but-never-called per `scripts/slice_orchestrator/resume.py:154` and won't accept hand-rolled phase-1-done state).

### Specification Detail

#### S1 — `ROLE_DENY_READ` extended to phases 2/3/4

`checks/role_guard.py` lines 29-38 currently maps `phase-1-writer` to six canonical-knowledge path patterns. Slice 3 MUST extend the table to add `phase-2-skeptic`, `phase-3-implementer`, and `phase-4-integrator` keys mapped to **the same six patterns** (DRY refactor — extract a `_CANONICAL_DENY_PATTERNS` constant if Phase-3 implementation prefers, or duplicate verbatim — implementation choice as long as the four role keys end up with byte-identical pattern lists). The patterns:

- `^scripts/cairn_query/`
- `^docs/ARCHITECTURE\.md$`
- `^docs/adr/`
- `^docs/lessons\.md$`
- `^docs/spec-v1\.md$`
- `^docs/operational-reference\.md$`

The downstream branch logic (Read-class lockdown at line 134, Bash lockdown at line 163) is per-role-keyed via `if role in ROLE_DENY_READ`, so adding the three new role keys propagates the deny to all enforced surfaces with zero additional code:
- Read/Grep/Glob via `READ_CLASS_TOOLS = {Read, Grep, Glob}` — already extended in Slice-2-fixup;
- Bash via `_bash_path_tokens` — already extracts `cat`/`head`/`grep` token paths.

D9 envelope-grant escape MUST extend identically to all four roles. The `_envelope_patterns` parser (lines 67-90, JSON array / object-with-`paths` / colon-legacy) is role-agnostic and requires no edit.

#### S2 — `phase-2-skeptic` prompt query-first directive

`.claude/agents/phase-2-skeptic.md` MUST add a query-first directive in the prompt body (post-frontmatter, before the existing skeptic instructions) modeled on `phase-1-writer`'s pattern. Suggested text (Phase-3 may rephrase as long as semantics are preserved):

> **Query-first via cairn-knowledge MCP server.** When you need canonical knowledge (architecture invariants, ADR decisions, lessons, spec sections, operational rules), query through the `cairn-knowledge` MCP server using `lookup`/`search`/`path_bindings`/`cypher`. Do not Read/Grep/Glob the canonical sources directly — `role_guard.py` will deny those calls. Envelope-grant escape (D9): if a slice's envelope explicitly declares one of the locked-down paths, that path is read-allowed for that slice only.

The frontmatter `tools:` line (line 4) MUST remain `Read, Write, Edit, Bash, Grep, Glob` — phases 2/3/4 need broad source-code read access; dropping Read/Grep/Glob would break source-test work. The phase-1-writer-style "drop Bash, drop Grep+Glob" frontmatter tightening does NOT transfer to phases 2/3/4 (lockdown enforced at the `role_guard` layer only — see out-of-scope item).

#### S3 — `phase-3-implementer` prompt query-first directive

`.claude/agents/phase-3-implementer.md` MUST add the same query-first directive (S2 text adapted with phase-3-implementer-appropriate framing if needed). Frontmatter tools unchanged.

#### S4 — `phase-4-integrator` prompt query-first + invariant_check_results consumption + sweep-notes template scaffold

`.claude/agents/phase-4-integrator.md` MUST add three directives:

1. **Query-first** (per S2).
2. **Invariant evidence consumption.** When verifying an invariant declared in `intent.md`'s `invariants-touched` field, the integrator queries the substrate (e.g., `lookup` per `INV-NNN`, or `cypher` over Invariant records) for the canonical statement and the `invariant-check target:` grep token. The integrator runs the grep target against source as before (Bash-grep is the actual evidence collection); the canonical statement and target spec are READ from the typed record rather than re-grepped from `docs/ARCHITECTURE.md` by hand.
3. **Sweep-notes template scaffold.** When emitting `sweep-notes.md`'s invariants table, pre-fill the Statement column from substrate query results. Status (PASS/FAIL) and Evidence (file:line citations from the actual grep run) are filled from per-slice work as before. The intent is to remove hand-typed canonical-statement copying — not to remove evidence collection.

The frontmatter `tools:` line is unchanged. The existing write surface (`.claude/current-slice/integration/sweep-notes.md`, `handoff-phase-4.md`, `slice.yaml`, `.claude/handoff.md`, `.claude/sweep.yaml`) is unchanged.

#### S5 — INV-010 prose amendment

`docs/ARCHITECTURE.md` INV-010 prose currently names `phase-1-writer` in the deny surface (per Slice-2-fixup). Amend to name all four phase roles: `phase-1-writer`, `phase-2-skeptic`, `phase-3-implementer`, `phase-4-integrator` — equivalent phrasings acceptable as long as the prose names the actual set of roles the lockdown covers post-this-slice.

The `invariant-check INV-010` block MUST NOT be touched. The grep target stays at the `ROLE_DENY_READ` literal in `checks/role_guard.py` — the constant's set of role keys widens; the constant's name does not change. (Same discipline as Slice-2-fixup S5.)

#### S6 — Phase-2 RED tests

A new test file `tests/unit/test_role_guard_phases_234_deny.py` MUST cover, for each of the three new role keys (`phase-2-skeptic`, `phase-3-implementer`, `phase-4-integrator`):

- **D1 Read on locked-down path is denied.** With `AGENT_ROLE=<role>`, `tool_name=Read`, `tool_input.file_path` matching a `ROLE_DENY_READ` pattern (e.g., `docs/ARCHITECTURE.md`), `role_guard.main()` returns 1 and emits a stderr diagnostic naming the role and path.
- **D2 Grep on locked-down path is denied.** Same as D1 but `tool_name=Grep` (READ_CLASS_TOOLS coverage from Slice-2-fixup propagates).
- **D3 Glob on locked-down path is denied.** Same as D1 but `tool_name=Glob`.
- **D4 Bash with deny-path token is denied.** With `tool_name=Bash`, `tool_input.command="cat docs/ARCHITECTURE.md"` (or equivalent), denied via `_bash_path_tokens`.
- **D5 Envelope-grant escape allows the call.** With `AGENT_ENVELOPE` (object shape, `paths` key) matching the path, the call returns 0 and appends one line to `.claude/envelope-grants.log`.
- **D6 Non-locked path is allowed.** Path outside `ROLE_DENY_READ` patterns: returns 0, no diagnostic, no log entry.
- **D7 Cross-role isolation.** Existing `phase-1-writer` tests in `tests/unit/test_role_guard_grep_glob_deny.py` (G1-G7 from Slice-2-fixup) MUST still pass — adding the three new role keys MUST NOT alter `phase-1-writer` behavior.

Three new prompt-presence test files:

- `tests/unit/test_phase_2_skeptic_query_first_prompt.py` — string-presence assertion that the query-first directive text appears in `.claude/agents/phase-2-skeptic.md`.
- `tests/unit/test_phase_3_implementer_query_first_prompt.py` — same for `phase-3-implementer.md`.
- `tests/unit/test_phase_4_integrator_query_first_prompt.py` — three string-presence checks: (a) query-first directive, (b) invariant_check_results / substrate-query directive, (c) sweep-notes template scaffold instruction.

Brittleness of string-presence prompt tests is explicitly accepted per the cluster-RED-test discipline lesson from `compression/learnings-capture` (every Phase-3 cluster must carry a RED test, including prompt-amendment clusters — string-presence is the cheapest signal that GREEN cannot vacuously satisfy).

### Boundary

- **Out: Phase-1 dispatch defect.** A separate fixup slice MUST address the `.claude/**` sensitive-file gate / unreachable-P1-escape combination. Candidate fixes (operator-decision in the fixup): restore Bash to `phase-1-writer.md:4` frontmatter (steelman: `_bash_path_tokens` already catches canonical-knowledge `cat`/`head`/`grep` tokens, so canonical-knowledge lockdown is preserved; only the `.claude/**` escape is restored), or amend `settings.json`/CC built-in gate behavior, or document an alternative escape mechanism. This slice was hand-rolled at Phase 1 because of that defect; the defect itself is not in this slice's envelope.
- **Out: mutation surface.** ADR D7 explicit deferral — v1 substrate stays read-only.
- **Out: AGENT_ENVELOPE schema.** Slice 2 shipped the object shape with `paths` + `cairn_query_snapshot` keys. This slice consumes the schema unchanged.
- **Out: Bash read-class deny widening.** `_bash_path_tokens` already extracts path-like tokens from `cat`/`head`/`grep`/etc. No code path widening here.
- **Out: cairn_query / mcp_servers internals.** Slices 1 and 2 + the Slice-2 fixup own those.
- **Out: scripts/slice_orchestrator/dispatch.py AGENT_ENVELOPE construction.** Slice 2 already wired phases 1-4 to receive the object envelope with `cairn_query_snapshot`. No orchestrator-side changes here.
- **Out: INV-010 invariant-check `target:` block.** Grep target stays at the `ROLE_DENY_READ` literal — set membership widens, name does not.
- **Out: substrate Slice 4+.** Not yet designed.
- **Out: per-phase MCP tool surface differentiation.** All four phases share the same four-tool surface (`lookup`/`search`/`path_bindings`/`cypher`).
- **Out: new ADR.** D8's second-stage rollout to phases 2/3/4 is already authorized; no new ADR required.
- **Out: cost re-measurement infrastructure.** Uses existing Track-0 `orchestrator-result.json` + per-phase cost telemetry shipped pre-this-slice.
- **Out: phases 2/3/4 frontmatter `tools:` tightening.** Phases 2/3/4 need broad source-code read access; dropping Read/Grep/Glob would break their work. Lockdown enforced at the `role_guard` layer only for these three roles.
- **Out: orchestrator carry-over items from `.claude/handoff.md`.** `_reconcile_resume_state` orphan, Phase-3 commit-prefix drift (`fix(...)` vs `phase 3 [<cluster>]:`), Phase-3 invariant-prose cluster stale-`commit_hash` orphan — all separate concerns, candidates for `docs/lessons.md` or follow-up slices.

### Verification

#### Closes when

1. `checks/role_guard.py` `ROLE_DENY_READ` contains keys for `phase-1-writer`, `phase-2-skeptic`, `phase-3-implementer`, AND `phase-4-integrator`, each mapped to the same six canonical-knowledge path patterns (DRY refactor or duplication — implementation choice).
2. `tests/unit/test_role_guard_phases_234_deny.py` GREEN — D1-D7 cover all three new role keys.
3. `tests/unit/test_role_guard_grep_glob_deny.py` (Slice-2-fixup regression) still GREEN — `phase-1-writer` behavior preserved.
4. `.claude/agents/phase-2-skeptic.md`, `phase-3-implementer.md`, AND `phase-4-integrator.md` each contain the query-first directive text (string-presence verifiable by the new prompt-presence tests).
5. `.claude/agents/phase-4-integrator.md` additionally contains the invariant_check_results / substrate-query directive AND the sweep-notes template scaffold instruction (verifiable by `test_phase_4_integrator_query_first_prompt.py`).
6. `docs/ARCHITECTURE.md` INV-010 prose names all four phase roles in the deny surface; `invariant-check INV-010` `target:` block unchanged at the `ROLE_DENY_READ` literal.
7. Full pytest GREEN: `uv run python -m pytest` passes modulo the pre-existing INV-004 turn-1 token-budget OOS env-dependent failure (`test_inv004_turn1_token_budget`) documented in handoff and not introduced by this slice.
8. Architecture validator passes: `uv run python scripts/validate_architecture.py` exits 0 with INV-010 reported PASS.
9. Sweep-notes template fills invariant-evidence rows with Statement-column data sourced from substrate queries on this slice's own Phase-4 run (dogfood verification of S4).
10. Cost dogfood (soft observation, not hard gate): record per-phase cost in Track-0 `orchestrator-result.json`; full-slice total compared against $18.71 Lever-1 baseline. ≥50% stacked reduction is the design-doc target. If the actual delta is below target, the slice still closes structurally — the gap is recorded in `sweep-notes.md` as a finding for the next substrate iteration. (Phase 1 of this slice was operator-driven and does not contribute representative cost; the cost dogfood is for phases 2-4 dispatched via in-session subagents.)

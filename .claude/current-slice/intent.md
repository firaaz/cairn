---
slice: compression/lever-Z-fixup
date: 2026-04-27
phase: 1-intent
invariants-touched: [INV-003, INV-008]
adrs-referenced: []
envelope:
  - ".claude/agents/phase-1-writer.md"
  - ".claude/agents/phase-4-integrator.md"
  - "scripts/slice_orchestrator/lifecycle.py"
  - "docs/upgrading-from-pre-compression.md"
  - "docs/lessons.md"
  - "tests/unit/test_phase_1_writer_bash_restored.py"
  - "tests/unit/test_consumer_migration_doc.py"
  - "tests/unit/test_lessons_cross_slice_contradiction.py"
  - "tests/unit/test_lifecycle_artifact_relpaths_paper_cut.py"
  - "tests/unit/test_phase_4_integrator_paper_cuts.py"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/slice.yaml"
  - ".claude/features/compression.yaml"
out-of-scope:
  - "ROLE_DENY_READ deny-set widening or membership change (Lever-Z territory; closed at 003d9ad)"
  - "_reconcile_resume_state wiring (scripts/slice_orchestrator/resume.py:154 orphan — needs resume state-machine design pass; own slice)"
  - "Cost re-measurement against $18.71 Lever-1 baseline (gated on §13(a) so Track-0 telemetry runs end-to-end again — own slice)"
  - "scripts/cairn_query/** internals (substrate Slice 1 territory)"
  - "mcp_servers/cairn_knowledge/** internals (Slice 2 + Slice 2 fixup territory)"
  - "scripts/slice_orchestrator/dispatch.py AGENT_ENVELOPE construction (already wired phases 1-4)"
  - "scripts/slice_orchestrator/core.py and other lifecycle.py functions outside _ARTIFACT_RELPATHS (paper-cut scope only)"
  - "Substrate Slice 4+ (not yet designed)"
  - "INV-010 invariant-check `target:` block or ROLE_DENY_READ structural change"
  - "Mutation surface (ADR cairn-substrate-and-fastmcp D7 deferral; v1 substrate stays read-only)"
  - "Any new ADR (operationalizes existing decisions)"
  - "CLAUDE.md updates beyond what the consumer-migration doc references; CLAUDE.md surgery is a separate slice if needed"
  - "Bash read-class deny widening (cat/head/grep tokens already extracted via _bash_path_tokens in role_guard.py)"
  - ".claude/settings.json hook entries (only documented in (b); no in-repo change here — cairn's own settings already correct)"
---

### What and Why

Stabilization slice for the `compression` feature. Bundles four post-Slice-3 gating fixes surfaced during `compression/lever-Z-substrate-full-pipeline` (closed `003d9ad`) and **gates the `feature/compression → dev` merge**. The substrate program v1 enforceability commitment is structurally complete (`ROLE_DENY_READ` covers all four phase roles, MCP server functional, JSON-RPC dispatcher live), but four operational defects make the next orchestrator-driven slice unable to open cleanly and leave the consumer-migration story undocumented for downstream projects symlinking cairn via `.slice-system → .`. This slice closes those four items in a single bundled commit-set so the merge to `dev` can proceed.

**Phase 1 of THIS slice is itself operator-interactive (hand-rolled in this main session)** — the same recursive-bootstrap situation as `compression/lever-Y-mcp-substrate-fixup` and `compression/lever-Z-substrate-full-pipeline`, because the Phase-1 dispatch defect this slice fixes is currently active. Phases 2-4 dispatch via in-session subagents (the prior two slices' established pattern). The fix's own dogfood lands in the **next** orchestrator-driven slice, not this one — recorded as a soft Phase-4 finding in `sweep-notes.md` if a quick smoke-test is run, but not a hard close gate (a full end-to-end orchestrator dispatch is a separate workflow concern).

### Specification Detail

#### S1 — Restore `Bash` to phase-1-writer frontmatter (roadmap §13(a) — primary blocker)

`.claude/agents/phase-1-writer.md` line 4 currently reads `tools: Write, Edit`. Slice-2-fixup hardening dropped Grep+Glob+Bash from this list to defense-in-depth the canonical-knowledge lockdown. Combined with Claude Code's built-in sensitive-file gate that denies `Write` to `.claude/**` paths even under `bypassPermissions`, the documented Phase-1 Bash-heredoc escape (used by the orchestrator's `phase-1-writer` subagent to write `intent.md` and `.claude/features/<feature>.yaml`) is now unreachable. The first orchestrator-driven `/start-slice` after merge will fail the same way Lever-Z's would have (three retries → triager-escalate → operator hand-roll).

**Edit:** Change line 4 to `tools: Write, Edit, Bash`. (Grep+Glob remain dropped — only `Bash` is restored.)

**Steelman against "this undoes the Slice-2-fixup canonical-knowledge hardening":** `_bash_path_tokens` in `checks/role_guard.py` already extracts `cat`/`head`/`grep` token paths from Bash commands and routes them through the same `ROLE_DENY_READ` check that gates Read/Grep/Glob. Restoring `Bash` to phase-1-writer's frontmatter does NOT reopen the canonical-knowledge bypass; the `role_guard` layer enforces the deny against Bash-tokens regardless of frontmatter membership. Only the `.claude/**` write escape is restored. INV-010 preserved by construction.

**Why frontmatter at all:** Claude Code's outer subagent gate consults the `tools:` frontmatter; without `Bash`, the orchestrator's phase-1-writer subagent literally cannot invoke Bash even if `role_guard` would allow it. The frontmatter is the outer ring of defense-in-depth, and for `Bash` specifically the inner ring (`_bash_path_tokens`) already covers the canonical-knowledge surface this slice is NOT widening.

#### S2 — Consumer migration documentation (roadmap §13(b))

New file `docs/upgrading-from-pre-compression.md`. Cairn is consumed by downstream projects (`portfolio`, `complex-rag-analysis`, `kazoo`, others) via a `.slice-system → .` symlink at the consumer root. Updating the symlink alone does NOT make the new compression-feature wiring functional in an existing consumer. This doc enumerates the **5 wiring deltas** a consumer must apply post-merge, in order:

1. **Hook registration** in the consumer's `.claude/settings.json`: `checks/role_guard.py` registered as a `PreToolUse` hook on `Write|Edit|MultiEdit|NotebookEdit`; `scripts/role-cheatsheet.sh` (or equivalent) registered on `SessionStart`. Without these, role-keyed write-path enforcement (INV-003 narrow exception per `compression-infrastructure-bootstrap`) silently no-ops in the consumer.
2. **MCP server registration** in the consumer's `.mcp.json`: cairn-knowledge stdio server registered. Open question to address explicitly: `python -m mcp_servers.cairn_knowledge` only resolves when CWD is the cairn root, so consumers self-symlinked at `.slice-system → .` resolve trivially, but consumers using non-self-symlinked layouts need PYTHONPATH or an alternative invocation. Doc names whole-directory symlink as the recommended path and notes the PYTHONPATH escape for non-symlink layouts.
3. **Python dependencies** for the substrate (`pydantic`, `kuzu`, `mistune`, `typer`, `fastmcp`): two paths — (a) consumer runs `cd .slice-system && uv sync` and the orchestrator then runs under cairn's venv, OR (b) consumer vendors the deps into its own `pyproject.toml`. Doc names tradeoffs (isolation vs duplication).
4. **Agent + slash-command discoverability**: Claude Code reads agents from the consumer's `.claude/agents/` and slash commands from `.claude/commands/`, NOT from `.slice-system/.claude/...`. Whole-directory symlinks (`.claude/agents → .slice-system/.claude/agents`, `.claude/commands → .slice-system/.claude/commands`) are the cleanest path. Doc names this as the recommended migration step.
5. **`CLAUDE.md` updates** for two retired constraints: stdlib-only target (retired by ADR `cairn-substrate-and-fastmcp` D3 — substrate ships `pydantic`/`kuzu`/`mistune`/`typer`/`fastmcp`) and Rust-mapping end-of-v1 target (retired by ADR D4). Doc cites the ADR and decision points; CLAUDE.md surgery itself stays out of scope (consumer-side, slice-by-slice).

Doc structure: 5 numbered sections (one per delta), each ≤200 words, with a "Verify" snippet (a one-line shell command or grep that confirms the delta landed). The 5 deltas are the verifiable surface; cosmetic prose is open to Phase-3 judgment.

#### S3 — Cross-slice contradiction lesson L-014 (roadmap §13(c))

`docs/lessons.md` gains entry **L-014: Slice that widens an enforcement set should pre-grep for inverted assertions in the existing test corpus**. Three confirmed instances ground the lesson:

- G7 in Slice-2-fixup (resolved by commit `8fc0133`).
- G7-again, `test_v4_other_roles_unaffected_by_read_denylist`, and `test_bootstrap_scope_read_tool_ignored` in Lever-Z (resolved by envelope-expansion commits `2713662` and `a79f609`).

**Lesson directive (load-bearing — must appear verbatim or with preserved semantics):** "When a slice's spec widens an enforcement set (e.g., adds role keys to `ROLE_DENY_READ`, expands a deny pattern set, or generalizes a contract), Phase-2 skeptic SHOULD pre-grep the existing test corpus for assertions that depend on the OLD set membership and surface those tests as candidate envelope-expansions in the validation approach BEFORE Phase 3 dispatches. This catches the inversion structurally rather than discovering it at Phase-3 RAISE_ISSUE time, which costs re-dispatch cycles and operator-side envelope-expansion fixups."

**Rationale (≤100 words):** All three resolved instances took the form of an existing test asserting "role X is NOT in deny-list" being silently inverted by a slice that adds role X to the deny-list. The slice's intent.md correctly named the new set membership; what it did NOT name was the test corpus's existing negation assertions. A Phase-2-side `grep -rn "not in ROLE_DENY_READ\|other_roles_unaffected\|bootstrap_scope.*ignored" tests/` (or the equivalent for the enforcement set being widened) surfaces inversion candidates structurally. Cost is one Phase-2 grep; benefit is one less Phase-3 RAISE_ISSUE cycle.

Entry inserted as `L-014` after `L-013` in `docs/lessons.md` (currently 13 entries through L-013).

#### S4 — Operational paper-cuts (roadmap §13(d))

Two co-landed source edits, both in scope of the same operational-paper-cuts cluster:

**S4.a — `_ARTIFACT_RELPATHS` path reconciliation.** `scripts/slice_orchestrator/lifecycle.py:101` declares `_ARTIFACT_RELPATHS` with `"envelope-expansions.log"` at top-level. The actual orchestrator-bundle path during in-session execution wrote to `integration/envelope-expansions.log` (manually copied at Slice-3 close to avoid loss). Reconcile by changing the tuple entry from `"envelope-expansions.log"` to `"integration/envelope-expansions.log"`. Match-where-the-orchestrator-actually-writes is preferred over moving-the-orchestrator's-write-path because the orchestrator's bundle path is the more constrained surface (cross-references with `_copy_artifacts_to_sweep_results` and the bundle staging code). Regression test asserts `"integration/envelope-expansions.log" in _ARTIFACT_RELPATHS and "envelope-expansions.log" not in _ARTIFACT_RELPATHS` (the bare-string variant must NOT remain — both forms living together would re-introduce the silent-skip pattern).

**S4.b — `phase-4-integrator` prompt clarifications from Slice-3 dogfood.** `.claude/agents/phase-4-integrator.md` gains three clarifications surfaced as rough edges during Lever-Z's Phase-4 dogfood:

1. **`lookup`'s required `entity_type` parameter named explicitly.** The current prose mentions `lookup` as one of four query tools but does not call out that `entity_type` is required (not optional). Phase-3 amendment: name it.
2. **Typed-record attribute access vs subscript.** Substrate query results are pydantic models; access is `record.statement` (attribute), not `record["statement"]` (subscript). Phase-4 dogfood hit `KeyError` on subscript-style access. Phase-3 amendment: document the attribute-access pattern in one sentence.
3. **Stdio-only constraint of cairn-knowledge MCP.** The MCP server runs over stdio transport (per ADR `cairn-substrate-and-fastmcp` D6); in-process audit paths that try to import the server module directly will not see the JSON-RPC layer. Phase-3 amendment: flag the stdio-only constraint with a one-sentence note that in-process audits should call the underlying `tools.py` callables directly, not the server.

The frontmatter `tools:` line is unchanged. The existing write surface is unchanged. INV-003 preserved by construction (role contract widened in prose only, not in role identity or write-surface).

#### S5 — Phase-2 RED tests

Five new test files (one per S1-S4 sub-item):

- `tests/unit/test_phase_1_writer_bash_restored.py` — string-presence assertion that `.claude/agents/phase-1-writer.md` line containing `tools:` field includes `Bash`. RED until S1 lands. Includes a **negative regression**: `Grep` and `Glob` MUST NOT appear in the same line (Slice-2-fixup hardening preserved).
- `tests/unit/test_consumer_migration_doc.py` — file-existence assertion for `docs/upgrading-from-pre-compression.md`; presence-assertions for 5 section headers (one per wiring delta) and the 5 corresponding "Verify" snippets. Brittle by design — exactly the cluster-RED-test discipline from `compression/learnings-capture` (cheap signal that GREEN cannot vacuously satisfy).
- `tests/unit/test_lessons_cross_slice_contradiction.py` — string-presence assertion that `docs/lessons.md` contains the `L-014` heading and the load-bearing directive sentence (or its preserved-semantics equivalent — Phase-3 may rephrase, but the test asserts the stable token "pre-grep the existing test corpus" appears).
- `tests/unit/test_lifecycle_artifact_relpaths_paper_cut.py` — imports `_ARTIFACT_RELPATHS` from `scripts.slice_orchestrator.lifecycle` and asserts `"integration/envelope-expansions.log" in _ARTIFACT_RELPATHS` AND `"envelope-expansions.log" not in _ARTIFACT_RELPATHS`. Two-sided to prevent the silent-skip both-paths-present regression.
- `tests/unit/test_phase_4_integrator_paper_cuts.py` — three string-presence checks against `.claude/agents/phase-4-integrator.md`: (a) `entity_type` named in connection with `lookup`, (b) `record.statement` or equivalent attribute-access pattern named, (c) `stdio` constraint named in the cairn-knowledge MCP context.

All five test files are RED at Phase-2-commit and turn GREEN after Phase 3 lands the corresponding edits. Cluster-RED-test discipline (every Phase-3 cluster carries a RED test, including prompt/doc-amendment clusters) is honored throughout — brittleness explicitly accepted as the price of progress signal that GREEN cannot vacuously satisfy (per `compression/learnings-capture` retry's distinguishing constraint).

### Boundary

- **Out: ROLE_DENY_READ widening or membership change.** Lever-Z (closed `003d9ad`) shipped the four-role coverage. This slice does not touch the deny-set or its membership.
- **Out: `_reconcile_resume_state` wiring.** The exported-but-never-called orphan at `scripts/slice_orchestrator/resume.py:154` is a separate concern requiring a resume state-machine design pass — own slice. Surfaces in handoff Blocked/Pending #4 already.
- **Out: cost re-measurement against $18.71 baseline.** The Lever-1 baseline ($2.96 Phase-1 / $18.71 total) requires Track-0 telemetry to run end-to-end again, which itself is gated on §13(a) landing first. Re-measurement is its own slice once §13(a) ships and a clean orchestrator-driven slice runs.
- **Out: cairn_query / mcp_servers internals.** Substrate Slices 1, 2, and 2-fixup own those.
- **Out: orchestrator core/dispatch/resume modules outside `_ARTIFACT_RELPATHS`.** Paper-cut scope only — this slice does NOT touch `dispatch.py`, `core.py`, `resume.py`, `git.py`, or `telemetry.py`.
- **Out: substrate Slice 4+.** Not yet designed.
- **Out: INV-010 invariant-check `target:` block or ROLE_DENY_READ structural change.** Frozen by Lever-Z.
- **Out: mutation surface.** ADR `cairn-substrate-and-fastmcp` D7 explicit deferral; v1 substrate stays read-only.
- **Out: any new ADR.** This slice operationalizes existing decisions (ADR `cairn-substrate-and-fastmcp` D3/D4/D6/D8/D9 all referenced informationally; no new structural decisions).
- **Out: CLAUDE.md surgery.** The consumer-migration doc references retired constraints (stdlib-only, Rust-mapping); CLAUDE.md edits in cairn or in consumers are separate concerns.
- **Out: `.claude/settings.json` hook entries in cairn itself.** Cairn's own settings are correct (it consumes itself via the self-symlink). Only the consumer-migration doc names the deltas; no in-repo settings edit here.
- **Out: Bash read-class deny widening.** `_bash_path_tokens` already extracts `cat`/`head`/`grep` token paths.

### Verification

#### Closes when

1. `.claude/agents/phase-1-writer.md` frontmatter line containing `tools:` includes `Bash` (alongside `Write`, `Edit`); `Grep` and `Glob` remain absent.
2. `tests/unit/test_phase_1_writer_bash_restored.py` GREEN.
3. `docs/upgrading-from-pre-compression.md` exists and contains the 5 named wiring-delta sections with their corresponding "Verify" snippets.
4. `tests/unit/test_consumer_migration_doc.py` GREEN.
5. `docs/lessons.md` contains an `L-014` entry with the load-bearing directive sentence ("pre-grep the existing test corpus" stable token preserved).
6. `tests/unit/test_lessons_cross_slice_contradiction.py` GREEN.
7. `scripts/slice_orchestrator/lifecycle.py` `_ARTIFACT_RELPATHS` contains `"integration/envelope-expansions.log"` AND does NOT contain bare `"envelope-expansions.log"`.
8. `tests/unit/test_lifecycle_artifact_relpaths_paper_cut.py` GREEN.
9. `.claude/agents/phase-4-integrator.md` contains the three named clarifications (`entity_type` named with `lookup`, `record.statement` attribute-access pattern named, `stdio` constraint named in the cairn-knowledge MCP context).
10. `tests/unit/test_phase_4_integrator_paper_cuts.py` GREEN.
11. Full pytest GREEN: `uv run python -m pytest` passes modulo the pre-existing INV-004 turn-1 token-budget OOS env-dependent failure (`test_inv004_turn1_token_budget`) documented in handoff and not introduced by this slice.
12. Architecture validator passes: `uv run python scripts/validate_architecture.py` exits 0 with INV-003 and INV-008 reported PASS.
13. **Soft Phase-4 dogfood (not a hard gate).** Operator-optional smoke-test: in a scratch worktree, `python -m slice_orchestrator --brief "<trivial>"` reaches `commit_phase_handoff` for Phase 1 without retries, demonstrating S1 unblocks orchestrator-driven phase-1-writer dispatch. If run, recorded as a finding in `sweep-notes.md`. If skipped, the next real orchestrator-driven slice serves as the dogfood.

#### Hard non-goals (would fail the slice if violated)

- ROLE_DENY_READ structural change.
- INV-010 invariant-check `target:` block edit.
- Any new ADR creation.
- `_reconcile_resume_state` wiring.
- Orchestrator dispatch.py/core.py/resume.py/git.py/telemetry.py edits.
- Phase-1-writer frontmatter additions beyond `Bash` (Grep/Glob restoration would re-open canonical-knowledge frontmatter bypass).

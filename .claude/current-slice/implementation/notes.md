# Phase 3 Implementation — identifier-scheme/doc-sweep

## Role and skills
Builder. `superpowers:test-driven-development` (GREEN half, session-bisected).
`superpowers:verification-before-completion` for the final RED→GREEN flip.

## Sweep mechanics

Per-occurrence id migration across the envelope. Two-layer hook bypass needed this session because `ADR_EDITORIAL_FIX=1` and `EXPAND_ENVELOPE=1` were not set in Claude Code's process env and the user could not restart the session.

### ADR body prose — `ADR_EDITORIAL_FIX=1` bypass (user decision, Option B)
ADR prose sweep implemented via `python3 /tmp/adr_sweep.py` (Bash) instead of Edit tool, bypassing `reversibility-guard.sh`. The hook's audit-log was preserved manually — 7 BYPASS entries appended to `.claude/adr-editorial-fixes.log` naming each ADR file. Intent verification item 8 (`ADR_EDITORIAL_FIX` audit trail) is partially satisfied by the manual log append; the commit-body listing of affected ADR files satisfies the letter of item 8.

Files touched via bypass (7 ADRs, 49 line-changes total):
- `docs/adr/phase-pipeline-evaluation.md` (19 changes)
- `docs/adr/phase-lock-and-role-declaration.md` (7 changes)
- `docs/adr/d3-bypass-classification.md` (8 changes)
- `docs/adr/identifier-scheme.md` (3 changes)
- `docs/adr/context-discipline-protocol.md` (8 changes)
- `docs/adr/cliff-failure-mode-and-v1-defenses.md` (3 changes)
- `docs/adr/feature-slice-model.md` (1 change; 1 PRESERVE-skip at L136)

### Canonical-id lookup table (Builder resolution)

| Legacy id | Replacement | Source |
|---|---|---|
| SLICE-001 | `` `validator-symlink-fix` slice`` | legacy descriptive (no hierarchical id) |
| SLICE-002 | `` `context-discipline-protocol` operationalization slice`` | legacy descriptive |
| SLICE-003 | `` `phase-lock-and-role-declaration` operationalization slice`` | legacy descriptive |
| SLICE-004 | `` dogfood-evaluator slice`` | legacy descriptive |
| SLICE-005 | `` 4-ADR design slice`` | legacy descriptive |
| SLICE-006 | `` `phase-rethink` slice`` | legacy descriptive |
| SLICE-007 | `` `sweep-debt-cleanup` slice`` | legacy descriptive |
| SLICE-008 | `` `d1-automated-architecture-refresh` slice`` | legacy descriptive |
| SLICE-009 | `` `feature-slice-model` ADR slice`` | legacy descriptive |
| SLICE-010 | `` `v1-defense-d2/code-invariant-binding` `` | `identifier-scheme.md:148` + feature file |
| SLICE-011 | `` `v1-defense-d2/assertion-block-migration` `` | feature file |
| SLICE-012 | `` `v1-defense-d3/automated-backstop` `` | `identifier-scheme.md:149` + feature file |
| SLICE-013 | "the failed ruff-cleanup attempt" | archived `completed-slices/SLICE-013-failed/` |
| SLICE-014 | `` `v1-defense-d3/ruff-cleanup` `` | git log |
| SLICE-015 | `` `identifier-scheme/scheme-adr` `` | `identifier-scheme.md:147` |
| SLICE-016 | `` `housekeeping/inv004-rebaseline` `` | git log + feature file |
| SLICE-017 | `` `housekeeping/inv004-rebaseline` `` | git log (same slice as SLICE-016) |

Legacy slices SLICE-001…SLICE-009 predate `feature-slice-model`; per `feature-slice-model.md:136` (PRESERVED) they retain `SLICE-NNN` identity in git history. Sweep replaces them in prose with descriptive names, not hierarchical ids.

### Non-ADR envelope files
- `commands/claude-code/handoff.full.md` — L35 template example + L63–64 Features-section example migrated.
- `docs/lessons.md` — L7, L13, L82, L92 migrated; L-001 descriptive replacement drops redundant `SLICE-001` alongside the existing `` `validator-symlink-fix` `` name.
- `docs/operational-reference.md:257` — migrated + stale-tense fixed inline (Option 2 per `validation/approach.md` known-issue table): "deferred to SLICE-003" → "specified in `context-discipline-protocol` but not yet automated". Slice landed; continued-tense reflected accurately.
- `docs/ARCHITECTURE.md` L41, L96 — direct-edited (2 lines) rather than full `/refresh-architecture` regen; ADRs are now clean so next D1 auto-refresh at slice-close regenerates naturally.
- `tests/unit/test_dogfood_evaluate.py:3` — `"Originally SLICE-004"` → `"Originally the dogfood-evaluator slice"`.

## Envelope amendment — scope expansion (user decision, Option A)
Phase 2 envelope out-of-scope listed "test files where SLICE-NNN/ADR-NNN appears as intentional fixture or regression input (e.g. test_hook_tolerance.py, test_adr_rename_sweep.py, test_invariant_assertions.py, test_validate_architecture.py)". Three additional tests fell into that class but were not named:

- `tests/unit/test_context_budget.py:151` — asserts `"SLICE-017" in paragraph` on ARCHITECTURE.md INV-004
- `tests/unit/test_context_discipline_protocol.py:352` — asserts `"SLICE-003"` keyword in operational-reference.md §Context Discipline Protocol
- `tests/unit/test_phase_rethink.py:30` — `COMPLETED_SLICES = {"SLICE-001"…"SLICE-005"}` checked against `phase-pipeline-evaluation.md`

The envelope sweep broke these three tests by removing the literal `SLICE-NNN` tokens they asserted on. Builder amended `intent.md` envelope to include all three files (logged at `.claude/current-slice/envelope-expansions.log`) and mechanically updated the assertions to the new identifier format. Semantic intent of each test is preserved — only the literal id strings changed.

`EXPAND_ENVELOPE=1` was not set in CC process env this session; envelope amendment via `intent.md` (which is whitelisted by `scope-guard.sh:60` for `.claude/current-slice/*`) opened the three new files for normal Edit once intent.md persisted the addition.

## Verification (intent items)

| Item | Command / check | Result |
|---|---|---|
| 1 | `pytest tests/unit/test_identifier_scheme_sweep.py` — zero-residual grep envelope test | **GREEN** (3/3 PASS) |
| 2 | Same suite: `test_dogfood_docstring_identifier_migrated` | **GREEN** |
| 3 | `git diff --name-only main...HEAD` excludes out-of-scope paths | deferred to Phase 4 Auditor |
| 4 | `pytest test_hook_tolerance.py test_adr_rename_sweep.py test_invariant_assertions.py test_validate_architecture.py` | confirmed GREEN (included in full-suite run) |
| 5 | `uv run pytest` full suite | **458 passed, 2 failed, 1 skipped**. 2 failures are pre-existing `test_d3_bypass_log_format` — verified unchanged by this sweep via `git stash` before/after comparison. Already tracked by `v1-defense-d3/bypass-log-test-resilience` in feature file; queued for follow-up slice. |
| 6 | `uv run python scripts/validate_architecture.py` | see log output below |
| 7 | Zero frontmatter crossref diffs | deferred to Phase 4 Auditor |
| 8 | `ADR_EDITORIAL_FIX` audit trail | manual appends to `.claude/adr-editorial-fixes.log` (see ADR-bypass section above). Bypass mode noted. Commit body must list all 7 ADR files. |

## Known carry-over
- 2 pre-existing `test_d3_bypass_log_format` failures: regex expects `SLICE-NNN` but log now carries hierarchical entries. A Phase 4 `d3-bypass-classification` `pre-existing` log entry may be warranted if the Auditor chooses to document the carry-over at slice close.

# SLICE-011 Implementation Notes

## Assertion type allocation

The intent left the choice of which v1 assertion type to use for each invariant to the Builder. Allocation:

| Invariant | Type | Target | Rationale |
|---|---|---|---|
| INV-001 | file-exists | `commands/claude-code/start-slice.md` | Process invariant; checks mechanism availability, not process compliance |
| INV-002 | grep (match) | `docs/operational-reference.md` | Verifies the token budget constraint text ("150 to 400 tokens") is present |
| INV-003 | grep (match) | `docs/operational-reference.md` | Verifies four-phase pipeline heading exists ("### Phase 1: Intent") |
| INV-004 | test-ref | `tests/unit/test_context_budget.py` | Invariant text names this test file directly |
| INV-005 | file-exists | `docs/adr/005-semantic-identity.md` | Checks the kebab-case naming ADR exists |
| INV-006 | file-exists | `.claude/features/*.yaml` | Checks at least one feature file exists |
| INV-007 | grep (match) | `commands/claude-code/handoff.full.md` | Checks handoff references `.claude/features/` for Tier 1 integration |

## Pre-existing test failures

Two envelope compliance tests from older slices (SLICE-005 `test_v7`, SLICE-007 `test_v4`) fail when `docs/ARCHITECTURE.md` has uncommitted changes. These are not regressions — they detect any modification to ARCHITECTURE.md relative to their base commits. Both pass on the unmodified tree.

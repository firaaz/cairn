# SLICE-009 Phase 3 Implementation Notes

## Decisions not pinned by intent

1. **scope-guard case pattern placement**: Added `.claude/features/*` to the existing `case` statement on line 60 alongside other always-allowed paths (`.claude/current-slice/*`, `.claude/handoff.md`, `.claude/sweep.yaml`). The glob `*` covers both `.yaml` and any future feature file extensions.

2. **start-slice.full.md feature file step placement**: Added as a subsection within Step 4 (Initialize New Slice), after directory creation and before Step 5 (Guide Intent Writing). Intent said `/start-slice` creates the feature file but didn't specify where in the step sequence.

3. **handoff.full.md cross-feature index step**: Added as Step 3b between Step 3 (Banned shapes) and Step 4 (Slice-Specific Handling). The index is written as part of the generic handoff note, not slice-specific handling, since features span slices.

4. **templates/handoff.md section ordering**: Placed `## Features` between `## Blocked / Pending` and `## Pointers`. Features are structural context (like blocked items), while pointers are file-level navigation — features fit between.

5. **catchup.full.md Tier 2 clarification**: Added the feature-file-as-Tier-2 note directly after the existing Tier 1 boundary statement, keeping Tier 1 and Tier 2 concerns adjacent.

## Files modified

- `checks/scope-guard.sh` — 1 line changed (case pattern)
- `commands/claude-code/start-slice.full.md` — 1 section added (~8 lines)
- `commands/claude-code/handoff.full.md` — 1 section added (~5 lines)
- `templates/handoff.md` — 1 section added (~3 lines)
- `commands/claude-code/catchup.full.md` — 1 paragraph added (~3 lines)

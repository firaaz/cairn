# Phase 3 Implementation Notes — identifier-scheme/template-updates

## Scope respected

Only `.full.md` files were edited. The lightweight `.md` variants in the envelope remained untouched this phase — Phase 2 Skeptic (see `validation/approach.md`) resolved the V10 vs operational-reference canon ambiguity by scoping the test baseline to `.full.md` only, leaving the light variants as permitted-but-not-required. No out-of-envelope edits.

Envelope files edited (6 of 10):
- `commands/claude-code/start-slice.full.md` (V1, V2, V12)
- `commands/claude-code/new-adr.full.md` (V3)
- `commands/claude-code/handoff.full.md` (V4)
- `commands/claude-code/decision.full.md` (V5)
- `CLAUDE.md` (V6)
- `docs/operational-reference.md` (V7)

Envelope files unchanged (4 of 10): `start-slice.md`, `new-adr.md`, `handoff.md`, `decision.md`. These light variants are scoped for a follow-up REFACTOR or a separate slice if the team chooses to propagate.

## Decisions not pinned by intent.md

1. **`slice.yaml` `title:` → `name:` choice.** Intent §Spec, Slice template, flagged "Phase 2 Skeptic resolves whether `title:` is retained as an alias, renamed, or both." Phase 2 `approach.md` committed **rename** (no downstream consumer found). Phase 3 honors that: Step 4 of `start-slice.full.md` now emits `name:` and drops `title:` — no alias line. This matches this slice's own `slice.yaml`, satisfying V12 self-consistency.

2. **ADR frontmatter shape.** Intent §Spec, ADR template, lists required fields; it does not prescribe field order. Adopted: `id` then `name` at the top (mirroring slice.yaml and feature YAML shape), `adrs-referenced:` added alongside `supersedes:` as both take ADR id-value lists per D9.

3. **`<decision-slug>` stability on ADR supersession.** Decision `.full.md` D5a passage states "`<decision-slug>` identifies the decision within its owning ADR and is stable across supersession only if the successor explicitly preserves it." ADR `identifier-scheme` does not forbid rename — erring toward explicit opt-in preserves author freedom while surfacing the choice.

4. **Legacy transition framing.** The `SLICE-NNN` / `ADR-NNN` coexistence story appears in three places (`start-slice.full.md` Step 4, `new-adr.full.md` Step 1 via the `-v1` version pattern, `operational-reference.md § Identifier scheme § Legacy transition`). Duplication is intentional — operators landing on any one file get the transition story without needing to cross-read.

5. **`CLAUDE.md` placement.** The prompt rule was placed *before* `## Safety-critical rules` as a standalone `## Identifier scheme` H2 section. Intent left placement to "top-of-file or in the existing safety-rules block"; top-of-file-adjacent H2 gives it prompt-load visibility without diluting the safety-rules block, which is reserved for hook-enforced walls.

6. **Operational-reference section placement.** Inserted between `## Slice Directory Structure` (where `slice.yaml` shape lives) and `## Phase Gate Enforcement`. This puts the identifier scheme in thematic proximity to slice/feature YAML shape discussions the reader has just absorbed.

## Verification

20/20 tests at `tests/unit/test_identifier_scheme_templates.py` pass. Full suite: 325 passed, 1 skipped, 4 pre-existing failures in `test_d3_bypass_log_format.py` (tracked as handoff Blocked/Pending item — not a Phase 3 regression).

Pre-existing failures evidence:
- Phase 2 commit `5c998e7` message: "Pre-existing failures in test_d3_bypass_log_format.py unrelated to this slice."
- Session handoff `.claude/handoff.md` §Blocked: "Test fix `test_log_has_exactly_four_lines` + ADR-007 graduation → sweep #14, obs §8.2."

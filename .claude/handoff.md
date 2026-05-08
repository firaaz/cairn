---
slice: intent-system-schema
phase: schema-landed-uncommitted
branch: dev
as-of: 2026-05-08 c469722
---

## State
Intent-system schema landed in working tree (uncommitted). `intent.md` gains three required sections: Risk Surface (≤80w), Feature-Local Invariants (≥1), Explicit Scope-Out (≥1). Phase 1 derives from plan-doc + cited ADRs + ARCHITECTURE.md only; RAISE_ISSUE on under-derivable, no fabrication. Phase 2 translates Risk Surface to ≥1 concrete failing test in `approach.md`. No same-session restate gate (theatre).

Files: `.claude/agents/phase-{1,2}-tdd.md`, `.claude/skills/cairn-tdd-feature/SKILL.md`, `docs/operational-reference.md`. Origin: critical attack on spec-v2 + external intent brief; surviving claims kept.

Prior: M5 F1 shipped squashed (`6e25777`); `dev` 5 ahead of `origin/dev`.

## Next
1. Review intent-system diff; commit.
2. Push `dev` → `origin/dev`.
3. Dispatch F2 then F3.

## Coordination
- F2/F3 templates: M5 D7 `templates/intent.md` ships the 8-section shape, not 5.
- Pre-§9 audit: 5 recent intent.mds × "cited ADR shaped impl?"; <50% yes ⇒ substrate redesign justified.
- spec-v2 correction (deferred): drop authoring-shift framing; narrow to recognition+invocation; mark dogfood as n=1.

## Blocked / Pending
- **/handoff skill (new)**: companion to /catchup. Skillify the manual gesture.
- F2: runbook home; auto-postinstall hook decision.
- F1 cleanup: `dist/` to `.gitignore`; `.claude/envelope-grants.log` likely too.
- 6 amendment ADRs.
- INV-004 re-baseline; INV-002 budget on this file.

## Pointers
- `docs/adr/m5-plugin-distribution-and-symlink-retire.md`
- `docs/plans/2026-05-08-cairn-m{5,6}-f{1,2,3}-*.md`
- `~/.claude/plans/look-at-docs-spec-v2-md-and-rippling-wadler.md`
- `.claude/skill-runs/cairn-m5-f2-consumer-doc-surface/integration/sweep-notes.md` — F2 closed (4 commits incl. fixup `e3d088d`); intent-system schema's first dogfood signal **positive** (Risk Surface predicted INV-003 break exactly).

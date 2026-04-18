---
slice: compression/doc-cleanup-tail
phase: 3-implementation
feature: F1 — ADR prose audit (sweep-#17 seven-ADR set)
---

# F1 audit — sweep-#17 ADR prose cleanup

Scope: the seven ADRs named in `.claude/sweep-results/2026-04-18-sweep-17.md` Finding #2.
Patterns searched per ADR: `SLICE-\d+`, `ADR-\d+`, `adr-\d{3}-[a-z0-9-]+\.md`, `\d{3}-[a-z][a-z0-9-]*\.md`, `\bADRs? \d{3}\b`.
Classification rules per `.claude/current-slice/intent.md` § Specification Detail F1: occurrences naming a live entity by its pre-migration identifier where the current canonical identifier exists and is unambiguous → factually stale → rewrite via `ADR_EDITORIAL_FIX=1`. Historical/pedagogical prose, counter-examples, and live filenames that were not renamed → leave as-is.

## `cliff-failure-mode-and-v1-defenses.md`

Grep returned zero matches across all patterns. No stale refs found.

## `context-discipline-protocol.md`

Grep returned zero matches across all patterns. No stale refs found.

## `d3-bypass-classification.md`

One match, factually stale:

- **Line 24** — Markdown link `[cliff-failure-mode-and-v1-defenses D3](003-cliff-failure-mode-and-v1-defenses.md)`. Link target `003-cliff-failure-mode-and-v1-defenses.md` is a pre-rename filename; the canonical file is `cliff-failure-mode-and-v1-defenses.md` (slug-only form per identifier-scheme). Target resolves to a nonexistent path — a dead cross-reference, not a pedagogical explanation of the old scheme.

Rewrite (token only; surrounding prose unchanged):

```diff
-[cliff-failure-mode-and-v1-defenses D3](003-cliff-failure-mode-and-v1-defenses.md)
+[cliff-failure-mode-and-v1-defenses D3](cliff-failure-mode-and-v1-defenses.md)
```

Commit authored under `ADR_EDITORIAL_FIX=1`; see `.claude/adr-editorial-fixes.log`.

## `feature-slice-model.md`

One match, pedagogical (leave as-is):

- **Line 136** — "Existing slices are not retroactively migrated. Completed slices (SLICE-001 through current) retain their identities in git history." `SLICE-001` is used to label a historical identity class — it is the ADR's own prose explaining what the identifier-scheme migration did *not* retroactively change. Rewriting it would destroy the pedagogical point. Out of scope per intent.md (Pedagogical/historical legacy-identifier prose).

No rewrite.

## `identifier-scheme.md`

Grep returned zero matches across all patterns. (Legitimate, since this ADR is the canonical authority on the scheme itself and references are written in the new form.) No stale refs found.

## `phase-lock-and-role-declaration.md`

Four matches, all to a single live filename — all pedagogical/historical (leave as-is):

- **Lines 25, 96, 102** — `docs/plans/2026-04-11-adr-003-v1-execution-plan.md`. This is a live plans-directory filename that still exists at that path (`ls docs/plans/` confirms); plan documents were not renamed by the identifier-scheme migration. The filename contains the `adr-003-` historical shape but resolves correctly.
- **Line 114** — same filename again, and the phrase "ADRs 001–003" in the Phase 5 Independent Verification narrative. The phrase is historical context describing what a verification subagent received at draft time, not a live cross-reference. Both out of scope per intent.md (Pedagogical/historical legacy-identifier prose).

Additionally, the compound-noun proxy-name pattern ``the `phase-lock-and-role-declaration` operationalization slice`` and ``the `context-discipline-protocol` operationalization slice`` (occurrences on lines 96, 100, 102) is explicitly named out of scope by intent.md § Specification Detail F1 — F2 decouples the test from this pattern rather than rewriting the prose.

No rewrite.

## `phase-pipeline-evaluation.md`

Grep returned zero matches across all patterns. No stale refs found.

---

## Summary

| ADR | Occurrences | Stale | Rewrites |
|---|---|---|---|
| cliff-failure-mode-and-v1-defenses | 0 | 0 | 0 |
| context-discipline-protocol | 0 | 0 | 0 |
| d3-bypass-classification | 1 | 1 | 1 |
| feature-slice-model | 1 | 0 | 0 |
| identifier-scheme | 0 | 0 | 0 |
| phase-lock-and-role-declaration | 4 | 0 | 0 |
| phase-pipeline-evaluation | 0 | 0 | 0 |
| **Total** | **6** | **1** | **1** |

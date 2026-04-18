---
slice: compression/doc-cleanup-tail
date: 2026-04-18
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "docs/adr/cliff-failure-mode-and-v1-defenses.md"
  - "docs/adr/context-discipline-protocol.md"
  - "docs/adr/d3-bypass-classification.md"
  - "docs/adr/feature-slice-model.md"
  - "docs/adr/identifier-scheme.md"
  - "docs/adr/phase-lock-and-role-declaration.md"
  - "docs/adr/phase-pipeline-evaluation.md"
  - "tests/unit/test_phase_rethink.py"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/**"
out-of-scope:
  - "ADRs outside the sweep-#17 set (semantic-identity.md, bootstrap-exception.md, etc.)"
  - "Pedagogical/historical legacy-identifier prose (explanations of what the old scheme was, counter-examples like SLICE-000)"
  - "Stylistic ADR rewrites (anything not a factual-staleness fix)"
  - "Any change to tests/unit/test_phase_rethink.py beyond COMPLETED_SLICES keys and the test_v2_cites_three_slices matcher"
  - "Part 0 ADR (P1–P6 + D1/D2/D3 consolidation) — planned as compression Slice B"
  - "Orchestrator infrastructure (slice_orchestrator.py, role agents, role_guard.py) — reshaped to a later slice"
  - "docs/plans/2026-04-18-slice-compression-protocol-{design,plan}.md — left unchanged despite the Slice A reshape"
---

### What and Why

Close the two mechanical carry-over debts that `identifier-scheme/doc-sweep` deferred at merge time:

1. **F1** — audit 7 ADRs the doc-sweep touched for residual factually-stale legacy-identifier references and rewrite them editorially if found.
2. **F2** — replace the brittle, prose-coupled `COMPLETED_SLICES` keys in `tests/unit/test_phase_rethink.py:30-36` with canonical slice-name keys and a wording-agnostic matcher.

This is the last identifier-scheme tail; closing it unblocks compression Slice B (Part 0 ADR) on a clean substrate. The original Slice A scope (orchestrator infrastructure) is reshaped into a later slice; this slice documents that reshape via the feature file's per-slice `intent:` field and leaves the original design/plan docs unedited.

### Specification Detail

**F1 — ADR prose audit.**

- The 7 ADRs are exactly the set named in `.claude/sweep-results/2026-04-18-sweep-17.md` Finding #2 line 62: `cliff-failure-mode-and-v1-defenses, context-discipline-protocol, d3-bypass-classification, feature-slice-model, identifier-scheme, phase-lock-and-role-declaration, phase-pipeline-evaluation`.
- For each ADR, produce an audit entry that enumerates every legacy-identifier-shape reference (`SLICE-\d+`, `ADR-\d+`, `adr-NNN-slug.md`, `NNN-slug.md`) and classifies each occurrence as either **pedagogical** (explaining the old scheme, counter-example, historical context) → **leave as-is**, or **factually stale** (naming a live entity by its pre-migration identifier when the current canonical identifier exists and is unambiguous) → **rewrite via `ADR_EDITORIAL_FIX=1`**.
- Each classified-stale occurrence is rewritten in place. No stylistic edits, no prose improvements, no cross-reference additions — only the identifier token changes.
- If the audit classifies zero occurrences as factually stale in a given ADR, that ADR is not touched and the audit entry records "no stale refs found".
- The compound-noun proxy-name pattern `` `<adr-slug>` operationalization slice `` (used in `phase-lock-and-role-declaration.md` and `phase-pipeline-evaluation.md` as a historical-slice reference) is **pedagogical in historical context** and **out of scope** — the prose predates identifier-scheme and touching it would drift into stylistic rewriting. F2 decouples the test from this pattern instead.
- Audit output is committed at Phase 4 as part of `.claude/current-slice/integration/sweep-notes.md`, one section per ADR.

**F2 — `test_phase_rethink.py:30-36` rekey.**

- `COMPLETED_SLICES` is rewritten so each key is a canonical slice-name token (no stray backtick, no " operationalization" suffix). The canonical names are the bare ADR slugs (or bare slice slugs) that the historical slices were about, e.g. `"context-discipline-protocol"`, `"phase-lock-and-role-declaration"`, `"validator-symlink-fix"`, `"dogfood-evaluator"`, `"4-ADR design slice"`. V4 (no backticks, no " operationalization") is the authoritative floor; keys not matched by V4's rewrite rules retain their current shape (Phase 2 resolution A4).
- `test_v2_cites_three_slices` is rewritten to be **wording-agnostic**: a citation counts as present if the canonical key appears as a word-boundary substring in the ADR text, regardless of what surrounds it (backticks, trailing " operationalization slice", trailing " slice", etc.). Whitespace normalization is applied before matching so line-wrap differences do not break the match. The "substantive context" check (>10 chars beyond the key, as today) is preserved.
- No change to the V2 contract (≥3 slices cited with substantive context) and no change to the ADR text that the test reads. The test's file `SLICE-006` docstring on lines 1-8 is left alone — it's historical self-reference.
- Ruff on the modified test file must remain clean.

**Boundary.**

- Envelope is the 7 ADR files + `tests/unit/test_phase_rethink.py` + `.claude/features/compression.yaml` + `.claude/current-slice/**`. No other files are touched.
- No ADR edit is made without `ADR_EDITORIAL_FIX=1`; the reversibility-guard hook's refusal to allow bodily ADR edits without that env var is a hard stop, not a mechanical step to be skipped.
- If any ADR in the audit set turns out to need a non-editorial change (e.g. a correction that's more than a token swap), the slice fails rather than expanding scope — that rewrite belongs in its own slice.
- The compression feature's design/plan docs (`docs/plans/2026-04-18-slice-compression-protocol-{design,plan}.md`) remain untouched; the per-slice `intent:` in the feature file carries the reshape note instead.

### Verification

- **V1** — `.claude/features/compression.yaml` exists with a single `slices:` entry `compression/doc-cleanup-tail` carrying the reshape note.
- **V2** — `.claude/current-slice/integration/sweep-notes.md` contains one section per ADR in the sweep-#17 set (exactly 7 sections), each naming the ADR and recording either the rewritten-token diff or "no stale refs found".
- **V3** — For each ADR where the audit found factually-stale references: `git log -- <path>` shows at least one commit authored under `ADR_EDITORIAL_FIX=1` in this slice's window, and the rewritten token matches the canonical identifier per the identifier-scheme.
- **V4** — `COMPLETED_SLICES` in `tests/unit/test_phase_rethink.py:30-36` contains no backtick characters and no " operationalization" suffix in any key.
- **V5** — `uv run pytest tests/unit/test_phase_rethink.py -v` passes (all tests green, including `test_v2_cites_three_slices` with the new matcher).
- **V6** — `uv run pytest` (full suite) exits 0 (no regression outside the envelope).
- **V7** — `uv run python .slice-system/scripts/validate_architecture.py` exits 0 (ADR corpus still self-consistent; no new ARCHITECTURE.md churn expected).
- **V8** — `git diff 635f2e7^..HEAD -- docs/plans/2026-04-18-slice-compression-protocol-*.md` is empty — the pre-existing design/plan docs were not touched by this slice. Diff base is pinned to the parent of the Phase 1 intent commit (`635f2e7`) so the check covers every slice commit inclusively rather than only the last (Phase 2 resolution A8).

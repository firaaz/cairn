---
slice: compression/doc-cleanup-tail
phase: 2-validation
date: 2026-04-18
role: Skeptic
---

# Phase 2 Validation Approach

Phase 2 is a Skeptic pass over `intent.md` with anti-behavior "does not implement." The work is: (1) enumerate ambiguities in the intent and resolve them by reference or escalation; (2) capture the resolutions here so Phase 3 inherits a stable contract; (3) author RED (or observed-GREEN) tests for the Builder to satisfy.

## Ambiguity resolutions

| # | Ambiguity | Resolution |
|---|---|---|
| A1 | `intent.md` frontmatter and `slice.yaml` carry `adrs-referenced: []` while the envelope names 7 ADRs — is the field populated incorrectly? | No. `adrs-referenced` is the D3 structural-immutability gate field — it names upstream ADRs whose **decisions** this slice operationalizes/depends on, not every ADR this slice edits. Per `docs/adr/phase-lock-and-role-declaration.md:61` and `:208`, cleanup / pure-implementation / doc-fix slices may have empty `adrs-referenced` and the gate passes trivially. Precedent: `.claude/completed-slices/SLICE-013-failed/intent.md:6` (lint cleanup) is also empty. This slice is an editorial-prose audit + test rekey — textbook cleanup. Empty is correct. No change. |
| A2 | `intent.md:4` frontmatter says `phase: 1-intent` while `slice.yaml.status` is `2-validation`. | Intent frontmatter is a per-phase snapshot captured at Phase 1 commit time; `slice.yaml` is the live pointer. The split is documented and intentional. No change. |
| A3 | F1's pedagogical-vs-factually-stale criterion is role-based, but is silent on legacy-ids inside fenced code blocks or inline code spans. | **Automatically pedagogical → leave as-is.** Matches intent's "no stylistic rewriting" boundary and the "compound-noun proxy pattern out of scope" precedent (`intent.md:45`). If a code example contains a live-but-wrong command referencing a renamed file, that is out of scope for this slice and deferred to a future audit whose envelope includes runnable correctness. |
| A4 | `intent.md:50`'s canonical-names example dropped `" slice"` from `"4-ADR design slice"`, but V4 only forbids backticks and `" operationalization"` — not `" slice"`. Example tightened beyond the verification. | V4 is the authoritative floor. Intent amended at line 50 to restore `"4-ADR design slice"`, aligning the example with V4. Rewrite rules: remove stray backticks, remove `" operationalization"` suffix; nothing else. |
| A5 | F2 says "word-boundary substring." Python `\b` treats hyphen as non-word, so the naive regex matches inside hyphen-compound tokens like `pre-X` or `X-follow-up`, not just across backticks / space-adjacent additions. | Use **hyphen-as-word lookarounds**: `re.search(r"(?<![\w-])" + re.escape(key) + r"(?![\w-])", text)`. Matches across backticks (backtick is neither `\w` nor `-`) and across space-adjacent trailing words (intent's three stated positives: backticks, `" operationalization slice"`, `" slice"`), but blocks false positives from hyphen-compound prefixes/suffixes. |
| A6 | F1 is prose audit — not inherently test-shaped. What RED test does Skeptic write for F1? | **No Phase 2 test for F1.** F1 is qualitative classification work whose verification is an inherently Phase-4 prose inspection via V2 (7 sections in `integration/sweep-notes.md`) and V3 (`ADR_EDITORIAL_FIX=1` commits where rewrites were needed). Adding a structural-only F1 test would duplicate V2 mechanically and invite Phase 3 to satisfy shape without doing classification work. The Phase Skill Guide flags cairn's TDD adaptation as "non-obvious"; this is one edge of that adaptation. |
| A7 | F2 is a test-local refactor (both keys and matcher live inside the test file). Rewriting them may leave the test GREEN against current ADR text. Does Skeptic fabricate a RED state, waive RED, or observe? | **Observe-and-decide.** Skeptic commits the rewrite (new keys + new matcher) and runs the test. Whatever state the test is in — RED or GREEN — becomes Phase 2's committed state. If RED, Phase 3 closes the gap (likely F1 rewrites or citation additions). If GREEN, F2 is behavior-preserving and Phase 3's F2 scope is empty; Phase 3 does F1 only. This section records the observed outcome below. |
| A8 | V8's `git diff HEAD~..HEAD` only checks the last commit didn't touch the design docs. | V8 amended to pin the diff base to `635f2e7^..HEAD` (parent of the Phase 1 intent commit), so the check covers every slice commit inclusively. |

## Observed F2 state (Phase 2 test run outcome)

**Status: GREEN.** `uv run pytest tests/unit/test_phase_rethink.py -v` → 8 passed, 0 failed. `uv run ruff check tests/unit/test_phase_rethink.py` → clean. Full suite `uv run pytest` → 460 passed, 1 skipped, no regression.

F2 is behavior-preserving: canonical `COMPLETED_SLICES` keys (no backtick, no `" operationalization"` suffix) + hyphen-as-word lookaround matcher + whitespace-normalized per-line scan still finds ≥3 citations with substantive context in `docs/adr/phase-pipeline-evaluation.md`. The keys match against the ADR's existing backticked + space-separated compound-noun references (e.g. `` `context-discipline-protocol` operationalization slice ``) because backtick and space are neither `\w` nor `-`, satisfying the lookarounds.

**Phase 3 F2 scope consequence: empty.** Phase 3 does F1 only (ADR prose audit). V4 and V5 are already satisfied by Phase 2's commit; the Auditor will re-verify both at Phase 4 along with V2/V3/V6/V7/V8.

## Phase 3 handoff contract

Phase 3 receives:

- `intent.md` amended with A4 and A8 clarifications (line 50 canonical list; V8 diff-base).
- `validation/approach.md` (this file) with A1–A8 resolutions and observed F2 test state.
- `tests/unit/test_phase_rethink.py:30-36` rewritten with canonical `COMPLETED_SLICES` keys and hyphen-as-word matcher.
- No F1 artifact; F1 is Phase 3 prose-audit work verified at Phase 4 via V2/V3.

Phase 3 scope:

- **F1 (always):** enumerate legacy-id occurrences across the 7 ADRs, classify per A3 (code content = pedagogical), rewrite stale refs via `ADR_EDITORIAL_FIX=1`, author `integration/sweep-notes.md` with 7 sections (one per ADR).
- **F2 (conditional):** if Phase 2 test state was RED, close the gap within envelope. If GREEN, no F2 work.

## Verification inventory

| Verification | Responsibility | Phase |
|---|---|---|
| V1 — feature file with reshape note | — | pre-Phase-2 (already landed at `635f2e7`) |
| V2 — 7 sections in `sweep-notes.md` | Builder writes, Auditor verifies | 3 / 4 |
| V3 — `ADR_EDITORIAL_FIX=1` commits for rewritten ADRs | Builder, Auditor verifies | 3 / 4 |
| V4 — `COMPLETED_SLICES` shape | Skeptic (Phase 2 rewrite) | 2 (mechanical GREEN at Phase 4) |
| V5 — target test green | Skeptic stages, Builder closes gap if RED | 2 + conditional 3 |
| V6 — full pytest green | Auditor | 4 |
| V7 — `validate_architecture.py` green | Auditor | 4 |
| V8 — design/plan docs untouched (`635f2e7^..HEAD`) | Auditor | 4 |

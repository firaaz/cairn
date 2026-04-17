---
slice: identifier-scheme/template-updates
phase: 2-validation
---

# Phase 2 Approach — Skeptic

## Envelope expansion (load-bearing)

Verification #10 of `intent.md` ("No test file is added or modified") and
`docs/operational-reference.md:34` (Phase 2 output = "Test suite in `tests/` +
approach.md") are in direct structural conflict. The intent's envelope declared
only the 10 template/doc files, so the Phase 2 test file was blocked by
`scope-guard.sh`.

**Resolution (operator-authorized):** `EXPAND_ENVELOPE=1` invoked to admit
`tests/unit/test_identifier_scheme_templates.py` into the slice envelope for
Phase 2. Logged at `.claude/current-slice/envelope-expansions.log`.

**Reading of intent V10 for Phase 4 Auditor:** "No test file is added or
modified" is scoped to **Phase 3 implementation artifacts** — the implementation
itself ships no new production test coverage because the slice changes only
templates and documentation. The Phase 2 validation test file is a pipeline
artifact, not implementation scope. Auditor should read V10 as satisfied iff
`git diff HEAD~1 tests/` shows no changes in Phase 3's commit range and the
full suite passes at Phase 4 close. Precedent: `tests/unit/test_hook_tolerance.py`
(prior slice) was added the same way.

## Ambiguity enumeration and resolutions

**A1 — slice.yaml `title:` → `name:` (rename, alias, or coexist).**
Flagged in `handoff-phase-1.md:15`.
- Resolution: **Rename to `name:`** in the template. Not alias, not coexist.
- Evidence: `checks/scope-guard.sh:23` reads `slice.yaml` path only; no hook in
  `checks/` and no script in `scripts/` grepped for `title:` as a slice.yaml
  consumer. Zero downstream impact from the rename.
- ADR D7 Phase 1 is "additive, no renames" but scoped to **file/ID renames** —
  adding a new field and retiring a documentation-prose field (that was never
  specified as a cross-reference key) does not trigger D7's file-rename cost.
  ADR D1 explicitly calls out reach-into-`title:` as an anti-pattern; replacing
  it with the dedicated `name:` slot is the anti-pattern's direct remedy.
- This slice's own `slice.yaml` already uses `name:` (intent:41 confirms).

**A2 — CLAUDE.md prompt rule placement.**
Flagged in `handoff-phase-1.md:16`.
- Resolution: **Top-of-file H2 section** (own heading, e.g. `## Identifier scheme`)
  placed **before** `## Safety-critical rules`. Single-sentence rule + pointer.
- Rationale: the rule is a standing behavioral protocol (applies to every write
  touching an entity), not a hook-enforced safety rule. Mixing it into
  `## Safety-critical rules` would blur the mechanically-enforced line. The
  line-3 preamble is intentionally dense (load-on-demand guide for other docs)
  and should not carry behavioral rules. Top-of-file H2 keeps high prompt-load
  visibility without polluting existing blocks.
- Phase 3 Builder may override if a stronger placement emerges; v6a/v6b only
  require the rule's content + pointer, not a specific section.

**A3 — `slice-yaml-id` bridge field in feature template.**
Not flagged in handoff; observed during Skeptic pass.
- Resolution: feature slice-list template **shows the hierarchical `id:` +
  `added:` shape** (normative per intent); `slice-yaml-id:` is documented as
  **transition-permitted, not required** in surrounding prose. The test
  (v2c) asserts only the hierarchical `id:` shape; the bridge-field guidance
  is prose-only and not test-enforced.

**A4 — operational-reference.md identity section placement.**
Not flagged in handoff; the intent allows "new subsection (or extension of the
existing identity-related section)" but no identity-related section exists.
- Resolution: **New H2 section `## Identifier scheme`** placed after
  `## Slice Directory Structure` and before `## Phase Gate Enforcement`. Groups
  with other entity/format material.
- Test v7a–v7d scope the assertions to this new section (heading-scoped regex)
  so Phase 3 cannot satisfy them by sprinkling the required strings into
  unrelated paragraphs.

**A5 — Lightweight (`.md`) vs full-reference (`.full.md`) variants.**
Intent envelope includes both, but spec commitments describe template content
that lives only in the `.full.md` variants (YAML blocks, worked examples).
- Resolution: Phase 2 tests target **only the `.full.md` variants**. Updates to
  lightweight variants are permitted but not required. Phase 3 Builder decides
  whether any lightweight variant needs a pointer-update based on how the user
  surface reads post-change. If a lightweight variant carries a `slice.yaml`
  reference or similar that reads staler than it should, Builder should update
  it as part of their own GREEN work — v1a/v2/v3 do not require it.

## Validation suite shape

One file: `tests/unit/test_identifier_scheme_templates.py`, 20 tests mapped to
intent verification IDs:

| Test | Intent V# | Target |
|------|-----------|--------|
| v1a  | V1 | slice.yaml template has `name:` field |
| v1b  | V1 | hierarchical `<feature-id>/<slice-slug>` id: guidance |
| v1c  | V1 | legacy SLICE-NNN framed as accepted during transition |
| v2a  | V2 | feature template has `name:` field |
| v2b  | V2 | feature template has `shaped-from:` field |
| v2c  | V2 | feature slice-list entry uses hierarchical `id:` |
| v3a  | V3 | ADR frontmatter template has `name:` |
| v3b  | V3 | ADR `id:` guidance names flat-slug form + has example |
| v3c  | V3 | `supersedes:`/`adrs-referenced:` id-values-not-filenames guidance |
| v3d  | V3 | ADR body decision-point `<adr-id>/<decision-slug>` guidance |
| v4a  | V4 | handoff template references ADR identifier-scheme D8 for `## Features` |
| v4b  | V4 | handoff has worked-example code block with `## Features` + `- <feature-id>:` lines |
| v5a  | V5 | decision template names `<adr-id>/<decision-slug>` as cross-ADR citation |
| v6a  | V6 | CLAUDE.md prompt rule mentions `id:` and `name:` |
| v6b  | V6 | CLAUDE.md rule paragraph points to `identifier-scheme.md` or `operational-reference.md` |
| v7a  | V7 | operational-reference has per-entity id-shape table (Entity\|id shape\|Example\|Hierarchy) |
| v7b  | V7 | identity section enumerates ADR, Decision point, Slice, Feature |
| v7c  | V7 | identity section frames `name:` as frontmatter slot |
| v7d  | V7 | identity section documents `shaped-from:` provenance |
| v12  | V12 | start-slice Step 4 slice.yaml example is self-consistent (has `name:`) |

Intent checks **V8, V9, V10, V11** are Phase 4 Auditor concerns (structural
snapshot diff, scope discipline, test-file scope, architecture validator) and
are not executable pytest assertions in the Phase 2 suite.

## RED verification

`uv run pytest tests/unit/test_identifier_scheme_templates.py -v` → **20 failed**
against HEAD `d1cdb55`. No test passes vacuously; each assertion ties to a
spec commitment currently absent from the envelope files.

Pre-existing unrelated failures in `tests/unit/test_d3_bypass_log_format.py`
(4 tests) are tracked in `.claude/handoff.md` blocked/pending list and are
not caused by this slice.

## Phase 3 Builder notes (not input to Builder)

Builder receives `intent.md` + this test file only — **not this approach.md**
(operational-reference.md:46). The table above is Skeptic's audit trail for
Phase 4 Auditor and for future readers. If Builder finds a test's wording
ambiguous, the intent is the source of truth; the test is only the compiled
assertion.

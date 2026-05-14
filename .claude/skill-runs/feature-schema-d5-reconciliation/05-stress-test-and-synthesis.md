# Phase 2 comparison + Phase 3 stress test

## Comparison table

| Approach | Core idea | Constraints honored | Pre-mortem exposure | Downstream impact |
|----------|-----------|---------------------|---------------------|-------------------|
| **A — NARROW pure (drop extras)** | D5 unchanged; orchestrator-paths migrates fully to D5 (rename charter→intent, add shaped-from, **drop** all 6 extras, fix slice-status) | D5 ✓ (strict read); feature-slice-model D0 ✓; minimal-schema philosophy ✓ | Resolves S1, S2, S3, S5, S6. **Residual: S4 (audit-findings cross-ref loss)** | One YAML edit. No ADR change. Most conservative. |
| **A' / C — NARROW permissive + L-024** | D5 unchanged; orchestrator-paths conforms structurally but **retains 6 extras as unvalidated advisory** (D5's epic-rejection-only pattern permits silent fields). Add L-024 lesson with N≥3 schema-amendment threshold | D5 ✓ (default-permit read); operational-reference ✓; lesson convention ✓ | Resolves S1, S2, S3, S5, S6. **Mitigates S4** by retaining audit-findings as inert prose | One YAML edit + one lesson entry. No ADR change. Documents the meta-decision. |
| **B — WIDEN via supersession** | Author identifier-scheme-v2 ADR per identifier-scheme/D3 versioning rule; canonize charter as primary, intent as alias, 6 extras as enumerated optional | identifier-scheme/D3 ✓; preserves audit-findings ✓; **inverts** D5's minimal-schema principle | Resolves S1, S4. Avoids S5 via supersession form. **Residual: S2 (independent), S6 (alias risk), long-term S3 (proliferation)** | New ADR; template + operational-reference updates; possible helper script. Largest blast radius. |

## Phase 3 — Adversarial stress test on C (HYBRID)

C is the apparent winner. Attack it.

### Disconfirming search

**Claim 1: D5 is default-permit (extras are silently allowed).**
- Supporting evidence: D5 names *one* rejection (`epic:`); doesn't say "and only these fields are permitted" (`identifier-scheme.md:91`). Pattern is "list what's allowed + reject specific things by name."
- Disconfirming evidence: spec-writing convention is usually default-deny — "schema X has fields A, B, C" implies "and no others." A reader could read D5 as exhaustive.
- Verdict: **genuinely ambiguous**. C's reading is defensible but not unique. If a future /decision reads D5 as default-deny, retained extras become violations.
- Mitigation: document the reading in the migration commit and in L-024. If/when the strict reading is adopted, the extras can be relocated then.

**Claim 2: N≥3 is the right threshold for schema-amendment trigger.**
- Supporting evidence: cairn precedent — L-011 in lessons.md uses 3 for mechanical-fix recurrence (`docs/lessons.md:223`).
- Disconfirming evidence: L-011 is for code-pattern recurrence, not schema decisions. Schema amendments have different stakes (firm ADR change). N=2 might be enough if both instances are independently structurally important.
- Verdict: **convention, not derived**. C's threshold is consistent with cairn precedent but not analytically grounded.
- Mitigation: state the threshold as "starting heuristic, revise if a single high-importance instance forces re-evaluation."

**Claim 3: No tooling reads feature-file fields, so retention is safe.**
- Supporting evidence: Phase 0 confirmed (`01-constraints.md:24-25`).
- Disconfirming evidence: future tooling MIGHT validate strictly. If `test_feature_file_schema.py` is extended to live files AND adopts the default-deny reading of D5, the retained extras fail.
- Verdict: **forward-risk under a specific future**. The risk is bounded — strictness adoption requires a deliberate decision; not silent.
- Mitigation: L-024 names this scenario; if/when strict validation lands, the extras move to canonical homes (lessons.md, slice files, etc.) at that point.

### Steel-man the runner-up (NARROW pure / Approach A)

A's case made strongest:
1. **Simpler migration.** A drops the extras outright. No "default-permit reading" to defend, no advisory-field convention to maintain. Future readers see a clean D5-conforming file.
2. **Avoids the ambiguity entirely.** If D5 is later read as default-deny, A's migration is already correct; C requires a follow-up cleanup.
3. **Forces the data-relocation decision NOW.** Under A, audit-findings either gets a canonical home (lessons.md back-refs) or is acknowledged as lost. Under C, the data lives in limbo — not officially in D5, not officially relocated.
4. **L-024 might be over-engineering.** If feature-file fields are advisory anyway and no tool reads them, why establish a threshold mechanism? The next time this comes up, a fresh /decision reaches the same conclusion. The lesson is methodology overhead.

These are real points. The strongest is #3 — under C, audit-findings is in a "neither-here-nor-there" state. Inert but not relocated.

### Assumption audit (C)

| Assumption | Verified or believed? | Failure mode if wrong |
|------------|----------------------|----------------------|
| D5 reads as default-permit | Believed (text is ambiguous) | Future strict reading invalidates retained extras |
| L-024 will influence future authors | Believed (lessons.md convention) | Authors ignore lessons → drift repeats |
| N≥3 is right threshold | Believed (precedent borrowed from L-011) | Wrong threshold under-triggers or over-triggers WIDEN |
| audit-findings cross-ref doesn't need canonical relocation | Believed (no tool reads it; informal persistence is enough) | Audit trail breaks the moment someone tries to validate it |
| No tool will validate feature-file fields strictly soon | Believed (no scheduled work; current tests synthetic-only) | Strict validation lands → C requires immediate cleanup |

5 beliefs, 0 verifications. C rests entirely on assumptions, but they're all *plausible* given current state. The failure modes are all "future cleanup needed", not "present breakage." That's acceptable under cairn's "cut before adding" philosophy: don't pre-build for hypothetical futures.

### Verdict

**C survives the stress test.** Its weakest assumption (D5 default-permit reading) is genuinely defensible and the failure mode degrades gracefully (cleanup-later, not break-now). Its strongest argument over A is preservation of audit-findings cross-reference at zero migration cost. Its strongest argument over B is avoiding firm-ADR amendment for an advisory schema with zero mechanical consumers.

**Recommended decision: C — HYBRID NARROW + L-024.**

Concretely:
1. Migrate `.claude/features/orchestrator-paths.yaml` mechanically: rename `charter:` → `intent:`, add `shaped-from: substrate/root-resolver` (using predecessor as provenance), add `created: <git-derived-date>`, remove slice-entry `status: phase-1`. **Retain** `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope`, top-level `status` as unvalidated advisory fields.
2. Append L-024 to `docs/lessons.md`: "Single-feature schema drift insufficient to amend firm ADR; N≥3 trigger for WIDEN."
3. D5 unchanged — no ADR edit.
4. Resume Trial B from T5 with D5 contract block reflecting the default-permit reading (D5 must-satisfy clause = "feature files carry id, name, intent, shaped-from"; doesn't reject extras).

### What this enables Trial B to do

T5 can now write `test_d5_feature_files_well_formed` to check ONLY the four required keys are present. Extras pass through unchecked. orchestrator-paths.yaml satisfies the test after migration. T6, T7, T8 proceed as planned.

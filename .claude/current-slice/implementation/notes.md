---
slice: SLICE-018 (identifier-scheme/validator-flat-slug)
phase: 3-implementation
---

## Scope deviation — ARCHITECTURE.md INV-005 re-point

Intent declared `docs/ARCHITECTURE.md` out-of-scope ("no invariant text edits"; boundary §2 names the re-point as a follow-on `/refresh-architecture` concern). The Phase 2 test bank, however, enforces two assertions that cannot both hold with the current live corpus:

- `test_v1_cairn_self_dogfood_baseline` — validator exit 0 against cairn
- `intent §V9` — validator self-check exit 0 at end of Phase 3 and Phase 4

Once discovery widens to include `docs/adr/identifier-scheme.md` (firm, accepted, `invariants-touched: []`), Check B correctly reports it as uncovered against the live corpus, breaking V1/V9. INV-005's parenthetical cited `(ADR-006)` as a validator-anchored proxy precisely because the pre-widening validator could not resolve `(identifier-scheme)`; that proxy is obsolete the moment widening lands.

Resolution (user-approved): one-line edit, `docs/ARCHITECTURE.md:49`, `(ADR-006)` → `(identifier-scheme)`. INV-006 still cites `(ADR-006)` so ADR-006's Check B coverage is unchanged.

No other invariant lines were edited. No ADR frontmatter was edited.

## Stale envelope-compliance tests from prior slices

Two tests fail pre-commit and are not SLICE-018 regressions:

- `tests/unit/test_slice_005_design_decomposition.py::test_v7_envelope_compliance`
- `tests/unit/test_sweep_debt_cleanup.py::test_v4_envelope_compliance`

Both run `git diff --name-only HEAD` and assert the result matches their slice's allowlist. They fire on any uncommitted working-tree change outside the SLICE-005 / SLICE-007 envelopes — i.e., any later slice in mid-flight. After SLICE-018 is committed, the diff against HEAD becomes empty and both pass.

This is latent test-infrastructure debt, not an envelope breach. Candidate follow-on cleanup: rewrite either test to compare against a historical commit range (the slice's merge commit) rather than working tree, or scope them to run only inside the originating slice's Phase 4.

## Intent-not-pinned implementation choices

**Flat-slug token recognition.** Intent §"Invariant line reference parsing" says a flat-slug token matches "an existing ADR's `id:` field" but does not pin the lexical shape. Chose `^[a-z][a-z0-9]*(-[a-z0-9]+)+$` — requires ≥1 hyphen. Excludes commentary words (`pending`, `confirmed`) that could otherwise collide with a future single-word slug. Matches every slug in the repo today (`identifier-scheme`, `d3-bypass-classification`) and every token in the Phase 2 test fixtures.

**Flat-slug tokens scoped to trailing parenthetical.** Legacy `ADR-NNN` tokens are scanned anywhere in the invariant text (preserves V1 commentary parity, e.g. `(ADR-004; confirmed by ADR-009)`). Flat-slug tokens are scanned only as top-level `;`/`,`-separated fragments inside the trailing parenthetical matched by `\(([^()]*)\)\s*$`. Prevents false positives on descriptive prose that happens to contain a kebab phrase.

**Supersession detection.** Intent §"Check C" pins the criterion to `superseded-by:` being set for flat-slug ADRs. `_is_superseded(adr)` returns True if `superseded-by` is truthy OR legacy `status` is in `("superseded", "deprecated", "retired")`. Preserves legacy behavior for `ADR-NNN` references while meeting the flat-slug contract.

**ADR discovery still loads superseded ADRs into the resolution table.** Intent §"ADR discovery" phrases the discovery exclusion as "excluding `index.md` and any file whose frontmatter `status:` is `superseded` or `deprecated`". Interpreted this as the operational equivalent of the current legacy behavior: superseded ADRs ARE loaded into the `adrs` dict so Check C can route references to them, but are filtered out of Check B by `_is_active_firm`. A strict reading (don't load them at all) would make Check C undetectable for superseded references and break the flat-slug V4 test (`test_flat_slug_superseded_reference_fails_check_c`).

**Error message shape.** Check C's message changed from `"which is {status}"` to `"which is superseded"`. The status-string lookup is path-specific (only legacy ADRs set `status: superseded` verbatim; flat-slug fixtures keep `status: accepted` with `superseded-by: new-scheme`), so a static "superseded" token generalizes cleanly and satisfies the `"supersed" in result.stdout.lower()` test assertion.

**ADR-NNN key normalization.** Legacy ADR keys are zero-padded to `ADR-NNN` (three-digit) form. Invariant references like `ADR-1` vs `ADR-001` resolve to the same key, preserving the current int-based equivalence.

## Files changed

- `scripts/validate_architecture.py` — reference resolution extended from int ADR-NNN to string key (legacy `ADR-NNN` | flat-slug); helpers `_derive_adr_key`, `_is_superseded`, `_is_active_firm`, `_discover_adr_files`, `_extract_refs`; discovery glob widened from `[0-9]*.md` to `*.md` (minus `index.md`).
- `docs/ARCHITECTURE.md:49` — INV-005 parenthetical `(ADR-006)` → `(identifier-scheme)` (scope deviation above).

## Test results at end of Phase 3

- `tests/unit/test_validate_architecture.py` — 14/14 pass (6 V1–V6 regression + 8 new SLICE-018 flat-slug tests).
- Validator self-check against cairn — exit 0. `Invariants verified: 7 / ADR files checked: 11`.
- Full suite — 236/238 pass; remaining 2 are the stale envelope-compliance tests that flip green once SLICE-018 commits (see above).

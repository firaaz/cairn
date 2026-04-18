---
slice: identifier-scheme/slice-and-feature-rename
phase: 2-validation
date: 2026-04-18
---

## Ambiguity resolutions (from intent §§9, 8)

### §9 — `adr-003-landed-at-slice` disposition: **(C) drop**

The frontmatter field in `docs/dogfood-log.md:3` is declared meaningless
post-retirement. Rationale:

- Pre-§9, `baseline` from this field and `current_slice_number` from
  `sweep.yaml` combined as `current − baseline` to produce the
  slices-since-ADR-003 delta fed to `_evaluate()`.
- Post-§9, the git-log counter keyed on ADR `cliff-failure-mode-and-v1-defenses`'s
  first-commit sha produces that delta directly. Both halves of the subtraction
  are replaced in one step; no surviving consumer for the field.
- Repurposing (sha or slice-id) would preserve a decorative annotation with
  zero protocol role. YAGNI — drop.

`docs/dogfood-log.md` is out of envelope; the stale line physically remains
until an operator edit. Phase 3 removes the frontmatter read-path in
`scripts/dogfood_evaluate.py` so the field's presence or absence is
ignored. Phase 3 records the same disposition in `implementation/notes.md`.

### §8 — sweep-due fallback is normatively tested

Per intent §8: missing/unresolvable `last-sweep-at-slice-id:` → "sweep due" +
one-line stderr diagnostic. Phase 2 encodes this as test assertions against the
`/start-slice complete` sweep-due computation path.

## Envelope-correct Phase 2 pytest scope

Intent §154 labels all ten verification items as **"Phase 4 Auditor checks
(every assertion cited with `file:line`)"**. The slice envelope
(intent.md:8–19) permits test modifications only in
`tests/unit/test_dogfood_evaluate.py` — no new test files. Therefore:

- **Phase 2 pytest** = rewrite `test_dogfood_evaluate.py` per intent §12 only.
- **Phase 4 Auditor** handles verification items 1, 2, 4, 5, 8, 9, 10 via
  direct file inspection with `file:line` citations — not pytest.

First attempt (`test_feature_file_identifier_scheme.py`, plus three other
new test files) was blocked by `scope-guard.sh` and correctly so; the
envelope was written on the assumption that the migration is data/prose
with a single code site (`dogfood_evaluate.py`).

## Phase 2 test targets (envelope-constrained)

| Intent § | Location | Assertion shape |
|---|---|---|
| 3 — `dogfood_evaluate.py` CLI contract | `tests/unit/test_dogfood_evaluate.py` (existing; rewritten per intent §12) | Exits 0/1/2; fixtures stage synthetic git history rooted on the ADR `cliff-failure-mode-and-v1-defenses` first-commit; sweep.yaml fixture uses new shape (`last-sweep-at-slice-id` + `sweep-interval` only). |
| 8 §fallback — baseline-missing | same file | When the ADR-003 baseline commit cannot be located, the counter MUST fall back conservatively (treat as maximal post-cliff count / trigger evaluation) and emit a one-line stderr diagnostic — mirrors §8's sweep-due fallback philosophy in the one codepath inside the envelope. |
| 9 — field drop | same file | No code path reads `adr-003-landed-at-slice` from dogfood-log.md frontmatter; harness that writes dogfood-log.md no longer seeds the field. |

Phase 4 Auditor (run-at-close) absorbs items 1, 2, 4, 5, 6, 7, 8 (INV-005),
9 (INV-006), 10 (D1+D3 gates) — all handled by `grep -n` / yaml-parse
citations in `integration/notes.md` per the standard Auditor pass.

## Phase 2 scope limits

- No source/implementation writes. Tests commit as RED; Phase 3 Builder makes
  them GREEN.
- `docs/dogfood-log.md` stays as-is (out of envelope) even though its frontmatter
  carries the now-meaningless `adr-003-landed-at-slice: 2`.
- Legacy-format fixtures in out-of-scope tests (per intent §12) MUST NOT be
  touched — they regression-test hook/validator mixed-window tolerance.

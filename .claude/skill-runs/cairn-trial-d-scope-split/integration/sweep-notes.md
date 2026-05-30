# Phase 4 sweep notes — cairn-trial-d-scope-split

- Feature: `cairn-trial-d-scope-split` (Trial D — scope-split rule + four atomicity exception classes)
- Snapshot SHA: `c2e93f9c8ec6956e984e9ea3739558f36b18e297`
- HEAD at audit: `644f3db` (phases 1-3 committed: `233096e` intent, `8dec48e` tests, `c1ae50c` impl, `644f3db` wiring)
- Baseline file: `/tmp/cairn-trial-d-scope-split-baseline-failures.txt` (8 pre-existing failures — NOT this feature's)
- invariants-touched: `[]` (none; per `intent.md` frontmatter)

## Tests

| Command | Result |
|---|---|
| `uv run pytest tests/unit/test_atomicity.py tests/unit/test_atomicity_guard.py tests/unit/test_template_extraction.py -q` | **58 passed** (GREEN, as expected) |
| `uv run pytest -q --tb=no -rf` | **8 failed, 552 passed, 2 skipped, 2 xfailed** |

Baseline reconciliation: the 8 failures at HEAD are **byte-identical** to the 8 in the baseline file
(`diff` of sorted FAILED-id lists → exit 0, IDENTICAL). **Zero new failures.** Delta vs baseline:
`+53 passed` (499 → 552), accounting for the Phase-2/3 atomicity tests; failure set unchanged.

Documented out-of-scope pre-existing failures (inherited at snapshot, NOT attributable to this feature):
- `test_assertion_block_yaml_parser.py::test_real_architecture_md_parses_inv_002_correctly`
- `test_context_discipline_protocol.py::test_v1_handoff_template_exists_and_is_tight`
- `test_feature_skill_conformance.py::TestHandoffCrossFeatureIndex::test_handoff_template_has_features_section`
- `test_feature_skill_conformance.py::TestHandoffCrossFeatureIndex::test_handoff_features_section_describes_per_feature_line`
- `test_inv_002_inv_008_architecture_blocks.py::test_inv_002_block_type_is_structural_parser`
- `test_inv_002_inv_008_architecture_blocks.py::test_inv_002_block_carries_binding_effective_from`
- `test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks`
- `test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged`

## Validator

| Command | Result |
|---|---|
| `uv run python scripts/validate_architecture.py` | **ALL CHECKS PASSED** — 12 invariants verified, 38 ADR files checked (rc=0) |
| `bash scripts/smoketest_hooks.sh` | **PASS atomicity_guard.py**, PASS premise_guard.py, PASS role_guard.py (clean import under bare `python3`) |

No pre-existing validator FAILs; nothing out-of-scope to document for the validator.

## Invariants

`invariants-touched: []` — this feature declares no `INV-NNN` global invariants. The validator's
12 invariant blocks all PASS unchanged. Evidence below covers the feature-local invariants (FLI-1..6)
the intent claims, plus the contract drift + wiring audits.

| ID | Statement | Status | Evidence |
|---|---|---|---|
| (global) INV blocks | 12 architecture invariants verified against 38 ADRs | PASS | `scripts/validate_architecture.py` → `ALL CHECKS PASSED  Invariants verified: 12  ADR files checked: 38` |
| FLI-1 | single source of truth: only `scripts/lib/atomicity.py` defines `EXCEPTION_TAGS`/`is_atomic`/`check_clauses`; CLI gate + validator both import it | PASS | `scripts/lib/atomicity.py:14` `EXCEPTION_TAGS = frozenset(...)`; both surfaces `from lib.atomicity import ...` per intent spec; smoketest confirms `atomicity_guard.py` imports cleanly |
| FLI-2 | fail-open on absence (exit 0 + visible stderr notice), fail-closed on malformation (exit 2); `CAIRN_CONTRACT_REQUIRED=1` flips absence to exit 1 | PASS | `docs/operational-reference.md:241` exit-code table; SKILL.md:68 step 5b; covered by `test_atomicity_guard.py` (58 green) |
| FLI-3 | tag is a one-line escape, never a hard wall | PASS | `scripts/lib/atomicity.py:80-102` `check_clauses` — a flagged clause passes by carrying a valid tag + (where required) declaration; SKILL.md:68 "tagging is the cheap one-line escape" |
| FLI-4 | `trivial-existence` needs no declaration; other three require non-empty declaration; unknown tag always fails | PASS | `scripts/lib/atomicity.py:17` `TAGS_REQUIRING_DECLARATION = EXCEPTION_TAGS - {"trivial-existence"}`; `:91` unknown-tag offence; `:94` empty-declaration offence |
| FLI-5 | ADD-not-REPLACE: eight prose headings remain in order after `## Contract` | PASS | `test_template_extraction.py` eight-heading-in-order assertion green (part of the 58) |
| FLI-6 | template-documented tags == `scripts/lib/atomicity.EXCEPTION_TAGS` exactly | PASS | `templates/intent.md:102-105` documents `universal-set`/`regression-meta`/`operator-bound`/`trivial-existence`; matches `scripts/lib/atomicity.py:14-16` set exactly (no drift) |

### Wiring audit (intent Verification §)
- SKILL.md gate step: `.claude/skills/cairn-tdd-feature/SKILL.md:68` — step 5b "Scope-split (atomicity) gate (sibling of the premise gate)" invoking `checks/atomicity_guard.py`, exit-code 0/1/2 semantics + both env knobs. PASS.
- ops-ref env knobs: `docs/operational-reference.md:303` `CAIRN_ATOMICITY_FIX`, `:304` `CAIRN_CONTRACT_REQUIRED` (both in the env-var table). PASS.
- dist mirror: `dist/skills/cairn-tdd-feature/SKILL.md:68` contains the atomicity gate step (`atomicity_guard.py`, `CAIRN_ATOMICITY_FIX`, `CAIRN_CONTRACT_REQUIRED`); identical to the canonical SKILL.md (`diff` rc=0). PASS.

## Dist mirror

`uv run python scripts/build_dist.py` (rc=0). `build_dist.py` copies an allow-list of canonical
sources into `dist/`; the canonical `.claude/skills/cairn-tdd-feature/SKILL.md` mirrors to
`dist/skills/cairn-tdd-feature/SKILL.md`. `git status --porcelain -- dist/` → **0 lines (clean)**:
the dist `SKILL.md` mirror was regenerated and committed during the feature build (`git log` shows
it last changed in Phase-2 commit `8dec48e`), and re-running the build produced byte-identical
output. **No unrelated dist changes** were pulled in. The dist `SKILL.md` mirror carries the
atomicity gate step at line 68 (verified by grep + a clean `diff` against canonical), so there is
nothing new for Phase 4 to commit in `dist/` — only this sweep-notes file + the handoff pointer.

## Adversarial verification (run by the conductor — recorded)

NO real defects. GREEN holds. The gate is mechanically sound across 26 adversarial inputs.
Escape-hatch design validated: visible stderr notice on absence + `CAIRN_CONTRACT_REQUIRED` opt-in
hard-block lever. The exit-2 fail-closed backstop (`## Contract` heading present but unparseable)
fires as designed.

## Known findings — carried forward to the DEFERRED 3-intent measurement

Heuristic is FROZEN this session per the plan Scope-Out ("build + tests only; heuristic frozen at
close"). Do NOT fix here. These are calibration concerns for the follow-on measurement, not Phase-4
defects:

- **F1 — `_UNIVERSAL` over-block.** `\bno\s` and the bare `\b(every|all|each|any)\b` tokens fire on
  incidental occurrences, a confirmed false-POSITIVE mechanism (`scripts/lib/atomicity.py:19-22`)
  that threatens the Trial D <10% false-positive target. Tag is the escape, but high noise trains
  rubber-stamping.
- **F2 — Calibration is UNMEASURABLE this session.** None of the 3 real corpus intents
  (`m2-dogfood-extract-invariant-ids`, `m5-f1`, `m7`) carries a `## Contract` block, so `is_atomic`
  has ZERO real positive corpus. Unit tests prove the *mechanism*, not *calibration*. First work
  item of the measurement: author the 3 real intents' contracts in the new shape, then size the real
  false-positive rate.
- **F3 — GAP-1 / GAP-3.** GAP-1: first-yaml-fence-wins (a 2nd `## Contract` block / 2nd yaml fence
  is unchecked). GAP-3: near-miss heading (`##  Contract` / wrong casing) fails-open-with-notice.
  Both low severity, recorded.
- **F4 — Residual semantic hole.** Trivial-existence mis-tag / junk declaration is by-design
  operator-review-bound (same honest limit as premise-grounding). A judge-agent is the post-Trial-E
  closer.

## Conclusion

Suite green at HEAD (only the 8 pre-existing baseline failures, zero new). Validator + smoketest
pass. FLI-1..6 + drift + wiring all PASS. Dist mirror reproducible and already committed. Status: OK.

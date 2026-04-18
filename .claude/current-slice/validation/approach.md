# Phase 2 Approach — identifier-scheme/doc-sweep

## Role and skills
Skeptic. `superpowers:test-driven-development` (RED + Verify RED half;
cairn session-bisected). `superpowers:brainstorming` applied to per-
occurrence ambiguity enumeration (intent.md:43).

## Scope anchor
Intent.md references `§D7 Phase 2 Part 3` as the slice locus. ADR
`identifier-scheme` §D7 Phase 2 is an unnumbered bullet list at
`docs/adr/identifier-scheme.md:115-122`; "Part 3" is intent-shorthand
for the cross-reference-sweep bullet at line 120: _"Cross-reference
sweep across `docs/`, `commands/`, `scripts/`, `.claude/`. Every site
touched."_ This slice's concrete scope is the residual live-prose
subset of that site list after `adr-rename-sweep` and
`slice-and-feature-rename` already landed.

## Envelope amendment (Skeptic discovery)
Phase 1 intent envelope omitted the new Phase 2 test file. Amended
`intent.md` envelope to add `tests/unit/test_identifier_scheme_sweep.py`.
This is a narrow declarative correction (where the Phase 2 test lives),
not a spec change. Scope-guard permits `.claude/current-slice/*` writes
unconditionally, so the amendment required no escape hatch.

## Enumeration result
`git grep -E '(SLICE-[0-9]+|ADR-[0-9]+)'` over the envelope returns
~58 occurrences. Classified below.

### MIGRATE (~52 occurrences)
- `commands/claude-code/handoff.full.md` L35, L63, L64 — instructional
  examples. User decision 2026-04-18: migrate so the template teaches
  current canonical form.
- `tests/unit/test_dogfood_evaluate.py` L3 — explicit intent verification
  item 2 (`Originally SLICE-004` → current canonical id).
- `docs/lessons.md` L7, L13, L82, L92 — concrete-instance references to
  historical events. User decision 2026-04-18: migrate so entries
  remain stable against future renames.
- `docs/operational-reference.md` L257 — two `SLICE-003` mentions in
  the `learning.md` staging-ground paragraph. See known-issue below.
- `docs/ARCHITECTURE.md` L41, L96 — handled via regeneration (see
  ARCHITECTURE.md treatment below).
- `docs/adr/*.md` body prose across 7 ADR files: `phase-pipeline-
  evaluation.md` (~16), `phase-lock-and-role-declaration.md` (~7),
  `d3-bypass-classification.md` (8), `identifier-scheme.md` L147-149
  (3 in the D8 example block; user decision: migrate), `context-
  discipline-protocol.md` (~8), `cliff-failure-mode-and-v1-defenses.md`
  (3), `feature-slice-model.md` L112 (1). All require `ADR_EDITORIAL_FIX=1`
  per intent §Specification Detail; Phase 3 commits must log affected
  files in commit-message bodies (verification item 8).

### PRESERVE (6 occurrences — discussion-of-legacy-format exception)
Rule of thumb (intent.md:43): _"if removing the legacy mention would
make the surrounding sentence incoherent, it stays."_

| File:Line | Preserved snippet |
|---|---|
| `docs/adr/semantic-identity.md:24` | prose explicitly describing the numeric-prefix convention being replaced |
| `docs/adr/semantic-identity.md:30` | _"`SLICE-003` communicates nothing about what the slice does"_ directly critiques the legacy form |
| `docs/adr/semantic-identity.md:86` | contrasts `after: [adr-rename]` vs `after: [SLICE-007]` to illustrate the migration motivation |
| `docs/adr/bootstrap-exception.md:30` | `SLICE-000` is a hypothetical degenerate slice that never existed |
| `docs/adr/bootstrap-exception.md:50` | same: `SLICE-000` hypothetical in the Rejected-Alternatives |
| `docs/adr/feature-slice-model.md:136` | _"Completed slices (SLICE-001 through current) retain their identities in git history"_ is *about* the non-retroactive-rename policy |

The PRESERVE allowlist is encoded as the `PRESERVE` dict in
`tests/unit/test_identifier_scheme_sweep.py`. Phase 3 must retain
these 6 sites unchanged; the canary test
`test_preserve_allowlist_entries_still_present` enforces it.

## Test-shape decision (user 2026-04-18)
Intent verification items 1 and 2 encoded as discriminating RED pytest
tests. Items 3-8 documented as Phase 4 Auditor checklist below. A third
GREEN-canary test enforces that Phase 3's sweep does not accidentally
delete discussion-of-legacy-format sites alongside nearby residuals.

Test file: `tests/unit/test_identifier_scheme_sweep.py` (stdlib + pytest,
three functions, ~110 LoC).

### RED verified (this Phase 2 commit)
```
$ uv run pytest tests/unit/test_identifier_scheme_sweep.py -v
test_envelope_zero_residual_modulo_allowlist          FAILED  (58 offenders)
test_dogfood_docstring_identifier_migrated            FAILED  (SLICE-004)
test_preserve_allowlist_entries_still_present         PASSED  (canary)
```

## ARCHITECTURE.md treatment (user 2026-04-18)
Two occurrences (L41, L96) in `docs/ARCHITECTURE.md`. User decision:
Phase 3 invokes `/refresh-architecture` to regenerate the file rather
than direct-editing prose that the refresh may overwrite. The test
envelope includes ARCHITECTURE.md, so regeneration must emit canonical
ids; post-regen, `test_envelope_zero_residual_modulo_allowlist` passes
iff the generator uses current form. If the generator still emits
legacy ids, Phase 3 escalates (likely the generator source itself needs
a separate migration slice).

## Phase 3 Builder known-issue — `operational-reference.md:257`
L257 reads: _"the 3× promotion rule ... is **deferred to SLICE-003**.
Until SLICE-003 lands, nothing in cairn writes to `learning.md`
automatically"_. Mechanical id migration produces a false-continuing-
tense sentence if the referenced slice has landed (per
`phase-pipeline-evaluation.md:31`, SLICE-003 did ship). Builder decides
at Phase 3 time between:

1. Migrate id only, accept the staleness (strict §D7 Phase 2 scope).
2. Migrate id AND fix tense inline (one-line content correction under
   the same sweep-commit rubric). **Recommended.**
3. Escalate via handoff for a separate slice.

Option 2 is recommended: same-line content correction is de minimis
and aligned with the spirit of a residual-prose sweep. Phase 3
Builder records the choice in `implementation/notes.md`.

## Canonical-id lookup (Phase 3 responsibility)
For each MIGRATE occurrence, Phase 3 Builder resolves the canonical
`id:` via:
- Active slices: `.claude/features/<feature>.yaml` entries.
- Completed slices: `.claude/completed-slices/<id>/slice.yaml` or
  `git log --follow` on the archived intent/slice files.

The Skeptic does not pre-resolve the lookup table; it is Phase 3
mechanical work.

## Phase 4 Auditor checklist
Items 3-8 are auditor-time checks, not Phase 2 pytest surface:

| Intent item | Check |
|---|---|
| 3 | `git diff --name-only main...HEAD` shows no files under `.claude/completed-slices/`, `.claude/sweep-results/`, `.claude/plans/`, `docs/plans/`, `docs/reviews/`, `.claude/learning.md`, `CHANGELOG.md`, `checks/`, `scripts/validate_architecture.py`, `scripts/dogfood_evaluate.py`. |
| 4 | `uv run pytest tests/unit/test_hook_tolerance.py tests/unit/test_adr_rename_sweep.py tests/unit/test_invariant_assertions.py tests/unit/test_validate_architecture.py` — all GREEN. |
| 5 | `uv run pytest` — full suite GREEN (includes the 3 tests introduced by this slice). |
| 6 | `uv run python scripts/validate_architecture.py` — exit 0. |
| 7 | `git diff main...HEAD` shows zero changes inside YAML frontmatter `adrs-referenced:` or `supersedes:` fields of any ADR file. |
| 8 | Every commit using `ADR_EDITORIAL_FIX=1` names the ADR file(s) edited in its commit-message body (auditable via `git log --grep='ADR_EDITORIAL_FIX'` or inspection of the Phase 3 commits). |

Items 4, 5, 6 are expected GREEN at Phase 2 exit (they were GREEN before
this slice began); they re-run at Phase 4 to catch regressions.

## Files committed at Phase 2 close
- `tests/unit/test_identifier_scheme_sweep.py` — three tests encoding
  verification items 1, 2 plus the PRESERVE canary.
- `.claude/current-slice/intent.md` — envelope amendment adding the
  test file path.
- `.claude/current-slice/validation/approach.md` — this document.

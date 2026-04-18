---
slice: efficiency-program-afternoon-wins/all-seven
phase: 2-validation
date: 2026-04-18
---

# Phase 2 Approach — efficiency-program/all-seven

Seven items, seven test modules, plus one cross-cutting invariants-evidence
module. All tests are RED as of this commit. Phase 3 (seven parallel Builders)
turns them GREEN.

## Ambiguities enumerated + resolutions

Enumerated before writing any test, per the Skeptic anti-behavior contract.

1. **Hook filename for Item 1 (role cheatsheet).** intent.md does not name the
   hook file. Resolved: test accepts any of
   `checks/{session-start,role-cheatsheet,session_start,cheatsheet}.sh`. Phase
   3 Builder picks one; registration in `.claude/settings.json` must reference
   whichever is chosen, which the test also checks.

2. **Form A vs Form B for Item 2 (measurements idempotency).** intent.md
   explicitly names this as a Phase 3 judgement call. Resolved: the
   measurements test passes if either (a) tracked path exists AND
   `git status --porcelain` is empty after two hook runs, OR (b) tracked path
   is gone AND a candidate relocated path exists outside `git ls-files`. One
   test enforces the top-level assertion; two companion tests assert
   form-specific extras, each early-returning if the other form was chosen.

3. **"SessionStart" hook wiring for Items 1 and 2.** intent.md implies one
   hook for Item 1, with Item 2 sometimes described as "the session-start
   hook." Resolved: tests treat Item 2 as potentially the same hook. The Item
   2 test searches the same candidate set as Item 1 plus a
   `measurements-refresh.sh` alternative, and accepts any match.

4. **"Pass state" fixture shape for Item 4 verifier.** intent.md names three
   checks (status-matches-subject, phase-commit handoff file exists, subject
   prefix). It does not exhaustively specify which combinations count as
   pass. Resolved: test uses a commit subject `handoff: phase-2 complete`
   plus an in-place `handoff.md` pointer and `slice.yaml.status:
   2-validation` — this satisfies checks 1 (status can legally be
   2-validation after a handoff), 2 (handoff.md exists — phase-commit check
   is only required when the subject is `phase-N:`, which this subject is
   not), and 3 (subject begins with `handoff:`). Phase 3 can refine the
   `phase-N` gating but the pass fixture we chose is minimally-assumptive.

5. **Renderer for Item 7.** intent.md says the `/status` skill is extended;
   it does not say whether the rendering is pure skill prose or a companion
   script. Resolved: test accepts a renderer at any of
   `scripts/{render_status,status}.{sh,py}`. If Phase 3 implements /status
   purely as prose, the renderer-existence test (and the two
   fixture-rendering tests) remain red but the schema-level checks on
   status.md still cover the five dashboard lines. FLAG for Phase 3: the
   choice of prose-only vs script is left open; skill text alone cannot be
   machine-verified for output length under 1500 chars, so a thin renderer
   script is the pragmatic path. Not a blocker for the slice.

6. **"Recent validation artifact" for Item 7.** intent.md says the dashboard
   line 2 comes from "most-recent `.claude/current-slice/validation/` or
   `integration/` artifact mtime." Resolved: fixture drops
   `validation/approach.md` in `tmp_path` and the test asserts the `Last test
   run` token is present, not its exact value — Phase 3 picks the formatting.

7. **Template format specifics for Item 6.** intent.md gives the shape:
   `phase-<N>: <slice-id> — <phase-output-label>` + preamble + `Next:`
   trailer. Resolved: test asserts only the load-bearing tokens — `phase-<N>:`
   and `Next:` — both of which are required by intent. Trailer wording is
   left to Phase 3.

8. **`status: failed` treatment in Item 6 hook.** intent.md says the hook
   no-ops for `complete`, `failed`, or non-phase values. Test includes an
   explicit `status: failed` no-op case.

9. **Allowlist entry-string format for Item 5.** intent names ten patterns
   using literal parenthesized strings like `Bash(sed -n *)`. These are the
   Claude Code permission-match strings; the test uses them verbatim. No
   resolution needed — intent is specific.

10. **Evidence schema for INV-002/INV-003/INV-004 in invariants module.**
    intent.md mentions the cross-item invariant-evidence table but does not
    pin exact file:line citations. Resolved: each invariant test asserts an
    artifact exists AND (for INV-003) that hook source references the Phase
    Skill Guide surface — minimum viable evidence. Phase 4 Auditor can cite
    stronger evidence once Phase 3 lands.

## Per-item test shape rationale

- **Item 1** — `test_item_01_role_cheatsheet.py`. Mirrored-root fixture using
  symlinks to real `docs/` and `checks/` so the hook resolves the Phase Skill
  Guide from a tmp cwd. Four phase-positive tests (one per phase value), two
  fallback tests (complete/failed), two malformed-input tests, two
  registration tests.

- **Item 2** — `test_item_02_measurements_idempotency.py`. Runs in
  PROJECT_ROOT (double-invocation check needs real git state). Form-agnostic
  top-level test with form-specific companion tests that early-return when
  inapplicable.

- **Item 3** — `test_item_03_read_before_write_prose.py`. Pure grep: verbatim
  phrase substring must appear at count ≥1 in two files. Extra ordering
  check: phrase precedes any following `slice.yaml` mention.

- **Item 4** — `test_item_04_handoff_verifier.py`. Uses `tmp_path` with a
  minimal git repo so `git log -1 --format=%s` works. Pass fixture and fail
  fixture isolated per test. Also checks handoff.md/handoff.full.md wiring.

- **Item 5** — `test_item_05_allowlist.py`. Pure JSON/regex: length ≥10, all
  ten required patterns present, no broad-wildcard regex violations.

- **Item 6** — `test_item_06_commit_templates.py`. Parameterized template
  existence over N in {1..4}; hook-invocation tests using `COMMIT_EDITMSG`
  buffer in `tmp_path` with symlinked templates and fixture slice.yaml.

- **Item 7** — `test_item_07_status_dashboard.py`. Split into: schema checks
  on status.md, existence of status.full.md, renderer fixture test with
  1500-char budget. Renderer path is candidate-search (accept any of four
  names).

- **Invariants evidence** — `test_invariants_evidence.py`. Three classes
  (one per invariant touched) plus a ledger class enumerating one assertion
  per item for Phase 4 Auditor citation convenience.

## Phase 3 judgement calls flagged

- **Item 2 Form A vs Form B.** Test is form-agnostic; Phase 3 picks.
- **Item 1/2 hook filename.** Test is candidate-set; Phase 3 picks.
- **Item 7 renderer type (sh vs py).** Test is candidate-set.
- **Item 7 prose-only vs with-renderer.** FLAG: prose-only implementation
  will leave three Item 7 tests red (renderer existence + two rendering
  tests). Not a blocker — skeletal renderer is a ~30-line shell script.

## RED verification evidence

Run: `uv run pytest tests/unit/efficiency_program/ -v 2>&1 | tail -60`.

**Summary:** 72 failed, 5 passed in 0.79s.

The 5 trivial passes are all precondition assertions that hold in RED state:

1. `test_inv004_status_md_under_lite_budget` — status.md is 16 lines today,
   well under 2500-char lite budget (expands in Phase 3).
2. `test_item2_no_chronic_M` (ledger) — tracked measurement file currently
   exists on disk; Item 2 has not been touched yet, so the "some artifact
   exists" ledger line passes.
3. `test_item_numbers_covered` (ledger meta) — counts the seven ledger
   methods in the class; structural not spec assertion.
4. `test_form_b_tracked_path_absent_when_relocated` — early-returns because
   tracked path still exists (Form A path, trivial pass).
5. `test_status_md_exists` — status.md file exists today in short form; the
   expansion is a separate assertion.

All 72 acceptance-criteria assertions fail. Example failure excerpt:

```
tests/unit/efficiency_program/test_item_04_handoff_verifier.py::TestVerifierExists::test_verifier_file_present
    E   AssertionError: scripts/verify_handoff.sh missing
    E       (expected at .../scripts/verify_handoff.sh)
```

```
tests/unit/efficiency_program/test_item_07_status_dashboard.py::TestDashboardRendering::test_renderer_exists
    E   AssertionError: No /status renderer found under scripts/;
    E       intent Item 7's fixture render test needs one of
    E       ['scripts/render_status.sh', 'scripts/render_status.py',
    E        'scripts/status.sh', 'scripts/status.py']
```

RED confirmed.

## Intent.md contradictions / open questions (not patched)

- **Envelope vs status-full.md.** Envelope declares
  `commands/claude-code/status.md` and `commands/claude-code/status.full.md`
  implicitly via the pattern line `commands/claude-code/status.md`. Only
  `status.md` is literally matched. If scope-guard treats the envelope
  glob as string-exact, writing `status.full.md` during Phase 3 may be
  blocked. Suggest Phase 3 either extends the envelope or that Phase 1
  clarify. Not patched — this is a Phase 3 problem.

- **Item 1 "Phase: <N> <phase-name>" output shape.** intent.md gives the
  exact format but the Phase Skill Guide table uses `1. Intent`, `2.
  Validation`, etc. Format `Phase: 3 Implementation` requires Phase 3 to
  strip the leading `<N>. `. Minor, not tested — hook source can emit any
  formatting that contains `Phase: <N>`.

- **Envelope: `.gitmessage-phase-*` is a new pattern at repo root.**
  scope-guard should allow it (new-file create), but `.gitmessage-phase-*`
  is not a pattern currently recognized by any hook allowlist. Phase 3 may
  need `EXPAND_ENVELOPE=1`. Flagged.

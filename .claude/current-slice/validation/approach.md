# Phase 2 — Skeptic approach

## Ambiguity enumeration

1. **Synthetic vs. live project root for scope-guard tests.** Intent §Test
   surface says "synthetic Write hook input under a slice whose envelope
   excludes the log." The live `.claude/current-slice/intent.md` (this
   slice) does not list the bypass logs in its envelope, so a live-root
   test would also exercise the admin-allowlist path. I chose **synthetic**:
   `tmp_path` + `CLAUDE_PROJECT_DIR` override + a fixture intent.md whose
   envelope is `src/unrelated/module.py`. Rationale: deterministic across
   slice phases (won't false-pass when run from `complete`/`failed` slice
   states where scope-guard short-circuits at line 27).
2. **Sweep-subject canonical form.** Intent says
   `sweep: post-demo — PASS`. The em-dash separator is U+2014, mirroring
   the `slice: ... — complete` arm. I asserted both the minimal form and
   a `PASS-with-known-debt` variant to lock the contract as **prefix-only**
   (matches `^sweep: ` only) — Phase 3 is free to keep the regex tight to
   the `^sweep: ` prefix without committing to a trailing-label vocabulary.
3. **Error-message wording.** Intent §Specification says the
   `expected one of:` string "updates to enumerate all four forms." I
   assert (i) the literal substring `expected one of` survives (regression
   guard against accidental rewording) and (ii) `sweep:` appears in the
   stderr of a rejected commit. Phase 3 may pick exact phrasing.
4. **Paper-cut #2 (doc).** Intent explicitly defers — no test surface.
   No file written; no assertion fabricated.

## Test coverage map

- `test_scope_guard_admin_allowlist.py` — source inspection (literal
  path strings present) + subprocess matrix `{Write,Edit} × {d1,d3}` under
  a synthetic excluding envelope. 6 cases total. RED: case statement at
  scope-guard.sh:60 lacks both literals and envelope-fall-through exits 2.
- `test_verify_handoff_sweep_subject.py` — source inspection (`^sweep:`
  + error-string `sweep:`) + subprocess accept (`sweep: post-demo — PASS`,
  `PASS-with-known-debt` variant) + negative regression (`chore:` still
  rejected, stderr enumerates `sweep:`). RED across 5 cases.

## Confirmed RED

`uv run pytest tests/unit/test_scope_guard_admin_allowlist.py
tests/unit/test_verify_handoff_sweep_subject.py -v` → **11 failed,
2 passed**. The two passes are file-exists sanity checks and not
contract assertions; all behavioural and source-shape assertions
fail as required. INV-008 untouched; stdlib-only.

---
feature-id: cairn-m6-f3-migration-and-symlink-retire
as-of: 2026-05-08 23fcba3
phase: 4-integration
verdict: PASS-with-pending-manual
---

## Status

**PASS-with-pending-manual.** All eight dispatch-time audit checks (intent §Verification 1–8) green. Audit check 9 (manual end-to-end real `/plugin install`) is recorded as PENDING below per intent (operator-bound, requires `origin` push + interactive slash commands; F3 branch not yet pushed at audit time per operator's "wait for the push" sequencing).

F3 is **merge-eligible but not merge-final** until check 9 is recorded green by an operator follow-up commit (sweep-notes amendment or follow-up referencing this F3 chain).

## Phase chain

| Phase | Commit | Summary |
|---|---|---|
| Phase 1 (intent) | `4bae8ec` | Intent committed (third revision after two operator-amendment RE_DISPATCHes — `d640ac6`, `33291ca` → final at `4bae8ec` against `caa7599` plan). |
| Phase 2 (failing tests) | `b287c23` | `tests/unit/test_migrate_from_symlink.py` — 8 named cases (a, b, c1, c2, c3, d, e, f); shellcheck (e) skips on this dispatch host (no `shellcheck` on PATH); dash (f) runs against `/bin/dash`. RED at this commit. |
| Phase 3 (implementation) | `23fcba3` | `scripts/migrate_from_symlink.sh` (executable, Bash 3.2 / dash compatible), `docs/upgrading-from-symlink.md` (new, six sections), `docs/upgrading-from-pre-compression.md` (`git rm`'d — replace branch survivor swap), `README.md` rewrite (four bullets per R.1), `CONSUMER.md` (URL placeholder fix + line-21 comment rewrite), `docs/ARCHITECTURE.md` (P.1 INV-011 cite append), `docs/roadmap.md` (F1.1 gated entry). GREEN at this commit. |
| Phase 4 (this sweep-notes) | (this commit) | Audit record. |

## Test results

**New suite (audit check 1): `uv run pytest tests/unit/test_migrate_from_symlink.py -v`**

```
collected 11 items

tests/unit/test_migrate_from_symlink.py::test_a_happy_path_exit_0_symlink_unlinked_settings_filtered PASSED
tests/unit/test_migrate_from_symlink.py::test_b_in_flight_skill_run_exit_2_no_state_change PASSED
tests/unit/test_migrate_from_symlink.py::test_c1_cairn_self_no_env_exit_3_with_required_stderr_tokens PASSED
tests/unit/test_migrate_from_symlink.py::test_c2_cairn_self_with_FORCE_still_exits_3 PASSED
tests/unit/test_migrate_from_symlink.py::test_c3_cairn_self_with_BREAK_INV011_proceeds_with_multiline_stderr PASSED
tests/unit/test_migrate_from_symlink.py::test_d_force_mode_quiescence_override PASSED
tests/unit/test_migrate_from_symlink.py::test_e_shellcheck_zero_warnings SKIPPED
tests/unit/test_migrate_from_symlink.py::test_f_dash_runtime_a_happy_path PASSED
tests/unit/test_migrate_from_symlink.py::test_f_dash_runtime_b_in_flight PASSED
tests/unit/test_migrate_from_symlink.py::test_f_dash_runtime_c1_cairn_self PASSED
tests/unit/test_migrate_from_symlink.py::test_f_dash_runtime_d_force_quiescence_override PASSED

10 passed, 1 skipped in 0.10s
```

- **Behavioural cases (a, b, c1, c2, c3, d):** 6/6 PASS.
- **Tooling-quality (e):** SKIPPED — `shellcheck` not on PATH (operator setup variance per FLI-5; manual end-to-end audit check 9 backstops missing static analysis).
- **Tooling-quality (f):** 4/4 PASS — script runs cleanly under `/bin/dash` against the four behavioural fixtures.

**Full suite (audit check 7): `uv run pytest -q --tb=no -rf`**

```
13 failed, 413 passed, 1 skipped, 2 xfailed in 13.01s
```

Baseline-vs-current diff against `/tmp/cairn-m6-f3-migration-and-symlink-retire-baseline-failures.txt` (14 failures captured at `c78f863`, validated unchanged through `caa7599`):

- **Newly passing (1):** `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` — moved baseline `FAIL → PASS`. Phase 3's doc-churn (README rewrite + CONSUMER.md edits + roadmap append) trimmed the turn-1 prompt below the 440-token budget. **Incidental positive signal**, not a regression.
- **New regressions (0):** `comm -13 baseline current` empty. No test failures observed beyond the baseline.

The +11 new passing count (413 vs baseline ~402) is the 10 GREEN tests in `test_migrate_from_symlink.py` plus the incidental INV-004 budget pass.

## Validator results

**`uv run python scripts/validate_architecture.py`** (audit check 6 part 2):

```
Validating ARCHITECTURE.md against ADR corpus...

FAILED — 1 issue(s):

  1. Check D: INV-002 FAIL — structural-parser: token budget exceeded:
     758 tokens (fail-at 440) in .claude/handoff.md
```

**Pre-existing — out of scope.** This is the same Check D / INV-002 failure documented in the F2 sweep-notes and the current `.claude/handoff.md` (line 20 names `TestSlice011AssertionCoverage` failures + INV-002 re-baseline as a known follow-up). The handoff token budget breach is structural to the surviving F2-era handoff prose; F3 did not write to `.claude/handoff.md` and did not introduce the breach. The `invariant-check INV-011` block at `docs/ARCHITECTURE.md:93–97` continues to validate (`type: file-exists; target: ".slice-system"` resolves green — see Invariant verification below).

## Invariant verification

| Invariant | Statement | Evidence (`file:line`) | Status |
|---|---|---|---|
| INV-011 | Cairn-the-repo retains `.slice-system → .` self-symlink (bootstrap exception); migration helper aborts exit 3 on self-symlink detection. | `readlink .slice-system` → `.` (audit check 6 part 1, run from cairn root). `docs/ARCHITECTURE.md:91` carries the prose with M6/F3 cite appended (verified verbatim — see audit check 4 below). `docs/ARCHITECTURE.md:93–97` carries `invariant-check INV-011 type: file-exists target: ".slice-system"` (machine check). `scripts/migrate_from_symlink.sh:69–104` enforces structural exit-3 on `readlink == "."`. | PASS |

### Per-check evidence

**Check 1 (new test suite passes).** See "Test results / New suite" above. 10 passed, 1 skipped (shellcheck unavailable). All 6 behavioural cases pass. PASS.

**Check 2 (`grep -n "fallback while" README.md` → 0 hits).**

```
$ grep -n "fallback while" README.md
(no output)
```

Maintainer carve-out present at `README.md:21`: "Cairn-the-repo itself retains a `.slice-system → .` self-symlink for maintainer dogfooding (INV-011, `docs/ARCHITECTURE.md`). This is a one-repo exemption — downstream consumers must NOT recreate it." INV-011 cited inline. PASS.

**Check 3 (replace-branch atomicity / FLI-2).**

```
$ git ls-files docs/upgrading-from-pre-compression.md docs/upgrading-from-symlink.md
docs/upgrading-from-symlink.md
```

Only the symlink doc is tracked; the pre-compression doc is `git rm`'d. PASS.

**Check 4 (F3 cite in INV-011 prose at `docs/ARCHITECTURE.md:91` — hard requirement per amendment 1).**

```
$ grep -n "F3\|M6/F3" docs/ARCHITECTURE.md
91: ... M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration:
    the `scripts/migrate_from_symlink.sh` helper aborts with exit 3 if it detects a
    self-symlink target of `.`, and the retire-docs sweep preserves cairn-the-repo's
    self-symlink documentation. ...
```

Cite is present at line 91 (the INV-011 prose line), names `scripts/migrate_from_symlink.sh` and exit 3 explicitly. P.1 was NOT denied — `reversibility-guard.sh` did not block the body-prose append at `docs/ARCHITECTURE.md` (the file is outside the ADR corpus). PASS — hard requirement satisfied without RAISE_ISSUE escalation.

**Check 5 (`grep -rn "\.slice-system" docs/ README.md CLAUDE.md`).** ~80 hits total. All hits classify into one of the allowed contexts:

- INV-011 prose / self-symlink mentions: `docs/ARCHITECTURE.md:91,95,96`; `docs/operational-reference.md:262,344,361,377`; `CLAUDE.md:13,20`; `README.md:20,21`.
- Migration runbook (the new `docs/upgrading-from-symlink.md`): lines 1, 4, 9, 20, 37, 40, 65, 94, 96, 105 — all consumer-context references to the legacy symlink, expected.
- `docs/lessons.md:229,327,333,362,376,378`: historical lessons (L-017 / L-018 / L-019 family) referencing the symlink in their named-mechanism prose.
- `docs/cairn-audit-2026-04-29.md` and `docs/reviews/2026-04-*-*.md`: historical audit / review docs (date-stamped, append-only by convention).
- `docs/roadmap.md:57`: pre-existing F-049 / Slice-3 prose (consumer-migration delta, predates F3).

No stale "downstream consumers should set up `.slice-system`" instructions remain in active consumer-facing docs. PASS.

**Check 6 (INV-011 directly verified).** `readlink .slice-system` → `.` (cairn-the-repo self-symlink unchanged). `invariant-check INV-011` at `docs/ARCHITECTURE.md:93–97` continues to resolve `file-exists target: ".slice-system"`. PASS.

**Check 7 (full suite — see "Test results" above).** 13 failed, all in baseline; 1 baseline failure newly passing; 0 new regressions. PASS.

**Check 8 (URL placeholder + comment rewrite + roadmap entry).**

```
$ grep -n "<marketplace-url>" CONSUMER.md README.md
(no output)

$ grep -n "validator stdout literal lands in F1's PR" CONSUMER.md
(no output)

$ grep -n "validator stdout" docs/roadmap.md
71:- **F1.1 / post-install validator stdout literal** — gated on first real
   consumer-side `/plugin install` data. ...
```

`<marketplace-url>` placeholder fully resolved (FLI-7). The line-21 F1-followup comment in `CONSUMER.md` rewritten to obviously-intentional ("F1-followup (intentional, separately tracked): validator stdout literal lands in F1.1. See docs/roadmap.md or .claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md."). The validator-stdout-literal line at `CONSUMER.md:22` (`uv run python scripts/validate_plugin_install.py`) is **untouched** as designed (separately tracked F1.1-followup). The roadmap entry at `docs/roadmap.md:71` cross-references both `CONSUMER.md:20–22` and this sweep-notes file. PASS.

## Adjacent code regression check

Eyeball pass against the seven Phase-3-touched paths.

- **`scripts/migrate_from_symlink.sh`** (read in full, 201 lines).
  - **FLI-1 (asymmetric force overrides).** `CAIRN_MIGRATE_FORCE` checked at line 125 — gates exit 2 (quiescence) only. `CAIRN_MIGRATE_BREAK_INV011` checked at line 77 — gates exit 3 (cairn-self) only with multi-line stderr block at lines 80–87 (≥3 lines, cites INV-011 / D8 / `docs/ARCHITECTURE.md:91`). Asymmetry confirmed by case (c2) — `CAIRN_MIGRATE_FORCE=1` alone still exits 3. PASS.
  - **FLI-3 (exit codes 0, 2, 3 only).** Three explicit `exit` statements: line 61 (idempotent re-run, exit 0), line 102 (cairn-self refusal, exit 3), line 152 (quiescence refusal, exit 2), line 200 (success, exit 0). No exit 1 / exit 4+ surface. PASS.
  - **FLI-4 (no slash-command chaining).** Banner at lines 39–52 names the slash commands as **manual next steps** (`log_out` only, no shell invocation of `/plugin marketplace add` or `/plugin install`). PASS.
  - **FLI-5 (POSIX-only surface).** No `mapfile` / `readarray`; all conditionals use `[ ]` (single-bracket, not `[[ ]]`); no process substitution `<()` / `>()`; `printf '%s' "$non_quiesced" | while IFS= read -r p` (line 132) is the POSIX-portable per-line iteration idiom; no GNU-only flags (`-printf`, `-Z`, `--quoting-style`, etc.). Dash runtime case (f) — 4/4 PASS — empirically confirms portability. PASS.
  - **FLI-7 (literal URL).** Banner line 45: `/plugin marketplace add https://github.com/firaaz/cairn` (literal, no placeholder token). PASS.

- **`docs/upgrading-from-symlink.md`** (read in full, 130 lines). All six sections present: §1 Quiescence preflight (lines 14–31, names Pre-mortem Scenario 6 + the verbatim warning string), §2 Atomic swap (lines 33–70, four steps with literal URL inline at line 49), §3 Session restart (lines 72–77, agent-registry reload requirement), §4 State preservation (lines 79–97, eight-item survives + two-item goes-away enumeration), §5 Rollback (lines 99–112, re-create-symlink path + `git checkout HEAD -- .claude/settings.json`), §6 Smoke test (lines 114–129, validator + trivial dispatch + envelope-grants.log check). Maintainer carve-out callout at lines 8–12 cites INV-011 + `docs/ARCHITECTURE.md:91` + the script's exit-3 behaviour. PASS.

- **`README.md`** (read in full, 43 lines). Four-bullet R.1 block at lines 17–21:
  - Line 19: first-time-consumer block with literal URL ("Run `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`").
  - Line 20: migration block linking to `docs/upgrading-from-symlink.md`.
  - Line 21: maintainer carve-out citing INV-011.
  - Fallback-framing prose, the prior `ln -s` block, the hook-configuration paragraph, and the `F3-followup:` self-reference comment all removed. PASS.

- **`CONSUMER.md`** (read in full, 81 lines). Install block at lines 13–15 carries the canonical two-step (literal URL). Line 21 comment rewritten to the obviously-intentional F1-followup form. Line 22 (`uv run python scripts/validate_plugin_install.py`) untouched — validator-stdout-literal is the separately tracked F1.1 follow-up by amendment-6 design. PASS.

- **`docs/ARCHITECTURE.md`** (line 91 + lines 93–97 read). M6/F3 cite appended to INV-011 prose verbatim per intent §Specification "P.1". The cite cleanly threads into the existing prose ("Plugin consumers are unaffected … M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration: `scripts/migrate_from_symlink.sh` aborts exit 3 …"). The trailing `(m5-plugin-distribution-and-symlink-retire; bootstrap-exception)` ADR-cite parenthesis preserved. PASS.

- **`docs/roadmap.md`** (line 71 read). New `## Gated` bullet "F1.1 / post-install validator stdout literal" cross-references `CONSUMER.md:20–22` + this sweep-notes path. Heading-class anchor matches intent's principled-placement spec. PASS.

- **`docs/upgrading-from-pre-compression.md`** — `git rm`'d (verified by `git ls-files`, audit check 3 above). PASS.

## Pending manual verification — audit check 9

Phase 4 cannot run check 9 in this dispatch — it requires:

1. The F3 branch (or a tagged commit on it) pushed to `origin` (https://github.com/firaaz/cairn).
2. A fresh Claude Code session in a throwaway fixture project (any non-cairn directory the operator picks).
3. Interactive slash-command invocation:

```
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

4. Operator confirms hooks fire (`reversibility-guard.sh`, `role_guard.py`, `reality-check.sh` all present and active in the fresh session).
5. Operator runs `scripts/postinstall_validate.py` (or equivalent under the plugin install tree) and confirms clean exit.

**Recording protocol (per intent §Verification check 9):** the operator's follow-up commit either amends this sweep-notes (changing verdict to `PASS`) or lands a follow-up commit referencing this F3's commit chain with the manual-end-to-end result. Until then F3 is **merge-eligible but not merge-final**.

**Why deferred:** Operator at session start: "Wait for the push, right now just start f3 in a branch." The branch has not been pushed; check 9 cannot run.

## Notes / observations

- **Phase-1 RE_DISPATCH chain (traceability).** The intent went through three drafts: `d640ac6` (initial) → `33291ca` (operator amendment for `<marketplace-url>` placeholder + README fallback drop) → `4bae8ec` (operator amendment for the six-amendment set: P.1 hard-requirement, Risk-Surface item 2 settings.json shape grounding, audit check 9 manual end-to-end, shellcheck / dash automated checks with graceful skip, asymmetric force overrides with `CAIRN_MIGRATE_BREAK_INV011`, validator-stdout-literal comment-rewrite + roadmap breadcrumb). All three amendments are observable in F3's deliverable inventory and verification surface.
- **Incidental INV-004 token-budget pass.** `test_inv004_turn1_token_budget` flipped from baseline-FAIL to PASS in the full-suite run. Mechanism: Phase 3's doc churn (README rewrite + CONSUMER.md edits + roadmap append) trimmed the turn-1 prompt below the 440-token budget. **Not** an F3 deliverable — recorded as a positive incidental signal.
- **Risk Surface item 8 (env-var-name typo) — structural mitigation landed.** Cannot test directly (typos are by definition out-of-band), but the script's exit-3 stderr at `scripts/migrate_from_symlink.sh:99–101` names the literal token `CAIRN_MIGRATE_BREAK_INV011` so a typo'd override is greppable in shell history. Phase 2 case (c1) asserts the literal substring is in stderr. PASS structurally.
- **Settings.json shape drift (Risk Surface item 2).** The `jq` filter is grounded against cairn's own `.claude/settings.json` (Phase 1 intent §Specification verified directly). Real `complex-rag-analysis` shape drift is an explicit residual risk caught only by audit check 9 / runbook §6 smoke test — not Phase 4-blocking.
- **Validator pre-existing failure.** `validate_architecture.py` reports INV-002 FAIL (handoff token budget). Pre-existing per `.claude/handoff.md:20` (F2's known follow-up); F3 did not author handoff.md and did not introduce it.
- **Workspace artefact integrity.** Workspace `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/` carries `intent.md`, `validation/approach.md`, and (post-this-commit) `integration/sweep-notes.md`. Each phase's artefact landed in the expected per-phase subdir.

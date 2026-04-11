---
slice: validator-symlink-fix
phase: 4-integration
date: 2026-04-11
gate-at-entry: implementation committed at d06fb64, working tree clean on envelope files
---

# Phase 4 Integration — SLICE-001

## Gate validation

**PHASE 3 GATE CONFIRMED.** Implementation committed at `d06fb64` (`slice: validator-symlink-fix — phase 3 implementation`). `git status --short` on the envelope files (`scripts/validate_architecture.py`, `tests/unit/test_validate_architecture.py`, `CHANGELOG.md`) returned empty — no uncommitted changes. The only untracked file in the working tree is `docs/2026-04-11-review-from-rag-session.md`, which is explicitly out of envelope and remains untouched by Phase 4.

## Test-suite evidence

### Slice-specific suite
Command: `uvx pytest tests/unit/test_validate_architecture.py -v`

Result (fresh run, this session):
```
collected 6 items

tests/unit/test_validate_architecture.py::test_v1_cairn_self_dogfood_baseline PASSED [ 16%]
tests/unit/test_validate_architecture.py::test_v2_consumer_via_symlink_with_env_var PASSED [ 33%]
tests/unit/test_validate_architecture.py::test_v3_consumer_via_symlink_no_env_var PASSED [ 50%]
tests/unit/test_validate_architecture.py::test_v4_consumer_invoked_from_subdirectory PASSED [ 66%]
tests/unit/test_validate_architecture.py::test_v5_consumer_with_broken_substrate PASSED [ 83%]
tests/unit/test_validate_architecture.py::test_v6_resolution_failure_no_viable_root PASSED [100%]

============================== 6 passed in 0.53s ===============================
```

**6 passed / 0 failed.** V1–V6 all green.

### Full suite
Command: `uvx pytest`

Result: `6 passed in 0.40s`. Collected item count matches the slice suite — cairn has no other test files today. No unexpected new tests appeared.

### Validator self-dogfood (V7 integration regression)
Command: `python3 scripts/validate_architecture.py` from cairn repo root.

Result:
```
Validating ARCHITECTURE.md against ADR corpus...

ALL CHECKS PASSED
  Invariants verified: 1
  ADR files checked: 1
```
Exit 0. V7 passes — the 1-invariant / 1-ADR substrate that ADR-001 relied on is intact.

(Note on runner: the Phase 3 handoff contract permitted either `uv run --no-project python scripts/validate_architecture.py` or plain `python3 scripts/validate_architecture.py` — cairn has no `pyproject.toml` and should not acquire one. Plain `python3` was used here. The observable contract — exit 0, `ALL CHECKS PASSED`, `Invariants verified: 1`, `ADR files checked: 1` — does not depend on the runner.)

## Invariant verification table

`intent.md` declares `invariants-touched: []`. This slice touches no invariants in `docs/ARCHITECTURE.md`, so the per-invariant verification table is empty by design:

| INV | Statement | Status | Evidence |
|-----|-----------|--------|----------|
| (none declared) | — | — | — |

The sole invariant in cairn's architecture (INV-001: "all cairn development after the bootstrap commit flows through `/decision` or `/start-slice`") is unrelated to validator resolution and is not affected by this slice's changes.

## ADR-001 alignment check

`adrs-referenced: [ADR-001]`. Read ADR-001 briefly to confirm no contradiction.

- ADR-001 records the `.slice-system → .` self-symlink as a known path-canonicalization hazard and explicitly defers a scope-guard fix "for a future slice, not for this ADR." It does not prescribe a root-resolution mechanism for the validator.
- SLICE-001's chosen mechanism (`CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel` → exit 2 with diagnostic) is compatible with all four contexts in intent.md, including cairn's self-dogfood. In the cairn-self case, `git rev-parse --show-toplevel` from cairn root returns cairn root directly — the cwd does not route through the self-symlink, so no canonicalization is forced. V1 covers this empirically.
- ADR-001's consequence "the substrate validator's Check B is satisfied on commit #1" is preserved: cairn's 1-invariant / 1-ADR pair still passes all three checks (confirmed above).
- `adrs-created: []` in slice.yaml is correct. No new ADR needed.

## Off-intent fixture edit verification

Phase 3 edited `_make_consumer_project()` in `tests/unit/test_validate_architecture.py` (not just the implementation). This was flagged in the Phase 3 handoff as a soft-line crossing requiring Phase 4 attention. Verified independently via `git diff 570386a d06fb64 -- tests/unit/test_validate_architecture.py`.

The diff touches exactly three things in the fixture builder:
1. `**TMP-{i:03d}**` → `**INV-{i:03d}**` in ARCHITECTURE.md lines (required because the validator's invariant-parser hard-codes the `INV-` prefix and is out of scope for this slice).
2. ADR-sweep rule when `adrs > invariants`: extra ADRs get appended to the first invariant's references (required because Check B rejects orphaned firm/accepted ADRs).
3. `invariants-touched: [TMP-{i:03d}]` → `[INV-{i:03d}]` in ADR frontmatter (consistency with #1).

**No `assert` statement in any test was modified by Phase 3.** The diff shows only fixture construction edits.

The three assertions flagged in the Phase 3 handoff, checked directly against intent.md's Verification section:

| Test | intent.md requirement | Test assertion | Status |
|------|----------------------|----------------|--------|
| V2 (`test_v2_consumer_via_symlink_with_env_var`, line 188) | Output references the tmp project's invariants, not cairn's; exit code 0 | `assert count == 2` (cairn has 1 invariant, tmp fixture has 2) + `returncode == 0` + `"ALL CHECKS PASSED" in result.stdout` | **preserved** — count-distinguishing is anti-leak-equivalent to identifier-distinguishing because cairn's count is 1, so any reading of cairn's substrate would produce `count == 1 != 2`. |
| V5 (`test_v5_consumer_with_broken_substrate`, lines 273, 278, 281–282) | Nonzero exit on broken tmp substrate; failure references the tmp project, not a cairn false-green | `returncode != 0` + `"ALL CHECKS PASSED" not in result.stdout` + `any(m in combined for m in ("TMP-", "ADR-9"))` | **preserved** — all three clauses unchanged from Phase 2, independently re-verified. |
| V6 (`test_v6_resolution_failure_no_viable_root`, lines 314, 319, 323) | Nonzero exit; no false-green; no silent read of cairn | `returncode != 0` + `"ALL CHECKS PASSED" not in result.stdout` + **`"Invariants verified: 1" not in result.stdout`** | **preserved** — the load-bearing anti-leak assertion (cairn has 1 invariant, so the literal substring `Invariants verified: 1` in stdout would prove a silent read of cairn) is intact. |

**Phase 3's fixture edit did not weaken any assertion.** The soft-line crossing is acceptable.

### Secondary observation (informational, does not block Phase 4)

V5 and V6 use `returncode != 0` while intent.md's Verification section specifies exact exit codes (V5 → `1`, V6 → `2`). This is a **Phase 2 design decision** (present in commit `570386a`, unchanged by Phase 3), applying the same property-over-wording principle that Phase 3 handoff noted for V6. The semantic property — "validator did not silently produce a cairn false-green" — is preserved. A stricter exit-code assertion would be a Phase 2 tightening, not a Phase 4 regression, and is out of scope for this integration check.

The implementation does produce the contracted exit codes: `main()` on Check A/B/C failure exits `1` (line 280 of `scripts/validate_architecture.py`), and `_resolve_project_root()` on unresolvable root exits `2` (line 72). So the looser assertions under-constrain the implementation but do not let an incorrect implementation pass.

## Adjacent-module regression check

The envelope is narrow: one script file, one test file, one changelog. Checked the blast radius:

1. **No Python module imports `validate_architecture`.** Grep for `from scripts|import scripts|import validate_architecture|from validate_architecture` across the repo returned no matches. The validator is a CLI script, not a library — there are no transitive Python dependents to regress.

2. **Three slash commands reference the validator** as a subprocess invocation:
   - `commands/claude-code/start-slice.md:69` — Phase 4 step: `uv run python .slice-system/scripts/validate_architecture.py`
   - `commands/claude-code/status.md:42` — status dashboard
   - `commands/claude-code/refresh-architecture.md:60` — post-refresh validation

   The intent explicitly commits to preserving the CLI invocation pattern ("no new flags, no changed flags"). All three callsites remain valid: the script still takes no arguments, no new flags, and produces the same `ALL CHECKS PASSED` / `FAILED` stdout format on success / Check-A-B-C failure paths. The only new behavior is a stderr diagnostic on resolution failure (exit 2), which these slash commands do not test for and would simply surface to the user as-is. No regression.

3. **Imports added this phase**: `os`, `subprocess`. Both stdlib, both already used elsewhere in the repo indirectly. No new third-party dependencies.

4. **Full test collection is 6 items**, all from `test_validate_architecture.py`. No other test file exists — nothing else to regress.

5. **`checks/*.sh` hooks**: explicitly out of scope per `intent.md`. Grep confirms none of the hook scripts reference the validator. The scope-guard canonicalization hazard documented in `CLAUDE.md` is a separate concern (a different slice).

6. **`docs/ARCHITECTURE.md` and `docs/adr/*`**: untouched by this slice. Consumers of those documents (`/status`, `/refresh-architecture`) continue to work since the validator output format is unchanged.

**No adjacent-module regressions.**

## Summary

| Check | Result |
|-------|--------|
| Phase 3 gate (implementation committed, working tree clean on envelope) | PASS |
| Slice suite (`uvx pytest tests/unit/test_validate_architecture.py -v`) | PASS — 6/6 in 0.53s |
| Full suite (`uvx pytest`) | PASS — 6/6 in 0.40s |
| Validator self-dogfood (`python3 scripts/validate_architecture.py`) | PASS — exit 0, `ALL CHECKS PASSED`, 1 invariant, 1 ADR |
| Invariant verification (`invariants-touched: []`) | N/A — empty by design |
| ADR-001 alignment | no contradiction; `adrs-created: []` correct |
| Off-intent fixture edit verification | no assertion weakened; soft-line crossing acceptable |
| Adjacent-module regression check | no regressions |

**PHASE 4 PASS.** SLICE-001 `validator-symlink-fix` is ready to be marked `complete`.

## Observations for downstream consumers

Not blocking, but worth recording:

- **Phase 2's property-over-wording stance on exit codes** (V5/V6 using `!= 0` instead of `== 1`/`== 2`) is an intentional design pattern, not a gap. Future Phase 2 reviewers should decide whether to keep this or tighten it based on whether the exit-code distinction carries information callers rely on. As of today no caller branches on exit code 1 vs 2.
- **The `uv run python` pattern in slash commands** (`start-slice.md:69`, `status.md:42`, `refresh-architecture.md:60`) will prompt for project initialization when run in cairn itself because cairn has no `pyproject.toml`. This is latent today (cairn's own slice pipeline isn't wired up yet) and will surface once the meta-dogfood is active. Not part of this slice's scope — flagged for whoever owns the cairn-pipeline-wiring slice to decide between `uv run --no-project python`, `python3`, or adding `pyproject.toml` (the last of which the Phase 3 handoff explicitly warned against).
- **The `.claude/current-slice/integration/` directory did not exist before this phase.** Created as part of Phase 4. The scope-guard default allowlist covers `.claude/current-slice/*`, so no envelope expansion was needed.

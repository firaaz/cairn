---
slice: SLICE-014
phase: 4-integration
auditor-session: 2026-04-15
pre-slice-baseline: bc6acb1 (handoff: SLICE-013 failed, SLICE-014 planned)
head: ed8f263 (handoff: SLICE-014 phase 3 complete, ready for phase 4 integration)
verdict: PASS (with 1 spec-level follow-up noted under V1)
---

## Invariant Evidence Table

Phase 4 verification per `intent.md:80-90` (§Verification — Definition of Done).

| # | Check | Command | Verdict | Evidence |
|---|---|---|---|---|
| V1 | Ruff clean on both test files, no E402/E741/suppressions | `python3 -m ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` | PASS-with-note | Literal intent.md command non-executable in cairn env (CLAUDE.md:7 prescribes `uv tool install ruff` → standalone CLI, no `ruff` Python module). Equivalent `ruff check <files>` → `All checks passed!`, EXIT=0. Integration gate Step 4a (V3) independently confirms ruff clean. See §V1 Discrepancy below. |
| V2 | Pytest exit 0, all pass, imports resolve via pythonpath | `python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py -v` | PASS | `58 passed in 1.80s`, exit 0. `configfile: pyproject.toml` confirms pytest picked up `[tool.pytest.ini_options]`. Imports in `test_invariant_assertions.py:27` (`from validate_architecture import parse_assertion_blocks, parse_invariants`) resolve — pytest output shows no ImportError, all 44 assertion-related tests PASSED. |
| V3 | integration_gate.py steps 3/4a/4b pass without bypass | `python3 scripts/integration_gate.py` | PASS | Output: `Step 3 (invariant check): PASS / Step 4a (ruff check): PASS / Step 4b (pytest): PASS`, exit 0. No bypass required. |
| V4 | snapshot_diff confined to envelope + `.claude/current-slice/` | `python3 scripts/snapshot_diff.py --diff` | PASS | Exit 0, empty stdout — no out-of-envelope drift detected. |
| V5 | git diff shows no changes outside envelope | `git diff bc6acb1..HEAD --name-only` (committed); `git diff HEAD --name-only` (uncommitted); `git ls-files --others --exclude-standard` (untracked) | PASS | 12 committed files, all in envelope: 3 declared (`pyproject.toml`, 2 test files) + 8 slice artifacts (`.claude/current-slice/**`) + `.claude/handoff.md` (expected cross-phase). 1 uncommitted (`docs/plans/measurements/2026-04-12-slice-003.txt`) and 2 untracked (`.claude/worktrees/fervent-mcnulty/`, `docs/plans/2026-04-14-brainstorming-formalization-exploration.md`) are pre-existing per `handoff.md:17-18` — not attributable to SLICE-014. |
| V6 | No new d3-bypasses.log entries at slice-close | `cat .claude/d3-bypasses.log \| wc -l` | PASS | 1 line total. Line is SLICE-012 entry dated 2026-04-14 — pre-existing, not SLICE-014. No new entries appended during SLICE-014. |
| V7 | pyproject.toml only `[tool.pytest.ini_options]` with single `pythonpath` key | Read `pyproject.toml` | PASS | File is exactly 2 lines: `[tool.pytest.ini_options]` (L1) and `pythonpath = ["scripts"]` (L2). No additional sections or keys. |

## V1 Discrepancy — Verification Command Spec vs Environment

**Fact:** `intent.md:84` literal command `python3 -m ruff check ...` exits 1 with stderr `No module named ruff` in this environment. The integration gate (V3 Step 4a) and a direct `ruff check` invocation both exit 0 with zero violations on the same two files.

**Root cause:** CLAUDE.md:7 prescribes `uv tool install ruff`, which installs a standalone CLI binary on PATH but does not register a `ruff` module importable via `python3 -m`. The intent-phase author wrote a `python3 -m ruff` form that assumes `pip install ruff` semantics.

**Auditor judgment:** Implementation is NOT wrong. The underlying invariant ("ruff reports zero violations on the two test files post-slice") is met by independent evidence (V3 Step 4a + direct CLI). Per `docs/operational-reference.md:70`, Phase 4 fails only when the implementation is wrong — which is not the case here.

**Recommendation (out of Phase 4 scope, flagged for follow-up):** Update the Phase 1 intent template and/or any cairn doc that models verification commands to use `ruff check ...` (CLI form) rather than `python3 -m ruff check ...`. This is a documentation-spec defect, not a slice-004 problem.

**Disposition:** V1 marked PASS-with-note. Slice does NOT fail on this.

## Overall Verdict: PASS

All 7 declared verification items met by evidence. SLICE-014 achieves its stated goal:
- Eliminates two D3 bypasses (E402 + E741) that SLICE-012 logged and SLICE-013 failed to address.
- Introduces `pyproject.toml` with minimal config (`pythonpath = ["scripts"]`) so validator imports resolve at module-level rather than via runtime `sys.path` injection.
- `.claude/d3-bypasses.log` pre-existing SLICE-012 entry can now be considered cleared (the underlying lint violations are gone); operator's call whether to prune the log or leave it as historical record.

## Follow-ups for Human Operator

1. **V1 command-spec fix** — edit Phase 1 intent template so future slices default to `ruff check` CLI form instead of `python3 -m ruff`.
2. **Stashed SLICE-013 edits** — `git stash list` top entry can be discarded now per `handoff.md:16`.
3. **d3-bypasses.log SLICE-012 entry** — pre-existing entry is now obsolete (its cause is fixed). Operator decides whether to prune or leave for audit history.
4. **Pre-existing working-tree drift** (not SLICE-014) — `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted since before SLICE-010, and 2 untracked files listed in `handoff.md:17-18`. Unrelated to this slice but worth addressing in a housekeeping pass.

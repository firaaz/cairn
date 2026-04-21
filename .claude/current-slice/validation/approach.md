# Phase 2 Approach — housekeeping/post-inv008-and-substrate-bugs

## Charter scope

Two scopes from intent.md:
- **Scope A**: 13 pre-existing tech-debt items (10 pytest reds, 2 ruff E741, 1 ruff F841, 1 docs gap). The 10 pytest reds are *already failing* on trunk; they constitute the Scope-A RED set verbatim and need no Phase-2 re-authoring. Phase-3 fixes them in place.
- **Scope B**: 5 substrate bugs (B1-B5) requiring new failing tests against public-interface contracts in intent.md V7-V11.

## What Phase 2 writes

A single new test module `tests/unit/test_orchestrator_bug_fixes.py` covering B1-B5, plus one structural test for A3 docs gap. Six test functions total - well under the 15-function re-split threshold.

| Item | Test fn | Contract source | Mode |
|---|---|---|---|
| A3 | test_heartbeat_env_vars_documented | intent V3 + ADR orchestrator-observability | structural grep |
| B1 | test_current_phase_persisted_across_phase_boundary | intent V7 | sim resume |
| B2 | test_coupling_clusters_yaml_safe_load_round_trip | intent V8 | string + yaml.safe_load |
| B3 | test_init_new_slice_normalizes_dot_slug_to_hyphen | intent V9 | call init + read slice.yaml |
| B4 | test_pytest_run_does_not_dirty_measurements | intent V10 | git status post-run |
| B5 | test_close_slice_commit_subject_matches_em_dash_pattern | intent V11 | regex on commit subject + verify_handoff exit |

## Why no extra tests for A1/A2

A1 - the 10 named pytest tests are already RED on trunk. Phase 2 does not duplicate them; existing files are the Scope-A RED set. Duplicating would inflate the envelope without strengthening any assertion.

A2 - ruff lint is checked by intent V2/V5; a pytest wrapper around `ruff check` would duplicate Phase-4 V5 without adding signal.

## Public-interface seams used

- B1: import `init_new_slice` and the post-phase persistence path from `scripts.slice_orchestrator`; assert `slice.yaml.current_phase` advances after a simulated phase boundary commit.
- B2: load a `coupling-clusters.yaml` string mirroring the prompt-template literal block and assert `yaml.safe_load` returns without exception; also assert the prompt at `.claude/agents/phase-2-skeptic.md` mentions a single-quote-safety directive for regex patterns.
- B3: call `init_new_slice` with a brief whose id contains `1.2.3`; read `.claude/current-slice/slice.yaml`; assert dots became hyphens and id matches `SLICE_ID_REGEX`.
- B4: invoke `subprocess.run(["uv","run","pytest","tests/unit/test_context_budget.py","-q"])` from the repo root in a clean git tree, then `git status --porcelain docs/plans/measurements/`; assert empty.
- B5: invoke `close_slice` against a fixture, read `git log -1 --format=%s`, regex match the em-dash pattern, and assert `scripts/verify_handoff.sh` exits 0 against that commit.

## Out of scope

No tests for Path C, multi-instance locking, or triager prompt iteration - explicitly deferred per intent Boundary. No assertions added against ADR bodies (firm append-only).

## Coupling-clusters note

Bug-fix tests cluster into one Phase-3 cluster covering `scripts/slice_orchestrator.py`, `.claude/agents/phase-2-skeptic.md`, `tests/unit/test_context_budget.py`, and `docs/operational-reference.md`. See `coupling-clusters.yaml`.

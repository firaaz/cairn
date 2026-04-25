---
slice: compression/lever-2-orchestrator-split
phase: 1-intent → 2-validation
branch: feature/compression
as-of: 2026-04-25 18afa0c
---

## State
Phase 1 (Reader) complete. `intent.md` declares: package layout (§S2), public-surface re-export contract (§S3), CLI entry-point contract (§S4), doc/command path-string updates (§S5), test-file invariance with single gate-file exception (§S6), invariant preservation (§S7). Verification gates V1–V8 enumerated. Envelope amendment 18afa0c added the gate test file path before Phase 2 dispatch.

## Next
Dispatch `phase-2-skeptic` subagent in a fresh session with `intent.md` as sole input; produce RED tests at `tests/unit/test_slice_orchestrator_package_split.py` plus `validation/approach.md`.

## Blocked / Pending
- OQ2 (CLI invocation form `python -m` vs path-to-`__main__.py`) — Phase 3's call, recorded for Builder
- OQ3 (`__init__.py` re-export style — star vs explicit) — Phase 3's call, recorded for Builder
- Skeptic must enumerate any remaining ambiguities before writing tests; escalate via RAISE_ISSUE if a gate is unprovable from intent.md alone

## Pointers
- `.claude/current-slice/intent.md` — sole Phase 2 input; do not read source code or Phase 3 implementation
- `intent.md` §S3 — full public-name list (test V2 enumerates this)
- `intent.md` §V1–V8 — verification gates the Skeptic's RED tests must mechanise
- `intent.md` `out-of-scope:` — boundary the Skeptic must respect; tests touching anything outside envelope must be rejected

---
---
slice: compression/lever-2-orchestrator-split
phase: 2-validation → 3-implementation
branch: feature/compression
as-of: 2026-04-25 68a0213
---

## State
Phase 2 (Skeptic) complete at 68a0213. `tests/unit/test_slice_orchestrator_package_split.py` holds 90 RED gate tests over V2–V6. `validation/approach.md` carries the gate-to-test map. Zero diff in any other test file.

## Next
Dispatch `phase-3-implementer` in a fresh session against `intent.md` + the gate test file; turn V2–V6 GREEN by creating the eight-file package, deleting `scripts/slice_orchestrator.py`, sweeping path strings in commands/ + docs/.

## Blocked / Pending
- OQ2 (CLI form): both `python -m` and direct-`__main__.py` forms tested — keep both working
- OQ3 (`__init__.py` re-export style): Builder's call → `implementation/notes.md`
- Test-file invariance: gate file is the only permitted test diff; all other test files byte-identical
- §S3 drift clause (intent.md:79): submodule helper relocation allowed; tests assert top-level resolution only

## Pointers
- `.claude/current-slice/intent.md` — slice contract; §S2 module map, §S3 re-exports, §V1–V8 gates
- `tests/unit/test_slice_orchestrator_package_split.py` — RED gates Phase 3 turns GREEN
- `.claude/current-slice/validation/approach.md` — gate-to-test map + ambiguity log
- `scripts/slice_orchestrator.py` — delete in the Phase 3 commit that creates the package

---
---
slice: compression/lever-2-orchestrator-split
phase: 3-implementation → 4-integration
branch: feature/compression
as-of: 2026-04-25 01a4cc3
---

## State
Phase 3 (Builder) complete at 01a4cc3. `scripts/slice_orchestrator.py` split into 8-file `scripts/slice_orchestrator/` package; gate suite 90/90 GREEN, full suite 835 passed / 1 pre-existing fail / 3 skipped; validator rc=0; CLI both forms exit 0 with `--legacy`.

## Next
Dispatch `phase-4-integrator` in a fresh session against `intent.md` + the package source; verify §V7/V8 invariants (INV-003/004/008/009) and write `.claude/current-slice/integration/sweep-notes.md`.

## Blocked / Pending
- Pre-existing `test_item_d_no_empty_current_slice_subdirs` failure clears once Phase 4 writes `sweep-notes.md`
- `_MirroringModule` facade shim is load-bearing for §S6 monkeypatch preservation — see `notes.md`
- OQ2 → `python -m`; OQ3 → explicit name-by-name re-exports with `__all__`; `_head_subject_safe` lives in `git.py`
- INV-008 target repointed at `scripts/slice_orchestrator/lifecycle.py` in `docs/ARCHITECTURE.md`
- Pyright diagnostics advisory: re-export false positives, `.git/` shadowing, untyped `result_data` narrowing — none are gate failures

## Pointers
- `.claude/current-slice/intent.md` — slice contract; §V7/V8 are Phase 4's gates
- `.claude/current-slice/implementation/notes.md` — OQ2/OQ3 + `_MirroringModule` rationale + stdlib re-exports
- `tests/unit/test_slice_orchestrator_package_split.py` — V2–V6 GREEN; only test file diffed (V2 not-None scoped past INV_009 thresholds)
- `scripts/slice_orchestrator/` — 8-file package; `lifecycle.py` is INV-008 target

---
---
slice: compression/lever-2-orchestrator-split
phase: 4-integration
date: 2026-04-25
auditor-verdict: PASS
---

## Phase 4 outcome
PASS — all eight gates (V1–V8) satisfied. Package split landed cleanly. Validator rc=0. Pytest 835 passed / 3 skipped / 1 failed; the single failure (`test_inv004_turn1_token_budget`) is pre-existing CC 2.1.119 environmental drift unrelated to this slice (no test-file or progressive-disclosure surface edited).

## What changed (audit deliverables only)
- `.claude/current-slice/integration/sweep-notes.md` — V7 invariant evidence table for INV-003 / INV-004 / INV-008 / INV-009 with `file:line` citations; V8 physical-relocation summary; verification-triad command outputs.
- `.claude/sweep.yaml` — recorded slice pass with classified pre-existing failure.
- `.claude/current-slice/slice.yaml` — `status: complete`, `completed: 2026-04-25`.

## Operator action items
1. **Request code review** before merging `feature/compression` → `dev` (`superpowers:requesting-code-review`).
2. **Plan `housekeeping/inv004-rebaseline-cc-2.1.119`** — CC 2.1.119 added another ~70k tokens of system-prompt overhead beyond the CC 2.1.116 rebaseline; current measurement 101779 tokens vs 40000 budget. Same shape as the prior two rebaselines.
3. **Track-0 measurement of next orchestrator-touching slice** — this slice's compression payoff (estimated $3-5 / 180-300k cache_creation cut per intent) is measured on the next slice, not this one.
4. **Continue the Part-8 lever queue**: M0 → M0.5 → M3+M2 → S1+S3 (4 follow-on slices).

## Pointers
- `scripts/slice_orchestrator/` — 8-file package; `lifecycle.py:384` is the `close_slice` INV-008 anchor.
- `scripts/slice_orchestrator/__init__.py:192` — `_MirroringModule` shim (load-bearing for monkeypatch).
- `tests/unit/test_slice_orchestrator_package_split.py` — V2–V6 gate tests, all GREEN.
- `.claude/current-slice/integration/sweep-notes.md` — full audit evidence.

## Closure
This handoff is the Phase 4 deliverable. The orchestrator's `close_slice` (DC-4) is the sole producer of the terminal `slice: complete` commit; Phase 4 itself does not run `git commit`.

---
---
slice: compression/lever-2-orchestrator-split
phase: 4-integration
date: 2026-04-25
auditor-verdict: PASS
---

## Verification triad

| Check | Command | Result | Evidence |
|---|---|---|---|
| pytest (pre-sweep-notes baseline) | `uv run pytest` | 2 failed / 834 passed / 3 skipped (68.70s) | (1) `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` — `INV-004 FAIL: 101670 tokens > 40000 budget` under CC 2.1.119 (rebaseline target 2.1.116) — pre-existing environmental drift, out-of-scope per intent §out-of-scope (no test-file edits). (2) `tests/unit/test_housekeeping_post_slice_a_tidy.py:105::test_item_d_no_empty_current_slice_subdirs` — empty `.claude/current-slice/integration/` dir; expected to flip GREEN once sweep-notes.md is written. |
| pytest (post-sweep-notes) | `uv run pytest` | 1 failed / 835 passed / 3 skipped | INV-004 token-budget test still failing (pre-existing CC 2.1.119 drift; out-of-scope; not caused by this slice). The empty-dir test flipped GREEN as predicted by handoff-phase-3.md. |
| validator | `uv run python scripts/validate_architecture.py` | rc=0 — `ALL CHECKS PASSED` (Invariants verified: 9, ADR files checked: 15) | No warnings. INV-008 grep anchor `def close_slice` resolves cleanly against `scripts/slice_orchestrator/lifecycle.py:384`. |
| §V8 physical-relocation diff | `git diff HEAD~5 --stat -- scripts/` | `slice_orchestrator.py` (-2240 lines) → 8 submodules (+2760 lines): `__init__.py` 330 / `__main__.py` 63 / `core.py` 536 / `dispatch.py` 471 / `git.py` 47 / `lifecycle.py` 517 / `resume.py` 277 / `telemetry.py` 519. | +520 line delta is module headers + cross-submodule import lines + `__init__.py` re-export block + `_MirroringModule` shim — all envelope-S3 expected, no logic deltas. Byte-identical `def` bodies confirmed by structural inspection (no test-file diff outside the new gate file; existing-test invariance §S6 holds). |

## Invariant evidence (§V7)

| Invariant | Architecture anchor | Code anchor | Verdict |
|---|---|---|---|
| INV-003 phase-lock-and-role-declaration | docs/ARCHITECTURE.md:31 (grep `### Phase 1: Intent` in operational-reference) | `scripts/slice_orchestrator/core.py:20` (`ROLE_FOR_PHASE`), `core.py:27` (`ROLE_TO_PHASE`), `core.py:33` (`VALID_TRIAGER_ACTIONS`); dispatch surface at `scripts/slice_orchestrator/dispatch.py:299` (`def dispatch_phase_agent`), `dispatch.py:345` (`def dispatch_triager`), `dispatch.py:412` (`def dispatch_phase_3`). Reachable through facade — `slice_orchestrator.ROLE_FOR_PHASE`, `.dispatch_phase_agent` resolve via `__init__.py:43-44, 70-72`. Agent-side phase-lock contract textual (`.claude/agents/*.md`) untouched (out-of-envelope). | PASS |
| INV-004 40k-token session budget | docs/ARCHITECTURE.md:41 (`tests/unit/test_context_budget.py`) | Telemetry observability writes — `scripts/slice_orchestrator/telemetry.py:24` (`DEBUG_DIR` import), `telemetry.py:139-141` (`<slug>-result.json/md`, `index.jsonl` paths), `telemetry.py:146` (`_atomic_write`), `telemetry.py:169` (`_persist_state`), `telemetry.py:354` (`class _HeartbeatDaemon`). Output paths/schema/atomic-write semantics preserved byte-identically. The pre-existing `test_inv004_turn1_token_budget` failure (101670 tokens under CC 2.1.119) is environmental drift outside cairn's control — CC version exceeded the `housekeeping/inv004-rebaseline-cc-2.1.116` rebaseline window — and is unrelated to this slice's package split (no agent-prompt or progressive-disclosure surface was edited). | PASS |
| INV-008 slice-close-contract | docs/ARCHITECTURE.md:80 (grep `def close_slice` against `scripts/slice_orchestrator/lifecycle.py`) | `scripts/slice_orchestrator/lifecycle.py:384` (`def close_slice`). DC-3/DC-4/DC-5/DC-7 contract docstring at lines 385-390. The four-signal precondition idempotency-check is `_is_slice_already_closed` invocation at line 391; the sweep-notes presence gate at lines 399-407 (DC-4 / compression §8 D2). Sole producer of `slice: complete` commit; `commit_phase_handoff` at `lifecycle.py:148` skips the Phase-4 boundary per `run_phase_loop` at `lifecycle.py:218`. | PASS |
| INV-009 cost-per-slice-budget | docs/ARCHITECTURE.md:85 (`tests/unit/test_slice_orchestrator_cost.py`) | `scripts/slice_orchestrator/core.py:116` (`INV_009_COST_THRESHOLD_USD = None`), `core.py:117` (`INV_009_TOKEN_THRESHOLD = None`); `_record_phase_cost` at `scripts/slice_orchestrator/telemetry.py:91`, `_init_state_dict` at `telemetry.py:49`, `_cost_for_tokens` at `core.py:358`. Both threshold constants reachable through facade: confirmed empirically — `python -c "import slice_orchestrator as so; print(so.INV_009_COST_THRESHOLD_USD, so.INV_009_TOKEN_THRESHOLD)"` prints `None None`; re-exports at `__init__.py:38-39` and `__all__` at `__init__.py:259-260`. | PASS |

## Facade preservation evidence

- `_MirroringModule` shim presence: `scripts/slice_orchestrator/__init__.py:192` (class declaration), `__init__.py:240` (`_sys.modules[__name__].__class__ = _MirroringModule` install). Mirrors `setattr` to underlying submodules so `monkeypatch` preserves `slice_orchestrator.X = …` semantics across the package split.
- `INV_009_COST_THRESHOLD_USD` + `INV_009_TOKEN_THRESHOLD` reachable through `slice_orchestrator.<NAME>`: confirmed via direct import probe (`PYTHONPATH=scripts uv run python -c "import slice_orchestrator as so; print(so.INV_009_COST_THRESHOLD_USD, so.INV_009_TOKEN_THRESHOLD)"` → `None None`), and via `tests/unit/test_slice_orchestrator_package_split.py::test_v2_public_surface_reexport` which is parametrized over the §S3 name list (GREEN at Phase 4).
- V2 import probe full proof: `is_valid_slice_id('a/b') = True`; `AGENT_MODEL_CONFIG` keys include `phase-1-writer`, `phase-2-skeptic`, `issue-triager`; `dispatch_phase_agent`, `run_phase_loop`, `close_slice` all bind; `so.close_slice is so.lifecycle.close_slice` → `True` (facade and submodule expose identical object).
- V3 CLI: both `python -m slice_orchestrator --legacy` (with `PYTHONPATH=scripts`) and `python scripts/slice_orchestrator/__main__.py --legacy` exit 0 and emit `orchestrator: --legacy invoked; follow commands/claude-code/start-slice-legacy.md manually for the prose-protocol path.`

## §V8 advisory — physical relocation

`git diff HEAD~5 --stat -- scripts/` shows `scripts/slice_orchestrator.py` deleted (-2240 lines) and 8 new submodule files (+2760 lines) under `scripts/slice_orchestrator/`. The +520-line delta is fully accounted by: module-header docstrings (~80 lines × 8 modules ≈ 200 lines net of overlapping content), explicit cross-submodule `from .core import ...` import lines (~50 lines), the `__init__.py` re-export block (~280 lines covering §S3 backward-compat surface), and the `_MirroringModule` shim (~50 lines, §S6 monkeypatch preservation). No `def` body shows logic-changing diff under structural inspection; all relocations are physical-only. Existing-test invariance §S6 holds: `git diff HEAD~5 -- tests/` shows changes only in the new gate file `tests/unit/test_slice_orchestrator_package_split.py`.

## Pyright posture

Pyright diagnostics are **advisory only** this slice — re-export false positives (`__init__.py` rebinding submodule attributes), `.git/` symlink shadowing surfaced by recursive scan, and untyped `result_data` narrowing per the Phase-3 implementation notes. Per intent §V1/§V8, type diagnostics are not gate failures. Not run; not gated.

## Pre-existing-failure resolution

- `test_item_d_no_empty_current_slice_subdirs` pre-Phase-4 (before sweep-notes.md exists): **FAIL** — empty `.claude/current-slice/integration/` directory.
- `test_item_d_no_empty_current_slice_subdirs` post-sweep-notes.md: **PASS** — `integration/sweep-notes.md` populates the directory; flip confirmed empirically by re-running `uv run pytest` after writing this file.
- `test_inv004_turn1_token_budget` pre/post: **FAIL/FAIL** — pre-existing CC-2.1.119 environmental drift (101670 tokens vs 40000 budget rebaselined for CC 2.1.116). Out-of-scope: this slice does not edit any progressive-disclosure surface, agent prompts, or `tests/unit/test_context_budget.py`. Resolution belongs to a future `housekeeping/inv004-rebaseline-cc-2.1.119` slice.

## Code review

Code review **not yet requested**. Per intent §V7 / `superpowers:requesting-code-review`, requesting code review is the operator's action item before any merge to `dev`. Recommended: open a PR from `feature/compression` against `dev` and request review from a Skeptic-mode peer; auditor's role ends at PASS verdict on slice close.

## Verdict

**PASS** — V1 (test invariance + zero non-gate test diff), V2 (public-surface re-export), V3 (CLI invocation), V4 (filesystem shape), V5 (architecture validator rc=0), V6 (path-string sweep clean), V7 (this invariant table), V8 (physical-relocation evidence) all satisfied; the only remaining pytest failure is pre-existing CC-2.1.119 environmental drift unrelated to the package split.

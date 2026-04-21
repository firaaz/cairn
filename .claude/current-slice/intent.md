---
slice: housekeeping/post-inv008-and-substrate-bugs
date: 2026-04-21
phase: 1-intent
invariants-touched: [INV-002, INV-005, INV-008]
adrs-referenced:
  - slice-close-contract
  - orchestrator-observability
  - context-discipline-protocol
  - identifier-scheme
envelope:
  - "tests/unit/test_context_discipline_protocol.py"
  - "tests/unit/test_hook_relpath_bypass.py"
  - "tests/unit/test_hook_tolerance.py"
  - "tests/unit/test_housekeeping_post_slice_a_tidy.py"
  - "tests/unit/test_invariant_assertions.py"
  - "tests/unit/test_cross_slice_isolation.py"
  - "tests/unit/test_post_timeout_reconcile.py"
  - "tests/unit/test_context_budget.py"
  - "tests/unit/test_slice_orchestrator_state_machine.py"
  - "tests/unit/test_close_slice_hardened.py"
  - "tests/unit/test_orchestrator_bug_fixes*.py"
  - "docs/operational-reference.md"
  - "scripts/slice_orchestrator.py"
  - ".claude/agents/phase-2-skeptic.md"
  - "checks/"
  - "commands/claude-code/"
out-of-scope:
  - "Path C fleet-writes hardening (deferred; memory path_c_fleet_writes_empirical.md)"
  - "Multi-instance orchestrator locking (deferred; tightens heartbeat advisory per slice-close-contract D4)"
  - "Triager misroute on superseded tests (deferred prompt iteration; memory triager_misroute_on_superseded_tests.md)"
  - "New features, refactors, or abstractions beyond the named fixes and docs"
  - "INV-004 re-baseline (closed at fe5662c; explicitly dropped from tech-debt roster per sweep #23 Staleness table)"
  - "ADR body edits to slice-close-contract (firm, append-only)"
  - "Provisional-ADR promotion or supersession (orchestrator-observability stays provisional)"
---

# Intent — housekeeping/post-inv008-and-substrate-bugs: bundled tech-debt + substrate-bug cleanup

## What and Why

Single bundled housekeeping slice that clears the inherited red roster from integration sweep #23 and, in the same envelope, the five substrate bugs surfaced during `compression/slice-3-observability-and-close-slice` and `housekeeping/inv004-rebaseline-cc-2.1.116`. Operator chose bundling over the originally-queued two-slice sequence (handoff.md:15-16) to amortize Phase 1-4 overhead across a related failure surface.

**Scope A — post-INV-008 tech debt.** 10 pytest reds, 3 ruff errors, 1 docs gap. All 13 items are pre-existing, classified in sweeps #22 / #23, and unrelated to any live feature work. They represent drift, stale assertions, and un-documented env-var knobs from the orchestrator-observability provisional ADR.

**Scope B — orchestrator substrate bugs.** Five latent correctness failures in `scripts/slice_orchestrator.py` / agent prompts, observed on the non-happy path (crash-resume, phase-2 YAML-escape, slug regex, measurement side-effect, close_slice commit subject). Each has been reproduced in-the-wild at least once; item 3 (slug drift) and item 2 (coupling-clusters YAML escape, inline-hotfixed at `5319c53`) fired during the two most recent slices.

**Why now.** The substrate bugs undermine INV-008's "close_slice is the sole commit source and is idempotent under crash-resume" guarantee (slice-close-contract D1, D2, D4). Leaving them live makes every subsequent slice-close a probabilistic event. The tech-debt reds block the integration gate from ever going green (sweep #23 Verdict: FAIL, exits 1 at Step 4a).

## Specification Detail

### Scope A — tech-debt (13 items)

**A1 — pytest reds (10).** Each failing test's assertion must pass without weakening the assertion semantics. Fix location depends on the test:

- `test_context_discipline_protocol::test_v5_learning_staging_ground_exists_and_is_minimal` — asserts `.claude/learning.md` exists and stays under a size cap per context-discipline-protocol Layer 5. Fix: restore the file (if absent) or trim it to the ADR-specified cap; ADR text is authoritative.
- `test_hook_relpath_bypass::{test_edit_body_bare_relative_flat_slug_blocked, test_edit_body_bare_relative_legacy_blocked, test_edit_body_slice_system_flat_slug_blocked}` (3) — assert the scope-guard hook blocks edits whose `file_path` is a bare-relative or `.slice-system/`-prefixed path outside the active slice envelope. Fix in `checks/scope-guard.sh` so the three bypass shapes are denied; cite CLAUDE.md "Edit canonical paths only" safety-critical rule.
- `test_hook_tolerance::TestV3FrontmatterEditBothForms::{test_edit_body_flat_slug_blocked, test_edit_body_flat_slug_emits_message, test_edit_body_legacy_blocked}` (3) — assert the reversibility-guard hook tolerates ADR frontmatter edits in both flat-slug and legacy forms while still blocking body edits. Fix in `checks/reversibility-guard.sh`.
- `test_housekeeping_post_slice_a_tidy::test_item_b_handoff_not_tracked` — asserts `.claude/handoff.md` is gitignored. Fix: confirm/add `.gitignore` entry.
- `test_invariant_assertions::TestSlice011AssertionCoverage::{test_no_extra_assertion_blocks, test_invariant_count_unchanged}` (2) — assert `docs/ARCHITECTURE.md` contains exactly N `invariant-check` blocks matching exactly N declared firm invariants. Fix: reconcile the architecture doc against the firm-invariant set (8 per sweep #23 Gate table); no net invariant additions or removals — drift cleanup, not semantic change.

**A2 — ruff errors (3).**
- `tests/unit/test_cross_slice_isolation.py:72-73` — 2x E741 ambiguous variable name `l`. Rename to a non-ambiguous identifier (e.g. `line`).
- `tests/unit/test_post_timeout_reconcile.py:101` — 1x F841 unused `result`. Use the value or drop the binding.

**A3 — heartbeat env var docs.** `docs/operational-reference.md` Environment variables table (at lines 339-344 today) gains two rows documenting `CAIRN_HEARTBEAT_INTERVAL` and `CAIRN_HEARTBEAT_STALE` with their defaults, the script(s) that read them, and their purpose. Read-by cite per CLAUDE.md "no hardcoded timeouts/sizes in consumer-facing scripts" convention. Sources: orchestrator-observability ADR (heartbeat cadence) and slice-close-contract D4 (stale-heartbeat advisory).

### Scope B — substrate bugs (5 items)

Each bug is specified by its public-interface-observable contract. Internal implementation is Phase-3 Builder's call; Phase-2 Skeptic writes the failing tests to these contracts.

**B1 — `current_phase` persisted across crash-resume** (memory bug 1). After `run_phase_loop` successfully commits a `handoff: phase N complete` (or finishes phase N for N == max_phase), `.claude/current-slice/slice.yaml` MUST reflect the advanced `current_phase` before the next phase begins. A subsequent `--resume` MUST NOT re-dispatch a completed phase. Contract: resume reads the persisted `current_phase` and dispatches that phase; persistence happens after every phase-commit, not only at `init_new_slice`.

**B2 — phase-2-skeptic coupling-clusters YAML validity** (memory bug 2). The agent prompt at `.claude/agents/phase-2-skeptic.md` MUST produce `.claude/current-slice/coupling-clusters.yaml` whose regex patterns parse under `yaml.safe_load` on every Phase-3 dispatch. The narrow inline hotfix at `5319c53` (`commands/claude-code/start-slice.md` YAML single-quoting) resolved the immediate symptom; this slice resolves the class. Fix the prompt: add an explicit single-quote requirement for regex patterns and a "no backslash escapes in double-quoted strings" note. Orchestrator-side pre-flight validation (Fix candidate B in the memory item) is OPTIONAL and may be deferred if the prompt fix suffices.

**B3 — slug canonical form is hyphenated** (memory bug 3, confirmed live in sweep #23 section 5). Pick one canonical slug form and enforce it at every producer. Canonical form: **hyphens** (matches `SLICE_ID_REGEX` at `scripts/slice_orchestrator.py:35` and INV-005 flat-slug discipline). `init_new_slice` normalizes any dot-form in the brief-derived id to hyphen-form BEFORE writing `slice.yaml`, and any newly-added `.claude/features/<feature>.yaml` entries use hyphen-form. Commit subjects and branch names should follow; this slice updates the normalization code, not historical commits. No regex relaxation — regex stays strict.

**B4 — measurement file write is test-pure** (memory bug 4). `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` MUST NOT rewrite `docs/plans/measurements/2026-04-12-slice-003.txt` as a side effect of a normal `uv run pytest` invocation. Options (Builder's choice): (a) guard the write behind an explicit `--record` flag or env var, or (b) make the write idempotent-within-tolerance so stable runs produce identical bytes. `git status` after a green test run MUST show a clean tree for the measurement file.

**B5 — `close_slice` commit subject satisfies `verify_handoff.sh` check (c)** (memory bug 5). `scripts/slice_orchestrator.py` `close_slice` writes its final commit with subject `slice: <slice-id> — complete` (em-dash, space-separated, slice-id present). This satisfies `scripts/verify_handoff.sh` check (c)'s required pattern and matches the prose-protocol convention used in pre-orchestrator closes. This is an additive narrowing of INV-008 D2 ("sole commit source") — the commit source does not change; the subject format tightens.

### Cross-cutting constraints

- **INV-008 firm contract preservation.** All B-items MUST preserve slice-close-contract D1 (idempotent close), D2 (sole commit source), D3 (wipe semantics), D4 (resume matrix), D5 (slug isolation + collision tripwire). Existing tests `test_close_slice_hardened.py` and `test_cross_slice_isolation.py` remain green. B3 normalization lands upstream of the slug producer, so D5's tripwire is unaffected.
- **ADR append-only.** No edits to `docs/adr/slice-close-contract.md` (firm) or other ADR bodies. `orchestrator-observability` stays provisional; heartbeat env-var names land in operational-reference.md only.
- **Stdlib-only Python, function-based.** Per CLAUDE.md New-code guidance.
- **No new hooks or validators.** The scope-guard / reversibility-guard / role-guard files are edited to fix existing assertions, not to add new enforcement surfaces.

## Boundary

**In scope.** The 13 failing tests' backing files and the source they exercise (scope-guard.sh, reversibility-guard.sh, `.gitignore`, `docs/ARCHITECTURE.md`, `.claude/learning.md`, `docs/operational-reference.md`). `scripts/slice_orchestrator.py` for B1/B3/B5. `.claude/agents/phase-2-skeptic.md` for B2. `tests/unit/test_context_budget.py` for B4. New test files under `tests/unit/test_orchestrator_bug_fixes*.py` at Phase-2 Skeptic's discretion to lock B1-B5 contracts.

**Out of scope.** See envelope `out-of-scope` block. Explicitly: no Path C work, no multi-instance locking, no triager prompt iteration, no new ADRs, no ADR body edits, no INV-004 re-touching, no refactors beyond the named fixes.

## Verification

### Structural assertions (Phase 4 Auditor)

- **V1** `uv run pytest tests/unit/test_context_discipline_protocol.py tests/unit/test_hook_relpath_bypass.py tests/unit/test_hook_tolerance.py tests/unit/test_housekeeping_post_slice_a_tidy.py tests/unit/test_invariant_assertions.py -q` returns exit 0.
- **V2** `uv run ruff check tests/unit/test_cross_slice_isolation.py tests/unit/test_post_timeout_reconcile.py` returns exit 0.
- **V3** `grep -c 'CAIRN_HEARTBEAT_' docs/operational-reference.md` returns >= 2 (both env vars documented as rows in the Environment variables section).
- **V4** `uv run pytest --tb=no -q` returns exit 0 (full suite green).
- **V5** `uv run ruff check` returns exit 0 (zero errors, no warnings suppressed).
- **V6** `scripts/integration_gate.py` returns exit 0.

### Behavioral assertions (Phase 4 Auditor, from Phase 2 test targets)

- **V7 (B1)** A synthetic resume scenario where `slice.yaml` has `current_phase: 1` but HEAD carries `handoff: phase 2 complete` does NOT re-dispatch Phase 1 on `slice_orchestrator.py --resume`; the post-phase write has updated `current_phase`. Test target: `tests/unit/test_orchestrator_bug_fixes*.py::test_current_phase_persisted_across_phase_boundary`.
- **V8 (B2)** The coupling-clusters YAML produced via the phase-2-skeptic prompt template (or fixture mimicking it) parses under `yaml.safe_load` without raising. Structural test: grep for double-quoted pattern starts returns 0 matches, OR a parse round-trip succeeds.
- **V9 (B3)** `init_new_slice` given a brief containing `housekeeping/foo-1.2.3` writes `slice.yaml` with `id: housekeeping/foo-1-2-3` (dots normalized to hyphens); `SLICE_ID_REGEX` unchanged. Test target: `test_orchestrator_bug_fixes::test_slug_dot_normalization`.
- **V10 (B4)** `git status --porcelain docs/plans/measurements/` is empty after a full green `uv run pytest` run starting from a clean tree.
- **V11 (B5)** After `close_slice` on a fixture slice-id (integration test), `git log -1 --format=%s` matches the exact pattern `slice: <id> — complete`, and `scripts/verify_handoff.sh` exits 0 against that commit.
- **V12 (INV-008 non-regression)** `uv run pytest tests/unit/test_close_slice_hardened.py tests/unit/test_cross_slice_isolation.py -q` stays green — all seven INV-008 machine-check targets pass.

### Invariant check (Phase 4 Auditor)

- **INV-002** Layer 3 wipe (close_slice wipe semantics) and Layer 5 learning.md cap both true. Evidence: A1 learning-cap test green + existing wipe tests green.
- **INV-005** Flat-slug discipline preserved; no dot-form slugs in `.claude/current-slice/slice.yaml` or `.claude/features/*.yaml` after B3.
- **INV-008** All three sub-properties (idempotent close, sole commit source, cross-slice artifact isolation) remain true after the substrate fixes. Evidence: V12 green + `git log --oneline | grep 'slice:.*— complete'` shows unique per-slice commit.

### Re-split criterion (Phase 1 Writer / Phase 2 Skeptic joint call)

If Phase 2 Skeptic's failing-test envelope exceeds ~15 distinct test functions OR the Phase-3 implementation envelope touches more than 4 source files beyond the 13 tech-debt files, re-open the split: `housekeeping/post-inv008-tech-debt` (Scope A only) lands first, and a successor `housekeeping/orchestrator-substrate-bugs` (Scope B only) lands second. Operator has pre-authorized bundling but flagged re-split as acceptable if the envelope proves unwieldy (brief closing paragraph).

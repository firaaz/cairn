# Phase 4 Integration Sweep — `identifier-scheme/rename-sweep-test-robust`

**Date:** 2026-04-20
**Branch:** `feature/compression`
**Tip (pre-Phase-4):** `48d8665`
**Envelope:** `tests/unit/test_adr_rename_sweep.py` (single file; +424 / −24 cumulative).
**Previous sweep:** `#20 (2026-04-19-sweep-20.md)` — post-`housekeeping/post-slice-a-tidy`, PASS, and the sweep that filed Finding §1 (stale twelve-file latch) against the exact envelope now closed by this slice.
**Verdict:** **PASS** — the envelope closes sweep #20 Finding §1, the widened contract is robust to `compression-infrastructure-bootstrap.md` and every future flat-slug ADR, no out-of-envelope substrate was touched, and no new failures were introduced. Pre-existing failures outside the envelope persist and are listed below with file:line pointers.

---

## Cross-slice failure modes (pre-check enumeration)

| # | Mode | Hypothesis | Outcome |
|---|---|---|---|
| 1 | Import / stdlib-only drift | New imports leak 3rd-party deps into test envelope | Clean — ruff PASS; test uses stdlib only (`re`, `pathlib`, manual frontmatter scan) |
| 2 | Schema drift on ADR corpus | Widened contract fails on `index.md`, legacy tolerance fixtures, or the new provisional ADR | Clean — `index.md` excluded; tolerance fixtures in `test_hook_tolerance.py` / `test_hook_relpath_bypass.py` untouched; `compression-infrastructure-bootstrap.md` passes the shape assertion |
| 3 | Tool contract — hooks drift | Widening interacts with `reversibility-guard.sh` / `scope-guard.sh` / `role_guard.py` | Clean — no hook files edited |
| 4 | Config conflict — provisional ADR treated as firm | Shape contract latches firmness or rejects provisional ADRs | Clean — test ignores firmness; only asserts filename shape + `id:` stem match |
| 5 | `.slice-system/` symlink / scope-guard boundary | Edit routed via symlink stripped to no-allowlist match | Clean — all three slice commits on canonical path; scope-guard allowlisted the envelope |
| 6 | INV-005 interaction | Widened contract over-specifies and rejects `<feature>/<slice>` or `<adr-id>/<decision-slug>` ids appearing inside ADR bodies | Clean — shape check applies only to `docs/adr/*.md` filename + top-level `id:` frontmatter |
| 7 | INV-003 interaction with new ADR | Role-guard narrow exception (compression-infrastructure-bootstrap) requires the corpus guard to accept provisional ADRs | Clean — shape-only contract accepts any flat-slug filename regardless of firmness |
| 8 | Snapshot / out-of-envelope drift | Non-envelope files mutated under the slice | Clean — `snapshot_diff.py --diff` exit 0; only `tests/unit/test_adr_rename_sweep.py` changed in the slice window |

---

## Gate Results

| Gate | Command | Exit | Detail |
|---|---|---|---|
| Envelope regression | `uv run pytest tests/unit/test_adr_rename_sweep.py -q` | 0 | 66 passed on live 13-file corpus |
| Integration gate — invariant check | `uv run python scripts/integration_gate.py` (Step 3) | 0 | PASS — 7 firm invariants (Check D) |
| Integration gate — ruff | `uv run python scripts/integration_gate.py` (Step 4a) | 0 | PASS |
| Integration gate — pytest (full) | `uv run python scripts/integration_gate.py` (Step 4b) | 1 | Fails fast on pre-existing `TestV1BareRelativeFlatSlugBlocked::test_edit_body_bare_relative_flat_slug_blocked`; confirmed pre-existing on stashed base (§Pre-existing out-of-scope) |
| Full pytest (envelope-out) | `uv run pytest tests/unit/ -q --deselect <V1 bypass test>` | 1 | 7 failed / 558 passed / 1 skipped — all pre-existing or Phase-4-gated (two resolve on this sweep-notes write) |
| Validator | `uv run python scripts/validate_architecture.py` | 0 | 7 invariants verified, 12 ADRs checked |
| Snapshot diff | `uv run python scripts/snapshot_diff.py --diff` | 0 | No out-of-envelope drift |

---

## Invariant Evidence (one row per declared invariant)

INV-005 is the only invariant listed under `invariants-touched`. The other six firm invariants are sanity-checked because the integration gate runs their machine-checkable assertions (Check D) and the test corpus exercises several.

| Invariant | Verdict | Evidence (file:line) |
|---|---|---|
| INV-001 (bootstrap-exception) | PASS | `scripts/validate_architecture.py` Check D green; every commit in the slice window carries a slice-prefixed subject (`b4ce212 phase-3(rename-sweep-test-robust):`, `6985d43 test(adr-rename-sweep):`, `38100de refactor(test_adr_rename_sweep):`, `b700c1c test(adr-rename-sweep):`) |
| INV-002 (3-layer context discipline) | PASS | `tests/unit/test_context_budget.py` green in envelope-out bucket; `.claude/handoff.md:1-29` — 29 lines (within budget); `current-slice/` subdirs all non-empty post-write |
| INV-003 (4-phase pipeline + compression narrow exception) | PASS | Four phases ran in order (`handoff-phase-1.md`, `handoff-phase-2.md`, `handoff-phase-3.md`, this file); `checks/role_guard.py` permission-policy governs `compression/*` only; `docs/adr/compression-infrastructure-bootstrap.md:10` `invariants-touched: [INV-003]` |
| INV-004 (session-start ≤30k + progressive disclosure) | PASS | `tests/unit/test_context_budget.py` (5 tests) green; no lite/full command files added or widened |
| INV-005 (two-field identity; flat-slug for ADR/feature, hierarchical for slice/decision-point) | **PASS (directly exercised)** | `tests/unit/test_adr_rename_sweep.py::TestLiveCorpusFlatSlugShape` parametrized over 12 live ADRs; every filename matches `^[a-z][a-z0-9-]*\.md$` and frontmatter `id:` equals the stem. Live-corpus: `docs/adr/{bootstrap-exception,cliff-failure-mode-and-v1-defenses,compression-infrastructure-bootstrap,context-discipline-protocol,context-tiers-integration,d3-bypass-classification,feature-slice-model,identifier-scheme,parallelism-v1,phase-lock-and-role-declaration,phase-pipeline-evaluation,semantic-identity}.md` — 12/12 match |
| INV-006 (feature containment + single state file) | PASS | `.claude/features/identifier-scheme.yaml:48-51` registers `identifier-scheme/rename-sweep-test-robust` with `after: identifier-scheme/doc-sweep`; no duplicate state outside `slice.yaml` |
| INV-007 (feature-slice 3-tier integration) | PASS | `handoff.md` Features section names `identifier-scheme` and `compression`; validator Check D verifies `commands/claude-code/handoff.full.md` references `.claude/features/`; no new tier introduced |

---

## Findings

### F1 — sweep #20 Finding §1 closed (primary purpose of this slice)

Sweep #20 flagged `tests/unit/test_adr_rename_sweep.py` failing on the 13-file live corpus via a 12-file size latch and a hardcoded `expected_ids` set. Phase 3 rewrote the test module around a **shape** contract: `TestLiveCorpusFlatSlugShape` enumerates `docs/adr/*.md` at test time, excludes `index.md`, asserts `^[a-z][a-z0-9-]*\.md$` on the filename, and checks that frontmatter `id:` equals the stem. The count assertion (`test_exact_twelve_adr_files_total`) is retired. V5 index assertions derive expected ids from the live corpus rather than a hardcoded enumeration.

- `grep -c compression-infrastructure-bootstrap tests/unit/test_adr_rename_sweep.py` → **0** (V3 satisfied).
- Envelope suite: **66 passed** on the live 13-file corpus.
- Robustness predicate (V4 from intent.md): parametrized shape test reads the live filesystem; a new valid flat-slug ADR at `docs/adr/<new>.md` with matching `id:` yields a new parametrized case passing with no test-source edit — verified by parametrize-source inspection.

**Class:** resolved by this slice.

### F2 — handoff staleness: pre-existing-failure accounting must be revised

`.claude/handoff.md:15` still reads "Stale `test_adr_rename_sweep` hardcoded 12-ADR list... separate housekeeping micro-slice queued." **Resolved** by this slice; remove from Blocked/Pending.

Sweep #20 Finding §4 revised the pre-existing failure count to "5 pre-existing (3 classes)". Post-close the corrected count is **5 pre-existing (1 class)**:
- **Class P1: `reversibility-guard.sh` body-edit bypass** — 6 failures across `tests/unit/test_hook_relpath_bypass.py` (V1 / V2 bare-relative, V3 slice-system-prefixed) and `tests/unit/test_hook_tolerance.py` (V3 flat-slug + legacy body blocks). Root cause: `checks/reversibility-guard.sh` returns `0` on Edit-body (non-frontmatter) ADR edits even when outside an editorial-fix envelope. Confirmed pre-existing by stash-and-retest: V1 test fails exit 0 vs expected 2 on base commit with working-tree stashed. Out-of-envelope per intent.md:12.

Sweep #20 Class P2 ("state-machine tests read real `slice.yaml`") appears closed: the whole `tests/unit/test_slice_orchestrator_state_machine.py` passed in the envelope-out bucket. `compression/orchestrator-hardening` (closed `fc1de9d`) likely addressed it; next sweep can drop it.

Sweep #20 Class P3 ("ephemeral `sweep-notes.md` assertion in `test_housekeeping_post_slice_a_tidy.py`") resolves on commit of this file (F3).

**Class:** handoff-docs drift; resolved by the handoff update this phase writes.

### F3 — housekeeping test `test_item_8_dogfooding_findings_section_in_sweep_notes` resolves on this write

`tests/unit/test_housekeeping_post_slice_a_tidy.py:122` (Item 8) and `:101` (Item D — no-empty subdirs) both assert artifacts of a live Phase-4 slice. Both pass after this file is committed. Sweep #20 Finding §3 recommended deleting the Item-8 assertion as structurally incompatible with post-close state; logged but out-of-envelope here.

**Class:** resolves on commit of this file.

### F4 — out-of-envelope writes (permitted by role_guard policy, not slice drift)

Non-envelope files modified during Phase 1–3:

- `.claude/current-slice/{intent.md, slice.yaml, validation/approach.md, validation/coupling-clusters.yaml, implementation/notes.md, handoff-phase-{1,2,3}.md}` — slice substrate; authorized by role-guard for Phase 1–3 writers.
- `.claude/features/identifier-scheme.yaml` — slice registration; INV-006 single-state-file update (always-create policy).
- `.claude/structural-snapshot.json` — delta belongs to `compression/orchestrator-hardening`'s scripts/tests; **not this slice's drift.** Baseline refreshed at close.

No source/test file outside the envelope was edited. `snapshot_diff.py --diff` exit 0 confirms.

---

## Dogfooding findings

Compressed-dispatch end-to-end was not a dogfood target this slice (ran via interactive phase agents, not the compressed pipeline). Still-open items relevant to the compressed pipeline are preserved verbatim as pointers for the next compressed-dispatch slice; no new evidence gathered this sweep.

1. **`brief` unescaped in `init_new_slice`** — `scripts/slice_orchestrator.py:368` writes `brief: "{brief}"` without escaping `"` / `\n`; crashes on briefs containing either. Open (carried from `.claude/handoff.md:16`).
2. **`brief` fanned-out to every phase, not only Phase 1** — `scripts/slice_orchestrator.py:262-264` injects the brief into every phase's stdin; contract/code divergence. Open (carried from `.claude/handoff.md:17`).
3. **`--permission-mode` still absent on dispatch path** — sweep #20 / handoff recorded this at `scripts/slice_orchestrator.py:105-133, 241`. Not re-verified this slice.
4. **Orchestrator `stderr` capture on FAILED dispatch** — `scripts/slice_orchestrator.py` logs agent-reported FAILED to `.claude/orchestrator-debug/`; confirmed by untracked `.claude/orchestrator-debug/` in the working tree.
5. **`features` cross-index in handoff** — INV-007 tier-integration; validator green this sweep.
6. **Envelope enforcement** — `tests/unit/test_adr_rename_sweep.py` was the sole source-of-truth file edited in the slice window; envelope held.

This slice ran interactively, so items #1–#3 were not exercised. The next compressed `/start-slice <brief>` remains the live test for those items.

---

## Pre-existing out-of-scope (do not gate this slice)

| Location | Symptom | Status |
|---|---|---|
| `tests/unit/test_hook_relpath_bypass.py::TestV1BareRelativeFlatSlugBlocked::test_edit_body_bare_relative_flat_slug_blocked:175` | exit 0 vs expected 2 on Edit-body bare-relative flat-slug ADR | Pre-existing; Class P1; confirmed on stashed base |
| `tests/unit/test_hook_relpath_bypass.py::TestV2BareRelativeLegacyBlocked::test_edit_body_bare_relative_legacy_blocked:223` | exit 0 vs expected 2 on Edit-body bare-relative legacy ADR | Pre-existing; Class P1 |
| `tests/unit/test_hook_relpath_bypass.py::TestV3SliceSystemPrefixedDeniesConsistently::test_edit_body_slice_system_flat_slug_blocked` | same bypass under `.slice-system/`-prefixed tool-input path | Pre-existing; Class P1 |
| `tests/unit/test_hook_tolerance.py::TestV3FrontmatterEditBothForms::{test_edit_body_flat_slug_blocked, test_edit_body_flat_slug_emits_message, test_edit_body_legacy_blocked}` | same body-edit bypass via tolerance fixtures | Pre-existing; Class P1 |

Root cause is a single `reversibility-guard.sh` branch (body-edit vs frontmatter-edit detection); one ADR-fix slice can close the class.

---

## Staleness audit of `.claude/handoff.md`

| Line | Item | Status after this slice |
|---|---|---|
| 15 | Stale `test_adr_rename_sweep` hardcoded 12-ADR list | **RESOLVED** — remove |
| 16 | `init_new_slice` `brief` unescaped at `scripts/slice_orchestrator.py:368` | VALID — still open |
| 17 | `_slice_brief` injects brief to every phase at `scripts/slice_orchestrator.py:262-264` | VALID — still open |
| 18 | Compressed dispatch end-to-end unverified | VALID — still open (this slice ran interactive) |
| 19 | Stash `stash@{0}` with unrelated WIP | VALID (no stash interaction this slice) |

---

## Next

- Handoff Blocked/Pending line #1 replaced with reversibility-guard body-edit bypass pointer (6 failures, 1 root cause).
- Snapshot baseline refreshed after close commit; re-anchored to new tip.
- `.claude/sweep.yaml` → `last-sweep-at-slice-id: identifier-scheme/rename-sweep-test-robust`; `sweep-interval: 1` unchanged.
- Next sweep due after 1 further slice-close.

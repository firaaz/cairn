```yaml
slice: compression/slice-artifact-preservation
date: 2026-04-26
phase: 1-intent
invariants-touched: [INV-008]
adrs-created: [slice-artifact-preservation]
adrs-referenced: [parallelism-v1]
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "tests/unit/test_slice_orchestrator_artifact_preservation.py"
  - "commands/claude-code/start-slice.full.md"
  - ".gitignore"
  - "docs/ARCHITECTURE.md"
  - "docs/adr/slice-artifact-preservation.md"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/{intent.md,validation/approach.md,implementation/notes.md,integration/sweep-notes.md}"
  - ".claude/current-slice/handoff-phase-{1,2,3,4}.md"
out-of-scope:
  - "Any change to scripts/slice_orchestrator/ outside lifecycle.py"
  - "Any extractor or substrate-side change (substrate slices own that)"
  - "Compaction / retention policy for .claude/sweep-results/ (deferred per ADR D4)"
  - "Commit-vs-gitignore reconsideration (deferred to extraction time per ADR D3)"
  - "Any change to existing close_slice test files (test_close_slice_*.py) other than additive imports if needed"
  - "Any change to INV-008's invariant-check grep target (D7 preserves it)"
  - "Any change to .claude/agents/phase-*.md"
  - "Any new ADR beyond slice-artifact-preservation"
```

# Intent — compression/slice-artifact-preservation: pre-wipe snapshot of phase ephemerals

## What and Why

`close_slice` (DC-5) wipes `.claude/current-slice/` before the sole `slice: complete` commit, destroying every phase ephemeral the four agents produced (`intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `handoff-phase-{1..4}.md`, `envelope-expansions.log`, the pre-close `slice.yaml`). The git-history record preserves only the bundled summary; the per-phase artifacts are gone.

This slice operationalizes ADR `slice-artifact-preservation` (firm, 2026-04-26) by adding a pre-wipe copy step in `close_slice` that snapshots the ephemerals to `.claude/sweep-results/<slug>/artifacts/` (gitignored). Co-lands the ADR file in the same Phase-3 commit as the lifecycle change, satisfying the substrate program's need for stable per-slice phase-level provenance and restoring failed-slice forensics access beyond git-history-only.

Sibling to substrate Slice 1 (`compression/lever-X-knowledge-index`) under `parallelism-v1`; envelopes are disjoint (substrate owns `scripts/cairn_query/**`, this slice owns `scripts/slice_orchestrator/lifecycle.py`).

## Specification Detail

### S1 — `_copy_artifacts_to_sweep_results(slice_id, pre_close_yaml_text)` helper in `lifecycle.py`

Private helper added between `_wipe_current_slice` and `_is_slice_already_closed`. Public surface (signature + side effects) only:

- **S1.a — Slug derivation.** `slug = slice_id.replace("/", "-")`. Inherits `slice-close-contract` D5 collision tripwire.
- **S1.b — Target tree.** `os.makedirs(".claude/sweep-results/<slug>/artifacts/", exist_ok=True)` plus the three subdirs `validation/`, `implementation/`, `integration/`. Operational `OSError` propagates.
- **S1.c — Snapshot scope (ADR D2).** Iterates a fixed `_ARTIFACT_RELPATHS` tuple of 9 paths relative to `.claude/current-slice/`: `intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `handoff-phase-{1,2,3,4}.md`, `envelope-expansions.log`. Each existing source `shutil.copyfile`'d byte-identical to its target.
- **S1.d — Pre-close `slice.yaml` (ADR D2.vii).** Helper writes the caller-supplied `pre_close_yaml_text` to `<target>/slice.yaml` via `Path.write_text`. Caller is responsible for capturing the pre-mutation text.
- **S1.e — F5-tolerance (ADR D6).** Per-source `src.is_file()` guard; missing source → silent skip, no raise. Mirrors `_wipe_current_slice`'s `FileNotFoundError` posture.
- **S1.f — Operational loud-fail (ADR D7).** `OSError` from `os.makedirs`, `shutil.copyfile`, or `write_text` (e.g. `ENOSPC`, `EACCES`) propagates uncaught, aborting the close before Step 3 wipes the originals. Mirrors Step 0's sweep-notes-missing posture.

### S2 — `close_slice` step ordering update (ADR D1)

`close_slice` public signature unchanged. Internal step order becomes:

1. Step 0: sweep-notes presence check (existing).
2. **Step 0.5 (new): Capture pre-close `slice.yaml` text** — `_pre_close_yaml_text = SLICE_YAML.read_text()` if the file exists; on `OSError` or absence, set to `""` (D2.vii F5-tolerance, matching existing `read_slice_state` posture).
3. Step 1: `slice.yaml → status=complete` (existing).
4. Step 2: bundle `.claude/handoff.md` (existing).
5. Step 2.x: drift detector (existing).
6. **Step 2.5 (new): `_copy_artifacts_to_sweep_results(slice_id, _pre_close_yaml_text)`.** Slice-id sourced from the in-memory `sy` dict (`sy.get("id") or "unknown/unknown"`).
7. Step 3: `_wipe_current_slice` (existing).
8. Step 4: sole `slice: complete` commit (existing — DC-4 preserved; helper performs no `_git` calls).
9. Step 5: persist terminal observability (existing).

DC-3 idempotency preserved by the existing `_is_slice_already_closed` short-circuit at the top of `close_slice` — gates the new step too.

### S3 — `.gitignore` directive (ADR D3)

Append three lines to `.gitignore` (comment + pattern) covering `.claude/sweep-results/*/artifacts/`. The existing `.claude/sweep-results/<date>-sweep.md` integration-sweep notes remain committed; only the new per-slice `<slug>/artifacts/` subtree is ignored.

### S4 — `commands/claude-code/start-slice.full.md:210` prose narrowing (ADR D5)

Replace "no archive directory **for successful slices**" with "no archive directory **for committed history**" and insert one new sentence noting the on-disk artifact preservation under `.claude/sweep-results/<slug>/artifacts/`. Same line, no line-count delta.

### S5 — `docs/ARCHITECTURE.md:75` INV-008 prose amendment (ADR D8)

Promote "three properties" → "four properties"; add property `(d)` describing the pre-wipe copy step (snapshot scope, two-tier failure handling, ordering between bundle and wipe); append `; slice-artifact-preservation` to the closing parenthetical. The `invariant-check INV-008` block (`type: grep`, `pattern: "def close_slice"`, `target: "scripts/slice_orchestrator/lifecycle.py"`) is **NOT** touched — D8 explicitly preserves the grep target.

### S6 — Co-landed ADR file

`docs/adr/slice-artifact-preservation.md` (drafted under a separate `/decision` session, present uncommitted/pre-staged in this worktree) is staged in this slice's Phase-3 commit alongside the `lifecycle.py` change. Frontmatter `adrs-created: [slice-artifact-preservation]` records the authorship; `adrs-referenced: [parallelism-v1]` records the concurrent-worktree dispatch context governing this slice.

## Boundary

In scope: the eight envelope paths above. Out of scope: every item in the frontmatter `out-of-scope` block — most notably any non-`lifecycle.py` orchestrator file, any extractor or substrate-side change (substrate slices own that), `.claude/sweep-results/` compaction policy (ADR D4 parks it), the commit-vs-gitignore reconsideration (ADR D3 defers to extraction time), the existing `test_close_slice_*.py` files (additive imports only if Phase 3 surfaces them), the INV-008 grep target, `.claude/agents/phase-*.md`, and any ADR beyond `slice-artifact-preservation`.

## Verification

### Phase 2 (RED) tests — `tests/unit/test_slice_orchestrator_artifact_preservation.py`

Nine RED tests, all asserting against `lifecycle._copy_artifacts_to_sweep_results` and `lifecycle.close_slice`:

- **V1 (D2 byte-identity, handoff)** `test_d2_handoff_phase_files_copied_byte_identical` — all four `handoff-phase-{1..4}.md` snapshots match source bytes.
- **V2 (D2 byte-identity, phase artifacts)** `test_d2_phase_artifact_files_copied_byte_identical` — `intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `envelope-expansions.log` snapshots match source bytes.
- **V3 (D2.vii pre-close yaml capture)** `test_d2_pre_close_slice_yaml_captured_not_post_close` — snapshotted `slice.yaml` contains `status: in-progress`, NOT `status: complete`.
- **V4 (D6b F5-tolerance)** `test_d6b_missing_source_skips_silently` — only-`intent.md`-present case copies what exists; absent siblings produce no target file; no raise; pre-close yaml still written.
- **V5 (D7 ops-error, copyfile)** `test_c_operational_copy_failure_raises` — patched `shutil.copyfile → OSError(ENOSPC)` propagates from helper.
- **V6 (D7 ops-error, makedirs)** `test_c_target_dir_creation_failure_raises` — patched `os.makedirs → OSError(EACCES)` propagates from helper.
- **V7 (D6a idempotency)** `test_d6a_helper_idempotent_on_repeat_invocation` — second helper call over identical sources leaves target byte-equal to first; no raise.
- **V8 (D1 ordering, integration)** `test_d1_close_slice_copies_before_wipe` — end-to-end `close_slice` (with `_git` and `_git_head_safe` stubbed) populates `<sweep-results>/<slug>/artifacts/intent.md` AND `<slug>/artifacts/slice.yaml` with `status: in-progress` AND wipes `.claude/current-slice/` to `slice.yaml` only.

Initial run after Phase 2 commit: all 9 RED with `AttributeError: module 'scripts.slice_orchestrator.lifecycle' has no attribute '_copy_artifacts_to_sweep_results'`.

### Phase 3 (GREEN) verification

- **V9** `uv run pytest tests/unit/test_slice_orchestrator_artifact_preservation.py -v` → 9/9 PASS.
- **V10** `uv run pytest tests/unit/test_close_slice_*.py tests/unit/test_slice_orchestrator_*.py -v` → all green; pre-existing close_slice tests untouched (the new copy writes outside `.claude/current-slice/`).
- **V11** `uv run python .slice-system/scripts/validate_architecture.py` → PASS; INV-008 grep target `def close_slice` unchanged in `scripts/slice_orchestrator/lifecycle.py`.

### Phase 4 (Integrator sweep) verification

- **V12 — Manual end-to-end.** Operator opens a throwaway slice on a sibling worktree, closes it. `.claude/sweep-results/<slug>/artifacts/` contains the 9 source-file snapshots that existed at close (missing files skip per F5) and a `slice.yaml` with `status: in-progress`.
- **V13 — `.gitignore` directive applies.** Post-close `git status` does NOT list `.claude/sweep-results/<slug>/artifacts/**` as untracked.
- **V14 — Idempotency.** Re-running `close_slice` on an already-closed slice short-circuits at `_is_slice_already_closed` (DC-3); helper not re-invoked.
- **V15 — ADR co-landed.** `docs/adr/slice-artifact-preservation.md` is staged in the Phase-3 commit alongside `scripts/slice_orchestrator/lifecycle.py`; appears in `git show` of that commit.

### Invariant check

- **INV-008** four separately-testable properties hold: (a) DC-3 idempotency, (b) DC-4 sole-commit-source (`close_slice`; helper performs no commits), (c) DC-7 slug-keyed observability (`<slug>/artifacts/` slug-namespaced), (d) **new** — phase ephemerals snapshotted between bundle and wipe with two-tier failure handling. Validator's `def close_slice` grep target preserved.

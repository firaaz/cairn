---
id: slice-artifact-preservation
name: "Slice artifact preservation — pre-wipe snapshots of phase ephemerals"
status: superseded
firmness: firm
supersedes: []
supersedes-sections:
  - "slice-close-contract — INV-008 prose only (additive: new property (d) describing the pre-wipe copy step; DC-3 idempotency, DC-4 sole commit source, DC-5 explicit wipe, and DC-7 slug-keyed observability are unchanged; the invariant-check `def close_slice` grep target is preserved). The amendment propagates to `docs/ARCHITECTURE.md`'s INV-008 prose surface (D8 below); the frontmatter attribution targets the canonical ADR source — ARCHITECTURE.md is a derived view of ADR-resident decisions."
superseded-by: null
topic: process
adrs-referenced: [slice-close-contract, context-discipline-protocol, phase-lock-and-role-declaration, parallelism-v1, compression-infrastructure-bootstrap]
invariants-touched: [INV-008]
date: 2026-04-26
---

# slice-artifact-preservation: Pre-wipe snapshot of slice phase ephemerals

## Status
Accepted

## Date
2026-04-26

## Context

`slice-close-contract` (firm, 2026-04-20) commits `close_slice` to wiping every file under `.claude/current-slice/` except `slice.yaml` (DC-5) before producing the sole `slice: <id> — complete` commit (DC-4). The wipe is load-bearing for `context-discipline-protocol` Layer 3 — without it, the next slice inherits stale framing through `/catchup` and the four-phase isolation property degrades.

A consequence of the wipe is that everything the four phase agents produced as ephemerals — `intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `handoff-phase-{1..4}.md`, `envelope-expansions.log`, and the pre-close `slice.yaml` (with envelope intact) — is destroyed at close. The git-history record (`slice: <id> — complete` commit + the bundled `.claude/handoff.md`) preserves a coarse summary; the ephemerals themselves are gone.

`commands/claude-code/start-slice.full.md:210` records this stance: "no archive directory for successful slices — the `status: complete` commit IS the git-history record." That stance was correct at the time it was written. Two pressures have since accumulated:

1. **Substrate work needs phase-level provenance.** The knowledge-substrate program (`docs/plans/2026-04-25-knowledge-substrate-design.md`) introduces typed analytical queries over the cairn corpus — invariant-evidence rows, lesson extraction, envelope-expansion patterns. Several intended analyses (e.g., "what fraction of slices expanded their envelope past Phase 1?") need the wiped artifacts as their source of truth. The git-history bundle (`.claude/handoff.md`) is too coarse to support these queries.

2. **Operator-side failure analysis is degraded.** When a slice fails Phase 4 *and* operator triage takes more than a few hours, the operator already loses access to the in-process artifacts because they only existed under `.claude/current-slice/`. Re-deriving them from git is partial (handoffs are committed, but the intent / approach / notes and the envelope-expansion log are not).

The original "no archive" stance was correct against three concerns:
- Maintenance cost of a parallel git-tracked archive that drifts from canonical history.
- Merge-collision churn on archive paths during parallel slices (anticipated by analogy with `.claude/sweep.yaml` and `.claude/sweep-results/<date>-sweep-NN.md` contention patterns under the manual-parallel dogfood; no published lesson cites archive-path collisions specifically as of 2026-04-26).
- Recovery-via-git-log adequacy for the *failed-slice debugging* use case.

This ADR narrows that stance: **no archive in committed history**, but ephemeral artifacts preserved on-disk in a per-slice gitignored directory for analytical use. The git-history record stays canonical; the new directory is non-authoritative analytical data.

The chosen mechanism — pre-wipe copy in `close_slice` — was selected over (i) move/rename instead of copy (asymmetric with `_wipe_current_slice`'s F5-tolerance, adds rename-across-filesystems failure mode), (ii) post-close pipeline-substrate session (the ephemerals are never in git history, so a separate session has no recovery source), (iii) capture-on-write at each phase agent (distributes archival concern across four prompts; L-005-class skill-coordination tax), and (iv) deferred-archive at next slice's open (strictly weaker — the wipe destroys originals before the next slice runs). Stress-tested against five pre-mortem scenarios (disk-full, perm-denied, manual rebase, post-copy wipe failure, concurrent close); all five recover within existing close_slice idempotency contracts. A fresh-context Phase-5 verification rerun surfaced four amendments — incorporated into D2.vii failure classification, supersedes-sections dual-surface clarification, the lesson-attribution correction above, and the F/G alternatives below.

## Decision

### D1 — Pre-wipe copy step in close_slice

`scripts/slice_orchestrator/lifecycle.py:close_slice` gains a copy step that snapshots ephemeral phase artifacts to `.claude/sweep-results/<slug>/artifacts/` *before* `_wipe_current_slice` runs. `<slug>` is the slice id with `/` replaced by `-`, matching the existing slug convention in the orchestrator.

Updated step ordering (slice-close-contract DC-4 sole-commit-source unchanged):

1. Step 0: sweep-notes presence check (existing — slice-close-contract D2)
2. **NEW Step 0.5: Capture pre-close `slice.yaml` text in memory.** Read the file content as a string before Step 1 mutates it. This is a memory-only operation; no I/O target. Read failures are F5-tolerant per D2.vii below.
3. Step 1: `slice.yaml` → `status=complete`, `current_phase=max_phase` (existing)
4. Step 2: bundle `.claude/handoff.md` from phase handoffs + sweep-notes (existing)
5. Step 2.x: drift detector (DC-4 layer 3, existing)
6. **NEW Step 2.5: Copy artifacts to `.claude/sweep-results/<slug>/artifacts/`.** Reads from `.claude/current-slice/`; writes to the gitignored target. Pre-close `slice.yaml` is written from the in-memory capture (D2.vii).
7. Step 3: wipe `.claude/current-slice/` (existing — DC-5 strict, F5-tolerant)
8. Step 4: sole `slice: <id> — complete` commit (existing — DC-4 + B5-tightened)
9. Step 5: persist terminal observability state (existing — DC-7)

The copy step is implemented as a private helper `_copy_artifacts_to_sweep_results(slice_id, pre_close_yaml_text)` in `lifecycle.py`. It is the only new commit-site-adjacent code; DC-4's "close_slice is the sole producer of `slice: complete`" property is preserved by construction (the helper does not invoke `_git`).

*Rationale:* preserves data the wipe would otherwise destroy, enabling future analytical use of phase-level provenance. Does not alter cairn's INV-008 sole-commit-source contract.

### D2 — Snapshot scope

The copy includes exactly:

i. `intent.md`
ii. `validation/approach.md`
iii. `implementation/notes.md`
iv. `integration/sweep-notes.md`
v. `handoff-phase-1.md`, `handoff-phase-2.md`, `handoff-phase-3.md`, `handoff-phase-4.md` (each, where present)
vi. `envelope-expansions.log` (where present)
vii. The pre-close `slice.yaml` text — captured in memory before Step 1 mutation; written by the helper as `<target>/slice.yaml`. Format: identical bytes to the on-disk `slice.yaml` at the moment Step 0.5 ran (with `status: in-progress` and the envelope intact).

**Step 0.5 read-failure classification.** If `SLICE_YAML.is_file()` returns False (operator manually rebased away) OR if `read_text()` raises `OSError` (transient unreadable state), `_pre_close_yaml_text` is set to the empty string and the helper writes an empty `<target>/slice.yaml`. This is **F5-tolerance (D6-style silent skip)**, NOT D7 loud-fail, because the existing `close_slice` already tolerates missing/unreadable `slice.yaml` throughout: Step 1 uses `read_slice_state(...) if SLICE_YAML.exists() else {}` defaulting to empty; `_is_slice_already_closed` Signal 1 returns False on missing/unreadable. Treating Step 0.5 differently would create a load-bearing precondition that downgrades the rest of close_slice's missing-slice.yaml tolerance — undesirable. The empty `<target>/slice.yaml` is honest signal that the snapshot couldn't capture the pre-mutation state, and is recoverable: the slice-id is encoded in the slug-keyed parent path, so the operator can reconstruct enough context from the directory name.

This is the full set of files the wipe (DC-5) would otherwise destroy, except for the `slice.yaml` survivor which DC-5 itself preserves and which we capture in its pre-mutation form.

*Rationale:* completeness — operator analysis of envelope-expansion frequency, Phase-2 ambiguity rates, etc. needs the full set. Selective preservation forces future re-design.

### D3 — Gitignored by default

`.claude/sweep-results/*/artifacts/` is added to `.gitignore`. The data is on-disk only; not committed.

*Rationale:* preserves the analytical data without polluting git history with mechanical churn. Operator can grep / analyze locally. The existing `.claude/sweep-results/<date>-sweep.md` integration-sweep notes remain committed as before — only the new per-slice `<slug>/artifacts/` subtree is gitignored. Re-considerable when a cross-machine analytical workflow lands and demands committed shape.

### D4 — Retention / compaction policy parked

v1 ships with no automatic GC, no compaction. Operator runs `du`-based diagnostics if disk-growth becomes a concern. Compaction policy (e.g. gzip after N days, prune after N slices) decided in a future slice once growth is observed.

*Rationale:* premature optimization. Ship the preservation; learn what disk-growth looks like in practice; design compaction with data.

### D5 — Supersedes "no archive directory for successful slices" stance

Amends `commands/claude-code/start-slice.full.md:210` from:

> "no archive directory for successful slices — the `status: complete` commit IS the git-history record"

to:

> "no archive directory **for committed history** — the `status: complete` commit IS the git-history record. Ephemeral artifacts (intent, validation/approach, implementation/notes, sweep-notes, handoff-phase-{1..4}, envelope-expansions.log, pre-close slice.yaml) ARE preserved on-disk at `.claude/sweep-results/<slug>/artifacts/` (gitignored) for analytical use."

*Rationale:* the prior stance was correct that the git-history record is canonical. The amendment narrows it to "no archive in *committed* form" — preserving the commit-narrative purity while enabling on-disk analytical preservation.

### D6 — Idempotency and F5-tolerance

The copy step is idempotent — re-closing an already-closed slice (DC-3 re-entry path) does NOT double-write the artifacts. Idempotency is preserved by construction: `close_slice`'s existing `_is_slice_already_closed(state)` short-circuit at the top of the function returns before any of Steps 0–5 run, including the new copy step.

F5-tolerant: missing source files (the operator-rebase corner — manual `git restore` or interactive rebase removed an artifact) do NOT break the close. The helper checks `src.is_file()` before each `shutil.copyfile`; absent files skip silently. Mirrors the existing `_wipe_current_slice` `FileNotFoundError` posture, and is the same posture as the Step 0.5 `slice.yaml` read failure (D2.vii).

*Rationale:* matches existing close_slice discipline. The new copy step inherits the same robustness.

### D7 — Two-tier copy-failure handling

Operational copy failures — disk-full (`ENOSPC`), permission-denied (`EACCES`), target-directory creation failure — propagate as `OSError` from the helper. `close_slice` does NOT catch them; the exception bubbles out, aborting the close BEFORE Step 3's wipe destroys the originals. The slice stays in `current_phase=4 status=in-progress` until the operator triages and re-runs.

This is distinct from D6's missing-source posture: missing-source is a quiet skip (operator-driven, expected); operational error is a loud abort (environmental, unexpected, must be visible).

The seam between D6 and D7 is precisely whether the operation is *bound by precondition* or *bound by environment*. F5 (missing source / unreadable slice.yaml at Step 0.5) is precondition: the operator manually altered state, the close should tolerate it. Operational errors at the copy step (disk-full mid-write, target-dir creation denied) are environmental: the host is broken, the close should not pretend success.

The two-tier choice mirrors Step 0's existing `sweep-notes-missing` posture: a precondition that fails loudly rather than silently producing a `slice: complete` commit against a broken environment.

*Rationale:* a `slice: complete` commit produced against a half-failed copy step would be a silent data loss — the artifacts directory would be partial, but git history would claim success. Loud-fail prevents this. Recovery is straightforward (free disk, fix perms, re-run) because the slice has not yet wiped or committed.

### D8 — INV-008 prose amendment

`docs/ARCHITECTURE.md` INV-008 (slice-close-contract) prose is amended to add a fourth separately-testable property describing the new copy step. The existing three properties (a) idempotent close, (b) DC-4 sole commit source, (c) cross-slice slug-keyed isolation are preserved verbatim.

The `invariant-check INV-008` block (`type: grep`, `pattern: "def close_slice"`, `target: "scripts/slice_orchestrator/lifecycle.py"`) is **NOT** amended. The grep target stays valid (the function is still named `close_slice` in the same file), and the new behavior is captured by the test file `tests/unit/test_slice_orchestrator_artifact_preservation.py` per the implementing slice's plan at `docs/plans/2026-04-26-slice-artifact-preservation-plan.md`.

*Rationale:* the architecture doc is the authoritative declaration of INV-008's contract; the new property must be reflected there, not just in the ADR. Validator stability is preserved by leaving the grep target untouched. The `supersedes-sections` frontmatter targets `slice-close-contract` (the ADR-canonical INV-008 source); ARCHITECTURE.md's prose is the propagated derived surface.

## Consequences

### Easier

- **Phase-level analytical queries become tractable.** The substrate program (`compression/lever-X-knowledge-index` and successors) gains a stable per-slice file tree to extract `EnvelopeExpansion`, `PhaseAmbiguity`, and similar entities from. Without this ADR, those entities have no source.
- **Failed-slice forensics extend from "git history only" to "git history + on-disk per-phase artifacts."** Operators triaging Phase-4 failures or pre-close crashes can read the actual `intent.md`, `approach.md`, etc. as they were at close time, not just the bundled summary.
- **Per-slice namespacing eliminates archive-path overlap across concurrent slices.** The new `<slug>/artifacts/` subtree has zero overlap across concurrent slices — each slice's artifacts live in a slug-distinct subtree. Pre-existing `<date>-sweep.md` contention is a separate concern (out of scope; the `<date>` keying is what causes that collision pattern, not the per-slice artifacts).
- **Manual operator analysis (grep, du, find) gains a stable target tree.** No need to capture artifacts mid-flight; they're preserved automatically at close.

### Harder

- **Disk usage grows unboundedly until D4 compaction lands.** Per-slice ephemerals are small (~10–30 KB typical), but accumulating across hundreds of slices over months will require operator attention. D4 explicitly defers GC; this is a deliberate trade.
- **Two storage locations for handoff content.** `handoff-phase-N.md` is bundled into the committed `.claude/handoff.md` AND preserved standalone in `<slug>/artifacts/handoff-phase-N.md`. The two are byte-different (the bundle concatenates with `\n---\n` separators; the artifacts preserve original formatting). Consumers must be clear on which source is canonical (git history) vs. analytical (on-disk).
- **Operational-error loud-fail (D7) creates a new failure mode where a slice closes Phase 4 successfully but `close_slice` itself errors.** The operator sees a non-zero exit, slice stays `in-progress`. Recovery is documented (fix the environmental issue, re-run); but the failure surface is new. Acceptable trade vs. silent data loss.
- **Test-file existing assertions on directory content post-close need re-checking.** The `tests/unit/test_close_slice_*.py` suite asserts on `.claude/current-slice/` survivors after close; those assertions remain valid (the new copy writes to a different parent dir). But cross-machine test runs that use a temp `.claude/sweep-results/` will see a new directory tree post-close. No existing test is broken by this; flagged for caution.
- **Architecture validator load-bearing on prose stability.** INV-008's prose now describes four properties instead of three. Future amendments to the prose (e.g. adding a fifth property) must keep the validator's grep target stable, as this ADR does.

## Alternatives Considered

### Alternative A: Move (rename) instead of copy

Rename each artifact from `.claude/current-slice/<rel>` to `.claude/sweep-results/<slug>/artifacts/<rel>` before the wipe. Saves disk (no double-write).

**Rejected because:**
- Asymmetric with `_wipe_current_slice`'s existing F5-tolerance — rename has different failure modes than copy (notably ENOTSUP across filesystems, which would force a copy+delete fallback, defeating the original "save disk" rationale).
- A half-completed rename leaves files in an unknown state ("which side has the file?"); a half-completed copy leaves both sides in known states (source intact, target partial).
- The disk-saving argument is theoretical: ephemerals total ~10–30 KB per slice. Doubling is not material.

### Alternative B: Post-close pipeline-substrate session

Write a separate session that runs after close, reads from git history (reflog or stash), and reconstructs ephemerals into `.claude/sweep-results/<slug>/artifacts/`.

**Rejected because:**
- The ephemerals are never in git history. They live only in `.claude/current-slice/` and are wiped before any commit could capture them. A post-close session has no recovery source.
- A pre-close session would require a new orchestration entry point and a new commit site, conflicting with DC-4.

### Alternative C: Embed artifact text in `sweep-notes.md` before close

Have Phase-4 integrator concatenate phase artifacts into `sweep-notes.md` as fenced blocks; sweep-notes is already bundled into `handoff.md` and committed.

**Rejected because:**
- Loses byte-identity (concatenation, fence escapes, formatting drift).
- Inflates the committed `handoff.md` blob — every slice's full ephemeral set becomes part of the commit narrative, defeating the "narrative purity" rationale of the original "no archive" stance.
- Cannot grep specific phase artifacts later — they're sub-strings of a larger document.

### Alternative D: Commit artifacts to an orphan branch

Use a git mechanism (orphan branch, notes ref) to commit ephemerals out-of-band from the main slice commit.

**Rejected because:**
- Conflicts with DC-4 (sole `slice: complete` commit). An orphan-branch write is still a commit.
- Adds a new merge-conflict surface for parallel slices.
- The `git notes` mechanism specifically is fragile against ref pruning; not a stable substrate for analytical queries.

### Alternative E: Status quo — wipe destroys

Make no change. Accept the loss of phase-level provenance.

**Rejected because:**
- The substrate program has analyses that depend on the artifacts. Without preservation, those analyses cannot be implemented.
- Failed-slice forensics is degraded relative to the moderate cost (~50 LOC + helper) of preserving.

### Alternative F: Capture-on-write (each phase agent dual-writes)

Have each phase agent (phase-1-writer, phase-2-skeptic, phase-3-implementer, phase-4-integrator) write its outputs to both `.claude/current-slice/<rel>` and `.claude/sweep-results/<slug>/artifacts/<rel>` simultaneously, eliminating the need for a copy step at close.

**Rejected because:**
- Distributes archival concern across four agent prompts (each must learn about the archive path), increasing prompt complexity and the surface area of "agent forgets to dual-write" failure modes — an L-005-class skill-coordination tax pattern.
- Splits authoritative state during the slice: which copy is "real" if the agent's two writes are not byte-identical (interrupted mid-write, partial output)?
- If the archive lives under `.claude/`, conflicts with Layer 3 wipe semantics (the archive paths would be wiped along with `.claude/current-slice/`). Moving the archive outside `.claude/` violates the "preserve in `.claude/sweep-results/`" model the ADR adopts.
- Harder to test: each phase agent's contract test gains assertions about archive-path writes. A pre-wipe copy in `close_slice` is a single test surface.

### Alternative G: Deferred-archive (next slice reads survivors at open)

Have `init_new_slice` read any files surviving in `.claude/current-slice/` at the start of a fresh slice, archive them, then proceed with init.

**Rejected because:**
- Strictly weaker than pre-wipe copy: for *successful* slices, DC-5 has already wiped `.claude/current-slice/` before close commits, so nothing remains for the next slice to recover. The mechanism only works for failed-slice paths where the orchestrator never reached close.
- The successful-slice path is the dominant volume by orders of magnitude; an alternative that addresses only the rare path is structurally inadequate.
- Adds state-coupling between consecutive slices that doesn't exist today (the next slice's init becomes contingent on the prior slice's terminal state). Violates the slice-isolation property `parallelism-v1` D2 commits to.

## Risk Register

- **Risk: D4 compaction debt accumulates faster than expected.** Per-slice 30 KB × 1000 slices = 30 MB; per-slice 100 KB × 10,000 slices = 1 GB. **Mitigation:** D4 explicitly parks compaction. Operator can `du -sh .claude/sweep-results/` periodically. The compaction policy slice is queued; if disk-pressure observed, that slice runs.

- **Risk: D7 loud-fail creates a "stuck slice" state where operator must manually intervene.** A slice that successfully completed Phase 4 but failed the copy step stays `in-progress` until human triage. **Mitigation:** Documented in D7's rationale. The recovery is straightforward (fix environment, re-run); the failure is environmental, not logical. Stuck-slice is preferable to silent data loss.

- **Risk: D2.vii pre-close `slice.yaml` capture timing creates a subtle dependency.** The `_pre_close_yaml_text` capture in Step 0.5 must happen *before* Step 1 mutates `status`. A future close_slice refactor that reorders Steps 0.5 and 1 would silently break D2.vii (the snapshot would carry `status: complete` instead of the intended `in-progress`). **Mitigation:** the implementing slice's `tests/unit/test_slice_orchestrator_artifact_preservation.py::test_d2_pre_close_slice_yaml_captured_not_post_close` (per `docs/plans/2026-04-26-slice-artifact-preservation-plan.md` Task 1) asserts on `status: in-progress` in the captured text. Refactor that breaks ordering breaks the test. The tripwire becomes load-bearing once the implementing slice lands its Phase-2 commit; until then it is aspirational.

- **Risk: Concurrent close on the same slice (race window between `_is_slice_already_closed` and the copy step) double-writes artifacts.** Two orchestrator processes invoking close_slice simultaneously could both pass the precondition check and both run the copy. **Mitigation:** `shutil.copyfile` is atomic per-file (open+write+close). Worst case is the same file written twice with same content. No corruption. The DC-3 idempotency contract from `slice-close-contract` covers this case at the lifecycle level.

- **Risk: Slug collisions between distinct slice-ids produce co-mingled artifacts.** Two slice-ids (e.g., `a/b-c` and `a-b/c`) flatten to the same `<slug>` and write to the same `<slug>/artifacts/` directory. **Mitigation:** `slice-close-contract` already commits to a slug-collision tripwire in `_slice_id_slug` (per that ADR's D5); any future cross-slice collision loud-fails before the copy step is reached. This ADR inherits that protection.

- **Risk: Provisional → firm transition for child invariants.** This ADR is firm at introduction. If field experience reveals an unanticipated failure mode in the copy step, retraction would require a superseding ADR — higher cost than retracting a provisional ADR. **Mitigation:** The mechanism is intentionally simple (~50 LOC), well-isolated (one helper, one wiring point), and operator-recoverable on every failure mode enumerated. The copy step is additive — it can be removed by deleting the helper invocation in `close_slice` and the gitignore directive, with no downstream code dependent on its existence.

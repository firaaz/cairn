```yaml
slice: compression/phase-4-sweepnotes-required
date: 2026-04-23
phase: 1-intent
invariants-touched: [INV-008]
adrs-referenced: [slice-close-contract]
envelope:
  - "scripts/slice_orchestrator.py"
  - "tests/unit/test_close_slice_sweepnotes_required.py"
  - "tests/unit/test_close_slice_add_surface.py"
  - "tests/unit/test_close_slice_hardened.py"
  - "tests/unit/test_close_slice_invocation.py"
  - "tests/unit/test_orchestrator_bug_fixes.py"
out-of-scope:
  - ".claude/agents/phase-4-integrator.md — agent contract unchanged (writes-list at :9 is already the spec this slice mechanically enforces); this slice does not rewrite the prompt"
  - "docs/adr/slice-close-contract.md — no ADR edits; INV-008 DC-4 is preserved, not amended"
  - "general close_slice refactor beyond the two point edits (presence check, add-surface extension)"
  - "Slice C candidate-set hygiene (D3) — separate follow-up slice"
  - "Slice D envelope-immutability-guard (D1) — separate follow-up slice"
  - "Slice F rolling-window /status surfacing (D3) — separate follow-up slice"
  - "Path C fleet-writes empirical gap — tracked separately"
  - "additional commit sites in scripts/slice_orchestrator.py — close_slice remains the sole producer of `slice: complete` (INV-008 DC-4)"
  - ".claude/sweep-results/ content or schema — only its staging surface is in scope; no writer or consumer of that directory is added or changed"
```

### What and Why

**Why.** Audit finding F3 (`docs/plans/2026-04-18-session-compression-audit.md`) documented Phase-4 evidence living only in a commit-message body rather than a committed artifact. Compression §8 D2 elevates "committed-artifact-first" to principle: `sweep-notes.md` must exist at close. INV-008 DC-4 (`docs/adr/slice-close-contract.md:63`) further requires that `close_slice` be the sole producer of `slice: complete`. Today the Phase-4-integrator prompt (`.claude/agents/phase-4-integrator.md:11,19`) demands `sweep-notes.md` before OK, but nothing in `close_slice` mechanically verifies the file on disk before committing. Separately, commit `a8d8f23` exhibited an orphan-artifact pattern: Phase-4 writes declared at `.claude/agents/phase-4-integrator.md:9` (`.claude/handoff.md`, `.claude/sweep.yaml`, `.claude/sweep-results/`) fell outside `close_slice`'s `_git add` surface (`scripts/slice_orchestrator.py:1766-1770`) and never reached the committed tree.

**What.** (1) `close_slice` gains a pre-commit presence check for `integration/sweep-notes.md`; absence aborts the close with non-zero exit, stderr error, and `orchestrator-result.json status: FAILED`. (2) The same `_git add` call is extended to stage every path the Phase-4 agent is contracted to write.

**Boundary.** INV-008 DC-4 preserved: the add list grows, but there is no new commit site; close_slice remains the sole commit source. No agent-prompt edits, no ADR edits, no new observability fields. Failure handling, wipe semantics (D3), and resume matrix (D4) are untouched.

### Specification Detail

**Operator amendment (2026-04-23, post-Phase-3 RAISE_ISSUE).** The envelope was expanded to include `tests/unit/test_close_slice_hardened.py`, `tests/unit/test_close_slice_invocation.py`, and `tests/unit/test_orchestrator_bug_fixes.py` after Phase 3 correctly flagged that the new D2 presence check in `close_slice` regresses 8 pre-existing tests — their local `_init_project` / `_stub_dispatch_ok` helpers never produce `.claude/current-slice/integration/sweep-notes.md`, so the new presence check fails the close. The amendment is mechanical-only: Phase 3 must update those three fixture helpers so they write a minimal `integration/sweep-notes.md` stub (any non-empty file content is sufficient — the presence check is existence-only, not schema-validated) at the point where `_init_project` lays down the scratch slice, or equivalently inside `_stub_dispatch_ok` to mirror what a real Phase-4 integrator writes. Do not modify test assertions, do not broaden test scope, do not introduce new fixtures — only close the fixture-vs-invariant gap the amendment was written to fix.

All primary edits land in `scripts/slice_orchestrator.py` inside the existing `close_slice` function. No new functions are required; both orchestrator changes are localized to the pre-commit block.

**1. sweep-notes presence check (primary — enforces D2).**

Before the sole `slice: complete` commit, and after `_is_slice_already_closed(state)` has been consulted, `close_slice` must verify that `.claude/current-slice/integration/sweep-notes.md` exists as a file on disk.

- If present: proceed to the normal add + commit sequence.
- If absent: do not stage, do not commit, do not wipe. Instead:
  - Persist `orchestrator-result.json` with terminal `status: "FAILED"` and a machine-readable reason field naming `phase-4-sweepnotes-required` / D2 / INV-008 DC-4 (use a short literal token e.g. `reason: "sweepnotes-missing-at-close"`; keep the exact token stable so downstream consumers can match).
  - Emit a single-line stderr message citing the ADR principle and the absent path.
  - Return / exit the orchestrator with a non-zero exit code, consistent with the existing FAILED-terminal path.
- The presence check is gated by `_is_slice_already_closed`: if the slice is already closed (`slice: complete` already on HEAD, wipe already applied per D3), the check is bypassed — at that point `sweep-notes.md` has correctly been wiped, and re-asserting presence would false-positive. This preserves D1 idempotency.

**2. `_git add` surface extension (secondary — fixes orphan-artifact pattern).**

The `_git add` invocation at `scripts/slice_orchestrator.py:1766-1770` currently enumerates a closed set of paths. Extend that argument list to include every path declared in `.claude/agents/phase-4-integrator.md:9` that is not already staged:

- `.claude/handoff.md` (already produced by `_bundle_handoff_md()` per DC-3; ensure it is explicitly staged here if not already).
- `.claude/sweep.yaml`.
- `.claude/sweep-results/` — stage via `git add -A .claude/sweep-results/` so any newly-created file under that directory is staged en-masse without requiring the orchestrator to know filenames. Tolerate the directory being absent (invoke add only when path exists, or absorb the non-zero return as a no-op for the absent-directory case — implementer choice; both satisfy the spec).

No new commit invocations. No new `_git` call sites. The add expansion happens inside the one pre-existing pre-commit staging block.

**3. Idempotency and interaction with other INV-008 decisions.**

- **D1 (idempotent close).** Short-circuit logic in `_is_slice_already_closed` runs first; when it returns True, close_slice returns early as today — the presence check is not executed. Re-running close_slice on an already-closed slice remains a no-op.
- **D3 (wipe semantics).** Wipe continues to delete every non-`slice.yaml` file in `.claude/current-slice/` after the commit succeeds. Wipe is not invoked on the FAILED-on-absent-sweepnotes branch.
- **D4 (resume reconciliation).** A slice aborted by the new presence check leaves `slice.yaml: in-progress`, HEAD unchanged, `orchestrator-result.json: FAILED`. This triple is already covered by the FAILED row of D4's matrix (`docs/adr/slice-close-contract.md:106`) — "prior run terminated as FAILED; manual intervention"; no new matrix row needed.
- **DC-4 (sole commit source).** The add-surface extension changes *what* the single `slice: complete` commit stages, never *where* commits are issued. No additional `git commit` invocations.

### Verification (Definition of Done)

Phase 4 PASSES iff all of the following hold:

1. **Two RED-at-Phase-2 tests go GREEN** inside the envelope:
   - `tests/unit/test_close_slice_sweepnotes_required.py` — with `.claude/current-slice/integration/sweep-notes.md` absent, `close_slice` exits non-zero, `slice: complete` is NOT on HEAD, and `orchestrator-result.json` terminal `status == "FAILED"` with the stable reason token.
   - `tests/unit/test_close_slice_add_surface.py` — working-tree edits to `.claude/handoff.md` and `.claude/sweep.yaml`, plus a newly-created file under `.claude/sweep-results/`, all appear in the tree of the `slice: complete` commit (`git show HEAD -- <path>` returns the staged content).

2. **Full `uv run pytest` is green.** Pre-existing INV-008 tests continue to pass:
   - `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop` (D1 idempotency).
   - `tests/unit/test_close_slice_hardened.py::test_close_slice_produces_single_slice_complete_commit` (DC-4 single commit).
   - `tests/unit/test_close_slice_hardened.py::test_run_phase_loop_skips_commit_at_phase_4_boundary` (DC-4 skip).
   These confirm the add-surface extension does not introduce a second commit site and the presence-check ordering does not break idempotency.

3. **Architecture validator clean.** `python3 scripts/validate_architecture.py` exits 0. If Phase 3 adds test IDs, the INV-008 `invariant-check` block in `docs/ARCHITECTURE.md` picks them up via `/refresh-architecture`; this is a Phase-4 observation, not a Phase-3 edit.

4. **`sweep-notes.md` at close** records INV-008 DC-4 PASS with `file:line` citations for (a) the presence check and (b) the extended add list in `scripts/slice_orchestrator.py`. The audit follow-up `phase-4-sweepnotes-required` is marked closed in the sweep notes.

5. **Envelope discipline.** `git diff` against pre-slice HEAD shows changes confined to the three envelope files plus `.claude/current-slice/` artifacts. `.claude/agents/phase-4-integrator.md` and all ADRs are byte-identical to pre-slice. No new `git commit` invocations in `scripts/slice_orchestrator.py` (grep the diff).

# Compression Followup — Design & Slice Plan

**Branch:** `feature/compression-followup` (off `dev` at `ade3966`)
**Status:** Open 2026-04-27. Single design doc anchoring seven candidate slices.
**Supersedes (operationally, not in ADR sense):** the stale `feature/compression` branch, whose only un-replicated-on-dev work is `compression/triager-superseded-test-heuristic` and is forward-ported by Slice 1 below.

---

## 1. Mission

Clear the closeout-named carry-over debt (`docs/features/compression.md:63-69`) plus the newly-discovered substrate consumer-corpus gap, on a single short-lived feature branch, so the compression program's cost-discipline promise extends to downstream consumers and the inherited reds resolve.

**Exit predicate:** every item in `docs/features/compression.md`'s "Carry-over debt at close" list is either closed by a slice on this branch, struck through with citation to the closing slice, or explicitly re-deferred with a named justification.

---

## 2. Why this branch exists (context)

Two prompts:

1. **Newly discovered architectural gap — substrate consumer-corpus.** During the 2026-04-27 wiring of `complex-rag-analysis` to the compression program, it surfaced that `cairn-knowledge` MCP indexes only cairn's own corpus (`scripts/cairn_query/__init__.py:62-69` hard-codes relative paths). Consumer projects cannot `lookup` / `search` / `cypher` their own domain ADRs / lessons / architecture. The compression program's headline savings — `INV-009` cost-per-slice-budget, the ~$18.71 baseline — are therefore **cairn-internal only**. No doc qualifies the savings as such. This directly undermines the program's value to the audience it's designed for.

2. **Pre-existing carry-over debt that hasn't been sliced.** Five entries from the closeout (`docs/features/compression.md:63-69`); none had a home before this branch.

A long-lived `feature/compression` branch existed but was found stale: dev had absorbed 11+ lever / cost-discipline slices via shorter-lived sibling branches while `feature/compression` accumulated only one new slice (`compression/triager-superseded-test-heuristic`, closed `e46969d`). Reconciling that branch was net-negative; we forward-port the one delta worth saving and archive the rest. The lesson learned about long-branch divergence is captured as L-021 (renumbered during rebase onto dev; was L-016 at original authorship 2026-04-27).

---

## 3. Scope inventory — seven candidate slices

Each entry below is intent-style, not a full Phase-1 brief. Phase-1 writer drafts the brief at `/start-slice` time.

### Slice 1 — `compression/triager-superseded-forward-port`

Re-apply the orchestrator code + tests from the stale `feature/compression`'s `compression/triager-superseded-test-heuristic` slice (closed at `e46969d` 2026-04-21). The slice already passed Phase 4 once; this is delta-only re-application, not new design work.

**Forward-port mechanics:** the `compression/triager-superseded-test-heuristic` slice's intent text (visible in `.worktrees/compression/.claude/features/compression.yaml`) names the surface concretely — `dispatch_triager` heuristic + prompt amendment + one Phase-2 regression test file `tests/unit/test_triager_superseded_heuristic.py`. Either:
- **Path A (cherry-pick):** `git cherry-pick` the slice's Phase-3 implementation commit + its Phase-2 test commit + the orchestrator/triager prompt commits. The squash-target subjects on `feature/compression` are visible in `git log feature/compression..` for the slice.
- **Path B (re-derive from diff):** `git diff dev..feature/compression -- scripts/slice_orchestrator/ tests/unit/test_triager_superseded_heuristic.py .claude/agents/issue-triager.md docs/operational-reference.md` and apply selectively.

Path B is preferred — the dev tip has cumulative work (lever-X/Y/Z/cost-discipline) that the original feature/compression commits don't anticipate; cherry-picking would surface noisy conflicts. The diff approach scopes to the four files the original slice modified.

**Out of scope:** any refinement to the heuristic. Exact re-application; if the heuristic later proves too narrow or too broad, that's a future slice.

### Slice 2 — `substrate/slice-4-disk-fallback`

Implement `SliceExtractor` disk-fallback for the squash-collapses-slice-commits problem (L-015). `scripts/cairn_query/extractors/slice.py:74` currently runs `git log --grep='^slice: .* — complete$'` with no fallback. After this slice, the extractor reads from `.claude/sweep-results/<slice-id>/` (per ADR `slice-artifact-preservation`) and `.claude/completed-slices/<slice-id>/` (failed/archived) in addition to git log. Unblocks the four `@pytest.mark.xfail(strict=True)` tests in `tests/unit/test_extractor_slice.py:30-49`.

**Out of scope:** generalizing the fallback into a shared helper (deferred per L-015's "Mechanism" — only lift to a helper if a second extractor type recurs the same coupling).

### Slice 3 — `substrate/consumer-corpus`

Parameterize `rebuild_from_sources(*, sources_root: Path = Path("."))` in `scripts/cairn_query/__init__.py:46-69`. Thread `sources_root` through each extractor's `__init__` (most already accept `Path` args). Wire `SliceExtractor`'s pre-existing-but-unused `repo_root` parameter at `scripts/cairn_query/extractors/slice.py:66-72`. In `mcp_servers/cairn_knowledge/server.py`, read `CAIRN_QUERY_REPO_ROOT` env at startup; default to cairn root for backwards-compat. `mcp_servers/cairn_knowledge/tools.py:35` passes the value into `rebuild_from_sources`.

**v1 = Option A: single-corpus-per-process.** Consumers set the env in their `.mcp.json` `env:` block. Document Options B (multi-corpus union) and C (two MCP server registrations) in the slice's `intent.md` as deferred — not implemented in v1.

**Out of scope (for this slice, but cited in slice 4):** cost-claim corrections in ADRs or feature docs.

### Slice 4 — `compression/cost-claim-correction`

Qualify `INV-009` cost-per-slice-budget claims to mark the savings as cairn-internal-or-equivalent-corpus until and unless Option B (multi-corpus union) lands. ADR amendment via firmness-frontmatter edit (allowed under `reversibility-guard.sh`'s `ADR_EDITORIAL_FIX=1` path if the prose change exceeds frontmatter; otherwise straight Edit). Doc edits:

- `docs/adr/cost-per-slice-budget.md` — qualifier paragraph in the rationale.
- `docs/features/compression.md` line 59 — qualify "~$18.71 baseline" as cairn-internal until consumer-corpus support is wired in production downstream.
- `docs/plans/2026-04-25-knowledge-substrate-design.md:42` — append a corollary that "downstream consumers get it transparently" was mechanical-transparency-only in v1; functional transparency arrives with `substrate/consumer-corpus`.

**Sequenced after Slice 3** so the corrections describe shipped reality.

### Slice 5 — `compression/resume-state-machine-orphan`

Wire `_reconcile_resume_state` in `scripts/slice_orchestrator/resume.py:154` (function defined, never called). Documented at `docs/features/compression.md:67`. Small, isolated. Add the call site, add at least one Phase-2 regression test demonstrating the reconciliation actually fires under the matrix conditions the function handles.

### Slice 6 — `compression/cost-re-measurement`

Re-run the cost-per-slice measurement against the ~$18.71 baseline after Lever-Z-fixup S1 restored `Bash` to `phase-1-writer` (per `docs/features/compression.md:68`). Data-only artifact: produces a measurements file under `docs/plans/measurements/2026-04-{XX}-compression-followup-cost-rerun.txt` analogous to `2026-04-12-slice-003.txt`. No code changes.

**Sequenced after Slices 1+5** so the orchestrator surface is stable before measurement.

### Slice 7 — `compression/upgrade-doc-bug-fixes`

Fix the two consumer-breaking bugs in `docs/upgrading-from-pre-compression.md` discovered 2026-04-27 during complex-rag-analysis migration:

- **Delta 1:** the SessionStart hook path. Doc says `.slice-system/scripts/role-cheatsheet.sh`; actual path is `.slice-system/checks/role-cheatsheet.sh`.
- **Delta 2:** the MCP server command. Doc shows `"command": "python", "args": ["-m", "mcp_servers.cairn_knowledge"]`; bare `python` isn't on PATH in Claude Code MCP subprocesses, so the server silently fails to start. Working invocation: `"command": "uv", "args": ["run", "--directory", ".slice-system", "python", "-m", "mcp_servers.cairn_knowledge"]`.

Also strengthen each delta's Verify snippet to runtime-invoke (e.g., `bash .slice-system/checks/role-cheatsheet.sh </dev/null | head -1` should print a JSON envelope; `uv run --directory .slice-system python -c "import mcp_servers.cairn_knowledge"` should exit 0). The current jq snippets only check structural presence — both bugs survived the original verify-pass because nothing actually invoked the wired path.

**Could land first** as a quick-win unblocking other consumers attempting migration.

---

## 4. Sequencing & dependencies

```
1 (forward-port)          ── independent
2 (slice-4-disk-fallback) ── independent
3 (consumer-corpus)       ──┐
                            └─ 4 (cost-claim-correction)
5 (resume-orphan)         ── independent
6 (cost-re-measurement)   ── after 1 + 5
7 (upgrade-doc-fix)       ── independent (recommended quick-win)
```

Slices 1, 2, 3, 5, 7 can run in any order or parallel-by-worktree. Slice 4 sequences after 3 (so corrections describe shipped reality). Slice 6 sequences after 1 and 5 (so the orchestrator is settled before measurement).

---

## 5. Out of scope (this branch)

- **Path C fleet-writes empirical gap** (memory `path_c_fleet_writes_empirical.md`). Separate concern; not a compression-program debt item.
- **Slices C/D/F (candidate-set hygiene, envelope-immutability-guard, rolling-window /status surfacing).** These are stale labels in out-of-scope clauses of `docs/plans/2026-04-20-compression-pipeline-hardening-plan.md`; none have a firm spec. Each needs a `/decision` before it's sliceable.
- **`INV-004` turn-1 token-budget OOS env-dependent red.** Pre-existing per `.claude/sweep.yaml`; environment-coupled, not a compression-program regression. Tracked but not in this branch's scope.
- **L-015 candidate (Phase-3 parallel in-session fan-out git-index race).** Single observation per `docs/features/compression.md:69`; raise if recurrence.
- **Cleanup of the stale `feature/compression` worktree's drift** (`M README.md`, `?? docs/why-cairn.md`). Per the worktree's own handoff:18, "pre-existing, unrelated." If `docs/why-cairn.md` is worth saving, that's a separate decision.

---

## 6. Branch & merge strategy

**Off `dev`.** Single squash-merge back to `dev` at completion, per cairn merge protocol (`docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`).

**Branch lifetime ceiling: 14 days from open.** If the seven slices haven't all landed (or been re-deferred) by 2026-05-11, force a midpoint reckoning: rebase forward against current dev, evaluate divergence, and either ship what's done as a partial squash or spawn a fresh sub-branch off current dev for the remainder. Long-branch divergence is the failure mode L-021 names; this branch will not repeat it.

**`feature/compression` retirement.** After Slice 1 (forward-port) lands here, recommend `git tag archive/compression-pre-followup feature/compression && git worktree remove .worktrees/compression`. Do not execute without user confirmation — destructive-ish action.

---

## 7. Risk & open questions

- **Slice 3 design-space choice.** Option A (env-var single-corpus) is the v1 recommendation, but if a phase agent on a consumer slice demonstrably needs to query both cairn methodology and consumer domain in one call, Option B (multi-corpus union) becomes load-bearing. The slice's Phase-1 writer should re-evaluate against actual phase-agent traces from a consumer slice, not just the design-doc framing.
- **Slice 4 ADR amendment scope.** `cost-per-slice-budget` is firm. The amendment is a qualifier, not a contract change. If `reversibility-guard.sh` flags the edit, the right escape hatch is `ADR_EDITORIAL_FIX=1` for prose-only changes; if the qualifier requires re-stating an invariant, the slice escalates to an ADR supersession.
- **Slice 6 measurement noise.** The $18.71 baseline was measured under specific orchestrator config; lever-Z-fixup changed phase-1-writer's tool surface. The measurement may surface a regression masquerading as Bash-restoration cost. Phase-4 integrator must compare against `docs/plans/measurements/` precedents to disambiguate signal.
- **Slice 7 verify-snippet upgrade.** Strengthening the upgrade-doc verify snippets to runtime-invoke is a doc-only change but it changes the contract for downstream-migration validation. Consider whether the upgrade doc needs versioning.

---

## 8. Exit criteria for this branch

The branch can be squash-merged to dev when all five hold:

1. Either each of slices 1–7 is closed (Phase-4 sweep clean, all invariants PASS, no open RAISE_ISSUE) **or** explicitly re-deferred with a one-paragraph justification appended to `docs/features/compression.md`.
2. `tests/unit/test_extractor_slice.py`'s four xfails go GREEN (Slice 2 effect).
3. `complex-rag-analysis` (or another consumer) can `lookup` an entity from its own corpus through `cairn-knowledge` (Slice 3 effect).
4. `docs/upgrading-from-pre-compression.md` verify snippets pass when run against a fresh consumer setup (Slice 7 effect).
5. Branch age ≤14 days, or partial-merge has happened mid-flight per §6.

---

## 9. References

- `docs/features/compression.md` — closeout doc; carry-over debt source-of-truth.
- `docs/lessons.md` L-015 — squash-merge / extractor coupling (slice 2 closes the structural fix).
- `docs/lessons.md` L-021 — long-lived branch divergence (added in same commit as this doc; sets the 14-day ceiling). Renumbered from L-016 during 2026-05-02 rebase onto dev; dev had taken L-016 through L-020 with sibling content during the branch's lifetime — itself a self-applying instance of the lesson.
- `docs/plans/2026-04-25-knowledge-substrate-design.md:42` — the "transparently" framing slice 4 corrects.
- `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` — squash-merge protocol this branch follows.
- `docs/plans/2026-04-20-compression-pipeline-hardening-design.md` — structural template for this doc.
- `docs/adr/cost-per-slice-budget.md` — INV-009; slice 4 amends.
- `docs/adr/slice-artifact-preservation.md` — `.claude/sweep-results/` source path slice 2 reads from.

---
id: compression
name: "Compression program"
status: merged
opened: 2026-04-19
merged: 2026-04-27
archive-branch: archive/compression
---

# Compression program

## What shipped

The slice pipeline graduates from a prose protocol to a Python state machine with structural enforcement and a typed knowledge substrate. Phase agents now query a kuzudb-backed graph of cairn's markdown corpus through a FastMCP server (`cairn-knowledge`) instead of re-reading source markdown per phase, eliminating the dominant per-slice cost driver. Per-phase model selection and extended-thinking budgets land alongside, retuning the per-slice envelope to a $18.71 baseline. Role-keyed enforcement (`checks/role_guard.py`) closes the prompt-layer escape hatch by structurally denying canonical-knowledge reads outside the substrate query path for all four phase roles.

## Slices

Listed by close date. `compression/*` and `cost-discipline/*` slices were the program's primary tracks; `housekeeping/*` slices were merge-prep cleanup that landed in the same span.

- **compression/orchestrator-hardening** — 2026-04-19 — complete. Pre-substrate orchestrator robustness pass.
- **compression/doc-cleanup-tail** — 2026-04-19 — complete. ADR/spec residual prose from the substrate design phase.
- **housekeeping/post-slice-a-tidy** — 2026-04-19 — complete. Post-Slice-A tree cleanup.
- **compression/slice-1-foundation** — 2026-04-20 — complete. `pyproject.toml` standing-dep set + `scripts/cairn_query/` package skeleton (entity models, schema bootstrap).
- **compression/triager-superseded-test-heuristic** — 2026-04-21 — complete.
- **housekeeping/post-inv008-and-substrate-bugs** — 2026-04-21 — complete.
- **compression/phase-1-handoff-stage-surface** — 2026-04-23 — complete.
- **compression/phase-4-sweepnotes-required** — 2026-04-23 — complete.
- **cost-discipline/track-0-telemetry** — 2026-04-24 — complete. Per-phase token/cost capture; `INV-009` baseline mechanism.
- **cost-discipline/lever-1-per-phase-model** — 2026-04-24 — complete. `AGENT_MODEL_CONFIG` with role-specific model + thinking-budget defaults.
- **compression/lever-2-orchestrator-split** — 2026-04-25 — complete. Single-file `slice_orchestrator.py` (~3.5kLOC) split into a package: `core / git / telemetry / resume / dispatch / lifecycle / __main__`. Pre-split monkeypatch surface preserved via `_MirroringModule` facade.
- **compression/slice-artifact-preservation** — 2026-04-26 — complete. `INV-010`: phase artifacts (intent.md, validation/, integration/) preserved into `.claude/sweep-results/<slice>/` at slice close.
- **compression/lever-x-knowledge-index** — 2026-04-26 — complete. Substrate seven-extractor build (Invariant, Decision, Lesson, SpecSection, OpRule, Feature, Slice).
- **compression/lever-Y-mcp-substrate** — 2026-04-26 — complete. FastMCP server `cairn-knowledge` (stdio transport per ADR D6) exposing `lookup`, `search`, `path_bindings`, `cypher`.
- **compression/lever-Y-mcp-substrate-fixup** — 2026-04-26 — complete.
- **compression/learnings-capture** — 2026-04-26 — complete. (First attempt failed 2026-04-26 with Phase-3 cluster fan-out gap; retried under same id.)
- **cost-discipline/lever-1-tier-retune** — 2026-04-26 — complete. ~$18.71 per-slice baseline.
- **compression/lever-Z-substrate-full-pipeline** — 2026-04-26 — complete. Query-first directives across all four phase agents; `role_guard` `ROLE_DENY_READ` extended to phases 2/3/4 via `_CANONICAL_DENY_PATTERNS`.
- **compression/lever-Z-fixup** — 2026-04-27 — complete. Restored `Bash` to `phase-1-writer` `tools:` frontmatter (S1, dispatch defect fix); consumer-migration doc (S2); L-014 lesson (S3); `_ARTIFACT_RELPATHS` paper-cuts (S4). L-014 self-application surfaced three inversion candidates pre-Phase-3.

## ADRs

**Created:**
- [`compression-infrastructure-bootstrap`](../adr/compression-infrastructure-bootstrap.md) — provisional. Authorized mechanism for substrate hookpoints.
- [`slice-close-contract`](../adr/slice-close-contract.md) — firm. Slice-close criteria (≥4 slices, sweep.yaml emission, artifact preservation).
- [`orchestrator-observability`](../adr/orchestrator-observability.md) — provisional. Telemetry state shape + heartbeat.
- [`cost-per-slice-budget`](../adr/cost-per-slice-budget.md) — `INV-009` cost-per-slice envelope.
- [`slice-artifact-preservation`](../adr/slice-artifact-preservation.md) — firm. `INV-010` preservation contract.
- [`cairn-substrate-and-fastmcp`](../adr/cairn-substrate-and-fastmcp.md) — firm. v1 standing-dep set (pydantic, kuzudb, mistune, typer, fastmcp, pyyaml); FastMCP adapter; agent-context structural lockdown. Retires the prior stdlib-only / Rust-mapping-target wording in `CLAUDE.md:26`.

**Touched via propagation:** identifier-scheme rename sweep already landed; subsequent compression slices added cross-references but did not re-rename.

## User-visible changes

Mirrors the `CHANGELOG.md` `[Unreleased]` block. Highlights:

- **Knowledge substrate v1.** `cairn-knowledge` MCP server (stdio); `scripts/cairn_query/` package; kuzu graph store; four query tools (`lookup`, `search`, `path_bindings`, `cypher`). Read-only.
- **Slice-pipeline orchestrator.** `scripts/slice_orchestrator/` four-phase loop (Intent → Validation → Implementation → Integration); per-phase agents at `.claude/agents/phase-{1-writer,2-skeptic,3-implementer,4-integrator}.md`; CLI at `PYTHONPATH=scripts uv run python -m slice_orchestrator --brief|--resume|--legacy`; sweep-results artifact preservation; resume reconciliation matrix.
- **Role-keyed enforcement.** `checks/role_guard.py` canonical-knowledge read-class lockdown across all four phase roles; envelope-bound write enforcement for `phase-3-implementer`. Bash-token extraction (`_bash_path_tokens`) covers `cat` / `head` / `grep` paths.
- **Cost discipline.** Per-phase model config with extended-thinking budgets; Track-0 telemetry; lever-1 retune complete (~$18.71 baseline).
- **Lessons L-001 through L-015.** Latest: L-015 (squash-merge / extractor coupling, this commit).
- **Consumer migration guide.** [`docs/upgrading-from-pre-compression.md`](../upgrading-from-pre-compression.md) — five wiring deltas with one Verify snippet per delta.

## Carry-over debt at close

- **Substrate Slice 4 — SliceExtractor disk fallback.** `scripts/cairn_query/extractors/slice.py:74` reads `git log --grep='^slice: .* — complete$'` with no fallback; the dev squash collapses per-slice close commits, so extraction returns empty on dev tip. Four `tests/unit/test_extractor_slice.py` tests are `xfail(strict=True)` pending the disk-fallback slice (read from `.claude/sweep-results/` + `.claude/completed-slices/` in addition to git log). See L-015.
- **`INV-004` turn-1 token-budget OOS env-dependent failure.** `test_inv004_turn1_token_budget` measures Claude-Code session tokens; pre-existing per `.claude/sweep.yaml`. Not a compression-program regression.
- **`_reconcile_resume_state` orphan.** `scripts/slice_orchestrator/resume.py:154` — function defined, never called. Out-of-scope per Lever-Z-fixup intent; queued for its own slice.
- **Cost re-measurement vs $18.71 baseline.** Lever-Z-fixup S1 (`Bash` restored to phase-1-writer) unblocked re-measurement, but the run was not made on this branch. Queued.
- **L-015 candidate from feature-branch dogfood.** Phase-3 parallel in-session fan-out can race on the shared git index; observed once during lever-Z-fixup as the `fd88b95` mis-attribution. Documented in feature-branch handoff; promotion to lessons.md deferred (single observation; raise if recurrence).

## Design & research docs

- [`docs/plans/2026-04-25-knowledge-substrate-design.md`](../plans/2026-04-25-knowledge-substrate-design.md) — substrate program design doc.
- [`docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`](../plans/2026-04-18-feature-to-dev-merge-protocol-design.md) — merge protocol this feature instantiates (second instance after identifier-scheme; amended in this closeout to add the Structural-test-design-mismatches recovery class).
- Compression-era plan corpus under `docs/plans/2026-04-{19..27}-*.md`.

## Archaeology

```
git log archive/compression
```

335 pre-squash commits preserved on the archive branch (created at merge time from the feature branch rename). See `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` §Archaeology preservation for the rationale.

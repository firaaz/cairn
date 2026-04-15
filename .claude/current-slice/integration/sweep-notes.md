---
slice: SLICE-015 (identifier-scheme/scheme-adr)
phase: 4-integration
sweep: #10 (post-SLICE-015)
date: 2026-04-15
verdict: PASS
---

## Mechanical gates

- `integration_gate.py` — Step 3 (invariant check) PASS; Step 4a (ruff) PASS; Step 4b (pytest) FAIL on pre-existing `uv.lock` envelope-compliance noise only (halted at first failure).
- Full pytest with pre-existing `uv.lock` noise deselected: **202 passed, 2 deselected** (test_slice_005_design_decomposition::test_v7_envelope_compliance and test_v4_envelope_compliance, test_sweep_debt_cleanup::test_v4_envelope_compliance — all three red on `uv.lock` modification attributable to 364f297 "chore: adopt uv for python deps", not to SLICE-015).
- `validate_architecture.py` — ALL CHECKS PASSED; invariants verified: 7; ADR files checked: 9.
- `snapshot_diff.py --diff` — three out-of-envelope items flagged; all attributable to authorized commits (see Disposition below).

## Invariant evidence (file:line citations)

- **INV-001** — `commands/claude-code/start-slice.md` exists. Mechanism preserved.
- **INV-002** — `docs/operational-reference.md:197` ("Token budget: 150 to 400 tokens, whole-file.") — three-layer discipline documented; untouched this slice.
- **INV-003** — `docs/operational-reference.md:18` ("### Phase 1: Intent") — four-phase pipeline definition intact.
- **INV-004** — `tests/unit/test_context_budget.py` passes (22k token ceiling) per full-suite run above.
- **INV-005** — `docs/adr/identifier-scheme.md:2-8` (`id: identifier-scheme`, `name: "Identifier scheme — id + name two-field model"`, `status: accepted`, `firmness: firm`, `supersedes: [ADR-005]`, `superseded-by: null`). Governing ADR present; two-field model authoritatively defined. `docs/ARCHITECTURE.md:49-55` — INV-005 text rewritten to cite the two-field id+name model; validator anchored via ADR-006 proxy (substrate gap named in text, deferred to follow-on slice).
- **INV-006** — `.claude/features/identifier-scheme.yaml` exists; feature-slice decomposition governs this slice's ordering.
- **INV-007** — `commands/claude-code/handoff.full.md:54` — cross-feature index format defined; handoff Tier-1 integration intact.

## Cross-slice failure modes probed

| # | Failure mode | Check | Result |
|---|---|---|---|
| 1 | Schema drift (two-field ADR frontmatter vs. validator) | `validate_architecture.py` parses `docs/adr/identifier-scheme.md` cleanly, 9/9 ADR files OK | PASS |
| 2 | Tool contract break (hooks vs. flat-slug ADR filename) | ADR authored; `reversibility-guard.sh` bootstrap-window gap is named and scoped to `identifier-scheme/hook-tolerance` (intent.md:56-57, 64) | KNOWN-GAP (named) |
| 3 | Invariant interaction (INV-005 rewrite breaking INV-006 feature-file dependency or ADR-006 citation chain) | Validator 7/7 invariants green; INV-005 cites ADR-006 as proxy anchor, INV-006 file-exists check unchanged | PASS |
| 4 | Out-of-envelope edits by slice implementation | Snapshot-diff flagged 3 items; all attributable to Phase 4 D1 refresh + pre-slice design + D1 test remediation | AUTHORIZED |
| 5 | Handoff staleness (Blocked/Pending drift) | All five items still load-bearing (see Staleness section) | CLEAN |
| 6 | Import/config conflicts | N/A — no runtime modules in cairn (substrate is markdown + shell + Python validator) | N/A |

## Snapshot diff disposition

Three files flagged by `snapshot_diff.py --diff`:

1. `docs/ARCHITECTURE.md (changed)` — authored by af05bf2 "docs: refresh ARCHITECTURE.md from ADRs" (Phase 4 D1 automated refresh; pipeline-substrate commit per `docs/lessons.md` L-001; authorized under INV-001 by being named).
2. `docs/plans/2026-04-15-identifier-scheme-design.md (new)` — authored by pre-slice commit 1ab94f9 "docs: identifier-scheme design (fleet-coordinator Feature 1 split)"; snapshot baseline predates this commit. Not SLICE-015 implementation output.
3. `tests/unit/test_slice_005_design_decomposition.py (changed)` — authored by 20c5eff "test: widen test_v2_frontmatter_valid to accept superseded ADRs" (D1 gate remediation: widening SLICE-005's frontmatter test to accept the new `status: superseded` produced by this slice's ADR-005 edit). Legitimate Phase 4 D1 remediation, not silent scope expansion.

None are unauthorized out-of-envelope implementation edits. Baseline refreshed after sweep commit.

## Staleness check (handoff Blocked/Pending vs. git log)

- "Validator substrate gap: regex parses only `ADR-(\d+)`" — STILL LOAD-BEARING. INV-005 text now documents the proxy-anchor workaround; widening queued for a follow-on slice (explicitly NOT `hook-tolerance`).
- "Hard ordering: `identifier-scheme/hook-tolerance` MUST be next slice; bootstrap-window gap open" — STILL LOAD-BEARING. Gap persists until hook-tolerance lands.
- "Pre-existing pathologies still red: `test_v7_envelope_compliance`, `test_v4_envelope_compliance`" — STILL LOAD-BEARING. Root cause unchanged (`uv.lock` modified by 364f297, outside SLICE-005/SLICE-007 envelopes, flagged forever by those retroactive envelope tests). Housekeeping slice deferred.
- "Pre-existing drift: `docs/plans/measurements/2026-04-12-slice-003.txt`, `uv.lock`" — STILL LOAD-BEARING. Dirty working tree unchanged.
- "D3 bypass log 2/3 in rolling window" — STILL LOAD-BEARING. No bypass fired this slice; counter unchanged.

No stale entries to prune.

## Invariants touched

Per `slice.yaml`: `invariants-touched: []`. INV-005's *text* was rewritten by the D1 refresh (af05bf2) to reflect ADR-005's supersession by `identifier-scheme`, but the invariant's substance — mechanical identity — was unchanged; this is derived-view update, not an invariant mutation. Declaration remains accurate.

## Verdict

**PASS.** SLICE-015 authored the governing ADR, superseded ADR-005 in the frontmatter-only mode permitted by `reversibility-guard.sh`, and the D1 refresh cascaded INV-005's prose to match. All seven invariants pass mechanical checks. The three snapshot-diff flags are each accounted for by authorized commits (D1 refresh, pre-slice design, D1 test remediation). Known gaps — bootstrap-window ADR filename, validator ADR-ID regex, envelope-test `uv.lock` noise — are named, scoped to follow-on slices, and tracked in handoff. Slice ready for `superpowers:requesting-code-review` and close.

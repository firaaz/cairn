---
date: 2026-05-02
topic: INV-001 binding implementation (slice 1 of 2)
slice: v1-defense-d2/inv-001-binding-implementation
adrs:
  - invariant-binding-strategy (D1, D2, D3, D8)
  - pipeline-substrate-naming (D1–D5)
status: design — approved 2026-05-02
---

# INV-001 Binding Implementation — Slice 1 Design

## Scope

Bind INV-001 (`bootstrap-exception`) to a true machine-checkable assertion via the `git-log-walk` validator type, replacing the current `file-exists` deletion-detection proxy. Co-creates `.claude/pipeline-substrate-registry.yaml` (defined by `pipeline-substrate-naming` D2/D3) as the walker's classification input.

Sibling slice 2 (`v1-defense-d2/inv-002-binding-implementation`) covers INV-002 + INV-008 separately. Splitting rationale: validator types `git-log-walk` and `structural-parser` are mechanically independent (separate dispatcher branches, disjoint inputs, no shared code), so doing them in one slice conflates two unrelated failure modes in Phase 2/3/4 envelopes without throughput gain.

## Architecture

Add **`git-log-walk`** as a new validator assertion type — one dispatcher branch in `scripts/validate_architecture.py`, mirroring the INV-003 `phase-topology` precedent at `validate_architecture.py:368-454`. It walks `git log <effective-from>..HEAD` (separate `--no-merges` and `--merges` passes), classifies each commit subject against the registry, runs a per-prefix Python verifier on match, and emits SHA + subject citations on miss.

Per-prefix structural verification rules live in **Python** (Approach A from brainstorming Q2), not in YAML. The registry stays a thin authorization-by-name pairing per `pipeline-substrate-naming` D2; verification logic is a small dispatch table keyed by prefix in `validate_architecture.py`. Rejected: embedding rules in YAML (mini-DSL design overhead with no second instance to validate against — same anti-pattern the binding ADR itself rejected for assertion types in Approach B).

## Components (Phase-3 envelope target)

### New: `.claude/pipeline-substrate-registry.yaml`

Initial entries verbatim per `pipeline-substrate-naming` D3 — 9 prefixes (slice, handoff, sweep, bootstrap, feat, docs, fix, chore, test) with `prefix`, `tool`, `owner-adr`, `since`, optional `notes`.

### Modified: `scripts/validate_architecture.py`

Three additions:

- `_load_substrate_registry(project_root) -> dict[str, dict]` — YAML load, schema-check (`prefix`, `tool`, `owner-adr`, `since` required per entry).
- `_verify_<prefix>_commit(sha, files_changed, parents) -> str | None` — one helper per non-trivial prefix:
  - `sweep:` MUST touch `.claude/sweep-results/<slug>` AND `.claude/sweep.yaml`.
  - `fix:` MUST touch only files referenced by a recent sweep (heuristic: any file under `.claude/sweep-results/` OR named in the most recent sweep's report).
  - `docs:` (when emitted by `/refresh-architecture` rather than ADR-landing) — pass-through; ADR-landed `docs:` inside a slice inherits slice-class authorization.
  - `slice:`, `handoff:`, `test:`, `feat:` (squash), `bootstrap:`, `chore:` — pass-through (per `pipeline-substrate-naming` D5: structurally infeasible to verify deterministically; F2 residual).
- `_run_git_log_walk_assertion(project_root, inv_id, assertion) -> str | None` — registered in `_run_assertion` dispatcher (`validate_architecture.py:457-468`).

### Modified: `docs/ARCHITECTURE.md`

INV-001 assertion block changes from:
```
type: file-exists
target: "commands/claude-code/start-slice.md"
```
to:
```
type: git-log-walk
binding-effective-from: <pending-slice-close-sha>
registry: .claude/pipeline-substrate-registry.yaml
description: "True INV-001 binding via authorization-by-name walk over commits since binding-effective-from. Replaces prior file-exists proxy."
```

### Modified: `docs/lessons.md`

Close L-001:17 — registry now names sweep et al. as substrate; debt resolved.

## D3 grandfathering mechanism

Walker treats the literal string `<pending-slice-close-sha>` as a **no-op-with-notice** (binding registered but not yet active; emits an INFO-level message, returns no failures). After the slice closes, a single follow-up `docs:` commit substitutes the actual close SHA. The follow-up commit is either operator-typed during this slice's tail or emitted by `/refresh-architecture` on its post-close run. **No `close_slice` modification** — keeps the orchestrator out of envelope. Self-application paradox (F5 in binding ADR) is resolved-by-design.

## Data flow

1. Operator runs `uv run python scripts/validate_architecture.py` (or integration-gate Step 3, or `/refresh-architecture`).
2. `_run_assertion` sees `type: git-log-walk`, dispatches to `_run_git_log_walk_assertion`.
3. Handler reads `binding-effective-from`. If placeholder → emit notice, return no failures.
4. Else `git log <SHA>..HEAD --no-merges --format=%H%x09%s` and a separate `--merges` pass for squash-merge classification (per `pipeline-substrate-naming` D5).
5. For each commit: extract prefix, look up in registry. Miss → INV-001 violation. Hit → run prefix's verifier (file-shape or pass-through). Verifier failure → INV-001 violation with SHA cite.
6. Aggregate failures, return list.

## Error handling

- Missing registry file: hard fail with `INV-001: registry not found at .claude/pipeline-substrate-registry.yaml`.
- Malformed registry (YAML parse error or missing required fields): hard fail with parse-error cite.
- Unregistered prefix: emit `INV-001 FAIL: <SHA> '<subject>' — prefix '<P>' not in registry` (one line per offender, all collected — no early-exit).
- Verifier failure (e.g. `sweep:` doesn't touch `.claude/sweep-results/`): emit `INV-001 FAIL: <SHA> '<subject>' — sweep verifier: missing .claude/sweep-results/ touch`.
- Empty commit range (`<SHA>..HEAD` is empty): clean pass.

## Testing (Phase-2 RED set)

1. Registry file present and YAML-parses with required fields per entry.
2. Every prefix in registry has a Python verifier in dispatch table (or explicit `pass-through` marker).
3. `_run_git_log_walk_assertion` returns no-op notice when `binding-effective-from: <pending-slice-close-sha>`.
4. Synthetic git fixture (`tmp_path` repo) with one valid `sweep: x` and one operator-typed `chore: x` (chore not from registered emitter context) → walker reports chore commit only.
5. Synthetic `sweep:` commit that doesn't modify `.claude/sweep-results/` → walker reports verifier failure with SHA cite.
6. Synthetic unregistered prefix `wibble: foo` → walker reports prefix-miss with SHA cite.
7. Squash-merge `feat:` accepted on prefix alone (verifier is pass-through; F2 residual documented).
8. End-to-end: `uv run python scripts/validate_architecture.py` exits 0 with binding registered + placeholder still set.

## Phase-4 invariant evidence

PASS verdict citations target:

- `scripts/validate_architecture.py:<line>` — `_run_git_log_walk_assertion` registered in dispatcher.
- `scripts/validate_architecture.py:<line>` — verifier dispatch table.
- `.claude/pipeline-substrate-registry.yaml:1` — registry exists with all 9 D3 entries.
- `tests/unit/test_inv_001_git_log_walk.py::<8 test names>` — fixture-driven walker behavior.

## Out of scope (slice 2 territory)

- INV-002 structural-parser (D1 second type, D4 handoff schema, D7 token-counting precision).
- /catchup Tier-1 five-item-list test (D5).
- INV-002(c) / INV-008 grep→test-ref upgrade (D6).

## Risks

| ID | Scenario | Mitigation |
|---|---|---|
| L1 | Walker false-positive on a legitimate but unregistered prefix introduced by a future tool. | F1 of binding ADR — registry is ADR-amendment-gated; visible in ARCHITECTURE.md refresh. |
| L2 | Operator-typed `sweep:` commit that happens to touch `.claude/sweep-results/` passes verifier. | F2 residual; accepted. |
| L3 | Walker latency on growing git log (effective-from accumulates commits). | D8 — validator does NOT run on every `/status`; capped by `binding-effective-from` window. |
| L4 | Forgetting to substitute `<pending-slice-close-sha>` post-close leaves binding indefinitely advisory. | Phase-4 sweep-notes explicit handoff item; `/refresh-architecture` post-close run is the natural substitution point. |

## Open questions for writing-plans phase

- File-shape diff source for verifiers: `git show --name-only <SHA>` vs. parsing `git log --name-only`. Probably the former for clarity per-commit.
- Verifier helper module placement: alongside walker in `validate_architecture.py` (single file) vs. new `scripts/validate_architecture/substrate_verifiers.py`. Default to single file unless line-count exceeds existing module conventions.

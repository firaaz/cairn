---
id: carrier-hierarchy-and-process-diet
name: "Carrier hierarchy and process diet — constraints out of prose, ceremony down to receipts"
status: accepted
firmness: firm
contract:
  must-satisfy:
    - "D5: every non-superseded ADR carries a contract block naming its carrier OR carrier rationale-only (carrier: scripts/validate_architecture.py adr-carrier rule)"
    - "D8: every surviving hook has a liveness assertion proving it blocks a known-bad input (carrier: scripts/smoketest_hooks.sh via tests/unit/test_hook_smoketest.py)"
    - "D6: the handoff carries only load-bearing threads, no open-issue mirror (carrier: tests/unit/test_handoff_contract.py)"
    - "D4: role_guard denies with exit 2 and matches normalized repo-root-relative paths (carrier: tests/unit/test_role_guard_envelope.py + scripts/smoketest_hooks.sh)"
  must-not-violate:
    - premise_guard.py or either fresh-context checkpoint agent retired without a superseding ADR citing measured receipts
    - a new standing mechanism added without a named mechanical carrier and a liveness/contract test
  wrong-if:
    - a constraint an agent must heed exists only in ADR prose with no level 1-4 carrier
    - an enforcer ships without a test that proves it blocks
  evidence:
    - uv run pytest passes; uv run python scripts/validate_architecture.py passes
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: []
date: 2026-06-10
---

# Carrier hierarchy and process diet

## Status
Accepted, firm. Amends `intent-management-loop` (resolves its D7/R2 retire-with-conditions: `cairn-tdd-feature` goes legacy), the thin-substrate trials plan (no standing trial machinery; no Trial F), and `using-cairn`'s four-phase references.

## Date
2026-06-10

## Context

Six weeks of operation inverted the tool/work ratio: 48 ADRs, 63 plans, a ~50-thread handoff, and trial/firmness apparatus (~38k doc lines) wrap ~7k LOC of machinery; 32% of commits were handoff churn. Meanwhile the central mechanical enforcer, `role_guard.py`, failed open for weeks unnoticed (gh#35) — and the failure was double: its deny path exited 1 (Claude Code blocks only on exit 2), which masked a second defect — envelope regexes are repo-root-relative but the hook matched raw absolute tool paths, so every operator-session write was silently denied-then-allowed. The document apparatus grew while the enforcement layer was dead.

The diagnosis: cairn's own practice already shows that every constraint that actually binds has escaped prose into a mechanical carrier (identifier-scheme → contract test; carrier-contract → hook; invariant-binding → validator; intent-loop → skill). ADR prose is the right carrier for rationale and provenance, the wrong carrier for the thing an agent must heed.

## Decision

### D1 — The carrier hierarchy

A decision is carried by the strongest carrier that can hold it:

1. **Never-violate rules → hooks** (`checks/`). Fire without being loaded; fail closed; carry a liveness test (D8).
2. **Corpus/structural invariants → contract tests + validator assertions** (the `test_handoff_contract.py` pattern). Red on drift.
3. **Workflow decisions → skills/commands.** The decision *is* the default path.
4. **Must-know-before-acting guidance → CLAUDE.md line** (size-capped, pointer to the ADR).
5. **Rationale/history → ADR**, with a `contract:` block naming its level 1–4 carrier (D5).

### D2 — The receipts principle

A mechanism earns its place by a logged catch, not by completing its ceremony. Retention and retirement decisions cite the receipt inventory; "the process ran" is not evidence.

### D3 — Retirements

- **`/decision` 8-phase protocol** → legacy (docs kept for provenance). Replaced by the lean form: write the ADR, subject it to one fresh-context adversarial attack (intent-challenge form), record the attack report alongside.
- **Trials/firmness standing apparatus** → no standing machinery; trial plans stay as history. Trials remain available ad hoc when a question needs data, but carry no scheduled obligations.
- **`docs/dogfood-log.md`** → deleted (schema-only, zero entries in six weeks).
- **`cairn-tdd-feature` four-phase pipeline** → legacy (resolves `intent-management-loop` D7/R2). `cairn-intent` is the one operating loop.
- **Handoff-as-content** → handoff carries ≤6 load-bearing threads (D6); everything else lives solely as gh issues.

### D4 — Retentions, with receipts

- **Fresh-context checkpoints** (`intent-challenge`, `intent-review`): the strongest receipt holder (~3 live catches incl. a semantic ADR over-read no mechanical gate could see, `docs/operator-field-notes-2026-06-01.md`). This ADR's own challenge added four more: a session-bricking dangling-hook path, the premise_guard receipts transfer error, an unsatisfiable handoff clause, and the masked path-shape defect in role_guard.
- **`checks/premise_guard.py`**: RETAINED, reversing this plan's first draft. It has its own logged reds (field notes 2026-06-02), and every "challenge agent has receipts" datum was measured with premise_guard running as precondition; the stale/fabricated-quote class belongs to it. The challenge agent owns the semantic layer above it.
- **`checks/role_guard.py` + `.claude/active-envelope.yaml`**: REPAIRED, not deleted (operator call; deletion was the first draft). The repair is two paired fixes in one commit: deny exits 2, and `tool_input.file_path` is normalized against the repo root before matching (`.slice-system/` deliberately NOT stripped — preserves the edit-canonical-paths-only rule). Resolves gh#35, both halves. This makes envelope enforcement real for the first time: **consumers must audit `active-envelope.yaml` before pulling past this change — stale envelope paths become live denials.**
- **`reversibility-guard.sh`, `reality-check.sh`, `using-cairn` carrier, contract tests, validator**: retained; each gains/keeps a liveness or contract test.
- The cairn-intent **close-review additionally diffs changed paths against the intent contract's `execution-scope`** — a second, review-time envelope check that cannot die silently.

### D5 — ADR carrier declaration

Every non-superseded ADR declares its carrier tier in frontmatter: a `contract:` block whose clauses name their level 1–4 carrier (live constraint), or `carrier: rationale-only` (history/rationale, no standing rule). A new validator rule fails any non-superseded ADR with neither. Superseded ADRs are untouched (append-only stands). This generalizes the 6 existing `contract:` blocks.

### D6 — Handoff diet

`.claude/handoff.md` carries at most 6 active threads — load-bearing pointers only. Open gh issues live solely in gh; `test_handoff_contract.py`'s open-issue-coverage assertion is removed (it forced the handoff to mirror the tracker — the duplication this ADR exists to end). The per-line pointer/state/no-prose assertions stand.

### D7 — Lean decision form

Decision-weight changes take: ADR + one fresh-context adversarial attack on its premises before commit + operator sign-off. This ADR is the first instance; its own attack ran five revision rounds and produced four real catches (D4), which is the receipt for the form.

### D8 — Enforcer liveness

An enforcer without a test proving it BLOCKS a known-bad input is documentation. `scripts/smoketest_hooks.sh` asserts, per surviving hook, that a known-bad input is denied (exit code / decision JSON) and — for role_guard — that a known-good absolute in-envelope path is allowed; pytest runs it.

## Consequences

- The backlog is re-anchored: issues serving retired machinery close citing this ADR; `docs/roadmap.md` is rewritten to the minimal set.
- Top roadmap item: **measure the production gate** — de-prime the shipped intent-challenge (its brief hard-codes the slice-#25 example) and gather live, non-planted catch data; every existing "front gate works" datum used de-primed stand-ins.
- Falsification tripwires: a correlated miss by both fresh-context checkpoints reopens the cross-family decision (`intent-management-loop` D4); a constraint that drifts because its only carrier was prose reds D5's `wrong-if`; if the lean form (D7) lets a bad decision through that an 8-phase arc would demonstrably have caught, D7 is revisited with that receipt.

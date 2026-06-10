---
id: invariant-binding-strategy
status: accepted
contract:
  must-satisfy:
    - "every firm invariant carries a machine-checkable assertion (carrier: scripts/validate_architecture.py Check D/E runners)"
  evidence:
    - "uv run python scripts/validate_architecture.py"
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-001, INV-002]
date: 2026-05-02
---

# invariant-binding-strategy: Bind INV-001 and INV-002 to True Machine-Checkable Assertions

## Status
Accepted (pending Phase 5 independent verification per `/decision`)

## Date
2026-05-02

## Context

`docs/ARCHITECTURE.md:138` records the open commitment: *"INV-001, INV-002, and INV-003 currently have no machine-checkable form; their migration path is an explicit deliverable of D2's design slice."* The current assertion blocks for INV-001 and INV-002 are deletion-detection proxies (file-exists on `commands/claude-code/start-slice.md`; grep on the literal token-budget string). They catch accidental deletion of substrate, not actual violation of the invariant.

This is the single un-time-boxed v1 commitment that has not been satisfied. Per `cliff-failure-mode-and-v1-defenses` D2, *"Invariants that cannot be machine-checked at introduction time are marked `firmness: advisory` and do not count toward v1 defense satisfaction."* INV-001 and INV-002 are firm; their proxies do not satisfy D2; v1 stalls here.

INV-003 is in the same situation but is structurally simpler (a four-way cross-reference among orchestrator constant, phase prompts, Skill Guide table, and `role_guard.py` policies). INV-003's binding is **explicitly out of scope** for this ADR and is routed to a separate, independent slice.

The sibling ADR `pipeline-substrate-naming` (co-landing with this one) closes a load-bearing precondition: INV-001's binding cannot self-violate without a named pipeline-substrate commit class.

## Decision

### D1 — Two new validator assertion types

`scripts/validate_architecture.py:237-246`'s `_run_assertion` dispatcher gains two assertion types, joining the existing `grep`, `file-exists`, and `test-ref`:

- **`git-log-walk`**: walks `git log <binding-effective-from>..HEAD` and classifies each commit subject against a registry of legitimate prefixes plus per-prefix structural-verification rules. Designed for INV-001.
- **`structural-parser`**: parses a target file (Markdown initially) and verifies declared structural properties — required headers present, forbidden patterns absent, optional headers well-formed if present, byte/token bounds. Designed for INV-002 sub-clause (a).

Reserved-types comment at `scripts/validate_architecture.py:408-414` updated to reflect these as **implemented**, not reserved. The existing `ast` and `custom` reservations remain v2-deferred.

### D2 — Pipeline-substrate registry as INV-001 binding input

INV-001's `git-log-walk` assertion takes its legitimate-prefix list from `.claude/pipeline-substrate-registry.yaml` (defined by sibling ADR `pipeline-substrate-naming`). The walker:

1. Reads `binding-effective-from: <SHA>` from the assertion block.
2. Walks `git log <SHA>..HEAD --no-merges --format=%H%x09%s` (and a separate `--merges` pass for squash-merge classification per `pipeline-substrate-naming` D5).
3. For each commit, matches subject against registry prefixes; on match, runs the prefix's structural-verification rule (e.g., `sweep:` MUST touch `.claude/sweep-results/` and `.claude/sweep.yaml`).
4. Unmatched subjects → INV-001 violation, citing commit SHA and subject.

### D3 — INV-001 binding-effective-from is the slice-close SHA, not bootstrap

The INV-001 assertion block carries `binding-effective-from: <SHA>` where `<SHA>` is set at the close of the slice that lands this binding (recorded by the slice's `close_slice` writing the SHA back into ARCHITECTURE.md, or a follow-up commit). Pre-effective history is grandfathered.

**Rationale**: a retroactive walk from `25ff49f` would require classifying every historical commit, including pre-registry commits emitted before the substrate naming was firm. That is a separate forensic-audit slice if ever desired. The binding's purpose is forward-going enforcement.

### D4 — INV-002(a) handoff structure via structural-parser

The INV-002 assertion for sub-clause (a) is a `structural-parser` assertion against `.claude/handoff.md` with the schema:

```yaml
required-sections: ["State", "Next", "Blocked / Pending", "Pointers"]
optional-sections: ["Features"]
forbidden-section-patterns:
  - "What This Session Was About"
  - "What Was Accomplished"
  - "Surprises or Discoveries"
  - "Self-Check"
  - regex: '^##\s+(Lessons|Reflection|Notes)\b'  # broad coverage of forbidden classes
forbidden-content-patterns:
  - regex: 'I (was|am|will|just) '   # first-person reflective
  - regex: '\d+\s*/\s*\d+\s+(passed|failed|tests)'  # test tallies
token-budget:
  measure: byte-approximation
  bytes-per-token: 4
  warn-at: 360
  fail-at: 440
```

Schema source: `templates/handoff.md:1-24` (required sections), `commands/claude-code/handoff.full.md:42-50` (forbidden), `docs/ARCHITECTURE.md:21` (token bound 150–400).

### D5 — INV-002(b) /catchup five-item Tier-1 list via test-ref

Sub-clause (b)'s machine-check is a `test-ref` to a new test `tests/unit/test_catchup_tier1_list_pinned.py::test_tier1_five_items_verbatim` that pins the literal five-item list verbatim against `commands/claude-code/catchup.full.md`:

```
.claude/handoff.md
.claude/current-slice/slice.yaml
.claude/sweep.yaml
git log --oneline -5
git status --short
```

Tier-2 admission criteria (also in (b)) are NOT bound at v1 — they describe runtime LLM judgment, not file state. The same test pins the three admission criteria are still documented (structural assertion only). This residual is recorded under `cliff-failure-mode-and-v1-defenses/D2` as advisory until v2.

### D6 — INV-002(c) wipe via test-ref to existing close_slice test

Sub-clause (c)'s machine-check is a `test-ref` to the existing `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop`. This is INV-008's territory; INV-008 currently uses a grep proxy on `def close_slice` (`docs/ARCHITECTURE.md:77-83`). The slice landing this binding **also** upgrades INV-008's grep proxy to the same `test-ref`, eliminating the proxy duplication.

### D7 — Token-counting precision: byte-approximation with named buffer

`structural-parser`'s token measurement uses byte-approximation (4 bytes/token) per the precedent in `tests/unit/test_context_budget.py`. The buffer (warn-at: 360, fail-at: 440) absorbs ~10% drift from true tokenizer output. Tiktoken/Anthropic-API integration is rejected: validator stays self-contained and offline-runnable.

### D8 — When the binding runs

The validator runs in three contexts:
- **Operator-invoked** (`uv run python scripts/validate_architecture.py`) — primary path.
- **Integration-gate Step 3** (`scripts/integration_gate.py`) — already mechanized; new bindings inherit.
- **`/refresh-architecture`** (already gated on validator passing) — picks up new bindings automatically.

The validator does **NOT** run on every `/status` (latency on growing git log is the failure mode). It does **NOT** run as a pre-commit hook (would block the substrate tools whose output it validates).

## Consequences

### Easier
- INV-001 and INV-002 graduate from advisory to true machine-checkable. v1-defense-D2 satisfaction proceeds for these two invariants.
- The two new types (`git-log-walk`, `structural-parser`) are reusable for future invariants (e.g., any future "all commits in window X classify under registry Y" or "file Z conforms to schema W" assertion).
- The `test-ref` pattern (D5/D6) demonstrates a clean delegation path: invariants whose violation is already covered by a test cite the test rather than re-implementing the check. Reduces validator code growth (F6 mitigation).
- INV-008's grep proxy is also upgraded as a side effect (D6), reducing proxy debt across invariants.

### Harder
- Adding new substrate tools requires ADR amendment per `pipeline-substrate-naming` D4. Casual `chore:` commits from new scripts will fail until registered.
- `structural-parser` schema lives in this ADR. Schema changes (e.g., adding a new required section to handoff.md) require an ADR row update. This is intentional — handoff.md schema IS the invariant.
- The validator becomes mildly slower as the git-log-walker accumulates commits. Mitigated by `binding-effective-from` cap and by NOT running on every `/status`.
- Two new validator assertion types are now part of the supported surface; their behavior changes are ADR-gated.

## Alternatives Considered

### Approach A — Per-invariant custom code, no shared types
Each invariant gets bespoke code in `validate_architecture.py`. Rejected: F6 (per-invariant code sprawl) — by the time 5-10 invariants are bound, the validator is 3000 LoC of one-offs with no shared abstraction. The two new types in this ADR are lightweight by comparison and earn back their cost on the second invariant that uses each.

### Approach B — Generic policy framework with `type: policy`
Introduce a single `policy:` assertion type that takes a YAML rule file. Most ambitious. Rejected for v1: requires designing a policy DSL upfront with no second instance to validate the design against. Two concrete types (this ADR's choice) cover the needed surface and can be generalized later if a third invariant pattern emerges.

### Approach D — Stage: bind INV-002 first, INV-001 second
Land INV-002 first (no ADR amendment needed; schema is `templates/handoff.md`), then a second slice for INV-001 after `pipeline-substrate-naming` lands. Rejected (with one piece adopted): the bundling concern is real, and is addressed by **co-landing** `pipeline-substrate-naming` and `invariant-binding-strategy` as sibling ADRs in the same slice rather than serializing two slices. This captures D's clean-ADR-hygiene argument without the throughput cost.

## Risk Register

| ID | Scenario | Probability | Mitigation |
|---|---|---|---|
| F1 | Pipeline-substrate registry rot — new tool emits unregistered prefix; binding loud-fails on legitimate output | medium | `pipeline-substrate-naming` D4 requires ADR amendment for additions; visible in ARCHITECTURE.md refresh; documented residual. |
| F2 | Squash-merge classifier ambiguity — `feat:` from squash-merge accepted on prefix alone; operator-typed `feat:` bypasses | low | `pipeline-substrate-naming` D5 names this residual; a stronger structural verification of squash commits (single parent ≠ HEAD~1) is a v2 improvement. |
| F3 | Handoff parser brittleness — false-positive on `### Sub-section` or code-fenced `## …` | low-medium | Schema explicitly limits to top-level `## ` headers; parser ignores fenced blocks. Validator output cites the violating line so false-positives surface fast and registry edit is one-shot. |
| F4 | Token-count approximation drift — bytes/4 undercounts link-heavy content | low-medium | D7 buffer (warn-at: 360, fail-at: 440) absorbs ~10% drift. If observed drift exceeds buffer, follow-up slice tightens approximation or migrates to true tokenizer. |
| F5 | Self-application paradox — binding validates its own introducing commits | resolved-by-design | D3 sets `binding-effective-from` to slice-close SHA; pre-effective history grandfathered. |
| F6 | Per-invariant code sprawl across many future invariants | low | Two reusable types delivered (D1); `test-ref` delegation pattern (D5/D6) demonstrates the path for invariants already covered by tests. |

---
id: bootstrap-exception
status: accepted
contract:
  must-satisfy:
    - "the self-symlink bootstrap carve-out holds (carrier: scripts/validate_architecture.py INV-011 assertion)"
  evidence:
    - "uv run python scripts/validate_architecture.py"
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-001]
date: 2026-04-11
---

# bootstrap-exception: Bootstrap Exception

## Status
Accepted

## Date
2026-04-11

## Context

Cairn's v1 commitment #4 (`docs/vision.md`) is that cairn is meta-dogfoodable from slice #1 — every unit of cairn development flows through the slice pipeline (`/start-slice`) or the decision protocol (`/decision`), with no bootstrapping exception.

The commitment collides with physical reality: before the scaffolding exists, the pipeline cannot run on itself. `/start-slice` requires `.claude/sweep.yaml`, an ADR corpus, and `docs/ARCHITECTURE.md`. `/decision` Phase 0 reads `docs/ARCHITECTURE.md`, `docs/adr/index.md`, and `docs/lessons.md` before anything else. None of these files exist in cairn v0.1.0. Any "first slice" that attempts to create them is blocked by its own outputs.

There are three ways to resolve this:

1. Run the bootstrap directly as a one-shot commit, document the exception.
2. Invent a degenerate SLICE-000 that somehow runs through the pipeline without requiring its own prerequisites.
3. Leave the exception undocumented and let it become folklore.

Option 2 is sophistry — the pipeline cannot evaluate a slice whose declared input artifacts do not exist. Option 3 violates the commitment's spirit while claiming to honor its letter.

## Decision

The initial scaffolding is created as a one-shot direct commit. This commit is the singular permitted exception to the pipeline-first rule for cairn's own development. The exception is recorded in this ADR — in the canonical decision-record substrate the system considers authoritative — not buried in git history or hidden in a README paragraph.

After this commit lands, all cairn development flows through `/decision` or `/start-slice`. There is no second exception. If a future situation appears to demand another direct commit, the correct response is to write an ADR that supersedes this one, not to quietly repeat the pattern.

## Consequences

- **INV-001 becomes enforceable from slice #1 onward.** The invariant that all post-bootstrap work goes through the pipeline is now machine-checkable in spirit (via `/status`, code review, and the commit-history audit), though not yet by any automated hook.
- **The substrate validator's Check B is satisfied on commit #1.** This ADR is `firmness: firm` and is paired with INV-001 in `docs/ARCHITECTURE.md`, so `scripts/validate_architecture.py` reports `ALL CHECKS PASSED` from the bootstrap forward. A green validator from day one is a feature — it means `/status` has a truthful signal to report.
- **v1 commitment #4 is honored with an explicit footnote rather than a silent workaround.** Readers of cairn's ADR corpus encounter the bootstrap exception first, before any architectural decision. The exception is visible, attributed, and bounded.
- **Every future "can't we just…" shortcut has a precedent to point at.** The answer is: no, because bootstrap-exception is the only exception, and it was written because the pipeline physically could not run. Your shortcut is not that case.

## Alternatives Considered

**Treat the bootstrap as SLICE-000 with a documented pipeline exception.** Rejected because it pretends the pipeline ran when it did not, muddying the audit trail. A slice that skipped Phase 1 (Intent, which requires reading ARCHITECTURE.md) and Phase 2 (Validation, which requires tests) is not a slice — it is a direct commit wearing slice notation.

**Leave `docs/adr/` empty and accept a red validator until slice #1.** Rejected because `/status` is the primary operator-facing signal for system health, and starting in a known-red state desensitizes readers to validator output. A validator that is sometimes broken for "good reasons" is indistinguishable from one that is broken for bad reasons.

**Ship the bootstrap under bootstrap-exception `firmness: provisional`.** Rejected because the bootstrap decision is not provisional — there is no realistic future state where this ADR is revisited or replaced. Provisional firmness should mean "we may revisit this as we learn more." The bootstrap exception is a fact, not a hypothesis.

## Risk Register

- **Risk:** This ADR becomes a pattern for other "just this once" exceptions. **Mitigation:** the ADR's own text forbids additional exceptions; future attempts must go through supersession.
- **Risk:** The self-symlink (`.slice-system → .`) introduces path-canonicalization ambiguity in `scope-guard.sh`. **Mitigation:** documented in `CLAUDE.md` — always edit canonical paths (`checks/*.sh`, `commands/claude-code/*.md`), never via `.slice-system/` prefix. A scope-guard fix is a candidate for a future slice, not for this ADR.

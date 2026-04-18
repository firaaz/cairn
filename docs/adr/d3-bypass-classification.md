---
id: d3-bypass-classification
name: "D3 bypass classification — three-class reason schema + envelope exemptions"
status: accepted
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: scope
invariants-touched: []
date: 2026-04-16
---

# D3 bypass classification — three-class reason schema + envelope exemptions

## Status
Accepted.

## Date
2026-04-16

## Context

[cliff-failure-mode-and-v1-defenses D3](003-cliff-failure-mode-and-v1-defenses.md) established an automated unknown-unknown backstop with a bypass escape hatch (`D3_GATE_BYPASS=1`). The bypass mechanism was elaborated in `commands/claude-code/start-slice.full.md:224` using a rolling-window rule inherited from D1: three bypasses in the last ten slices triggers a warning that "the gates are producing more noise than signal" and a design review is recommended.

The threshold fired on 2026-04-16 at the close of `housekeeping/inv004-rebaseline`. Integration sweep #11 (`.claude/sweep-results/2026-04-16-sweep.md`) surfaced the three bypasses:

- **`v1-defense-d3/automated-backstop` (2026-04-14)** — three pre-existing ruff lint errors outside the slice envelope.
- **`v1-defense-d3/ruff-cleanup` (2026-04-15)** — a fleet-coordinator design document committed outside any slice envelope during a parallel session.
- **`housekeeping/inv004-rebaseline` (2026-04-16)** — INV-004 turn-1 token budget regression caused by Claude Code binary drift (2.1.107 → 2.1.110) between slice intent and Phase 4.

None of the three bypasses were D3 false positives. D3 correctly flagged real drift in every case. What the three share is that **none of the drift originated inside the bypassing slice's envelope** — each was either pre-existing debt, parallel-session artifact, or external-tool regression discovered after intent was written.

The rolling-window rule collapses three structurally distinct failure classes into a single counter:

- **class-A (slice-caused)** — the bypassing slice's own commits produced the drift D3 caught. Real signal about the slice's work.
- **class-B (pre-existing)** — drift predates the slice's start commit. Real signal about project debt, not about the slice.
- **class-C (false-positive)** — D3 fired on something that isn't actually drift. Real signal about D3's own quality.

Only class-C is what the warning text targets ("more noise than signal"). By conflating all three, the counter triggers design reviews of D3 when the problem is actually class-B debt accumulation.

## Decision

This ADR refines D3's bypass substrate in two coupled moves.

### Decision 1 — Three-class bypass log schema

Amend the `.claude/d3-bypasses.log` entry format from:

```
<slice-id> <YYYY-MM-DD> <one-line-reason>
```

to:

```
<slice-id> <YYYY-MM-DD> <class>: <one-line-reason>
```

Where `<class>` is exactly one of:

- `slice-caused` — the check-firing path is inside this slice's envelope OR appears in this slice's own commits. Git-verifiable.
- `pre-existing` — the check-firing path predates this slice's start commit. Git-verifiable.
- `false-positive` — D3 fired on a change that should not have tripped it (no semantic drift, or drift was legitimate and covered by a named mechanism). Requires operator judgment.

**Rolling-window rule change.** The `3-in-10 → design-review-recommended` threshold counts only `false-positive` entries. `slice-caused` and `pre-existing` entries are logged but not counted against D3's noise budget. This aligns the counter with the dogfood criterion in cliff-failure-mode-and-v1-defenses:136 ("no D1/D2/D3 false-positive rate is high enough that a check is muted").

**Pre-existing carry-over surfacing.** `pre-existing` entries appear in each integration sweep's "Handoff Staleness Check" section as named debt items. They do not trigger D3 review, but they do force visibility of what the project has deferred.

**Historical reclassification.** The three existing log lines are reclassified in a one-time substrate edit as part of this ADR's adoption:
- `v1-defense-d3/automated-backstop` → `pre-existing`
- `v1-defense-d3/ruff-cleanup` → `pre-existing`
- `housekeeping/inv004-rebaseline` → `pre-existing`

After reclassification, the rolling `false-positive` count is zero.

### Decision 2 — Envelope exemptions at intent time

Extend the intent.md envelope syntax to accept an `exempt:` sibling list alongside the include globs:

```yaml
envelope:
  - checks/*.sh
  - tests/unit/test_*.py
exempt:
  - docs/plans/measurements/2026-04-12-slice-003.txt  # known CC-version drift, not this slice's scope
```

`scripts/snapshot_diff.py` is extended to match paths against the exempt list before flagging them as out-of-envelope. Exempt paths carry an inline comment naming the reason — version-controlled context, unlike orphan log entries.

Intent-time exemption is the preferred path for *anticipated* drift. The bypass-log classification handles *unanticipated* drift discovered at Phase 4 (e.g., CC-binary-drift between intent and Phase 4 close).

### Scope of this ADR

- **This ADR does not supersede cliff-failure-mode-and-v1-defenses D3.** The defense itself, its falsification commitment (cliff-failure-mode-and-v1-defenses:108), and the dogfood criterion remain intact.
- **This ADR does not modify D1's bypass log.** D1's domain (validator false-positives) is naturally single-class; no classification is needed. The D1/D3 log format asymmetry reflects real semantic difference.
- **False-negative invisibility** — bypass logs cannot measure D3 coverage. This limitation is not addressable by classification alone and remains a concern for cliff-failure-mode-and-v1-defenses:108's falsification-test commitment to resolve.

## Consequences

**Made easier:**
- Future integration sweeps can distinguish "D3 is noisy" from "carry-over debt is accumulating." The design-review trigger now targets its named concern.
- Intent.md authors can declare anticipated debt upfront rather than discovering it at Phase 4. The Reader role gains a small discipline mechanism.
- `pre-existing` entries surface debt visibly in every sweep without consuming the D3 review budget. Debt becomes a tracked backlog, not a threshold ceiling.

**Made harder:**
- Bypass-log entries now require a classification step. Operator judgment is required for `false-positive`; the other two classes are git-verifiable.
- D1 and D3 bypass log formats diverge. One more asymmetry to remember.
- Intent.md envelope gains a second YAML key (`exempt:`). `scripts/snapshot_diff.py:_parse_envelope` must parse both keys.

**Downstream effects:**
- `commands/claude-code/start-slice.full.md:224` needs rewrite to describe the new format.
- `scripts/snapshot_diff.py:_parse_envelope` gains an exempt-list branch.
- `commands/claude-code/integration-sweep.md` / `.full.md` gains a note directing the sweep to distinguish `false-positive` count from total bypass count.
- `docs/operational-reference.md` Phase Skill Guide may want a small note on when Reader should use `exempt:` — this is a doc refresh, not a substrate change.

**Invariant impact:**
- No existing invariant is changed. The three-class schema and exempt list are both operational substrate below the invariant layer.
- cliff-failure-mode-and-v1-defenses's dogfood criterion (at cliff-failure-mode-and-v1-defenses:136) becomes more precisely testable once `false-positive` is a distinct signal.

## Alternatives Considered

- **Status quo — keep the 3-in-10 unclassified rule.** Rejected because it fails to address the observed conflation and guarantees this same decision recurs at each threshold fire. The warning's literal text ("more noise than signal") doesn't match the situation in any of the three observed cases.

- **Pre-log known-debt registry (`.claude/d3-known-debt.yaml` with lifecycle semantics).** Rejected because it adds a new substrate file with expiry/ownership rules on top of a provisional defense. The end-of-v0 vision reset makes lifecycle investment unattractive; the envelope-exempt route (Decision 2) gets most of the same benefit with zero new substrate surface.

- **Decision 1 alone (classification only) or Decision 2 alone (exemption only).** Rejected in favor of both combined. Decision 1 alone doesn't exploit intent.md's natural discipline layer; Decision 2 alone doesn't handle post-intent discoveries like the `housekeeping/inv004-rebaseline` Claude Code binary drift. Combined, they cover both pre-intent and post-intent drift with minimal additional surface.

## Risk Register

- **Risk:** Operators misclassify `false-positive` as `pre-existing` to avoid burning the counter. **Mitigation:** two of three classes are git-verifiable (`slice-caused` ↔ slice's own commits; `pre-existing` ↔ predates slice start commit). Only `false-positive` requires operator judgment, and it's the class that warrants review — so misclassification moves a "needs review" into the "surfacing backlog" bucket, not into silence. Integration-sweep already reads the bypass log and can spot-audit classifications against git evidence.

- **Risk:** `pre-existing` queue accumulates without clearing. **Mitigation:** not a new failure mode — it's the *intended* signal. If debt consistently defers, the sweep surfaces it, and the accumulating count itself becomes evidence that a housekeeping slice is overdue. The queue is visible, not hidden.

- **Risk:** Exempt list rot in intent.md — future authors copy-paste exempt blocks without fresh justification. **Mitigation:** exempt entries live inline in version-controlled intent.md; sweep can diff exempt lists across slices. If the same path appears exempt in N consecutive slices, it's a debt candidate, same surfacing mechanism as `pre-existing` bypasses.

- **Risk:** Three classes prove non-exhaustive as cairn encounters new failure modes. **Mitigation:** schema is extendable; this ADR is provisional; the v0 reset is an explicit sunset horizon. Adding a fourth class is an in-scope supersession.

- **Risk:** Bypass logs cannot measure D3 false-negatives — blind spots that never trigger a bypass. **Mitigation:** named explicitly in the scope note; remains the responsibility of cliff-failure-mode-and-v1-defenses:108's falsification-test commitment. This ADR does not claim to solve coverage; it refines the noise signal only.

- **Risk:** End-of-v0 vision reset supersedes this ADR's substrate. **Mitigation:** `firmness: provisional` with zero new substrate files (only format extension on an existing log + parser extension on an existing script). Amendment cost is a format migration, not a substrate tear-down.

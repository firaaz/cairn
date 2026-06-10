---
id: carrier-hierarchy-refocus
name: Cairn refocus — carrier hierarchy and process diet
snapshot-sha: 2d24db106b4e2aef61ed0f8bcae445331d61a967
invariants-touched: []
---

## Operator Prompt
<!-- VERBATIM, derive-exempt. Full approved plan pinned at
.claude/skill-runs/carrier-hierarchy-refocus/plan.md -->
> Implement the following plan:
>
> # Cairn refocus: constraints out of prose, ceremony down to what has receipts
>
> Cairn's problem statement is sound (session-boundary decorrelation, empirically backed). The execution has inverted: 48 ADRs + 63 plans + trials + a 40-thread handoff (~38k doc lines) wrap ~7k LOC of machinery; 32% of 6 weeks of commits are handoff churn; the central mechanical enforcer (`role_guard.py`) failed open for weeks unnoticed while the document apparatus grew. The operator asked: don't patch defects — interrogate whether the mechanisms (ADR-as-carrier, decision arcs, trials, handoff) are the right solution shape at all.

## What

Adopt the carrier hierarchy (hooks → contract tests/validator → skills/commands → CLAUDE.md line → ADR-for-rationale-only) and the receipts principle (a mechanism earns its place by a logged catch). Record both in a new superseding ADR `docs/adr/carrier-hierarchy-and-process-diet.md`. **Operator call at sign-off: `role_guard.py` is REPAIRED, not deleted** — its deny path exits 1 but Claude Code blocks only on exit 2, which is the entire gh#35 fail-open; fix deny→2, correct the unit tests that assert the wrong code, add a liveness assertion. `.claude/active-envelope.yaml` and both hook registrations stay. The close-review envelope-diff step still lands (it checks the intent's execution-scope at close — complementary, not a replacement). Retire receipt-less machinery: the `/decision` 8-phase protocol (legacy), trials/firmness standing apparatus, `dogfood-log.md`. **Challenge revision: `premise_guard.py` is RETAINED** as the mechanical verbatim-grounding layer — it has logged reds (field notes 2026-06-02) and the challenge agent's receipts were all measured with it running as precondition; the plan's "demote/delete" is dropped. Diet the handoff to ≤6 active threads, **amending `test_handoff_contract.py` to drop the open-issue-coverage assertion** (issues live solely in gh — the duplication the refocus removes; the plan's "test unchanged in shape" premise was wrong). Add hook liveness assertions to `scripts/smoketest_hooks.sh`. Add a validator rule: live-constraint ADRs must carry a `contract:` block naming their mechanical carrier; backfill the ~14 live-constraint ADRs. Sweep gh issues serving retired machinery; rewrite `docs/roadmap.md` to the minimal set topped by "measure the production gate (de-prime the intent-challenge)".

## Why

Every live constraint that works has already escaped prose into a mechanical carrier; prose-only ADRs are rationale. Only fresh-context checkpoints and concluding trials have logged catches. The central enforcer failed open unnoticed (gh#35) — empirically not load-bearing — while ~38k doc lines accreted around ~7k LOC. Plan: `.claude/skill-runs/carrier-hierarchy-refocus/plan.md`; supersedes/amends `intent-management-loop.md` (D7/R2), thin-substrate trial machinery, four-phase references.

## Boundary

Does NOT de-prime or measure the intent-challenge itself (becomes the roadmap's top item). Does NOT edit superseded ADRs beyond frontmatter status fields (append-only stands). Does NOT delete trial plans, `/decision` docs, or other history — legacy-marked, kept for provenance. Does NOT change `/catchup`; `test_handoff_contract.py` keeps its pointer/state/prose assertions but loses `test_coverage_open_issues` (challenge finding: that assertion forces ≥20 gh lines and makes the ≤6-thread diet unsatisfiable). Does NOT retire `premise_guard.py` (challenge revision — retained with its tests). Does NOT run an 8-phase `/decision` arc for this decision — the lean form (ADR + one fresh-context attack) is itself the proposal, flagged as an explicit operator call.

## Specification

- New ADR: `docs/adr/carrier-hierarchy-and-process-diet.md` with `id:`/`name:` frontmatter, the 5-level hierarchy, the receipts principle, the retirement list, and its own `contract:` block naming carriers.
- Deletions: `docs/dogfood-log.md`.
- `checks/role_guard.py`: TWO paired fixes in one commit. (1) deny path exits 2 (currently 1 — non-blocking in Claude Code, the gh#35 fail-open); malformed-stdin stays fail-closed (also blocking). (2) `tool_input.file_path` normalized against CAIRN_ROOT before matching (tools report absolute paths; envelope regexes are repo-root-relative anchored — today every absolute-path write is denied-but-masked, so the exit flip alone would block all writes in any `mode: operator` session). `.slice-system/` is deliberately NOT stripped — preserves the CLAUDE.md "edit canonical paths only" rule. Unit tests assert BOTH directions: known-bad path blocked (exit 2) AND known-good ABSOLUTE in-envelope path allowed (exit 0). Stale exit-code docstrings updated: `role_guard.py:13`, `premise_guard.py:8` mirror line (docstring-only carve-out from "retained unchanged"), `docs/operational-reference.md` role_guard exit-code mention. Hook registrations and `.claude/active-envelope.yaml` untouched. gh#35 closes on the fix commit (defect resolved, not retired).
- `checks/premise_guard.py`: retained unchanged, with its tests; the refocus ADR records the retention rationale (logged reds; owns the stale/fabricated-quote class the challenge agent delegates to it).
- `.claude/skills/cairn-intent/SKILL.md`: close-review brief gains an envelope-diff instruction (changed paths vs intent `execution-scope`); premise_guard invocation in Step 3 stays.
- `scripts/smoketest_hooks.sh`: per surviving hook (`reversibility-guard.sh`, `reality-check.sh`, `using-cairn-carrier.sh`, `role_guard.py`), assert a known-bad input is BLOCKED (exit code / decision JSON), plus pytest wrapper.
- `scripts/validate_architecture.py`: new assertion — live-constraint ADR without `contract:` fails; paperwork-audit rules serving retired machinery pruned.
- `.claude/handoff.md`: ≤6 active thread lines; contract frontmatter unchanged. `tests/unit/test_handoff_contract.py`: `test_coverage_open_issues` removed (open issues live solely in gh); other assertions untouched.
- `CLAUDE.md`: `cairn-tdd-feature` marked legacy; operator-envelope section stays (mechanism repaired, now actually enforcing).
- gh issue closures cite the refocus ADR.

## Verification

- `uv run pytest` green after each retirement commit (tests deleted with their mechanism, never skipped).
- `scripts/smoketest_hooks.sh` exits 0 and demonstrably blocks known-bad inputs per hook.
- `uv run python scripts/validate_architecture.py` passes; a contrived live-constraint ADR without `contract:` reds (asserted in a unit test).
- `tests/unit/test_handoff_contract.py` green on the dieted handoff.
- Challenge report + close-review report in `.claude/skill-runs/carrier-hierarchy-refocus/`.

## Risk Surface

Receipt-less ≠ value-less: a prevention mechanism can have shaped behaviour without logging a catch. The close-review envelope-diff detects only after construction, not at write time. Issue-sweep may close a defect mislabelled as retired-machinery. The lean decision form replaces `/decision` using itself as precedent — circularity the fresh-context attack sustained as a risk; resolved at sign-off (operator chose the gh#35 repair over deletion). The repaired role_guard makes envelope enforcement REAL for the first time: concurrent sessions and consumers that silently relied on the fail-open will start seeing denials; a stale `active-envelope.yaml` becomes live friction. The fix propagates to consumers as a file change (registrations unchanged) but is an intended behaviour change — the upgrade note ("audit your envelope before pulling") is a contracted deliverable. The exit-code defect masked a path-shape defect (absolute file_path vs repo-root-relative regexes); the flip must never land without the normalization fix or every `mode: operator` session bricks.

## Feature-Local Invariants

- Each retirement lands as its own commit with the full suite green (bisectable; never a mixed delete+feature commit).
- No mechanism is removed before its replacement exists in the same or an earlier commit; the role_guard exit-code flip never lands without the path-normalization fix in the same commit (liveness tests land before any hook is declared "kept").
- ADR append-only discipline holds throughout (supersession via frontmatter/new ADR only).

## Explicit Scope-Out

- De-priming + live measurement of the intent-challenge (roadmap top item, separate work).
- Any new standing machinery beyond the liveness assertions and validator rule.
- Rewrites of trial plans, field notes, or superseded ADRs.
- Consumer-repo dist propagation beyond the role_guard repair itself — the repair is an INTENDED consumer-facing enforcement change (envelopes start actually enforcing); the refocus ADR / upgrade doc carries a note: audit `active-envelope.yaml` before pulling, stale envelopes become live denials. No other consumer-facing behaviour changes intended.

## Premise Grounding

```yaml
premises:
  - source: checks/role_guard.py
    quote: |
      AGENT_ROLE unset is the no-op path unless .claude/active-envelope.yaml
      is present with mode: operator, in which case it enforces the declared paths.
    label: "operator-session per-write enforcement lives in role_guard.py's envelope path, registered as a PreToolUse hook in .claude/settings.json and the consumer template; the repair touches only the script, registrations stay"
  - source: checks/role_guard.py
    quote: |
      Exit codes: 0 = allow, 1 = deny (with stderr diagnostic), 2 = malformed stdin.
    label: "deny currently exits 1, which Claude Code does not treat as blocking (only exit 2 blocks) — the gh#35 fail-open; the repair flips deny to exit 2 paired in the same commit with file_path normalization against CAIRN_ROOT (raw absolute paths currently match no repo-root-relative envelope regex, so the flip alone would deny everything)"
  - source: checks/premise_guard.py
    quote: |
      Reads an intent's optional `## Premise Grounding` block (verbatim source-quotes)
      and diffs each quote against live source via the shared lib.premise_match.grounded
    label: "premise_guard checks verbatim quote-vs-source grounding only (a grounded quote with a misrepresenting label exits 0 — the slice-#25 shape the challenge agent owns); it is RETAINED as the mechanical verbatim layer because it has logged reds and the agent brief delegates that class to it"
  - source: .claude/agents/intent-challenge.md
    quote: |
      **The slice-#25 obligation.** The failure you exist to catch: a premise whose `quote:` is genuinely grounded (so `premise_guard` exits 0) but whose `label:` or dependent claim misrepresents the source
    label: "the challenge agent's brief already owns the slice-#25 semantic gap premise_guard cannot catch — and hard-codes that example (the priming the roadmap item must remove)"
  - source: docs/dogfood-log.md
    quote: |
      Append entries as fenced YAML blocks. Each entry must contain: slice, date,
      defense, type, description, would-manual-have-caught, disposition.
    label: "dogfood-log.md is schema-only with zero entries"
  - source: .claude/handoff.md
    quote: |
      - every body line names a thread with a resolvable pointer
    label: "handoff contract asserts pointer+state shape AND (test_coverage_open_issues) that every open gh issue appears; the diet removes the coverage assertion so issues live solely in gh and only load-bearing threads stay"
```

## Contract

```yaml
scope-statement: replace ADR-as-constraint-carrier with the carrier hierarchy and retire receipt-less machinery (/decision arc, trials apparatus, dogfood-log, handoff bulk; premise_guard retained, role_guard repaired not deleted), adding hook liveness tests and an ADR contract-block validator rule
must-satisfy:
  - the repo shall contain docs/adr/carrier-hierarchy-and-process-diet.md recording the hierarchy, the receipts principle, and the retirements
  - when scripts/validate_architecture.py runs against a live-constraint ADR lacking a contract block, the validator shall fail
  - clause: when scripts/smoketest_hooks.sh runs, each surviving hook shall block its known-bad input
    except: "universal-set: surviving hooks are reversibility-guard.sh, reality-check.sh, using-cairn-carrier.sh, role_guard.py"
  - if role_guard.py denies a write, then the hook shall exit 2 (blocking), asserted by both a unit test and the smoketest liveness check
  - when role_guard.py receives an absolute path to an in-envelope file, the hook shall allow it (exit 0), asserted by a unit test
  - the cairn-intent close-review brief shall instruct the reviewer to diff changed paths against the intent contract's execution-scope
  - the handoff file shall carry at most 6 active thread lines with the amended tests/unit/test_handoff_contract.py green
  - clause: every live-constraint ADR shall carry a contract block naming its mechanical carrier
    except: "universal-set: the live-constraint set is the ~14 ADRs enumerated in the refocus ADR"
  - clause: open gh issues serving retired machinery shall be closed citing the refocus ADR
    except: "operator-bound: gh closures are external writes authorized by the operator-approved plan; final close list surfaced before execution"
must-not-violate:
  - ADR append-only discipline (reversibility-guard rules)
  - uv run pytest green at every retirement commit; tests deleted with their mechanism, never skipped
  - reversibility-guard.sh, checks/role_guard.py + .claude/active-envelope.yaml + hook registrations, cairn-intent skill + both checkpoint agents, using-cairn carrier, checks/premise_guard.py + its tests, and contract tests remain live
wrong-if:
  - a hook liveness test passes while the hook fails to block its known-bad input
  - after the role_guard repair, a known-good absolute in-envelope path is denied (the deny-everything inversion)
  - any deleted mechanism's tests survive as skipped tests
  - test_handoff_contract.py red after the handoff diet
escalate-when:
  - the fresh-context challenge sustains a block on any premise
  - an issue slated for closure turns out defect-shaped rather than retired-machinery-shaped
  - an unintended consumer-facing change emerges beyond the named role_guard enforcement repair
evidence:
  - uv run pytest output at each retirement commit
  - scripts/smoketest_hooks.sh run output
  - validate_architecture.py pass output plus the intentionally-red contract-block case in a unit test
  - intent-challenge.md and close-review.md reports in the workspace
execution-scope:
  - docs/adr/.*
  - docs/ARCHITECTURE\.md
  - docs/roadmap\.md
  - docs/operational-reference\.md
  - docs/operator-field-notes-.*\.md
  - docs/dogfood-log\.md
  - CLAUDE\.md
  - \.claude/handoff\.md
  - \.claude/active-envelope\.yaml
  - \.claude/skills/.*
  - \.claude/agents/.*
  - \.claude/skill-runs/carrier-hierarchy-refocus/.*
  - checks/.*
  - scripts/.*
  - tests/.*
  - commands/claude-code/.*
  - workflows/.*
```

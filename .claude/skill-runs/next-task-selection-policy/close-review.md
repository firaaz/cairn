# Close-review — next-task-selection-policy

Back-loaded reviewer, fresh context. Judged from the live diff, the live `.claude/handoff.md`,
and live `gh`/roadmap signal — not from the construction conversation. The front-challenge
(`intent-challenge.md`) passed and flagged ONE residual obligation for this stage: actually run
the selection ladder against the live handoff and record the pick. Honored below.

Sources read directly: `intent.md` (full `## Contract`), `git diff docs/operational-reference.md`,
`git diff --stat`, `git status --short`, `.claude/handoff.md`, `gh issue list --state open`,
`gh issue view 31`, `docs/roadmap.md` Must-land/`Depends on` markers,
`git rev-list --left-right --count origin/dev...dev`.

## contract-clause-check

### must-satisfy

1. **"present the six-rung selection ladder in order" — PASS.**
   Diff lines 403-408 are an ordered `1.`-`6.` list, rungs in the Specification's exact sequence:
   (1) `blocked` rots, (2) `deferred` parked, (3) finish-started, (4) severity tiebreak,
   (5) roadmap dependency tiebreak, (6) route by weight. The lead-in (diff line 401, "Apply the
   rungs in order; the first that resolves a candidate wins") makes the ordering load-bearing and
   first-match, matching intent Specification rung order.

2. **"every rung shall name the existing signal source it reads" — PASS.**
   Each rung carries an explicit `*Signal:*` callout:
   - R1 → `.claude/handoff.md` state `blocked` (diff:403)
   - R2 → `.claude/handoff.md` state `deferred` + freetext trigger (diff:404)
   - R3 → `git status` / `git log origin/<branch>..<branch>` + handoff context tails (diff:405)
   - R4 → GitHub issue `severity:` labels (diff:406)
   - R5 → `docs/roadmap.md` Must-land ordering + `Depends on (N)` markers (diff:407)
   - R6 → "the candidate's own nature, not a stored field" (diff:408)
   Every named source verified live (see scope/evidence below). The `except` clause (rungs = the 6
   enumerated) is satisfied — exactly six, no extras.

3. **"if a rung would require a new field/command/file, the section shall not introduce it" — PASS.**
   No rung introduces a maintained input. Diff line 409 states this explicitly ("reads only signal
   that already exists and is maintained independently — it adds no field, command, or file to keep
   current"). R6 deliberately reads "the candidate's own nature, not a stored field" — the one rung
   that could have demanded a new weight/tag avoids it by design.

### must-not-violate

1. **"no new standalone doc file; policy lives in docs/operational-reference.md" — HOLDS.**
   `git diff --stat` shows `docs/operational-reference.md | 17 +++` and nothing else under `docs/`.
   `git status --short` confirms the only tracked-doc modification is `M docs/operational-reference.md`.
   No `docs/next-task-selection-policy.md` exists. The dated field note named in execution-scope
   (`docs/operator-field-notes-2026-06-05.md`) was NOT created — which is fine: it is an *allowed*
   scope target, not a required one, and the dogfood record lives here in the close-review instead.

2. **"no executable ranking logic (script/command/weights) added" — HOLDS.**
   The diff is pure prose markdown. No `scripts/`, `commands/`, `checks/`, or `plugins/` file touched
   (`git diff --stat` = one file). No frozen weights — diff line 408 explicitly rejects a stored
   field; diff line 399 names the bespoke-ranker-with-frozen-weights anti-pattern as the thing the
   policy avoids. "Selection stays a human judgment the ladder makes explicit, not deterministic
   automation" (diff:409).

## evidence-adequacy-check

The contract's `evidence` is grep + `git diff --stat` + a live-handoff dogfood — deliberately not a
pytest file, because the change is pure documentation with no executable behaviour. That is the
correct evidence shape for a D3-graduation light-docs section; absence of a test is not a finding.

The question is whether grep + dogfood is *adequate for this contract's depth*. It is, and the depth
matches the diff:

- **grep** (`grep -n "Next-task selection"` → line 397; rungs at 403-408) proves the structural
  clauses (heading exists, six rungs, in order) — mechanically sufficient for must-satisfy #1 and
  the "names a signal source" surface of #2.
- **The dogfood** is the only thing that can catch the contract's one genuine risk — a ladder that
  *reads* systematic but yields a wrong/contested pick (intent `## Risk Surface`, `wrong-if`). I ran
  it (below). It converges. Because the diff is a 17-line, zero-behaviour, zero-new-data section, the
  domain-wrongness surface is exactly "does the ladder resolve sanely against real state," and the
  dogfood probes precisely that. Evidence depth is proportionate to diff depth — neither thin-on-heavy
  nor over-built. No deeper evidence (e.g. a test) is *available* for a doc with no executable path,
  and none is *needed* given the smell-test below.

## scope-check — IN SCOPE

`execution-scope` = `docs/operational-reference.md`, `.claude/skill-runs/next-task-selection-policy/`,
`.claude/handoff.md`, `docs/operator-field-notes-2026-06-05.md`.

- The only tracked change is `docs/operational-reference.md` — in scope.
- `.claude/skill-runs/next-task-selection-policy/` is an untracked workspace dir — in scope (this
  report writes into it).
- The other untracked dirs in `git status` (`cairn-intent-loop-build/...`, `intent-review-build/`,
  `using-cairn-carrier-decision/phase-*`) are **pre-existing, unrelated skill-run artifacts** from
  other threads, NOT products of this construct step (the construct step changed exactly one file per
  `git diff --stat`). They are not attributable to this feature and are out of this diff entirely.
- `.claude/handoff.md` and the dated field note were NOT modified — both are allowed-not-required
  targets. No out-of-scope write by the construct step.

**No out-of-scope file.**

## Live-handoff dogfood — RAN THE LADDER (the residual obligation)

State pulled live: handoff has 1 `blocked` (`gh#31`), 4 `deferred` (trial-b, delivery-mechanism-friction,
git-workflow-v1, cairn-intent-git-lifecycle), rest `open`. `origin/dev...dev` = `0 0` (nothing
unpushed). Open issues carry live `severity:` labels (S1 on #4,5,6,7,8,9,10,11,15,16,17,23,26; S2 on
#12,13,14,17,18,19,20,21,22,27,28,29,30,31). Roadmap items 6,7,8,9 carry `Depends on (N)` markers.

- **R1 (blocked rots):** `gh#31 blocked V-3-attempt-2+V-5-operator-bound`. `gh issue view 31` confirms
  V-3 is a manual `/plugin install` from a fresh non-cairn session and V-5 is operator-bound — the
  unblocking action is **not agent-executable**. R1's instruction "clear it or surface it" resolves
  to **surface #31 to the operator**. First-match wins → the ladder's pick is *surface gh#31*.
- **R2 (deferred skip):** all 4 deferred triggers unmet today (2026-06-05 < 2026-09-01 trigger;
  no J5-count signal; the two git ADRs marked deferred/firm). Correctly skipped. Non-contradictory.
- **R3 (finish-started):** no unpushed/staged source work; handoff tails name paused trials
  (TrialD-paused, m2-paused). R3 would steer toward resuming a paused trial over a fresh issue —
  actionable.
- **R4 (severity):** S1 issues sort ahead of S2 — labels live and applied. Actionable.
- **R5 (roadmap deps):** item 1 (`/decision` rethink) has no unmet dep; items 6-9 carry explicit
  `Depends on` markers. Actionable, non-contradictory.
- **R6 (route by weight):** the R1 result (#31 — outward-facing release/`/plugin install` touching a
  published payload) is correctly classified operator-surface, consistent with the R1 outcome.

**Pick: surface `gh#31` (blocked, operator-bound M7 close) to the operator.** The ladder converges on
a single, defensible, non-contradictory candidate. Every rung names a signal that exists and is
populated; no rung references a missing source. `wrong-if` does NOT fire.

## Smell-test — contract depth vs diff size

17-line section, six rungs, three reused signals, zero new data, zero executable path. The
scope-statement ("add a written next-task selection ladder ... anchored to existing
handoff/severity/roadmap signal, introducing no tool or new maintained data") faithfully describes
the diff — it neither over-claims (no tool/automation promised that the diff doesn't deliver) nor
under-claims (the diff adds nothing the contract omits). Contract depth (one structural clause + one
signal-source clause + one no-new-data clause + a dogfood obligation) is matched 1:1 by a 17-line
docs section. No thin-contract-on-heavy-diff mismatch. Right-sized.

## Verdict

All must-satisfy clauses hold against the cited diff lines; both must-not-violate clauses hold; the
diff stays inside execution-scope; grep + dogfood evidence is proportionate to a zero-behaviour docs
change; and the live-handoff dogfood — the front-challenge's named residual obligation — produces a
defensible, non-contradictory pick (surface gh#31). Contract depth matches diff size.

Residual risk (documented, not blocking): the ladder is a human-judgment aid, so a future backlog
state could surface a contested pick that no static review anticipates; the section itself routes
that case to operator escalation (diff:409), which is the correct handling. Also: the dated field
note named in execution-scope was not created — acceptable, as the dogfood record lives in this
close-review and the note was an allowed-not-required target.

```json
{"status": "close-review-pass", "verdict": "all six must-satisfy clauses hold against diff lines 397-410 (six rungs in order, each names a live *Signal:* source, no new maintained data); both must-not-violate clauses hold (only docs/operational-reference.md changed per git diff --stat, pure prose, no script/command/weights); diff stays in execution-scope; grep+dogfood evidence is proportionate to a zero-behaviour 17-line docs section; the live-handoff dogfood was actually run and converges on a defensible non-contradictory pick (surface gh#31, blocked+operator-bound) with every rung's signal verified live", "clause_results": ["must-satisfy[six-rung ladder in order]: PASS (diff:403-408, first-match lead-in diff:401)", "must-satisfy[every rung names existing signal]: PASS (*Signal:* callouts diff:403-408; all sources verified live)", "must-satisfy[no new field/command/file]: PASS (diff:409 'adds no field, command, or file'; R6 reads candidate nature not a stored field)", "must-not-violate[no new standalone doc]: HOLDS (git diff --stat = docs/operational-reference.md only; no docs/next-task-selection-policy.md)", "must-not-violate[no executable ranking logic]: HOLDS (pure markdown; no scripts/commands/checks touched; no frozen weights)", "wrong-if[indefensible/contradictory pick]: DOES NOT FIRE (ladder converges on surface-gh#31, all lower rungs non-contradictory on live state)", "wrong-if[names a non-existent signal source]: DOES NOT FIRE (handoff states, severity:S1/S2/S3 labels, roadmap Depends-on markers all verified live and populated)"], "evidence_summary": "grep resolves heading@397 + six rungs@403-408; git diff --stat = 1 file/17 insertions; live dogfood ran the ladder against current .claude/handoff.md (1 blocked, 4 deferred, origin/dev...dev=0 0, live severity labels, live roadmap Depends-on) and produced pick=surface gh#31 — defensible and non-contradictory; grep+dogfood is the correct and adequate evidence shape for a no-behaviour docs section, no test needed or available", "residual_risk": "Ladder is a human-judgment aid; a future backlog state could surface a contested pick no static review anticipates — the section self-routes that to operator escalation (diff:409). The dated field note in execution-scope was not created (allowed-not-required; dogfood record lives in this close-review instead)."}
```

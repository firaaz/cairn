# Intent-challenge — next-task-selection-policy

Front-loaded skeptic pass. Fresh context; canonical source read directly. `premise_guard`
already exited 0 (verbatim grounding); this report does the semantic attack it cannot.

## premise-source-checks

### P1 — `source: docs/adr/board-as-roadmap-substrate.md`, quote: "The board is **never** a mirror of cairn-side state."

- Read `docs/adr/board-as-roadmap-substrate.md:60-73` (D1 — Four-layer model).
- Surrounding lines: line 71 — "The board is the **front door** — capture without ceremony…
  Promotion to features.yaml or slice is gated; capture is not." Line 73 — the quoted sentence,
  continued: "It is the cairn-side committed answer to 'what could be worked on' — not 'what is
  being worked on'…"
- The `label:` claims the board "is a capture surface, not a ranked view of the backlog — it does
  not answer 'which task next'." The surrounding code (the ADR's own D1 table at lines 64-71)
  assigns the board the role "what could be worked on" with cardinality "Many small items," and
  line 73 expressly denies it mirrors cairn-side execution state. The label faithfully describes
  these lines. **Faithful.**

### P2 — `source: docs/adr/board-as-roadmap-substrate.md`, quote: "None of the four are required by this ADR."

- Read `docs/adr/board-as-roadmap-substrate.md:127-136` (D5 — PM-session commands stay in `.local/`).
- Surrounding lines: line 129 names the four — `/groom`, `/promote`, `/weekly-status`,
  `/board-sync`. Line 131 — "This ADR commits to the **pattern** … not to immediate
  implementation of the four commands. None of the four are required by this ADR. They are
  described in `docs/plans/2026-04-27-board-roadmap-integration.md` as design sketches and remain
  there until built."
- The `label:` claims "the board-driven PM commands are decided-but-unbuilt, so no built path
  ranks the next task." Verified against the live filesystem: `commands/claude-code/.local/`
  contains exactly `dev-mode.md` and `README.md` — none of `/groom`, `/promote`,
  `/weekly-status`, `/board-sync` exist as files. The label faithfully describes both the quote
  and the live tree. **Faithful.**

## semantic-counterfactual-search

For each premise I constructed the reading under which the grounded quote is true but the
intent's claim fails, and tested it against live source.

### P1 counterfactual — "board never mirrors cairn-state, yet still ranks next task"

Constructed reading: a surface can be "not a mirror of cairn-side state" and *still* present a
ranked backlog (the board could rank its own captured items even if it doesn't mirror cairn
execution state). If true, "the board does not answer 'which task next'" would be false.

Tested against source. The closest thing to a ranked board view in the repo is `/dev-mode` §4
(`commands/claude-code/.local/dev-mode.md:60-63`): it buckets board items by Status and lists
"top 3 each by priority/order" for Ready/Backlog. This is a **read-only dashboard** that surfaces
board Status; it is cairn-internal (`.local/`, not shipped), gated behind a Docker MCP that may be
absent (line 63 fallback), and — per `board-as-roadmap-substrate` D1 — reflects the board's *own*
state, which is "what could be worked on," not a cross-signal decision of which task next.
Critically, the cairn-side board flips that would populate Status (`/start-slice`/`/close-slice`
log + `/board-sync` reconciler, D2/D4/D7) are themselves the unbuilt four from P2 — so the board's
Status field is not even being written by the cairn pipeline today. The counterfactual **does not
hold**: there is no built surface that ranks the next task. Label survives.

### P2 counterfactual — "quote is about the four PM commands, but some OTHER built path ranks next"

Constructed reading: the quote only disclaims the four named PM commands; the intent's broader
claim is "nothing **anywhere** ranks which open item to work next." A grounded quote about four
specific commands cannot, by itself, license a claim about the whole repo. So I searched the whole
repo for any ranking/prioritization/next-task mechanism the premise's dependent claim denies.

Tested against source (grep across `commands/ scripts/ checks/ plugins/ docs/` for
ranking/priority/next-task/triage/select-next):
- `/catchup` (`commands/claude-code/catchup.md:9-15`) — reads handoff + git + envelope and
  **stops**; "the user drives next." Explicitly does not rank: line 15 "No 'what would you like to
  do next?' prompts." Not a ranker.
- L-002 "Route-before-run / Triage" (`docs/lessons.md:27-60`) — a *classifier* of which flow a
  unit of work routes to (`/start-slice` vs `/decision` vs `brainstorming`); it does not pick
  **which** open item to work next. Different axis. Promotion to a `/triage` skill is explicitly
  deferred (line 60).
- `triager-tdd` / `superseded_test_signal.py` — adjudicates a phase `RAISE_ISSUE` (ESCALATE /
  RE_DISPATCH / ABORT) *inside* a running slice. Not next-task selection.
- `docs/roadmap.md:88` ("Not for v1") explicitly defers "Dependency graph automation /
  topological slice ordering" — the repo's own roadmap names automated next-task ordering as a
  **not-yet-built** item, corroborating the gap.
- No script/command/check/plugin computes or emits a ranked next task.

The counterfactual **does not hold**: the broader "nothing ranks next" claim survives whole-repo
search. The four-command quote is a sufficient (not load-bearing-alone) instance; the dependent
claim is independently true against live source. Label survives.

## Additional attacked claims (intent body, not premise-block)

These are not in `## Premise Grounding` so `premise_guard` never touched them, but the intent's
`must-satisfy` / `wrong-if` clauses depend on them. I verified each against live source.

- **Signal sources exist and are populated** (the ladder reads them; `wrong-if`: "names a signal
  source that does not already exist"):
  - Handoff `open|blocked|deferred` — `.claude/handoff.md` body carries ~40 thread lines; all
    three states present (e.g. `…#31 blocked V-3…`, `…trial-b.md deferred…`, dozens `open`).
    Contract at handoff frontmatter pins state ∈ {open, blocked, deferred}. **Populated.**
  - `severity:S1/S2` GitHub labels — `gh label list` confirms `severity:S1`, `severity:S2`,
    `severity:S3` exist; `gh issue list --state open` shows them densely applied (S1 on #4,5,6,7,
    8,9,10,11,15,16,23,26; S2 on #13,14,17,18,19,20,21,22,27,28,29,30,31). **Populated.**
  - Roadmap `Depends on` ordering — `docs/roadmap.md` Must-land section uses explicit
    `Depends on (N)` markers (items 6,7,8,9 reference predecessors) and a "Gated — sequenced after
    specific milestones" section naming gates. **Populated.**
  - All three rungs are anchored to live, already-maintained signal. No new maintained data.

- **Envelope placement** (`must-not-violate`: "no new standalone doc file… policy lives in
  docs/operational-reference.md"; Specification claims a standalone doc "would be denied"):
  - `.claude/active-envelope.yaml` is `mode: operator`. `paths:` includes
    `^docs/operational-reference\.md$` (line 16) — target is in-envelope, write allowed.
  - No pattern matches `docs/next-task-selection-policy.md` (the `^docs/.*` wildcard is **not**
    present; only enumerated `^docs/<name>\.md$` entries plus `^docs/adr/.*`, `^docs/plans/…`,
    `^docs/operator-field-notes-.*`, `^docs/lessons\.md$`, `^docs/roadmap\.md$`). A standalone
    `docs/next-task-selection-policy.md` matches nothing → `role_guard` denies. **Claim correct.**
  - `docs/operational-reference.md` has a natural adjacency target: `## Routing…` (line 19) and
    `## Context Discipline Protocol` (line 334) — the Specification's "adjacent to routing /
    context-discipline material" placement is real.

- **Scope-depth smell** (is a 6-rung markdown ladder right-sized?):
  - The intent builds no tool, adds no maintained data, and reuses three live signals. The repo's
    own roadmap defers *automated* next-task ordering (line 88) and the operator stated a
    build-at-home/maintenance allergy — a written policy is the lowest-maintenance form and matches
    the stated constraint. No rung invents a new input.
  - The ladder's rungs are individually actionable against the current backlog: blocked (#31 is
    `blocked`), deferred (trial-b, delivery-mechanism-friction marked `deferred`), finish-started
    (multiple `open` in-flight threads), S1>S2 tiebreak (live labels), roadmap Depends-on
    (live markers), route-by-weight. None is non-actionable or contradictory given real state.
  - One genuine residual (already named by the intent's own Risk Surface and `wrong-if`): the
    ladder could *read* systematic but yield a contested pick on real backlog — domain wrongness no
    grep catches. The intent correctly routes this to the close-review dogfood (apply ladder to the
    live handoff, record the pick). That is the right place for it; it is not a premise-grounding
    defect and does not sustain a block here. The close-review must actually run the dogfood, not
    just confirm the heading exists.

## verdict

Both grounded premises survive the semantic attack: each `label:` faithfully describes the lines
surrounding its quote, and both constructed counterfactuals fail against live source. The
policy-gap (not tooling-gap) framing is corroborated, not refuted — `/dev-mode` is a read-only,
unbuilt-flip board dashboard, `/catchup` stops without ranking, L-002 triage is flow-routing not
item-selection, and the roadmap itself defers automated next-task ordering. All three signal
sources the ladder reads are live and populated. The envelope placement claim is correct. Scope is
right-sized; the one real risk (domain-wrong pick) is the intent's own declared close-review
obligation, not a grounding gap.

**Pass.**

```json
{"status": "challenge-pass", "verdict": "both grounded premises' labels faithfully describe their source spans; both semantic counterfactuals fail against live source; the policy-gap-not-tooling-gap framing is corroborated (no built path ranks next task) and all three signal sources are live and populated", "challenged_premises": ["P1:board-never-mirrors-cairn-state", "P2:none-of-the-four-required"], "cited_evidence": ["docs/adr/board-as-roadmap-substrate.md:60-73", "docs/adr/board-as-roadmap-substrate.md:127-136", "commands/claude-code/.local/ (only dev-mode.md + README.md)", "commands/claude-code/catchup.md:9-15", "docs/lessons.md:27-60", "docs/roadmap.md:88", "commands/claude-code/.local/dev-mode.md:60-63", ".claude/handoff.md (open/blocked/deferred states present)", "gh label list (severity:S1/S2/S3 exist + applied)", ".claude/active-envelope.yaml:16 (operational-reference in-envelope; no standalone-doc pattern)"], "blocked_counterfactuals": ["P1: board not-a-mirror yet ranks-next — refuted: only ranked surface is /dev-mode, a read-only unbuilt-flip dashboard of board Status, not a cross-signal next-task decision", "P2: some OTHER built path ranks next — refuted: whole-repo search found only flow-triage (L-002) and in-slice RAISE_ISSUE triage; roadmap defers automated ordering"]}
```

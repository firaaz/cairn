# Operator field notes — 2026-06-01

## Trial E, data point 1 — cairn-intent loop dry-run (gh#28 mitigation 2)

First felt-cost dry-run of the cairn-intent loop, run as the activate-first
dogfood (the activation lever landed the same session at `26d00c1`). Vehicle:
gh#28 "intent.md template tightening", scoped to mitigation 2 (pin the operator
prompt verbatim). Workspace: `.claude/skill-runs/intent-template-operator-prompt/`.

### What the loop did
- Formed intent (1 write + `premise_guard` exit 0).
- Front intent-challenge (fresh ctx): **blocked once**, 1 revision, re-challenge → pass.
- Operator sign-off on the intent.
- Construct (test-first, one continuous context): RED → impl → GREEN; 2 new tests.
- Close-review (fresh ctx): pass, 1 documented residual.
- Operator sign-off on the close. Closed.

### Felt cost vs four-phase (cairn-tdd-feature)
**Lighter** for a change this size. The loop spent 2 fresh-context subagent
dispatches (challenge + close-review) + 2 operator sign-offs, with construction
in one continuous conversation. Four-phase would have dispatched 4 full phase
subagents (Reader/Skeptic/Builder/Auditor) + 4 commits + per-phase context-window
setup — strict isolation that is overkill for a one-section template change. The
loop preserved the decorrelation (2 fresh contexts at the brackets) at roughly
half the dispatch ceremony.

### Value delivered (the load-bearing signal)
The front-challenge caught a **real semantic error the mechanical gate could not**:
the premise quote was verbatim-grounded (`premise_guard` exit 0), but the label
**over-read** it — D3's "no hard cardinality gate" was widened into "no length
cap", manufacturing a D3 ↔ gh#28-#3 conflict the source does not support.
`premise_guard` (mechanical, verbatim-match) passed it; the fresh-context
same-family challenge caught the semantic gap. This is exactly the decorrelation
value proposition: the checkpoint catches what the mechanical gate structurally
cannot. It also caught an under-scope (the omitted authoritative shape source
`.claude/agents/phase-1-tdd.md`).

### Semantic-grounding-leak check
No leak shipped. The over-read was caught pre-construction; the close-review
re-confirmed evidence live and the eight-section derive-don't-fabricate contract
stayed intact (the `wrong-if` leak did not occur). The one residual (the in-sync
guard is substring-based) is documented and accepted.

### Caveats — do NOT over-read a single point
- n=1, and the vehicle was **self-referential** (the loop improving its own
  intent template) — motivation to make the loop look good is a confound on the
  value read.
- The same-family decorrelation residual (Kim et al. ~60% co-miss, `intent-management-loop`
  D4 EXPOSED) is **unmeasured** here: the challenge caught *my* error this once;
  that is an anecdote, not evidence against correlated misses. The slice-#25
  counterfactual probe remains the separate mechanical acceptance gate and was
  **not** run here.

### Incidental finding — Trial-E sink mismatch
`cairn-intent` skill Step 6 says record the Trial-E observation to
`docs/dogfood-log.md`, but that log has a rigid defense-catch schema
(slice/defense/type/would-manual-have-caught/disposition, evaluated by
`scripts/dogfood_evaluate.py`) built for the cliff-failure-mode defenses — it
does not fit a felt-cost narrative, and the operator envelope does not permit
writing it. Recorded here per the approved plan instead. The canonical felt-cost
sink for Trial E is an open question worth a one-line skill fix.

### Loop reliability observations
- The dispatched `intent-review` (close-review) agent's report did not appear in
  this feature worktree — it was written to the **main worktree**
  (`/.../cairn/.claude/skill-runs/.../close-review.md`) instead. Subagents
  dispatched from a feature worktree resolved the write against the primary
  worktree (a cwd / CLAUDE_PROJECT_DIR misdirection), so the artifact silently
  landed in the wrong tree. Discovered when the merge into `dev` flagged the file
  as a colliding untracked path; the agent's real report was then promoted into
  the committed artifact. A genuine cairn-on-cairn worktree hazard — subagent
  writes can escape the feature worktree (related: gh#30 cairn-on-cairn-carve-out,
  gh#4 close-sequence-hardening). Worth its own gh issue.

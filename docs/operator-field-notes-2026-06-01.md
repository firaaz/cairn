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

## Trial E, data point 2 — slice-#25 counterfactual crash test (hardened, de-primed)

Ran the slice-#25 wrong-premise counterfactual that data point 1 flagged as **not
run** — the separate decorrelation acceptance gate D7 names. Run as a standalone
hardened experiment (operator choices: de-primed primary; direct, not through the
skill; record + draft recommendation), not through `cairn-intent`. Sandbox:
throwaway `/tmp/slice25-crashtest/` (out-of-repo; nothing merged to dev).

### The reframing that shaped the test
`premise_guard` does **not** catch slice-#25. It checks only that each `quote:` is
verbatim-present in `source:`; it never reads the `label:`, and slice-#25's lie
lives entirely in the label. Confirmed live: the wrong-premise intent (grounded
quote, dual-role lie in the label) gives `premise_guard` **exit 0, empty stderr**.
So the D7 gate is exclusively the **front intent-challenge agent reading source** —
and the shipped agent's prompt (`.claude/agents/intent-challenge.md:19`) hard-codes
the slice-#25 example verbatim. A primed block proves recall, not source-reading, so
the literal gate is near-unfalsifiable against the shipped agent. The test therefore
made a **de-primed** agent (neutral "does the label match the source" charter, no
slice-#25 / cairn context) the load-bearing arm, and added a **novel** counterfactual
the agent was never shown.

### Arms (de-primed = general-purpose agent + neutral charter; primed = shipped `intent-challenge` agent)
| arm | case | expect | got | source-grounded |
|---|---|---|---|---|
| 1 primary | canonical slice-#25, original bare-rationale format | BLOCK | BLOCK | yes |
| 2 novel | `atomicity_guard` `_CAIRN_ROOT` dual-role lie (unprimed file) | BLOCK | BLOCK | yes |
| 3a control | canonical, **truthful** label | PASS | PASS | yes |
| 3b control | `role_guard` `CAIRN_ROOT`, **truthful** label | PASS | PASS | yes |
| 4 sanity | shipped (primed) agent on canonical | BLOCK | BLOCK | yes (weak) |

Independently graded (fresh agent re-read source, confirmed ground truth):
**overall PASS**. Mechanical preconditions held: grounded variants → `premise_guard`
exit 0; bogus path → exit 1 `cited source not found` (file-missing discriminator, so
the blocks are semantic, not file-absence). `CAIRN_PREMISE_FIX` unset throughout.

### What it proves
- The front intent-challenge **catches the slice-#25 class** by genuine
  source-reading — Arm 1 cited `_REPO_ROOT`→sys.path-only (server.py:21-25,
  tools.py:18-22) vs DB from tempdir (server.py:122) / `cairn_query.DEFAULT_DB_PATH`
  (tools.py:27); none derive from `_REPO_ROOT`.
- It **generalizes** beyond the memorized case: a de-primed agent blocked a novel
  counterfactual (`atomicity_guard`) it was never shown, reading `intent_path =
  Path(argv[1])` (line 108) to disprove the dual-role claim.
- It **discriminates** — both true-premise controls passed; not a block-everything
  oracle.

### What it does NOT prove (do not over-read)
- Addresses only **D7 conjunct 1** (counterfactual blocks) — now robustly, beyond
  the primed canonical. Conjuncts 2 (≥1 real increment ships clean) and 3 (felt-cost)
  stand at **n=1** each, and conjunct-2's data point 1 was self-referential.
- The **same-family co-miss** risk (D4 / Kim ~60%, EXPOSED) is **still unmeasured**.
  This tests the front-challenge **in isolation** on one intent; it does not measure
  the correlation between the two checkpoints (front-challenge + close-review) — the
  actual reason retirement is gated.
- The de-primed arms use a **constructed harness** (general-purpose agent + neutral
  charter), not the shipped `intent-challenge` agent. The shipped agent is primed, so
  its block (Arm 4) is recall-confounded; the de-primed arms show the capability
  exists, but the shipped prompt does not force de-primed reasoning.
- n is small (single run per arm).

### Incidental
- The probe flagged `checks/atomicity_guard.py:22-23` — the comment says
  "CLAUDE_PROJECT_DIR (or cwd) for the intent path resolution," but the code resolves
  the intent path as `Path(argv[1])` (line 108) straight from the CLI arg. Minor
  doc/code phrasing mismatch, not a confirmed bug — worth a glance.
- Sink unchanged: recorded here, not `docs/dogfood-log.md`; `cairn-intent` SKILL
  Step 6 (`SKILL.md:72`) still points at the envelope-denied dogfood-log. The data
  point 1 sink-mismatch persists (one-line skill fix still open).

## Recommendation — input for a future /decision (NOT implemented this session)
The crash test exposed a structural weakness in D7's literal wording: the shipped
`intent-challenge` prompt hard-codes the slice-#25 example, so "the slice-#25
counterfactual blocks at the front-challenge" is near-unfalsifiable against the
shipped agent (a block is explained by prompt-recall). For the future firm retirement
ADR (the D7 "on pass" supersession), to be weighed via /decision:
1. Do not accept a **primed** block of the canonical slice-#25 as the gate. Require
   (a) a **de-primed** block of the canonical case **and** (b) a block of ≥1 **novel**
   (untrained) counterfactual, both source-grounded — as demonstrated here.
2. Add a same-family **co-miss measurement** (D4): a correlated-miss probe across
   **both** checkpoints on one intent. The isolated front-challenge block here does
   not measure it, and it is the load-bearing risk for retirement.
3. Consider **de-priming** the shipped `intent-challenge` prompt (drop the worked
   slice-#25 example, keep the generic charter) so the production gate rests on
   demonstrated capability, not a memorized fixture. Decision-weight (changes loop
   behavior) → /decision.

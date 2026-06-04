# Trial-E W3 — team brief (decision-prep, operator-bound calls)

You are the team lead for **W3 of Trial-E closure**: the three separate `/decision`
arcs. Set up an agent team (you are in tmux, in a dedicated window) and run the
**parallelizable prep** for all three decisions, then **pause and surface each
decision to the operator** — do NOT make the operator-bound calls yourself.

Read this brief, then read the closure spec and the W1 field note before spawning
anyone. Persist all team output under `.claude/skill-runs/trial-e-w3/<arc>/`.

## Source-of-truth files (read these first)

- `docs/plans/2026-06-02-cairn-trial-e-closure.md` — the closure spec. §3.W3 + §4 + §6 define the three arcs, their gates, and the exit criteria. **This is your governing doc.**
- `docs/operator-field-notes-2026-06-04.md` — W1 cross-family probe result.
- `docs/operator-field-notes-2026-06-02.md` — dp3 (co-miss, asymmetry finding), dp4, dp5.
- `docs/operator-field-notes-2026-06-01.md` — dp1, dp2.
- The three target ADRs (each holds the deferred decision): `docs/adr/intent-contract-cost-model.md`, `docs/adr/intent-management-loop.md`, `docs/adr/intent-fidelity-measure-before-enforce.md`.
- `docs/adr/identity-and-scope-deferral.md` — D3 revisit triggers (`:45`); trigger #4 binds D-retire.

## What is already done (do not redo)

- **W2** — dp5 sink fix committed (`c371d72`). Tree clean for that work.
- **W1** — cross-family co-miss probe **run and committed** (`84f5ce6`). Result: a fresh **Codex** front-challenger scored **5/5** vs ground truth (3/3 planted fidelity defects blocked, 2/2 controls passed, 0 misses, 0 false positives) over the dp3 corpus. This is **parity** with dp3's same-family front arm (also 0/3 miss) — **no measured improvement**, because the baseline already had no misses. Artifacts: `.claude/skill-runs/trial-e-w1-*`, `grader.json`.
  - **W1 caveat (load-bearing for D-xfam):** the five cases were *reconstructed from the dp3 corpus inside the Codex session*, not freshly Claude-authored. Treat the result as the Codex-challenge datum over the dp3 corpus. If strict Claude-draft provenance is required, the cases must be rerun from a Claude-authored case pack.

## The three decisions (each its own `/decision` arc — keep separate)

### D-xfam — `measure-before-enforce` B (cross-family enforcement)
- **Trigger (ADR `:90`):** commit cross-family fidelity enforcement *iff* the cross-family co-miss delta is **materially below** same-family ~60% on the fidelity-leap class.
- **W1 says:** 0/3 vs the same-family 0/3 front-arm baseline → **no material delta below baseline.** The pre-recorded trigger is **not met**.
- **Prior:** record "not triggered." The live operator-bound question is whether the **W1 provenance caveat** (Codex-reconstructed cases) is acceptable for a "not triggered" close, or whether a Claude-authored rerun is required first.

### D-retire — `intent-management-loop` D7/R2 (retire the four-phase pipeline)
- Decide whether to retire the four-phase pipeline now that Trial-E data is in.
- **Must engage `identity-and-scope-deferral` D3 trigger #4** (supersession by explicit `/decision`) — this `/decision` *is* that invocation; address the deferral's Alternatives section.
- **Inputs:** dp3's **front-loaded / asymmetry** finding (front intent-challenge is the strong arm; close-review is a conditional backstop) + dp4/dp5 live-dogfood felt cost + W1 cross-family parity + trials-plan Trial-3 pass criteria (`2026-05-20-...:213`: slice-#25 blocks under `premise_guard` — confirmed; ≥1 production session completes the four-phase-replacement shape with no semantic-grounding leak — dp4/dp5).
- **Constraint:** do NOT frame retirement on "two independent decorrelation catches" — dp3 shows fidelity is front-loaded. Keeping `cairn-tdd-feature` as a fallback is a live option.

### D-cost — `intent-contract-cost-model` D3 (heavy-band bundle)
- Decide **commit vs retire** the heavy-band enforcement bundle (derived banding + agent-declared/challenger-attacked severity + front-loaded fidelity challenge).
- **Gate (D5):** does the formal proof catch anything a thin prose intent + the existing gates would not? Adjudicate on dp1–5 + W1. Note D2 is already built (agent-judges-band + operator-veto 5a).

**Dependencies:** D-xfam's result feeds the "front-loaded fidelity challenge value" question in D-cost and the cross-family angle in D-retire. Surface them in an order that lets the operator see those links (suggested: D-xfam → D-cost → D-retire), but keep each a distinct decision.

## How to run it (operator memory: "Run /decision with agent teams")

1. `TeamCreate` a team (e.g. `trial-e-w3`).
2. For each arc, parallelize the `/decision` **prep** phases via teammates:
   - **Phase 0** — constraint envelope (what's fixed/forbidden for this decision).
   - **Phase 0.5** — journey trace (how this decision got here; what prior decisions bind it).
   - **Phase 2** — 2–3 candidate approaches with tradeoffs.
   - Mount the **attack-before-synthesis** pass on every load-bearing claim (operator memory: default-to-acceptance is the named failure mode) — including the W1 result and the dp3 findings.
3. Persist each arc's prep to `.claude/skill-runs/trial-e-w3/<arc>/` (e.g. `d-xfam/`, `d-cost/`, `d-retire/`) so teammate prompts stay short.
4. **PAUSE at the gate.** Present each decision to the operator with the approaches + your recommendation + the main tradeoff. The operator makes the call (Phase 3+ selection, ADR write). The calls are operator-bound by design: operator-veto 5a, identity D3.4, retire-vs-keep.

## Out of scope for this team
- The `measure-before-enforce` D1 (baseline capture) + D3 (decoy/recall pilot) instrumentation build — downstream, not a Trial-E blocker.
- Writing the final ADRs / making the calls without the operator.
- No new hooks (`intent-management-loop` D6).

## Closing the loop (after the operator makes the calls — for later, not now)
Per closure-spec §6: transition the three ADR statuses, mark trials-plan Trial-3 closed, resolve the handoff Trial-E threads, and confirm/firm the provisional `cairn-intent-git-lifecycle` bits keyed to Trial E.

## Worktree note
Shared tree, concurrent sessions (operator memory). Stale untracked leftovers exist
(`.claude/skill-runs/.../_check/`, `using-cairn-carrier-decision` phase docs) — ignore them;
do not commit them. The closure spec + envelope are committed (`d2d37fe`).

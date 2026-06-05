# Operator field notes — 2026-06-05

## Trial-E observation: next-task-selection-policy (cairn-intent loop)

**Work:** codify the next-task selection ladder as a docs section in `docs/operational-reference.md` (17 lines, zero executable behaviour). Preceded by a 14-agent research workflow that surfaced the already-accepted `board-as-roadmap-substrate` ADR and reframed the ask as a policy gap, not a tooling gap.

**Felt cost vs four-phase pipeline.** Heavy relative to the diff: full loop = intent contract + premise-grounding gate + fresh front-challenge subagent + fresh close-review subagent + two operator sign-offs, for a 17-line prose section. The four-phase pipeline would have been heavier still (per-phase resets); the intent loop's single continuous construction was the right call. But for a light docs change the two decorrelation subagents are the dominant cost. D3 graduation (thin contract for light work) helped — no test, scope-statement + 3 must-satisfy clauses.

**Did the checkpoints earn their cost?** Yes, more than expected for docs work. The front-challenge did NOT rubber-stamp — it ran its own whole-repo grep and independently corroborated "nothing ranks the next task" (catching that `/dev-mode` is the only ranked surface and its flips are unbuilt). The close-review independently ran the dogfood the front-challenge had flagged. Both added real verification, not ceremony.

**Correlated-miss signal (the Trial-E watch).** None detected — but also not exercised. Both same-family checkpoints PASSED and converged on the same dogfood pick (surface gh#31). That is agreement on a correct result, not independent detection of an injected defect; there was no planted error to test the Kim-et-al ~60% same-family agreement risk. So this run gives no evidence either way on correlated MISS. Note for the cross-family `/decision` trigger: convergence-on-correct is not the signal; convergence-on-wrong is — and nothing here stressed that.

**Process note.** Research-before-build (operator-initiated) materially changed the outcome: it caught the already-accepted board ADR that two earlier read-only passes (my own + the first Explore) missed, preventing a redundant build proposal. Worth keeping the "adopt-vs-build research before any new tooling" reflex.

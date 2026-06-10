# Operator field notes — 2026-06-10

## carrier-hierarchy-refocus close (cairn-intent loop observation)

**Feature:** the refocus itself — carrier hierarchy adopted, receipt-less machinery retired, role_guard repaired, corpus carrier-declared. Decision-weight change run through the lean form (ADR + fresh-context attack) it proposes — first instance, self-applied.

**Checkpoint receipts (the headline observation).** The front challenge ran five revision rounds and produced four real catches, two of them severe: (1) deleting role_guard without deregistering its settings hooks would have bricked every write in any operator session — the plan as operator-approved contained a session-killing defect; (2) the gh#35 exit-code fix alone would have inverted the silent fail-open into a deny-everything gate, because the exit-1 defect was masking a path-shape defect (absolute tool paths vs repo-root-relative regexes) — found by the challenger running the hook live. It also reversed a retirement on receipts grounds (premise_guard has logged reds; the challenge agent's own receipts were measured with it as precondition) and caught an unsatisfiable contract clause (handoff ≤6 lines vs the open-issue coverage test). The close-review independently caught a green-on-dirty-tree miss: a handoff pointer to an uncommitted doc — every clean checkout was red while the construction tree passed. No correlated miss observed; the two checkpoints caught disjoint defect classes (front: design/premise defects; close: tree-state defects).

**Felt cost.** Five challenge rounds ≈ 3 subagent dispatches + 2 resumes (~280k subagent tokens total incl. close-review); each round returned concrete, evidence-cited blocks — none felt like ceremony. Versus an 8-phase /decision arc: materially cheaper, and the catches came from exactly the two checkpoints the lean form keeps.

**Enforcement irony, recorded.** The repaired role_guard landed its first live deny mid-construction (stale envelope vs scripts/postinstall_validate.py) — the mechanism whose deletion the plan proposed proved its liveness during the session that nearly deleted it. The operator's "it returns 1 instead of 2 — do the fix" call was validated, but only because the challenger had already surfaced the second defect the fix needed to pair with.

**Residual.** Historical bisect gap at 3050df1/25bb90f ratified at sign-off. Production gate remains primed — measurement is the roadmap top item; this session's catches are still primed-gate data.

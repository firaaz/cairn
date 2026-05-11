# Phase 2 — Convergence note + comparison

## Comparison table

| Axis | A1 — `url` + `sha` | A3a — self-marketplace (`./dist`) | A6 — Releases tarball URL |
|---|---|---|---|
| **Empirical prior** | 82/82 Anthropic plugins use `url`+`sha`; **strongest** | 49/82 Anthropic plugins use string-relative-path; **strong** | 0/82 Anthropic plugins use tarball URL; **none** |
| **Bypass mechanism** | Hypothesis: sha-pin routes to HTTP-fetch-by-commit path | By construction: no second clone — payload is in marketplace-cache dir | Hypothesis: `.tar.gz` URL routes to HTTP-fetch (no git) |
| **Probe cost** | ~5 min (5-line manifest edit, push, install) | ~30 min (probe branch + dist commit + default-branch override) | ~30 min (build tarball, gh release create, manifest edit) |
| **Restructure scope** | Manifest field swap + 1 workflow step | Manifest shape change + dist-on-dev discipline shift | Workflow restructure + release-asset pipeline |
| **Consumer prereq delta** | Zero | Zero | Zero (tarball extraction in-resolver) |
| **Platform risk** | Windows BELIEVED (same darwin/linux resolver) | Windows BELIEVED but SSH-bypass is structural | Windows BELIEVED; tar-impl uncertain |
| **INV-012 impact** | Field swap (ref→sha); semantics preserved | Redefined (`dev`-tip authoritative, `release` archaeology) | Redefined (release-asset URL authoritative) |
| **Schema-lint assertion delta** | 4 preserved, 1 redefined | 3 rewritten, 2 retained | 3 rewritten/dropped, 2 retained |
| **release-publish.yml delta** | +1 step (post-push SHA capture + dev rewrite) | 0 or fail-fast verify (no new push) | +2 steps (tar package + gh release create) |
| **Two-step CI coupling** | YES (S3 anti-pattern) | NO | YES (tag + release-asset ordering) |
| **Update mechanism** | BELIEVED via marketplace-cache refresh of `dev` | Same as Anthropic's 49 self-marketplace plugins | Worst case — URL rotation + cache refresh |
| **New-infra delta** | Zero | Zero | Zero (uses `github.token`) |
| **Exit-ramp cost** | ~30 min (1 PR — drop sha, restore ref) | ~1-2h (1 PR — restore URL shape + assertions) | ~2 PRs (revert workflow + manifest, asset URL orphaned) |
| **R-most-painful** | Sha-locked consumers on update (S4) | dev-instability bleeds to consumers (R-A3a-3) | Resolver may not support tarball URLs at all (R-A6-1) |
| **Adversarial weak point** | "ref resolves to sha internally; pin field non-causal" | "Deep restructure for unverified hypothesis" | "If it worked, Anthropic would already do it" |
| **Synthesis rank** | **1st** (highest empirical prior + lowest cost) | **2nd** (most robust by construction) | **3rd** (highest hypothesis risk) |

## Cross-cutting findings

1. **All three are probe-gated.** None have empirical V-3 confirmation today. Each needs the same kind of operator-bound install probe before the impl slice opens. Probe cost is the discriminator.

2. **Update mechanism is the second-order unknown for all three.** Stage 6 (phase-0.5-journey:88-96) is the resolver behavior we have not observed for any source-type. Whatever transport we pick, F3 check-9 must run **both** install + update cycles. A3a has the best prior (49 examples ride marketplace-cache refresh); A6 has the worst (URL rotation is fragile).

3. **A1 + A3a are complementary, not redundant.** Same probe surface (fresh consumer, no SSH key) discriminates between them. If A1 probe passes, ship A1 (cheaper). If A1 falsifies, A3a is the next probe — it costs more to set up but has a stronger structural argument. A6 only enters if both fail.

4. **The control approach (A7 — document SSH prereq)** is the implicit fallback if all three probes falsify. A7 ships zero engineering but spends the "zero-friction install" credit from `delivery-mechanism-friction`. It is a real option, not a non-option — and should be named explicitly in the ADR's risk register so the decision shape includes a known exit.

5. **A1's "two-step CI coupling" is the residual concern.** The m5-plugin-deployment-pattern Phase 3 stress test rejected Approach D for two-step coupling (constraints:45). A1 reintroduces it (push `release` → rewrite `marketplace.json` on `dev`). The Phase-3 adversarial pass should attack this directly.

## Provisional recommendation (pending Phase 3)

**Probe-sequenced shape:**

1. **A1 probe first** (5-min cost, 82/82 empirical prior). If green → ship A1; close decision.
2. **A3a probe if A1 falsifies** (30-min cost, structural SSH-bypass). If green → ship A3a; supersede with new ADR.
3. **A6 probe if A3a falsifies** (30-min cost, weakest prior; consider skipping straight to A7 instead).
4. **A7 (document SSH prereq) if all empirical paths fall** — ship a CONSUMER.md note + amend `delivery-mechanism-friction` to mark zero-friction install as superseded, with a triggered re-decision when Anthropic ships an upstream resolver fix.

The ADR captures **A1 as the load-bearing decision**, with A3a/A6/A7 enumerated as triggered fallbacks. Firmness: **provisional** — until F3 check-9 passes the install + update cycle, A1 is hypothesis-grade.

## What Phase 3 must attack

- **The sha-vs-ref causal claim.** Is the 82/82 Anthropic pattern actually causal, or stylistic? What evidence would falsify the causal interpretation that doesn't require us running V-3 attempt 3?
- **The two-step CI coupling rejection rationale.** Did the m5-plugin-deployment-pattern Phase 3 stress test rule out two-step coupling per se, or only when paired with a third-party Action (Approach D)? Re-read the rejection rationale; if it was Action-specific, A1's first-party two-step is fine.
- **The update story across all three.** Stage 6 is unknown for every approach. Should the decision include a Stage-6 probe as a load-bearing acceptance gate, not just "documented in F3 check-9"?
- **The "ship A7 immediately" steel-man.** If Anthropic's bug is open with three issues filed and no fix shipped, betting on the resolver's behavior is fragile. A7 + watch upstream + revisit at fix-release is a defensible "do less" move. What's wrong with it?

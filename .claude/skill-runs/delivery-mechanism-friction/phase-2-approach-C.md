# Phase 2 — Approach C: Hybrid / split

## One-paragraph statement
Ship a strictly-budgeted `using-cairn` SessionStart skill plus a *navigational* subset of the branch (`slice-status`, `worktree-map`, `adr-context`, `handoff-closer`) in this slice; defer the *diagnostic* pair (`pytest-triage`, `root-cause-hunter`) and the PREREQS surface to a follow-on slice that gates them behind detection. The bet: most of the branch's onboarding/orientation value is in agents that need *no new consumer-machine deps*, and most of #33-1's value is in a SessionStart pointer (not payload). Doing both at once is not "the safe lukewarm middle" because A (capability-up) and B (friction-down) each leave half of Phase 0.5's verified friction unresolved — A doesn't fix J1's 20-min prose-orient (still no SessionStart), B doesn't fix J2's "no /catchup in F1" or J3's manual ADR-context harvest. C resolves the friction whose mechanism is already known to be zero-new-dep, and refuses to commit on the friction whose mechanism is still contested.

## Concrete shape (what actually lands in THIS slice)
- **`using-cairn` SessionStart skill** (#33-1): pointer-only, hard byte budget ≤2,000 tokens injected, progressive-disclosure links to CLAUDE.md/CONSUMER.md/phase-skill-mapping. Detects `superpowers` SessionStart and yields/dedupes (mitigates S2). Composes via "if superpowers already loaded, emit only cairn-delta"; otherwise emits short cairn-orientation block. CI token-budget check on the injected payload (mitigates S9).
- **Branch agents shipping in this slice:**
  - `slice-status` — reads git log + handoff; no new deps. Ship.
  - `worktree-map` — reads filesystem + git worktree list; no new deps. Ship.
  - `adr-context` — reads `docs/adr/`; no new deps; directly closes J3 step 1–4 "manual Phase 0 harvest". Ship.
  - `handoff-closer` — substrate-reinforcing (stage-by-name, no -A, no amend, no commit-to-dev/main, no push). Encodes existing CLAUDE.md commit-hygiene rules in agent form. No new deps. Ship.
- **Branch agents deferred:** `pytest-triage`, `root-cause-hunter` — defer to provisional slice **`diagnostics-with-detection`**. Re-ship only after (a) superpowers cite is softened to opt-in *or* (b) an ADR justifies hard-pinning superpowers with explicit reversal cost (S8) and a `.slice-system` exclusion is tested (S5).
- **New consumer-side requirements:** none beyond current floor (`jq`, `ruff`, `python3`). Zero added setup surface this slice.
- **PREREQS.md disposition:** reshape, do not ship as-is. Becomes `docs/optional-capabilities.md` describing Pyright/ast-grep/LSP/superpowers as *opt-in capability enablers* tied to deferred diagnostic agents, not preconditions for cairn. Defer the version-floor decision to the diagnostics slice.
- **ADR(s) this slice commits:** one — **`delivery-mechanism-friction`** — with these clauses: (a) SessionStart bootstrap is the discovery vehicle, pointer-not-payload, budgeted; (b) cairn agents that ship in main payload take **no hard external-plugin dep**; (c) auto-routing of agents is **out of scope** for this slice (S3, S10 deferred to diagnostics slice); (d) diagnostic agents require substrate pre-flight before any write. No ADR-locking of Pyright/ast-grep/superpowers as cairn deps yet.
- **Out-of-scope-for-this-slice from #33's 7 candidates:** #33-2 (slash discoverability — partially covered by SessionStart pointer, full surface in M5.1), #33-3 (role_guard heredoc removal), #33-4 (`/fix-adr-typo`), #33-5 (id+name scoping), #33-6 (small-change path), #33-7 (commit-prefix vs JSON-stdout).

## Constraint fit (against Phase 0 hard + soft constraints)

| Constraint | Fit | Evidence |
| --- | --- | --- |
| H1 phase-pipeline locked | OK | No agent ships modifies phase count/names; SessionStart is orthogonal to dispatch. |
| H2 plugin distribution release-branch+marketplace | OK | All 4 agents + SessionStart skill ship via `dist/` curation; no install-mechanism change. |
| H3 maintainer dogfood (INV-011) | OK | No LSP/indexer this slice, so `.slice-system` symlink loop hazard (S5) is dodged entirely. |
| H4 role isolation fabrication-block | OK | New agents are read-only or commit-only (handoff-closer); role_guard unchanged. |
| H5 ADRs append-only | OK | One new ADR; no supersession; reversibility-guard unchanged. |
| H6 Conventional Commits binding (INV-001) | OK | `handoff-closer` explicitly enforces this; reinforces, not relaxes. |
| H7 session-start ≤40k (INV-004) | OK *with measurement* | SessionStart capped ≤2k; CI budget check enforces. Mitigates S1, S9. |
| H8 three-tier context discipline | OK | SessionStart is Tier-1 pointer; agents are Tier-2 on-demand. |
| Soft 1 progressive disclosure | OK | SessionStart is lite-pointer to `.full.md` siblings. |
| Soft 2 audience tags | OK | SessionStart respects `[both]` vs `[maintainer]`. |
| Soft 3 new deps ADR-justified | OK | None added; deferred diagnostics will need their own ADR. |
| Soft 4 structural enforcement | Partial | SessionStart token budget is CI-checked; agent-definition pre-flight (J1 step 7, J2 step 2 risk) **not** structurally enforced this slice — see exposure below. |
| Soft 5 minimize ceremony | OK | No new operator setup steps. |
| Soft 6 bootstrap autonomy | OK | SessionStart auto-fires; no manual install step beyond plugin install. |

## Pre-mortem exposure (against Phase 1 S1–S10)
- **S1 context-budget breach:** HANDLED. PREREQS.md not shipped; SessionStart hard-budgeted ≤2k with CI check; 4 agents shipped are read-on-demand (Tier 2), not eager-loaded.
- **S2 SessionStart collision with superpowers:** HANDLED. ADR clause requires detect-superpowers-and-yield/dedupe; integration-test against clean Claude Code session with superpowers installed is acceptance gate.
- **S3 auto-routed false-fire across repos:** HANDLED by deferral. No auto-routing this slice; the two diagnostic agents that motivated it are deferred. Slice ADR explicitly puts auto-routing out of scope.
- **S4 superpowers drift cascade:** HANDLED. ADR clause (b) — no hard external-plugin dep in shipped agents. The deferred diagnostic slice owns this question.
- **S5 INV-011 maintainer dogfood breakage:** HANDLED. No LSP/indexer/ast-grep this slice; `.slice-system` symlink loop hazard untouched.
- **S6 PREREQS shifts friction:** HANDLED. PREREQS.md not shipped as consumer precondition; reshaped to opt-in capability doc tied only to deferred agents.
- **S7 per-worktree LSP memory:** HANDLED by deferral. No LSP this slice.
- **S8 reversibility of ADR-locking superpowers:** HANDLED. Slice ADR explicitly does *not* lock superpowers as a cairn dep; the deferred diagnostics ADR must carry reversal-cost analysis.
- **S9 SessionStart ballooning:** PARTIAL. Day-one budget + CI check is the documented mitigation; long-term drift requires policing on every PR touching the skill. Best available mitigation, but a forever-tax.
- **S10 operators never learn surface because auto-routing hides:** HANDLED. No auto-routing this slice; navigational agents are invokable by name and surfaced via SessionStart pointer.

**Weakest exposure: S9** — the SessionStart skill is an evergreen accretion target. Mitigation is real (token budget + CI) but requires sustained discipline; cannot be made fully structural without a hard byte cap that may force ugly trade-offs in 6 months.

**Secondary exposure: agent-definition pre-flight (Phase 0.5 highest-friction #2)** — shipping `handoff-closer` and the 3 navigators expands the set of agent-definitions that must pre-load. SessionStart can *surface* this but does not *enforce* it; structural fix is out of scope this slice.

## Downstream impact
- **`parallelism-v1` workflow:** Net positive. `worktree-map` + `slice-status` directly serve the cross-worktree state-boundary gap flagged in Phase 0.5 §State boundaries §Cross-worktree; no new daemon/memory pressure since no LSP ships.
- **`m5-plugin-deployment-pattern` release surface:** Compatible. SessionStart skill curates into `dist/skills/`; 4 agents curate into `dist/agents/`. No marketplace.json or release-branch shape change. Release workflow unchanged.
- **Consumer time-to-first-dispatch (J1):** Cuts the ~20 min prose-orient (J1 step 3–5) to ~3 min via SessionStart pointer + `adr-context`/`slice-status` invokable by name. Closes J1 highest-friction #1.
- **Returning-operator experience (J2):** Partial. SessionStart auto-fires (closes J2 step 1 gap). `/catchup` still missing in F1, but `slice-status` is a serviceable proxy invokable by name from SessionStart's pointer. Closes most of J2 highest-friction #3.
- **Maintainer dogfood loop (INV-011):** Unaffected (no LSP/indexer added).
- **Future slices:**
  - Unblocks: `diagnostics-with-detection` (gets pytest-triage + root-cause-hunter with proper detection + ADR), M5.1 `/catchup` ship (composes with `slice-status`), `auto-routing-design` (if ever wanted, can be its own decision).
  - Defers: #33-3 through #33-7, branch's PREREQS surface, superpowers hard-cite question.

## Evidence (not memory)
- Phase 0 H1–H8, soft constraints 1–6.
- Phase 0.5 J1 step 3–5 (20-min prose-orient), J1 step 7 (pre-flight risk), J2 step 1–3 (mid-slice resumption), J3 step 1–4 (`/decision` ceremony), J5 (pytest-triage motivation).
- Phase 1 S1, S2, S3, S5, S6, S9, S10 mitigation mechanisms.
- INV-004 (40k budget), INV-011 (dogfood), INV-012 (release-branch lock).
- ADRs: `m5-plugin-deployment-pattern` D4 (hook registration), `context-discipline-protocol` (pointer-not-payload), `cairn-substrate-and-fastmcp-superseded` D2 (new-dep gate).
- CLAUDE.md §Safety-critical §Symlink recursion hazard (forces S5 deferral if LSP shipped).
- Branch facts: `feature/workflow-subagents` @ `8b680cb`, +334 LOC, 6 agents, `docs/PREREQS.md`.
- L-005 (prompt-only drift), L-020 (mechanize execution contracts).

## Why this approach beats the alternatives (steelman)
- **C resolves Phase 0.5's verified friction with zero-new-dep mechanisms, then stops.** A ships unverified capability claims (framing load-bearing #1, #3, #4 all unargued); B ships SessionStart but throws away `handoff-closer` and `adr-context`/`slice-status`/`worktree-map`, all of which are substrate-reinforcing or navigational and cost nothing.
- **"Split slice = double gates and half velocity" is wrong here, because the split is along the dep-surface axis, not the work axis.** The 4 navigational agents + SessionStart share one ADR, one F3 audit, one release. The diagnostic 2 require their own decision (auto-routing? cite-strength? `.slice-system` test? per-worktree daemon ceiling?) — that's a different conversation, and pretending it's the same conversation (A) is the velocity loss.
- **C is the only approach that doesn't paper over S3, S5, S7 with prose.** A ships them and hopes; B sidesteps them by shipping nothing. C ships the parts whose pre-mortem exposure is HANDLED and defers exactly the parts whose pre-mortem exposure would be PARTIAL/EXPOSED.
- **C honors `feedback_attack_before_synthesis`.** Framing load-bearing claims #1, #3, #4 are unverified; C does not commit to them. It commits to the operationally-verified part (Phase 0.5 friction is real, navigational agents need no new deps) and forces the contested part through its own /decision (deferred slice ADR).
- **C closes the largest Phase 0.5 friction transitions (#1 J1 prose-orient, #2 pre-flight, #3 J2 resumption, #4 J3 ADR-harvest via `adr-context`) without touching #5 (pytest-triage), which is also the only one with unverified setup-cost magnitude.**

## What this approach asks the operator to accept
- **Slice scope is larger than B.** SessionStart + 4 agents + 1 ADR is more surface than B's SessionStart-alone. Defended: the 4 agents are zero-new-dep and substrate-reinforcing; not shipping them now means doing a second slice for work that has no contested decisions.
- **Capability is less than A.** No pytest-triage, no root-cause-hunter, no LSP-driven navigation this slice. Defended: those agents' value is real but their setup-cost magnitude (framing load-bearing #4) is unverified; ship them when the cost-side evidence exists.
- **One ADR locks in early.** `delivery-mechanism-friction` ADR commits to: SessionStart-is-pointer, no-hard-external-plugin-dep, auto-routing-out-of-scope. A or B could defer some of these. Defended: those three commitments are the ones that mitigate S2, S4, S8, S10 — deferring them means deferring mitigations, which is worse than committing to a defensible position now.
- **`/catchup` gap in F1 remains for non-SessionStart paths.** `slice-status` is invokable from SessionStart pointer but not auto. Defended: M5.1 ships `/catchup`; SessionStart bridges the gap; no need to duplicate.
- **Branch is partially merged, partially deferred.** Branch author may prefer all-or-nothing. Defended: handoff-closer + navigational 3 land in this slice with attribution; diagnostic 2 land in the follow-on slice with attribution. Net branch survival = 4/6 in slice 1, 2/6 in slice 2.

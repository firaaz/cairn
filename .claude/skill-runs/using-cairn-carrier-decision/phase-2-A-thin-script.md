---
decision: using-cairn-carrier-contract
phase: 2-approach-A
approach: A-thin-script
date: 2026-06-01
---

# Phase 2 — Approach A: Thin Bash-Script, In-Repo-First

One coherent answer to the five coupled sub-questions, then constraint-fit,
premortem exposure, and downstream impact. Honest, not advocacy.

## The five answers as one design

### (1) Testable "fired" definition — RENDER, not host injection

"Fired" = the carrier script, run as a SessionStart command hook, emits a
deterministic first stdout line `CAIRN_CARRIER_FIRED` followed by exactly one of
a pointer line (`cairn: active intent — <path>` + scope) or the literal
`cairn: no active intent — run the cairn-intent skill to load or form one`. This
is exactly the #2 draft (`proposed/using-cairn-carrier.sh:33-46`,
`proposed/test_using_cairn_carrier.py:59-91`).

The unit test runs the bash script in a subprocess with a fixture
`CLAUDE_PROJECT_DIR` tmp tree and asserts:
- first line == `CAIRN_CARRIER_FIRED` (`test_using_cairn_carrier.py:59-63`),
- a fixture handoff + `intent.md` yields the pointer
  (`:80-91`), an empty tree yields the no-intent signal (`:75-77`),
- `returncode == 0` on all paths (`:66-69`).

This satisfies D5's "testable 'fired' definition" (`intent-management-loop.md:79-81`)
and the D9 acceptance scope "the carrier's fired-detection + fallback"
(`:100-104`) **as a render test**. The honest limit, correctly surfaced by the
close-review (`close-review.md:138-141`): the test asserts the script *renders*
the marker, NOT that Claude Code actually injects it at SessionStart on a host.
The "fired on host" claim stays a Trial-E integration observation
(`intent-management-loop.md:102-104`: "Trial-E dogfood is the integration test").
Phase 0's (1)-vs-(5) tension (`phase-0-constraints.md:157-161`) is resolved on
the in-repo side and explicitly NOT on the consumer side — consumers get the
script, not the test suite.

A bash carrier makes the marker observable two ways simultaneously: it is the
stdout the host injects AND the stdout the test captures. There is no separate
"render path" vs "inject path" — the same `echo` is both. That is the one place
the thin script is genuinely cleaner than a SKILL-file realization.

### (2) ≤2k-token budget — in-hook byte clamp, env-overridable

`CAIRN_CARRIER_BUDGET_BYTES` (default 8000 ≈ 2000 tokens at ~4 B/tok), clamped at
emit time via `head -c` (`using-cairn-carrier.sh:18,27-30,47`). Env-overridable
per CLAUDE.md no-hardcoded-sizes. Truncation is visible (mid-line cut), not
silent. The unit test forces a 32-byte cap and asserts the emission obeys it
(`test_using_cairn_carrier.py:97-108`).

This is the *runtime* enforcement. It is a crude proxy — bytes ≠ tokens, and the
close-review flags this honestly (`close-review.md:142-145`): a proxy can pass a
payload a real tokenizer scores >2k. But the carrier's content is fixed and tiny
(a marker + one pointer line + a ~200-char scope snippet), so the proxy's
inaccuracy is harmless *for this payload* — there is no path by which a 5-line
pointer block crosses 2000 real tokens.

Critically: the byte clamp is the ONLY enforcement this approach ships in-slice.
`tests/unit/test_context_budget.py` measures the **40k turn-1 host budget via
telemetry** (`test_context_budget.py:108-114`), not the carrier's own 2k render —
nothing in-repo asserts "the carrier alone renders ≤2k tokens" except the
byte-proxy. delivery-mechanism-friction D6's CI tokenizer gate
(`delivery-mechanism-friction.md:70-72`) is NOT built here. Per D6's own
fallback clause, not landing the CI check means S9 (SessionStart drift) stays
EXPOSED and L-005 drift exposure is the standing risk
(`delivery-mechanism-friction.md:72`). This approach accepts that exposure
deliberately: in-repo-first means runtime byte-clamp now, CI tokenizer gate
deferred to the same future ADR that hardens distribution (sub-question 5).

### (3) Fallback contract — skill never branches on carrier state

`cairn-intent` SKILL Step 1 (`load-or-form-intent`) runs **unconditionally**
(`SKILL-cairn-intent.md:49`: "This step is the carrier's fallback: if the
SessionStart carrier did not fire, load/form here explicitly — the carrier is an
optimization, not the only path (D5)"). The journey's summary is explicit
(`phase-0.5-journey.md:317-321`): the skill does NOT check "did the carrier
fire?" and skip Step 1. It always reads `.claude/handoff.md` +
`.claude/skill-runs/<feature>/intent.md`; if the carrier already injected the
pointer, Step 1 sees the same git state and quickly returns a `resume`
classification — one file read, no API call.

So the answer to "how does the skill detect non-firing, and does it branch on it
at all?" is: **it does not detect, and does not branch.** Non-firing is
indistinguishable from firing at the skill layer because both converge on the
same on-disk source of truth (handoff + intent.md). This is the most robust
fallback because the carrier can never strand or mislead the skill — the skill
re-derives from canonical state regardless (open decision (c) default,
`intent.md:238-251`).

This directly defuses the rejected "approve every session" fatal failure mode
the ADR pre-mortem found (`intent-management-loop.md:38-40`): the skill trusting
a carrier marker and skipping re-load is the stale-load risk; unconditional
re-derive eliminates it. The cost is a redundant file read when the carrier did
fire — negligible.

The honest weakness here is NOT in this approach's choice but in L-005
(`phase-0-constraints.md:148-152`): the fallback is a *prose-specified protocol
commitment* in a SKILL body, and L-005 says prose-specified side-effects execute
inconsistently under context pressure. The draft conformance test
(`test_cairn_intent_skill_conformance.py`) greps the fallback prose is *present*;
it cannot assert the running model *honors* it. Same exposure as any other
SKILL-step contract — Trial E is the only real test.

### (4) Realization — bash command hook, reconciled against D1's wording

A bash command hook at `checks/using-cairn-carrier.sh`, registered in
`.claude-plugin/hooks-template.json` under a new `SessionStart` block
(`proposed/hooks-template.json:3-12`), wired `${CLAUDE_PLUGIN_ROOT}/checks/...`
exactly like the three surviving guards.

**The reconciliation with delivery-mechanism-friction D1 is the load-bearing
honesty of this approach, and it does NOT cleanly resolve.** D1 LITERALLY says
"Ship `using-cairn` SessionStart **skill** at `dist/skills/using-cairn/SKILL.md`,
registered via `dist/hooks/hooks.json`" (`delivery-mechanism-friction.md:39`).
The thin-script approach ships a bash hook at `dist/checks/using-cairn-carrier.sh`
instead. Three things make this defensible but none make it conformant:

- D6 ("no new hooks", `intent-management-loop.md:83-85`) names the three
  *enforcement* guards (premise/role/atomicity) that must be reused unchanged; a
  SessionStart emitter is not an enforcement guard, so adding it is not literally
  a "new hook" in D6's sense. Phase 0 reads it the same way
  (`phase-0-constraints.md:166`: "a SKILL file carrier is not a hook... D6 is
  technically not violated"). But the symmetric reading also holds: a *bash
  command hook* registered in hooks.json IS a fourth `command` entry, and Phase
  0's (2)-vs-(4) tension note says exactly that — "that IS a fourth hook type in
  defiance of D6" (`phase-0-constraints.md:166`).
- D1's "SessionStart skill" can be read as "the thing that fires at SessionStart"
  rather than "a SKILL.md file". The #2 draft took that reading
  (`close-review.md:154-159` confirms honest-minimal: "the carrier is a bash hook
  in the surviving-guard family, not new Python"). But that is a *re-reading* of
  a firm-for-this-decision constraint (`phase-0-constraints.md:52`: "D1 — ...
  FIRM for this decision"), and re-reading a firm ADR's explicit
  `dist/skills/.../SKILL.md` path to mean "a bash script under checks/" is a
  stretch that a future reviewer can legitimately reject.
- The honest framing: this approach **trades D1 literal-conformance for
  honest-minimal + lowest blast radius.** A bash script that drains stdin and
  echoes five lines is the smallest possible carrier; it adds no Python module
  (CLAUDE.md honest-minimal, `phase-0-constraints.md:133`), reuses the
  surviving-guard family, and is mechanically reversible (delete one file + one
  hooks.json block). If the decision values honest-minimal over D1's literal
  wording, this is correct. If it values D1 literal-conformance, this approach is
  out of contract and a SKILL-file realization is required.

This is the single sharpest weakness of Approach A and it is a *contract* weakness,
not a technical one. The script works; it may simply not be what D1 authorized.

### (5) Distribution scope — cairn-internal ONLY until Trial E passes

The carrier ships into `dist/` via a `scripts/build_dist.py` ALLOW_LIST row
(`build_dist-allowlist.patch.md:9-15`), and `build_dist` deny-list permits
`checks/` so the row lands cleanly (`test_build_dist.py:122-138` —
EXCLUDED_TOPLEVEL is `.claude`, not `checks`/`skills`/`agents`). The thin-script
brief says: **register and test it cairn-internally now, but do NOT promote the
ALLOW_LIST row to consumer distribution until Trial E passes / the D7 retirement
ADR lands.**

Concretely, in-repo-first means:
- The carrier lives at canonical `checks/using-cairn-carrier.sh` and is wired in
  `.claude-plugin/hooks-template.json` — so cairn-the-repo's own sessions fire it
  via `.slice-system → .` (INV-011 self-consumption, `phase-0-constraints.md:25-34`).
  This is where Trial E dogfoods it.
- The `build_dist` ALLOW_LIST row is the lever that ships it to consumers. Holding
  that row back (or shipping it but documenting the carrier as provisional-inert)
  keeps the ADR-R1 blast radius off consumer sessions until the mechanism is
  proven.

The tension: hooks.json is a single shipped artifact. If the SessionStart block
is in the canonical `hooks-template.json` AND `hooks-template.json` is already in
the ALLOW_LIST (`build_dist.py:31`), then the SessionStart registration ships to
consumers the moment it lands canonical — even if the `using-cairn-carrier.sh`
ALLOW_LIST row is withheld. That produces a **dangling hook registration**: every
consumer session tries to run `${CLAUDE_PLUGIN_ROOT}/checks/using-cairn-carrier.sh`,
the file is absent, and the hook errors per session. So "cairn-internal only"
under this realization requires EITHER (a) gating the SessionStart block out of
the dist build (a `build_dist` transform, which the allow-list-is-contract design
has no mechanism for — `build_dist.py:1-8`), OR (b) shipping the script too but
keeping it inert, which is no longer "cairn-internal only." This is a real
coupling the brief's "cairn-internal ONLY" framing under-specifies.

ADR-R1 (stale `.slice-system` / non-Claude-Code-host blast radius,
`intent-management-loop.md:146,148`) is the reason to hold back: a carrier that
ships to every consumer fires on every consumer session, and a stale `.slice-system`
or a non-CC host turns that into silent grounding failure or a dangling hook.
In-repo-first scopes that blast radius to cairn-the-repo until D7. The cost: the
J1 friction-collapse that delivery-mechanism-friction D1 shipped *for*
(`delivery-mechanism-friction.md:78`: "~20 min to ~3 min") is NOT delivered to
consumers until D7 — so consumers keep paying the cold-start cost through the
whole Trial-E window. In-repo-first is conservative on R1 at the direct cost of
the friction the carrier exists to remove.

## Constraint fit (cite the envelope)

| Constraint (Phase 0) | Fit |
|---|---|
| INV-004 ≤2k carrier budget (`phase-0-constraints.md:182`) | MET at runtime via byte-clamp (crude proxy); NOT met by a CI tokenizer gate (not built — D6 EXPOSED accepted). |
| Testable "fired" + fallback, D5 (`:185`) | MET in-repo as a render test; host-injection stays Trial-E observation. |
| No new hooks; reuse three shipped, D6 (`:186`) | TENSION. Defensible (emitter ≠ enforcement guard) but a 4th `command` hook in hooks.json is the symmetric reading (`:166`). |
| Standing deps pydantic/typer/pyyaml (`:187`) | MET — bash + stdlib, zero new Python module (honest-minimal, `close-review.md:154-159`). |
| Premise-grounding keystone, carrier binds intent to evidence (`:188`) | PARTIAL — carrier greps handoff for an `intent.md` pointer (`using-cairn-carrier.sh:36-40`) but does NO freshness/version check; Phase-1 S2/S5/S6 stale-load exposures (below) are unmitigated by the carrier itself. |
| `cairn-intent` coexists, no retirement, D1 (`:184`) | MET — carrier + skill add a coexisting path; INV-003 + phase ADRs untouched. |
| INV-012 release-branch distribution (`:189`) | DEFERRED — distribution lever (ALLOW_LIST row) held back until D7. |
| delivery-mechanism-friction D1 literal "SKILL at dist/skills/" (`:52-57`) | VIOLATED-OR-REINTERPRETED — see sub-question (4). The sharpest fit failure. |

## Premortem exposure (Phase 1)

**NOT vulnerable / well-covered:**
- **S1 (non-CC host non-firing, `phase-1-premortem.md:21-29`)** — covered. The
  unconditional skill-Step-1 fallback (sub-q 3) means non-firing is a no-op; the
  loop is correct without the carrier. This is the approach's strongest property.
- **S4 (premise_guard `.slice-system` traversal, `:70-82`)** — out of scope for
  the carrier; the carrier reads `.claude/handoff.md` relative to
  `CLAUDE_PROJECT_DIR` (`using-cairn-carrier.sh:24-25`), not through
  `.slice-system`. S4 is a premise_guard concern, untouched here.
- **S3 budget drift (`:51-66`)** — partially covered: the byte-clamp prevents
  *runtime* runaway. NOT covered: silent *source* drift past 2k real tokens with
  no CI tokenizer gate (D6 not built). For this fixed 5-line payload the residual
  is near-zero, but the *mechanism* against drift is absent.

**Vulnerable (the carrier does not mitigate):**
- **S2 stale-intent poisoning (`:34-47`)** — EXPOSED. The carrier greps the
  *last* `intent.md` pointer in handoff (`using-cairn-carrier.sh:37`:
  `tail -n1`) and emits it with NO freshness, TTL, or version check. If a closed
  Feature-A pointer is still in handoff, the carrier emits Feature-A's scope into
  a Feature-B session. The skill's unconditional re-derive (sub-q 3) catches this
  ONLY if the skill re-reads handoff and reaches the same (wrong) pointer — i.e.
  the fallback does not *fix* a stale handoff, it faithfully reproduces it.
  Mitigation lives in handoff hygiene (INV-002 pointer states open/closed), not
  the carrier. S2's prescribed prevention (carrier emits freshness signal, skill
  ignores stale pointers, `:129`) is NOT implemented.
- **S5 fallback on stale `.slice-system` (`:86-103`)** — EXPOSED, and worsened by
  in-repo-first. If a consumer ever DOES get the carrier (post-D7) on a stale
  symlink, the carrier reads a deprecated-schema intent and the fallback loads a
  stale artifact. No version tag, no freshness check (`:99-103` prescription
  unimplemented).
- **S6 pointer file deleted at cleanup (`:107-120`)** — PARTIALLY EXPOSED. The
  carrier guards `[ -f "$PROJECT_DIR/$POINTER" ]` (`using-cairn-carrier.sh:39`),
  so a deleted-file pointer falls through to the no-intent signal — it does NOT
  emit a dangling pointer. But it also does NOT escalate ("approved intent is
  missing", `:117`); it silently degrades to no-intent, and the skill then
  form-fresh's a different contract. Silent contract-break survives.
- **L-012 (`docs/lessons.md:225`)** — DIRECTLY EXPOSED and the most
  approach-specific risk. A prior SessionStart **bash** cheatsheet hook emitted a
  misleading "No active slice — /start-slice" line; a low-tier Phase-4 agent
  quoted it verbatim and refused to proceed four times. This carrier emits a
  near-identical "cairn: no active intent — run the cairn-intent skill" line
  (`using-cairn-carrier.sh:45`). A low-tier agent in a legitimately read-only
  session (D8-exempt) could read that as a directive and refuse or derail. The
  bash-script realization inherits this exact failure shape; the byte-clamp and
  fired-marker do nothing against it. This is the strongest case that the emitted
  *prose* matters as much as the mechanism, and it is the lesson the thin-script
  approach most needs to answer (and the draft does not).

## Downstream impact

- **Consumers:** Net-zero during Trial E (distribution lever withheld). They keep
  paying J1 cold-start cost (`delivery-mechanism-friction.md:78`) until D7. If
  the SessionStart block lands canonical while the script ALLOW_LIST row is
  withheld, consumers get a **dangling hook error per session** (sub-q 5 coupling)
  unless the build is taught to strip the block — which allow-list-is-contract
  cannot do today.
- **Codex plugin:** Unaffected. The Codex `using-cairn`/`cairn-intent` SKILLs
  drive the same `workflows/cairn-intent.yaml` (`SKILL-cairn-intent.md:8`); the
  carrier is a Claude-Code SessionStart mechanism with no Codex analogue. No
  reconciliation surface — Codex has no SessionStart hook, so the carrier is
  simply absent there and Step 1 fallback carries it (same as any non-CC host).
- **Trial E:** This is where the carrier earns its keep. In-repo-first means
  cairn-the-repo dogfoods the carrier on its own sessions via `.slice-system`
  self-consumption; the "fired on host" claim that the unit test cannot make
  (sub-q 1) is exactly what Trial E observes (`intent-management-loop.md:102-104`).
  The bash realization makes this dogfood cheap to wire (one hooks.json block, no
  Python). But Trial E will also surface S2/L-012 (stale-pointer + literal-prose)
  if they bite — which is the honest point of dogfooding before consumer ship.
- **D7 retirement ADR:** This approach front-loads two decisions onto D7: (a)
  promote the `build_dist` ALLOW_LIST row to ship the carrier to consumers, and
  (b) build the D6 CI tokenizer gate before consumer ship (since the byte-proxy
  is the only enforcement and S3 drift is a per-consumer-blast-radius risk). It
  also leaves the D1-literal-conformance question (sub-q 4) unresolved — if a
  future reviewer insists D1 means a SKILL.md file, D7 inherits a re-realization
  cost (bash → SKILL) on top of retirement.

## Where this approach is weak (summary, no advocacy)

1. **D1 literal conformance (sub-q 4)** — ships a bash hook where D1 wrote
   "SKILL at dist/skills/.../SKILL.md". Defensible by re-reading, not conformant.
   The single sharpest weakness.
2. **L-012 literal-prose hazard** — the bash carrier's "no active intent" line is
   the same shape as the cheatsheet line that derailed a low-tier Phase-4 agent
   four times. Approach-specific, unmitigated by the draft.
3. **No CI tokenizer gate** — byte-proxy is the only enforcement; D6's S9 stays
   EXPOSED. Fine for this tiny payload, no *mechanism* against drift.
4. **Stale-load (S2/S5/S6)** — the carrier does no freshness/version check; the
   unconditional fallback faithfully reproduces a stale handoff pointer rather
   than correcting it. Mitigation is pushed to handoff hygiene + Trial E
   observation, not built in.
5. **Distribution coupling (sub-q 5)** — "cairn-internal only" is under-specified
   given hooks-template.json ships via the existing ALLOW_LIST; either a dangling
   consumer hook or shipping-but-inert results, neither of which is cleanly
   "internal only."

Its genuine strengths: lowest blast radius, honest-minimal (zero new Python,
mechanically reversible), the cleanest in-repo "fired" render test (stdout is
both inject and assert surface), and the most robust fallback (skill never trusts
the carrier, so the carrier can never strand or mislead — it can only redundantly
help).

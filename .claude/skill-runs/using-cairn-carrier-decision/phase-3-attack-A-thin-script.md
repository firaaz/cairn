---
decision: using-cairn-carrier-contract
phase: 3-attack
approach: A-thin-script
date: 2026-06-01
verdict: survives-as-cairn-internal-prototype-only; the consumer-distribution and D1-conformance framing do NOT survive
---

# Phase 3 — Adversarial Stress Test: Approach A (thin bash-script, in-repo-first)

Goal: refute. Disconfirming search against INV-004, delivery-mechanism-friction
D1/D6, the "fired" test's epistemics, and the distribution choice vs ADR R1. Every
load-bearing claim audited verified-vs-believed against live source. Default to
survives=false on a standing fatal flaw.

The honest finding: Approach A's own Phase-2 doc already self-discloses most of its
weaknesses. The attack's job is to test whether they are *fatal* (not just listed),
and to catch claims the doc states as fact that the source contradicts. One fatal
flaw stands that the doc *under-states* (it calls it "under-specified," not fatal);
one fatal flaw stands that the doc states correctly but does not let bite on the
verdict (D1 literal non-conformance). I let both bite.

## Load-bearing claim audit (verified vs believed)

| # | Claim in phase-2-A | Source check | Verdict |
|---|---|---|---|
| C1 | D1 LITERALLY says "Ship `using-cairn` SessionStart **skill** at `dist/skills/using-cairn/SKILL.md`, registered via `dist/hooks/hooks.json`" | `delivery-mechanism-friction.md:39` — exact quote present | **VERIFIED.** A ships a bash hook at `checks/using-cairn-carrier.sh`. Non-conformant. |
| C2 | hooks-template.json already ships via the existing ALLOW_LIST, so a SessionStart block lands on consumers the moment it's canonical | `build_dist.py:31` `(".claude-plugin/hooks-template.json", "hooks/hooks.json")` present; `dist/hooks/hooks.json` today has NO SessionStart entry; `dist/checks/` today holds only the three guards | **VERIFIED, and worse than the doc admits — see F1.** |
| C3 | byte-clamp is the ONLY in-slice 2k enforcement; D6 CI tokenizer gate not built | `.github/workflows/` = {`dist-gate.yml`, `release-publish.yml`}; grep token/tiktoken/sessionstart-budget → empty | **VERIFIED.** No CI gate exists. D6 S9 stays EXPOSED. |
| C4 | `tests/unit/test_context_budget.py` measures the 40k turn-1 host budget via telemetry, not the carrier's own 2k render | `test_context_budget.py:107-119` — `@pytest.mark.skipif(not _claude_available())`, measures turn-1 total via `claude` CLI | **VERIFIED, and stronger — see F2.** The host test is *skipped in CI*. |
| C5 | EXCLUDED_TOPLEVEL is `.claude`, not `checks`/`skills`/`agents`, so the carrier row lands cleanly | `test_build_dist.py:122-139` — confirmed; `checks`/`skills`/`agents` not excluded | **VERIFIED.** |
| C6 | The skill never branches on carrier state; both paths converge on `.claude/handoff.md` + intent.md | close-review.md:46-49 confirms Step 1 prose "if the carrier did not fire, load/form here explicitly"; carrier `using-cairn-carrier.sh:36-46` reads handoff | **VERIFIED at the prose layer.** Robust *by design*; fragile *by L-005* — see S4. |
| C7 | L-012 is directly exposed: the "no active intent" line is the same shape as the cheatsheet line that derailed a Phase-4 opus/low agent 4× | `lessons.md:225,231` — exact instance (`role-cheatsheet.sh` "No active slice — /start-slice", opus-4-7/low refused 4×); carrier `using-cairn-carrier.sh:45` emits "cairn: no active intent — run the cairn-intent skill" | **VERIFIED.** Same failure shape, same mechanism — see F3. |
| C8 | Fired test asserts RENDER not host injection | `test_using_cairn_carrier.py:42-53,59-63` — subprocess runs bash, asserts first stdout line == marker | **VERIFIED.** The test proves a script echoes; nothing more — see S3. |

No claim in phase-2-A is *falsified* by source — the doc is honest. The attack's
yield is that two of the disclosed weaknesses are **fatal**, not the "sharpest
weakness / under-specified" the doc grades them, and the test's epistemic reach is
even thinner than claimed.

---

## FATAL FLAWS (each independently sinks the approach as briefed)

### F1 — The "cairn-internal only" distribution choice is mechanically impossible under this realization; it ships a per-session dangling-hook error to every consumer the moment it lands canonical

This is the decisive refutation, and the Phase-2 doc *names the coupling* but grades
it "a real coupling the brief's 'cairn-internal ONLY' framing under-specifies"
(`phase-2-A-thin-script.md:181-182`). Under-specified is too soft. It is **incoherent
under the realization A picks**, and the failure mode is a live consumer regression.

Verified chain against source:
1. The carrier is registered by adding a `SessionStart` block to canonical
   `.claude-plugin/hooks-template.json` (`proposed/hooks-template.json:3-12`,
   command `${CLAUDE_PLUGIN_ROOT}/checks/using-cairn-carrier.sh`).
2. `build_dist.py:31` ships `hooks-template.json → dist/hooks/hooks.json`
   **unconditionally** — it is an existing ALLOW_LIST row with no transform, no gate
   (`build_dist.py:18-33,65-68` — the build is a flat copy loop; the module docstring
   states "Allow-list IS the contract … no include/exclude glob fields", `:1-8`).
3. Therefore the instant the SessionStart block is in canonical hooks-template.json,
   the next `build_dist` run writes a SessionStart command into `dist/hooks/hooks.json`
   pointing at `${CLAUDE_PLUGIN_ROOT}/checks/using-cairn-carrier.sh`.
4. **`dist/checks/` today contains only `reality-check.sh`, `reversibility-guard.sh`,
   `role_guard.py`** (verified by `ls dist/checks/`; `dist/hooks/hooks.json` today has
   no SessionStart entry). If A withholds the `checks/using-cairn-carrier.sh`
   ALLOW_LIST row to keep the carrier "cairn-internal only," the shipped
   `dist/hooks/hooks.json` references a script that **does not exist in the consumer
   payload** → every consumer SessionStart fires a command hook whose target file is
   absent.

So A's stated sub-q5 answer ("register and test cairn-internally now, withhold the
ALLOW_LIST row until Trial E / D7") produces one of exactly two outcomes, neither of
which is "cairn-internal only":
- (a) **dangling hook error on every consumer session** (script row withheld), or
- (b) **ship the script too** (script row added) — which is full consumer distribution,
  the precise R1 blast radius A claims to be deferring (`intent-management-loop.md:146`
  R1 stale-`.slice-system`/silent-grounding-failure; ADR Risk Register Med/High).

The build system has **no mechanism** to strip a single hook block from a
shipped-as-a-whole JSON file — `build_dist` is a flat allow-list copy with no
per-file transform (`build_dist.py:42-58`). A's own doc concedes this
(`:178-182`: "a `build_dist` transform, which the allow-list-is-contract design has no
mechanism for"). The conclusion the doc declines to draw: **A cannot deliver its own
sub-q5 answer.** The chosen realization (bash hook in the shared hooks-template.json)
*forecloses* the in-repo-first distribution posture it is selected to enable.

This is fatal because sub-q5 is one of the five coupled questions the decision must
answer, and A's answer is internally contradictory against live build behavior — not
a tradeoff, a defect. A's three exits all break a different commitment: (i) admit it
ships to consumers now (owns R1 directly, contradicting its stated conservatism), or
(ii) add a build transform / separate hooks fragment (new mechanism, contradicting
honest-minimal and "no new infra"), or (iii) keep the SessionStart block OUT of the
canonical *shipped* hooks-template.json and wire it only in cairn-the-repo's own
session config — which is a different design than the one A documents (A explicitly
registers in `proposed/hooks-template.json`, the shipped template, and its sub-q5 even
relies on `.slice-system → .` self-consumption firing it, `phase-2-A:164`).

**Refutation strength: decisive for sub-q5.**

### F2 — The "testable fired definition" does not satisfy D5/INV-004 in the sense the decision needs; in CI there is ZERO token-budget enforcement on the carrier

D5 requires the carrier emit its signal "**within the ≤2k-token INV-004 budget**"
(`intent-management-loop.md:79-81`). A claims this is MET at runtime via byte-clamp
(`phase-2-A:47-53,199`). Audit of what actually enforces the 2k:

- The byte-clamp (`using-cairn-carrier.sh:18,29,47`, default 8000 B) is a *byte* proxy,
  not a *token* count. A concedes bytes≠tokens (`:55-60`) and argues it is harmless
  *for this fixed payload*. Granted for today's payload — but D5's budget is on the
  *carrier*, and the only thing pinning the payload small is the current prose, not a
  measured token bound.
- `test_context_budget.py` does NOT measure the carrier's 2k render at all. It measures
  **turn-1 total host context ≤40,000 tokens** (`:108-119`, `BUDGET_HARD`), and it is
  `@pytest.mark.skipif(not _claude_available())` (`:107`) — **it does not run without
  the `claude` CLI on PATH, i.e. it is skipped in CI.** So the firm INV-004 binding
  A leans on (Phase-0 mapped INV-004 → this test, `phase-0-constraints.md:6,12`):
  (i) never measures the carrier in isolation, and (ii) is conditionally skipped in
  the exact environment (CI) where drift would otherwise be caught.
- D6's CI tokenizer gate, which delivery-mechanism-friction designates as *the*
  SessionStart-budget enforcement (`delivery-mechanism-friction.md:70-72`), **does not
  exist** (verified: no token/tiktoken/sessionstart workflow in `.github/workflows/`;
  only `dist-gate.yml`, `release-publish.yml`). D6's own fallback clause then applies:
  not landing it leaves S9 EXPOSED + L-005 drift as standing risk (`:72`). A accepts
  this (`phase-2-A:64-72`).

Net: the only thing standing between the carrier and a 2k-token overrun is a byte
proxy with an 8000-byte default that nothing re-validates as tokens, plus a host-budget
test that is *skipped in CI*. A's Phase-0 envelope lists "INV-004 ≤2k carrier budget"
as FIRM/machine-checked (`phase-0-constraints.md:6-13,182`). **That mapping is wrong**:
the ≤2k carrier sub-budget is a *prose* constraint from delivery-mechanism-friction D1
(`delivery-mechanism-friction.md:39`); ARCHITECTURE.md INV-004 itself
(`ARCHITECTURE.md:39-45`) bounds only the 40k turn-1 total and binds to a test that
never isolates the carrier. So the claim "INV-004 ≤2k carrier budget is MET" is a
*believed* satisfaction resting on a constraint the cited binding does not check.

Why fatal (not merely serious): sub-q2 asks the decision to *choose* an enforcement
mechanism. A's answer ("byte-clamp only, CI gate deferred") means the decision ships
a carrier whose 2k budget — the D5-named acceptance property — has **no token-level
check anywhere that runs in CI**. For a *consumer-shipped* artifact (which A's sub-q5
either does as (b), or breaks as (a) per F1) that is exactly the silent-drift exposure
L-012 warns is paid at the most-compliant downstream consumer (`lessons.md:225,233-237`).
For a *cairn-internal-only prototype* this is tolerable; combined with F1 it is not,
because A cannot actually stay cairn-internal-only.

### F3 — L-012 literal-prose hazard is not just exposed, it is the textbook recurrence: A's realization re-creates the exact line shape that already caused a 4× hard refusal

A discloses this (`phase-2-A:245-255`) and grades it "the strongest case that the
emitted prose matters … the lesson the thin-script approach most needs to answer (and
the draft does not)." I verified the lesson and the carrier text; the match is
near-identical, and the consequence is documented as a *hard failure*, not a
hypothetical:

- L-012 concrete instance: a SessionStart **bash** cheatsheet hook (`role-cheatsheet.sh`)
  fell through to emit `"No active slice — /start-slice to open one"`; a Phase-4
  `opus-4-7 / low` integrator "**refused to proceed, returning FAILED four times in a
  row with the verbatim hook text quoted as its justification**" (`lessons.md:231`).
  L-012's rule: "treat every hook's `additionalContext` output as part of the prompt
  for every agent the hook fires for" (`:235`).
- A's carrier emits, via the *same channel* (a SessionStart `command` hook whose stdout
  Claude Code injects — `using-cairn-carrier.sh:2-4`), the line `"cairn: no active
  intent — run the cairn-intent skill to load or form one."` (`:45`) plus, on resume,
  `"Run the cairn-intent skill to resume."` (`:43`). These are *imperative* lines.

The carrier fires on **every** session including legitimately read-only / Q&A sessions
that D8 explicitly exempts from intent governance (`intent-management-loop.md:97-98`;
phase-0.5-journey Case iii, `:120-145`). A compliant low-tier agent in a D8-exempt
read-only session can read "run the cairn-intent skill to load or form one" as a
directive and derail — the precise tier-sensitive compliance failure L-012 documents.
The byte-clamp and fired-marker do nothing against it (A concedes, `:252-253`).

Fatal *as briefed* because the decision is being made to *unblock #2 and feed Trial E*,
and Trial E runs the loop on real cairn sessions under the per-phase model config (some
low-tier). Shipping a carrier whose no-intent prose is a known-refusal shape into the
dogfood window re-introduces the L-012 footgun into the harness that already lost four
Phase-4 runs to it. The mitigation (neutral, non-imperative, clearly-informational
phrasing; or suppress the line entirely on read-only sessions) is *not in A's draft* —
A leaves it as an open weakness. A decision cannot ratify A's draft as-is without
re-incurring a lesson cairn already paid for.

---

## SERIOUS FLAWS (do not individually sink, but compound)

### S1 — D1 literal non-conformance (sub-q4): ships a bash hook where the firm-for-this-decision ADR wrote "SKILL at dist/skills/.../SKILL.md"

Verified exact: `delivery-mechanism-friction.md:39`. A's own doc calls this "the single
sharpest weakness … a *contract* weakness" (`phase-2-A:148-149,287-289`) and offers a
re-reading ("SessionStart skill" = "the thing that fires at SessionStart"). The
re-reading is *available* but re-interprets a constraint Phase-0 itself tagged "D1 — …
FIRM for this decision" (`phase-0-constraints.md:52`). I down-grade this from A's
"sharpest" to *serious* (not fatal) only because the decision under adjudication is
explicitly empowered to *reconcile* sub-q4 — the brief names "reconcile with D1's
wording" as the question. But note the coupling to F1: the SKILL-file realization D1
literally specifies sits under `dist/skills/` as a directory shipped (or not) as a unit
— the build already shows the pattern (`dist/skills/cairn-tdd-feature/` exists). A
picked the realization that *maximizes* the F1 coupling AND *minimizes* D1 conformance
simultaneously — the wrong corner of the tradeoff space if the decision values either.

### S2 — Stale-intent reproduction (S2/S5/S6 premortem): the carrier does no freshness/version check, and the "robust" unconditional fallback faithfully reproduces a stale pointer

Verified: carrier greps the *last* matching pointer (`using-cairn-carrier.sh:37`
`grep -oE … | tail -n1`) with no TTL, no version tag, and **no read of the handoff
pointer's state token** — INV-002 declares `state ∈ {open, blocked, deferred}`
(`ARCHITECTURE.md:22`), and the carrier's regex ignores it entirely. A concedes S2
EXPOSED (`phase-2-A:224-233`) and correctly notes the skill's unconditional re-derive
*reproduces* a stale handoff rather than fixing it (`:229-230`). The premortem
prescribed the prevention (carrier emits freshness signal, skill ignores stale pointers
— `phase-1-premortem.md:129`); A does not implement it. Serious, not fatal, because
(a) D8 single-operator-per-branch narrows the window and (b) handoff hygiene is the
intended mitigation locus — but the carrier *could* cheaply honor the state token and
does not, so it emits closed-feature pointers verbatim.

### S3 — The fired test is a near-tautology against the real claim (sub-q1 epistemics)

`test_using_cairn_carrier.py:42-63` runs the bash script in a subprocess and asserts
the first stdout line equals the marker. A states this honestly: it tests RENDER, not
host injection (`phase-2-A:33-40`). The serious part: D9's acceptance scope says
"unit-test … the carrier's fired-detection + fallback" (`intent-management-loop.md:100-102`)
and A satisfies the *letter*, but the test proves only "this script, when executed by
bash, echoes a constant string." It cannot fail unless someone deletes the `echo`
(`using-cairn-carrier.sh:33`). It does not prove the marker is *useful* (nothing
consumes `CAIRN_CARRIER_FIRED` — the skill explicitly does NOT branch on it, sub-q3,
`phase-2-A:74-92`), nor that Claude Code injects it. The marker is a test fixture with
no runtime consumer and no host verifier — defensible for a prototype, but not the
"testable fired definition" D5 implies (one that proves the carrier *did its job*).

### S4 — Fallback is an L-005-class prose commitment with no mechanical backstop

A discloses (`phase-2-A:100-106`): the fallback ("Step 1 runs unconditionally") is a
SKILL-body prose side-effect, and L-005 (`phase-0-constraints.md:148-152`) says exactly
these execute inconsistently under context pressure. The conformance test greps the
prose is *present*, not *honored*. The whole safety argument for A ("the skill never
trusts the carrier, so the carrier can never strand it") rests on a prose commitment
L-005 flags as unreliable — and sub-q3 deliberately uses *no* marker detection
(`phase-2-A:74-92`), so there is no second line of defense if the prose isn't honored.

---

## What survives

A's genuine strengths are real and verified: lowest *technical* blast radius, zero new
Python module (honest-minimal — confirmed, `close-review.md:154-159`; bash + stdlib
only), mechanically reversible, and the cleanest in-repo render test (the same `echo`
is inject-surface and assert-surface). As a **cairn-internal prototype wired only into
cairn-the-repo's own session config (NOT the shipped hooks-template.json) for Trial-E
dogfood**, A survives — that is the honest scope where its strengths hold and F1 does
not bite.

But the approach **as briefed** — bash hook registered in the *shipped*
`hooks-template.json`, with distribution "cairn-internal only until Trial E" — does not
survive: F1 makes that posture mechanically impossible (dangling consumer hook or full
distribution, no third option under the build), F2 leaves the D5 2k budget unchecked in
CI, and F3 re-ships a documented hard-refusal prose shape into the dogfood window. Each
is independently disqualifying for the consumer-distribution and D1-conformance halves
of the decision.

## Verdict

**survives = false** for the approach as briefed (consumer-distribution posture +
realization + sub-q5 answer). It survives only in the narrower, *unstated* scope of a
cairn-the-repo-internal prototype wired via local settings, not via the shipped
template — which is not the design A documents. The fatal flaw that most cleanly sinks
it is F1: A cannot deliver its own "cairn-internal only" sub-q5 answer under the bash-
hook-in-shared-template realization it selects, because `build_dist.py:31` ships the
template wholesale and the build has no block-strip mechanism.

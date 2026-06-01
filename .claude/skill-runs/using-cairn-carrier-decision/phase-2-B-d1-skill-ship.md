---
decision: using-cairn-carrier-contract
phase: 2-approach-B
approach: B-d1-skill-ship (D1-literal SKILL, ship-now)
date: 2026-06-01
status: pressure-tested, not advocated
---

# Phase 2 — Approach B: D1-LITERAL SKILL, SHIP-NOW

**Posture brief:** Carrier = a `using-cairn` SessionStart SKILL file (most faithful to
`delivery-mechanism-friction` D1's literal wording); budget = a CI tokenizer gate (D6 shape)
measuring the real tokenized payload, no runtime truncation; fallback = `cairn-intent` Step 1
unconditional; distribution = ship to consumers via `build_dist` NOW (full D5 distribution).
This is the widest-blast-radius, most-D1/D5-faithful option. I design it concretely and then
state honestly where it is weak. I do not advocate.

---

## The reconciliation fact this approach must confront first

`delivery-mechanism-friction.md:39` (D1) says verbatim: *"Ship `using-cairn` SessionStart skill
at `dist/skills/using-cairn/SKILL.md`, registered via `dist/hooks/hooks.json`."* The brief asks
this approach to be D1-literal: the SKILL *is* the carrier.

But Claude Code's SessionStart hook schema does not have a "SKILL injector" hook type. The two
live precedents on this machine register SessionStart as a `type: command` script that emits to
stdout:

- superpowers (`~/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/hooks/hooks.json`):
  `SessionStart → matcher "startup|clear|compact" → type: command → "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start`.
- warp (`.../claude-code-warp/warp/2.1.0/hooks/hooks.json`):
  `SessionStart → matcher "startup|resume" → type: command → ${CLAUDE_PLUGIN_ROOT}/scripts/on-session-start.sh`.

The cairn canonical template (`.claude-plugin/hooks-template.json`) only ever uses
`type: command`. There is no `type: skill` registration anywhere in the corpus.

**Consequence for "D1-literal SKILL":** A SKILL.md cannot *itself* be the thing `hooks.json`
registers and fires at SessionStart. The honest D1-literal realization is: the SKILL.md at
`dist/skills/using-cairn/SKILL.md` is the **authored carrier surface** (the prose D1 enumerates:
substrate description, command name-list, dispatch entry point, envelope paragraph, gate paragraph,
pointers), and a thin `type: command` SessionStart emitter renders/points to it. There are two
sub-shapes:

- **B1 (purist):** the emitter `cat`s the SKILL.md body (or a budgeted slice of it) to stdout at
  SessionStart, so the SKILL *content* is what gets injected. The SKILL is the literal payload;
  the command hook is a dumb pipe. This is the most D1-faithful reading.
- **B2 (pragmatic):** the emitter is the #2-draft `using-cairn-carrier.sh` (computes the active-intent
  pointer dynamically), and the SKILL.md is the static narrative the dynamic emitter's pointers
  resolve to. This collapses toward the #2 draft and toward Approach D's bash-emitter.

This approach (B) takes **B1** to stay honestly distinct from the #2 draft: the SKILL body is the
injected payload. That is the price of D1-literalism — and it is precisely where B is weakest
(see premortem S2, below: a static SKILL body cannot compute "which intent is active *now*").

---

## Answers to the five coupled sub-questions

### (1) Testable "fired" definition

**Fired = the SessionStart command emitter, on session open, writes the `using-cairn` SKILL body
(or a budgeted prefix of it) to stdout, the first line of which is a machine marker
`CAIRN_CARRIER_FIRED`, followed by the carrier's pointer block (substrate one-liner, command
name-list, `cairn-intent` dispatch entry point, envelope/gate paragraphs, Tier-2 pointers) —
all sourced from `dist/skills/using-cairn/SKILL.md`.**

What the unit test asserts (in-repo, RENDER not host-injection — the same honesty the #2 draft's
open-decision (a) records at `close-review.md:138-141`):
- the emitter exits 0 and its stdout first line is `CAIRN_CARRIER_FIRED`;
- the emitted body is a deterministic function of `dist/skills/using-cairn/SKILL.md` (B1: the body
  IS the SKILL body, so the test asserts `emitted == budgeted(SKILL.md)`);
- a no-intent session still fires (marker present) — but B1's static SKILL cannot itself carry a
  *dynamic* intent pointer, so "fired" here means "the orientation payload was injected," NOT "the
  correct active-intent pointer was injected." This is a real semantic narrowing of D5's "emits the
  intent pointer or a no-intent signal" (`intent-management-loop.md:79-81`) — see constraint_fit and S2.

Test file `tests/unit/test_using_cairn_carrier.py` (the #2 draft already has 8 passing carrier tests
for the bash-emitter shape; under B1 the pointer-shape assertions weaken to body-equals-SKILL
assertions, which is *less* informative than the #2 draft's dynamic-pointer assertions).

**Honest weakness:** D5 wants the carrier to emit *the intent pointer or a no-intent signal*. A
static SKILL body (B1) emits orientation, not a computed pointer. To recover D5's dynamic pointer
under a "SKILL is the payload" reading you must either (a) drop to B2 (a dynamic emitter — the #2
draft / Approach D, not D1-literal), or (b) accept that the SessionStart payload is generic
orientation and the *actual* active-intent resolution moves entirely into `cairn-intent` Step 1.
Option (b) makes the carrier strictly weaker than D5 specifies — it fires, but it does not point.

### (2) ≤2k-token budget enforcement — CI tokenizer gate only

A CI workflow (`sessionstart-budget.yml`, or a step in `dist-gate.yml`) tokenizes
`dist/skills/using-cairn/SKILL.md` (the literal carrier payload under B1) with a real tokenizer and
fails the build if it exceeds `CAIRN_SESSIONSTART_BUDGET` (default 2000, env-overridable per
CLAUDE.md no-hardcoded-sizes). **No runtime truncation** — D6 (`delivery-mechanism-friction.md:70-72`)
specifies a *CI* check, and runtime truncation of a SKILL body would corrupt the pointer payload
mid-sentence. Cleanest fit to D6's literal shape: D6 names "a CI token-budget check on the
`using-cairn` SessionStart payload."

**Tokenizer-dependency tension:** A *real* tokenizer is a new dependency (e.g. `tiktoken`, or an
Anthropic count-tokens call), which collides with CLAUDE.md's standing-dep set (pydantic/typer/pyyaml)
and `intent-management-loop` D6 (`intent-management-loop.md:83-85`, "Deps stay pydantic/typer/pyyaml").
Resolutions, none free:
- run the tokenizer **only in CI** (not shipped to consumers, not in `pyproject` standing deps) — a
  CI-only dev tool, arguably outside the standing-dep constraint, but still a new tool to install/pin;
- use an Anthropic API `count_tokens` call in CI — network dependency + auth in CI, heavier;
- fall back to a char/word proxy — but then it is no longer a *tokenizer* gate, it is the #2 draft's
  byte-proxy clamp (open-decision (b), `close-review.md:142-145`), i.e. Approach D's budget shape, not B's.
The brief assigns B "a CI tokenizer gate measuring real tokenized payload" — so B owns the
new-CI-tool cost honestly. Heavier than the #2 in-hook byte clamp; B's named cost.

**No runtime guard:** Because the budget is CI-only with no in-hook clamp, a *consumer's* pinned copy
can silently exceed 2k if the CI gate was bypassed or the consumer's tokenizer differs — Phase-1 S3
(silent budget drift on consumers) is only partially closed (CI catches it cairn-side at build; the
consumer who never re-runs cairn CI has no runtime backstop). See premortem_exposure.

### (3) Fallback contract — `cairn-intent` Step 1 unconditional, skill never branches

Identical to the #2 draft's open-decision (c) default (`close-review.md:146-149`, `intent.md:238-251`)
and to the Phase-0.5 journey's resolved fallback (`phase-0.5-journey.md:311-321`): the `cairn-intent`
skill's Step 1 (`load-or-form-intent`, `workflows/cairn-intent.yaml:16-65`) runs **unconditionally**.
The skill does **not** branch on "did the carrier fire?" It always reads `.claude/handoff.md` +
`.claude/skill-runs/<feature>/intent.md` and classifies new / material-change / resume. If the carrier
fired, the pointer is already in context and Step 1 confirms it; if it did not fire (non-Claude-Code
host, R3, `intent-management-loop.md:148`), Step 1 is the sole path and nothing is lost but the saved
first prompt.

**How the skill detects non-firing:** it does not need to. Non-branching is the safety property — it is
exactly the prevention property the Phase-1 premortem names for S2/S5/S6 (stale-load is the *fatal*
failure mode the ADR's own pre-mortem found for the rejected "approve every session" design,
`intent-management-loop.md:38-40`). Under B1 this matters *more*: because B1's SKILL body is static
orientation (not a computed pointer), Step 1's unconditional load/form is the **only** place the
*actual* active intent gets resolved. The fallback is not a fallback here — it is the primary
intent-resolution path, and the carrier is pure orientation. Coherent and safe, but it means the
carrier delivers less than D5 promised (it orients; it does not point).

### (4) Realization — SessionStart command emitter rendering the SKILL, SKILL.md as the payload surface

- `dist/skills/using-cairn/SKILL.md` is the authored carrier payload (D1's enumerated content),
  shipped via `build_dist` to `skills/using-cairn/` (the #2 allowlist patch already lists
  `(".claude/skills/using-cairn", "skills/using-cairn")`, `build_dist-allowlist.patch.md:11`).
- A `type: command` SessionStart hook in `hooks-template.json` (the #2 draft already registers a
  `SessionStart → type: command → ${CLAUDE_PLUGIN_ROOT}/checks/using-cairn-carrier.sh` entry,
  `proposed/hooks-template.json:3-12`) runs the emitter. Under B1 the emitter is a *thin* renderer
  that cats the budgeted SKILL body + prepends `CAIRN_CARRIER_FIRED`.
- **No new Python module** (honest-minimal, CLAUDE.md / `intent.md:108-109`): the emitter is a bash
  hook in the surviving-guard family (`checks/*.sh`), consistent with `reversibility-guard.sh` /
  `reality-check.sh`. **No new hook *type*** beyond `type: command` — D6's "no new hooks" is read as
  "no new *guard* hooks (premise/role/atomicity)"; a SessionStart `command` entry is the same
  mechanism superpowers/warp use and is not a fourth guard. This is the (2)-vs-(4) tension the Phase-0
  envelope flags at `phase-0-constraints.md:163-167`, resolved toward: a SKILL-file payload + a
  `command` emitter is not the disallowed "fourth guard hook."

**The D1-literal cost:** B1 forces the emitter to be dumb (cat the SKILL) to keep the SKILL as "the
carrier." The moment the emitter computes the active-intent pointer dynamically, the SKILL stops being
the payload and you are in B2 = the #2 draft = Approach D. So D1-literalism and D5's dynamic-pointer
pull in opposite directions; B resolves it by keeping the SKILL literal and demoting the pointer to
Step 1. Structural weakness of being maximally D1-faithful.

### (5) Distribution scope — ship to consumers via build_dist NOW (full D5)

Append to `scripts/build_dist.py` `ALLOW_LIST` now (`build_dist-allowlist.patch.md:9-15`):
`skills/cairn-intent`, `skills/using-cairn`, `agents/intent-challenge.md`, `agents/intent-review.md`,
`checks/using-cairn-carrier.sh`. The carrier ships to every consumer on the next `release`-branch
build (INV-012, `ARCHITECTURE.md:87-93`). Consumers get the carrier firing on every session.

**Maximal-blast-radius choice and B's defining bet.** Faithful to D5's distribution intent
(`intent-management-loop.md:77-81` builds the carrier as a shipped artifact) but ships a *provisional*
carrier (the ADR is provisional, `intent-management-loop.md:18-20`) before Trial E has passed (D7,
`intent-management-loop.md:87-93`) and before the D7 retirement ADR exists. Every consumer session
pays the carrier's blast radius (R1 stale-`.slice-system`, R3 non-CC-host non-firing) from day one,
for a mechanism the ADR itself marks as a *trial*.

---

## constraint_fit (against the Phase-0 envelope)

| Constraint (envelope citation) | B's fit |
|---|---|
| INV-004 ≤2k carrier budget (`phase-0-constraints.md:11`, D1 `delivery-mechanism-friction.md:39`) | **Met cairn-side, CI-enforced**; no runtime backstop on consumers (partial). |
| D5 "emits the intent pointer or a no-intent signal" (`phase-0-constraints.md:79-83`) | **Violated in spirit under B1** — static SKILL body orients, does not emit a computed pointer; pointer moves to Step 1. B's biggest constraint friction. |
| D5 testable "fired" (`phase-0-constraints.md:79-83`, D9 `intent-management-loop.md:100-104`) | Met as RENDER test (host-injection stays a Trial-E observation, honest per `close-review.md:138-141`). |
| D6 no-new-hooks / standing deps (`phase-0-constraints.md:85-88`, `intent-management-loop.md:83-85`) | **`command` emitter = no new guard hook (OK)**; but the **CI tokenizer is a new dev tool** in tension with pydantic/typer/pyyaml — B's named dep cost. |
| D1 "SessionStart skill at dist/skills/using-cairn/SKILL.md" (`delivery-mechanism-friction.md:39`) | **Most faithful of all approaches** — the SKILL is the literal payload surface. B's whole reason to exist. |
| D6 CI token-budget check (`delivery-mechanism-friction.md:70-72`) | **Most faithful** — exactly the CI check D6 names, with a real tokenizer. |
| No-hardcoded-sizes / env-override (`phase-0-constraints.md:131`, CLAUDE.md) | Met — `CAIRN_SESSIONSTART_BUDGET` default 2000. |
| Honest-minimal, no module w/o caller (`intent.md:108-109`) | Met — bash emitter, no new Python module. |
| INV-012 release-branch distribution (`phase-0-constraints.md:35-43`) | Met mechanically — but ships a provisional carrier pre-Trial-E. |
| D7 retirement gated on Trial E (`phase-0-constraints.md:90-94`) | **Tension** — B ships full consumer distribution *before* the D7 gate; D5 permits provisional distribution but D7 + R1 raise the cost of doing it now. |

Net: B is **maximally faithful to the two D1 wordings and to D6**, and **least faithful to D5's
dynamic-pointer clause** (static-SKILL-as-payload guts the computed pointer). It also carries the
new-CI-tokenizer dep cost and the full pre-Trial-E consumer blast radius.

## premortem_exposure (against `phase-1-premortem.md`)

**Exposed to:**
- **S1 (non-firing on non-CC host, `phase-1-premortem.md:21-29`)** — fully exposed, same as all
  approaches; mitigated only by the unconditional Step-1 fallback (3). B ships this to *all* consumers
  now, so the non-firing surface is the widest. R3 (`intent-management-loop.md:148`).
- **S2 (stale-intent poisoning, `:34-47`)** — *less* exposed one way, *more* another. Less: B1's
  static SKILL cannot emit a stale *computed* pointer (no dynamic pointer to get wrong). More: a
  static SKILL body that names a path inline drifts silently across branches/sessions, and because
  the real intent resolves only in Step 1, poisoning is pushed to whatever Step 1 loads from a
  possibly-stale `.slice-system` (S5, `:86-94`).
- **S3 (budget drift on consumers, `:52-66`)** — partially exposed. CI tokenizer catches drift
  cairn-side at build; a consumer pinned to an old release whose CI never re-ran has **no runtime
  backstop** (B chose CI-only, no in-hook clamp). The #2 byte-clamp (Approach D) closes this at
  emit-time; B does not.
- **S5 (fallback on stale `.slice-system`, `:86-94`)** — exposed; B ships to consumers now, so the
  stale-symlink + deprecated-schema surface is live on every consumer from day one, earlier than a
  cairn-internal-first approach would expose it.

**NOT (or less) exposed to:**
- **S2 dynamic-pointer mis-emit** — B1 has no dynamic pointer to emit wrong (static), so the specific
  "carrier emits Feature-A's intent into Feature-B's session" path (`:37-39`) is closed at the carrier;
  it reappears only via Step 1 (S5).
- **S4 (premise_guard `.slice-system` traversal, `:70-82`)** — orthogonal to the carrier choice; B
  neither worsens nor fixes it (it is `premise_guard.py`'s problem, not the carrier's).
- **S6 (pointer file deleted at cleanup, `:107-113`)** — under B1 the carrier emits no file pointer,
  so "carrier points at a deleted intent.md" is closed at the carrier; reappears via Step 1.

## downstream_impact

- **Consumers:** every consumer session runs the carrier from the next release. Widest blast radius of
  any approach. R1 (stale `.slice-system`, `intent-management-loop.md:146`) and R3 (non-CC host) live
  on all consumers immediately, for a *provisional* trial mechanism. Reversal is mechanical (one SKILL
  + one hooks.json entry + allowlist rows, `delivery-mechanism-friction.md:94-95`), but it is
  reversal-on-every-consumer, gated on the fragile `marketplace remove + re-add` update path (INV-012,
  `ARCHITECTURE.md:87`).
- **Codex plugin:** the Codex `using-cairn` SKILL (`plugins/cairn/skills/using-cairn/SKILL.md`) is a
  *chooser*, not a SessionStart carrier (Codex has no SessionStart hook — `cairn-intent.yaml:298-300`
  notes "hook registration is not available in plugin.json for this slice"). B's Claude-side carrier
  does not change the Codex surface; the two `using-cairn` SKILLs diverge in role (Codex = chooser,
  Claude = injected carrier payload). B must keep them reconciled in *naming* (same workflows) while
  honest that only the Claude one fires at SessionStart.
- **Trial E:** B ships the carrier to consumers *before* Trial E passes, front-loading the trial's
  blast radius onto third parties — arguably contaminating Trial E (consumers experiencing a
  not-yet-validated carrier) rather than letting cairn dogfood it internally first. The Trial-E pass
  condition (`intent-management-loop.md:88-93`) is about cairn's own increment + felt cost; B's
  ship-now does not help that condition and adds external exposure that a cairn-internal-first
  approach avoids.
- **D7 retirement:** B's distribution is *not* the firm D7 distribution — it ships the provisional
  carrier under D5's provisional license, ahead of the firm retirement ADR. If Trial E *fails*
  (`intent-management-loop.md:93`, "the pipeline stays"), B has already shipped a carrier for a loop
  whose retirement was rejected — a sticky consumer artifact to walk back.

---

## Honest summary (no advocacy)

B is the right answer **if the operator values literal fidelity to the two D1 wordings and D6's
CI-check over D5's dynamic-pointer semantics and over minimizing pre-Trial-E consumer exposure.** Its
strengths are real: most D1-faithful, uses exactly D6's CI gate, mechanically clean distribution.

Its three honest weaknesses:
1. **D1-literalism guts the pointer.** Claude Code has no SessionStart-SKILL hook type; making the
   SKILL "the carrier" (B1) forces a dumb cat-the-SKILL emitter that cannot compute the active-intent
   pointer D5 asks for, demoting the pointer to `cairn-intent` Step 1. The moment you let the emitter
   compute the pointer, you are in the #2 draft / Approach D, not D1-literal. B cannot be both
   D1-literal *and* D5-dynamic-pointer at once.
2. **New CI tokenizer dep.** The "real tokenized payload" gate needs a tokenizer not in the standing-dep
   set; the #2 byte-proxy avoids this. B owns that cost and has no runtime backstop, so S3 (consumer
   budget drift) is only partially closed.
3. **Maximal pre-Trial-E blast radius.** Shipping a provisional trial carrier to all consumers now
   front-loads R1/R3 onto third parties and risks contaminating (or having to walk back) Trial E if the
   loop's retirement is later rejected.

If those costs are acceptable, B is coherent and the most spec-literal option. If the operator weights
D5's pointer semantics, dep-minimalism, or Trial-E containment higher, a cairn-internal-first or
dynamic-emitter approach dominates B on exactly those axes.

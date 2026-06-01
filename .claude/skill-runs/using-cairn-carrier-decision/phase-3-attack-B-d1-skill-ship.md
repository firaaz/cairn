---
decision: using-cairn-carrier-contract
phase: 3-adversarial
approach: B-d1-skill-ship (D1-literal SKILL, ship-now)
date: 2026-06-01
verdict: survives=false
---

# Phase 3 — Adversarial stress test of Approach B (D1-literal SKILL, ship-now)

Disconfirming posture. I tried to break B against live source. Two fatal flaws stand;
B does not survive as written. The flaws are not fixable inside B's defining bets
(B1-SKILL-as-payload + ship-now) — fixing either collapses B into Approach A/D or into a
defer posture. Each claim below is verified-vs-believed against the file I read.

---

## Load-bearing-assumption audit (verified vs believed)

| # | B's load-bearing claim | Status | Evidence |
|---|---|---|---|
| 1 | "INV-004 ≤2k carrier budget … Met cairn-side, CI-enforced" (`phase-2-B:179`) | **FALSE** | INV-004's binding `tests/unit/test_context_budget.py` is a **live `claude -p hi` turn-1 measurement asserting ≤40k** (`:18,108-119`), **skipped without the CLI** (`:107`). It tokenizes **no file** and has **zero** carrier-2k assertion. The ≤2k figure is a `delivery-mechanism-friction.md:39` (D1) number with **no machine binding**. B claims a CI enforcement that does not exist and a budget binding INV-004 does not contain. |
| 2 | B1 = "the SKILL *content* is what gets injected … the SKILL is the literal payload" (`phase-2-B:46-47`) | **FABRICATED vs artifacts** | Every shipped artifact does the opposite. The carrier `using-cairn-carrier.sh:36-46` **dynamically greps `.claude/handoff.md`** for an intent pointer and emits it. `SKILL-using-cairn.md:16` describes a **dynamic** pointer ("If an active intent exists … emit a one-block pointer"). `proposed/hooks-template.json:8` registers the `.sh`, not a SKILL-cat. The test `test_using_cairn_carrier.py:80-91` asserts the `.sh`'s **dynamic resume behavior**. B's "cat the SKILL body" emitter is **unbuilt and contradicted** by the artifacts it inherits. |
| 3 | "Claude Code's SessionStart … has no SKILL injector hook type; precedents use `type: command`" (`phase-2-B:28-36`) | **TRUE** | `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/hooks/hooks.json:3-12` is `SessionStart → matcher "startup\|clear\|compact" → type: command`. Cairn's `.claude-plugin/hooks-template.json` is all `type: command`. B's *premise* is correct — which is exactly what guts B's own D1-literalism (flaw FATAL-1). |
| 4 | "CI tokenizer gate measuring real tokenized payload" is a new dep in tension with standing set (`phase-2-B:99-109`) | **TRUE and worse than stated** | `pyproject.toml` deps = `pyyaml, pydantic, typer` only; **no tokenizer anywhere** (`grep` clean). `dist-gate.yml` has **no token-budget step** (checkout→uv sync→build→allowlist pytest→postinstall). B's D6 gate is net-new infra + a dep that `intent-management-loop.md:85` ("Deps stay pydantic/typer/pyyaml") and CLAUDE.md forbid. |
| 5 | D5 "emits the intent pointer or a no-intent signal" is satisfiable under B1 (`phase-2-B:75-87`) | **FALSE — B concedes it** | `intent-management-loop.md:79-81` verbatim: carrier "emits the intent pointer or a no-intent signal." B1's static SKILL body "fires but does not point" — B's own constraint_fit row marks D5 **"Violated in spirit under B1"** (`phase-2-B:180`). A static SKILL cannot compute "which intent is active *now*." |
| 6 | "ship to consumers via build_dist NOW" is mechanically clean (`phase-2-B:159-164`) | **FALSE — breaks the build** | The allowlist patch adds `("...intent-review.md", "agents/intent-review.md")` (`build_dist-allowlist.patch.md:13`). `build_dist._copy_pair` **raises `FileNotFoundError` on a missing source** (`build_dist.py:45-46`). Increment #1's `intent-review.md` is not in this branch's allowlist; close-review F2 (`close-review.md:105-115`) already flags the landing-order coupling. Ship-now *now* reds the build. |
| 7 | "fired" RENDER test "proves" the carrier fired (`phase-2-B:60-80`) | **BELIEVED, not proven** | `test_using_cairn_carrier.py:59-108` runs `bash using-cairn-carrier.sh` in a subprocess and asserts the first stdout line is `CAIRN_CARRIER_FIRED`. This proves **a script runs and prints a string** — it does **not** prove Claude Code injects at SessionStart on any host. The #2 close-review states this honestly (`close-review.md:138-141`: "tests the carrier's RENDER, not that Claude Code actually injects"). Under B1 it is weaker still: the test would assert `emitted == budgeted(SKILL.md)` (`phase-2-B:72`), i.e. that `cat` works. |
| 8 | "`command` emitter = no new guard hook (OK)" vs D6 no-new-hooks (`phase-2-B:147-151,182`) | **DEFENSIBLE** | `intent-management-loop.md:83-85` D6 names the three *guard* hooks (premise/role/atomicity). A SessionStart `type: command` entry is the superpowers/warp mechanism (verified, claim 3), not a fourth guard. This reading survives — it is *not* one of B's fatal flaws. Recorded so the verdict is not inflated. |

---

## FATAL FLAWS (each independently sinks B as written)

### FATAL-1 — B1 cannot satisfy D5's "emits the intent pointer"; the carrier fires but does not point

D5 is verbatim (`intent-management-loop.md:79-81`): the carrier "emits **the intent pointer**
or a no-intent signal within the ≤2k-token budget." B's defining bet is B1 = the static
`SKILL.md` body *is* the injected payload (`phase-2-B:46-47`). A static SKILL body cannot
compute the active intent for the current branch/session — B says so itself
(`phase-2-B:54`: "a static SKILL body cannot compute 'which intent is active *now*'";
`:180`: D5 "**Violated in spirit under B1**"; `:256-260`: "D1-literalism guts the pointer").

This is not a tunable parameter. The moment the emitter computes the pointer dynamically
(to satisfy D5), the SKILL stops being the payload and B **collapses into B2 = the #2 draft
= Approach D** (B's own admission, `phase-2-B:155-157`). So B's choice is binary: be
D1-literal and **fail D5**, or satisfy D5 and **stop being B**. Either branch eliminates B.

Disconfirming check: I read `SKILL-using-cairn.md` to see whether the SKILL could carry a
static-but-sufficient pointer. It cannot — `:16` itself specifies a **dynamic** emission
("If an active intent exists … emit a one-block pointer: the intent path, its one-line scope
… and its `delta_kind`"). The only artifact that produces this is the dynamic `.sh`, which
is the not-B realization. **B1 has no artifact that satisfies D5. Fatal.**

### FATAL-2 — B's central enforcement and budget claims are unbacked by live source

B's constraint_fit asserts "INV-004 ≤2k carrier budget — **Met cairn-side, CI-enforced**"
(`phase-2-B:179`) and "D6 CI token-budget check — **Most faithful** … with a real tokenizer"
(`:184`). Both are false against the repo *today*:

- INV-004's only binding (`tests/unit/test_context_budget.py`) measures a **live ≤40k
  session** (`:18,108-119`), is **skipped without the `claude` CLI** (`:107`), and contains
  **no ≤2k carrier assertion of any kind**. There is no machine-checked 2k budget to "meet."
- The CI gate B leans on **does not exist**: `dist-gate.yml` has no token step
  (checkout → uv sync → build → allowlist pytest → postinstall). A real tokenizer is **not
  in the dep set** and is **forbidden** by `intent-management-loop.md:85` + CLAUDE.md. B owns
  "the new-CI-tool cost honestly" (`phase-2-B:109`) — but a *new forbidden dep* is not an
  honest in-scope cost; it is an infra commitment the ADR's no-new-deps clause rejects.

So B's two "most faithful" selling points (CI-enforced 2k, D6 tokenizer gate) are a
**believed mechanism with no live backing** plus a **dep the governing ADR forbids**. The
only budget enforcement that actually exists in the artifacts is the **byte-clamp** in the
`.sh` (`using-cairn-carrier.sh:18,29` — `CAIRN_CARRIER_BUDGET_BYTES` default 8000) — which is
**Approach D's mechanism, not B's**. Strip the fiction and B's distinguishing budget posture
is unbuilt and partly illegal; what remains *is* Approach D. **Fatal as a distinct approach.**

---

## SERIOUS FLAWS

### SERIOUS-1 — Ship-now reds the build (FileNotFoundError) and front-loads provisional blast radius

Distribution = "build_dist NOW" (`phase-2-B:159-164`). Two problems verified:

1. **Build break.** The allowlist patch row `agents/intent-review.md`
   (`build_dist-allowlist.patch.md:13`) has no source on this branch;
   `build_dist._copy_pair` raises `FileNotFoundError` on a missing source
   (`build_dist.py:45-46`). Shipping now without increment #1's persona landing first reds
   `build_dist` (close-review F2, `close-review.md:105-115`). `test_build_dist.py:113` is a
   presence-subset and won't catch it — the **build itself** throws first.
2. **Provisional blast radius, pre-Trial-E.** `intent-management-loop.md` is **provisional**
   (`:6,18-20`); D7 gates retirement on Trial E (`:87-93`), and Trial E hasn't run. R1
   (stale `.slice-system`, `:146`) + R3 (non-CC-host non-firing, `:148`) go live on **every
   consumer session** (`hooks-template.json` ships as `hooks/hooks.json`, `build_dist.py:31`)
   for a mechanism the ADR marks a *trial*. If Trial E fails (`:93` "the pipeline stays"),
   B has shipped a carrier for a rejected loop — a sticky consumer artifact behind the
   fragile `marketplace remove + re-add` update path (INV-012, `ARCHITECTURE.md:87`).

D5 *permits* provisional distribution, but nothing *requires* shipping pre-Trial-E, and
doing so contaminates the trial (consumers experience an unvalidated carrier) while buying
**nothing** for the Trial-E pass condition (`:88-93` is about cairn's *own* increment + felt
cost). Serious, not fatal: the build break is fixable by sequencing #1 first, and the
blast-radius is a chosen cost — but it is strictly dominated by a cairn-internal-first ship.

### SERIOUS-2 — The "fired" test proves a script runs, not that the carrier fired on a host

Verified (audit row 7): `test_using_cairn_carrier.py` is a subprocess RENDER test. It cannot
observe real SessionStart injection — the #2 close-review concedes this (`close-review.md:138-141`).
Under B1 it degrades to asserting `cat` reproduces the SKILL body. So B's D9 "testable fired
+ fallback" (`intent-management-loop.md:100-104`) is met only as a render shape; the real
"fired on host" claim remains a Trial-E observation. This is honest in the #2 draft, but B
**inherits the #2 test wholesale** (`phase-2-B:78-80`) while asserting a *stronger* B1
body-equals-SKILL contract the inherited test does not check. Test and stated contract are
misaligned.

### SERIOUS-3 — D2 superpowers-composition is specified in prose, untested, unbuilt — and its own ADR makes it a ship-blocker

`delivery-mechanism-friction.md:43` makes the superpowers-composition integration test an
**F3 audit acceptance gate** ("the slice does not ship without it passing"). `SKILL-using-cairn.md:20-22`
describes the probe in prose, but the dynamic `.sh` does **no** superpowers probe and **no
test asserts non-double-load**. Under B1's static SKILL the probe cannot execute at all. B
ships to consumers (Serious-1) **without** the D2 gate its governing ADR makes a hard
blocker. L-005 (`phase-0-constraints.md:148-151`): prose-specified side-effects execute
inconsistently — exactly this gap.

---

## What survives (so the verdict is not inflated)

- **Audit row 3** (no SessionStart-SKILL hook type; `type: command` precedent) — TRUE, verified.
- **Audit row 8** (a SessionStart `command` entry is not a fourth *guard* hook; D6-compatible) — DEFENSIBLE.
- **Fallback contract (sub-q 3)** — B's "Step 1 unconditional, skill never branches"
  (`phase-2-B:116-134`) is sound and matches `phase-0.5-journey.md:311-321` + the ADR
  pre-mortem's anti-stale-load finding (`intent-management-loop.md:38-40`). This is B's one
  genuinely robust answer — but it is **identical across A/B/C**, so it neither differentiates
  nor rescues B.

The fallback being correct does not save B: B's *distinguishing* bets (B1-SKILL-as-payload,
CI-tokenizer budget, ship-now) are precisely the parts that fail.

---

## Verdict

**survives = false.** B is refuted on its two defining bets:

1. **FATAL-1**: B1 (SKILL-as-payload) **structurally cannot emit D5's intent pointer** — it
   "fires but does not point," by B's own admission and confirmed against the artifacts. To
   satisfy D5, B must become the dynamic #2-draft/Approach-D, ceasing to be B.
2. **FATAL-2**: B's "CI-enforced 2k / D6 tokenizer gate" is **unbacked by live source** (no
   2k binding in INV-004's test; no CI token step; tokenizer dep forbidden). Strip the
   fiction and B's only real budget mechanism is Approach D's byte-clamp.

Net: B is not a distinct, shippable approach. It is either **D1-literal-and-D5-broken** (fires
but points at nothing) or **D5-correct-by-becoming-Approach-D** (dynamic emitter + byte-clamp).
Plus three serious flaws (build-reds-on-ship, render-test overclaim, untested D2 ship-blocker).
The honest move: keep B's one good part (the unconditional Step-1 fallback, shared with all
approaches) and otherwise prefer the dynamic-emitter realization with a byte-clamp +
cairn-internal-first distribution — i.e. *not B*.

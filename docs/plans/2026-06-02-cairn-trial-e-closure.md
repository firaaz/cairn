# Trial-E closure — what remains and how it ends

**Status:** spec (brainstorm output). Not a commitment to enforcement — it specifies the
remaining *measurement* and the *adjudication arcs* that consume it.
**Date:** 2026-06-02.
**Supersedes nothing.** Companion to `docs/plans/2026-05-20-cairn-thin-substrate-trials.md`
(Trial E = that plan's "Trial 3").

## Cross-references

- `docs/plans/2026-05-20-cairn-thin-substrate-trials.md` — Trial 3 definition, gating, pass criteria (`:198`–`:215`).
- `docs/adr/intent-contract-cost-model.md` — D3 deferral + D5 Trial-E gate (the heavy-band bundle).
- `docs/adr/intent-management-loop.md` — D6 (no new hooks), D7/R2 (four-phase retirement gated on Trial E).
- `docs/adr/intent-fidelity-measure-before-enforce.md` — D2 (cross-family instrumentation), B-trigger (`:90`).
- `docs/adr/identity-and-scope-deferral.md` — D3 revisit triggers (`:45`); trigger #4 binds the retirement /decision.
- `docs/operator-field-notes-2026-06-01.md`, `-2026-06-02.md` — dp1–5 verbatim findings.

## 1. Frame

Trial E's job is **measurement for adjudication**: does the formal intent contract plus the
four-phase pipeline buy fidelity/value that the thin intent loop (intent.md + premise-grounding +
envelope + the two fresh-context checkpoints) would not? It is *not* a mandate to build permanent
machinery. Its output is the data three deferred decisions are waiting on.

## 2. State of evidence (dp1–5)

**Measured:**
- Felt cost across 3 live `cairn-intent` dogfoods (dp4 gh#2 fail-closed, dp5 sink) + 2 probes.
- Same-family two-checkpoint **co-miss: 0/3, front-loaded** (dp3). Every planted slice-#25-class
  fidelity defect was caught by at least one checkpoint.
- The **asymmetry finding** (dp3, load-bearing): the front intent-challenge is the strong, reliable
  arm (3/3 defects de-primed); the close-review is a *conditional* backstop — it only catches a
  fidelity defect that propagates into a diff-visible regression (it missed D2, the no-friendly-tell
  case). Fidelity protection in the loop is therefore **front-loaded, not two independent shots.**

**Not measured (the gap that keeps Trial E open):**
- **Cross-family co-miss.** dp3 ran same-family only (de-primed `general-purpose` both arms). The
  Claude-drafts / Codex-challenges datum named at `measure-before-enforce` D2 and the B-trigger
  (`:90`) has not been run.

## 3. What's left

Three work items. Detail concentrates on W1 (the experiment); W3 is named gates with triggers, not
full decision designs (those are the /decision arcs' own work).

### W1 — Cross-family co-miss probe (the experiment)

**Goal:** measure whether a cross-family challenger (Codex) changes the co-miss rate on cairn's
fidelity-leap class relative to the same-family 0/3 baseline.

**Method:** extend the dp3 de-primed harness. Reuse its planted-defect corpus — 3 distinct
slice-#25-class lies in 3 real hooks (D1 path-anchor, D2 misattribution-no-tell, D3
control-flow-consequence) + 2 truthful controls (C1/C2). Hold dp3's mechanical preconditions
(grounded variants → `premise_guard` exit 0; bogus path → exit 1; `CAIRN_PREMISE_FIX` unset).

**Cross-family arm:** Claude drafts the intent; **Codex runs the challenge** via the codex-hook-parity
path —
`render_codex_dispatch_brief(load_workflow('workflows/cairn-intent.yaml'), 'cairn-intent-challenge')` —
with the de-primed charter (production charter minus the slice-#25 example and cairn naming, matching
dp3). Compare Codex's block/pass verdicts against the same blind grader's ground truth, and against
dp3's same-family Arm A.

**Exit (W1 done):** cross-family co-miss rate on the fidelity-leap class recorded in dated field
notes, stated against the same-family 0/3 baseline, with the same anti-over-read caveats dp3 carried
(existence-not-rate; de-primed capability floor, not production-prompt behaviour).

**Degradation:** if Codex is unavailable, record the run as same-family-only per the ADR's recorded
fallback — do **not** silently skip or relabel.

### W2 — Loose-end commit (dp5 sink fix)

The dp5 sink fix (Trial-E close sink: `docs/dogfood-log.md` → dated operator field notes, across the
canonical workflow, plugin workflow mirror, Claude skill, Codex plugin skill, + matching tests) is
**uncommitted in the working tree.** Verify green (focused `cairn-intent` tests + full suite +
validator), then commit. Cheap; do first to clean the tree before the probe.

### W3 — The three adjudication /decision arcs

Each is a **separate** `/decision` (distinct commitment, distinct gate). They may be sequenced in one
closure session but must not be collapsed into a single yes/no — they decide different things:

1. **`cost-model` D3 — heavy-band bundle.** Commit vs retire the derived-banding + agent-declared/
   challenger-attacked severity + front-loaded fidelity-challenge bundle. Gate (D5): does the formal
   proof catch anything a thin prose intent + existing gates would not? Adjudicate on dp1–5 + W1.
2. **`intent-management-loop` D7/R2 — four-phase retirement.** Decide whether to retire the
   four-phase pipeline. **Must engage `identity-and-scope-deferral` D3 trigger #4** (supersession by
   explicit /decision). The dp3 front-loaded finding is the central input: frame any retirement on
   the front-challenge's demonstrated strength, **not** on "two independent decorrelation catches."
3. **`measure-before-enforce` B — cross-family enforcement.** Commit cross-family fidelity
   enforcement **iff** W1 shows the cross-family co-miss delta *materially below* same-family ~60% on
   the fidelity-leap class (the pre-recorded trigger at `:90`). Otherwise record "not triggered" and
   leave the same-family challenger as-is.

## 4. Sequencing and gates

```
W2 (commit sink fix, clean tree)
  └─> W1 (cross-family probe → records the missing datum)
        ├─> D-xfam   (gated *on* W1's co-miss result)
        ├─> D-retire (W1 informs; dp3 finding central) ── engages identity-and-scope-deferral D3.4
        └─> D-cost   (adjudicate on dp1–5 + W1)
```

W1's result is a hard gate for D-xfam and an input for D-retire (does a cross-family arm move the
front-loaded conclusion?). D-cost and D-retire can otherwise proceed on existing + W1 data.

## 5. Out of scope

- **`measure-before-enforce` D1 (baseline capture) + D3 (decoy/recall pilot) instrumentation build.**
  That ADR is accepted but its instrumentation is unbuilt; building it is its own downstream
  initiative, **not** a Trial-E blocker. Trial E closes on the probe + existing dp data, per the
  chosen approach.
- **The enforcement commits themselves.** Those are the *outputs* of the W3 /decisions, not this
  spec's work.
- **New hooks.** `intent-management-loop` D6 stands: any instrument is a skill-step, not a PreToolUse
  hook.

## 6. Exit criteria — "Trial E complete"

1. Cross-family co-miss datum (W1) recorded in dated field notes with caveats.
2. dp5 sink fix committed; tree clean (W2).
3. All three W3 /decisions adjudicated — each either **commits** its bundle or **retires the
   ambition**, with recorded rationale (an explicit "not triggered / retire" is a valid close).
4. ADR status transitions written: `cost-model` D3, `intent-management-loop` D7/R2, and
   `measure-before-enforce` B resolved from "deferred/gated" to their adjudicated state.
5. Trials plan (`2026-05-20-...`) marked Trial 3 = closed with outcome.
6. Handoff Trial-E threads resolved; provisional bits keyed to Trial E
   (`cairn-intent-git-lifecycle` `--no-ff`/`feat/<id>` provisional decisions) confirmed or firmed now
   that the gate has resolved.

## 7. Anti-over-read (carried from the ADRs, recorded not novel)

- The probe **must stay de-primed.** The shipped `intent-challenge`/`intent-review` agents are primed
  (slice-#25 hard-coded), so their blocks are recall-confounded — measure the capability floor.
- **n is existence, not rate.** 0/3 (or any small-n cross-family result) rules out "co-miss is the
  common case" only weakly; it does not establish "co-miss is rare."
- **Do not justify retirement on bracket redundancy.** dp3 showed fidelity is front-loaded; the
  close-review is conditional. Retirement framing rests on the front-challenge's strength.
- **Reject review-time-under-15-min as a success metric** (`measure-before-enforce` D5): fast approval
  is observationally identical to disengagement.

# Approach FREEZE+DISTRIBUTE — Steelman

## Core idea

Pause the trial sequence (RETROFIT, TRIAL-C, TIGHTEN-FIRST). Resume distribution-track work: close the open `delivery-mechanism-friction` impl slice (`gh:firaaz/cairn#33`), execute the Node-20-deadline CI bump (`gh:firaaz/cairn#32`, due 2026-06-02), and let real external use of `cairn-tdd-feature` produce the contract-shape signal a fourth internal trial would only simulate. Success criterion: contract pattern validated by *external consumers exercising it*, not by adding a fourth in-repo trial on a v0.1.0 plugin (`git tag -l` shows v0.1.0 is the only published release) whose update path is documented-fragile (`plugin-payload-transport-a1.md:103-111`). The 4th option exists because Phase 1 cross-branch failure mode #1 named the meta-constraint: "the actual constraint may be 'ship what's stable'" (`03-premortem.md:68`).

## What "freeze" means concretely

- **Trial A: keep landed; no amendments.** Handoff-as-pointer protocol stays as committed at `53a7c58`. The contract block at `.claude/handoff.md:1-12` is enforced by `tests/unit/test_handoff_contract.py` under INV-002 (`docs/ARCHITECTURE.md:23-27`).
- **Trial B: keep closed with the deferred retrofit documented.** Commits `45c31a8` + `a0e3fe6` are the freeze line. The 14-ADR + 6-slice-id deferred audit (`01-constraints.md:31-33`) gets a "deferred" entry in `.claude/handoff.md` (matching the pattern at lines 14-16), trigger "re-open only when an external consumer surfaces legacy-label friction." `LEGACY_LABEL_BASELINE = 10` and `LEGACY_SLICE_ID_BASELINE = 6` stay where Trial B set them.
- **The contract pattern as v1 stable surface.** Trial A handoff contract + Trial B identifier-scheme contract + the existing N≥3 schema-amendment-threshold (`docs/adr/schema-amendment-threshold.md:49-61`) constitute the firm v1 shape. No shape changes — including no TIGHTEN-FIRST amendments — until external use produces signal. Trial B's "might be too strict" verdict was already resolved by the `adr-contract-execution-scope-clause` ADR (commit `801e580`); Phase 1's load-bearing-claim audit confirmed this is targeted, not structural (`03-premortem.md:36-37`).

## What "distribute" looks like

Three concrete first moves, date-pressured order:

1. **`gh:firaaz/cairn#32` — Node-20 CI deprecation deadline 2026-06-02.** 13 calendar days from today. Affects `.github/workflows/release-publish.yml` and `dist-gate.yml`, both pinning `actions/checkout@v4` and `astral-sh/setup-uv@v3` (workflow files verified present). The only naturally time-boxed open thread — it sets the calendar. Missing the date means silent release-publish breakage.

2. **`gh:firaaz/cairn#33` — `delivery-mechanism-friction` impl slice.** ADR accepted but un-shipped (`delivery-mechanism-friction.md:14-17`). D1 ships `using-cairn` SessionStart skill collapsing J1 first-slice friction "from ~20 min to ~3 min" (line 78); D3 ships four `cairn-*` nav agents with substrate pre-flight; D6 adds SessionStart token-budget CI check. Single highest-leverage external-adoption move named anywhere in the corpus — gh:#33's own framing ("could pay for itself the first time a future-self or collaborator picks cairn up on a clean machine") is unambiguous.

3. **F1.1 / post-install validator stdout literal** (`docs/roadmap.md:71`). Explicitly gated on "first real consumer-side `/plugin install` data." Shipping (2) + driving one real external install produces that data, unblocking a gate open since M5.

Concrete deliverable: a versioned `v0.2.0` release (bumped per `m5-plugin-deployment-pattern/D3`) carrying SessionStart skill + four nav agents + Node-24 workflow pin + the F3-check-9-PASS state at `3df4a53`. `marketplace.json` sha-pin bumped per `plugin-payload-transport-a1/D3`. CONSUMER.md gains the "Updating" section D6 deferred (`plugin-payload-transport-a1.md:113`).

## Self-administered pre-mortem (≥3 failure scenarios)

1. **Technical/integration failure — A1 update fragility strands consumers on v0.1.0.** `plugin-payload-transport-a1/D5` documents `/plugin update` does NOT refresh the marketplace cache; manual `remove + re-add` per release. If v0.2.0 ships without loudly surfacing the manual-update procedure in CONSUMER.md, consumers silently stay on v0.1.0 — the distribution "succeeds" mechanically but produces no external signal. Risk register R1 names this exact failure. Mitigation must land in-slice; without it, the slice ships nothing observable.

2. **Scale/external-use failure — no consumer signal within 30 days.** `delivery-mechanism-friction/R4` (line 128) names this: if SessionStart does not visibly collapse J1 friction within 30 days, follow-up /decision revisits. The more brutal scenario: *no consumers exercise the plugin at all*. Cairn's current consumer is solely the operator (CLAUDE.md: "consumed by other projects via a `.slice-system → .` symlink"); operator dogfooding produced the "might be too strict" signal the FREEZE position dismisses as not-yet-structural. If 30 days of post-v0.2.0 use produces zero new friction, the freeze-justifying claim is itself unfalsifiable.

3. **Re-emergence failure — external stress surfaces later, trial-sequence design is stale.** A consumer hits a too-strict `must-satisfy` clause three months out. FREEZE commits to re-opening the trial sequence — but the three prepared branches were designed against 2026-05-20 codebase state. Three months of distribution will have shifted `.claude/handoff.md`, the identifier-scheme contract may have aged against external naming conventions, the operator's intuitions will have drifted. Frozen branches become Chesterton's fence: present but no longer trustworthy. Recovery cost: re-running Phase 0/0.5/1 against new state — roughly one trial from scratch.

## Constraint fit

- **Honors:** every INV-* and firm ADR enumerated in `01-constraints.md:5-22`. INV-002, INV-003, INV-005, INV-006 untouched. Trial A + Trial B contract blocks stay firm-bound. No ADR supersession. The N≥3 trigger is not invoked. The freeze actively honors the firmness shape — TIGHTEN-FIRST's N=1 amendment proposal (`03-premortem.md:27`) would have violated it.
- **Risks violating:** the operator's stated goal "do C" → step B (this /decision) after closing INV-002 (`00-question.md:35`). Step A shipped at `d35ded5`. The "do C" framing presumes step B's output is *a pick among RETROFIT/TRIAL-C/TIGHTEN-FIRST*. FREEZE+DISTRIBUTE refuses that pick. Central tension; see below.

## Why FREEZE+DISTRIBUTE *despite* the operator's "do C" framing

The /decision protocol's job is to surface meta-questions the framing missed. Three signals make the meta-question load-bearing:

1. **The trial sequence has already produced the meta-pattern.** Trial A + Trial B both landed. The pattern is demonstrated at two audiences (agent-to-agent handoff; validator-facing identifier-scheme). Phase 1 verification (`03-premortem.md:80`) confirms Trial B's tests are deterministic filesystem scans — the pattern works at the validator layer. A third internal trial yields diminishing evidence; cairn has at most one operator, all "external" use is operator dogfooding.

2. **Distribution has explicit operator-side gating, not absent will.** `docs/roadmap.md:67-72` enumerates "Gated" items deliberately deferred: F1.1 stdout literal gated on first real consumer install; agent-managed-planning-substrate gated on substrate Slices 1+2. Memory note "GitHub Project management — gated on substrate Slices 1+2" confirms the deferral pattern is active discipline. The handoff `.claude/handoff.md:43` blocks `gh:#31` as "V-3-attempt-2+V-5-operator-bound" — distribution threads are operator-bound *now*.

3. **External use generates qualitatively different signal.** Phase 1 named the categorical gap: Trial B uses deterministic filesystem checks, TRIAL-C's semantic-drift detection is "categorically different" (`03-premortem.md:80`). The operator cannot generate the missing signal class via more internal trials — only external use against a non-cairn codebase produces the audience-of-three (operator + phase-agent + external-consumer) the contract pattern was designed for. TRIAL-C simulates this; v0.2.0 to one external consumer is the actual test.

The right answer to "do C" is: surface that the /decision itself falsified the three-way framing.

## Downstream impact

**Easier:**

- External signal becomes available. A real `/plugin install` produces F1.1 stdout-literal data.
- Node-20 CI deadline (2026-06-02) is the time-boxing forcing function — the calendar does operator-bandwidth prioritization.
- Plugin update story gets documented (CONSUMER.md "Updating" section), closing a known `plugin-payload-transport-a1/D6` gap.
- The `cairn-diagnostics-with-detection` deferred trigger at 2026-09-01 (`delivery-mechanism-friction/D4`) gains 3+ months of evidence runway.

**Harder:**

- The deferred retrofit ages. `LEGACY_LABEL_BASELINE = 10` stays at 10; baseline-decrement-race (`03-premortem.md:11`) surfaces under field conditions rather than controlled trial conditions.
- Intent-contract validation does not happen. TRIAL-C's stated success ("contract surfaced ambiguity Phase 2 would have asked about", `02-journey.md:94`) remains untested. The most-LLM-authored artifact stays uncontracted.
- Less per-session learning. Each cairn-internal session would produce a contract-shape data point; distribution sessions produce zero such points.

## Honest costs

**Calendar time.** Node-20 bump (#32) is the 2026-06-02 lock-in. The `delivery-mechanism-friction` impl slice (#33) is multi-file (SessionStart skill + 4 nav agents + CI token-budget check) — 2–4 sessions. CONSUMER.md "Updating" is small. Total: ~3–5 sessions before any external signal is reachable.

**Strongest argument against.** Phase 1's audit #4 (`03-premortem.md:48-49`) contested "RETROFIT is zero-decision, low-risk" and found four implicit decisions. FREEZE over-trusts the symmetric claim — "distribution is low-decision-weight, just ship what's stable." v0.2.0 carries its own implicit decisions: which nav agents land vs. defer to `cairn-diagnostics-with-detection`; whether D6 token-budget enforcement lands in-slice or fails to documented EXPOSED; whether manual-update is surfaced loudly enough to matter. FREEZE+DISTRIBUTE is *also* "many small editorial decisions" — the same surface where rubber-stamping bites.

**Risk that distribute gets stuck on dependencies the trials would have surfaced.** If the impl slice hits a contract-pattern-shape problem mid-execution (e.g., SessionStart spec-as-prose vs. spec-as-contract tension TRIAL-C would have explored), FREEZE has to either (a) cross its own freeze line and run a mini-trial, or (b) ship with a gap the un-run TRIAL-C would have caught. Both erode the freeze's justification. Honest reading: trial sequence and distribution track are not as separable as the FREEZE framing claims.

# Cairn thin-substrate trials plan — 2026-05-20 (landed 2026-05-25)

> Companion to `docs/adr/cairn-thin-substrate-direction.md` (DRAFT). Carries the empirical evidence that shaped the ADR's amendments to the original `govllm-trial/CAIRN_PLAN.md` proposal, the trial sequence, and the gating each trial requires.

---

## Late-landing acknowledgment (2026-05-25)

Between this plan's drafting (2026-05-20, alongside the companion ADR) and its landing on `dev` (2026-05-25), three ADRs and one direction-doc shipped on `dev` that this plan must reconcile with rather than ignore. The body below is preserved as drafted so the original framing is auditable; this section maps stale references to current state.

**ADRs landed since 2026-05-20:**

- `identity-and-scope-deferral` (2026-05-20) — explicitly defers direction-level identity pivots. The companion ADR is offered as candidate D3.4 input under that ADR's revisit triggers, not as an attempted supersession.
- `adr-contract-execution-scope-clause` (2026-05-20) — adds `execution-scope:` as a sixth contract clause. The companion ADR's D2.1 grammar enumeration ("must-satisfy / must-not-violate / wrong-if / escalate-when / evidence") was five clauses; reading-in-2026-05-25-and-later should treat the grammar as those five plus the landed `execution-scope:` clause.
- `schema-amendment-threshold` (2026-05-14) — N≥3 protocol for firm-schema amendment under single-instance drift. Doesn't bind this plan (this plan proposes direction, not schema amendment), but the option-value reasoning behind it is shared with `identity-and-scope-deferral`.

**Trials landed since drafting:**

- **Trial A** (handoff contract block, shipped at commit `53a7c58`, 2026-05-13) — this is what this plan's body calls "Trial 1." It is **done**. The Trial-A handoff contract template lives at `templates/handoff.md`; tests at `tests/unit/test_handoff_contract.py`.
- **Trial B** (ADR contract on `identifier-scheme.md`, closed at verdict `a0e3fe6`, 2026-05-14 → 2026-05-19) — operator verdict: *"works, but might be too strict."* That verdict directly produced `adr-contract-execution-scope-clause`. Trial B is **closed**; the "too strict" insight is absorbed.

**Trial renumbering:** read this plan's "Trial 1 / 2 / 3" as **Trial C / D / E** to avoid collision with the landed Trial A / B. The mapping:

| This plan's name | Read as | Status |
|------------------|---------|--------|
| Trial 1 — Contract block on handoff | (Already landed as **Trial A**, 2026-05-13) | Done; this plan's framing is retrospectively descriptive, not prospective |
| Trial 2 — EARS in intent.md | Trial D | Unblocked, gated on exception-class implementation |
| Trial 3 — Drop phase 1 derivation | Trial E | Gated on `premise_guard.py` shipping AND on `identity-and-scope-deferral` D3 evaluation |
| (new) `premise_guard.py` implementation | Trial C | Independent of D and E; the slice #25 counterfactual is sufficient motivation |

**`docs/plans/2026-05-19-adaptive-reliability-direction.md`** is the direction-doc that `identity-and-scope-deferral` ruled on. Its tiered-reliability model is orthogonal to the six-primitive thin-substrate framing in the companion ADR; both proposals are now on file for the next operator evaluation.

The empirical probes recorded below (§1.1–1.3) are unaffected by the intervening ADRs — they read source and ran agents against state that has not changed materially. The strongest single net-new contribution is **§1.3's slice #25 counterfactual** and the `premise_guard.py` proposal it motivates. Even if the directional ADR is not advanced past DRAFT, Trial C (premise-grounding hook) stands on its own.

---

## Goal

Validate (or further falsify) the load-bearing claims of `cairn-thin-substrate-direction` through a trial sequence, with empirical evidence required before each trial transitions to the next.

The ADR commits to the *direction*. This plan commits to *how the direction is tested into production*.

---

## 1. Empirical baseline (2026-05-20)

Three parallel agent probes against the original plan's load-bearing claims. Verbatim findings preserved here as the falsification-on-record.

### 1.1 EARS authorability (Probe A)

**Method:** Three real completed cairn intents under `.claude/skill-runs/` translated to EARS notation; atomicity check applied per clause. Mix of size: heavy, medium, light/papercut.

**Findings:**

- Authoring surcharge **+25-33%** across the size span (fairly constant).
- Sharper on heavy/medium intents — EARS forced explicit trigger-naming (Event-driven shape) and split compound claims hidden under "and X and Y and Z" prose.
- Ritualistic on light/papercut intents — trivial existence claims like "the file X shall exist" gained no rigor.
- Atomic-primitive pass rate as-authored:
  - Light intent: ~90% (9/10)
  - Medium intent: ~38%
  - Heavy intent: ~47% post-decomposition; **0/12 of original A-clauses were strictly atomic** — every one bundled 2-4 sub-claims.
- Estimated overall: ~50-60% of real clauses pass atomicity.

**Prose-leakage failure mode discovered:** EARS catches trigger/response clarity but does **not** catch universal-quantification-over-implicit-domain. Authors will write grammatically-correct EARS that the atomic-primitive rule should reject, but the rule has no syntactic hook. Four concrete cases:

1. "Citing INV-011" — Ubiquitous in form, reader-judgment in semantics.
2. "Shall not modify the working tree/index/environment" — universal-over-all-ops disguised as Ubiquitous.
3. "Every consumer-facing surface" — universal-over-implicit-set; EARS passes, atomicity fails.
4. "Existing behaviour unchanged" — regression-class meta-claim that EARS shapes naturally but atomicity cannot adjudicate.

**Verdict:** Generalizes to ~60-70% of cairn intents. The atomicity rule needs named exception classes (ADR D3 codifies four: `universal-set`, `regression-meta`, `operator-bound`, `trivial-existence`).

**Scratch artifact:** `.claude/scratch/ears-authorability-spike.md` (untracked).

### 1.2 PBT-on-clauses falsification (Probe B)

**Method:** One EARS clause (Unwanted shape, lifted from `role_guard.py:142-165` envelope-mode behavior) translated to a Hypothesis property test; run against correct and deliberately-violating implementations.

**Clause tested:**

> *IF `active-envelope.yaml` declares `mode: operator` AND the write `file_path` matches no regex in `paths`, THEN `role_guard.py` shall deny the write (non-zero exit).*

**Result:** Falsification worked. Correct guard: 40/40 generated cases pass in 2.9s. Buggy guard (always-allow): falsified at `patterns=['^0/'], candidate='0'` in 14s, with Hypothesis shrinking to a minimal counterexample.

**Honest caveat — the oracle is the load-bearing cheat.** The property test's reference implementation re-applies `re.search` over the same patterns the SUT consumes. The test is therefore a differential test against a one-line spec, not an independent falsification of arbitrary semantics. For *this* clause that's defensible (the clause IS regex semantics, lifted directly), but the property test degenerates into a triviality. The falsification signal catches gross violations (always-allow, always-deny, inverted logic) and misses subtle ones (PyYAML `off→False` coercion, the empty-`file_path` early-return at line 158) because the generators didn't model them.

**Estimated PBT coverage of real `must-satisfy` clauses: ~30-40%.**

PBT-friendly:
- Envelope path matching, regex-allowlist invariants
- ADR frontmatter shape, identifier-scheme parsing
- Supersession-graph acyclicity
- Force-push-flag detection

PBT-hostile (60-70%):

1. **Aesthetic / prose clauses** ("pointer-only", "no narrative", "reads naturally") — no generator can synthesize a falsifying narrative-leaking handoff without an LLM-as-judge oracle, at which point PBT collapses into vibes-grading (which the original Trial 1 `wrong-if` explicitly forbids).
2. **Process clauses** ("operator drives cold on resume", "one pause-resume cycle") — not state-functions; not Hypothesis'able.
3. **Cross-artifact clauses** ("ADR body checksum matches commit at `status: accepted`") — generators possible, but property is an integration check, not PBT.
4. **Atomicity-of-clauses meta-rule** — requires parsing intent and counting tool calls; that's a static analyzer.
5. **Clauses where the SUT *is* the oracle** — PBT confirms internal consistency but can't catch a wrong spec.

**Verdict:** The original plan's framing of PBT as "the falsification surface that replaces Phase 2 Skeptic" is **overclaim by ~2x.** PBT replaces Skeptic for ~30-40% of clauses; the rest still need judges, static analyzers, or integration assertions. The "~25-37% pass@1 code-gen gain" citation is doing rhetorical work — code generation has a built-in runtime oracle; contract falsification on qualitative cairn clauses does not.

**Recommendation surfaced by the probe:** Trial 1's contract-on-handoff will likely succeed *because handoff has the highest mechanical-checkability ratio* (frontmatter shape, line counts, file existence). **Do not generalize Trial 1 success to `intent.md` `must-satisfy` clauses.**

**Scratch artifact:** `.claude/scratch/pbt-spike/test_envelope_property.py` and `role_guard_buggy.py` (untracked).

### 1.3 Slice #25 wrong-model counterfactual (Probe C)

**Method:** Slice #25's source materials recovered from git commit `2f39d90` (M4 retirement removed the working-tree files). The wrong-premise xfail is at `test_root_resolver_migration.py:421-440`; its docstring claims `_REPO_ROOT` is used "for sys.path injection AND DB/corpus paths," but `server.py:21` and `tools.py:18` only used it for `sys.path.insert`, with DB/corpus already on `cairn_query.DEFAULT_DB_PATH` via `project_root()`. An EARS-shaped contract block was constructed faithfully from the wrong premise the original intent had.

**EARS contract block as authored from slice #25 (wrong premise preserved):**

```yaml
must-satisfy:
  - "When mcp_servers/cairn_knowledge/server.py is loaded, it shall obtain project root by calling scripts._root.project_root()."
  - "When mcp_servers/cairn_knowledge/tools.py is loaded, it shall obtain project root by calling scripts._root.project_root()."
must-not-violate:
  - "No occurrence of `Path(__file__).resolve().parent.parent.parent` in mcp_servers/cairn_knowledge/{server,tools}.py."
envelope:
  - "mcp_servers/cairn_knowledge/(server|tools)\\.py"
  - "tests/unit/test_root_resolver_migration\\.py"
```

EARS grammar accepts this. Scope-split passes (each clause = one grep/pytest call). Envelope correctly contains the proposed writes.

**Which mechanical layer catches the wrong model? None.**

- EARS grammar checks form, not truth.
- Scope-split checks atomicity, not factual grounding.
- `role_guard.py` checks write-scope containment — the wrong fix writes *within* the declared envelope.
- `reversibility-guard.sh` sees no destructive op, no secret, no ADR mutation.
- The ADR corpus (lesson L-017) is *itself* the half-wrong input.
- PBT-on-clauses would generate Hypothesis cases *from* the wrong clause and assert it, never crossing into the integration premise (`import cairn_query` at server boot from consumer cwd) that actually fails.

**Verdict on Trial 3 of the original plan: Falsified.** "Contract grammar alone defeats wrong-model propagation" is not supported by this counterfactual. The slice #25 failure was a *semantic grounding* failure (intent's premise about existing source was false), and no cairn-simplified layer reads source to challenge premises. Arguably worse than today's pipeline: Phase 2 Skeptic at least exists as a role where the check could be added; cairn-simplified deletes the role and adds no replacement. EARS shape may make it worse by lending wrong claims a more authoritative form.

**Smallest fix:** A *premise-grounding hook* — for any `must-satisfy` / `must-not-violate` clause that names a file path or regex, require an `evidence.premise:` field quoting the cited source line(s) verbatim with a one-line current-behavior label. Hook mechanically diffs the quoted text against actual source and rejects on mismatch at intent-approval time. For slice #25, the operator would have had to write "server.py:21 — `_REPO_ROOT` chain used at lines 22-25 to insert into sys.path. NOT used for DB or corpus path" — at which point the wrong premise becomes self-evidently contradicted by the surrounding `sys.path.insert` lines. ~30-60 LOC, same hook layer as `role_guard.py`, provider-agnostic. **Codified as `premise_guard.py` in ADR D2.5.**

**Scratch artifact:** `.claude/scratch/slice-25-counterfactual.md` (untracked).

---

## 2. Trial sequence and gating

The three trials descend from the original plan but are re-gated by the probes above.

### Trial 1 — Contract block on handoff (unblocked)

**Why first:** Handoff has the lowest coupling to other artifacts. Changing handoff doesn't break phase expectations or any consumer. Handoff also has the highest mechanical-checkability ratio (frontmatter shape, line counts, file existence) — the most favorable terrain for PBT-on-clauses.

**Caveat surfaced by Probe B:** A successful Trial 1 does **not** generalize to `intent.md`. The plan must explicitly resist that inference. Trial 2 is where the harder question gets answered.

**Trial-contract sketch** (operator may amend):

```yaml
contract:
  must-satisfy:
    - "WHEN handoff.md is committed, it shall contain a frontmatter contract block of ≤15 lines."
    - "WHEN tests/unit/test_handoff_contract.py runs, it shall pass against a conforming handoff and fail against a violating one."
    - "After one pause-resume cycle under the new shape, the operator shall confirm cold resume succeeded without out-of-band context."
  must-not-violate:
    - "No new files outside handoff.md + one test file."
    - "No new substrate layer (no MCP, no daemon)."
  wrong-if:
    - "The property test is itself prose-shaped (vibes-grading the contract)."
    - "Operator feels they're authoring narrative on resume."
    - "Contract block needs amendment after first use (signals over-design)."
  escalate-when:
    - "Property test takes >30 minutes to write."
    - "Contract block grows past 15 lines while drafting."
  evidence:
    - "Diff to handoff.md showing the contract block."
    - "tests/unit/test_handoff_contract.py with PBT generators."
    - "Operator's one-line verdict after pause-resume."
```

**Estimated effort:** One session.

**Pass criteria → Trial 2:** All three `must-satisfy` met, no `wrong-if` triggered, operator confirms reduced ceremony cost.

### Trial 2 — EARS contract block in intent.md (gated on Trial 1 + exception classes)

**Why second:** Validates EARS at production intent scale. The ~25-33% surcharge from Probe A is acceptable on heavy/medium intents but ritualistic on light ones. Trial 2 must surface whether the named exception classes (D3) make the rule operable, or whether operators continue to game it.

**Pre-Trial-2 requirement:** The four exception classes (`universal-set`, `regression-meta`, `operator-bound`, `trivial-existence`) must be specified in the intent template and accepted by the scope-split rule. Without exceptions, Trial 2 will reproduce Probe A's findings (atomicity fires on ~half of real intents).

**Probe to run during Trial 2:** Pick three real candidate intents spanning the size range. Author each in EARS shape with exception classes available. Measure:

- Authoring time delta vs. prose-shape baseline
- Operator's subjective rubber-stamping reduction
- Atomicity-rule firing rate (false-positive vs. true-positive ratio)
- Whether prose-leakage failures from Probe A recurred

**Pass criteria → Trial 3:** Authoring time delta ≤30%. Operator confirms reduced rubber-stamping on at least 2 of 3 intents. Atomicity rule false-positive rate <10% with exceptions in play.

### Trial 3 — Drop phase 1 derivation (gated on `premise_guard.py` shipping)

**Why last and gated:** Probe C falsified the original Trial 3 thesis ("contract grammar alone defeats wrong-model propagation"). The slice #25 counterfactual makes the failure mode concrete: a wrong-premise input propagates through every cairn-simplified mechanical layer unchallenged.

**Gating requirement:** `premise_guard.py` must ship as a working hook before Trial 3 begins. Specification (initial):

- For each `must-satisfy` / `must-not-violate` clause that names a file path, regex, line number, or source identifier:
  - The intent's `evidence:` block must include a `premise:` field
  - `premise:` contains a verbatim quote of the cited source span + a one-line current-behavior label
  - Hook mechanically reads the cited source at intent-approval time, diffs against the quoted text, denies the session start on mismatch
- Mismatch denial includes the diff in the error message
- Editorial escape hatch (similar to `ADR_EDITORIAL_FIX=1`) for known divergence (e.g. removed code)

**Re-probe during Trial 3:** Re-run the slice #25 counterfactual under the new discipline. With `premise_guard.py` active, the operator authoring slice #25's intent would have had to quote `server.py:21-25` verbatim. The surrounding `sys.path.insert` lines would then contradict the docstring's "AND DB/corpus paths" claim within the intent itself — surfacing the wrong premise mechanically.

**Pass criteria for Trial 3:** Slice #25 counterfactual blocks at intent-approval under `premise_guard.py`. At least one production session completes the four-phase shape replaced by intent.md + premise-grounding + envelope, with the operator confirming no semantic-grounding failure leaked through.

**If Trial 3 fails:** The four-phase pipeline is retained. The contract grammar + premise-grounding combo did not produce a complete replacement for Phase 2 Skeptic's source-reading pass. Possible next step: add a *judge subagent* mechanism as the formal Skeptic-replacement, not just delete phases.

---

## 3. Trial schedule (advisory, not load-bearing)

| Trial | Earliest start | Gating |
|-------|----------------|--------|
| 1 — handoff contract block | 2026-05-21 | None |
| 2 — EARS in intent.md | Trial 1 close + exception-class implementation | Trial 1 pass + atomicity-exceptions live |
| `premise_guard.py` ship | Independent | None (parallelizable with Trial 2) |
| 3 — drop phase 1 | Trial 2 close + `premise_guard.py` shipped | Both gates passed |

Trials 1, 2, and the premise-grounding implementation are independent enough to run in any order or in parallel. Trial 3 strictly waits.

---

## 4. Open questions surviving the empirical baseline

1. **What does a judge-subagent mechanism look like if Trial 3 still falls short under `premise_guard.py`?** Probe C's smallest fix may not be sufficient; the formal Skeptic role may need preservation as a subagent, not just a hook. Decide post-Trial-3.

2. **Generation policy for AGENTS.md / CLAUDE.md.** Manual curation guarantees drift past ~20 ADRs; auto-generation tooling doesn't exist. Either commit to building it as a follow-on, or keep CLAUDE.md so thin it's a pointer index. Defer until Trial 2 close.

3. **Multi-session intents.** Larger features span sessions. Does an `intent.md` commit + handoff pointer suffice, or does the model need an explicit `parent-intent:` field? Lean toward handoff suffices; revisit if pain emerges.

4. **Threshold for "trivial edits skip intent."** D3's `trivial-existence` class addresses lightweight clauses *within* an intent, but the meta-question of when a session even *has* an intent is unresolved. Without a mechanical threshold (diff-size cap, file-count cap), this becomes the new ad-hoc path.

5. **Hook-portability gap on narrower providers (Cursor and pre-hook tools).** Documented as "convention-portable, not enforcement-portable" in ADR D1, but the operational consequence — how cairn-on-Cursor degrades — is unspecified. Defer until a real Cursor user emerges.

6. **What is `premise_guard.py`'s line-quote-matching tolerance?** Exact string match is brittle (whitespace, trailing comments). Fuzzy match is permissive. Likely answer: normalize whitespace and strip comments, but specify before building.

---

## 5. Anti-temptations (recorded, not novel)

These are restated from the ADR's "Out of scope" section and reinforced here as trial-time temptations:

- **Do not add Spec-Kit-shaped mandatory artifacts** because they look thorough. One intent.md per session is the right default.
- **Do not let PBT-on-clauses become the default for all `must-satisfy` clauses.** It is one of four mechanisms; operators must pick the right one via the `evidence:` field.
- **Do not delete Phase 2 Skeptic without an equivalent mechanism.** The judge role survives even if the phase shape doesn't.
- **Do not let `premise_guard.py` become a full source-comprehension layer.** Its job is verbatim-quote-vs-source mechanical diff, nothing more. Semantic grounding remains an operator-and-Skeptic responsibility.

---

## References

- `docs/adr/cairn-thin-substrate-direction.md` — companion ADR
- `docs/plans/2026-05-13-cairn-as-interaction-protocol.md` — reframe this plan extends
- `docs/adr/phase-pipeline-evaluation.md` — four-phase pipeline retained pending these trials
- `docs/adr/identifier-scheme.md` — id/name two-field model
- `.claude/scratch/ears-authorability-spike.md` — Probe A artifact
- `.claude/scratch/pbt-spike/` — Probe B artifact
- `.claude/scratch/slice-25-counterfactual.md` — Probe C artifact
- `govllm-trial/CAIRN_PLAN.md` — original downstream proposal, superseded by the ADR

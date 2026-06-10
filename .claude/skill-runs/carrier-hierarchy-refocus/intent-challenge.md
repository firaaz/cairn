# Intent challenge — carrier-hierarchy-refocus

Verdict: **BLOCKED** (premises p1, p2, p5). Challenged at snapshot 2d24db1, 2026-06-10.
Premise ids follow intent order: p1 role_guard, p2 premise_guard, p3 intent-challenge brief, p4 dogfood-log, p5 handoff.

## premise-source-checks

### p1 — checks/role_guard.py
- Quote verified verbatim: docstring lines 4–5.
- Read: `checks/role_guard.py:1-207` (full file), `.claude/settings.json:44-52` (hook registration: `uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py` on `Write|Edit|MultiEdit|NotebookEdit`; file is git-tracked), `commands/claude-code/settings.json:2,19` (consumer template registers `python3 $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py`), gh#35 body, `.claude/envelope-grants.log` (11 lines, all `foo/bar.py` test fixtures dated 2026-05-08 — no real grants ever logged).
- gh#35 fail-open report is ACCURATE: every deny path (`role_guard.py:149,165,184,200,203`) returns exit 1 with no `permissionDecision` JSON; per Claude Code hook semantics only exit 2 / deny JSON blocks. All three enforcement paths (operator envelope, phase-3 envelope, per-role allowlist) have never blocked a write in production. Tests assert the broken code (`== 1`). No catch evidence anywhere (grants log is fixtures-only; no field-note or commit cites a role_guard block).
- Label narrowly true. Dependent claim FALSE — see counterfactual.

### p2 — checks/premise_guard.py
- Quote verified verbatim: docstring lines 3–4.
- Read: `checks/premise_guard.py:95-114` (`_check_premises` reads only `source`/`quote`, never `label`) — label's mechanism claim is accurate; slice-#25 exit-0 confirmed live at `docs/operator-field-notes-2026-06-01.md:84-87`.
- Label true. Dependent retirement claim ("premise-grounding is the challenge subagent's job — it's the thing with receipts") FALSE — see counterfactual.

### p3 — .claude/agents/intent-challenge.md
- Quote verified verbatim: line 19. Brief owns the slice-#25 semantic gap (line 13: "That gap is your job") and hard-codes the `_REPO_ROOT` example (line 19). Label accurate. PASS — but note line 13 also states "premise_guard already ran at the approval gate: it confirmed each quote is verbatim-present", which the p2 retirement falsifies (coupling fed into p2's block).

### p4 — docs/dogfood-log.md
- Quote verified verbatim: lines 8–9. Full file read (12 lines): schema + pointer to `scripts/dogfood_evaluate.py`, zero entries. Corroborated by `docs/operator-field-notes-2026-06-01.md:56-57`. Label accurate. PASS.

### p5 — .claude/handoff.md
- Quote verified verbatim: frontmatter line 4.
- Read: `tests/unit/test_handoff_contract.py` in full. The contract the test asserts is NOT only pointer+state per line. Test 4 `test_coverage_open_issues` (~line 165): **every open GitHub issue must appear as a handoff line** (`open_issues - in_handoff` must be empty). Test 5 `test_coverage_provisional_adrs`: every provisional-status ADR must appear (currently 0, inert).
- Live numbers: `gh issue list --state open` → **29 open issues**. The plan's sweep candidates (#5,6,8,9,12,13,16,18,28) = 9; "keep defect-shaped and consumer-shaped issues" leaves ~20 open → test 4 forces **≥20 handoff gh lines**.
- Label FALSE — see counterfactual.

## semantic-counterfactual-search

### p1 — HELD (block)
Counterfactual: the quote (operator-envelope path description) is true, and the label is true, but the dependent claim — deleting `role_guard.py` + `active-envelope.yaml` "removes the mechanism gh#35 reports as fail-open" as a clean retirement — is false in effect. The deletion does not produce absence; it produces inversion:
- `.claude/settings.json` (git-tracked, NOT in the intent's `execution-scope`) keeps the PreToolUse registration. `python3`/`uv run python` on a missing file exits **2** (verified live: `exit=2`) — and exit 2 is the one code that BLOCKS. Deleting the script while the registration persists turns the never-blocked hook into a **block-every-write** gate in cairn itself, including for the agent executing the remaining retirement commits.
- must-satisfy clause 4 ("repo shall contain neither checks/role_guard.py nor .claude/active-envelope.yaml") is therefore unachievable inside the declared `execution-scope`: the required deregistration edit to `.claude/settings.json` matches no scope pattern, so satisfying the clause either bricks writes or forces an out-of-scope write the close-review envelope-diff must then flag.
- Consumer blast radius: `commands/claude-code/settings.json:19` (the consumer template) registers the same hook; any consumer that copied it and pulls a cairn without `checks/role_guard.py` via `.slice-system → .` gets all writes blocked. This contradicts both the Boundary's scope-out ("no consumer-facing script behaviour changes intended") and `escalate-when` clause 3.
- Secondary elision: deleting the whole file also removes the per-phase (`AGENT_ROLE` set) gate that the kept-as-legacy `cairn-tdd-feature` skill documents as its write enforcement (`docs/operational-reference.md:131,290-292`). Empirically that gate also never blocked (same exit-1 defect), so the functional loss is nil — but the intent should say so rather than scope the label to the envelope path only.

### p2 — HELD (block)
Counterfactual: quote and label true (premise_guard never reads `label:`; slice-#25 exits 0), but the dependent claim that the challenge agent "is the thing with receipts" for premise-grounding — making premise_guard retireable — is false against the live record:
- The agent's brief explicitly delegates the verbatim layer to premise_guard (`.claude/agents/intent-challenge.md:13`) and charters the agent for the semantic layer only.
- Every logged challenge-agent receipt was earned WITH premise_guard running as a mechanical precondition: `docs/operator-field-notes-2026-06-01.md:106-108` ("Mechanical preconditions held: grounded variants → premise_guard exit 0; bogus path → exit 1"), `docs/operator-field-notes-2026-06-02.md:45-47` (same). The stale/fabricated-quote class was deliberately pre-filtered out of every experiment — the agent has **zero receipts** on the class premise_guard covers.
- premise_guard itself is not receipt-free: it red'd a mis-anchored (comment-quoted) premise during D2 drafting (`operator-field-notes-2026-06-02.md:47-49`) and demonstrably discriminates fabricated paths (exit 1 "cited source not found") — harness-context catches, but logged ones, which the plan's "no-evidence/untested" bucket (Finding 2) overstates into zero.
- Retiring it without re-chartering the agent leaves the brief's line 13 false and the verbatim class owned by nobody with receipts. The receipts principle, applied to its own evidence, does not support this retirement as specified.

### p3 — DID NOT HOLD (pass)
Counterfactual attempted: "the brief mentions slice-#25 but doesn't actually charter the semantic check" — refuted by lines 13–19 read directly; charter and hard-coded example both present, and de-primed generalization receipts exist (`operator-field-notes-2026-06-01.md:111-119`). Label faithful.

### p4 — DID NOT HOLD (pass)
Counterfactual attempted: "entries exist elsewhere / the log is consumed by live machinery whose deletion reds something" — file read in full (zero entries); field notes confirm zero entries and a schema mismatch (`2026-06-01.md:56-57`). Label faithful.

### p5 — HELD (block)
Counterfactual: the quote ("every body line names a thread with a resolvable pointer") is verbatim-true, but the label — "the diet shrinks line count without changing the contract shape test_handoff_contract.py asserts" — misrepresents the test. The asserted contract includes **coverage** (test 4: every open gh issue must appear; test 5: every provisional ADR), not just per-line shape. With 29 open issues and a sweep closing ~9, the post-sweep handoff must carry ≥20 gh lines for the suite to stay green. The intent's must-satisfy pair — "at most 6 active thread lines" AND "test_handoff_contract.py green" — is jointly unsatisfiable while the Boundary forbids changing the test's shape. The plan's premise "everything else lives solely as gh issues" (Changes B) is the exact state test 4 exists to red. Classic slice-#25 shape: grounded quote, label extrapolates a model the file contradicts 120 lines below the quote.

## Plan-level load-bearing claims (briefed attack items)

1. **role_guard fail-open accuracy** — CONFIRMED accurate (gh#35; deny paths exit 1; tests assert it). No evidence of any real catch: `envelope-grants.log` holds only `foo/bar.py` fixtures; no field note or commit cites a role_guard block. "Empirically not load-bearing" stands — but see p1: the *deletion mechanics* are what's wrong, not the diagnosis.
2. **premise_guard redundancy** — NOT supported. Division-of-labor is complementary, not redundant; the agent's receipts are conditional on premise_guard's floor (p2 above).
3. **"Only fresh-context checkpoints and concluding trials have receipts"** — Mostly holds, with one overstatement: premise_guard has logged harness-context reds (`2026-06-02.md:47-49`, bogus-path discrimination in both experiment writeups). No production catch logged for role_guard, handoff content, dogfood-log, or a `/decision` arc (the 2026-06-05 catch was operator-initiated research-before-build, not the 8-phase machinery). Not independently block-grade; folded into p2.
4. **Circularity of the lean decision form** — Strongest self-serving reading: the lean form's single fresh-context attack audits *premises*, not *alternatives*. An 8-phase `/decision` arc's parallel-approaches phase would have surfaced the alternative this plan never weighs: gh#35 ships a concrete ~5-line repair (shared `_deny` helper, flip five `return 1`→deny-JSON+2, flip test asserts) — "repair + liveness test" vs "delete + close-review diff" is exactly an alternatives-comparison question, and the plan's own lesson (C: "an enforcer without a liveness test is documentation") argues the failure was missing liveness, not the mechanism class. This challenge can name the omission but cannot adjudicate it; that is a real capability the retired arc had. Mitigation: the intent flags the lean form as an explicit operator call (Boundary), so this is recorded as a sustained risk feeding p1's revision, not an independent block.
5. **Post-hoc envelope-diff vs write-time blocking** — No material regression found: per gh#35, write-time blocking has never functioned (all deny paths non-blocking since the exit-code convention applies), so nothing in the repo can have been relying on it. The phase-3 dispatch envelope and consumer paths were equally fail-open. The only write-time loss is theoretical; the only *real* write-time behaviour change introduced by this intent is the accidental fail-closed inversion in p1.

## verdict

**challenge-blocked** — p1, p2, p5 sustained. p3, p4 pass.

Required revision before re-challenge:
1. (p1) Add `.claude/settings.json` hook deregistration to the Specification and `execution-scope`; sequence it in the same commit as (or before) the `role_guard.py` deletion. Address the consumer template (`commands/claude-code/settings.json`) and already-deployed consumer registrations, or retract "no consumer-facing script behaviour changes intended" and route per `escalate-when`. Record the gh#35 repair-plus-liveness alternative and why deletion wins it.
2. (p2) Either retain `premise_guard.py` as the mechanical verbatim layer (its receipts and the agent's chartered division of labor both argue for it), or pair its deletion with a re-chartered `intent-challenge.md` brief that assigns the verbatim class to the agent and an honest Risk Surface line stating that class is receipt-less under the new owner.
3. (p5) Reconcile the ≤6-line diet with `test_coverage_open_issues`: either the diet floor becomes "6 + one line per remaining open issue", or the coverage tests change (currently forbidden by Boundary), or the issue sweep is ~3x larger than planned. Pick one explicitly; the current must-satisfy pair is unsatisfiable.

---

# Re-challenge verdict (revision 2, 2026-06-10)

## Resolution check on the three sustained blocks

- **p1 (role_guard) — RESOLVED.** Specification line 32 bundles the deletion with deregistration in BOTH `.claude/settings.json` and `commands/claude-code/settings.json` in the same commit, naming the exact failure mode (dangling registration → exit 2 → blocks every write). `\.claude/settings\.json` added to `execution-scope` (line 137). must-satisfy clause 4 now requires "nor any settings hook entry referencing role_guard" — satisfiable in scope. The repair-gh#35 alternative is recorded in Risk Surface as an explicit operator call at sign-off, not dropped. Premise-1 label rewritten to the verified model; re-verified against `checks/role_guard.py`, both settings files, and the live exit-2 check. Holds.
- **p2 (premise_guard) — RESOLVED in all operative clauses.** Retained unchanged with tests (What line 19, Boundary line 27, Specification line 33, must-not-violate line 114); SKILL.md Step-3 invocation stays (line 34); retention rationale routed to the refocus ADR. Premise-2 label updated and accurate. **But see new finding below: `scope-statement` was not updated.**
- **p5 (handoff) — RESOLVED.** must-satisfy clause 6 now pairs the ≤6-line diet with the AMENDED test (`test_coverage_open_issues` removed; Specification line 37); Boundary updated honestly ("the plan's 'test unchanged in shape' premise was wrong"). Premise-5 label now correctly describes the test's coverage assertion. Remaining assertions verified compatible with a 6-line handoff: pointer/state/prose checks are per-line; `test_coverage_provisional_adrs` currently binds 0 ADRs (if the new refocus ADR ships `status: provisional` it consumes 1 of the 6 lines — satisfiable).

## New finding — contract-internal contradiction (revision residue)

`Contract.scope-statement` (line 98) still reads: "retire receipt-less machinery (role_guard envelope, **premise_guard gate**, /decision arc, trials apparatus, dogfood-log, handoff bulk)" — while `must-not-violate` (line 114) requires "checks/premise_guard.py + its tests ... remain live" and Specification line 33 retains it. Pre-revision the scope-statement was consistent with the (then-wrong) spec; the revision updated every operative section except this line, so the contract now grants retirement authority its own must-not-violate forbids. The scope-statement is the one-line scope the operator signs and the close-review reads first; a constructor or reviewer anchoring on it is authorized to do the exact thing line 114 blocks. This meets the re-challenge's blocking criterion (revision-introduced contradiction). One-line fix; everything else passes.

## Residual (non-blocking, named for sign-off)

Already-deployed consumers whose `settings.json` was composed from the template still register `python3 .slice-system/checks/role_guard.py`; on their next cairn pull the dangling registration blocks all their writes (fail-closed, loud, self-explaining stderr). Cairn cannot edit consumer settings; the contract's `escalate-when` clause 3 covers the emergence path. Recommend (non-blocking): one upgrade note in `docs/upgrading-from-symlink.md` or the refocus ADR instructing consumers to drop the role_guard hook entry when pulling past the retirement commit.

## verdict

**challenge-blocked** (narrow) — original p1/p2/p5 blocks all resolved; one revision-introduced contradiction sustained: `scope-statement` vs `must-not-violate` on premise_guard retention.

Required revision: remove "premise_guard gate" from `Contract.scope-statement` (line 98) so the signed scope summary matches Specification line 33 and must-not-violate line 114. Optionally add the consumer upgrade-note line to Risk Surface.

---

# Final verdict (revision 3, 2026-06-10)

Verified against the live intent: `scope-statement` (line 98) no longer lists premise_guard among retirements and explicitly states "premise_guard retained" — consistent with Specification line 33 and must-not-violate line 114. Risk Surface now carries the deployed-consumer dangling-registration residual with the upgrade-doc obligation ("drop the role_guard hook entry" note in the refocus ADR / upgrade doc). All sustained blocks (p1, p2, p5, contract-scope-statement) are resolved; no new contradictions introduced.

**challenge-pass.** Construction may begin. Standing risks the close-review should hold: (1) the role_guard deletion commit must contain both settings deregistrations or writes brick; (2) the consumer upgrade note is a contracted deliverable, not optional; (3) the lean-decision-form circularity remains an explicit operator call at sign-off.

---

# Re-challenge verdict (revision 4 — role_guard REPAIRED, not deleted; 2026-06-10)

Directed change verified in the intent: repair clauses at What line 19, Specification line 33, must-satisfy 109, smoketest universal-set line 108 (+ spec line 36), must-not-violate 119, scope-statement 103. New premise (exit-codes docstring) verified verbatim against `checks/role_guard.py:13`; its label is accurate (deny=1, only 2 blocks, per gh#35 and the PreToolUse protocol).

## (a) Is deny→exit 2 sufficient? NO — second fail-open cause found and demonstrated live. BLOCK.

The exit-code defect has been masking a path-shape defect. The envelope's regexes are repo-root-relative and anchored (`active-envelope.yaml:6-8` says "matched against the path AS REPORTED BY THE TOOL... anchor with ^"), but the tool reports ABSOLUTE paths. `role_guard.py` `main()` matches `tool_input.file_path` raw — no normalization, no CAIRN_ROOT stripping. Live demonstration at snapshot (CLAUDE_PROJECT_DIR set, shipped `mode: operator` envelope):

- `{"file_path":"docs/roadmap.md"}` → exit 0 (allowed; matches `^docs/roadmap\.md$`)
- `{"file_path":"/Users/.../cairn/docs/roadmap.md"}` → **exit 1 DENIED** — same file, inside the envelope
- `{"file_path":"/Users/.../cairn/.claude/skill-runs/carrier-hierarchy-refocus/intent-challenge.md"}` → **exit 1 DENIED** — this challenge's own report write, inside the envelope (`^\.claude/skill-runs/.*`)

Every absolute-path write in an operator session is currently being denied and proceeding only because exit 1 is non-blocking. Flip deny→2 with no path normalization and the repaired hook **blocks every Write/Edit in any session with `mode: operator`** — including this feature's remaining construction the moment the fix lands in the working tree (the hook re-executes the live script per call). The unit tests and smoketest will go green on crafted relative-path payloads (the existing fixtures use `foo/bar.py`) while the live repo is unwritable — a liveness test passing against a hook that blocks known-GOOD input, the mirror image of wrong-if clause 1, which the contract does not currently catch. Same class: `.slice-system/`-prefixed consumer paths (CLAUDE.md safety rule) become real blocks. must-satisfy 109 as specified is therefore wrong-making, not just insufficient.

## (b) Legitimate exit-1 dependents

- Unit tests asserting `== 1` (gh#35's list, incl. `tests/unit/test_postinstall_validator.py:196` "OUTSIDE envelope → role_guard exits 1") — covered by Specification line 33 ("unit tests corrected"), all under `tests/.*` in scope. OK.
- `checks/premise_guard.py:8` — "Exit codes (mirror role_guard.py)" becomes FALSE after the flip (role_guard will have no exit-1 path), while the contract says premise_guard "retained unchanged" (Spec line 34). A misleading mirror-docstring is the exact planted-lie shape D2 used (`operator-field-notes-2026-06-02.md:30-32`). Needs a one-line docstring edit + a carve-out from "unchanged".
- `docs/operational-reference.md:220` ("Exit codes (mirror role_guard.py)") and the role_guard docstring's own line 13 — both need the same editorial pass; in scope, unmentioned in Specification.
- `scripts/smoketest_hooks.sh:13` already distinguishes role_guard exit 2 as legitimate runtime behaviour — no exit-1 dependence. OK.

## (c) New contradictions from the revision

1. **Feature-Local Invariants line 57 residue**: "envelope-diff step lands with/before role_guard *deletion*" — references the abandoned deletion; conflicts with must-not-violate 119 (role_guard + envelope + registrations remain live). Same residue class as the rev-2 scope-statement block.
2. **Consumer-change denial**: Risk Surface concedes "consumers that silently relied on the fail-open will start seeing denials" yet concludes "no upgrade note needed", while Explicit Scope-Out and escalate-when still assert "no consumer-facing script behaviour changes intended". The repair's express purpose is a consumer-propagating behaviour change (dist ships the fixed hook); escalate-when clause 3 is a tripwire guaranteed to fire or be ignored. With the (a) finding un-fixed, the consumer impact is not "denials where envelopes are stale" but "denials everywhere an operator-mode envelope exists".

## verdict

**challenge-blocked** — must-satisfy 109 / Specification line 33 as written. The exit-code flip is necessary but converts a fail-open no-op into a deny-everything gate, demonstrated live against in-envelope absolute paths.

Required revision:
1. The fix commit must pair deny→2 with **path normalization** (relativize `file_path` against CAIRN_ROOT before matching, mirroring reversibility-guard's prefix handling; decide `.slice-system/` stripping explicitly) — and the unit/liveness tests must assert BOTH directions: known-bad input blocked (exit 2) AND a known-good **absolute** in-envelope path allowed (exit 0). Add the allowed-direction assertion to wrong-if.
2. Fix FLI line 57 ("role_guard deletion" → repair sequencing or drop the clause).
3. Reconcile the consumer language: amend Scope-Out/escalate-when to name the intended enforcement change, and either restore the upgrade note or justify its absence against the now-real denial surface.
4. Editorial pass on the stale exit-code docs: `role_guard.py:13`, `premise_guard.py:8` (carve out of "retained unchanged"), `docs/operational-reference.md:220`.

---

# Final verdict (revision 5, 2026-06-10)

All four revision-4 items verified against the live intent:

1. **(a) resolved** — Specification line 33 pairs deny→2 with file_path normalization against CAIRN_ROOT in the same commit, names today's masked deny-everything state, keeps `.slice-system/` deliberately un-stripped (consistent with the CLAUDE.md canonical-paths rule; those denials become real and are documented intended behaviour), and requires both-direction unit tests. must-satisfy 110 contracts the absolute-allow direction; wrong-if 123 names the deny-everything inversion (closing the gap my live demo exposed: green relative-path fixtures over a bricked repo); FLI line 57 binds "the flip never lands without the normalization fix in the same commit". Premise 2's label now states the paired fix and survives the counterfactual.
2. **(c1) resolved** — FLI line 57's stale "role_guard deletion" sequencing removed.
3. **(c2) resolved** — Scope-Out line 65 names the repair as the single INTENDED consumer-facing enforcement change with the envelope-audit upgrade note as a deliverable; escalate-when 129 reworded to trip only on UNINTENDED changes beyond it; "no upgrade note needed" deleted from Risk Surface.
4. **(b) resolved** — stale exit-code docs (`role_guard.py:13`, `premise_guard.py:8` mirror line, `operational-reference.md`) contracted for update, with an explicit docstring-only carve-out reconciling Specification line 34's "retained unchanged".

No new contradictions found. Residual edge noted for construction (non-blocking, fail-closed by design): paths outside CAIRN_ROOT cannot relativize and will match no envelope pattern → denied; acceptable and consistent with the envelope's purpose.

**challenge-pass.** Construction may begin. The close-review should hold: (i) wrong-if 123 verified against a real absolute-path write, not only the unit fixture; (ii) the upgrade note ships in the refocus ADR / upgrade doc; (iii) gh#35 closure cites both paired defects (exit code AND path shape), since the issue as filed documents only the first.

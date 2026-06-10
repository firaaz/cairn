# Close-review — carrier-hierarchy-refocus

Fresh-context review of `git diff 2d24db1..70b3884` (6 commits, 65 files, +1076/-308) against
`.claude/skill-runs/carrier-hierarchy-refocus/intent.md` (challenge-pass at revision 5).
Reviewer had no access to the construction conversation; every check below was run live.

**Verdict: close-review-blocked** — one sustained finding (F1). Everything else passes.

---

## contract-clause-check

### must-satisfy

| # | Clause | Result | Evidence |
|---|--------|--------|----------|
| 1 | refocus ADR exists (hierarchy, receipts, retirements, own contract block) | **PASS** | `docs/adr/carrier-hierarchy-and-process-diet.md` — frontmatter `contract:` lines 6–19; D1 hierarchy (44–52), D2 receipts (54–56), D3 retirements (58–64) |
| 2 | validator fails a live-constraint ADR lacking `contract:` | **PASS** | `check_adr_carrier` in `scripts/validate_architecture.py` (Check F); contrived red case `test_missing_declaration_fails` in `tests/unit/test_adr_carrier_contract.py:35`; live corpus asserted clean (`test_live_corpus_passes:61`) |
| 3 | smoketest: each surviving hook blocks its known-bad input | **PASS with note** | `scripts/smoketest_hooks.sh:84–131`. Enforcers (role_guard, reversibility-guard) prove BLOCK (exit 2 / deny decision). reality-check proves corrective reformat; the carrier proves marker emission — neither has a deny path by design, so the clause as drafted is literally unsatisfiable for them. Adjudicated: per-hook-class interpretation is the strongest available proof; drafting imprecision, not a miss. ADR D8 prose slightly overclaims ("denied") vs what the smoketest asserts for the non-gating hooks. |
| 4 | role_guard deny exits 2, unit test + smoketest | **PASS** | `checks/role_guard.py:180,199,215`; `test_role_guard_repair.py:68–74,120–122,134–136`; smoketest `PASS liveness role_guard.py deny`. Re-verified live by this review: out-of-envelope absolute write against the REAL repo envelope → rc=2. |
| 5 | absolute in-envelope path allowed (exit 0), unit test | **PASS** | `_normalize_path` (`role_guard.py:57–68`); `test_role_guard_repair.py:77–83`; smoketest allow-absolute. Re-verified live by this review against the real envelope: absolute write to `docs/roadmap.md` → rc=0. `.slice-system/` deliberately not stripped (`test_slice_system_prefix_is_not_stripped:97–106`). |
| 6 | close-review brief instructs envelope-diff vs execution-scope | **PASS** | `.claude/skills/cairn-intent/SKILL.md:68` |
| 7 | handoff ≤6 active threads, amended test_handoff_contract.py green | **FAIL — F1** | Handoff carries 5 threads (≤6 OK); `test_coverage_open_issues` deleted, `test_handoff_is_dieted` added. But `test_pointers_resolve` is RED on every committed tree from 25bb90f through HEAD: handoff line 17 points to `docs/plans/2026-06-07-spec-elicitation-discipline.md`, which is an UNTRACKED file in the main worktree and absent from the commits. Verified in a clean worktree at 70b3884: `1 failed, 4 passed`. The submitted "703 passed" HEAD evidence ran on the dirty tree, which masked this. |
| 8 | every live-constraint ADR carries a contract block | **PASS with note** | Mechanically enforced by Check F; corpus at HEAD: 22 `contract:` blocks, 14 `carrier: rationale-only`, superseded/`superseded-by` exempt, `index.md` not parsed as ADR; validator ALL CHECKS PASSED (48 ADRs). Note: the clause's universal-set says the set is "enumerated in the refocus ADR" — no prose enumeration exists; the enumeration is the corpus itself under Check F. Mechanical carrier is strictly stronger than the promised prose list; ADR append-only prevents retrofitting. Adjudicated acceptable, recorded. |
| 9 | gh closures citing the refocus ADR | **NOT EXECUTED — per except** | Operator-bound per the clause's own `except`; close list surfaced, awaiting operator pick. Prepared citation adequate: commit 3050df1 body and ADR D4 both cite BOTH paired defects (exit-1 non-blocking AND absolute-path/relative-regex mismatch), satisfying challenge hold (iii). Remains an open obligation at close. |

### must-not-violate

| Clause | Result | Evidence |
|--------|--------|----------|
| ADR append-only | **HELD** | db2ffe9's 33 ADR edits are frontmatter-only insertions immediately after `status:` (spot-checked `cairn-substrate-and-fastmcp-superseded.md`, `intent-management-loop.md`); superseded ADRs untouched; reversibility-guard live throughout |
| pytest green at every retirement commit | **VIOLATED at 25bb90f — F1** | Retirement commit 25bb90f (handoff diet): `1 failed (test_pointers_resolve), 696 passed` in a clean worktree — construction-introduced (the unresolvable pointer landed in that commit). c775a0e: `1 failed (test_coverage_open_issues), 683 passed` — pre-existing: the same test fails identically at base 2d24db1 (it queries live gh state; exactly the flakiness D6 removed), so not attributed to construction. |
| named mechanisms remain live | **HELD** | role_guard repaired, registrations + `.claude/active-envelope.yaml` intact (envelope refreshed to this intent's scope, includes self-pattern); `checks/premise_guard.py` diff is docstring-only (the contracted carve-out); cairn-intent skill, both checkpoint agents, using-cairn carrier, contract tests all present and green |

### wrong-if

1. liveness false-pass — **not triggered** (re-verified live, not from fixture output alone).
2. deny-everything inversion — **not triggered**; challenge hold (i) closed by this review's own run: real absolute-path write, real repo envelope, rc=0.
3. deleted mechanism's tests surviving as skips — **not triggered**: `test_coverage_open_issues` deleted outright; the 2 suite skips are pre-existing environment conditionals (`claude` CLI absence etc.).
4. test_handoff_contract.py red after the diet — **TRIGGERED** (F1, clean-checkout red at 25bb90f..HEAD).

### Challenge holds (revision-5 obligations)

- (i) inversion verified against a real absolute-path write — **done by this review** (real envelope, both directions).
- (ii) consumer envelope-audit upgrade note shipped — **yes**: ADR D4 (bold note, line 70) + `docs/roadmap.md:13`.
- (iii) gh#35 closure cites both paired defects — **prepared**: commit 3050df1 message + ADR D4 "both halves"; execution operator-bound.

---

## findings

**F1 (blocking).** The dieted handoff's thread 3 points at an uncommitted file. `tests/unit/test_handoff_contract.py::test_pointers_resolve` is red in any clean checkout of 25bb90f, db2ffe9, or HEAD (70b3884). This fails must-satisfy 7, triggers wrong-if 4, violates "pytest green at every retirement commit" at 25bb90f, and violates the handoff's own frontmatter wrong-if ("any pointer fails to resolve on read"). The green HEAD evidence was an artifact of the dirty working tree.

**F2 (non-blocking, recorded).** Sequencing defect: the INV-001 `fix:`-verifier prune (`_verify_fix_commit` → pass-through) landed in 7d2f8af, one commit AFTER the `fix:`-prefixed 3050df1 it was needed for. At 3050df1 the validator is red (Check D, INV-001) and 10 validator-e2e tests fail (verified in worktree: `11 failed`). 3050df1 is not a retirement commit, so the clause's letter is not violated, but bisectability is broken mid-sequence — the exact property FLI-1 protects. The prune itself is legitimate (`fix:` sweep-scope machinery retired at M4; Spec line 37 "paperwork rules pruned"). No history rewrite recommended on a shared tree; record as residual.

**F3 (non-blocking notes).**
- `docs/ARCHITECTURE\.md` was added to `execution-scope` after challenge-pass without re-challenge (forced by validator Check B: the new firm ADR must bind an invariant → INV-013). Not a premise/must-satisfy change, so the SKILL's D2 delta-trigger did not formally fire; still a widening of the envelope the challenge reviewed. Single declarative file, edit is the INV-013 registry entry only — adjudicated tolerable, should have been flagged at the time.
- Handoff frontmatter gained two lines (≤6 cap, no-mirror) despite Spec line 38 "contract frontmatter unchanged" — strengthens consistently with D6; minor spec drift.
- Commit db2ffe9's message claims "19 contract blocks"; corpus shows 22 (pre-existing blocks counted differently). Cosmetic.
- Test fixtures in 4 test files gained carrier declarations so synthetic corpora pass Check F — `tests/.*` in scope, necessary, fine.

---

## evidence-adequacy-check

Contract depth vs diff size: proportionate — 9 must-satisfy / 3 must-not-violate / 4 wrong-if clauses plus a five-round challenge history against a 65-file, +1076/-308 diff. No D3 thin-contract floor issue.

Evidence as submitted: pytest 703-pass, validator ALL-PASS, smoketest all-PASS at HEAD are genuine but were run on a **dirty working tree**, which masked F1; per-retirement-commit pytest output (a contracted evidence item) was not supplied. This review generated it in clean worktrees and found the reds at 25bb90f and 3050df1. **Inadequate as submitted** — clean-checkout runs are required for the handoff contract specifically, since untracked files satisfy pointer resolution.

## scope-check

`git diff --name-only 2d24db1..HEAD` — all 65 changed paths match the contract's `execution-scope` patterns (verified per-pattern; includes the post-challenge `docs/ARCHITECTURE\.md` entry, see F3). No out-of-scope file touched. `.claude/settings.json` (the deletion-era risk) untouched, correctly. Note for rework: `docs/plans/.*` is NOT in scope, so "commit the missing plan doc" is not an in-scope fix for F1.

## required rework

Make handoff thread 3 resolve in the **committed** tree, in scope: repoint the line to a committed pointer (gh issue or existing committed doc) or drop it (4 threads still satisfies pointer/state/diet assertions). Alternatively the operator commits `docs/plans/2026-06-07-spec-elicitation-discipline.md` outside this intent (out of execution-scope — operator action, not constructor's). Then run `tests/unit/test_handoff_contract.py` in a CLEAN worktree at the new HEAD and resubmit the diff for fresh review. Record F2 in the close evidence as a known bisect gap (no rewrite).

## residual risk (carried to sign-off)

- Clause 9 (gh closures) open until the operator executes the surfaced close list; citation prepared.
- F2 bisect gap at 3050df1 stands in history.
- Real envelope enforcement is now live for every `mode: operator` session and consumer; the audit-before-pull note is shipped but unconfirmed downstream.
- Clause 3's "block" semantics for non-gating hooks (reality-check, carrier) rest on the per-class interpretation recorded here.

---

# Re-review — rework at 4d8738d (2026-06-10)

## F1 (blocking) — RESOLVED

Commit 4d8738d deletes exactly one line: the handoff thread pointing at the
uncommitted `docs/plans/2026-06-07-spec-elicitation-discipline.md`. The in-scope
option named in the rework instruction; the diff touches only `.claude/handoff.md`
(execution-scope match). Handoff now carries 4 threads, all pointers committed
(2 ADR paths, 2 commit SHAs).

Evidence re-generated independently by this review in a fresh detached worktree at
4d8738d (`git worktree add` + `uv run`):

- `uv run pytest -q` → **703 passed, 2 skipped, 2 xfailed** (clean tree — no
  dirty-tree masking this time; `test_pointers_resolve` green against the
  committed handoff)
- `uv run python scripts/validate_architecture.py` → **ALL CHECKS PASSED**
  (13 invariants, 48 ADRs)
- `bash scripts/smoketest_hooks.sh` → **exit 0**, all liveness lines PASS
  including `role_guard.py deny` and `role_guard.py allow-absolute`

must-satisfy clause 7 now holds on the committed tree; wrong-if 4 no longer triggers.

## F2 + retirement-commit reds — ACCEPTED AS DOCUMENTED RESIDUAL

The historical defects stand and are NOT repaired:

- 3050df1: validator red (INV-001, fix-verifier pruned one commit late) + 10
  downstream test failures — non-retirement commit, FLI-1 bisectability damaged.
- 25bb90f: `test_pointers_resolve` red — a retirement commit, so the
  must-not-violate clause "pytest green at every retirement commit" is violated
  in the permanent record.

Adjudication: this reviewer explicitly judges these **acceptance-worthy as
documented residual risk**, for the operator to ratify at sign-off. Grounds:
(1) the defect class is bisectability of two intermediate commits, not end-state
correctness — the end state is verified green in a clean checkout; (2) the only
repair is history rewrite on a shared working tree operated by concurrent
sessions, which this review recommended against and which would trade a recorded,
bounded defect for a live coordination hazard; (3) both reds are precisely
characterized above (commit, test, cause), so the gap is auditable, and close.md
will state it per the rework note. The clause violation at 25bb90f remains a
fact; acceptance is the operator's call, made with it named rather than hidden.

## Verdict

**close-review-pass** — conditional on the operator accepting the named residual
(historical reds at 3050df1 and 25bb90f) at sign-off, and with clause 9 (gh
closures, operator-bound) still open as a tracked obligation, citation prepared.

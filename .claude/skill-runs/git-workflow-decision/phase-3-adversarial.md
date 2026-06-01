# Phase 3 — Adversarial Stress Test (git-workflow-v1)

Mandate: break Approach A. Every load-bearing claim re-verified against real code + **live `dev` history** (not prior-agent summary). Verdict per claim: VERIFIED / BELIEVED / FAILED.

## Claim 1 — `--no-merges` walk (F2's resolution) — **VERIFIED, and live-confirmed**
`validate_architecture.py:367`: `["git", "log", range_arg, "--no-merges", "--format=...", "--name-only"]`. Fixed start: `range_arg = f"{base_sha}..HEAD"` (`:365`) with `base_sha = binding-effective-from = 2fb83f6` (`ARCHITECTURE.md:17`). Walk is `2fb83f6..HEAD --no-merges`, not first-parent.
**Stronger than the steelman claimed:** `dev` *already* carries 2 merge commits since `2fb83f6` — `Merge remote-tracking branch 'origin/dev'` and `merge: feature/compression-followup …`. WITHOUT `--no-merges` both appear in range; WITH it both vanish (reproduced). The lowercase `merge:` one matches `cc_re` (`:408`) as bare type `merge`, and `merge:` is **absent** from `_FALLBACK_REGISTRY` (`:273-285` lists slice/handoff/sweep/bootstrap/feat/docs/fix/chore/test/design/plan — no `merge`/`Merge`). So dropping `--no-merges` reds the walk *today*, not hypothetically. `--no-ff`'s default `Merge branch 'feat/<id>'` is equally unregistered. **F2 is real and currently load-bearing.** Validator runs clean (exit 0) only because the flag holds.
→ **A's INV-001 story stands**, conditional on pinning `--no-merges` as contract. Must-pin #1 is non-negotiable: a one-flag regression reds every historical + future merge.

## Claim 2 — Handoff append location (F1) — **VERIFIED**
`phase-4-tdd.md:18`: "Append a one-line entry to `.claude/handoff.md`'s Pointers section" on HEAD = `feat/`. `:24`: commits it (`chore(<feature-id>): phase 4 — sweep + handoff`) — Phase 4 IS allowed to commit in TDD path. Test: `tests/unit/test_handoff_contract.py`. `test_no_narrative_prose:73-77` asserts `len(blocks)==1` where blocks = `body_raw.strip().split("\n\n")`; `:70` 120-char cap; `:71` multi-sentence ban. Live handoff body = **1 block / 37 lines** (reproduced) — exactly at contract. A merge-conflict marker (`<<<<<<<`/`=======`) inserts blank-separated regions → ≥2 blocks → red; `>>>>>>>` lines also fail `test_pointers_resolve:125` (no recognized pointer). **F1 collision is real but latent solo** (single `--no-ff` lands clean by accident); catastrophic surface is deferred-D4 concurrent merge. A does not fix it — correctly scoped as D4 open question.

## Claim 3 — Supersession legality — **VERIFIED**
`reversibility-guard.sh:85`: `if echo "$OLD" | head -1 | grep -qE '^(status:|superseded-by:|superseded_by:|firmness:)'; then exit 0`. A frontmatter Edit whose `old_string` line 1 begins `superseded-by:` is ALLOWED on the three target ADRs. **Caveat (adversarial):** `supersedes-sections:` is **NOT** in the allowed-first-line set — an Edit adding that field must lead with `superseded-by:`/`status:`/`firmness:` as line 1, or it's denied (escape hatch `ADR_EDITORIAL_FIX=1`, additive-only, `:95-100`). New-file Write: `:59-67` denies `docs/adr/*.md` only `if [ -f … ]` (exists); `git-workflow-v1.md` doesn't exist → Write permitted. **Legal, with a sequencing pin: lead supersession edits with an allowed frontmatter key.**

## Claim 4 — No merge guard (F5) — **VERIFIED, un-backstopped**
`grep merge|--no-ff|squash|--ff` over `role_guard.py` + all `checks/*.sh` = **zero matches**. `reversibility-guard.sh:21-31` blocks only `rm -rf`, force-push, `reset --hard`, `clean -fd`, `DROP`. `role_guard.py:25` `WRITE_TOOLS = {"Write","Edit","MultiEdit","NotebookEdit"}` — **Bash absent**; `:143` and `:168` both early-return for non-write tools, so `git merge` (a Bash call) is never seen. Nothing enforces `--no-ff`, blocks `-ff`/squash, or detects a stranded `feat/`. D2 rejects squash in prose only. **F5 is A's worst exposure — pure-instruction enforcement, no mechanical backstop.**
*Cheap guard feasibility:* a `PreToolUse` Bash matcher in `reversibility-guard.sh` (same `case "$CMD"` block, `:21`) can deny `git merge` lacking `--no-ff` and deny `--squash`/`-ff`. Trivially feasible (one case arm, no new file). Out of committed scope but the obvious D6-graduation hook. Cannot detect *forgotten* merge (no command to intercept) — that stays advisory.

## Steel-man B (final) — does ANY solo scenario favor B?
Re-checked. B = A + physical worktree isolation. B fixes **nothing** A doesn't: F1 collides at the shared `dev`/`handoff.md` merge target (not the working tree); F3 `/tmp/<id>-baseline` is global, outside the worktree boundary. B *worsens* F5 (adds un-guarded create/teardown; `rm -rf`/`clean -fd` blocked → fiddly dirty-worktree removal) and re-opens fail-open envelope (`role_guard.py:150` `env is None → allow`) per fresh worktree unless copied. **The single solo scenario where B wins:** one long-running multi-day feature whose dirty tree would otherwise block all other work on `dev` — physical isolation beats stash-juggling, and create/teardown amortizes over days. That is real but **not today's state** (solo, one feature at a time). B's win is exactly the deferred-D5 trigger; gating it there is correct. **No solo scenario justifies B's standing overhead now.**

## Assumption audit

| Assumption | Status | How-checked | Degradation if wrong |
|---|---|---|---|
| Walk uses `--no-merges` | **VERIFIED** | `validate_architecture.py:367` + reproduced WITH/WITHOUT on live range | If dropped: every merge reds INV-001 immediately (2 already live) |
| Walk start fixed at `2fb83f6` | **VERIFIED** | `ARCHITECTURE.md:17`, `:365` range_arg | Moving start re-walks more history; cost only |
| `merge`/`Merge` unregistered | **VERIFIED** | `_FALLBACK_REGISTRY:273-285` — no merge key; `merge:` matches cc_re | Without flag, "prefix not in registry" red |
| Phase 4 appends handoff on `feat/`, commits it | **VERIFIED** | `phase-4-tdd.md:18,24` | — |
| `--no-ff` carries handoff to `dev` solo | **BELIEVED** (mechanism sound, not run) | 3-way merge logic + 1-block live body | Solo: clean. Concurrent: conflict → red (F1/D4) |
| Frontmatter `superseded-by:` Edit allowed | **VERIFIED** | `reversibility-guard.sh:85` | If led by `supersedes-sections:`: denied → use allowed key first line |
| New ADR Write allowed | **VERIFIED** | `:59-67` `-f` existence gate | — |
| No merge guard exists | **VERIFIED** | grep = 0; `WRITE_TOOLS:25` Bash-absent | F5: `-ff`/squash slip irreversibly destroys 4-commit trail |
| `--no-ff` preserves phase SHAs | **BELIEVED** (git semantics, not run) | D2 design intent; merge ≠ rewrite | Rebase instead → SHAs dangle vs SNAPSHOT_SHA (F6) |
| `/tmp/<id>-baseline` global, B doesn't fix | **VERIFIED** | `SKILL.md:30,36` path has no worktree qualifier | F3 clobber under concurrency (D4) |

## Go / No-go on A
**GO.** All four load-bearing claims VERIFIED against real code; two (F2, F5) empirically confirmed live, not just believed. No claim FAILED. A is the correct committed direction; B/C stay deferred-gated as scoped. Two items are BELIEVED-not-run (`--no-ff` carries handoff; `--no-ff` preserves SHAs) — both rest on standard git semantics, acceptable to commit, but the ADR's first real merge is the verification.

**Newly-required pins (beyond the 4 the prior phase named):**
- P5: supersession Edits MUST lead `old_string` line 1 with `status:`/`superseded-by:`/`firmness:` — `supersedes-sections:` as line 1 is denied by `reversibility-guard.sh:85`.
- P6 (record, don't build): the F5 backstop is a one-arm `case` in `reversibility-guard.sh:21` denying `git merge` without `--no-ff` and denying `--squash`/`-ff` — flag as the natural D6 graduation; cannot catch a *forgotten* merge.
- P7: adopt `git log --first-parent dev` for `/catchup` + m5 cut-point (C's carry-over) to neutralize F4's 25%-bubble legibility tax.

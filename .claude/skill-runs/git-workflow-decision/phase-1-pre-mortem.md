# Phase 1 — Pre-Mortem: git-workflow-v1

Imagine `feat/<id>` + `git merge --no-ff` shipped and broke. Failures named before solutions. Exposure = does committed narrow scope (D1/D2/D3, solo) trip it, or only deferred concurrency (D4/D5)?

## F1 [technical] — handoff append lands on the wrong branch, then collides on merge
**Trigger:** Phase 4 (`phase-4-tdd.md:18`) appends a Pointers line to `.claude/handoff.md` on whatever branch HEAD is on — i.e. `feat/<id>`. `feature-slice-model` D1 says handoff lives *on dev*.
**Mechanism:** Append is committed in the phase-4 `chore:` commit on the feat branch. `--no-ff` merges it back, so the append *does* reach dev — solo it works by accident. With 2 concurrent features both branched off the same dev SHA, each appends to its own copy; the second `--no-ff` merge is a textual conflict in the Pointers block, or (if auto-resolved) duplicates/reorders lines. `test_handoff_contract.py:74` requires `len(blocks) == 1` (one continuous bullet list); a conflict-marker or blank-separated re-merge yields ≥2 blocks → red. `:70` 120-char cap and `:71` multi-sentence ban also fire on any merged-in prose.
**Severity:** graceful (caught by test, but only at merge time, post-audit — phase-4 already returned OK; see L-011/gh#4 audit-escape class).
**Exposure:** D1 latent solo (works by accident); **catastrophic surface is deferred D4** (concurrent merge).

## F2 [integration] — merge commit subject is an unregistered prefix that INV-001 silently tolerates
**Trigger:** `--no-ff` writes subject `Merge branch 'feat/<id>'` to dev.
**Mechanism:** INV-001 git-log-walk (`validate_architecture.py:367`) runs `git log ... --no-merges`, so the merge commit is **excluded** — `_FALLBACK_REGISTRY` (`:266`) never sees `Merge`. No rejection today. The risk is inverted: the guard's coverage gap is load-bearing and undocumented. If any future change drops `--no-merges`, `cc_re` (`:408`) fails to match `Merge` → "prefix not in registry" red across every historical merge. The ADR must pin `--no-merges` as the contract that makes `--no-ff` legal.
**Severity:** graceful now; catastrophic-on-regression (a one-flag change reds the whole walk).
**Exposure:** **D2 solo** — first `--no-ff` merge creates the unwalked commit; concurrency not required.

## F3 [technical] — `/tmp/<feature-id>-baseline-failures.txt` + `SNAPSHOT_SHA` clobber
**Trigger:** Two `cairn-tdd-feature` runs (or one re-run) share the `/tmp/<feature-id>-...` path (SKILL.md:30,36,56); both branch off the same dev SHA so `SNAPSHOT_SHA` is identical but baselines differ once feature A merges first.
**Mechanism:** Feature B's Phase 4 diffs against a baseline captured pre-A-merge; A's new tests now count as "new failures" mis-attributed to B (the self-attribution failure mode `phase-4-tdd` regression language guards against). Concurrent writes to the same `/tmp` file race; tmp is not branch-scoped.
**Severity:** graceful (wrong attribution, surfaced in sweep-notes) but corrodes the audit's authority.
**Exposure:** **deferred D4** (needs concurrency / out-of-order completion); solo single-run is safe.

## F4 [scale] — dev history shape: 5 commits/feature degrades log readability + cut tooling
**Trigger:** Every feature lands 4 phase commits + 1 merge commit on dev.
**Mechanism:** `/catchup` and `release`/`dist/` cut (`m5-plugin-distribution`, INV-012 sha-pin) read linear dev history; `--no-ff` makes it a sequence of merge bubbles. `_git_subjects_in_range` (`:362`) already `--no-merges`-filters so INV-001 is fine, but human/`/catchup` log-walks and any `git log --oneline` cut-point selection see 25% noise commits. Not a correctness break — a legibility tax that scales linearly.
**Severity:** graceful.
**Exposure:** **D1/D2 solo** — every feature, immediately; worsens with volume, not concurrency.

## F5 [adoption] — operator-owned merge (interim D6) has zero guard
**Trigger:** Operator forgets to merge (work stranded on `feat/`), merges with `-ff`/squash (destroys the 4-commit audit D2 exists to preserve), or branches a new feature off un-merged dev.
**Mechanism:** `reversibility-guard.sh:21-31` guards only `rm -rf`, force-push, `reset --hard`, `clean -fd` — **no merge-direction or merge-omission guard**. `role_guard.py` gates Write/Edit paths, not `git merge`. Nothing enforces `--no-ff`, nothing detects an un-merged feat branch, nothing blocks `-ff`. D2 rejects squash *in prose*; the hook layer is silent. Pure-instruction enforcement (gh#17 class).
**Severity:** catastrophic for the audit trail (squash/ff is irreversible once dev moves on); graceful for the forgotten-merge case.
**Exposure:** **D6-interim solo** — single operator, single slip; the whole committed model rests on operator discipline with no mechanical backstop.

## F6 [integration] — feat branch off stale dev re-anchors phase SHAs vs SNAPSHOT_SHA
**Trigger:** Operator branches `feat/<id>` off a dev that later advances; D2 rejects rebase-onto-dev precisely because it rewrites phase SHAs that `intent.md`/sweep-notes pin against `SNAPSHOT_SHA`.
**Mechanism:** `--no-ff` preserves SHAs (correct), but if the operator rebases to "tidy" before merging (no guard forbids it), every phase SHA in intent.md/sweep-notes dangles; F3's baseline diff and any commit-pointer in handoff (`test_handoff_contract.py:122`) fail to resolve.
**Severity:** graceful (broken pointers detectable) but silent until read.
**Exposure:** **D1/D2 solo** (single operator can rebase); amplified under D4.

# Cairn refocus: constraints out of prose, ceremony down to what has receipts

> Operator-approved plan (plan mode, 2026-06-10). Pinned verbatim as the intent's source document.

## Context

Cairn's problem statement is sound (session-boundary decorrelation, empirically backed). The execution has inverted: 48 ADRs + 63 plans + trials + a 40-thread handoff (~38k doc lines) wrap ~7k LOC of machinery; 32% of 6 weeks of commits are handoff churn; the central mechanical enforcer (`role_guard.py`) failed open for weeks unnoticed while the document apparatus grew. The operator asked: don't patch defects — interrogate whether the mechanisms (ADR-as-carrier, decision arcs, trials, handoff) are the right solution shape at all.

## Findings the plan rests on

**1. ADR is the wrong carrier for constraints; cairn's own practice already proves it.**
Every live constraint that actually works has escaped prose into a mechanical carrier: identifier-scheme → `tests/unit/test_identifier_scheme_contract.py`; carrier-contract → `checks/using-cairn-carrier.sh`; invariant-binding → `scripts/validate_architecture.py`; intent-loop → the `cairn-intent` skill. The prose-only ADRs are rationale/narrative. ~40% of the corpus is superseded/dead weight; the selection-ladder doc is the symptom of carrier overload. ADR is *right* for rationale, provenance, and falsification tripwires — *wrong* as the thing an agent must heed.

**2. Only two mechanism families have receipts.**
- Fresh-context checkpoints (intent-challenge, close-review): ~3 live catches incl. a semantic ADR over-read no mechanical gate could see (`docs/operator-field-notes-2026-06-01.md:28-36`).
- Trials *when they conclude something*: B caught real drift; E retired the heavy band and the four-phase pipeline.

No-evidence/untested: handoff thread content (only `/catchup` reads it), mechanical `premise_guard.py` (exit 0 on its motivating slice-#25 lie), heavy-band contract (never instantiated), `dogfood-log.md` (zero entries), role_guard envelope (failed open, nobody noticed — empirically not load-bearing). The shipped intent-challenge is primed (slice-#25 hard-coded); every "front gate is strong" datum used de-primed stand-ins.

**3. Governing principle going forward:** a mechanism earns its place by a logged catch, not by completing its ceremony. Decisions are carried by the strongest carrier that can hold them.

## The carrier hierarchy (the answer to "is ADR the right way")

1. **Never-violate rules → hooks** (`checks/`) — fire without being loaded; must fail closed; must have a liveness test.
2. **Corpus/structural invariants → contract tests + validator assertions** (the `test_handoff_contract.py` pattern) — red on drift.
3. **Workflow decisions → skills/commands** — the decision *is* the default path.
4. **Must-know-before-acting guidance → CLAUDE.md line** (size-capped, pointer to ADR).
5. **Rationale/history → ADR**, with a mandatory `contract:` block naming its mechanical carrier (levels 1–4). New validator rule: a live-constraint ADR with no named carrier fails validation. (6/47 already have `contract:` blocks — this generalizes existing practice.)

## Changes

### A. Record the refocus (1 ADR, superseding)
- New ADR `docs/adr/carrier-hierarchy-and-process-diet.md`: adopts the hierarchy, the receipts principle, and the retirements below. Supersedes/amends: `intent-management-loop.md` (D7/R2 conditions resolved), thin-substrate trial machinery, `using-cairn` four-phase references.
- Decorrelation for this decision itself: one fresh-context adversarial attack on this plan (intent-challenge form) before the ADR commits — honoring the principle without an 8-phase arc. *Note: operator's standing rule routes decision-weight changes through `/decision`; this plan proposes the lean form as its replacement — flagged as an explicit operator call at approval time.*

### B. Cut process surface
- **One loop.** `cairn-intent` is the operating mode (Trial E already retired four-phase "with conditions"). Mark `cairn-tdd-feature` legacy in CLAUDE.md/skill description; stop maintaining its per-phase agents as the default path.
- **Handoff diet.** Collapse `.claude/handoff.md` to ≤6 active threads (load-bearing only); everything else lives solely as gh issues. `/catchup` and `test_handoff_contract.py` unchanged in shape — just fewer lines.
- **Retire (delete or mark superseded):**
  - `/decision` 8-phase protocol → replaced by "write ADR + one fresh-context attack" (`commands/claude-code/decision*` marked legacy; keep doc for provenance).
  - Trials/firmness apparatus as standing machinery (trial plans stay as history; no Trial F).
  - `checks/premise_guard.py` mechanical gate → demote to optional lint or delete; premise-grounding is the challenge subagent's job (it's the thing with receipts).
  - `docs/dogfood-log.md` (empty schema), heavy-band contract template remnants.
  - `role_guard.py` per-write envelope enforcement + `.claude/active-envelope.yaml` → **delete**, replaced by a close-review step that diffs changed paths against the intent contract's envelope (observable in review, can't die silently). This resolves gh#35 by removing the mechanism rather than fixing it — it never demonstrably enforced anything. Tradeoff surfaced: loses per-write blocking; gains a check that's actually exercised every close.
- **Keep:** `reversibility-guard.sh` (works, has receipts), `cairn-intent` skill + challenge/close-review subagents, `using-cairn` carrier, contract tests, validator (pruned of paperwork-audit rules per the minimal set).

### C. Enforcer liveness (the role_guard lesson, structural not tactical)
- Every surviving hook gets a liveness assertion: `scripts/smoketest_hooks.sh` extended to assert each hook *blocks* a known-bad input (exit code + decision JSON), run in CI/pytest. An enforcer without a liveness test is documentation.

### D. Re-anchor the backlog
- Sweep the 35 open gh issues against the minimal mechanism set: close those serving retired machinery (likely candidates: #5 D1/D3 gates, #6 AGENT_ENVELOPE synthesis, #8 phase-3 fan-out, #9 retry/backoff, #12 heartbeat, #13 resume/run_id, #16, #18 triager, #28 caps — anything whose subject no longer exists). Keep defect-shaped and consumer-shaped issues. Each closure cites the refocus ADR.
- `docs/roadmap.md` rewritten to the minimal set + one new top item: **measure the production gate** — de-prime the shipped intent-challenge and get live (non-planted) data, since every existing "front gate works" datum used stand-ins.

## Changes (continued)

### E. ADR corpus hygiene (mechanical, one pass)
- Add `contract:` blocks to the ~14 live-constraint ADRs naming their carrier; validator rule enforces presence going forward. Superseded ADRs untouched (append-only stands).

## Critical files
- `docs/adr/carrier-hierarchy-and-process-diet.md` (new), `docs/roadmap.md`, `CLAUDE.md`
- `.claude/handoff.md`, `.claude/active-envelope.yaml` (delete), `checks/role_guard.py` (delete), `checks/premise_guard.py` (demote/delete)
- `.claude/skills/cairn-intent/SKILL.md` (absorb envelope-diff step into close-review)
- `scripts/smoketest_hooks.sh`, `scripts/validate_architecture.py` (liveness + contract-block rule; prune paperwork rules)
- `tests/unit/` — remove role_guard/premise_guard test files; add liveness tests; keep contract tests

## Verification
- `uv run pytest` green after each retirement step (tests deleted with their mechanism, never skipped).
- `scripts/smoketest_hooks.sh` proves each surviving hook blocks a known-bad input.
- `scripts/validate_architecture.py` passes with the new contract-block rule; intentionally-missing case reds.
- `/catchup` on a fresh session reads the dieted handoff in one screen.
- Fresh-context attack report on this plan committed alongside the ADR.

## Sequencing
1. Fresh-context attack on this plan → 2. Refocus ADR → 3. role_guard/envelope removal + close-review envelope-diff → 4. Hook liveness tests → 5. Handoff diet + loop consolidation → 6. Backlog sweep + roadmap rewrite → 7. ADR contract-block pass. Steps 3–7 are independent enough to land as separate small commits on a feature branch off `dev` (shared-worktree rule: check for live writers first).

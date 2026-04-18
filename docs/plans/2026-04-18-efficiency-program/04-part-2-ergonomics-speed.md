# Part 2: Ergonomics + Speed

**Date:** 2026-04-18
**Gates:** Part 0 ADR; some items depend on Part 1 agents
**Estimated:** ~6 slices
**Ports to:** Parts 3, 5

## Intent

Two thrusts:
1. **Ergonomics** — auto-detect state so the user never types phase numbers, mode letters, or `--advance` flags. Code-not-prose side effects so skills can't skip. `state.json` for near-instant catchup on SHA match.
2. **Speed** — shorten feedback loops via test-impact analysis, parallel test runs, background precommit, commit-message drafting.

## Part 2A — Ergonomics

### E1 — Auto-phase-detection in `/catchup`, `/handoff`, `/start-slice`

**Problem:** Three skills have phase-explicit forms (`/catchup phase 2`, `/handoff` phase auto but archive path is prose-driven, `/start-slice phase 3` or `/start-slice advance`). User has to recall which phase they're in.

**Change:** All three skills auto-detect phase from `.claude/current-slice/slice.yaml.status`. Explicit forms remain as escape hatches, rarely needed.

- `/catchup` — already auto-detects in the base form; default stays; tighten behavior so phase-explicit form is a rare override.
- `/handoff` — detect current phase, write the correct phase archive, flip status to next phase, commit. No argument needed.
- `/start-slice next` — canonical advance verb. Detects current phase, runs phase-boundary hardening (flip status, write archive = same as `/handoff`), enters the next phase. `/start-slice phase N` stays as escape hatch.

**Slice:** `part-2-s1-auto-phase-detect`.

---

### E2 — Code-not-prose side-effects

**Problem:** L-005 — `/handoff` reproducibly skipped side-effects on worker A because they were prose. Part -1 #4 added a verifier; this slice promotes the side-effects from prose to code.

**Change:** `/handoff` skill invokes `scripts/commit_handoff.sh`:
1. Read `slice.yaml.status` → determine current phase.
2. Build `handoff-phase-N.md` from templated sections.
3. Flip `slice.yaml.status` to next phase.
4. `git add` the three files (handoff.md, handoff-phase-N.md, slice.yaml).
5. `git commit -m "handoff: phase $N complete"` (using Part -1 #6 template).
6. Verify via Part -1 #4 script.

Skill prose is now a thin invoker; side-effects are mechanical.

**Slice:** `part-2-s2-code-side-effects`.

**Depends on:** Part -1 #4 verifier exists; Part -1 #6 commit templates exist.

---

### E3 — `state.json` + SHA-short-circuit catchup

**Problem:** `/catchup` re-reads ~30k tokens even when nothing changed since last session. Roadmap item #3 — pulled forward.

**Change:** `handoff.md` narrative stays. Alongside it, `state.json`:
```json
{
  "schema_version": 1,
  "sha": "af660a5",
  "phase": "1-intent",
  "slice_id": "identifier-scheme/slice-and-feature-rename",
  "last_action": "Phase 1 intent committed; next /start-slice phase 2",
  "next_step": "/start-slice next",
  "features_active": ["identifier-scheme", "v1-defense-d3"],
  "timestamp": "2026-04-18T14:23:11Z"
}
```

`/catchup` flow:
1. Read `state.json`.
2. `git rev-parse HEAD` → compare to `state.sha`.
3. If match → print `state.last_action` + `state.next_step`. STOP. No Tier 1 read.
4. If mismatch → standard Tier 1 / Tier 2 flow.

Typical case (resumed after a fresh session, no intervening commits): catchup becomes a one-liner. Seconds.

**Slice:** `part-2-s3-state-json`.

**Schema discipline:** `state.json` is regenerable from `slice.yaml` + `handoff.md` if lost. Not a source of truth.

---

### E4 — Layer-1 allowlist refinement (unified with F6 projection)

**Problem:** Part -1 #5 ships a first pass. This slice refines it with rule categories, names, pattern discipline mirroring F6's `permission-policy.yaml` exactly.

**Change:** Rewrite `.claude/settings.json` allowlist as named rules:
```json
{
  "permissions": {
    "allow_rules": [
      { "name": "read-only-project-ops", "pattern": "Bash(sed -n *)", "rationale": "..." },
      { "name": "read-only-project-ops", "pattern": "Bash(awk *)", "rationale": "..." },
      { "name": "test-runners", "pattern": "Bash(uv run pytest *)", "rationale": "..." }
    ]
  }
}
```

(Pseudo-schema — Claude Code's actual `.claude/settings.json` is a flat `allow` list. The names + rationales live in a sidecar `docs/permission-policy-source.yaml` that `.claude/settings.json` is generated from. When F6 lands, that sidecar becomes the production `permission-policy.yaml` directly.)

**Slice:** `part-2-s3-layer-1-refinement` (bundle with E3; both touch .claude/ config).

---

### E5 — Session-start tip upgrade

**Problem:** Part -1 #1 prints a phase role cheatsheet. This slice extends it to consume `state.json` and print the full orientation one-liner.

**Change:** Hook reads `state.json` + `slice.yaml`, prints:
```
Phase 3 of identifier-scheme/slice-and-feature-rename (commit af660a5).
Role: Implementer. Anti-behavior: do not modify tests.
Next: /start-slice next
```

**Slice:** `part-2-s4-session-start-upgrade`.

**Depends on:** E3 (`state.json` exists).

---

### E6 — Coupling-cluster step at Phase 2

**Problem:** Phase 3 parallel dispatch needs a coupling-cluster partition. Part 0 P4 declares it; this slice implements.

**Change:** Phase 2 skeptic (via the phase-2 skill) produces, alongside tests + approach.md:
- `.claude/current-slice/validation/coupling-clusters.yaml`

Shape:
```yaml
version: 1
clusters:
  - id: c1
    rationale: "shared API surface; B imports from A"
    files: [src/auth/api.py, tests/unit/test_auth.py]
  - id: c2
    rationale: "independent module"
    files: [src/utils/helpers.py]
```

Phase 3 reads this file and dispatches `phase-3-implementer` (Part 3) per cluster.

**Slice:** `part-2-s5-coupling-clusters`.

**Depends on:** Part 0 ADR; Part 3 phase-3-implementer (soft-depends — cluster file is useful even without fan-out, as documentation).

## Part 2B — Speed

### S1 — `test-impact-analyzer`

**Problem:** complex-rag-analysis's pytest suite is ~917s. Running the full suite after every 5-line change is wasteful; most changes affect <10% of tests.

**Change:** Agent reads staged diff + tests/ directory, returns ordered list of tests most likely affected:
- Direct-match: test imports the changed module.
- Name-match: test function name overlaps with changed function.
- Fixture-match: test uses fixtures defined in changed files.

Run the shortlist first (typically <30s). Only run full suite if shortlist passes and the author opts-in.

**Slice:** `part-2-s6-test-impact`.

**Return contract:** ≤50 test IDs, priority-ordered.

---

### S2 — `parallel-test-orchestrator`

**Problem:** Full-suite runs on complex-rag-analysis are 15 min. Could be ~4 min on 4 shards.

**Change:** Agent partitions tests by module, dispatches N subagents each running their shard via `uv run pytest tests/<shard>`. Aggregates results. Uses pytest-xdist under the hood if available; falls back to shard-subagents if not.

**Slice:** `part-2-s6-parallel-tests` (bundle with S1).

**Timeout discipline:** Per Part 0 P5. Hard-cap per shard: 10 min. If a shard stalls, report partial result + stall indicator.

---

### S3 — `background-precommit`

**Problem:** `validate_architecture.py` + `snapshot_diff.py` run sequentially, blocking for 10–30s before commit.

**Change:** On `git add` (PostToolUse hook), spawn these scripts async in background. Results cached to `.claude/precommit-cache/<sha>.json`. When `/handoff` or manual commit fires, check cache for current SHA; use cached result if fresh (≤5 min).

**Slice:** `part-2-s7-background-precommit`.

**Fallback:** If cache miss, run synchronously as today. Never blocks correctness.

---

### S4 — `commit-drafter`

**Problem:** Every commit requires 30–60s of "what should this say" thinking. For non-phase commits (refactors, fixes), there's no template.

**Change:** Agent reads `git diff --cached`, returns conventional-commit message:
- subject: `<type>: <imperative one-line>`, ≤50 chars
- body: 1–3 sentences on the "why" if non-obvious

User accepts/edits. Fast, unobtrusive.

**Slice:** `part-2-s7-commit-drafter` (bundle with S3).

**Respects:** Phase-commit templates (Part -1 #6) — those take precedence when `slice.yaml` indicates a phase boundary.

## Slice breakdown

- **S1** — E1 (auto-phase-detect in 3 commands).
- **S2** — E2 (code-side-effects in `/handoff` + sibling commands). Depends on Part -1 #4 + #6.
- **S3** — E3 (state.json) + E4 (Layer-1 allowlist refinement).
- **S4** — E5 (session-start tip upgrade). Depends on S3.
- **S5** — E6 (coupling clusters at Phase 2). Depends on Part 0 ADR.
- **S6** — S1 (test-impact) + S2 (parallel-test orchestrator).
- **S7** — S3 (background precommit) + S4 (commit-drafter).

## Cross-cutting

- **Backward compat:** All explicit forms (e.g., `/catchup phase 2`) remain supported as escape hatches.
- **Rollback surface:** Every ergonomic item is feature-flag-able via env var or frontmatter setting. If `state.json` becomes a foot-gun, `CAIRN_STATE_JSON=0` disables the short-circuit.
- **state.json vs handoff.md:** `state.json` is derived cache; `handoff.md` narrative remains canonical. Part 0 P6 applies.

## Success criteria

1. User never types `phase N` or mode letters for canonical flows.
2. L-005-class divergence impossible by construction.
3. Typical inter-phase `/catchup` completes in <5s.
4. Test feedback loop for most edits is <30s (vs 15 min baseline).
5. Tier-1 routine-read prompts → 0 for all team members.
6. Commits from Phase 3+ implementers routinely use commit-drafter; phase commits use templates.

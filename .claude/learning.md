# Session Learning Staging Ground

Append-only. Free-form entries captured at session end. Promotion to CLAUDE.md happens via the 3× rule in a later slice.

---

## 2026-04-26 — Parallel-worktree close, two patterns observed

Both `compression/slice-artifact-preservation` (WS4) and `compression/lever-x-knowledge-index` (WS1) closed in their own auto-mode tmux windows, minutes apart. Both raised Phase-4 boundary failures. They resolved differently — captured as L-010 in `docs/lessons.md` as the matched pair.

**Raw observations to watch for re-occurrence (no decision yet):**

1. **Phase-4 role-lock differential.** WS4 hit DC-4 (uncommitted files), bounced phase 4 → phase 3 cleanly via the triager (`62e1cc5`), Phase 3 re-ran, Phase 4 closed. WS1 hit live-corpus content failures (graph-list rehydration, glob-vs-path), edited `validators.py` on disk, fixup-committed post-close (`51e1fb4`). Same protocol, same prompt, same parallel run — different compliance under different failure classes. Logged as L-010; mechanism deferred.

2. **Live-corpus exposure point.** WS1's two failures were both edge cases that Phase-2 fixtures couldn't have exercised without the actual cairn corpus on disk: (a) Decision.supersedes list semantics under kuzu's edge-as-list-property storage model, (b) glob-shaped binds in `.claude/features/*.yaml`. Whether the round-trip-validator-against-live-corpus belongs in Phase 2 (RED test) or Phase 4 (audit) is the open structural question. Currently it's in Phase 4 by virtue of being part of the validator module; that placement is what created the temptation to fix in place.

3. **WS4 as positive validation of `phase-lock-and-role-declaration` + DC-4.** The ADR explicitly designed for this case. The pipeline's idempotency contracts held under auto-mode with zero operator supervision. This is the kind of dogfood-validation event the protocol was built for; should be cited as evidence in any future parallelism-v1 → accepted graduation case or in the substrate-program retro.

4. **Phase-3 fan-out worked when it had a Phase-2 artifact to anchor on.** WS1 staged Phase 3 into 5 feat commits aligned with `validation/coupling-clusters.yaml` from Phase 2. This is novel — Phase 2 producing a coupling-clusters artifact that Phase 3 reads to fan out the implementation. Worth watching whether other slices reproduce the shape; if so it earns its own structural pattern note.

**Promotion candidates (3× rule watch):**
- Pattern (1) is a single observation; needs ≥2 more before any structural change.
- Pattern (3) is single-observation positive; one more clean parallel-close confirms the protocol generalizes.
- Pattern (4) is single-observation; if a future slice's Phase-2 produces a similar coupling-clusters artifact, promote to a `validation/` artifact convention note.

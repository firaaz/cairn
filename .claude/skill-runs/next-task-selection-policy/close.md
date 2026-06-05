# Close — next-task-selection-policy

**Intent:** `.claude/skill-runs/next-task-selection-policy/intent.md`
**Snapshot at form:** `fd6576f`

## What landed
Added a `## Next-task selection` section to `docs/operational-reference.md` (lines ~397–409): a 6-rung selection ladder (`blocked` → `deferred` → finish-started → severity → roadmap `Depends on` → route-by-weight), each rung naming the existing signal it reads. 17 insertions, single file. No tool, no code, no new file, no new maintained data.

## Decorrelation checkpoints (both fresh-context, same-family)
- **Front intent-challenge:** `challenge-pass` — independently re-verified "policy gap not tooling gap" against live source (whole-repo grep found no existing ranker; only `/dev-mode`, a read-only board dashboard whose cairn-side flips are unbuilt). Report: `intent-challenge.md`.
- **Close-review:** `close-review-pass` — independently ran the ladder against the live handoff; converged on a defensible single pick (surface gh#31). All clauses hold; scope clean. Report: `close-review.md`.

## Final verification
- `grep '## Next-task selection' docs/operational-reference.md` → PRESENT; 6 rungs at lines 403–408.
- `git diff --stat` → `docs/operational-reference.md | 17 ++` only (within execution-scope).
- Dogfood: ladder applied to current `.claude/handoff.md` → pick = surface gh#31 (`blocked`+`operator-bound`); 4 deferred triggers unmet; dev `0 0`; non-contradictory.

## Residual risk (accepted, non-blocking)
The ladder is a human-judgment aid; a future backlog state could surface a contested pick no static review anticipates. Mitigation is in-band: rung 6 / the escalate-when clause self-routes that case to operator escalation.

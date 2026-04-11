# Lessons

Cross-cutting patterns discovered during slice work, referenced by `/decision` Phase 0 (Constraint Harvest) and `/integration-sweep` recommendations.

## L-001: Pipeline-bypass temptation — "just write it down" before opening a slice

**Discovered**: 2026-04-11, first integration sweep after SLICE-001 (`validator-symlink-fix`).

**Pattern**: a real bug is discovered in the middle of another session (often while consuming cairn from a downstream project). The urge is to *write it down somewhere* — a CHANGELOG entry, a known-issues note, a docs paragraph — before opening a slice to fix it. The bug feels too concrete to leave in working memory and too specific to lose to a session boundary. A tiny direct commit feels justified because "it's just docs."

**What happens**: the direct commit lands. It is a three-line addition, well-written, cleanly scoped. It is also a bypass of `/start-slice` and a violation of the invariant that requires all post-bootstrap work to flow through the pipeline. The first cross-slice integration sweep finds it. By then it is already in the permanent history.

**Concrete instance**: `f531087 docs: record validator symlink-resolution bug in Known issues` (2026-04-11). Three-line CHANGELOG edit recording the `scripts/validate_architecture.py:22` symlink bug that SLICE-001 subsequently fixed. Intent was honest; the act was a violation. After the first cross-sweep surfaced it, the remedy was **option 3 — accept as a scar**: leave INV-001 unchanged, record this lesson, let the violation stand in history as evidence that the pipeline is not mechanically enforced and the maintainer's own discipline is the only barrier.

**Why option 3 and not a new ADR**: rewriting the invariant to excuse the commit would hide the lesson. ADR-001 already says "there is no second exception" and "future attempts must go through supersession, not quiet repetition." A supersession to retroactively regularize the bypass would be quiet repetition in a different form. The honest answer is: the bypass happened, it should not have happened, and the cost of recording that is carrying one un-remediated violation in the `git log` forever.

**Recursive consequence**: `/integration-sweep` step 6.5 itself produces a commit that is not a slice phase commit and not a decision commit. Under a strict reading of INV-001, every sweep commit is also a violation of the same class. Option 3 accepts this too — sweep commits are scars of the same kind, landed deliberately, each one an audit-trail artifact of an honest check rather than a shortcut. This is the consequence of not writing an ADR-002 that names sweep commits as pipeline-substrate operations.

**Rule for future Claude sessions (and future me)**: if you are about to make a direct commit to cairn and you are not in the bootstrap commit, stop. The options are (1) open a slice via `/start-slice`, (2) run `/decision` if the change is architectural, or (3) write nothing to the repo and carry the information forward to the next session via `/handoff`. The temptation to "just write it down quickly" is the pattern this lesson names. Holding that information in `/handoff` state is strictly better than a direct commit, because a handoff does not pollute the audit trail.

**Exceptions**: `/integration-sweep` and `/refresh-architecture` commits are pipeline-substrate operations whose exclusion from `/start-slice` is a known scar (see the recursive consequence above). They are not a license for other kinds of direct commits.

**Anti-pattern signals**: "it's just docs," "it's only three lines," "I'll open the slice right after," "the invariant doesn't really mean this." All of these were internally true in the concrete instance. None of them prevented the violation.

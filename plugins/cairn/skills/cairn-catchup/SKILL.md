---
name: cairn-catchup
description: Orient a fresh Codex thread by reading Cairn's handoff pointer, recent git history, working-tree state, and active write envelope.
---

# Cairn Catchup

Codex version of `/catchup`. This is orientation only.

## Steps

1. Read these sources in order, then stop gathering context:
   - `.claude/handoff.md`
   - `git log --oneline -10`
   - `git status -s`
   - `.claude/active-envelope.yaml` if present
2. Summarize:
   - current branch and tip SHA
   - handoff threads grouped by `open`, `blocked`, and `deferred`
   - working-tree changes that need attention
   - active envelope `mode:` and one-line path scope, if present
3. Stop after the catchup. Do not run tests, validators, broad searches, or unrelated skills.

## Missing Or Stale Handoff

If `.claude/handoff.md` is missing, say so and fall back to `git log --oneline -20` plus `git status -s`. If the handoff appears stale against recent commits, surface that gap without rewriting the project narrative.

The original Claude command reference is bundled at `references/catchup.md`.

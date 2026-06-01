---
name: cairn-handoff
description: Write or refresh Cairn's `.claude/handoff.md` pointer file using `templates/handoff.md`.
---

# Cairn Handoff

Write or refresh `.claude/handoff.md` at the end of a session so the next Codex or Claude thread can resume from durable pointers.

## Steps

1. Read `templates/handoff.md` and preserve its frontmatter contract.
2. Inspect the existing `.claude/handoff.md` if present, `git status -s`, recent commits, and any active intent path that the current work depends on.
3. Write body entries only in this shape:
   - `<pointer> <state> [<short context>]`
   - state must be one of `open`, `blocked`, or `deferred`
4. Use resolvable pointers: ADR paths, plan paths, issue references, commit SHAs, or `.claude/skill-runs/<feature>/...` artifacts.
5. Keep the body pointer-only. No narrative paragraphs and no multi-sentence entries.
6. Run `uv run pytest tests/unit/test_handoff_contract.py -q` when changing the handoff in this repo.

If there is no meaningful active thread, keep the template contract and write the thinnest accurate deferred/open pointer instead of inventing context.

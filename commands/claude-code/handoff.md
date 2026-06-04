# /handoff

Write or refresh Cairn's pointer-only handoff. The bookend to `/catchup`:
handoff records durable pointers at session end; catchup reads them at session
start.

Usage: `/handoff`

## Rules

1. **Read the template first.** Load `templates/handoff.md` and preserve its
   frontmatter contract exactly.
2. **Inspect only the handoff inputs.** Read the existing `.claude/handoff.md`
   if present, `git status -s`, `git log --oneline -10`, and any active intent
   path that the current work depends on.
3. **Write pointer entries only.** Every body line in `.claude/handoff.md` must
   be `- <pointer> <state> [<short context>]`, where state is exactly one of
   `open`, `blocked`, or `deferred`.
4. **Use resolvable pointers.** Valid pointers include ADR paths, plan paths,
   GitHub issue references, commit SHAs, and `.claude/skill-runs/<feature>/...`
   artifacts.
5. **Keep the body sparse.** No narrative paragraphs, no multi-sentence
   entries, no retrospective summaries, and no hidden memory.
6. **Verify the contract after edits.** Run
   `uv run pytest tests/unit/test_handoff_contract.py -q`.

## Missing Active Thread

If there is no meaningful active thread, keep the template contract and write
the thinnest accurate `deferred` or `open` pointer instead of inventing context.

## Anti-patterns

- Do not add retired narrative handoff section headings.
- Do not stage unrelated files or commit unless the operator explicitly asked
  for a commit.
- Do not use the handoff as a transcript summary; durable context lives behind
  pointers.

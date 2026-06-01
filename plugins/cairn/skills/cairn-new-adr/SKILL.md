---
name: cairn-new-adr
description: Create or supersede a Cairn ADR with semantic id frontmatter, append-only discipline, index updates, and architecture validation.
---

# Cairn New ADR

Codex port of `/new-adr`.

## Steps

1. Read `docs/adr/index.md` and determine the next numeric filename prefix. The ADR `id:` is a flat semantic slug, not the numeric prefix.
2. Gather the decision statement, prompt, firmness, topic, referenced ADR ids, and touched invariants. Default to `firmness: provisional`.
3. Create `docs/adr/<NNN>-<slug>.md` using `templates/adr-frontmatter.yaml` as the frontmatter shape.
4. Body sections: Status, Date, Context, Decision, Consequences, Alternatives Considered. Commitments in Decision should be testable.
5. If superseding, update only the old ADR frontmatter: `status: superseded` and `superseded-by: <new-id>`. Do not edit the old body.
6. Update `docs/adr/index.md`.
7. Run `uv run python scripts/validate_architecture.py` and fix validation issues before closing.
8. If this was part of active feature work, update the relevant intent or sweep notes with the ADR pointer.

Read `references/new-adr.full.md` before partial supersession, validation repair, or any non-routine ADR structure.

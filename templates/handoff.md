---
slice: <SLICE-id or "none">
phase: <1-intent | 2-validation | 3-implementation | 4-integration | complete | n/a>
branch: <branch-name>
as-of: <YYYY-MM-DD commit-sha>
---

## State
<1–2 present-tense sentences. Current state, not history. No reasoning, no reflection.>

## Next
<One imperative. One line. Specific: "Rewrite Step 7 of start-slice.md to wipe current-slice" not "continue work".>

## Blocked / Pending
- <short item> → <pointer>
- <max 5 lines, each a one-liner plus pointer, no rationale>

## Features
<One line per active feature. Format: `- <feature-id>: <status-summary>`. Omit section if no features are active.>

## Pointers
- `path/to/file.md` — what's there and when the next session should read it
- `path/to/other.md` — one line each; the body of the pointed-at file carries the detail

---
slice: bypass-log-reclass
date: 2026-04-16
phase: 1-intent
invariants-touched: []
adrs-referenced: [d3-bypass-classification]
envelope:
  - ".claude/d3-bypasses.log"
out-of-scope:
  - "scripts/snapshot_diff.py — parser changes for the new format (separate slice)"
  - "commands/claude-code/start-slice.full.md:224 — rolling-window rule rewrite (separate slice)"
  - "commands/claude-code/integration-sweep.md / .full.md — sweep reporting changes (separate slice)"
  - "intent.md `exempt:` list syntax — Decision 2 of the ADR (separate slice)"
  - "SLICE-017 log line — already in new <class>: format; not re-edited"
---

### What and Why

Execute the one-time historical reclassification called for in `docs/adr/d3-bypass-classification.md` Decision 1. The three pre-classification log entries in `.claude/d3-bypasses.log` (SLICE-012, SLICE-014, SLICE-016) are migrated in-place from the old free-text reason format to the new `<class>: <reason>` format, with `class = pre-existing` on all three per the ADR's explicit historical-reclassification paragraph. The SLICE-017 entry is already in the new format and must not be re-edited.

After this slice lands, every line in `.claude/d3-bypasses.log` conforms to the classified format, and the rolling-window `false-positive` count sits at `0/N` as the ADR's adoption paragraph asserts. No parser, no command template, no ADR body, no other substrate changes.

### Specification Detail

**Format (from ADR Decision 1):**

```
<slice-id> <YYYY-MM-DD> <class>: <one-line-reason>
```

`<class>` is one of: `slice-caused`, `pre-existing`, `false-positive`. This slice only writes `pre-existing` entries; the other two classes are defined by the ADR but not exercised here.

**Per-line target state** (expressed as `<slice-id> | <class> | <reason verbatim from original line>`):

- `SLICE-012` | `pre-existing` | `ruff lint (E741, E402) in test_feature_cross_index.py and test_invariant_assertions.py — outside envelope`
- `SLICE-014` | `pre-existing` | `fleet-coordinator-design.md drift from parallel session (designing the automation for multi-slice work this slice's gates are catching)`
- `SLICE-016` | `pre-existing` | `INV-004 turn-1 token budget failure — CC 2.1.107 → 2.1.110 drift, slice envelope does not load at session start; re-baseline queued as housekeeping`
- `SLICE-017` | (unchanged) | the existing `pre-existing: snapshot_diff flags ...` line is preserved byte-for-byte

**Migration rule (text-level):** For the three legacy lines, the date field is immediately followed by a single space, then `pre-existing: `, then the original one-line reason verbatim. The date, slice-id, and reason-text substrings are all preserved. No re-ordering, no extra whitespace normalization beyond inserting the `pre-existing: ` marker.

**File invariants after migration:**

- Line count is exactly 4.
- Lines appear in the order SLICE-012, SLICE-014, SLICE-016, SLICE-017 (chronological, matching current order).
- File ends with a single trailing newline (matching current state).
- Every line matches the regex `^SLICE-\d+ \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive): .+$`.

**Out of scope — explicitly deferred:**

- Parser changes in `scripts/snapshot_diff.py` to understand the new format. The legacy and new formats both render as plain text; no existing consumer of this file parses the class field yet.
- Rewriting `commands/claude-code/start-slice.full.md:224`'s rolling-window rule text to say "false-positive only."
- Sweep-report changes in `commands/claude-code/integration-sweep*.md` to distinguish counts.
- Decision 2 of the ADR (envelope `exempt:` list) is a separate slice.

### Verification

1. **File line count:** `wc -l .claude/d3-bypasses.log` prints `4`.
2. **Regex conformance:** every line matches `^SLICE-[0-9]+ [0-9]{4}-[0-9]{2}-[0-9]{2} (slice-caused|pre-existing|false-positive): .+$`. A test iterates line-by-line and asserts match.
3. **Class distribution:** all four lines are classified `pre-existing`. A test counts class tokens and asserts `{'pre-existing': 4, 'slice-caused': 0, 'false-positive': 0}`.
4. **Reason preservation for the three migrated lines:** the reason text (substring after `<date> pre-existing: `) is byte-identical to the reason text of the pre-migration line (substring after `<date> `), modulo the leading `pre-existing ` → `pre-existing: ` change on SLICE-012's original prefix word. A test asserts, for each of SLICE-012/014/016, the post-migration reason substring equals the expected reason string pinned in this intent's Specification Detail table.
5. **SLICE-017 byte preservation:** the SLICE-017 line equals its pre-migration content. A test captures the current SLICE-017 line as a fixture string and asserts the post-migration file contains that exact line.
6. **Trailing newline:** `.claude/d3-bypasses.log` ends with exactly one `\n` (no missing newline, no blank trailing line). A test asserts `content.endswith('\n') and not content.endswith('\n\n')`.
7. **No other file touched:** `git diff --name-only` between Phase 1 HEAD and Phase 3 HEAD lists only `.claude/d3-bypasses.log`. Enforced by scope-guard during the slice and verified in Phase 4 sweep notes.

**Edge cases pinned:**

- SLICE-012's original line begins `... 2026-04-14 pre-existing ruff lint ...`. The migration inserts `: ` after the first `pre-existing` token, converting it from a free-text word into the class marker. The post-migration line therefore reads `... 2026-04-14 pre-existing: ruff lint ...` (single occurrence of `pre-existing`, now followed by a colon), not `... 2026-04-14 pre-existing: pre-existing ruff lint ...`. This matches the ADR's intent — the original word was a proto-classification and becomes the formal class token.
- SLICE-014 and SLICE-016 original lines do not begin with a class-word, so migration is a clean insertion of `pre-existing: ` immediately after the date.
- Em-dashes (`—`) and embedded parentheses in the reason text are preserved as-is; no escaping, no normalization.

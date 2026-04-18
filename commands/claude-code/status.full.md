# /status — Full Reference

Expanded registry / debug output. Load only on the discrete predicate
"user asks for the full registry view" — progressive-disclosure INV-004.

Usage: `/status full` or "show the full registry"

## When to load

Load this file **only** when one of these is true:
- User explicitly asks for the "full" status, "full registry view", or "debug dump".
- Lite `/status` dashboard showed a specific anomaly (failed verifier, sweep-overdue by a wide margin, unknown slice state) and the user asks to drill in.

Otherwise the five-line lite dashboard in `commands/claude-code/status.md` is sufficient — do not load this file speculatively.

## Expanded output sections

Rendered below the lite dashboard when loaded:

### Registry

1. **Invariant registry** — read `docs/spec-v1.md` § Invariants, print each invariant's ID + one-line statement.
2. **ADR registry** — `ls docs/adr/*.md`; for each, print `id · name · status · firmness`.
3. **Feature registry** — `.claude/features/*.yaml`; for each, print `id · name · slice count · last-slice-status`.
4. **Active slice dump** — full `slice.yaml` contents, plus the file list under `.claude/current-slice/` with sizes.

### Debug

1. **Hook inventory** — enumerate `.claude/settings.json` hooks, one per line with matcher + command path.
2. **Allowlist size** — `jq '.permissions.allow | length' .claude/settings.json`.
3. **Architecture validator** — run `uv run python .slice-system/scripts/validate_architecture.py` and report pass/fail with first 20 lines of output.
4. **Git state** — branch, ahead/behind counts vs upstream, uncommitted file count, last 3 commit subjects.

## Budget

Full output has no hard character ceiling — it is loaded on explicit request and the user has opted into the fuller surface. Keep per-section output tight (≤40 lines per section) so total stays under ~300 lines even on a busy repo.

## Progressive-disclosure invariant (INV-004)

The lite dashboard at `commands/claude-code/status.md` stays ≤1500 characters. This file is referenced from the lite dashboard by name only — its body does not load into the session unless the user explicitly asks for the full view. That separation is what keeps INV-004 intact across both surfaces.

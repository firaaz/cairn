# Start Slice — Full Reference

Begin a new development slice or advance an existing one through Intent → Validation → Implementation → Integration.

Usage: `/start-slice` (new slice) or `/start-slice phase 2|3|4` (advance) or `/start-slice complete` (finish)

## Why This Exists

Complex systems fail at integration, not at individual features. When the same agent writes code and checks it in the same context, mistakes are invisible — correlated errors. This pipeline forces context isolation between phases: the agent writing tests has never seen the implementation, and the agent implementing has never seen the test reasoning. Each phase receives only the previous phase's artifact.

## Step 1: Load Context

Read `.slice-system/docs/operational-reference.md` — specifically the section for the target phase. This is the source of truth for what each phase does, what it receives as input, and what it produces.

## Step 2: Determine Current State

Check if `.claude/current-slice/slice.yaml` exists.

**If it exists:** Read it. The `status` field tells you the current phase.
- If status is `failed` → go to Step 8 (Failed Slice Recovery)
- If `$ARGUMENTS` specifies a phase → validate the gate (Step 3) and advance
- If `$ARGUMENTS` is `complete` → go to Step 7 (Completion)
- If no argument → report current status and ask what the user wants to do

**If it doesn't exist:** This is a new slice → go to Step 4.

## Step 3: Phase Gate Validation

Each phase's artifact must be committed to git before advancing. This isn't bureaucracy — it's the mechanism that enables context isolation. If artifacts aren't committed, the next phase can't start in a fresh session with only the artifact as input.

| Target Phase | Required Artifact | Verification |
|-------------|-------------------|-------------|
| Phase 2 (Validation) | `intent.md` committed AND every ADR named in its `adrs-referenced` YAML field already exists as a committed file in `docs/adr/` (D3 gate, phase-lock-and-role-declaration) | `git log --oneline -- .claude/current-slice/intent.md` returns at least one line; AND for each slug in `adrs-referenced`, `git log --oneline -- docs/adr/<slug>.md` returns at least one commit |
| Phase 3 (Implementation) | Validation tests committed | `git log --oneline -- tests/` returns commits for test files matching the envelope's test patterns |
| Phase 4 (Integration) | Source files committed | `git status --short` shows no uncommitted changes in envelope files |

**D3 gate semantics (Phase 2 row).** Every ADR slug named in `intent.md`'s `adrs-referenced` field MUST already exist as a committed file in `docs/adr/` before Phase 2 starts. This enforces `docs/spec-v1.md` §6's Decision→Intent immutability rule structurally: intent cannot reference a decision that has not yet been made. Slug resolution is direct filename match — for a slug like `phase-lock-and-role-declaration`, check `git log --oneline -- docs/adr/phase-lock-and-role-declaration.md` (filename is `<slug>.md`, per ADR `identifier-scheme` D2). An **empty** `adrs-referenced` field **passes the gate trivially** — cleanup slices, pure-implementation slices, and other low-consequence slices are not forced to cite ADRs they do not depend on, per phase-lock-and-role-declaration D3.

**D3 gate failure path.** When one or more ADRs are missing from `docs/adr/`, the gate MUST fail and the failure message MUST name **every** missing ADR slug, not just the first. Example: `Gate FAILED: missing ADR files for slugs [phase-lock-and-role-declaration, parallelism-v1]. intent.md references ADRs that are not yet committed to docs/adr/. Either commit the missing ADRs first (via /decision or /new-adr), or remove them from adrs-referenced in intent.md.` The plurality commitment matters because silent truncation ("missing ADR: phase-lock-and-role-declaration") would let a slice drift past a second unresolved decision on retry. List all missing slugs in every failure message.

**If the gate fails:** Explain what's missing and give the exact git commands to fix it. Do not proceed — this gate is what makes the whole system work.

**If the gate passes:** Update `slice.yaml` status field. Then — before advancing into the phase-specific guidance below — read `docs/operational-reference.md § Phase Skill Guide` and print the target phase's **role name**, **primary anti-behavior**, **secondary anti-behaviors**, and **primary + supporting skills** to the operator. This is the phase-lock-and-role-declaration D4 surfacing commitment: roles and skills are not dead text, they are echoed at every phase entry. For Phase 1, the primary-skills column is an em-dash (no primary fit) — still print the row so the operator sees the explicit absence rather than inferring a missing assignment. The Phase Skill Guide is a living registry; if an entry looks stale, the registry is the source to update, not this skill.

### Phase 2: Validation

Input: only `intent.md` (+ `docs/ARCHITECTURE.md` and specific ADRs if referenced in intent).

Before writing any tests, do this forced enumeration step — it's the cheapest moment to catch ambiguity:
1. Read intent.md and list every place the intent could be interpreted multiple ways
2. For each ambiguity: resolve by reference to ARCHITECTURE.md/ADRs, or flag for human resolution
3. Only then design the validation suite

Write tests to `tests/` (matching the envelope's test patterns). These go in the project test tree so pytest discovers and runs them naturally. Write a brief approach summary to `.claude/current-slice/validation/approach.md` explaining the validation strategy.

The `.claude/current-slice/validation/` directory stores the approach summary only — test code lives in `tests/` alongside the rest of the project's tests.

The tests should verify the **stated intent and specification details**, not a hypothetical implementation. This is what makes the check external.

### Phase 3: Implementation

Input: `intent.md` + the validation test files. Do not load Phase 2's approach.md or any reasoning about why the tests are shaped the way they are — only load the tests themselves.

Write code that passes the validation suite. Record any decisions that intent.md didn't pin down in `.claude/current-slice/implementation/notes.md`.

Run tests frequently. The reality hook handles lint/format automatically on every edit.

### Phase 4: Integration

Input: the full implementation + `intent.md` + `docs/ARCHITECTURE.md`.

1. Run the full test suite (not just this slice's tests): `uv run python -m pytest`
2. Run the architecture validator: `uv run python .slice-system/scripts/validate_architecture.py`
3. Verify each invariant declared in intent.md's `invariants-touched` field using this evidence-based protocol:

For each invariant, read the relevant source files and produce a structured check:

| INV | Statement | Status | Evidence |
|-----|-----------|--------|----------|
| NNN | Text from ARCHITECTURE.md | PASS/FAIL | Specific file:line citations proving compliance or violation |

Use `grep` and file reads — assertions must be backed by what you actually found, not reasoning from memory.

4. Check for regressions in adjacent modules by reviewing imports and interfaces at the boundary of the envelope.
5. Record results in `.claude/current-slice/integration/sweep-notes.md`.

**If Phase 4 fails because the implementation is wrong** → the slice needs to be marked as failed and retried. Run `/start-slice failed` to archive the failed slice, then create a new slice with the Phase 4 failure as input context. Do NOT patch the implementation to force Phase 4 to pass — that recreates the correlated-error problem this system is designed to prevent.

**If Phase 4 fails because an invariant is outdated** → write a new ADR superseding the old invariant (`/new-adr supersede ADR-NNN`), run `/refresh-architecture`, then re-run Phase 4 checks. The scope guard allows ADR and architecture file writes during a slice.

## Step 4: Initialize New Slice

Pick the hierarchical slice id (`<feature-id>/<slice-slug>`) for the new slice. There is no numeric counter to increment — the hierarchical id is self-identifying and `.claude/sweep.yaml`'s `current-slice-number:` field has been retired (ADR `identifier-scheme` D7 Phase 2 Part 2, complete).

If `.claude/sweep.yaml` does not exist, create it with defaults:
```yaml
last-sweep-at-slice-id: null
sweep-interval: 1
```
Then proceed — `last-sweep-at-slice-id:` will be populated by `/integration-sweep` at the first sweep close.

Create the directory structure:
```
.claude/current-slice/
  slice.yaml
  intent.md          (empty, to be filled)
  validation/
  implementation/
  integration/
```

Write `slice.yaml`:
```yaml
id: <feature-id>/<slice-slug>
name: "<human label>"
status: intent
started: <today's date YYYY-MM-DD>
completed: null
invariants-touched: []
adrs-referenced: []
adrs-created: []
```

The hierarchical `<feature-id>/<slice-slug>` form is the only form for new slices per ADR `identifier-scheme` D2. Legacy `SLICE-NNN` identifiers survive only in archived `.claude/completed-slices/` fixtures and historical test data; hooks and the validator retain mixed-window tolerance for that read-only history per ADR `identifier-scheme` D7 Phase 1 (Phase 3 retirement deferred indefinitely). When `<feature-id>` is not yet known, pick the feature-slug now — `/start-slice` also writes the feature file in the next block, so the feature id is resolved together with the slice id.

No per-slice `.claude/sweep.yaml` write is needed at slice creation. The file is only updated by `/integration-sweep` at sweep close, when it writes the triggering slice's id into `last-sweep-at-slice-id:`. Retirement of the old `current-slice-number` counter is complete (ADR `identifier-scheme` D7 Phase 2 Part 2).

### Feature file (feature-slice-model D3 always-create)

Every slice belongs to a feature. Before guiding intent writing, create or update the feature file at `.claude/features/<feature-id>.yaml`:

**If no feature file exists** for the current feature: create one with the required fields (`id`, `intent`, `created`) and a `slices` list containing the new slice entry (with `id` and `added` fields). Even single-slice features get a feature file — there is no "too small" exemption.

**If a feature file already exists**: add a new slice entry to its `slices` list. Existing entries (including any with `status: dropped`) must be preserved — append only.

Feature YAML shape (ADR `identifier-scheme` D1/D5):

```yaml
id: <feature-id>
name: "<human label>"
intent: "<one short prose statement>"
shaped-from: "<path-or-url-or-null>"
created: <YYYY-MM-DD>
slices:
  - id: <feature-id>/<slice-slug>
    added: <YYYY-MM-DD>
```

Each slice-list entry uses the hierarchical `id: <feature-id>/<slice-slug>` form. `shaped-from:` records the feature's provenance — a design-doc path, a URL, or `null` for unshaped features.

Then guide intent writing (Step 5).

## Step 5: Guide Intent Writing (Phase 1)

The intent document has three zones. Help the user fill each one.

**Zone 1 — YAML Envelope** (machine-readable, consumed by scope-guard hook):
```yaml
slice: <short-name>
date: <YYYY-MM-DD>
phase: 1-intent
invariants-touched: [INV-NNN]
adrs-referenced: [ADR-NNN]
envelope:
  - "src/path/to/*.py"
  - "tests/unit/path/to/test_*.py"
out-of-scope:
  - "what this slice does NOT touch"
```

To fill this: read `docs/ARCHITECTURE.md` for invariants and `docs/adr/index.md` for relevant ADRs.

- **Greenfield slices** (new modules): Do not read source code — working from architecture docs only prevents implementation thinking from contaminating the intent.
- **Modification slices** (changing existing behavior): Read only the public interfaces of files in the envelope (function signatures, class definitions, docstrings). Do not read internal implementation logic. The intent should describe the target behavior, not the delta from current behavior.

**Zone 2 — What/Why/Specification** (human-readable):
```markdown
### What and Why
<What behavior change does this slice introduce? Why does it matter? 2-3 sentences.>

### Specification Detail
<Protocol-level commitments: wire formats, key patterns, return shapes, error codes.
Rule of thumb: if a different valid implementation could choose differently and break something downstream, it goes here.>

### Boundary
<What is explicitly out of scope? Specific items, not vague categories.>
```

**Zone 3 — Verification** (definition of done):
```markdown
### Verification
<Specific, concrete checks. Not "test it" — actual assertions with expected values.>
```

## Step 6: Remind About Committing

After intent.md is written:

> 1. Commit: `git add .claude/current-slice/ && git commit -m "slice: <name> — phase 1 intent"`
> 2. Run `/handoff phase` to package context and update slice status
> 3. Close this session
> 4. In the next session, run `/catchup` to load only Phase 2's declared inputs, then `/start-slice phase 2`

The fresh session matters — context isolation is what makes the external check actually external. `/handoff` packages what happened; `/catchup` loads only what the next phase should see. Together they bridge the session boundary without leaking reasoning.

## Step 7: Complete a Slice

When Phase 4 passes, the completion sequence **wipes** every file under `.claude/current-slice/`. This is not optional and there is no archive directory for successful slices — the `status: complete` commit IS the git-history record, and `.claude/learning.md` plus ADRs cover the post-mortem case. Per context-discipline-protocol, leaving residue in `.claude/current-slice/` after close would cause the next slice to inherit stale framing through `/catchup`, defeating the context-isolation boundary this pipeline exists to enforce.

### D1 + D3 Gates

Before the wipe sequence begins, run D1 and D3 gates. D1 runs first (it modifies ARCHITECTURE.md, which D3 reads). D3 gates run as parallel subagents after D1 completes.

#### D1 Refresh Gate (sequential, first)

1. Run `/refresh-architecture` logic. The refresh loads only `docs/adr/*.md` (excluding `index.md` and files with status: superseded) plus the prior `docs/ARCHITECTURE.md`. It does NOT load `.claude/current-slice/` artifacts or phase-role context — this is the session isolation contract from cliff-failure-mode-and-v1-defenses D1 and context-discipline-protocol INV-002.
2. Run `uv run python .slice-system/scripts/validate_architecture.py`. If the validator exits non-zero and `ADR_D1_BYPASS` is not set, the slice MUST NOT transition to `status: complete`. Print the validator output and instruct the operator to either fix the ADR/architecture inconsistency or set `ADR_D1_BYPASS=1` to bypass.
3. **Bypass escape hatch.** If `ADR_D1_BYPASS=1` is set and the validator fails, completion proceeds. Append a line to `.claude/d1-bypasses.log` in the format: `<slice-id> <YYYY-MM-DD> <one-line-reason>`. The log is append-only and does not exist until the first bypass.
4. **Rolling-window check.** After logging a bypass, count entries in `.claude/d1-bypasses.log` whose slice-id numeric suffix falls within the last 10 slices. If 3 or more bypasses exist in that window, print a warning: "D1 design review recommended — three bypasses in the last 10 slices suggests the validator is producing more noise than signal."

#### D3 Gates (parallel subagents, after D1)

After D1 completes, dispatch two parallel subagents:

**Subagent A — Integration gate:**
```bash
python3 scripts/integration_gate.py
```
Runs Step 3 (invariant assertions via `validate_architecture.py` Check D) + Step 4 (ruff check + pytest) without short-circuiting. Returns pass/fail + details. Exit 0 = pass, 1 = fail, 2 = missing prerequisites.

**Subagent B — Snapshot diff:**
```bash
python3 scripts/snapshot_diff.py --diff
python3 scripts/snapshot_diff.py --snapshot   # update baseline on pass
```
Compares current file tree against `.claude/structural-snapshot.json`. Reports out-of-envelope changes (new/deleted/changed files not matched by intent.md envelope globs). Exit 0 = clean, 1 = out-of-envelope changes found, 2 = no prior snapshot (creates one).

Each subagent returns a short pass/fail report (≤200 words). If either D3 gate fails, the slice MUST NOT transition to `status: complete` — same semantics as D1.

**D3 bypass escape hatch.** If `D3_GATE_BYPASS=1` is set and a D3 gate fails, completion proceeds. Append a line to `.claude/d3-bypasses.log` in the format: `<slice-id> <YYYY-MM-DD> <one-line-reason>`. Rolling-window check: 3+ bypasses in last 10 slices triggers a warning: "D3 design review recommended — three bypasses in the last 10 slices suggests the gates are producing more noise than signal."

### Completion Sequence

1. Update `slice.yaml`: set `status: complete`, `completed: <today>`
2. Check if an integration sweep is due: read `.claude/sweep.yaml` and count `^slice: .* — complete$` commits on the current branch since the commit that completed the slice named in `last-sweep-at-slice-id:` (exclusive of that commit). A sweep is due when that count is ≥ `sweep-interval`. If `last-sweep-at-slice-id:` is `null` or its completion commit cannot be located in git history, fall back to "sweep due" and emit a one-line stderr diagnostic — conservative default so sweeps are not silently skipped. If `sweep.yaml` is missing, create it with defaults (same as Step 4) before checking.
3. If sweep is due, suggest: "This is slice N — an integration sweep is due. Run `/integration-sweep` in a fresh session."
4. Stage the completion state AND the removal of every file under `.claude/current-slice/` in a single commit. The cleanest form is one commit that both updates `slice.yaml` → `status: complete` and removes the rest of the directory:
   ```
   git add .claude/current-slice/slice.yaml
   git rm -r .claude/current-slice/intent.md .claude/current-slice/validation .claude/current-slice/implementation .claude/current-slice/integration .claude/current-slice/handoff-phase-*.md
   git commit -m "slice: <name> — complete"
   ```
   If a file listed above does not exist (for example, a slice that never entered Phase 4 `integration/`), omit it from the `git rm` call; do not fail the close on a missing optional artifact. A follow-up close commit is an acceptable alternative when a single commit would be awkward, but no file under `.claude/current-slice/` may survive the close sequence — `slice.yaml` itself is the one exception because the `status: complete` commit needs somewhere to live until the next slice overwrites it.
5. Run `/handoff` to package session context
6. For the next slice or sweep, start a fresh session and run `/catchup` to orient

## Step 8: Failed Slice Recovery

When a slice fails Phase 4 because the implementation is fundamentally wrong (not because an invariant is outdated — that's the escape hatch in Phase 4), the slice must be retired and retried fresh.

Usage: `/start-slice failed` (when current slice has status `integration` and Phase 4 has failed)

1. Read `slice.yaml` to get the slice ID and title
2. Update `slice.yaml`: set `status: failed`, add `failure-reason: "<brief description of Phase 4 failure>"`
3. Commit the failed state: `git add .claude/current-slice/ && git commit -m "slice: <name> — failed (Phase 4: <reason>)"`
4. Create an archive directory: `.claude/completed-slices/` (if it doesn't exist)
5. Move the failed slice: `mv .claude/current-slice/ .claude/completed-slices/<SLICE-ID>-failed/`
6. Recreate an empty `.claude/current-slice/` with just `.gitkeep`
7. Report to the user:

> Slice <ID> has been archived to `.claude/completed-slices/<ID>-failed/`.
> The Phase 4 failure analysis is preserved in the archive.
>
> To retry: run `/start-slice` to create a new slice. Include the failure reason
> in the new slice's intent — it becomes input context for the retry, preventing
> the same mistake from recurring.

The failed slice's intent, tests, implementation, and failure notes are all preserved in the archive for reference. The new slice starts fresh through all 4 phases — this is deliberate, not wasteful. The fresh context is what catches the correlated error that caused the failure.

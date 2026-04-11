# SLICE-002 Phase 2 — Validation Approach (STOPPED)

Status: **stopped** on 2026-04-11 pending `/decision` on cairn's test pyramid and substrate strategy (language/runtime for the AI-managed codebase).

No test file written. Brainstorming conclusions preserved here so resume does not re-derive them.

## V2 ambiguity — resolved (option B, shared-window)

Intent §V2 token-budget check says: _"the literal substring `150` and `400` both appear within 100 characters of the word `token`"_.

**Chosen reading**: there must exist a single occurrence of `token` in the file such that both `150` and `400` appear within ±100 characters of that occurrence.

Rejected alternatives:

- **(A) independent proximity** — `150` near some `token`, `400` near some (possibly different) `token`. Too loose: two unrelated `token` mentions could pass even if the budget is not actually documented as a single fact.
- **(C) strict regex** — e.g. `150[\s–\-]*400\s+tokens?`. Too tight: rejects legitimate phrasings like "150 tokens minimum, 400 tokens maximum" that satisfy the spec in spirit.

Option B catches the real failure mode (budget not documented as a single fact) without binding Phase 3 to exact punctuation.

## V4 sub-resolutions (not flagged, resolved locally)

- **Step 7 scope**: slice `start-slice.md` by `## Step 7` … `## Step 8`, run the 300-char proximity check inside that slice, case-insensitive on the wipe verbs.
- **Step 8 unchanged check**: slice by `## Step 8` to EOF, assert `.claude/completed-slices/` still present there.
- **Wipe-keyword list**: stay inclusive (`wipe`, `rm -r`, `git rm`, `remove`, `delete`). Handoff-phase-1 explicitly said do not narrow.

## V6 sub-resolutions

- **Section slicing**: find `## Context Discipline Protocol`, walk to next line starting with `## ` or EOF.
- **Old section cross-reference**: EITHER no `## Session Handoff Protocol` section remains, OR if it remains, the phrase `Context Discipline Protocol` appears in it (covers both "markdown link" and "literal phrase" from intent).

## V7 scope

`rglob("*.md")` under `commands/` and `templates/`. Both directories are markdown-only in practice.

## Test design — Approach 1+ (primitive layer + 7 flat functions)

Rejected alternatives:

- **Approach 1** (flat functions with inline logic) — too much boilerplate; fails cairn's own thesis that _"better testing enables better code"_. If cairn can't dogfood this, the thesis is hollow.
- **Approach 2** (parametrized with V-spec dataclass) — V1–V7 check shapes are too heterogeneous; dispatcher degenerates into 7 branches and the "data table" becomes a facade over the same per-V logic, plus indirection. Failure messages become less informative.
- **Approach 3** (test class with methods) — zero gain over module-level flat functions; drifts from `tests/unit/test_validate_architecture.py` — cairn's only existing test file and the style anchor.

**Chosen**: flat `test_vN_*` functions (matches cairn's only existing test-file convention, gives best pytest failure messages — the failing V is named in the test ID) **with a primitive layer at the top of the file** absorbing all the repeated parse/assertion logic.

### The primitive layer

Module-level pure functions, zero state, each with one job and a structured return:

```python
def slice_frontmatter(text: str) -> str | None
def slice_section(text: str, header: str) -> str | None
def contains_all(text: str, phrases: list[str], *, case_insensitive=False) -> list[str]  # returns MISSING phrases
def contains_none(text: str, phrases: list[str], *, case_insensitive=False) -> list[str]  # returns FORBIDDEN phrases found
def shared_window(text: str, a: str, b: str, anchor: str, window: int = 100) -> bool
def proximity(text: str, keyword: str, anchor: str, max_distance: int = 300, case_insensitive=False) -> bool
def rglob_missing(root: Path, glob: str, banned: list[str]) -> list[tuple[Path, str]]
```

Rationale: primitives return structured data so assertion messages can name the specific failure (e.g. `"section missing required keywords: ['DISPATCH', 'SLICE-003']"`) rather than just "assert failed".

### What a test body looks like

V6 (the nastiest of the seven), as a worked example:

```python
def test_v6_operational_reference_documents_protocol():
    """V6 — operational-reference.md has a Context Discipline Protocol section
    with all required keywords; old Session Handoff Protocol section either
    gone or cross-references the new protocol."""
    text = (CAIRN_ROOT / "docs/operational-reference.md").read_text()

    section = slice_section(text, "## Context Discipline Protocol")
    assert section is not None, "missing `## Context Discipline Protocol` section"

    missing = contains_all(section, ["150", "400", "Tier 1", "Tier 2", "DISPATCH", "learning.md", "SLICE-003"])
    assert not missing, f"section missing required keywords: {missing}"
    assert "wipe" in section or "remove" in section, "no wipe/remove keyword in section"

    old = slice_section(text, "## Session Handoff Protocol")
    assert old is None or "Context Discipline Protocol" in old, \
        "old Session Handoff Protocol section exists but does not cross-reference the new protocol"
```

9 lines of body, reads like the intent bullets, failure messages name the specific missing thing.

### Known issue recorded for future refactor

Flat `test_vN_*` shape scales linearly with V count. At ~10–12 Vs it starts to hurt — repeated module-level declarations, harder to navigate. Revisit organization then; candidate refactor is parametrized tests with a rich V-spec dataclass once enough shared structure exists to justify it. Do not pre-abstract. The primitive layer carries most of the weight until that point.

## Testing pyramid — mapping (not ratified)

Locating V1–V7 in the testing pyramid surfaced that they are **not unit tests**. There is no code under test. They are **contract-conformance tests**: static artifacts (Phase 3's rewritten files) must match intent.md's spec.

| Layer | Purpose | Cairn example |
|---|---|---|
| **Unit** (base) | Pure functions | The 7 primitives above |
| **Property** (middle) | Invariants over input spaces | `slice_section` round-trip; `shared_window` edge cases — would use `hypothesis` |
| **Contract conformance** *(outside the classic pyramid)* | Static artifacts match spec | **V1–V7** |
| **Behavior** (top) | Observable end-to-end | "real `/catchup` lands ≤30k tokens on a real handoff" — needs consumer-level fixtures, out of SLICE-002 envelope |
| ~~Eval-based~~ | ~~LLM-as-judge~~ | **never, by agreement** |

This mapping is what Phase 2 would have committed to in `validation/approach.md` on completion. Flagging it here so it is not re-derived on resume.

## Open sub-decisions deferred to `/decision`

These blocked Phase 2 closure, which is why the slice is stopped rather than completed:

1. **Adopt `hypothesis` as a Python test dependency** to property-test the primitive layer. Cairn currently has zero Python runtime dependencies. Adding one is an architectural move, needs explicit commitment.
2. **Cairn's test-pyramid commitment** — is the unit/property/contract/behavior pyramid (explicitly no eval-based) cairn's self-applied testing discipline going forward? This is a durable commitment, ADR-shaped.
3. **Substrate strategy** — for an AI-managed codebase, which language/runtime makes bugs hardest to write given:
   - **Training data density** (AI code quality correlates with corpus size)
   - **Iteration loop speed** (compile/type-check cycles burn agent context)
   - **Ability to encode invariants in types** ("make illegal states unrepresentable")
   - **Consumer-via-symlink distribution model** (`.slice-system → .` — all text files, no binary)
   - **Actual bug surface** of cairn today (shell hooks parsing JSON tool input, Python markdown/ADR walker, markdown skill templates)

   Candidates surfaced during brainstorming (**not ranked**, will be revisited in the decision session):

   - **Rust** — strongest runtime guarantees; borrow checker + compile times hostile to AI iteration; poor fit for consumer distribution model.
   - **Haskell** — most expressive types; thin AI training data; slow tooling; niche.
   - **OCaml** — fast compile, strong ADTs, respectable training data, used in tooling (Flow, Rescript, Dune). Dark-horse contender.
   - **Functional Lisp (Clojure/Racket/Janet/Fennel)** — best edit-eval feedback loop via REPL; homoiconic; thin training data; homoiconicity partly moot since cairn's skills are markdown.
   - **TypeScript with `strict`** — massive training data; discriminated unions for "illegal states unrepresentable"; Deno gives scriptable distribution without a build step.
   - **Python + mypy-strict + hypothesis + shellcheck** — stay on current substrate, layer tooling. Lowest switching cost.

   The real axis is not "which language is safest" but **"which language makes cairn's specific bug classes hardest to introduce while keeping the AI iteration loop tight"** — and that answer depends on naming cairn's actual bug classes first.

## What resume needs

**If decision says "stay on current substrate":**

- Pick up this approach.md unchanged
- Answer sub-decision (1) — hypothesis yes/no — append to this file
- Write `tests/unit/test_context_discipline_protocol.py` with the primitive layer and V1–V7 thin test functions
- Commit, verify Phase 2 gate, handoff to Phase 3

**If decision says "rewrite substrate":**

- SLICE-002's envelope probably changes (test file language/location differs)
- Re-evaluate whether the primitive-layer sketch translates to the new language
- V2 (B), V4, V6, V7 sub-resolutions are language-independent and remain valid
- May need a new slice superseding SLICE-002, or an intent.md amendment

## Do NOT re-derive on resume

- V2 → option B (shared-window)
- V4 Step 7 slice-scope + Step 8 EOF slice-check + case-insensitive wipe-keywords
- V6 section-slicing rule + old-section cross-reference rule
- V7 `rglob("*.md")` across `commands/` and `templates/`
- Approach 1+ (primitive layer + flat `test_vN_*` functions)
- Pyramid mapping for V1–V7 as **contract-conformance** (not unit)
- The rejected alternatives and why they were rejected

---
id: graduated-contract
name: "Graduated-contract + completeness-floor rules in templates/intent.md (ADR D3)"
snapshot-sha: ef14b98
invariants-touched: []
---

## What

Add guidance to `templates/intent.md` that realizes ADR D3 for the `cairn-intent`
loop: (i) the exception-tag DIAL — the four tags (`universal-set`,
`regression-meta`, `operator-bound`, `trivial-existence`) with one-line semantics
each, framed as the mechanism by which contract depth GRADUATES by size; (ii) the
completeness floor — a required one-line scope-statement in every contract; and
(iii) how depth graduates from a trivial one-line must-satisfy clause up to the
full EARS grammar + premise grounding on heavy work. Add a unit test asserting the
template carries the four tag names AND the scope-statement requirement.

## Why

ADR D3 (`docs/adr/intent-management-loop.md`) decides: contract mandatory, depth
graduated by size via the four exception tags, completeness floor = a one-line
scope-statement (attackable by the front-challenge) + close-review smell-testing
depth-vs-diff, NO hard cardinality gate. The mechanism is decided; this increment
is the template REALIZATION + a regression test. Enforcement lives in the
subagents (intent-challenge attacks the scope-statement; #1 close-review
smell-tests depth-vs-diff), so this increment adds NO mechanical gate.

## Boundary

Does NOT:
- Add or modify any code, hook, or validator assertion (`atomicity_guard.py`,
  `premise_guard.py`, `scripts/lib/atomicity.py`, `scripts/validate_architecture.py`
  are all unchanged — this is template guidance + a test only).
- Add a hard cardinality gate or any mechanical contract-depth enforcement. ADR D3
  is explicit: "No hard cardinality gate." Depth is enforced by the two subagent
  checkpoints, not in the template.
- Change the four exception-tag names, their declaration rules, or the atomicity
  heuristic — those ship in `scripts/lib/atomicity.py` and are cited, not redefined.
- Touch the eight Phase-1 schema headings or the existing `## Contract` /
  `## Premise Grounding` blocks beyond ADDITIVE guidance (ADD-not-REPLACE).
- Edit `workflows/cairn-intent.yaml` or the ADR (those are the sources, not targets).
- Make the scope-statement machine-checked — it is operator/front-challenge-bound
  prose, the same honest limit as the atomicity tag declarations.

## Specification

Canonical landing targets (LAND LATER, not written by this run):

- `templates/intent.md` — ADDITIVE guidance, all inside the `## Contract` section
  comment text and/or a short adjacent comment:
  - **Scope-statement requirement (completeness floor):** state that every
    contract carries a one-line scope-statement naming what the diff is allowed to
    touch / what "done" means; it is the floor the front-challenge attacks. Phrase
    it as a REQUIREMENT ("carry a one-line scope-statement"), not a suggestion.
  - **Graduation dial:** state that depth graduates by size — trivial work may be a
    single one-line `must-satisfy` clause (optionally `trivial-existence`-tagged);
    heavy work expands to the full EARS grammar + `## Premise Grounding`. The four
    exception tags are the dial: each tag is the one-line escape that keeps a
    larger clause thin instead of forcing a split.
  - **Four tag semantics:** one line each for `universal-set`, `regression-meta`,
    `operator-bound`, `trivial-existence` (the tag NAMES must appear in the file).
- `tests/unit/test_intent_template_graduated_contract.py` — new unit test asserting
  `templates/intent.md`:
  - contains all four exception-tag names (parity with
    `scripts/lib/atomicity.EXCEPTION_TAGS`), AND
  - carries the scope-statement requirement (assert the literal token
    `scope-statement` is present in the template text).

Wire format / literals Phase-2-equivalent tests pin:
- Tag set source of truth: `scripts/lib/atomicity.EXCEPTION_TAGS` =
  `{"universal-set", "regression-meta", "operator-bound", "trivial-existence"}`.
- Scope-statement marker token: `scope-statement` (the test greps for this literal;
  the template guidance must use that exact hyphenated token).

## Verification

- `uv run pytest tests/unit/test_intent_template_graduated_contract.py -q` — green:
  asserts the four tag names present + the `scope-statement` token present.
- `uv run pytest tests/unit/test_template_extraction.py -q` — STILL green: the
  eight-heading-in-order assertion, the `## Contract` parseable-YAML assertion, and
  `test_intent_template_contract_tags_match_exception_tags` are unaffected
  (ADD-not-REPLACE; the existing tag-parity test already covers tag presence, so the
  new test's distinct value is the scope-statement requirement + graduation framing).
- `uv run pytest -q` — full suite, prior count + 1 new test file, 0 new failures.
- Drift audit: the four tag names documented in `templates/intent.md` equal
  `scripts/lib/atomicity.EXCEPTION_TAGS` (the existing
  `test_intent_template_contract_tags_match_exception_tags` enforces this; the new
  test must not contradict it).

## Risk Surface

The domain-level miss that passes CI: the template adds tag NAMES and the
`scope-statement` token (test goes green) but the graduation PROSE is incoherent or
contradicts D3 — e.g. it implies a cardinality gate, or frames the scope-statement
as optional. A grep-based test cannot catch semantic wrongness; the front-challenge
reading the template and the operator review are the real check. Second miss:
guidance duplicates rather than cross-references the atomicity tag rules, letting
the template tag set drift from `atomicity.py` (mitigated by the existing parity test).

## Feature-Local Invariants

- FLI-1: The four exception-tag names in `templates/intent.md` MUST equal
  `scripts/lib/atomicity.EXCEPTION_TAGS` exactly — single source of truth is the
  code, the template cites it.
- FLI-2: The scope-statement is documented as REQUIRED (the completeness floor),
  never as optional; and NO mechanical/cardinality enforcement is introduced.
- FLI-3: All template changes are ADDITIVE — the eight Phase-1 headings and the
  existing `## Contract` + `## Premise Grounding` blocks remain present and parseable.

## Explicit Scope-Out

- The intent-challenge attack on the scope-statement and the #1 close-review
  depth-vs-diff smell-test — those are subagent behaviors (separate increments),
  not template text.
- Any change to `atomicity_guard.py` / `scripts/lib/atomicity.py` behavior, the
  EARS shapes, or the declaration-required rules.
- Making the `## Contract` block mandatory by default (ADR D6 / Trial-D boundary
  keeps it optional + fail-open; flipping that is a separate `/decision`).
- Multi-operator / multi-branch intent reconciliation (ADR D8, EXPOSED + deferred).

## Premise Grounding

```yaml
premises:
  - source: docs/adr/intent-management-loop.md
    quote: |
      carries at least a thin (one-liner) intent; depth graduates by size via the D3 exception tags.
    label: "ADR D3 decides depth graduates by size via the four exception tags — this increment realizes that dial in the template."
  - source: docs/adr/intent-management-loop.md
    quote: |
      a one-line scope-statement in the contract (attackable by the
    label: "ADR D3 defines the completeness floor as a one-line scope-statement — the scope-statement requirement this template adds."
  - source: docs/adr/intent-management-loop.md
    quote: |
      front-challenge) + the close-review smell-testing contract-depth against diff size. No hard
    label: "ADR D3 forbids a hard cardinality gate; enforcement is the front-challenge + close-review, not the template — so this increment adds no mechanical gate."
  - source: scripts/lib/atomicity.py
    quote: |
      {"universal-set", "regression-meta", "operator-bound", "trivial-existence"}
    label: "EXCEPTION_TAGS is the source of truth for the four tag names the template must carry (FLI-1 parity)."
  - source: workflows/cairn-intent.yaml
    quote: |
      description: One-line scope statement plus must-satisfy floor.
    label: "The load-or-form-intent node's contract-floor evidence is the one-line scope statement plus must-satisfy floor this template guidance realizes."
  - source: templates/intent.md
    quote: |
      except: "universal-set: the consumer set is the 3 repos listed in roadmap.md"
    label: "The template already carries a worked exception-tag example; graduation guidance is ADD-not-REPLACE on top of the existing Contract block."
```

## Contract

```yaml
must-satisfy:
  - clause: where heavy intent work, the template shall document all four exception tags as the depth-graduation dial
    except: "universal-set: the set is the four tags in scripts/lib/atomicity.EXCEPTION_TAGS — universal-set, regression-meta, operator-bound, trivial-existence"
  - the template shall require a one-line scope-statement as the contract completeness floor
  - clause: when contract depth changes, the template shall describe graduation from a one-line must-satisfy clause up to full EARS grammar plus premise grounding
    except: "regression-meta: baseline is the existing eight Phase-1 headings plus the Contract and Premise Grounding blocks, which stay present and parseable (ADD-not-REPLACE)"
  - the new unit test shall assert templates/intent.md carries the scope-statement token
  - clause: the new unit test shall assert the four exception-tag names are present in templates/intent.md
    except: "universal-set: the four tag names are universal-set, regression-meta, operator-bound, trivial-existence per scripts/lib/atomicity.EXCEPTION_TAGS"
must-not-violate:
  - the eight Phase-1 schema headings stay present and in order (test_template_extraction green)
  - no hard cardinality gate or mechanical contract-depth enforcement is introduced
  - the four tag names in the template equal scripts/lib/atomicity.EXCEPTION_TAGS exactly
  - no code, hook, or validator assertion is modified (template plus test only)
wrong-if:
  - the template frames the scope-statement as optional rather than required
  - the graduation prose implies or adds a cardinality or diff-size gate
  - the template redefines a tag name or declaration rule instead of citing atomicity.py
  - the new test passes while the template guidance contradicts ADR D3 (grep-green but semantically wrong)
escalate-when:
  - the template needs a STRUCTURAL change (new heading, reordered blocks) to carry the graduation guidance — that is decision-weight, surface to operator
  - realizing D3 appears to require touching atomicity.py or the YAML node contract
evidence:
  - uv run pytest tests/unit/test_intent_template_graduated_contract.py -q is green
  - uv run pytest tests/unit/test_template_extraction.py -q stays green
  - uv run pytest -q reports prior count plus the one new test file with zero new failures
  - grep of templates/intent.md shows the four tag names and the scope-statement token
execution-scope:
  - templates/intent.md
  - tests/unit/test_intent_template_graduated_contract.py
```

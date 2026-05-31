# EXAMPLE walkthrough — what authoring a `## Contract` looks like

DEMO ONLY. A throwaway toy feature (`slugify`), **not** one of the three measured intents.
It exists so you can see the prose → EARS → atomicity loop concretely before you author m2.
Nothing here counts toward the measurement.

## Toy feature (prose — the way an intent's `## Specification` reads)

`slugify(text) -> str` turns a title into a URL slug. Behaviors:

1. Empty input returns an empty string.
2. Spaces become hyphens and uppercase becomes lowercase.
3. Every output character is within the URL-safe set.
4. Existing callers of the old `slug()` helper are unchanged.
5. A `slugify` function exists in `scripts/lib/slug.py`.

## The four moves (this is the whole skill)

| Prose behavior | Move | Why |
|---|---|---|
| 1. empty → empty | **bare atomic** | one check, one assert — a plain EARS string. |
| 2. spaces→hyphens AND upper→lower | **split** | two independent checks; the gate flags a verb-conjunction, so you write two clauses. |
| 3. every char URL-safe | **tag `universal-set`** | quantifies over a set; can't be one assert. Tag it, declare the set. |
| 4. callers unchanged | **tag `regression-meta`** | a "nothing broke" meta-claim; tag it, name the baseline. |
| 5. function exists | **bare** (or tag `trivial-existence`) | a single file/symbol existence check is already atomic. |

A clause is **atomic** iff one tool call / one file check proves it. Untagged clauses must be
atomic; non-atomic ones either split or carry a tag. Tagging is a one-line escape — you are
**not** expected to make every clause bare-atomic.

## Contract

```yaml
must-satisfy:
  # 1 — bare atomic
  - the slugify function shall return an empty string when given empty input
  # 2 — split (the prose conjoined two checks)
  - when the input contains a space, slugify shall replace it with a hyphen
  - when the input contains an uppercase letter, slugify shall lowercase it
  # 3 — quantifies over a set -> universal-set tag; declaration enumerates the set
  - clause: all output characters fall within the URL-safe set
    except: "universal-set: the URL-safe set is [a-z0-9-]"
  # 4 — "unchanged" meta-claim -> regression-meta tag; declaration names the baseline
  - clause: existing callers of slug() behave unchanged
    except: "regression-meta: baseline is the pre-change tests/unit/test_slug.py suite"
  # 5 — pure existence -> bare (trivial-existence tag also fine; it needs no declaration)
  - a slugify function is present in scripts/lib/slug.py
must-not-violate: []
wrong-if: []
escalate-when: []
evidence: []
execution-scope: []
```

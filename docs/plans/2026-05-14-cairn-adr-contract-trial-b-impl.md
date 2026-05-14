# ADR Contract Trial B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind a `contract:` block to `docs/adr/identifier-scheme.md` and ship 6 deterministic invariant tests in `tests/unit/test_identifier_scheme_contract.py` that enforce D1+D2+D3+D5+D9 against live filesystem state — the second trial of cairn's interaction-protocol reframe.

**Architecture:** Tests live in one pytest module; each `test_dN_*` function scans `docs/adr/*.md` and/or `.claude/features/*.yaml` and asserts a single contract clause. Module-level helpers (`_parse_frontmatter`, `_adr_files`, `_adr_ids`, `_feature_files`) are reused across tests. The contract block is added to the ADR's frontmatter via an `Edit` whose `old_string` starts at `firmness: firm` to satisfy `reversibility-guard.sh`. The handoff is updated to track the trial in flight and (on close) record the deferred legacy-label retrofit.

**Tech Stack:** Python 3.12, pytest 9.0, pyyaml (all in current deps; no new deps). Test runtime budget ≤5 seconds.

**Spec:** `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`

---

## File Structure

- **Create:** `tests/unit/test_identifier_scheme_contract.py`
  - Module docstring linking to spec
  - Module-level helpers: `_parse_frontmatter`, `_adr_files`, `_feature_files`, `_adr_ids`, `_resolve_adr_id_token`
  - Module-level constant: `LEGACY_LABEL_BASELINE = 10` (from spec audit)
  - 6 test functions: `test_d1_entities_have_id`, `test_d1_entities_have_human_label`, `test_d2_id_shape_matches_entity_type`, `test_d3_superseded_ids_intact`, `test_d5_feature_files_well_formed`, `test_d9_adr_cross_references_resolve`

- **Modify:** `docs/adr/identifier-scheme.md`
  - Insert `contract:` block in frontmatter directly after `firmness: firm` line (Edit gated by reversibility-guard.sh)

- **Modify:** `.claude/handoff.md`
  - One body line added at start of work: `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md open Trial-B-in-flight`
  - Updated at end: `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md deferred legacy-label-retrofit`

---

## Task 0: Open the trial in handoff

**Files:**
- Modify: `.claude/handoff.md` (body)

- [ ] **Step 1: Add the open entry**

Edit `.claude/handoff.md`. After the line `- docs/plans/2026-05-13-cairn-as-interaction-protocol.md open Trial-A-in-flight`, insert a new body line:

```
- docs/plans/2026-05-14-cairn-adr-contract-trial-b.md open Trial-B-in-flight
```

- [ ] **Step 2: Verify handoff contract still passes**

Run: `uv run pytest tests/unit/test_handoff_contract.py -v`
Expected: 5 passed (the new entry resolves to a real file, parses as a valid pointer line).

- [ ] **Step 3: Commit**

```bash
git add .claude/handoff.md
git commit -m "$(cat <<'EOF'
chore(handoff): track Trial B open

ADR-contract trial on identifier-scheme begins. Handoff entry tracks
it as open until tests are GREEN, then converts to deferred for the
legacy-label retrofit follow-up.
EOF
)"
```

---

## Task 1: D1 — every entity has `id:`

**Files:**
- Create: `tests/unit/test_identifier_scheme_contract.py`
- Test: `tests/unit/test_identifier_scheme_contract.py::test_d1_entities_have_id`

- [ ] **Step 1: Write helpers + first test**

Create `tests/unit/test_identifier_scheme_contract.py` with:

```python
"""Trial B: docs/adr/identifier-scheme.md decisions enforced as a contract.

See docs/plans/2026-05-14-cairn-adr-contract-trial-b.md.
Scope: D1 (entity has id + human label), D2 (id shape per type),
D3 (supersession id integrity), D5 (feature metadata), D9 (cross-ref resolution).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_DIR = CAIRN_ROOT / "docs" / "adr"
FEATURE_DIR = CAIRN_ROOT / ".claude" / "features"

LEGACY_LABEL_BASELINE = 10  # ADRs lacking both `name:` and `title:` at audit (2026-05-14)

FLAT_SLUG = re.compile(r"^[a-z][a-z0-9-]*$")
HIERARCHICAL_SLUG = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")


def _parse_frontmatter(path: Path) -> dict:
    """Return parsed YAML frontmatter (or whole-file YAML for .yaml inputs)."""
    text = path.read_text()
    if path.suffix == ".yaml":
        return yaml.safe_load(text) or {}
    if not text.startswith("---\n"):
        return {}
    rest = text[4:]
    end = rest.find("\n---\n")
    if end < 0:
        return {}
    return yaml.safe_load(rest[:end]) or {}


def _adr_files() -> list[Path]:
    """All ADR files except the index."""
    return sorted(p for p in ADR_DIR.glob("*.md") if p.name != "index.md")


def _feature_files() -> list[Path]:
    """All feature files."""
    return sorted(FEATURE_DIR.glob("*.yaml"))


def _adr_ids() -> set[str]:
    """All ADR `id:` values."""
    return {_parse_frontmatter(p).get("id", "") for p in _adr_files()} - {""}


def test_d1_entities_have_id():
    """D1: every entity file (ADR, feature) has id in frontmatter."""
    missing = []
    for p in _adr_files() + _feature_files():
        front = _parse_frontmatter(p)
        if not isinstance(front.get("id"), str) or not front["id"].strip():
            missing.append(str(p.relative_to(CAIRN_ROOT)))
    assert not missing, f"entities missing id: {missing}"
```

- [ ] **Step 2: Run; expect either PASS or specific drift list**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d1_entities_have_id -v`
Expected: PASS (every ADR and feature file in the audit has `id:`).

If FAIL: fix the entity by adding the missing `id:` field via an `Edit` whose `old_string` starts at the topmost frontmatter key. Re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D1 — entities have id

Trial B's first invariant: every ADR and feature file frontmatter
carries `id:` as a non-empty string. Establishes the test module
helpers (_parse_frontmatter, _adr_files, _feature_files, _adr_ids).
EOF
)"
```

---

## Task 2: D1 — every entity has a human label (advisory baseline)

**Files:**
- Modify: `tests/unit/test_identifier_scheme_contract.py`
- Test: `tests/unit/test_identifier_scheme_contract.py::test_d1_entities_have_human_label`

- [ ] **Step 1: Append the test function**

Append to `tests/unit/test_identifier_scheme_contract.py`:

```python
def test_d1_entities_have_human_label():
    """D1 advisory: count of entities lacking name AND title must be ≤ baseline.

    The identifier-scheme ADR's D7 migration is forward-only; pre-existing ADRs
    were not retrofit. This test enforces no-new-drift via a baseline constant
    rather than failing on legacy state. Lower the baseline as ADRs are normalised.
    """
    legacy = []
    for p in _adr_files():
        front = _parse_frontmatter(p)
        has_name = isinstance(front.get("name"), str) and front["name"].strip()
        has_title = isinstance(front.get("title"), str) and front["title"].strip()
        if not (has_name or has_title):
            legacy.append(p.name)

    assert len(legacy) <= LEGACY_LABEL_BASELINE, (
        f"ADRs without name/title increased above baseline "
        f"({len(legacy)} > {LEGACY_LABEL_BASELINE}): {sorted(legacy)}"
    )

    # Feature files should ALL have name (no legacy gap there per audit).
    feat_missing = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        if not (isinstance(front.get("name"), str) and front["name"].strip()):
            feat_missing.append(p.name)
    assert not feat_missing, f"feature files missing name: {feat_missing}"
```

- [ ] **Step 2: Run; expect PASS at baseline**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d1_entities_have_human_label -v`
Expected: PASS (10 ADRs at baseline, all features have name).

If count > 10: a new ADR was added without `name:` after baseline capture. Either retrofit the new ADR or bump baseline.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D1 — human-label advisory baseline

Pre-existing 10 ADRs lack frontmatter name/title. Per spec's narrowing
resolution, advisory test asserts count ≤ LEGACY_LABEL_BASELINE rather
than failing on legacy state. Forward gate: any new ADR without name
trips the test.
EOF
)"
```

---

## Task 3: D2 — id shape (strict for ADRs+features, advisory for slices)

**Note:** original T3 defined a single `test_d2_id_shape_matches_entity_type`. During implementation, 6 slice-id violations surfaced (4 uppercase Y/Z categoricals in `compression.yaml`, 1 dotted Claude Code version in `housekeeping.yaml`, 1 prefix mismatch in `orchestrator-paths.yaml`). Per operator decision (2026-05-14): narrow D2 to strict ADR+feature checks; add advisory baseline for slice ids mirroring T2's pattern.

**Files:**
- Modify: `tests/unit/test_identifier_scheme_contract.py`
- Tests: `test_d2_strict_id_shape_for_adrs_and_features`, `test_d2_slice_id_shape_advisory_baseline`

- [ ] **Step 1: Add baseline constant**

Find the `LEGACY_LABEL_BASELINE` constant. Below it, add:

```python
LEGACY_SLICE_ID_BASELINE = 6  # slice ids violating D2 shape at audit (2026-05-14)
```

- [ ] **Step 2: Append two test functions**

Append to `tests/unit/test_identifier_scheme_contract.py`:

```python
def test_d2_strict_id_shape_for_adrs_and_features():
    """D2 strict: ADR and feature ids match the flat semantic slug shape."""
    bad = []
    for p in _adr_files():
        adr_id = _parse_frontmatter(p).get("id", "")
        if not FLAT_SLUG.match(adr_id):
            bad.append(f"adr {p.name}: id={adr_id!r}")
    for p in _feature_files():
        feat_id = _parse_frontmatter(p).get("id", "")
        if not FLAT_SLUG.match(feat_id):
            bad.append(f"feature {p.name}: id={feat_id!r}")
    assert not bad, "id-shape violations:\n  " + "\n  ".join(bad)


def test_d2_slice_id_shape_advisory_baseline():
    """D2 advisory: slice id violations ≤ baseline.

    Slice ids predate identifier-scheme's lowercase-kebab-case rule in some
    cases (semantic uppercase categoricals, version-dotted ids, slice-moved-
    without-rekey). D1 says ids are immutable — this advisory ceiling permits
    the legacy state while gating any new violations. Lower the baseline as
    historical slices are renamed (deferred decision).
    """
    bad = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        feat_id = front.get("id", "")
        for entry in front.get("slices") or []:
            slice_id = (entry or {}).get("id", "")
            if not HIERARCHICAL_SLUG.match(slice_id):
                bad.append(f"{p.name}: id={slice_id!r}")
                continue
            prefix = slice_id.split("/", 1)[0]
            if prefix != feat_id:
                bad.append(
                    f"{p.name}: id={slice_id!r} prefix {prefix!r} "
                    f"!= feature id {feat_id!r}"
                )
    assert len(bad) <= LEGACY_SLICE_ID_BASELINE, (
        f"slice id violations increased above baseline "
        f"({len(bad)} > {LEGACY_SLICE_ID_BASELINE}):\n  " + "\n  ".join(bad)
    )
```

- [ ] **Step 3: Run new tests; expect PASS**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py -v`
Expected: **5 passed** (test_d1_entities_have_id, test_d1_adrs_have_human_label, test_d1_features_have_name, test_d2_strict_id_shape_for_adrs_and_features, test_d2_slice_id_shape_advisory_baseline)

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D2 — strict for ADR+feature, advisory for slices

Originally one test; split per operator decision after T3 surfaced 6
slice-id violations (Lever Y/Z categoricals, Claude Code version dots,
prefix mismatch). D1 immutability conflicts with retroactive D2
enforcement on existing slices — advisory baseline mirrors T2's pattern.
LEGACY_SLICE_ID_BASELINE = 6 captured at 2026-05-14 audit.
EOF
)"
```

---

## Task 4: D3 — supersession id integrity

**Files:**
- Modify: `tests/unit/test_identifier_scheme_contract.py`
- Test: `tests/unit/test_identifier_scheme_contract.py::test_d3_superseded_ids_intact`

- [ ] **Step 1: Append the test function**

Append to `tests/unit/test_identifier_scheme_contract.py`:

```python
def test_d3_superseded_ids_intact():
    """D3: ADR ids are unique; every superseded-by points to an existing ADR id."""
    ids: list[str] = []
    superseded_by_pairs: list[tuple[str, str]] = []
    for p in _adr_files():
        front = _parse_frontmatter(p)
        adr_id = front.get("id", "")
        if adr_id:
            ids.append(adr_id)
        target = front.get("superseded-by") or front.get("superseded_by")
        if isinstance(target, str) and target.strip():
            superseded_by_pairs.append((p.name, target.strip()))

    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"duplicate ADR ids: {duplicates}"

    known = set(ids)
    unresolved = [
        (src, tgt) for src, tgt in superseded_by_pairs if tgt not in known
    ]
    assert not unresolved, (
        f"superseded-by pointing to unknown ADR ids: {unresolved}"
    )
```

- [ ] **Step 2: Run; expect PASS**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d3_superseded_ids_intact -v`
Expected: PASS.

If duplicates: rare but indicates a copy-paste bug — fix manually.
If unresolved: a `superseded-by:` value points to an ADR that no longer exists. Fix by either restoring the target or correcting the value.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D3 — supersession id integrity

ADR ids unique across docs/adr; every superseded-by value resolves
to an existing ADR id. Catches the rename-without-sweep failure mode.
EOF
)"
```

---

## Task 5: D5 — feature metadata + no `epic:` field

**Files:**
- Modify: `tests/unit/test_identifier_scheme_contract.py`
- Test: `tests/unit/test_identifier_scheme_contract.py::test_d5_feature_files_well_formed`

- [ ] **Step 1: Append the test function**

Append to `tests/unit/test_identifier_scheme_contract.py`:

```python
def test_d5_feature_files_well_formed():
    """D5: feature files carry id, name, intent, shaped-from. No epic key."""
    required = {"id", "name", "intent", "shaped-from"}
    bad = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        missing = required - front.keys()
        if missing:
            bad.append(f"{p.name}: missing keys {sorted(missing)}")
        if "epic" in front:
            bad.append(f"{p.name}: forbidden `epic:` key present")
    assert not bad, "feature file violations:\n  " + "\n  ".join(bad)
```

- [ ] **Step 2: Run; expect PASS**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d5_feature_files_well_formed -v`
Expected: PASS (audit confirmed all 10 feature files have the required keys; `housekeeping.yaml`'s `shaped-from: null` is key-present, value-null — accepted).

If FAIL: add the missing key to the offending feature file (frontmatter edit).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D5 — feature metadata schema

Feature files carry id, name, intent, shaped-from (key present;
value may be null). No `epic:` key (must-not-violate folded in).
EOF
)"
```

---

## Task 6: D9 — ADR cross-references resolve

**Files:**
- Modify: `tests/unit/test_identifier_scheme_contract.py`
- Test: `tests/unit/test_identifier_scheme_contract.py::test_d9_adr_cross_references_resolve`

- [ ] **Step 1: Append helper + test function**

Append to `tests/unit/test_identifier_scheme_contract.py`:

```python
def _resolve_adr_id_token(token: str, known: set[str]) -> bool:
    """Return True if the first whitespace-separated token matches a known ADR id."""
    if not isinstance(token, str):
        return False
    head = token.strip().split()[0] if token.strip() else ""
    return head in known


def test_d9_adr_cross_references_resolve():
    """D9: adrs-referenced / supersedes / supersedes-sections values resolve to known ADR ids."""
    known = _adr_ids()
    bad = []
    cross_ref_keys = ("adrs-referenced", "supersedes", "supersedes-sections")
    for p in _adr_files():
        front = _parse_frontmatter(p)
        for key in cross_ref_keys:
            value = front.get(key)
            if value is None:
                continue
            items = value if isinstance(value, list) else [value]
            for item in items:
                if not item:
                    continue
                if not _resolve_adr_id_token(item, known):
                    bad.append(f"{p.name} {key}: {item!r} does not resolve")
    assert not bad, "unresolved cross-references:\n  " + "\n  ".join(bad)
```

- [ ] **Step 2: Run; expect FAIL with drift list**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d9_adr_cross_references_resolve -v`
Expected: likely FAIL with a list of unresolved cross-refs (per the spec's "remaining drift" prediction).

**Escalation check:** if the count > 5, STOP and surface to operator per the spec's renewed escalation rule.

If count ≤ 5: fix each one. For each unresolved ref:
- If the referenced ADR was renamed, update the cross-ref to the new id (frontmatter edit, gated by reversibility-guard.sh — `old_string` first line must start with status:/superseded-by:/firmness:)
- If the referenced ADR was deleted, drop the cross-ref entry
- If the cross-ref was a typo, correct it

After fixes, re-run the test.

- [ ] **Step 3: Re-run; expect PASS**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py::test_d9_adr_cross_references_resolve -v`
Expected: PASS.

- [ ] **Step 4: Run full module to confirm no regressions**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py -v`
Expected: 8 passed.

- [ ] **Step 5: Run full test suite to confirm no regressions elsewhere**

Run: `uv run pytest`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_identifier_scheme_contract.py docs/adr/
git commit -m "$(cat <<'EOF'
test(identifier-scheme): D9 — cross-references resolve

adrs-referenced / supersedes / supersedes-sections frontmatter fields
must point to existing ADR ids. Includes drift fixes discovered during
first run (cross-ref typos / stale renames).
EOF
)"
```

If no drift was discovered, drop `docs/adr/` from `git add`.

---

## Task 7: Add `contract:` block to identifier-scheme ADR

**Files:**
- Modify: `docs/adr/identifier-scheme.md` (frontmatter)

- [ ] **Step 1: Add the contract block**

Edit `docs/adr/identifier-scheme.md`. The Edit's `old_string` must start with `firmness: firm` to satisfy `reversibility-guard.sh`'s allow-rule for frontmatter edits.

`old_string`:
```
firmness: firm
supersedes: [semantic-identity]
```

`new_string`:
```
firmness: firm
contract:
  must-satisfy:
    - D1: every entity has id (strict) and a human label (name OR title; advisory baseline)
    - D2: ADR and feature ids are flat semantic slugs (strict)
    - D2: slice id-shape violations ≤ baseline (advisory; 6 at 2026-05-14)
    - D3: superseded ADR ids not reused; superseded-by chain resolves
    - D5: feature files carry id, name, intent, shaped-from (key present)
    - D9: ADR cross-reference fields resolve to existing ADR ids
  must-not-violate:
    - feature files carry an `epic:` field
    - new entity type added without amending D1/D2
  wrong-if:
    - any test_identifier_scheme_contract clause fails
    - new entity type appears in the codebase the model doesn't cover
    - any advisory baseline (legacy-label, slice-id-shape) is exceeded
  evidence:
    - tests/unit/test_identifier_scheme_contract.py passes
supersedes: [semantic-identity]
```

- [ ] **Step 2: Verify all tests still pass**

Run: `uv run pytest tests/unit/test_identifier_scheme_contract.py -v`
Expected: 8 passed.

- [ ] **Step 3: Verify reversibility-guard let the edit through**

The edit succeeded if the file was saved. If `reversibility-guard.sh` blocked it, the Edit returned an error before this step. If blocked unexpectedly, check that `old_string`'s first line is exactly `firmness: firm` (no leading whitespace).

- [ ] **Step 4: Commit**

```bash
git add docs/adr/identifier-scheme.md
git commit -m "$(cat <<'EOF'
feat(identifier-scheme): bind contract block to ADR

Trial B of the interaction-protocol reframe. Contract clauses (D1-strict,
D1-advisory, D2, D3, D5, D9) are enforced by tests/unit/test_identifier_scheme_contract.py.
14-line block; reversibility-guard.sh permits the frontmatter-only edit
because old_string starts at firmness:.

See docs/plans/2026-05-14-cairn-adr-contract-trial-b.md.
EOF
)"
```

---

## Task 8: Close the trial in handoff

**Files:**
- Modify: `.claude/handoff.md`

- [ ] **Step 1: Convert open entry to deferred**

Edit `.claude/handoff.md`. Replace the line:

```
- docs/plans/2026-05-14-cairn-adr-contract-trial-b.md open Trial-B-in-flight
```

with:

```
- docs/plans/2026-05-14-cairn-adr-contract-trial-b.md deferred legacy-label-retrofit
```

- [ ] **Step 2: Verify handoff contract still passes**

Run: `uv run pytest tests/unit/test_handoff_contract.py -v`
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add .claude/handoff.md
git commit -m "$(cat <<'EOF'
chore(handoff): Trial B closed; legacy-label retrofit deferred

ADR contract for identifier-scheme shipped (frontmatter block + 6 tests).
Deferred follow-up: retrofit the 10 ADRs lacking name/title and lower
LEGACY_LABEL_BASELINE in test_identifier_scheme_contract.py.
EOF
)"
```

---

## Verification checklist (run before declaring trial done)

- [ ] `uv run pytest tests/unit/test_identifier_scheme_contract.py -v` → 8 passed
- [ ] `uv run pytest tests/unit/test_handoff_contract.py -v` → 5 passed
- [ ] `uv run pytest` → full suite green (no regressions)
- [ ] `docs/adr/identifier-scheme.md` frontmatter has `contract:` block
- [ ] `.claude/handoff.md` body has the Trial B deferred entry
- [ ] Test runtime ≤5 seconds (per spec wrong-if clause)
- [ ] Total session time ≤1 session
- [ ] Operator one-line verdict captured (asked at end)

---

## Out of scope (do not do as part of Trial B)

- Retrofitting the 10 legacy-label ADRs (deferred follow-up; lower `LEGACY_LABEL_BASELINE` when done)
- Adding D4 (slice branch naming) or D6 (`name:` style) to the contract
- Generic ADR-contract runner (premature; only one ADR contract exists)
- Hypothesis dependency
- Editing `reversibility-guard.sh` (the contract block insertion fits within existing allow-rules)

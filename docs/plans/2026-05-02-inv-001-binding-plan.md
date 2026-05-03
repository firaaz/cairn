# INV-001 Binding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **For cairn pipeline:** This plan is executed via `/start-slice v1-defense-d2/inv-001-binding-implementation`. Phase 2 Skeptic and Phase 3 Builder enforce TDD by separation; the per-phase task lists below are the inputs each phase consumes.

**Goal:** Bind INV-001 to a true machine-checkable assertion via a new `git-log-walk` validator type, replacing the current `file-exists` deletion-detection proxy. Co-creates `.claude/pipeline-substrate-registry.yaml`.

**Architecture:** One new dispatcher branch in `scripts/validate_architecture.py` (`git-log-walk`) that walks `git log <effective-from>..HEAD`, classifies each commit subject against the registry, runs a per-prefix Python verifier on match, and emits SHA + subject citations on miss. Per-prefix verification rules are a Python dispatch table (Approach A from design Q2). Grandfathering uses a literal `<pending-slice-close-sha>` placeholder substituted post-close by a single `docs:` follow-up commit — no `close_slice` modification.

**Tech Stack:** Python 3.12 (cairn v1 standing deps: `pyyaml`, stdlib `subprocess` for git plumbing). Tests use `pytest` + `tmp_path` fixtures with synthetic git repos. Run via `uv run pytest`.

**ADRs:** `invariant-binding-strategy` (D1, D2, D3, D8); `pipeline-substrate-naming` (D1–D5).
**Design doc:** `docs/plans/2026-05-02-inv-001-binding-design.md` (committed at `b73fb83`).

---

## Slice brief (input to Phase 1 Reader)

**Slice id:** `v1-defense-d2/inv-001-binding-implementation`
**Branch:** continues `feature/compression-followup`
**Invariants touched:** INV-001 (binds), INV-008 (untouched in slice 1; slice 2 territory).

**Adrs-referenced (Phase 1 must declare):**
- `invariant-binding-strategy`
- `pipeline-substrate-naming`
- `bootstrap-exception` (referenced; unchanged)

**Envelope (Phase 3 write-path target):**
- `scripts/validate_architecture.py` — additions only; existing helpers untouched.
- `.claude/pipeline-substrate-registry.yaml` — new file.
- `docs/ARCHITECTURE.md` — INV-001 assertion block change only (lines ~13–19); prose line ~13 unchanged (it already names the binding strategy).
- `docs/lessons.md` — close L-001:17 marker line only.
- `tests/unit/test_inv_001_git_log_walk.py` — new test file.

**Out of envelope (must not touch):**
- `scripts/slice_orchestrator/` (close_slice unchanged — D3 grandfathering avoids it).
- INV-002 / INV-008 assertion blocks in `docs/ARCHITECTURE.md` (slice 2 territory).
- `templates/handoff.md`, `commands/claude-code/handoff.full.md` (slice 2).

---

## Phase 1 — Reader (Intent)

**Output:** `.claude/current-slice/intent.md`.

**Required content:**
- Restate INV-001's current proxy and why it doesn't satisfy v1-defense-D2 (cite `docs/ARCHITECTURE.md:13-19` and `cliff-failure-mode-and-v1-defenses` D2).
- Restate the binding contract from `invariant-binding-strategy` D1–D3 verbatim per ADR.
- Declare the registry-creation prerequisite per `pipeline-substrate-naming` D2/D3.
- Declare D3's grandfathering mechanism: literal `<pending-slice-close-sha>` placeholder + post-close `docs:` substitution; explicitly note `close_slice` is NOT modified.
- Declare `adrs-referenced: [invariant-binding-strategy, pipeline-substrate-naming, bootstrap-exception]`.

**Reader anti-behaviors to avoid (per Phase Skill Guide):**
- Do not propose new validator types beyond `git-log-walk` (structural-parser is slice 2).
- Do not modify INV-002 or INV-008 prose.

---

## Phase 2 — Skeptic (Validation, RED tests)

**Output:** `tests/unit/test_inv_001_git_log_walk.py` and `.claude/current-slice/validation/approach.md`.

**Each test below MUST RED at Phase-2 commit time** (the implementation lands in Phase 3). Tests use `tmp_path` to construct synthetic git repos.

### Test set

#### T1 — Registry file present and parses

```python
def test_registry_yaml_present_and_parseable():
    """Registry exists at canonical path with valid YAML and required schema."""
    from scripts.validate_architecture import _load_substrate_registry
    project_root = Path(__file__).resolve().parents[2]
    registry = _load_substrate_registry(project_root)
    assert isinstance(registry, dict)
    for prefix, entry in registry.items():
        assert prefix.endswith(":"), f"prefix {prefix!r} must end with ':'"
        for required in ("tool", "owner-adr", "since"):
            assert required in entry, f"{prefix} missing {required}"
```

#### T2 — Every registered prefix has a verifier

```python
def test_every_registered_prefix_has_verifier():
    from scripts.validate_architecture import (
        _load_substrate_registry,
        _SUBSTRATE_VERIFIERS,
    )
    registry = _load_substrate_registry(Path(__file__).resolve().parents[2])
    for prefix in registry:
        assert prefix in _SUBSTRATE_VERIFIERS, (
            f"prefix {prefix!r} has no Python verifier or pass-through marker"
        )
```

#### T3 — Placeholder SHA → no-op-with-notice

```python
def test_walk_with_placeholder_effective_from_is_noop(capsys):
    from scripts.validate_architecture import _run_git_log_walk_assertion
    project_root = Path(__file__).resolve().parents[2]
    result = _run_git_log_walk_assertion(
        project_root,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": "<pending-slice-close-sha>",
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is None  # no-op
    captured = capsys.readouterr()
    assert "binding pending effective-from" in captured.out.lower() \
        or "binding pending effective-from" in captured.err.lower()
```

#### T4 — Registered prefix passes; unregistered prefix is reported

```python
def test_unregistered_prefix_reported(tmp_path, monkeypatch):
    repo = _init_repo_with_registry(tmp_path)  # helper: copies real registry
    _commit(repo, "sweep: x", touch=[".claude/sweep-results/x/notes.md", ".claude/sweep.yaml"])
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "wibble: bad", touch=["foo.txt"])
    bad_sha = _git(repo, "rev-parse", "HEAD")
    from scripts.validate_architecture import _run_git_log_walk_assertion
    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base,
         "registry": ".claude/pipeline-substrate-registry.yaml"},
    )
    assert result is not None
    assert "INV-001" in result and bad_sha[:8] in result
    assert "wibble:" in result and "not in registry" in result
```

#### T5 — sweep verifier rejects missing files

```python
def test_sweep_verifier_rejects_missing_sweep_results(tmp_path):
    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "sweep: bad", touch=["foo.txt"])  # no sweep-results, no sweep.yaml
    bad_sha = _git(repo, "rev-parse", "HEAD")
    from scripts.validate_architecture import _run_git_log_walk_assertion
    result = _run_git_log_walk_assertion(
        repo, "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base,
         "registry": ".claude/pipeline-substrate-registry.yaml"},
    )
    assert result is not None and bad_sha[:8] in result
    assert "sweep verifier" in result and ".claude/sweep-results" in result
```

#### T6 — sweep verifier passes when both required paths touched

```python
def test_sweep_verifier_passes_with_both_touches(tmp_path):
    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "sweep: ok",
            touch=[".claude/sweep-results/abc/report.md", ".claude/sweep.yaml"])
    from scripts.validate_architecture import _run_git_log_walk_assertion
    result = _run_git_log_walk_assertion(
        repo, "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base,
         "registry": ".claude/pipeline-substrate-registry.yaml"},
    )
    assert result is None
```

#### T7 — squash-merge `feat:` accepted on prefix alone (F2 residual)

```python
def test_squash_merge_feat_accepted_on_prefix(tmp_path):
    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    # simulate squash-merge: feat: subject with arbitrary file changes
    _commit(repo, "feat: add unrelated thing", touch=["random/file.py"])
    from scripts.validate_architecture import _run_git_log_walk_assertion
    result = _run_git_log_walk_assertion(
        repo, "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base,
         "registry": ".claude/pipeline-substrate-registry.yaml"},
    )
    assert result is None  # pass-through verifier
```

#### T8 — End-to-end: validator exits 0 with placeholder still set

```python
def test_validator_e2e_passes_with_placeholder():
    """Real ARCHITECTURE.md INV-001 block uses placeholder; full validator must exit clean."""
    import subprocess
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/validate_architecture.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
```

### Skeptic anti-behaviors

- Do not write parser-shape tests (slice 2).
- Do not assume `_SUBSTRATE_VERIFIERS` symbol naming — Phase 3 may pick a different name; in that case Phase 3 must update T2 with a corresponding micro-edit (allowed within the binding-evidence chain).

---

## Phase 3 — Builder (Implementation, GREEN)

**Output:** code changes that turn Phase 2 RED tests GREEN, plus `.claude/current-slice/implementation/notes.md`.

### Task 3.1 — Create the registry YAML

**File:** `.claude/pipeline-substrate-registry.yaml` (new)

Verbatim from `pipeline-substrate-naming` D3, 9 entries:

```yaml
# Pipeline-substrate registry per ADR pipeline-substrate-naming D2/D3.
# Each entry authorizes a commit-subject prefix as legitimate INV-001 substrate
# when emitted by the named tool. See invariant-binding-strategy D2 for the
# walker's verification contract.
entries:
  - prefix: "slice:"
    tool: "/start-slice"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
    notes: "Slice-phase boundary and close commits."
  - prefix: "handoff:"
    tool: "/start-slice (phase boundary), /integration-sweep (sweep handoff)"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
  - prefix: "sweep:"
    tool: "/integration-sweep"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
    notes: "Integration sweep close commit; verifier requires .claude/sweep-results/ and .claude/sweep.yaml touch."
  - prefix: "bootstrap:"
    tool: "one-shot at 25ff49f per bootstrap-exception"
    owner-adr: bootstrap-exception
    since: 2026-05-02
    notes: "Single historical commit; no future entries."
  - prefix: "feat:"
    tool: "git merge --squash per merge protocol"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
    notes: "Squash-merge subject; verifier is pass-through (F2 residual)."
  - prefix: "docs:"
    tool: "/refresh-architecture, ADR landings inside slices"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
  - prefix: "fix:"
    tool: "/integration-sweep Step 6.5 post-sweep substrate fix-ups"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
    notes: "Constrained: must reference a sweep, must touch only files named in sweep-results."
  - prefix: "chore:"
    tool: "post-merge cleanup hooks"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
  - prefix: "test:"
    tool: "/start-slice Phase 2 RED commits"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
```

### Task 3.2 — Add `_load_substrate_registry`

**File:** `scripts/validate_architecture.py` (new helper, near other `_run_*` helpers)

```python
def _load_substrate_registry(project_root: Path) -> dict[str, dict]:
    """Load .claude/pipeline-substrate-registry.yaml as {prefix: entry}.

    Schema-checks: each entry has prefix, tool, owner-adr, since.
    Returns {} if file missing (caller decides hard-fail policy).
    """
    import yaml
    path = project_root / ".claude" / "pipeline-substrate-registry.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text()) or {}
    entries = raw.get("entries", [])
    out: dict[str, dict] = {}
    for entry in entries:
        prefix = entry.get("prefix", "")
        if not prefix:
            continue
        for required in ("prefix", "tool", "owner-adr", "since"):
            if required not in entry:
                raise ValueError(
                    f"INV-001 registry entry {prefix!r} missing {required}"
                )
        out[prefix] = entry
    return out
```

### Task 3.3 — Add per-prefix verifier dispatch table

**File:** `scripts/validate_architecture.py`

```python
def _verify_pass_through(sha: str, files: list[str], parents: list[str]) -> str | None:
    return None  # F2/D5 residual; accepted by name


def _verify_sweep_commit(sha: str, files: list[str], parents: list[str]) -> str | None:
    has_results = any(f.startswith(".claude/sweep-results/") for f in files)
    has_yaml = ".claude/sweep.yaml" in files
    if not (has_results and has_yaml):
        missing = []
        if not has_results:
            missing.append(".claude/sweep-results/")
        if not has_yaml:
            missing.append(".claude/sweep.yaml")
        return f"sweep verifier: missing {' AND '.join(missing)} touch"
    return None


def _verify_fix_commit(sha: str, files: list[str], parents: list[str]) -> str | None:
    # Constrained per registry note: must touch only files referenced by a sweep.
    # Heuristic: every changed file must be under .claude/sweep-results/ OR named
    # in the most recent sweep report (best-effort; full audit is v2).
    ok = all(f.startswith(".claude/sweep-results/") for f in files)
    if not ok:
        offenders = [f for f in files if not f.startswith(".claude/sweep-results/")]
        return f"fix verifier: files outside sweep scope: {offenders[:3]}"
    return None


_SUBSTRATE_VERIFIERS: dict[str, callable] = {
    "slice:": _verify_pass_through,
    "handoff:": _verify_pass_through,
    "sweep:": _verify_sweep_commit,
    "bootstrap:": _verify_pass_through,
    "feat:": _verify_pass_through,
    "docs:": _verify_pass_through,
    "fix:": _verify_fix_commit,
    "chore:": _verify_pass_through,
    "test:": _verify_pass_through,
}
```

### Task 3.4 — Add `_run_git_log_walk_assertion`

**File:** `scripts/validate_architecture.py`

```python
_PLACEHOLDER_SHA = "<pending-slice-close-sha>"


def _git_subjects_in_range(repo: Path, base_sha: str) -> list[tuple[str, str, list[str]]]:
    """Return list of (sha, subject, files_changed) for base_sha..HEAD --no-merges."""
    import subprocess
    range_arg = f"{base_sha}..HEAD"
    out = subprocess.check_output(
        ["git", "log", range_arg, "--no-merges", "--format=%H%x09%s", "--name-only"],
        cwd=repo, text=True,
    )
    commits: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for line in out.split("\n"):
        if "\t" in line and len(line.split("\t", 1)[0]) == 40:
            if current:
                commits.append(current)
            sha, subject = line.split("\t", 1)
            current = (sha, subject, [])
        elif line and current is not None:
            current[2].append(line)
    if current:
        commits.append(current)
    return commits


def _run_git_log_walk_assertion(
    project_root: Path, inv_id: str, assertion: dict
) -> str | None:
    """Walk git log range, classify each commit, run per-prefix verifier."""
    effective_from = assertion.get("binding-effective-from", "")
    if effective_from == _PLACEHOLDER_SHA or not effective_from:
        print(f"{inv_id}: binding pending effective-from set (placeholder present)")
        return None

    registry = _load_substrate_registry(project_root)
    if not registry:
        return f"Check D: {inv_id} FAIL — registry not found or empty"

    failures: list[str] = []
    for sha, subject, files in _git_subjects_in_range(project_root, effective_from):
        matched_prefix = next(
            (p for p in registry if subject.startswith(p)), None
        )
        if matched_prefix is None:
            failures.append(
                f"  {sha[:8]} {subject!r} — prefix not in registry"
            )
            continue
        verifier = _SUBSTRATE_VERIFIERS.get(matched_prefix)
        if verifier is None:
            failures.append(
                f"  {sha[:8]} {subject!r} — prefix {matched_prefix!r} has no verifier"
            )
            continue
        err = verifier(sha, files, [])
        if err:
            failures.append(f"  {sha[:8]} {subject!r} — {err}")

    if failures:
        return f"Check D: {inv_id} FAIL — INV-001 violations:\n" + "\n".join(failures)
    return None
```

### Task 3.5 — Register dispatcher branch

**File:** `scripts/validate_architecture.py:457-468`

Edit `_run_assertion`:

```python
    if atype == "git-log-walk":
        return _run_git_log_walk_assertion(project_root, inv_id, assertion)
```

### Task 3.6 — Update INV-001 assertion block

**File:** `docs/ARCHITECTURE.md:15-19`

Replace:
```
```invariant-check INV-001
type: file-exists
target: "commands/claude-code/start-slice.md"
description: "Verifies /start-slice command exists as the mechanism enabling this invariant"
```
```

With:
```
```invariant-check INV-001
type: git-log-walk
binding-effective-from: <pending-slice-close-sha>
registry: ".claude/pipeline-substrate-registry.yaml"
description: "True INV-001 binding via authorization-by-name walk over commits since binding-effective-from. Replaces prior file-exists proxy. Placeholder is substituted with the slice-close SHA by a single follow-up `docs:` commit (manual or via /refresh-architecture)."
```
```

### Task 3.7 — Close L-001:17 debt

**File:** `docs/lessons.md`

Find L-001:17 (the `context-discipline-protocol does not name sweep commits as pipeline-substrate operations` line) and append a closing marker pointing at `.claude/pipeline-substrate-registry.yaml`. Single-line edit.

### Task 3.8 — Run the suite

```bash
uv run pytest tests/unit/test_inv_001_git_log_walk.py -v
uv run pytest -q  # full suite — must remain GREEN minus known L-015 XPASS
uv run python scripts/validate_architecture.py  # exits 0 with placeholder
```

### Builder anti-behaviors

- Do not modify `scripts/slice_orchestrator/` — D3 grandfathering is via post-close `docs:`, not lifecycle code.
- Do not modify INV-002 / INV-008 assertion blocks.
- Do not change other invariants' prose.

---

## Phase 4 — Auditor (Integration, evidence)

**Output:** `.claude/current-slice/integration/sweep-notes.md` with PASS verdict.

### Required evidence

- **INV-001 binding registered:** cite `scripts/validate_architecture.py:<line of git-log-walk branch>` and `_run_git_log_walk_assertion` definition line.
- **Verifier dispatch table:** cite `scripts/validate_architecture.py:<line of _SUBSTRATE_VERIFIERS>`.
- **Registry present, all 9 entries:** cite `.claude/pipeline-substrate-registry.yaml:1`.
- **Test set GREEN:** cite `tests/unit/test_inv_001_git_log_walk.py::test_*` results from a `uv run pytest -v` run.
- **Validator end-to-end clean:** capture exit code from `uv run python scripts/validate_architecture.py`.
- **L-001:17 closed:** cite the closure line in `docs/lessons.md`.
- **No `close_slice` modification:** cite `git diff --name-only HEAD~N..HEAD` excluding `scripts/slice_orchestrator/`.

### Auditor anti-behaviors

- Do not chase parser/INV-002 evidence (slice 2 territory).
- Do not declare PASS unless all eight evidence items are present and the full suite is GREEN minus the documented L-015 XPASS-strict cases.

---

## Post-close housekeeping (operator step, NOT in slice envelope)

After `slice: complete` lands:

1. Capture the slice-close SHA: `git log -1 --format=%H`.
2. Open ARCHITECTURE.md and substitute `<pending-slice-close-sha>` with that SHA in INV-001's assertion block.
3. Commit:
   ```bash
   git add docs/ARCHITECTURE.md
   git commit -m "docs: set INV-001 binding-effective-from to slice-close SHA"
   ```
4. Run `uv run python scripts/validate_architecture.py` — should pass cleanly with the binding now active and the empty range `<close-sha>..HEAD` returning no failures.

If `/refresh-architecture` is invoked post-close, that tool MAY perform the substitution as part of its standard refresh; either path is acceptable.

---

## Risks (carried from design doc)

| ID | Scenario | Mitigation |
|---|---|---|
| L1 | Walker false-positive on legitimate but unregistered prefix from a future tool. | Registry is ADR-amendment-gated; visible in ARCHITECTURE.md refresh. |
| L2 | Operator-typed `sweep:` commit that happens to touch `.claude/sweep-results/` passes verifier. | F2 residual; accepted. |
| L3 | Walker latency on growing git log. | D8 — validator does NOT run on every `/status`; capped by `binding-effective-from`. |
| L4 | Forgetting to substitute placeholder leaves binding indefinitely advisory. | Phase-4 sweep-notes explicit handoff item; post-close housekeeping step (above). |

---

## Out of scope (slice 2)

INV-002 structural-parser, handoff schema (`templates/handoff.md`), /catchup Tier-1 list test (D5), INV-002(c)/INV-008 grep→test-ref upgrade (D6), D7 token-counting precision.

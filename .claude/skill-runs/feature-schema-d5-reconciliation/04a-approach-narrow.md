# Approach A — NARROW pure: advocacy

## Pre-mortem response

**Scenario 1 (test extension breaks NARROW silently):** NARROW resolves this proactively. After migration, `orchestrator-paths.yaml` has `intent:` and `shaped-from:`. When `test_feature_file_schema.py` extends to live files it passes immediately. NARROW turns a future surprise into a non-event. WIDEN cannot achieve this — the slice-entry `status: phase-1` bug (02-journey.md:31-35) persists regardless.

**Scenario 2 (slice-entry `status: phase-1` — both options):** Shared bug. NARROW migration fixes it as part of the same YAML edit. WIDEN would need to extend the permitted slice-status enum, contradicting `test_feature_file_schema.py:73-76`. NARROW fix is simpler.

**Scenario 3 (ad-hoc field proliferation under WIDEN):** NARROW is the direct prevention. D5's "explicit rejection" pattern (`docs/adr/identifier-scheme.md:91`) is the mechanism; NARROW preserves it. WIDEN inverts the norm — fields are permitted until explicitly rejected.

**Scenario 4 (NARROW loses `audit-findings` provenance):** Residual risk; addressed in §2 below.

**Scenario 5 (firmness claim undermined):** NARROW reaffirms D5 unchanged — zero process risk. WIDEN requires either an in-place edit (breaks firmness) or a supersession ADR (substantial overhead for a one-file drift).

**Scenario 6 (`charter:` alias ambiguity):** NARROW eliminates it. The alias never enters D5.

---

## 1. Migration: before / after

**Before** (`.claude/features/orchestrator-paths.yaml`, full file):
```yaml
id: orchestrator-paths
name: orchestrator-paths
status: in-progress
tracking: firaaz/cairn#24
predecessor: substrate/root-resolver
lesson: L-017
audit-findings:
  - F-039
  - F-040
  - F-041
  - F-042
  - F-048
  - F-049
  - F-050
slices:
  - id: substrate/orchestrator-paths
    status: phase-1
charter: |
  Close the orchestrator half of the root-resolver migration ...
out-of-scope:
  - mcp_servers/cairn_knowledge/server.py (issue #25)
  ...
```

**After**:
```yaml
id: orchestrator-paths
name: orchestrator-paths
created: "2026-05-14"        # feature-slice-model D0 required field (03-premortem.md:59)
intent: |
  Close the orchestrator half of the root-resolver migration deferred when
  substrate/root-resolver failed mid-phase-3. Migrate
  scripts/slice_orchestrator/{core,lifecycle,dispatch,telemetry}.py and the
  three scope-overflow callers (scripts/integration_gate.py,
  scripts/validate_architecture.py, scripts/dogfood_evaluate.py) off
  Path(".claude/...") literals, Path.cwd() fallbacks, and bare git
  subprocess calls onto scripts/_root.project_root(). Unmark the four
  strict-xfail entries in tests/unit/test_root_resolver_migration.py
  covering this cluster plus the single strict-xfail in
  tests/unit/test_path_discipline_lint.py. Path-plumbing only — no
  behavioral changes.
shaped-from: null            # no design doc; predecessor slice is substrate/root-resolver
slices:
  - id: substrate/orchestrator-paths
    added: "2026-05-14"      # drop status: phase-1 (violates test_feature_file_schema.py:73-76)
```

---

## 2. Where do the 6 extra fields go?

| Field | Disposition | Canonical home |
|---|---|---|
| `status: in-progress` | Drop. No automated reader (01-constraints.md:24-25). Git branch state implies status. | — |
| `tracking: firaaz/cairn#24` | Move to `docs/adr/identifier-scheme.md` D5 commentary OR drop. GitHub issue is discoverable via `gh issue list`. No tool reads this field. | Drop; no home needed |
| `predecessor: substrate/root-resolver` | Use as `shaped-from:` seed — set `shaped-from: null` and record the predecessor relationship in the commit message. The slice `id: substrate/orchestrator-paths` already encodes the lineage. | Commit body |
| `lesson: L-017` | Cross-reference belongs in `docs/lessons.md` entry for L-017 (reverse link). Not a feature-file concern. | `docs/lessons.md:L-017` entry |
| `audit-findings: [F-039…F-050]` | Record in a single-line comment in `docs/lessons.md` at the affected findings, OR in `docs/roadmap.md` under orchestrator-paths. The findings motivated the feature; the motivation is already captured in `intent:`. Losing the cross-ref is the only residual risk (see §5). | `docs/lessons.md` findings block or inline comment |
| `out-of-scope: [...]` | Move to `docs/plans/<date>-orchestrator-paths.md` scoping section if a plan doc exists; otherwise capture in `intent:` as "Path-plumbing only — no behavioral changes." The `intent:` block already contains the boundary statement. | Fold into `intent:` prose (already present in charter text) |

---

## 3. Cost / effort

- **Lines edited in orchestrator-paths.yaml:** ~37 → ~16. Net: remove 21 lines, add 3 (`created:`, `shaped-from: null`, rename `charter:` → `intent:`).
- **Cascading changes:** none. 01-constraints.md:24-25 confirms no hook, script, or skill reads `.claude/features/*.yaml` fields at runtime.
- **Ancillary:** add cross-ref comment to `docs/lessons.md` for F-039–F-050 (one line). No ADR edits required; D5 is reaffirmed, not changed.

---

## 4. NARROW vs. WIDEN given Phase 0/0.5/1 findings

- **01-constraints.md:24-25:** No code reads feature-file fields. Migration cost is a YAML edit, not a code change. WIDEN's benefit (preserve as-is) is worth zero tooling overhead but costs a firm-ADR amendment.
- **02-journey.md:53-62 (boundary table):** Only Stage 1 (creation template) and Stage 4 (test extension) are affected. NARROW fixes both; WIDEN fixes neither and adds a schema rule for slice-entry `status` that contradicts the existing validator.
- **03-premortem.md:72:** Pre-mortem's own risk asymmetry conclusion: "NARROW — its worst case is medium-cost data loss with a clear fix; WIDEN's worst case is large-cost methodology credibility damage with no clean retroactive fix."
- **01-constraints.md:40-41:** The schema deviation has a single commit with no documented rationale (`df8ba20`). This is context pressure during Phase 2, not a deliberate design. NARROW treats it correctly: fix the drift, not the standard.

---

## 5. Where NARROW falls short / residual risk

- **`audit-findings` traceability:** F-039–F-050 → orchestrator-paths is a live cross-reference with no validated canonical relocation. If `docs/lessons.md` entries for those findings don't back-reference the feature, the join is lost. Mitigation: explicitly add cross-ref lines to `docs/lessons.md` before deleting from the feature file.
- **`created:` date:** orchestrator-paths.yaml has no `created:` field (03-premortem.md:59). The correct value requires checking git log for the file's initial commit. Wrong date is worse than `null`; use git to retrieve it.
- **`shaped-from: null`:** D5 prescribes a design artifact path (`docs/adr/identifier-scheme.md:89`). `null` is technically permitted but signals missing provenance. Acceptable for a migration-era feature that predates the D5 norm; document in commit body.

---

## 6. Implementation steps

1. Run `git log --diff-filter=A -- .claude/features/orchestrator-paths.yaml` to retrieve the initial commit date for `created:`.
2. Add cross-ref lines to `docs/lessons.md` at F-039–F-050 entries: `feature: orchestrator-paths`.
3. Edit `.claude/features/orchestrator-paths.yaml`: rename `charter:` → `intent:`, add `created: <date>`, add `shaped-from: null`, delete slice-entry `status: phase-1`, delete the 6 extra fields.
4. Commit with body citing: D5 reaffirmation, `df8ba20` context-pressure origin, findings relocation.
5. No ADR edit required; D5 is unchanged.

# Cairn Shrink M3 — Bathwater Audit

```
firmness: provisional
status: audit — informs M4 deletion plan
date: 2026-05-06
scope: classify every cairn fix/feature for M4 disposition (carry-forward, dies-with-orchestrator, dies-with-substrate, dies-with-slice-machinery, re-evaluate)
```

## 1. Method

Walked design §5 don't-regress checklist row-by-row (`docs/plans/2026-05-06-cairn-shrink-design.md:259-277`), then swept `.claude/features/*.yaml` (10 features) and `.claude/completed-slices/*-failed/` (6 archives) for any fix not already enumerated in §5. For each item, recorded: origin commit/slice, current location in tree, classification, and the M3-vs-M4-vs-M5 disposition. Conservative-survival rule when a row is structurally ambiguous: pick the most-likely-to-survive bucket and note the boundary in §6.

Inventory inputs: 10 features (`compression`, `cost-discipline`, `efficiency-program-afternoon-wins`, `housekeeping`, `identifier-scheme`, `integration-gate`, `orchestrator-paths`, `substrate`, `v1-defense-d2`, `v1-defense-d3`); 6 failed-slice archives (`compression-learnings-capture-failed`, `SLICE-003-precursor`, `SLICE-013-failed`, `substrate-phase-2-skeptic-stage-surface-failed{,-2}`, `substrate-root-resolver-failed`).

## 2. Carry-forward (must survive M4 deletion)

Each row of design §5 marked **Carries forward**, plus compression-era fixes not enumerated in §5 that the M4 deletion plan must preserve.

**`role_guard` `READ_CLASS_TOOLS = {Read, Grep, Glob}` — Slice 2 fixup (compression/lever-Y-mcp-substrate-fixup).** Without it, a phase agent can bypass the canonical-knowledge lockdown by issuing `Grep` or `Glob` against `docs/ARCHITECTURE.md`/`docs/adr/**` instead of `Read`. Lives at `checks/role_guard.py:23` (the constant) and `checks/role_guard.py:148-150` (the gate). M4 must preserve `READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}` at `checks/role_guard.py:23` even after the simplification pass — verified by `tests/unit/test_role_guard_grep_glob_deny.py` (G1-G7 cases).

**`role_guard` envelope-grant escape (D9) — Slice 2 (compression/lever-Y-mcp-substrate).** Agents that legitimately need a denied path declare it in `AGENT_ENVELOPE` at dispatch time and the guard widens. Lives at `checks/role_guard.py:84-110` (`_envelope_patterns` + grant logging) and the gate hook at `:165, :202`. M4 must preserve envelope-grant lookup across read-class and write-class enforcement; the dispatch skill's prompt-construction step replaces the orchestrator as the envelope source.

**Triager superseded-test heuristic (`detect_superseded_test_signal`) — compression/triager-superseded-test-heuristic.** Pure function; recognizes a RAISE_ISSUE referring to tests superseded by a firm contract the current slice landed and biases the triager toward ESCALATE_TO_USER instead of RE_DISPATCH-to-Phase-2. Lives at `scripts/slice_orchestrator/core.py:406` (definition), re-exported from `scripts/slice_orchestrator/__init__.py:68,252`, called from `scripts/slice_orchestrator/dispatch.py:391`, and prose tweak in `.claude/agents/issue-triager.md`. M4 must preserve the function (move it into the dispatch skill, the new `triager-tdd` agent prose, or a small shared helper module — recipient TBD by M4 plan).

**YAML safety in `coupling-clusters.yaml` (single-quoted regex) — phase-2-skeptic agent doc.** Double-quoted YAML scalars interpret backslash escapes; the rule is that every regex in `files:` must be single-quoted. Lives at `.claude/agents/phase-2-skeptic.md:21` (and the M2 sibling `.claude/agents/phase-2-tdd.md` where the same guidance must live). M4 must preserve the single-quote-regex guidance verbatim in whichever phase-2 agent prose survives.

**`ADR_EDITORIAL_FIX=1` typo escape — reversibility-guard.sh.** Operator escape hatch for additive editorial corrections to firm/superseded ADRs without authoring a successor ADR. Lives at `checks/reversibility-guard.sh:88-98`. M4 must preserve the env-var, the additive-only narrowing, and the audit-log line at `.claude/adr-editorial-fixes.log` — `reversibility-guard.sh` itself is in design §3.1 "stays".

**Compression-era carry-forwards beyond design §5:**

- *FastMCP / pydantic / kuzu / mistune / typer dependency choice authorized by ADR cairn-substrate-and-fastmcp* — substrate dies (§4) so most of those deps go with it, but the **D1 standing dep set** (pydantic, pyyaml, typer specifically) survives because the dispatch skill, validators, and CLAUDE.md "new code is Python, function-based" rule still allow them. M4 must preserve the standing dep set declaration in CLAUDE.md and prune kuzu/fastmcp from `pyproject.toml` only after the substrate is gone.
- *Phase-3 cluster-RED-test discipline rule (compression/learnings-capture retry).* The discipline that "every Phase-3 cluster carries a RED test, including the prompt-amendment cluster" lives only as prose in the failed-slice archive narrative and the retry slice intent. M4 should re-encode this as a one-line norm in `cairn-tdd-feature/SKILL.md` Phase-3 section.
- *Substrate Slice-3 frontmatter tightening pattern (compression/lever-Z-substrate-full-pipeline).* Phase-2/3/4 agent frontmatter dropped direct read access to canonical sources as defense-in-depth. With the substrate gone, agents read canonical sources directly — the *concept* of frontmatter `tools:` allowlists carries forward (design §3.1, §4 step 2) but the substrate-specific deny set does not.

## 3. Dies-with-orchestrator (acceptable loss when M4 lands)

Each row of design §5 marked **Dies with orchestrator** or **Dies with `commit_phase_handoff`/`close_slice`** — the original failure mode is orchestrator-bound and does not exist in the dispatch-skill path.

- **B9 post-Timeout HEAD reconciliation** (compression/slice-2-state-machine) — orchestrator's `subprocess.TimeoutExpired` handler must reconcile against pre-dispatch HEAD. The dispatch skill invokes `Agent` natively; subagent returns or doesn't. No timeout reconciliation surface.
- **B13 `_active_child` for signal handlers** (compression/slice-2) — SIGINT/SIGTERM handlers needed a registry of live child PIDs. No Python subprocess to signal in the dispatch path.
- **B15 max-1 redispatch-per-phase cap** (compression/slice-2) — the orchestrator could loop on triager RE_DISPATCH; the cap prevented runaway. Manual re-run by operator is the dispatch-path equivalent; no automated redispatch.
- **Slice-artifact-preservation copy-before-wipe** (compression/slice-artifact-preservation) — `_copy_artifacts_to_sweep_results` snapshotted `.claude/current-slice/` before `close_slice` wiped it. No wipe to preserve from in the dispatch path.
- **Phase-1-handoff-stage-surface, Phase-4-sweepnotes-required staging** (compression/phase-1-handoff-stage-surface, compression/phase-4-sweepnotes-required) — `commit_phase_handoff` and `close_slice` had to extend their `_git add` surface to cover writer-declared write paths. Dispatch skill commits per-phase writes natively, staging by name as it goes.
- **`_copy_artifacts_to_sweep_results`** (compression/slice-artifact-preservation) — same root cause as above; git history of merged branches preserves the equivalent forensic surface.
- **23-slice-overdue sweep** (sweep ritual) — pre-commit / CI runs the validator on every commit; no periodic sweep ceremony.
- **Phase-2-staging-untracked-enumeration (issue #26 substrate slices)** — the original `git diff --name-only` exclude-untracked failure mode at `lifecycle.py:232-243` is a `commit_phase_handoff` artifact. Dispatch-skill commits the phase's writes by explicit name, no diff-based discovery. Tracked separately in §6 because we want M4 to *verify* the failure mode doesn't reappear.

## 4. Dies-with-substrate

Items whose survival depends on the typed-knowledge graph + MCP wrapper subsystem (gone in design §3.2).

- **Typed-knowledge graph (`scripts/cairn_query/`, ~1900 LOC).** Extractor + kuzudb-backed storage + cairn_query CLI. M4 deletes the package; M4 plan must enumerate consumer call sites (currently: tests in `tests/unit/test_cairn_query_*.py` and the substrate-bound MCP server).
- **MCP wrapper (`mcp_servers/cairn_knowledge/`).** JSON-RPC 2.0 dispatcher over stdio (compression/lever-Y-mcp-substrate-fixup). Dies with the substrate; M4 deletes `mcp_servers/`, drops the `.mcp.json` registration, and prunes `fastmcp` + `kuzu` from `pyproject.toml`.
- **INV-010 lockdown of canonical knowledge paths.** The `_CANONICAL_DENY_PATTERNS` / `ROLE_DENY_READ` table in `checks/role_guard.py` exists to force phase agents through the substrate. Without the substrate, the read-class lockdown becomes meaningless — phase agents must read canonical sources directly. M4 deletes the `ROLE_DENY_READ` table entries pointing at canonical sources; the role-allowlist mechanism (per-role write-path patterns) survives. ADR `cairn-substrate-and-fastmcp` is superseded — M4 plan §7.1 lists this in the supersession sweep.

## 5. Dies-with-slice-machinery

Items tied to the slice unit-of-work concept (`current-slice/`, `slice.yaml`, `close_slice`, `commit_phase_handoff`, sweep ritual).

- **Failed-slice archive (`completed-slices/<id>-failed/`).** `start-slice.full` Step 8. Git history of failed branches serves the same forensic purpose; M4 deletes `.claude/completed-slices/` machinery (the ADR allowing it remains for historical reference).
- **`start-slice` ceremony, `integration-sweep` ceremony, `close_slice` bundling.** Replaced by the dispatch skill's per-phase commits + standard PR review.
- **`commit_phase_handoff`.** Phase-boundary commit producer. Dispatch skill commits each phase's writes with conventional-commit subjects directly.
- **`slice.yaml` lifecycle.** Status field, schema_version, lifecycle transitions. No slice unit-of-work.
- **`current-slice/` directory.** No phase-ephemeral scratchpad; phases write to their final destinations (intent.md → `docs/plans/<feature>.md`; tests → `tests/unit/`; impl → its target file).
- **Sweep ritual (`sweep.yaml`, `.claude/sweep-results/`, 23-slice-overdue).** Validator runs on commit; no periodic sweep.
- **Heartbeat daemon, 13-state resume matrix, ThreadPoolExecutor for Phase-3 clusters, `_MirroringModule` test scaffolding** — all design §3.2 entries; orchestrator-internal machinery with no analog in the dispatch path.

## 6. Re-evaluate in M4 / M5

- **Phase-2-skeptic write-timing fix (issue #26 ae9e6c8).** §3 listed this as orchestrator-bound; explicit M4 verification is required. M4 plan must demonstrate that the dispatch-skill commit-per-phase pattern doesn't reproduce the original `git diff` exclude-untracked failure mode — typically by committing each phase's writes by explicit named path (no diff-based discovery), or by enumerating untracked via `git ls-files --others --exclude-standard` if discovery is needed.
- **`V1_ASSERTION_TYPES` allowlist hardcoded in tests** (`tests/unit/test_invariant_assertions.py:1116`). Validator stays in design §3.1; therefore the allowlist stays. Constraint: any new validator-type addition (M3 Task 6 INV-002 binding may surface one) must include the type in `V1_ASSERTION_TYPES` or the test at `:1153-1154` raises. Carry forward.
- **INV-009 cost-threshold trip in orchestrator.** Dropped (advisory only) per design §5. ADR amendment in M4 — likely supersession via a shrunken successor ADR or a pure-amendment marking it abandoned.
- **Triager-misroute on superseded tests (memory `triager_misroute_on_superseded_tests.md`).** The `detect_superseded_test_signal` heuristic carries forward (§2). M4 plan must verify the new `triager-tdd` agent's prompt iteration calls the heuristic the same way the legacy `issue-triager` did. If the dispatch-skill triager call signature differs, queue a follow-up to re-wire the hint.
- **L-014 cross-slice-contradiction lesson (compression/lever-Z-fixup §c).** Phase-2 skeptic should pre-grep the existing test corpus for assertions inverted by an enforcement-set widening before Phase 3 dispatches. Lives in `docs/lessons.md` (per the slice intent). Re-evaluate whether to encode this as a `cairn-tdd-feature/SKILL.md` Phase-2 line or leave it as a lesson.
- **Boundary case — `_bash_path_tokens` (`role_guard.py`).** Bash-heredoc escape used to bypass CC's built-in `.claude/**` sensitive-file gate (memory `path_c_fleet_writes_empirical.md`); the token extractor in `role_guard.py` covers `cat`/`head`/`grep` against canonical-knowledge paths. Substrate dies, but the **mechanism** still has tactical use — keep the extractor; drop the canonical-knowledge entries from the deny table per §4. Conservative-survival call: the token-extractor itself carries forward; only the deny entries die.

## 7. Open follow-ups (deferred, not blocking M4)

- **Consumer migration prep (M6 deferred).** `docs/upgrading-from-pre-compression.md` will be wholly replaced for M5 plugin packaging; the two consumer-breaking bugs fixed by `compression/upgrade-doc-bug-fixes` are obsoleted by the rewrite. No action in M4.
- **Plugin packaging concerns (M5).** Manifest, version pinning, Claude Code plugin discovery. Out of M4 scope.
- **INV-002(b) Tier-2 LLM-judgment runtime binding (v2).** Out of M4 scope; v1 stays property-based grep against literal source.
- **Substrate failed slices in `.claude/completed-slices/`** (`substrate-phase-2-skeptic-stage-surface-failed{,-2}`, `substrate-root-resolver-failed`, `compression-learnings-capture-failed`, `SLICE-003-precursor`, `SLICE-013-failed`). Forensic value tied to git history; M4 may delete the `completed-slices/` directory wholesale or preserve the archives as static reference under `docs/`.
- **Empty-feature placeholders.** `orchestrator-paths.yaml` carries one phase-1 charter slice never closed; merge into `housekeeping.yaml` or drop on M4 close.

## 8. M4 input — explicit don't-regress commitments

- M4 plan MUST preserve `READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}` at `checks/role_guard.py:23` — verified by `tests/unit/test_role_guard_grep_glob_deny.py` (G1-G7).
- M4 plan MUST preserve envelope-grant lookup at `checks/role_guard.py:84-110, :165, :202` — verified by `grep -n '_envelope_patterns\|AGENT_ENVELOPE' checks/role_guard.py` returning hits and the existing role-guard tests under `tests/unit/test_role_guard_*.py`.
- M4 plan MUST preserve `detect_superseded_test_signal` (function body intact, callable from the dispatch skill or `triager-tdd` agent path) — verified by `grep -rn 'detect_superseded_test_signal' .claude/ scripts/` returning at least one definition site and one call site.
- M4 plan MUST preserve the single-quote-regex YAML-safety guidance in whichever phase-2 agent prose survives (currently `.claude/agents/phase-2-skeptic.md:21` and `.claude/agents/phase-2-tdd.md`) — verified by `grep -n "single-quoted" .claude/agents/phase-2-*.md` returning at least one hit.
- M4 plan MUST preserve `ADR_EDITORIAL_FIX=1` env-var handling at `checks/reversibility-guard.sh:88-98` — verified by `grep -n 'ADR_EDITORIAL_FIX' checks/reversibility-guard.sh` returning the conditional and the audit-log write.
- M4 plan MUST preserve the validator parser fix (M3 Task 3, `parse_assertion_blocks` for nested YAML at `scripts/validate_architecture.py:151`) — verified by the new RED tests written under M3 Task 3 going GREEN.
- M4 plan MUST preserve the `V1_ASSERTION_TYPES` allowlist at `tests/unit/test_invariant_assertions.py:1116` — verified by the existing test at `:1153-1154` continuing to pass.
- M4 plan MUST preserve the per-phase agent frontmatter `tools:` allowlist mechanism at `.claude/agents/phase-{1,2,3,4}-{writer,skeptic,implementer,integrator,tdd}.md` — verified by `grep -n '^tools:' .claude/agents/phase-*.md` returning a tools line on every surviving phase-agent file.

---
id: cairn-m5-f1-packaging
name: Cairn M5 F1 — Plugin packaging
snapshot-sha: 5dc03cf421198aa43394fb241cf6a17df1320f47
invariants-touched:
  - INV-011
d-commitments-owned:
  - D1
  - D2
  - D3
  - D4
  - D5
---

# Intent — Cairn M5 F1 (Plugin packaging)

## What

F1 makes cairn installable as a Claude Code plugin via its own marketplace.
It introduces five artifact surfaces that did not previously exist in the
repo: a marketplace manifest, a plugin manifest (built from a canonical
template), a curated `dist/` payload produced by an explicit allow-list build
script, a plugin-internal `hooks.json` (built from a canonical template) that
registers the three existing hooks under `${CLAUDE_PLUGIN_ROOT}`, and a
post-install validator that exercises envelope enforcement end-to-end. F1
also lands one source-code fix in `checks/role_guard.py` so that
`CAIRN_ROOT` is anchored on `CLAUDE_PROJECT_DIR` (not `__file__`), and one
GitHub Actions job that gates `dist/` payload contents against the allow-list
on every PR.

## Why

Two load-bearing motivations shape every acceptance criterion:

- **D5 — enforcement, not theatre.** Under plugin-cache invocation,
  `__file__` resolves into the plugin cache, so the current
  `Path(__file__).resolve().parent.parent` makes `role_guard.py` look for
  the operator envelope inside the cache (which never has one) and silently
  fail-open. A green dep-check is not a fix. F1's validator must run a
  positive end-to-end test (write a sample envelope, attempt an
  out-of-envelope write, observe a real deny) and must fail loud if that
  deny does not land.

- **D3 — allow-list, not deny-list.** Plugin manifests have no
  `include`/`exclude` glob fields; payload curation is by physical
  separation. An allow-list is the only structurally honest gate against
  leaks of `tests/`, `docs/adr/`, `.venv/`, `.local/`, ADR drafts, or the
  retired slice orchestrator. CI must run the build and assert what is
  present, not enumerate what should be absent.

## Boundary

In scope: manifests (D1, D2), `dist/` build script + CI gate (D3), plugin
hooks.json (D4), `role_guard.py` runtime anchoring + positive validator
(D5). Out of scope: F2 consumer-doc surface (CONSUMER.md, README reading
order, template expansion D7, `[both]` tags D6, phase-skill-mapping
promotion, `docs/adoptable-disciplines.md`); F3 migration (consumer
`.slice-system → .` retire, `complex-rag-analysis` cutover, in-flight
skill-run quiescence checklist, deletion of `.slice-system`-anchored hook
entries in consumer settings.json); M5.1 slash-command payload
(`dist/commands/` is intentionally absent). F1 does not commit a `dist/`
tree — `dist/` is build output, gitignored, regenerated per release tag.
Cairn-the-repo's `.claude/settings.json` is unchanged (Path B self-symlink
per D8).

## Specification

### Acceptance criteria

Each criterion is testable and observable. Phase 2 owns the test design;
this list states the contract those tests must enforce.

**A1 — Marketplace manifest (D1).**
A `.claude-plugin/marketplace.json` file exists at the repo root, parses
as JSON, declares cairn as a marketplace with exactly one plugin entry
named `cairn`, whose `source.type` is `"git"` and `source.path` is
`"dist/"`. The manifest accepts (does not reject) `source.ref` or
`source.sha` as optional pin fields.

**A2 — Plugin manifest with explicit version (D1, D2).**
A canonical source for the plugin manifest exists in the repo and is
copied into `dist/.claude-plugin/plugin.json` by the build. The built
artifact is valid JSON, declares `name == "cairn"` and a `version` field
that is the literal string `"0.1.0"` (D2 requires explicit, not derived).
`description` is non-empty. The `name` agrees with the marketplace
entry's `name`.

**A3 — Build script populates only allow-listed paths (D3).**
A build script exists, is invocable through the project venv, and when
run against a clean output dir produces a tree containing exactly the
following surfaces: the plugin manifest under `dist/.claude-plugin/`; the
TDD dispatch skill under `dist/skills/cairn-tdd-feature/`; the five phase
agents and the role-topology under `dist/agents/`; the three hook
scripts (`reversibility-guard.sh`, `reality-check.sh`, `role_guard.py`)
under `dist/checks/`; the F1 templates under `dist/templates/`; the
hooks manifest under `dist/hooks/hooks.json`; and the post-install
validator at `dist/postinstall_validate.py`.

**A4 — Build script never leaks excluded surfaces (D3).**
The post-build tree contains no path under any of: `dist/tests/`,
`dist/docs/`, `dist/.venv/`, `dist/uv.lock`, `dist/pyproject.toml`,
`dist/commands/`, `dist/scripts/slice_orchestrator/`,
`dist/.claude/skill-runs/`, `dist/docs/adr/`, `dist/docs/plans/`,
`dist/docs/reviews/`. (Asserted as the inverse of the allow-list, not as
an enumerated deny-list — the allow-list IS the contract.)

**A5 — Build is idempotent and symlink-safe (D3, CLAUDE.md hazard).**
Two consecutive build runs against the same output dir produce
byte-identical trees (output dir is cleaned before population). The build
never traverses `.slice-system → .`, even if invoked from a working tree
where that symlink exists.

**A6 — Hooks manifest uses `${CLAUDE_PLUGIN_ROOT}` substitution (D4).**
A canonical hooks template exists in the repo and is copied into
`dist/hooks/hooks.json` by the build. The built JSON registers
`PreToolUse` entries that route `Bash|Edit|Write` to
`reversibility-guard.sh`, route `Write|Edit|MultiEdit|NotebookEdit` to
`role_guard.py`, and a `PostToolUse` entry that routes `Edit|Write` to
`reality-check.sh`. Every hook command path is prefixed by
`${CLAUDE_PLUGIN_ROOT}/`. No hook command contains the legacy literal
`$CLAUDE_PROJECT_DIR/.slice-system/`.

**A7 — `role_guard.py` anchors on `CLAUDE_PROJECT_DIR` (D5).**
With `CLAUDE_PROJECT_DIR` set to a directory `D`, the module-level
`CAIRN_ROOT` resolves to `D` and `OPERATOR_ENVELOPE_PATH` resolves to
`D/.claude/active-envelope.yaml`. With `CLAUDE_PROJECT_DIR` unset,
`CAIRN_ROOT` falls back to `os.getcwd()`. The `_log_grant()` writer
inherits this anchoring (writes land at
`<CAIRN_ROOT>/.claude/envelope-grants.log`). No reference to
`Path(__file__).resolve().parent.parent` remains in `role_guard.py`.

**A8 — Existing role_guard policy behaviour is unchanged (D5 regression
guard).** The matchers, allowlists, deny semantics, and exit-code
contract that `role_guard.py` enforces today behave identically after
the anchoring fix. F1 changes only the path source.

**A9 — Post-install validator: dep checks are warnings (D5).**
The validator detects missing `jq` and missing `ruff` independently and
emits a stderr warning naming the missing dep and the hook(s) that will
no-op. Missing deps are non-fatal — the validator does not exit non-zero
on dep absence alone.

**A10 — Post-install validator: positive enforcement is fatal (D5,
canary).** The validator constructs a temporary `CLAUDE_PROJECT_DIR`,
writes a `mode: operator` envelope whose `paths:` does NOT cover some
file `F`, invokes `role_guard.py` against tool-input JSON targeting `F`,
and asserts that the invoked process exits non-zero with non-empty
stderr. If the invoked process exits zero (i.e. enforcement silently
passed an out-of-envelope write — the pre-D5 failure mode), the
validator MUST exit non-zero with a stderr message stating that envelope
enforcement did not deny an out-of-envelope write and the installation
is not safe.

**A11 — CI gates the dist payload (D3, Risk #5).**
A GitHub Actions workflow runs on PRs and on pushes to `dev`/`main`,
syncs the project venv, builds `dist/` to a tmp dir, runs the
allow-list assertions against the freshly built tree, and runs the
post-install validator's self-test against that tree. The workflow
fails if any of those steps fail. `dist/` is gitignored.

**A12 — Cairn-the-repo settings.json is untouched (D8).**
F1 does not modify `.claude/settings.json`. The Path B self-symlink
hook configuration remains operative for cairn-the-repo's own
dogfooding.

## Verification

The acceptance criteria above are observable through the following
classes of evidence (Phase 2 selects the specific test mechanics):

- **Static-shape evidence** — JSON parsing and field assertions on the
  marketplace manifest, the canonical plugin manifest, the canonical
  hooks template, and the built `dist/.claude-plugin/plugin.json` and
  `dist/hooks/hooks.json` (A1, A2, A6).
- **Build-output evidence** — invoke the build script against a tmp
  output dir; enumerate the resulting tree; assert presence of
  allow-listed paths and absence of any path outside the allow-list;
  assert byte-identity across two consecutive runs (A3, A4, A5).
- **Module-state evidence** — set/unset `CLAUDE_PROJECT_DIR`, reload
  `checks/role_guard.py` (module-level constant capture), assert
  `CAIRN_ROOT` and `OPERATOR_ENVELOPE_PATH` resolution; exercise
  `_log_grant()` and observe the file landing path (A7); re-run the
  pre-existing role_guard suite and observe no regressions (A8).
- **Subprocess-behaviour evidence** — drive the validator with
  controlled `PATH` (missing deps), with a tmp `CLAUDE_PROJECT_DIR` and
  a real envelope file (positive enforcement), and with a stubbed
  `role_guard.py` that returns 0 (silent-pass canary). Observe exit
  codes and stderr contents (A9, A10).
- **CI-job evidence** — workflow runs all build + assertion + validator
  steps; the workflow's pass/fail is the contract (A11).
- **Repo-state evidence** — `.claude/settings.json` diff is empty
  across F1 (A12).

## Open questions and risks

- **Canonical-template envelope gap.** The plan body references two
  canonical-source files that the dispatch brief's envelope does not
  list: `.claude-plugin/plugin-template.json` (Sections F1.1 and F1.3)
  and `.claude-plugin/hooks-template.json` (Section F1.4). The
  envelope's `^\.claude-plugin/marketplace\.json$` row covers only the
  marketplace manifest. Phase 3 will be unable to write the canonical
  templates under the current envelope without an amendment. Two
  resolutions are possible: (a) the envelope was meant to include a
  broader `^\.claude-plugin/.*\.json$` family and got narrowed in
  error — operator extends the envelope before Phase 3; or (b) Phase 3
  is expected to author the manifests directly at their `dist/`
  destinations and the build script's allow-list rows for the
  templates are stale — plan body needs reconciliation. **Surfaced
  for operator review; do not amend the plan doc from this phase.**

- **Auto-postinstall hook field.** Whether the plugin spec exposes a
  `postinstall:` entrypoint that auto-runs the validator on install is
  not yet confirmed against the live plugin reference. F1 owns the
  validator's existence; F2 owns documenting manual invocation if no
  auto-hook field exists. Phase 3 should resolve at implementation
  time and pin the result for F2.

- **`pyyaml` consumer-env coverage.** `role_guard.py` lazy-imports
  `yaml` when an envelope file is present. Consumers without `pyyaml`
  on the python path will see envelope enforcement fail closed under
  `mode: operator`. F1 does not warn on missing `pyyaml`; the plan
  defers this to a future M5.1 audit triggered by first consumer
  report. Acceptable per plan; flagged for awareness.

- **Marketplace `source.url` confirm.** The marketplace manifest
  templates a `source.url` of the public cairn git URL. The exact
  string lands at PR-open time per plan F1.1 Step 2. Phase 3 should
  not block on URL precision; the value is owner-confirmable at
  review.

- **Plugin-cache simulation in CI.** The CI job runs the validator
  against the freshly built `dist/` tree, but the `CLAUDE_PROJECT_DIR`
  environment used by the test is the CI workspace, not a true plugin
  cache. The positive enforcement test will exercise the D5 fix
  correctly under that environment, but a deeper "simulate plugin
  cache invocation" test (where `__file__` is in a path different from
  `CLAUDE_PROJECT_DIR`) is the higher-fidelity defense. Phase 2 may
  choose to harden A10 with such a simulation; Phase 3 implements as
  specified by the chosen tests.

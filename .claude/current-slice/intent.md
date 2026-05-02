# Intent — v1-defense-d2/inv-003-phase-topology-binding

## What

Replace INV-003's grep-for-section-header proxy (ARCHITECTURE.md:33–39) with
a four-way cross-reference assertion that fails when the canonical
(phase, role) topology drifts in any of the four declaration sites. Resolve
one named asymmetry: `phase-3-implementer` lacks a static `ROLE_POLICIES`
entry; the slice picks between requiring static coverage for all four roles
or accepting envelope-grant-only per compression-infrastructure-bootstrap.

## Why

INV-003 is firm under phase-lock-and-role-declaration; D2
(cliff-failure-mode-and-v1-defenses) requires every firm invariant to carry
a machine-checkable assertion. The current grep catches deletion of one
heading and is silent against phase reordering, role rename, prompt-file
drift, and `ROLE_POLICIES` key drift. invariant-binding-strategy scopes
INV-003 out of its generic catalogue, delegating to a bespoke topology
check — which this slice provides.

## Boundary

In scope: one new INV-003 assertion; the ARCHITECTURE.md block update; the
D2 paragraph; the asymmetry decision plus its single edit in
`checks/role_guard.py`. Out of scope: INV-001 and INV-002 bindings; the
generic `git-log-walk` and `structural-parser` assertion types;
anti-behavior prose matching; any refactor of `ROLE_FOR_PHASE`'s shape.

## Specification

### Public interface

A new validator entry point reachable from `scripts/validate_architecture.py`
that loads the four canonical declaration sites listed below, projects each
into a normalized set of `(phase_ordinal, role_slug)` pairs, and asserts
pairwise equality across all four projections. Discrepancies are reported as
a structured failure naming the offending source(s), the missing/extra
pair(s), and the canonical reference set.

The binding is invoked from `validate_architecture.py`'s assertion loop the
same way other INV assertions are invoked. The invocation surface, not the
internal helper shape, is the public interface that downstream slices and
hooks may rely on.

### Canonical declaration sites (the four sources)

1. `scripts/slice_orchestrator/core.py` — the `ROLE_FOR_PHASE` mapping
   (lines 42–47 per recon). Treated as the authoritative source: when the
   four sets disagree, the failure message names this site as the reference.
2. `docs/operational-reference.md` § Phase Skill Guide — two regex-extracted
   tables (lines 80–85 and 91–96 per recon) yielding `(phase_ordinal, role)`
   rows.
3. `.claude/agents/phase-{1..4}-*.md` — filename glob; phase ordinal and
   role slug parsed from the `phase-N-role` filename prefix.
4. `checks/role_guard.py` — the union of keys in `ROLE_POLICIES` and
   `ROLE_DENY_READ` (lines 42–66 per recon), with the asymmetry handling
   below.

### Failure modes the binding must catch

- Phase added or removed in one source but not the others.
- Role renamed (e.g. `skeptic` → `validator`) in one source.
- `ROLE_POLICIES` or `ROLE_DENY_READ` key drift in `role_guard.py`.
- Prompt file added under `.claude/agents/` without a corresponding
  `ROLE_FOR_PHASE` entry.
- `ROLE_FOR_PHASE` entry added without a corresponding prompt file.

### Asymmetry decision (must be resolved in this slice)

`phase-3-implementer` carries no static `ROLE_POLICIES` entry; its
write-path gate is granted dynamically per `AGENT_ENVELOPE` under
compression-infrastructure-bootstrap. The Reader records the decision point;
the slice must converge on one of:

- (a) Treat the absence as a gap. Require a static entry for all four roles
  in `role_guard.py`; the binding asserts symmetric coverage across the four
  sources without exception.
- (b) Treat the absence as intentional per compression-infrastructure-bootstrap.
  The binding tolerates an envelope-grant-only role provided
  `role_guard.py` carries an explanatory comment naming the asymmetry, and
  the binding's source-4 projection accounts for the named exception
  explicitly (not via silent omission).

Operator recommendation in the brief is (b). The Reader does not select
between them; the decision is made in the next phase and reflected in tests.

### ARCHITECTURE.md surface

The INV-003 assertion block is replaced. The grep-style proxy is removed.
The new block points at the validator entry and names the four sources. The
D2 paragraph is updated to reflect that INV-003 now carries a true binding.

### Invariants touched

INV-003: proxy replaced with true four-way binding. No other invariants
modified.

### ADRs created

None. The slice operates under existing firm ADRs (phase-lock-and-role-declaration,
cliff-failure-mode-and-v1-defenses) and one provisional ADR
(compression-infrastructure-bootstrap, only for the asymmetry rationale under
option (b)). invariant-binding-strategy and pipeline-substrate-naming are
adjacent context.

## Verification

The slice is correct when, with the binding installed:

1. A clean tree passes the new assertion with all four sources in agreement.
2. Each of the following synthetic perturbations causes the assertion to
   fail with a message naming the perturbed source and the offending pair:
   - Drop a phase from `ROLE_FOR_PHASE`.
   - Rename a role in one Skill Guide table row.
   - Rename or remove a `ROLE_POLICIES` key in `role_guard.py` (under the
     option chosen for the asymmetry).
   - Add a `phase-5-*.md` file under `.claude/agents/` without a matching
     `ROLE_FOR_PHASE` entry.
3. The ARCHITECTURE.md assertion block for INV-003 is parseable by the
   architecture validator's existing block reader and resolves to the new
   binding.
4. The asymmetry decision is observable in the source: either a static
   `phase-3-implementer` entry exists in `role_guard.py` (option a) or a
   comment naming the asymmetry exists at the relevant declaration (option b).
5. Out-of-scope invariants (INV-001, INV-002) and out-of-scope assertion
   types (`git-log-walk`, `structural-parser`) are unchanged by this slice.

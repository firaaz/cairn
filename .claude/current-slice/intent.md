---
slice: design-decomposition
date: 2026-04-12
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-002, ADR-003, ADR-004]
envelope:
  - "docs/adr/005-*.md"
  - "docs/adr/006-*.md"
  - "docs/adr/007-*.md"
  - "docs/adr/008-*.md"
  - "docs/adr/index.md"
out-of-scope:
  - "ADR renaming (sequential → semantic) — future implementation slice"
  - "Feature directory structure (.claude/features/) — future implementation slice"
  - "Hook/command updates (/start-slice, /handoff, scope-guard) — future implementation slices"
  - "Code changes of any kind"
  - "docs/ARCHITECTURE.md regeneration — happens via /refresh-architecture after ADRs land"
---

### What and Why

Formalize the approved feature-slice model design (`docs/plans/2026-04-12-feature-slice-model-design.md`) into four separate ADRs. The design solves three structural problems (sequential numbering blocks multi-dev, no feature grouping, dependencies implicit in prose) but its decisions span distinct concern boundaries that need individual ADR treatment for clean supersession and independent firmness levels.

This slice produces decision documents only — no implementation. Implementation slices will reference these ADRs via the D3 gate.

### ADR Breakdown

**ADR-005: Semantic Identity**
- Replaces sequential numbering (SLICE-001, ADR-001) with kebab-case IDs for slices and ADRs
- Collision avoidance via semantic uniqueness
- Migration path for existing ADRs (rename + cross-reference update)
- `reversibility-guard.sh` glob change: `*/docs/adr/[0-9]*` → `*/docs/adr/*.md` with `index.md` excluded
- Scope-guard pattern updates for semantic slice IDs
- Firmness: firm (naming convention is load-bearing for all downstream tooling)

**ADR-006: Feature-Slice Model**
- Features as unit of intent, slices as unit of execution
- `.claude/features/<id>.yaml` file structure and schema
- Single-responsibility file model: handoff.md / feature file / slice.yaml ownership split
- Trigger-based updates: which events update which files, max 2 files per event
- Slice lifecycle: planned → active → [parked →] complete/dropped
- Parked state protocol: `parked: true` + `blocked-by` in slice.yaml
- Mid-work discovery protocol (prerequisite found, scope too large, phase is hard)
- Status derived from branch/file state, not stored (except `dropped`)
- Always-create policy for feature files
- Firmness: firm (structural model for all future work)

**ADR-007: Parallelism v1**
- Supersedes ADR-003 D4 parallelism deferral — parallelism is v1-native
- Slices without unmet `after` constraints can run concurrently
- Feature-level parallelism (different features on different branches)
- Intra-feature parallelism (different slices on separate branches within a feature)
- No global "active slice" pointer — state is branch-local
- Un-excludes `dispatching-parallel-agents` and `using-git-worktrees` from ADR-004 D4
- Specifies which other D4 time-box items remain deferred vs. return
- Firmness: provisional (parallelism model needs dogfood validation)

**ADR-008: Context Tiers Integration**
- Maps the feature-slice model to ADR-002's three-tier context discipline
- Tier 1: handoff.md gains cross-feature index (one-liner per active feature, within 150-400 token budget)
- Tier 2: feature file loaded on-demand when entering a feature branch
- Tier 3: slice.yaml on active branch (unchanged)
- Feature inventory for Tier 1 derived from handoff's feature index
- Confirms INV-002 accommodates this without amendment, or amends if needed
- Firmness: firm (context discipline is foundational)

### Supersession Map

| New ADR | Supersedes | Scope of supersession |
|---------|------------|----------------------|
| ADR-007 | ADR-003 D4 (partial) | Parallelism deferral only; D0/D1/D2/D3 unchanged |
| ADR-007 | ADR-004 D4 (partial) | Exclusion of `dispatching-parallel-agents` and `using-git-worktrees` only |
| ADR-008 | ADR-002 (partial, if needed) | Only if cross-feature index requires INV-002 amendment |

### Boundary

- This slice does NOT rename existing ADRs — that is an implementation slice after ADR-005 lands
- This slice does NOT create `.claude/features/` — that is an implementation slice after ADR-006 lands
- This slice does NOT modify hooks, commands, or scripts — those are implementation slices
- This slice does NOT regenerate `docs/ARCHITECTURE.md` — that happens via `/refresh-architecture` after commit
- This slice does NOT update `docs/roadmap.md` — roadmap updates happen after implementation slices complete the covered items

### Specification Detail

Each ADR follows the existing format in `docs/adr/`:
- YAML frontmatter: `id`, `title`, `status: accepted`, `firmness`, `date`, `supersedes` (if applicable)
- Sections: Context, Decision (numbered commitments D0..DN), Consequences, Risk Register (if provisional)
- Supersession references use the `supersedes:` frontmatter field AND inline prose in the relevant decision
- Each ADR must be self-contained — a reader with no other context should understand the decision from the ADR alone
- ADR index (`docs/adr/index.md`) updated with all four new entries

### Verification

- [ ] Four ADR files exist matching `docs/adr/005-*.md`, `006-*.md`, `007-*.md`, `008-*.md`
- [ ] Each ADR has valid YAML frontmatter with `id`, `title`, `status`, `firmness`, `date`
- [ ] ADR-007 `supersedes:` field names ADR-003 D4; ADR-007 prose explains partial supersession scope
- [ ] ADR-007 addresses each ADR-004 D4 time-boxed item: stays deferred or returns to v1
- [ ] ADR-008 explicitly states whether INV-002 needs amendment
- [ ] `docs/adr/index.md` has entries for all four new ADRs
- [ ] No files outside the envelope are modified
- [ ] No implementation decisions are made — ADRs describe what, not how to build it

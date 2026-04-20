---
phase: 3
commit: b4ce212abc055f40b65e78c22fe81241ef198f92
---

Phase 3 widening (tests/unit/test_adr_rename_sweep.py) already committed as 38100de: retired 12-file size latch, derived V5 expected ids from live corpus, added TestLiveCorpusFlatSlugShape parametrized over docs/adr/*.md with filename regex + id/stem match (offender name in message), docstring updated to name the non-cardinality shape contract, zero literal references to the post-sweep ADR slug. Phase 2 re-dispatch (6985d43) fragment-joined the C1 forbidden name, unblocking the probe. pytest tests/unit/test_adr_rename_sweep.py -q → 66 passed on live 13-file corpus. Envelope-clean. Out-of-envelope hook/housekeeping failures are pre-existing, not this slice.

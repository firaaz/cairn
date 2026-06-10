---
contract:
  must-satisfy:
    - every body line names a thread with a resolvable pointer
    - each thread declares state ∈ {open, blocked, deferred}
    - at most 6 active threads (carrier-hierarchy-and-process-diet D6)
  must-not-violate:
    - no narrative prose; no multi-sentence entries
    - no open-issue mirror — gh issues live solely in gh
  wrong-if:
    - any pointer fails to resolve on read
  evidence:
    - tests/unit/test_handoff_contract.py passes
---
- docs/adr/carrier-hierarchy-and-process-diet.md open closed-4d8738d+18-issues-swept+merge-to-dev-pending
- docs/adr/intent-management-loop.md open activated-default+D7/R2-resolved-tdd-feature-legacy
- a18bca0 open v0.1.0-tag-converged-local-eq-remote-b190b5f+release-smoke-unverified
- 61afec4 open codex-local-plugin+renamed-skills+manifest-tests-on-dev

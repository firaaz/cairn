# Cairn Workflow Registry

This directory holds Cairn-owned workflow definitions. A workflow is an
executable operating mode made of node contracts: role, prompt, allowed inputs,
write envelope, evidence requirements, and pass/fail output.

The first registry entry is `cairn-intent`. Its Claude dynamic workflow executor
is deliberately split into separate challenge and close-review runs because
Claude workflows cannot take mid-run user input. Reusable scripts should only be
saved under `.claude/workflows/` after the generated draft has been reviewed and
dogfooded.

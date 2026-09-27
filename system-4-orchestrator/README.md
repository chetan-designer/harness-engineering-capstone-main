# Shift Monitor Orchestrator

This component coordinates a quality-engineering shift workflow. It keeps a small
hot state for prompt construction, reads newer defects from the warm store, records
shift findings in a scratchpad, and supports isolated hypothesis forks.

## Design notes

- Hot state is validated before it is written.
- State files are replaced atomically and flushed before replacement.
- Recent defect identifiers are bounded so prompt state remains small.
- Forks allow experiments without mutating the main state.
- The scratchpad provides an append-only record of conclusions.

## Verification

Run the tests from this directory:

```bash
pytest tests/ -v
```

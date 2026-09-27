# Retail Support Context Strategy

This component builds a compact context for a multi-issue customer-support
conversation. The application decides what information should remain available:
stable case facts are kept explicit, resolved issues are summarized, and the
currently active issue remains verbatim.

## Architecture

1. Load and segment the conversation.
2. Extract durable case facts.
3. Prune verbose tool responses to decision-relevant fields.
4. Summarize completed issues.
5. Assemble the result with the durable facts and active issue at the boundaries.
6. Evaluate the assembled context against the supplied questions.

The implementation keeps these decisions in application code so the resulting
context can be inspected and tested.

## Verification

```bash
pytest tests/ -v
```

To build the context with an API key configured:

```bash
python -m retail_context.run --build
```

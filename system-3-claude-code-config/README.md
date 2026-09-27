# E-commerce Claude Code Configuration

This package provides project-level configuration helpers for a small e-commerce
codebase. It demonstrates hierarchical instructions, path-scoped rules, review
commands, and a deployment-check skill.

## Included pieces

- `CLAUDE.md` — project-wide conventions.
- `.claude/rules/` — rules activated for selected paths.
- `.claude/standards/` — shared engineering standards.
- `.claude/commands/review.md` — repeatable review guidance.
- `.claude/skills/deploy-check/SKILL.md` — read-only deployment checks.
- `ecommerce_team_config/` — parser and validation helpers.
- `tests/` — behavioral checks for the configuration.

## Verification

```bash
pytest -q
```

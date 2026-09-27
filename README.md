# Harness Engineering Capstone

A four-part engineering project exploring reliable patterns for agentic software systems.
The repository is organized as independent systems so each component can be installed,
tested, and reviewed on its own.

## Repository layout

- `system-1-agentic-loop/` — claims-intake agent loop, tool handling, and safety checks.
- `system-2-context-strategy/` — context selection and compression for retail support conversations.
- `system-3-claude-code-config/` — project configuration, scoped rules, review guidance, and validation helpers.
- `system-4-orchestrator/` — tiered state, recovery, invocation flow, and investigation forks.

## Requirements

- Python 3.11+
- Git
- A virtual environment is recommended for each system.
- System 1, 2, and 4 use Anthropic-related functionality for their live integrations. Tests that exercise live API behavior require the corresponding credentials.

## Running a system

Each system contains its own `pyproject.toml` and test suite. For example:

```bash
cd system-1-agentic-loop
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Repeat the same pattern in the other system directories. On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## GitHub hygiene

Generated caches, virtual environments, compiled Python files, build output, and local editor
metadata are excluded through `.gitignore`. Runtime state for the orchestrator is intentionally
not committed; the application recreates it when needed.

Do not commit API keys, `.env` files, credentials, or other secrets.

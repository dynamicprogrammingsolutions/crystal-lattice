# Testing & validation

This page is shared across plugin kinds.

## Plugin repo tests (recommended primary workflow)

For plugin development, prefer a tight loop:

1. edit plugin code
2. run `pytest`
3. iterate

Example (template provider repo):

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/template-python-provider[dev]"
pytest plugins/template-python-provider/tests -q
```

## Repo-level tests

From repo root:

- Core tests: `pytest core/python/tests -q`
- Example tests: `pytest core/python/examples/tests -qs`

Markers used in core tests:

- `-m openrouter` (requires `OPENROUTER_API_KEY`)
- `-m integration`
- `-m ollama`

## Lint/format/typecheck

From repo root:

```bash
ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins
black core/python/agent_core core/python/tests core/python/examples core/python/plugins
pyright
```

See also: `AGENTS.md`.

# Plugins Directory Guidelines

This directory contains **optional plugin repositories** for the AI Agent Platform.

What you'll find here:

- **Python plugins** packaged with `pyproject.toml` (providers, features, tools, apps).
- **Node.js tool plugins** (`js-*`) that are loaded via the `node_tool` plugin source.
- **Bash tool plugins** that are loaded via the `bash_tool` plugin source.
- **Templates** (`template-*`) that you can copy to start a new plugin repo.

For plugin authoring guidance, see:

- `docs/plugins/development.md` (general overview)
- `plugins/docs/provider-plugins.md` (canonical provider authoring guide)

## Testing Pattern

Do **not** add `conftest.py` files that mutate `sys.path` for imports.
Plugin tests should run using standard Python packaging semantics.

From the repo root:

1) Install the core SDK (editable):

```bash
python -m pip install -e core/python
```

2) Install a plugin (editable) with test dependencies:

```bash
python -m pip install -e "plugins/<plugin-name>[dev]"
```

3) Run the plugin tests:

```bash
pytest plugins/<plugin-name>/tests -q
```

## Core Test Fixtures

Core SDK tests should avoid depending on plugin repos under `plugins/`.

- Node tool loader tests use fixtures under `core/python/tests/fixtures/node_tools/`.
- Bash tool loader tests use fixtures under `core/python/tests/fixtures/bash_tools/`.

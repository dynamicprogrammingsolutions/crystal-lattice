# Plugins Directory Guidelines

This directory is the repo home for **built-in plugin projects** used by the current
runtime layout, along with plugin templates and shared plugin docs for the AI Agent
Platform.

What you'll find here:

- **Built-in plugin projects** packaged with `pyproject.toml` (providers, features,
  tools, apps).
- **Node.js tool plugins** (`js-*`) that are loaded via the `node_tool` plugin source.
- **Bash tool plugins** that are loaded via the `bash_tool` plugin source.
- **Templates** (`template-*`) that you can copy to start a new plugin repo.
- **Shared plugin docs** under `plugins/docs/`.

For plugin authoring guidance, see:

- `plugins/docs/index.md` (current plugin docs entrypoint)
- `plugins/docs/overview.md` (general plugin-system overview)

## Testing Pattern

Do **not** add `conftest.py` files that mutate `sys.path` for imports.
Plugin tests should run using standard Python packaging semantics.

From the repo root:

1) Install the core SDK (editable):

```bash
python -m pip install -e core/python
```

2) Install the terminal/server app only when the plugin work needs app-level integration:

```bash
python -m pip install -e application/python
```

3) Install the specific plugin package you are changing (editable) with test dependencies:

```bash
python -m pip install -e "plugins/<plugin-name>[dev]"
```

4) Run the plugin tests:

```bash
pytest plugins/<plugin-name>/tests -q
```

`core/python` and `application/python` do not install repo-root plugin
packages for you. Keep plugin installs explicit so tests run against the plugin
checkout you are editing.

## Core Test Fixtures

Core SDK tests should avoid depending on plugin repos under `plugins/`.

- Node tool loader tests use fixtures under `core/python/tests/fixtures/node_tools/`.
- Bash tool loader tests use fixtures under `core/python/tests/fixtures/bash_tools/`.

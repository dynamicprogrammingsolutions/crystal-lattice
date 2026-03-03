# Subtask: Create `plugins/template-python-provider` template repo

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

## Description

Create a new template plugin repository for **Python provider plugins**, modeled after the existing tool template repo `plugins/template-python-tools`.

This template is intended for plugin authors to copy/fork when building a new provider integration. It must include skeleton implementations for:

- `ProviderPlugin` (provider)
- `ProviderExtensionPlugin` (provider extension)
- `FeaturePlugin` (feature)

It must also include a small, deterministic test suite within the template package itself.

## Goals

- Provide a ready-to-use repo with:
  - `pyproject.toml` using `src/` layout
  - `agent_plugin.json` descriptor installed as a top-level data file
  - minimal provider/extension/feature skeleton code
  - `tests/` directory with pytest tests
- Ensure template tests pass offline and demonstrate:
  - non-streaming (`send_request`)
  - streaming (`send_request_stream`)
  - native history retention across two turns (preferably across two `AgentCore` instances)
  - extension and feature hooks actually run

## Planned template contents

Directory: `plugins/template-python-provider/`

- `README.md`
  - Development install/test commands (mirroring `plugins/template-python-tools/README.md`):
    - `python -m pip install -e core/python`
    - `python -m pip install -e "plugins/template-python-provider[dev]"`
    - `pytest plugins/template-python-provider/tests -q`

- `pyproject.toml`
  - `project.name = "template-python-provider"`
  - `dependencies = ["agent-core>=0.3.0"]`
  - `optional-dependencies.dev = ["pytest>=7.0.0"]`
  - setuptools `src/` package discovery
  - install `agent_plugin.json` via `[tool.setuptools.data-files]`
  - pytest config

- `agent_plugin.json`
  - `entries` includes dotted paths for provider, extension, and feature classes.

- `src/template_python_provider/`
  - `__init__.py` exports classes
  - `provider.py`: deterministic offline provider skeleton
    - supports both non-streaming and streaming patterns
    - uses `state["partial"]` accumulator in streaming
    - demonstrates `_metadata` handling in conversions
  - `extension.py`: provider extension skeleton
    - demonstrates tags + required_tags
    - demonstrates cooperating on `state["partial"]`
    - demonstrates `from_native_messages` enrichment of core metadata
  - `feature.py`: feature skeleton
    - demonstrates request modifications and/or finalize transformations

- `tests/`
  - `test_non_streaming_provider.py`
  - `test_streaming_provider.py`
  - `test_native_history_retention.py`

## Success criteria

- `python -m pip install -e core/python`
- `python -m pip install -e "plugins/template-python-provider[dev]"`
- `pytest plugins/template-python-provider/tests -q` passes.

## Notes / Constraints

- Template provider must avoid network I/O.
- Tests should run quickly and deterministically.

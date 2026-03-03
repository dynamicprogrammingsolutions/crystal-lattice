# template-python-provider

Template plugin repo for **Python provider plugins** (provider + provider extension + feature).

This is intentionally small and mirrors the structure of `plugins/template-python-tools`:

- `pyproject.toml` (editable install + `pytest` in `.[dev]`)
- `agent_plugin.json` descriptor
- `src/` layout Python package
- `tests/` with minimal unit tests (offline, deterministic)

## What’s included

This template contains **minimal placeholders**, plus a small shared
implementation for the **accumulator streaming pattern**.

You should be able to copy this repo and only **add** provider-specific logic
(HTTP calls, chunk parsing, conversions) without deleting a pre-built example.

Included:

- `TemplateProvider` (skeleton)
  - includes a shared accumulator-based `process_chunk`/`finalize`
  - you implement: `call_api`, `stream_api`, `extract_delta`, `process_delta`
- `TemplateProviderExtension` (no-op skeleton)
- `TemplateFeature` (no-op skeleton)

The `tests/` directory defines test-only provider subclasses that implement
the missing pieces deterministically. This keeps the template runnable while
still requiring authors to fill in real logic.

## Development

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/template-python-provider[dev]"
pytest plugins/template-python-provider/tests -q
```

## Using this template

Copy this directory, then rename:

- the project name in `pyproject.toml`
- the Python package under `src/`
- plugin class names and their `name`/`version` fields
- entries in `agent_plugin.json`

Then add provider-specific API I/O logic in your provider class and expand tests to match your integration.

## Two streaming paths

1) **Accumulator pattern (recommended)**
   - keep the shared `process_chunk` and `finalize`
   - implement: `stream_api`, `extract_delta`, `process_delta`

2) **Custom streaming**
   - implement: `process_chunk` and `finalize` yourself
   - use this when the provider stream format is unusual or you need
     specialized finalization behavior

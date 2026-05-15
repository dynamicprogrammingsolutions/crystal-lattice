# template-python-tools

Template plugin repo for **Python tool plugins**.

This is intentionally small and mirrors the structure of `plugins/codex-tools`:

- `pyproject.toml` (editable install + `pytest` in `.[dev]`)
- `agent_plugin.json` descriptor
- `src/` layout Python package
- `tests/` with a minimal unit test

## Development

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/template-python-tools[dev]"
pytest plugins/template-python-tools/tests -q
```

## License

This directory is available under the [Apache License 2.0](../../LICENSE).

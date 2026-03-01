# template-bash-tool

Template plugin repo for **bash tool plugins**.

This mirrors `plugins/bash-read-line-range`:

- A `*.bash` tool script implementing `schema`, `preview`, `run`, and `error`.
- An `agent_plugin.json` descriptor listing bash tool files.
- Minimal Python packaging (`pyproject.toml`) so tests can be run with `pytest`.

## Development

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/template-bash-tool[dev]"
pytest plugins/template-bash-tool/tests -q
```

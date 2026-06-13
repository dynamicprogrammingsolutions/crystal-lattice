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

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

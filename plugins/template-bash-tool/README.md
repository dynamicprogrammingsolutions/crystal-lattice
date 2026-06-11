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

# embedded-codex-tools

Codex-like, iOS-safe command tools for the embedded Crystal Lattice runtime.

The package exposes lowercase, command-shaped tools:

- `sed`: bounded line-range reads.
- `rg`: bounded recursive text search.
- `find`: bounded workspace path enumeration.
- `curl`: bounded public HTTP(S) GET requests.
- `apply_patch`: Codex freeform file patches.

The tools describe the shell commands they emulate and return command, exit
code, wall time, and bounded output. They use pure-Python engines from
`embedded-tools-shared`; no shell command is parsed or executed. In
particular, `curl` is a bounded public HTTP(S) GET wrapper, not a general shell
command.

## Loading

```json
{
  "plugins": [
    "path:/path/to/plugins/embedded-codex-tools"
  ],
  "working_directory": "/app-owned/workspace"
}
```

## Development

From the repository root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/embedded-codex-tools[dev]"
pytest plugins/embedded-codex-tools/tests -q
```

The credential-gated OpenAI Responses check uses Luna with all five tools:

```bash
pytest plugins/embedded-codex-tools/tests/test_luna_real_api.py \
  -m 'integration and api and openai' -q
```

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
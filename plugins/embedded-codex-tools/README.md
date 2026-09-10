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
`embedded-tools-shared`; no shell command is parsed or executed.

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

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
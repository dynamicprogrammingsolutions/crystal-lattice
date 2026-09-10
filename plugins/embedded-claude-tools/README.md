# embedded-claude-tools

Claude-like, iOS-safe workspace tools for the embedded Crystal Lattice runtime.

The initial package exposes:

- `Read`: read a bounded UTF-8 line window from a workspace-relative file.
- `Write`: create or replace a UTF-8 file inside the workspace.

The package uses `embedded-tools-shared` for canonical path authorization and
text operations. Absolute paths, traversal, and symlink escapes are rejected.
It does not provide shell execution or arbitrary filesystem access.

## Loading

Load the package through its plugin descriptor:

```json
{
  "plugins": [
    "path:/path/to/plugins/embedded-claude-tools"
  ]
}
```

Configure one workspace root:

```json
{
  "working_directory": "/app-owned/workspace"
}
```

## Development

From the repository root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/embedded-claude-tools[dev]"
pytest plugins/embedded-claude-tools/tests -q
```

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
# embedded-tools-shared

Pure-Python engines shared by the embedded Claude-like and Codex-like tool
plugins.

The package is model-invisible: it defines no plugin descriptor or tool
schemas. It owns canonical workspace path resolution plus bounded UTF-8 text
reading and writing. Model-facing packages provide their own names, schemas,
result formatting, and tool-use conventions.

Workspace paths are relative to a configured root. Absolute paths, traversal,
and symlink escapes are rejected.

## Development

From the repository root:

```bash
python -m pip install -e "plugins/embedded-tools-shared[dev]"
pytest plugins/embedded-tools-shared/tests -q
```

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
# embedded-claude-tools

Claude-like, iOS-safe workspace tools for the embedded Crystal Lattice runtime.

The package exposes:

- `Read`: read a bounded UTF-8 line window from a workspace-relative file.
- `Write`: create or replace a UTF-8 file inside the workspace.
- `Edit`: perform exact text replacements after reading the file.
- `Glob`: list files matching a workspace-relative glob.
- `Grep`: search workspace text using bounded regular expressions.
- `WebFetch`: fetch and extract bounded text from a public HTTP(S) page.

The package uses `embedded-tools-shared` for canonical path authorization and
text operations. Absolute paths, traversal, and symlink escapes are rejected.
Existing files must be read before `Write` or `Edit` changes them. The package
does not provide shell execution or arbitrary filesystem access.

`WebFetch` retrieves one public page; it is not a Tavily or general web-search
tool. It rejects private, local, reserved, and non-HTTP(S) destinations,
revalidates redirects, and bounds time, redirects, downloaded bytes, and
returned text. Requests and tool results may be sent to the selected model
provider as part of the conversation.

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

Credential-gated provider checks use the same package with OpenRouter and
official Anthropic:

```bash
pytest plugins/embedded-claude-tools/tests/test_provider_real_api.py \
  -m 'integration and api and openrouter' -q
pytest plugins/embedded-claude-tools/tests/test_provider_real_api.py \
  -m 'integration and api and anthropic' -q
```

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
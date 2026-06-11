# Glob Tool Investigation Notes

Status: initial default-path, scoped-path, no-match, missing-directory, and truncation fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/glob/success-default-relative.json`
- `plugins/claude-tools/investigation/fixtures/glob/success-scoped-absolute.json`
- `plugins/claude-tools/investigation/fixtures/glob/success-no-matches.json`
- `plugins/claude-tools/investigation/fixtures/glob/error-missing-directory.json`
- `plugins/claude-tools/investigation/fixtures/glob/success-truncated-results.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/glob/`.

## Tool Name

Claude Code advertises the file matcher as:

```text
Glob
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `Glob`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["pattern"]`
- `additionalProperties`: `false`

Properties:

- `pattern`: string, required, glob pattern.
- `path`: string, optional, directory to search in.

## Result Formatting

When `path` is omitted, successful matches are returned as newline-delimited paths relative to the current working directory:

```text
src/a.py
src/nested/b.py
```

When `path` is provided, successful matches are returned as newline-delimited absolute paths:

```text
<WORKSPACE>/src/a.py
<WORKSPACE>/src/nested/b.py
```

No-match result:

```text
No files found
```

Truncated result output appends:

```text
(Results are truncated. Consider using a more specific path or pattern.)
```

## Error Formatting

Missing directory:

```text
<tool_use_error>Directory does not exist: <WORKSPACE>/missing-dir. Note: your current working directory is <WORKSPACE>.</tool_use_error>
```

## Implementation Direction

- Implement `Glob` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared glob search engine for file discovery and sorting.
- Return newline-delimited results with the observed relative-vs-absolute path behavior based on whether `path` was omitted or provided.
- Match the observed no-match string, truncation suffix, and XML-like `<tool_use_error>...</tool_use_error>` wrapper for path errors.
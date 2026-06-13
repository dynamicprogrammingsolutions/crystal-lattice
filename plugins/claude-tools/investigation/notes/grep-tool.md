# Grep Tool Investigation Notes

Status: initial default files-with-matches, content mode, count mode, no-match, and missing-path fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/grep/success-default-relative.json`
- `plugins/claude-tools/investigation/fixtures/grep/success-default-absolute.json`
- `plugins/claude-tools/investigation/fixtures/grep/success-content-mode.json`
- `plugins/claude-tools/investigation/fixtures/grep/success-count-mode.json`
- `plugins/claude-tools/investigation/fixtures/grep/success-no-matches.json`
- `plugins/claude-tools/investigation/fixtures/grep/error-missing-path.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/grep/`.

## Tool Name

Claude Code advertises the search tool as:

```text
Grep
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `Grep`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["pattern"]`
- `additionalProperties`: `false`

## Result Formatting

Default `files_with_matches` mode:

- With no `path`, output starts with `Found N files` followed by newline-delimited relative paths from the current working directory.
- With `path` provided, output starts with `Found N files` followed by newline-delimited absolute paths.

Observed example:

```text
Found 2 files
<WORKSPACE>/src/b.txt
<WORKSPACE>/src/a.txt
```

Content mode:

```text
<WORKSPACE>/src/a.txt:2:needle one
<WORKSPACE>/src/b.txt:2:needle two
<WORKSPACE>/src/b.txt:3:needle three
```

Count mode:

```text
<WORKSPACE>/src/a.txt:1
<WORKSPACE>/src/b.txt:2

Found 3 total occurrences across 2 files.
```

No-match result:

```text
No files found
```

## Error Formatting

Missing path:

```text
<tool_use_error>Path does not exist: <WORKSPACE>/missing. Note: your current working directory is <WORKSPACE>.</tool_use_error>
```

## Implementation Direction

- Implement `Grep` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared grep search engine for regex search behavior and filters.
- Match the observed mode-specific formatting:
  - `files_with_matches`: `Found N files` header plus file list
  - `content`: raw `path:line:text` output
  - `count`: `path:count` lines plus summary footer
- Match the observed no-match string and XML-like `<tool_use_error>...</tool_use_error>` wrapper for missing paths.
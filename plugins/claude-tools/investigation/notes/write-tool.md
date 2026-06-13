# Write Tool Investigation Notes

Status: initial create, overwrite-after-read, overwrite-without-read, and nested-parent create fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/write/success-create-file.json`
- `plugins/claude-tools/investigation/fixtures/write/success-overwrite-after-read.json`
- `plugins/claude-tools/investigation/fixtures/write/error-overwrite-without-read.json`
- `plugins/claude-tools/investigation/fixtures/write/success-create-missing-parent.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/write/`.

## Tool Name

Claude Code advertises the file writer as:

```text
Write
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `Write`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["file_path", "content"]`
- `additionalProperties`: `false`

Properties:

- `file_path`: string, required, absolute path to the file.
- `content`: string, required, full replacement file content.

## Observed Calls

Create-file call:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Write",
  "input": {
    "file_path": "<WORKSPACE>/note.txt",
    "content": "WRITE_SENTINEL one two three"
  }
}
```

Overwrite-after-read call:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Write",
  "input": {
    "file_path": "<WORKSPACE>/existing.txt",
    "content": "NEW_CONTENT"
  }
}
```

Claude Code used absolute paths in every observed call.

## Result Formatting

Successful create results are sent back as a single Anthropic `tool_result` string:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "<TOOL_CALL_ID>",
      "content": "File created successfully at: <WORKSPACE>/note.txt",
      "cache_control": {
        "type": "ephemeral"
      }
    }
  ]
}
```

Successful overwrites after a prior `Read` return:

```text
The file <WORKSPACE>/existing.txt has been updated successfully.
```

Creating a file under a missing parent directory also succeeded:

```text
File created successfully at: <WORKSPACE>/missing/dir/note.txt
```

This indicates Claude Code creates parent directories as needed for `Write`.

## Read-Before-Write Guard

Attempting to overwrite an existing file without first reading it returns an error result:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "content": "<tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>",
  "is_error": true,
  "cache_control": {
    "type": "ephemeral"
  }
}
```

During this failure case, Claude Code repeatedly attempted other disabled tools such as `Read`, `Glob`, and `Shell`. The committed fixture should focus on the first `Write` error result for deterministic parity.

## Implementation Direction

- Implement `Write` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared file-writing engine for overwrite and parent-directory creation.
- Enforce the observed read-before-write guard for existing files.
- Return provider-native Anthropic `tool_result` payloads with exact observed success strings and the XML-like `<tool_use_error>...</tool_use_error>` error wrapper.
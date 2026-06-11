# Edit Tool Investigation Notes

Status: initial single-replace, replace-all, no-read, no-match, and multiple-match fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/edit/success-single-replace.json`
- `plugins/claude-tools/investigation/fixtures/edit/success-replace-all.json`
- `plugins/claude-tools/investigation/fixtures/edit/error-without-read.json`
- `plugins/claude-tools/investigation/fixtures/edit/error-string-not-found.json`
- `plugins/claude-tools/investigation/fixtures/edit/error-multiple-without-replace-all.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/edit/`.

## Tool Name

Claude Code advertises the exact string editor as:

```text
Edit
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `Edit`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["file_path", "old_string", "new_string"]`
- `additionalProperties`: `false`

Properties:

- `file_path`: string, required, absolute path to the file.
- `old_string`: string, required, exact text to replace.
- `new_string`: string, required, replacement text.
- `replace_all`: boolean, optional, default `false`.

## Observed Calls

Single replace:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Edit",
  "input": {
    "replace_all": false,
    "file_path": "<WORKSPACE>/sample.txt",
    "old_string": "beta",
    "new_string": "BETA"
  }
}
```

Replace all:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Edit",
  "input": {
    "replace_all": true,
    "file_path": "<WORKSPACE>/dups.txt",
    "old_string": "dup",
    "new_string": "DUP"
  }
}
```

Claude Code used absolute paths in every observed call.

## Result Formatting

Successful single replacement:

```text
The file <WORKSPACE>/sample.txt has been updated successfully.
```

Successful replace-all:

```text
The file <WORKSPACE>/dups.txt has been updated. All occurrences were successfully replaced.
```

## Read-Before-Edit Guard

Attempting to edit an existing file without first reading it returns:

```text
<tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
```

This message currently says "before writing to it" rather than "before editing it" in the captured Claude behavior.

## Other Error Formatting

String not found:

```text
<tool_use_error>String to replace not found in file.
String: DOES_NOT_EXIST</tool_use_error>
```

Multiple matches with `replace_all: false`:

```text
<tool_use_error>Found 2 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.
String: dup</tool_use_error>
```

## Implementation Direction

- Implement `Edit` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared literal replacement helper for exact single and replace-all replacements.
- Enforce the observed read-before-edit guard for existing files.
- Match the observed success text and XML-like `<tool_use_error>...</tool_use_error>` wrappers for key failures.
# Bash Tool Investigation Notes

Status: initial foreground success/failure/timeout, cwd-reset, and background fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/bash/success-pwd.json`
- `plugins/claude-tools/investigation/fixtures/bash/success-stderr-zero.json`
- `plugins/claude-tools/investigation/fixtures/bash/error-nonzero.json`
- `plugins/claude-tools/investigation/fixtures/bash/error-timeout.json`
- `plugins/claude-tools/investigation/fixtures/bash/success-cwd-reset.json`
- `plugins/claude-tools/investigation/fixtures/bash/success-background.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/bash/`.

## Tool Name

Claude Code advertises the shell tool as:

```text
Bash
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `Bash`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["command"]`
- `additionalProperties`: `false`

## Result Formatting

Successful foreground command with stdout:

```text
<WORKING_DIRECTORY>
```

Successful command with stderr but exit code `0`:

```text
problem
```

Non-zero exit:

```text
Exit code 7
problem
```

Timeout result:

```text
Exit code 143
```

Observed `cd` command result:

```text
<WORKING_DIRECTORY>/subdir
```

Background result:

```text
Command running in background with ID: <BACKGROUND_ID>. Output is being written to: <BACKGROUND_OUTPUT_PATH>
```

## Implementation Direction

- Implement `Bash` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared shell engine for foreground execution.
- Match the observed output policy:
  - success: raw output only
  - non-zero exit: `Exit code N` prefix plus output
  - timeout: report `Exit code 143`
- Use the configured working directory for each Bash execution; the current captured fixture for `cd ... && pwd` returns only the command output.
- Support `run_in_background` with the observed `background ID + output file path` success message.
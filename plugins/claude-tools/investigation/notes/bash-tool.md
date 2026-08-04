# Bash Tool Investigation Notes

Status: foreground success/failure/timeout (including no-output variants), cwd-reset, and background fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/bash/success-pwd.json`
- `plugins/claude-tools/investigation/fixtures/bash/success-stderr-zero.json`
- `plugins/claude-tools/investigation/fixtures/bash/success-no-output.json`
- `plugins/claude-tools/investigation/fixtures/bash/error-nonzero.json`
- `plugins/claude-tools/investigation/fixtures/bash/error-no-output.json`
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

Successful command with no output (exit code `0`, empty stdout/stderr):

```text
(Bash completed with no output)
```

Non-zero exit:

```text
Exit code 7
problem
```

Non-zero exit with no output:

```text
Exit code 7
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

Full Claude harness follow-up behavior:

- Claude also exposes `TaskStop` and `TaskOutput` outside the narrower standard-tool slice.
- For bash tasks, the `TaskOutput` schema text explicitly recommends using `Read` on the returned output file path.
- When prompted to prefer a dedicated task-management stop tool, Claude stops a running background Bash task with `TaskStop(task_id=<BACKGROUND_ID>)`.

## Implementation Direction

- Implement `Bash` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Reuse the shared shell engine for foreground execution.
- Match the observed output policy:
  - success: raw output only
  - success with no output: `(Bash completed with no output)` placeholder
  - non-zero exit: `Exit code N` prefix plus output
  - non-zero exit with no output: `Exit code N` with no body
  - timeout: report `Exit code 143`
- Persist the working directory between commands the way the upstream Claude
  Code Bash tool description says it does ("The working directory persists
  between commands"). The ending cwd of each foreground command is stored in
  the tool-result message's `metadata.bash.end_cwd`, formatted as a path
  relative to the configured `working_directory` when inside the tree
  (portable across sandbox moves) and absolute when outside. The next Bash
  command reads the most recent `end_cwd` from the session messages and
  resolves it against the configured `working_directory`. Background commands
  do not update the cwd chain.
- Support `run_in_background` with the observed `background ID + output file path` success message.
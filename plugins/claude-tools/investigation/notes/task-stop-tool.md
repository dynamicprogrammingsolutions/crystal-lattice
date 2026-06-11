# TaskStop Tool Investigation Notes

Status: focused schema and stop behavior captured from the full Claude Code harness.

Investigation script:

- `plugins/claude-tools/investigation/scripts/investigate_task_stop_tool.py`

## Fixtures

- `plugins/claude-tools/investigation/fixtures/task-stop/success-stop-background-task.json`
- `plugins/claude-tools/investigation/fixtures/task-stop/error-task-not-found.json`
- `plugins/claude-tools/investigation/fixtures/task-stop/error-invalid-parameters.json`

## Tool Name

Claude Code exposes a dedicated task-management stop tool as:

```text
TaskStop
```

## Schema

Observed schema:

- `name`: `TaskStop`
- `type`: `object`
- `additionalProperties`: `false`
- properties:
  - `task_id: string`
  - `shell_id: string` with description `Deprecated: use task_id instead`

## Behavior

Successful stop result:

```json
{"message":"Successfully stopped task: <BACKGROUND_ID> (while true; do sleep 60; done)","task_id":"<BACKGROUND_ID>","task_type":"local_bash","command":"while true; do sleep 60; done"}
```

Unknown task result:

```text
<tool_use_error>No task found with ID: does-not-exist</tool_use_error>
```

Invalid extra parameters result:

```text
<tool_use_error>InputValidationError: TaskStop failed due to the following issues:
An unexpected parameter `block` was provided
An unexpected parameter `timeout` was provided</tool_use_error>
```

## Tool Relationship

- Claude starts background shell tasks with `Bash` and `run_in_background: true`.
- Claude can stop those tasks with `TaskStop` using the background ID returned by `Bash`.
- Claude also exposes `TaskOutput`, but its schema text explicitly says `Read` is the preferred way to inspect bash-task output via the output path returned by `Bash`.
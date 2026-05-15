# Claude Code System Message Investigation Notes

Fixtures:

- `plugins/claude-tools/investigation/fixtures/system-message/no-tools.json`
- `plugins/claude-tools/investigation/fixtures/system-message/read-tool.json`
- `plugins/claude-tools/investigation/fixtures/system-message/read-relative-path.json`
- `plugins/claude-tools/investigation/fixtures/system-message/standard-tools.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/system-message/`.

## Invocation

The deterministic harness uses Claude Code `2.1.126`, Ollama's Anthropic-compatible API, and `../openai-proxy`:

```bash
python plugins/claude-tools/investigation/scripts/investigate_system_message.py --case all
```

The script prepares a temporary workspace, starts the proxy, runs Claude Code with explicit `--setting-sources project` settings, captures stdout/stderr/debug/proxy logs, and writes normalized fixtures.

## Request Shape

The main Claude Code request uses Anthropic Messages `system` as a list of text blocks:

- block 0: billing/version header
- block 1: short Claude Agent SDK identity line
- block 2: the main Claude Code behavioral prompt

Claude Code sends the current date separately as a `<system-reminder>` text block in the first user message, not in the main `system` list.

The main prompt headings observed in all cases:

- `# System`
- `# Doing tasks`
- `# Executing actions with care`
- `# Using your tools`
- `# Tone and style`
- `# Text output (does not apply to tool calls)`
- `# auto memory`
- `# Environment`
- `# Context management`

## Working Directory Behavior

The `# Environment` section includes a primary working directory line:

```text
- Primary working directory: <WORKSPACE>
```

It also includes git-repository status, platform, shell, OS version, current model, and Claude model-family information.

The prompt does not contain a separate general instruction saying to convert relative file paths into absolute file paths. Instead, path behavior comes from the combination of:

- the primary working directory in the environment section
- tool schema descriptions that require absolute paths for specific tools
- the general instruction to interpret software-engineering requests in the current working directory

The `read-relative-path` case prompted Claude Code to read `README.md`. Claude called `Read` with:

```json
{
  "file_path": "<WORKSPACE>/README.md"
}
```

So Claude Code's observed behavior is to resolve a user-provided relative path against the primary working directory before calling `Read`.

## Tool Path Guidance

Observed path-related tool guidance in the `standard-tools` case:

- `Read`: `file_path` must be an absolute path, not relative.
- `Write`: `file_path` must be absolute, not relative.
- `Edit`: `file_path` is the absolute path to modify.
- `Glob`: optional `path` defaults to the current working directory when omitted.
- `Grep`: optional `path` defaults to the current working directory.
- `Bash`: preserve the working directory where possible; use absolute paths and avoid unnecessary `cd`.

The system-message implementation should not rely on every model inferring the relative-path conversion from schema text alone. Our Claude-compatible system message should include a small explicit environment/path section:

```text
# Environment
You have been invoked in the following environment:
 - Primary working directory: {{CURRENT_WORKING_DIRECTORY}}
 - Platform: {{PLATFORM}}
 - Shell: {{SHELL}}

# Working with paths
When a file tool requires an absolute path and the user gives a relative path, resolve it against the primary working directory before calling the tool.
```

The exact file split can change, but the runtime-rendered primary working directory is the important missing piece for `Read`.

## Implementation Direction

For task `030`, replace the minimal `CLAUDE_CODE_DEFAULT.md` mixin with structured Claude system-message files and add a runtime variable/helper that renders the current working directory.

Recommended first implementation slice:

- add `system_messages/claude/template.md`
- add `system_messages/claude/introduction.md`
- add `system_messages/claude/tone-and-style.md`
- add `system_messages/claude/workflow.md`
- add `system_messages/claude/tool-usage.md`
- add `system_messages/claude/environment.md`
- update `claude_system_message` to include `{{CLAUDE_ENVIRONMENT}}`

The environment section should be dynamic. It should use the process current working directory that the application/tool execution uses as the workspace root.

Keep `TASKS` and `AGENTS_SECTION` after the Claude sections, as the existing mixin already does.
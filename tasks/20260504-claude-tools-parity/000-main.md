# Claude Tools Parity

Create Claude Code-compatible system message, standard tools, and compaction support by investigating Claude Code behavior through an Anthropic-compatible proxy and implementing matching plugins/config in this repository.

## Task checklist

- [x] `tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md` - completed for the standard-tool scope: repeatable harnesses and normalized fixtures now exist for `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`, `WebFetch`, `WebSearch`, plus system-message coverage.
- [ ] `tasks/20260504-claude-tools-parity/020-implement-claude-tools.md` - partial: all standard Claude tools plus `TaskStop` are implemented; remaining follow-up is shared interop/formatting cleanup and broader validation/docs work.
- [x] `tasks/20260504-claude-tools-parity/030-implement-claude-system-message-and-config.md` - completed for the current Claude `Read` slice: the primary `claude` default-config agent now uses `claude-tools`, the structured Claude system message is wired in, and focused rendering/config tests pass.
- [x] `tasks/20260504-claude-tools-parity/040-investigate-and-implement-claude-compaction.md` - completed: deterministic compaction investigation fixtures were normalized by script, a Claude-specific compaction feature was added inside `plugins/claude-tools`, and focused fixture-driven/unit/application tests now cover the action path.
- [ ] `tasks/20260504-claude-tools-parity/050-validation-and-docs.md`
- [ ] `tasks/20260504-claude-tools-parity/060-fix-claude-compaction-transcript-snapshot.md` - SPLIT FROM `040`: the transcript path reference in the compaction summary footer is broken because the live session file is overwritten on compaction. This subtask saves a pre-compaction transcript snapshot in Claude Code's JSONL format so the reference points to a valid file.

## Background

We previously investigated Codex, Gemini CLI, Kimi CLI, Qwen CLI, and Grok CLI repositories/behavior in order to build compatible local tools. Claude Code is not open source, so the Claude work must be behavior-driven: run real Claude Code through an intercepting proxy, capture Anthropic API request bodies, and reproduce the observed tool schemas, result formatting, and system-message behavior.

The relevant existing vendor packages are:

- `plugins/gemini-tools`
- `plugins/qwen-tools`
- `plugins/kimi-tools`
- `plugins/grok-tools`
- `plugins/codex-tools`
- `plugins/gemini-compaction-app`
- `plugins/gemini-compaction-feature`
- `plugins/tool-compat-shared`
- `plugins/web-fetch-shared`

The default config and system-message construction live under:

- `application/python/agent_terminal_app/default_config/config.json`
- `application/python/agent_terminal_app/default_config/CLAUDE_CODE_DEFAULT.md`
- `application/python/agent_terminal_app/default_config/system_messages/*`
- `application/python/agent_terminal_app/system_messages/*`

The existing `claude` agent in `application/python/agent_terminal_app/default_config/config.json` currently uses `codex-tools`, not a Claude-compatible tool bundle.

## Known Claude Code Setup

Claude Code was found at:

```text
/Users/ferenci84/.local/bin/claude
```

It was updated during investigation:

```text
2.1.59 -> 2.1.126
```

Claude Code can be run with Ollama using Ollama's Anthropic-compatible endpoint:

```bash
ANTHROPIC_AUTH_TOKEN=ollama
ANTHROPIC_API_KEY=ollama
ANTHROPIC_BASE_URL=http://localhost:11434
claude --model qwen3-coder-next:cloud
```

The existing proxy at `../openai-proxy` can intercept Claude Code's Anthropic traffic without editing the proxy by using this route trick:

```bash
cd ../openai-proxy
node proxy.js http://localhost:11434/v1 9018
```

Then run Claude Code with:

```bash
ANTHROPIC_BASE_URL=http://localhost:9018/api
```

Claude sends `/v1/messages`; setting the base URL to `/api` causes the proxy to see `/api/v1/messages`, which it supports, and forward to Ollama's `/v1/messages`.

Important harness details:

- Use `--setting-sources project` plus explicit `--settings` so `~/.claude/settings.json` cannot override the test environment.
- Use `--tools <ToolName>` to restrict the tool schemas sent to the model.
- `--allowedTools <ToolName>` affects permissions but still advertises the full built-in tool list.
- `--output-format stream-json` requires `--verbose` in Claude Code `2.1.126`.
- Pin `ANTHROPIC_SMALL_FAST_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL` to an Ollama model. Claude Code otherwise sends title-generation requests using a default Haiku model that Ollama does not have.
- Claude Code may make first-party telemetry/bootstrap calls with the fake key and log 401s. The core Anthropic API calls can still succeed through Ollama/proxy.

Known good command shape:

```bash
cd /Users/ferenci84/Dev/Mine/ai-agent-platform

ANTHROPIC_BASE_URL=http://localhost:9018/api \
ANTHROPIC_API_KEY=ollama \
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_SMALL_FAST_MODEL=qwen3-coder-next:cloud \
ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3-coder-next:cloud \
claude -p \
  --verbose \
  --setting-sources project \
  --settings '{"env":{"ANTHROPIC_BASE_URL":"http://localhost:9018/api","ANTHROPIC_API_KEY":"ollama","ANTHROPIC_AUTH_TOKEN":"ollama","ANTHROPIC_SMALL_FAST_MODEL":"qwen3-coder-next:cloud","ANTHROPIC_DEFAULT_HAIKU_MODEL":"qwen3-coder-next:cloud"}}' \
  --no-session-persistence \
  --model qwen3-coder-next:cloud \
  --tools Read \
  --permission-mode bypassPermissions \
  --output-format stream-json \
  'Use the Read tool to read README.md. Then answer with exactly the first Markdown heading from that file and nothing else.'
```

This successfully produced a `Read` tool call and returned:

```text
# Crystal Lattice / AI Agent Platform
```

Captured files from the manual investigation:

```text
/tmp/claude-proxy-read-tools-output.jsonl
/tmp/claude-proxy-read-tools-debug.log
/tmp/claude-ollama-proxy-read-tools-test.log
```

## Claude Tool Surface

Claude Code reported these relevant standard built-in tools:

- `Bash`
- `Glob`
- `Grep`
- `Read`
- `Edit`
- `Write`
- `WebFetch`
- `WebSearch`

It also reported broader nonstandard tools such as `Agent`, `AskUserQuestion`, `CronCreate`, `CronDelete`, `CronList`, `EnterPlanMode`, `EnterWorktree`, `ExitPlanMode`, `ExitWorktree`, `Monitor`, `NotebookEdit`, `PushNotification`, `RemoteTrigger`, `ScheduleWakeup`, `Skill`, `TaskOutput`, `TaskStop`, `TodoWrite`, and `ToolSearch`. These are outside the first standard-tool parity scope unless explicitly added later.

## Confirmed `Read` Behavior

Observed schema:

```json
{
  "name": "Read",
  "description": "...long description...",
  "input_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
      "file_path": {
        "description": "The absolute path to the file to read",
        "type": "string"
      },
      "offset": {
        "description": "The line number to start reading from. Only provide if the file is too large to read at once",
        "type": "integer",
        "minimum": 0,
        "maximum": 9007199254740991
      },
      "limit": {
        "description": "The number of lines to read. Only provide if the file is too large to read at once.",
        "type": "integer",
        "exclusiveMinimum": 0,
        "maximum": 9007199254740991
      },
      "pages": {
        "description": "Page range for PDF files (e.g., \"1-5\", \"3\", \"10-20\"). Only applicable to PDF files. Maximum 20 pages per request.",
        "type": "string"
      }
    },
    "required": ["file_path"],
    "additionalProperties": false
  }
}
```

Observed tool-call history payload:

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "call_sdlwwpsp",
      "name": "Read",
      "input": {
        "file_path": "/Users/ferenci84/Dev/Mine/ai-agent-platform/README.md"
      }
    }
  ]
}
```

Observed successful tool result sent back to the model:

```json
{
  "role": "user",
  "content": [
    {
      "tool_use_id": "call_sdlwwpsp",
      "type": "tool_result",
      "content": "1\t# Crystal Lattice / AI Agent Platform\n2\t\n3\tCrystal Lattice is ...",
      "cache_control": {
        "type": "ephemeral"
      }
    }
  ]
}
```

Notes:

- `Read` result content is a single plain string.
- Lines are numbered as `lineNumber<TAB>content`.
- Successful tool results did not include `is_error` on the Anthropic API wire payload.
- `cache_control: {"type": "ephemeral"}` is attached to the tool result.
- Claude Code's local `--output-format stream-json` output includes richer local metadata under `tool_use_result`, but that metadata was not sent to the model.

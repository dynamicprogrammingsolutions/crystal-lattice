# Terminal guide

The Crystal Lattice terminal provides an interactive prompt over the same
sessions, requests, events, and configuration used by the HTTP application.

Start it with:

```bash
crystal-lattice --console
```

Run the terminal and HTTP server together with:

```bash
crystal-lattice --console --server
```

## Startup guidance and help

The maintained default configuration prints a concise quick-help summary when
the terminal starts. Configure `application.terminal_startup_help` as:

- `summary`: show the quick-help summary;
- `hint`: show one line pointing to `/help`;
- `off`: show only `Session started.`.

Use `/help` for the complete registered slash-command and keyboard-shortcut
catalog. The catalog is generated from the command registry, so plugin and
terminal command descriptions remain aligned with completion.

Use `/help config` to inspect application-level terminal settings and
plugin-contributed session settings. It shows schema defaults and current
application values; it does not imply that runtime-only command state is
persisted.

## Important commands

| Command | Purpose |
|---|---|
| `/help` | List registered commands and shortcuts |
| `/help config` | Show configurable session and application settings |
| `/new` | Start a new session |
| `/session` | List or select a session |
| `/agent` | Select the active agent |
| `/send` | Send a request using the current history |
| `/append` | Append a message without starting a request |
| `/cancel` | Cancel the active request |
| `/list` | Print message history or one message in full |
| `/modify` | Load a message into the prompt for editing |
| `/delete` | Delete a message or range |
| `/fork` | Fork the session at a message index |
| `/plugins` | Inspect or change per-session plugin enablement |
| `/set` | Set a session configuration override |
| `/tool-output` | Show or select live tool-output presentation |
| `/exit`, `/quit` | Exit the terminal |

Argument completion is available for commands that expose known modes,
sessions, agents, plugins, or configuration choices.

## Requests and progress

Typing ordinary text starts a request. `/append` is the explicit way to add
text without requesting a model response.

The bottom toolbar shows the most specific active phase:

```text
Running: request
Running: LLM
Running: tool read_file
```

The request phase is the fallback between model and tool phases. Progress is
static rather than animated, and prompt redraw does not add progress frames to
scrollback. Permanent assistant and tool output continues to appear above the
prompt.

If terminal rewriting is unavailable, ordinary lifecycle lines and permanent
output remain readable. Headless `--no-tty` mode runs the prompt path with
dummy terminal output and does not provide a human-visible toolbar.

Use `/cancel` or `Ctrl-X C` to cancel the active request. Completion,
cancellation, errors, session changes, and shutdown clear transient progress
and tool-rendering state.

## Tool-output modes

Show the current mode:

```text
/tool-output
```

Select compact results:

```text
/tool-output one-line
```

Select full streaming output:

```text
/tool-output full
```

Full mode is the default. It streams tool content and prints the final
metadata footer.

One-line mode suppresses permanent streamed tool chunks while a call is
running; the toolbar still reports the active tool. When the call completes,
the terminal prints a compact two-line block:

```text
[7] Tool: read_file
    Read: README.md
```

The first line contains the stored message index and technical tool name. The
second line uses the tool-provided `display.single_line` preview when
available. Otherwise the terminal selects display-aware result content,
collapses whitespace, and applies the configured short character limit.

Use the displayed index to print the complete stored result:

```text
/list 7
```

Changing `/tool-output` affects the current terminal process. It does not
rewrite the application configuration or persist a per-session override.

## Listing and editing messages

Useful forms include:

```text
/list
/list 7
/list 3:8
/list short
/modify 7
/delete 7
/fork 7
```

`/list <index>` prints one message in full, including tool footer metadata.
`/list short` uses compact history presentation independently of the live
tool-output mode.

## Sessions, filters, and plugins

Session selection supports exact ids, search text, and command-local filter
overrides:

```text
/session
/session <session-id>
/session project search
/session --filter pinned_state=true
/session --filter session_status=todo,blocked
/session --filter pinned_state=any --filter session_status=any
```

`any` deactivates Boolean/select filters for that command. Multiple select
values use comma-separated values.

Plugin controls are stored in the session:

```text
/plugins
/plugins on <id-or-index>
/plugins off <id-or-index>
/plugins reset
```

## Application reload and provider keys

The built-in application-configuration plugin can request a full
`AgentApplication` replacement while the CLI process, HTTP listener, bridge,
and Bonjour integration remain alive. The runtime stops admitting new
application work, lets admitted requests and started tools finish, constructs
the replacement from current configuration and environment files, swaps it
in, closes the previous runtime, and resumes admission.

Application notifications report whether the reload was requested, completed,
or failed. New requests receive an application-reload-pending response while
the runtime drains.

Provider-key editing is configured under
`application.application_config`:

```json
{
  "env_file": "${env:CONFIG_DIR}/.env",
  "editable_env_keys": ["OPENROUTER_API_KEY"],
  "provider_env_keys": {
    "openrouter": "OPENROUTER_API_KEY"
  }
}
```

Only keys listed in `editable_env_keys` and mapped through
`provider_env_keys` can be changed. A key supplied directly by the process
environment is externally managed and is not overwritten through dotenv
editing.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl-N` | Start a new session |
| `Ctrl-Q` | Exit |
| `Ctrl-X S` | Send |
| `Ctrl-X A` | Append without sending |
| `Ctrl-X C` | Cancel the active request |
| `Ctrl-J` | Insert a newline |
| `Alt-Enter` | Insert a newline |

## Terminal configuration

These keys belong under the top-level `application` object:

| Key | Bundled default | Meaning |
|---|---:|---|
| `tool_output_line_limit` | `20` | Maximum displayed lines per full tool call; values at or below zero disable this limit |
| `tool_output_char_limit` | `2000` | Maximum displayed characters per full tool call; values at or below zero disable this limit |
| `tool_output_short_char_limit` | `200` when omitted | Maximum characters in a compact tool preview |
| `tool_output_short_one_line` | `true` | Collapse short/history tool content to one physical result line |
| `tool_output_short_line_limit` | `20` when omitted | Short-view line limit when one-line short output is disabled |
| `tool_output_live_one_line` | `false` | Initial `/tool-output` mode: `true` selects `one-line`, `false` selects `full` |
| `terminal_startup_help` | `"summary"` | Startup guidance: `summary`, `hint`, or `off` |

For line and character limits, a positive value enables that individual
limit. Setting both corresponding limits to zero or below leaves the content
unlimited.

Example:

```json
{
  "application": {
    "tool_output_line_limit": 20,
    "tool_output_char_limit": 2000,
    "tool_output_short_char_limit": 200,
    "tool_output_short_one_line": true,
    "tool_output_short_line_limit": 20,
    "tool_output_live_one_line": false,
    "terminal_startup_help": "summary"
  }
}
```

## Non-interactive console mode

For CI, subprocess tests, or a container without a TTY:

```bash
crystal-lattice --console --no-tty
```

This runs the console/session/event-polling path with `prompt_toolkit` pipe
input and dummy output. SIGTERM sends EOF and shuts the prompt down cleanly.
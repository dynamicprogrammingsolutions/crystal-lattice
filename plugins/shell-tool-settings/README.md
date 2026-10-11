# shell-tool-settings

Opt-in settings plugin that exposes the agent/session config key
`shell_tool_mode` in the session settings UI.

The plugin contributes a single `select` setting (`shell_tool_mode`, default
`auto`) and has no behavior of its own: the shell tools in `codex-tools`
consume the key from the merged agent/session configuration. It is **not**
referenced by the default configuration — load it explicitly when you want
the setting.

## What the setting does

| Value | Shell tool surface |
|-------|--------------------|
| `auto` (default) | `exec_command` + `write_stdin` (unified exec) — for every model, matching current upstream Codex |
| `exec_command` | `exec_command` + `write_stdin` (explicit) |
| `shell_command` | Legacy string-command tool (removed upstream 2026-08-20; kept as an opt-in escape hatch) |
| `shell` | Legacy array tool (removed upstream 2026-05-13; kept as an opt-in escape hatch) |

## Usage

Enable per agent by loading the plugin and setting the key in the agent
definition:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/codex-tools",
    "path:${env:BUILTIN_PLUGINS}/shell-tool-settings"
  ],
  "agents": {
    "my-agent": {
      "provider": "openai",
      "model": "gpt-6.1-sol",
      "shell_tool_mode": "shell_command"
    }
  }
}
```

Or set it per session in the session settings (terminal `/set
shell_tool_mode shell_command`, or the chips in the mobile/desktop session
settings). The value is stored as a session override and takes effect on
the next request in that session — no restart. Resetting the override
returns the session to the agent default.

## Tests

```bash
pytest plugins/shell-tool-settings/tests -q
```

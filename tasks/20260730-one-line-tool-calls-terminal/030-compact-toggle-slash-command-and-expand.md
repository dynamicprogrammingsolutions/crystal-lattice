# `/compact` Slash Command Toggle + Expand-By-Index Flow

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/020-compact-live-tool-rendering.md

Add the user-facing toggle in
`application/python/agent_terminal_app/terminal.py` and wire it to the
renderer's compact-mode supplier. Expansion by index is served by the
EXISTING `/list <index>` command — no new full-render code.

## Requirements checklist

- [x] New slash command `/compact` registered via the `@slash_command`
      decorator (pattern: `terminal.py` ~lines 68-107; examples `_cmd_list`
      ~line 1580, `_cmd_set` ~line 1156):
  - [x] `/compact` with no args toggles the mode and prints the new state,
        including a hint like
        `[compact] on - tool calls render as one line; use /list <index> to expand`.
  - [x] `/compact on|off` sets it explicitly; any other arg prints usage.
  - [x] Argument completion for `on`/`off` via the `completer=` hook
        (mirror `_plugins_completion` ~line 475).
- [x] Mode is stored in `ui_state` (created in `_run_terminal` ~lines
      1968-1983), e.g. `ui_state["compact_tool_calls"] = bool`. The
      `TerminalRenderContext` construction there passes
      `compact_supplier=lambda: bool(ui_state.get("compact_tool_calls"))`.
- [x] Initial value comes from a new application-config key
      `tool_output_live_compact` (bool, default `False`), added to
      `get_application_config_schema()` in `terminal_app.py` (~line 1046)
      with the other `tool_output_*` keys so it shows up in `/help config`.
- [x] `/help` lists the new command automatically (it iterates registered
      commands); verify the description reads well.
- [x] Expansion: confirm `/list <index>` prints the full tool message for an
      index shown in a compact line (it already routes a single integer to a
      one-element slice with `short=False` — `_cmd_list` ~lines 1614-1623,
      `render_message` full branch). No code change expected; cover with a
      test and mention in the `/compact` on-message hint.

## Notes

- Keep the handler thin (UI-only) per
  `application/python/agent_terminal_app/AGENTS.md`; the only state is a
  boolean in `ui_state`, and the config default read can go through
  `app.agent_app.get_application_config()` like `ToolRenderer.__init__`
  does (~line 557).
- Session-scoped persistence (`/set`-style overrides) is intentionally NOT
  part of this ticket; the config key provides the startup default and the
  command provides the runtime toggle.
- `_cmd_list`'s defensive `TerminalRenderContext` construction (~line 1634)
  must also pass a supplier (reading the same `ui_state` key when available)
  so list-triggered renderer rebuilds don't lose the toggle.

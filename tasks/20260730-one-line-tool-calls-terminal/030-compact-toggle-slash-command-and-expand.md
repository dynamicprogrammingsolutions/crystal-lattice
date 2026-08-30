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

## Post-completion follow-up

### Follow-up requirements checklist

- [x] `/compact` is not registered for tool-output presentation and remains
      available for future context compaction behavior.
- [x] An approved explicit command reports and selects the live tool-output
      mode with discoverable argument completion and clear usage errors.
- [x] The command distinguishes `one-line` and `full` modes rather than using
      ambiguous bare `on`/`off` language.
- [x] The selected mode is represented consistently in UI state, application
      configuration schema/defaults, help output, tests, and user
      documentation.
- [x] `/list <index>` remains the expansion command and is included in the
      one-line-mode confirmation.

## Execution plan
Status: Approved

Replace the tool-output use of `/compact` before the feature is published.
The recommended interface is:

```text
/tool-output
/tool-output one-line
/tool-output full
```

With no argument, report the current mode without changing it. Explicit mode
arguments avoid accidental toggles and make shell transcripts and support
instructions self-explanatory. Provide completion for `one-line` and `full`.
Do not retain `/compact` as an alias because the purpose of the change is to
reserve that command name for context compaction.

Rename internal command helpers and UI-state keys away from generic “compact”
terminology. Decide whether to rename the unreleased config key from
`tool_output_live_compact` to `tool_output_live_one_line`; if renamed, update
the maintained default config and schema together and do not add a legacy
alias unless compatibility is explicitly required.

### Implementation decisions and open questions

- Recommended slash command: `/tool-output one-line|full`.
- Alternatives if the command is considered too long:
  `/tool-view one-line|full` or `/tool-calls one-line|full`.
- Recommended no-argument behavior: report state, not toggle.
- Recommended config key: `tool_output_live_one_line` because the key is not
  yet released and “compact” should remain associated with context
  compaction. User approval is required before choosing the final command and
  config-key names.

### Documentation

- Subtask 060 owns user documentation and startup/help presentation.
- Update command descriptions and configuration schema text in the same
  implementation commit so `/help` and `/help config` never advertise stale
  names.

### Task checklist

- [x] Confirm command and config-key names.
- [x] Replace command registration, handler, completion, messages, UI-state
      naming, and tests.
- [x] Remove `/compact` from the tool-output registry without an alias.
- [x] Verify state reporting, explicit mode selection, bad-argument handling,
      completion, `/help`, and expansion hint.
- [x] Coordinate generated/default configuration updates with subtask 060.

### Requirement verification

- Command-registry inspection proves `/compact` is absent and the approved
  command is present exactly once.
- Direct command tests prove no-argument reporting does not mutate state and
  explicit modes do.
- Completion and help tests expose the approved vocabulary.
- A stored compact result still expands through `/list <index>`.

### Additional implementation verification

- Run the complete terminal command/application tests after renaming symbols
  to catch stale imports and test references.

### Follow-up completion notes

- `/tool-output` with no argument reports state without mutation.
- `/tool-output one-line|full` selects the runtime mode and completion offers
  both values.
- `/compact` has no command registration or alias.
- Runtime state is `tool_output_one_line`; the maintained startup key is
  `tool_output_live_one_line`.
- Registry/help/config tests prove the approved names appear once and stale
  tool-output uses of `/compact` are absent.

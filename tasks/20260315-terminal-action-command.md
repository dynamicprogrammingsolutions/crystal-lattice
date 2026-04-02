# Terminal `/action` Command

Short description: Add a `/action` slash command to the terminal app for invoking application-level plugin actions.

## Goal

Provide a CLI interface for invoking application plugin actions, similar to how the mobile/desktop frontends expose session actions and message actions via their UI.

## Background

Application plugins expose actions via `get_ui_elements()` (e.g., `GeminiCompactionAppPlugin` exposes `compact_range`, `compact_up_to_here`, `compact_full`). The mobile and desktop frontends render these as buttons/menu items, but the terminal app currently has no way to invoke them.

## Scope

### In Scope

1. `/action` command with tab completion for available actions
2. Support for `session_action` and `message_action` UI types
3. Parameter prompting (dialog-like interaction)
4. Integration with `TerminalApplication.execute_application_action()`

### Out of Scope

1. `composer_attachment` UI type (requires different UX)
2. `message_footer` / `status_bar` UI types (display-only)

## Proposed Design

### Command Syntax

```
/action <action_id> [param1=value1] [param2=value2]
```

Examples:
```
/action compact_range start=0 end=5
/action compact_full
/action compact_up_to_here end=3
```

### Interactive Mode

If required parameters are missing, prompt the user:

```
> /action compact_range
Required parameters:
  start (integer): _
  end (integer): _
Optional parameters:
  prompt (multiline): [press Enter to skip]
```

### Tab Completion

- Complete action IDs from available session actions
- Complete parameter names from action definition

## Implementation

1. Add `_cmd_action` function in `terminal.py`
2. Register with `@slash_command("action", "Invoke application plugin action")`
3. Use `app.session_application_ui_elements()` to get available actions
4. Call `app.execute_application_action()` with provided/prompted params

## Acceptance Criteria

1. `/action` lists available session actions for current session
2. `/action <id>` invokes the action with optional parameters
3. Tab completion works for action IDs and parameter names
4. Error messages are clear when action is disabled or not found
5. Compaction actions work from terminal for enabled agents

## Related

- Task 223: `tasks/20260315-gemini-qwen-grok-tool-packages/223-session-aware-application-plugin-ui.md`
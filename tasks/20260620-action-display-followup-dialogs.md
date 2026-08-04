# Action Display Follow-Up Dialogs

Allow returned action display follow-up actions to open the same kind of form dialog that session action UI elements already support. This is a future generic feature for workflows where a display action should launch a separate modal/popover form rather than embedding fields directly in the display.

## Requirements checklist

- [ ] Extend display follow-up `run_action` entries to accept `dialog`, `param_map`, and related action UI element fields.
- [ ] Reuse the existing action dialog form schema and rendering path.
- [ ] Implement the behavior on the React Native mobile app.
- [ ] Implement the behavior on the React Native macOS desktop app.
- [ ] Add SDK-level unit and integration coverage.
- [ ] Add React Native component/integration coverage for mobile.
- [ ] Add React Native component/integration coverage for desktop when relevant to the desktop test setup.
- [ ] Document the follow-up dialog protocol and examples in plugin/action documentation.
- [ ] Keep existing display follow-up actions backward compatible.

## Context

Normal session action UI elements already support a dialog form:

```json
{
  "ui_type": "session_action",
  "plugin": "example",
  "id": "edit_value",
  "label": "Edit value",
  "action_id": "save_value",
  "fixed_params": {
    "source": "session_view"
  },
  "param_map": {
    "value": "$dialog.value"
  },
  "dialog": {
    "kind": "form",
    "inputs": [
      {
        "name": "value",
        "type": "string",
        "required": true
      }
    ]
  }
}
```

Current display follow-up `run_action` entries do not support this full shape. Mobile and desktop synthesize a minimal action element from display actions and execute it immediately.

This task is separate from `tasks/20260620-action-display-embedded-forms.md`. Embedded forms show fields directly in the display. Follow-up dialogs open a separate form when the user presses a display action button.

## Proposed Protocol Shape

Allow `display.actions[]` entries of `kind: "run_action"` to include the same dialog and mapping fields used by action UI elements:

```json
{
  "kind": "run_action",
  "id": "finish-mcp-login",
  "label": "Paste callback URL",
  "plugin": "mcp_runtime_app",
  "action_id": "mcp_finish_login_from_callback_url",
  "fixed_params": {
    "server_name": "figma"
  },
  "param_map": {
    "redirect_url": "$dialog.redirect_url"
  },
  "dialog": {
    "kind": "form",
    "title": "Finish MCP login",
    "message": "Paste the full callback URL from Safari.",
    "inputs": [
      {
        "name": "redirect_url",
        "type": "multiline",
        "label": "Callback URL",
        "required": true
      }
    ]
  },
  "preserve_display": true
}
```

The mapping source remains `$dialog.<field>` because the values come from the separate action dialog, not from embedded display fields.

## Implementation Notes

- Update `packages/frontend-sdk/src/types/plugins.ts`:
  - add `dialog?: any` to `ActionDisplayRunActionAction`
  - add `param_map?: Record<string, string>` if not already added by the embedded forms task
  - consider sharing a small base interface with `ActionUiElement` fields if it stays readable
- Update mobile follow-up handlers:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
  - When a display follow-up action has a dialog, synthesize an action UI element with `dialog`, `fixed_params`, `param_map`, and open it with `openPluginDialogForElement`.
  - When no dialog is present, preserve immediate execution.
- Update desktop follow-up handlers:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx`
  - Use the existing `useMacOSApplicationActionDialog` / action dialog path for follow-up dialogs.
- Preserve `preserve_display` semantics: if true, keep the originating display visible while the dialog is open and after action completion unless the returned result replaces it.

## SDK Testing Requirements

Add or update tests under `packages/frontend-sdk/src/plugins/__tests__/`:

- A synthesized follow-up action element with `dialog` maps `$dialog.<field>` into backend inputs.
- Existing follow-up actions without `dialog` still execute immediately.
- Existing session action UI element dialog behavior remains unchanged.

Add or update SDK integration tests under `packages/frontend-sdk/src/integration/__tests__/`:

- Use a deterministic dummy application plugin that returns a display with a follow-up `run_action` containing a dialog.
- Execute the first action through the SDK and inspect the returned display action.
- Simulate the dialog submission path by passing dialog values through the same action runner path.
- Assert the backend receives the mapped value and returns the expected result/display.

## React Native Testing Requirements

Mobile:

- Add component/integration coverage in `mobile/crystal-lattice-control-rn/__tests__/`.
- Render a display with a follow-up `run_action` containing a dialog.
- Press the follow-up action.
- Assert the action dialog appears with the server-provided field.
- Enter text and submit.
- Assert the backend/action handler receives the mapped input.

Desktop:

- Add coverage in the desktop RN test location if present; otherwise document the current desktop RN test limitation and add the closest available unit/component coverage for the desktop follow-up handler.
- Verify that pressing a display follow-up action opens the desktop action dialog/popover/window with the server-provided fields.
- Verify submitted dialog values map into backend action inputs.

## Documentation Requirements

Update `plugins/docs/actions.md`:

- Document that display follow-up `run_action` entries may include a `dialog`.
- State that this dialog reuses the action UI element dialog schema.
- Document that `$dialog.<field>` mappings refer to values from the opened follow-up dialog.
- Include an example follow-up action that opens a dialog.
- Cross-reference embedded display forms from `tasks/20260620-action-display-embedded-forms.md` as the alternative when fields should be visible directly in the display.

Update frontend SDK integration README if relevant:

- Add the command/name for the follow-up dialog integration test.

## Acceptance Criteria

- A plugin can return a display action that opens a separate form dialog.
- Mobile and desktop both open the dialog using their existing action dialog UX.
- Submitted dialog values map into follow-up action inputs through `$dialog.<field>`.
- Display actions without dialogs are unchanged.
- Existing session action dialogs are unchanged.
- SDK and React Native tests cover the behavior.

## Proposed Future Work Note

This task is intentionally postponed until there is a workflow that needs a separate dialog. For the MCP OAuth mobile workaround, prefer the embedded display form from `tasks/20260620-action-display-embedded-forms.md` first.
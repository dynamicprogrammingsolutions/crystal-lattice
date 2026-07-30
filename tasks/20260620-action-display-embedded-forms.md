# Action Display Embedded Forms

Add generic form fields directly inside action display payloads so plugins can return user-facing text, server-decided form inputs, and follow-up actions in a single display surface. This should work on mobile and desktop and should be reusable beyond MCP login.

## Requirements checklist

- [x] Extend the generic action display protocol with embedded form support.
- [x] Reuse the existing action-dialog form input schema for display forms.
- [x] Support mapping submitted display form values into follow-up action inputs.
- [x] Implement display form rendering on the React Native mobile app.
- [x] Implement display form rendering on the React Native macOS desktop app.
- [x] Add a dummy plugin that returns embedded display forms so the feature can be tested manually before MCP depends on it.
- [x] Add SDK-level unit and integration coverage for display form input mapping and action execution.
- [x] Add React Native component/integration coverage for display forms on mobile.
- [x] Add React Native component/integration coverage for display forms on desktop when relevant to the desktop test setup.
- [ ] Before implementing MCP runtime usage, manually verify the Figma OAuth flow is compatible with the pasted-callback flow and can call tools after login.
- [x] Document the display form schema and examples in the plugin/action documentation.
- [x] Keep existing action display behavior backward compatible.

## Context

Current generic action results can return a `display` payload containing markdown/plain text and follow-up actions. The current shape is documented in `plugins/docs/actions.md` under "Generic display payloads":

```json
{
  "display": {
    "format": "markdown",
    "title": "ChatGPT Login",
    "body": "Open [this link](https://example.test).",
    "variant": "info",
    "presentation": "inline",
    "actions": [
      {
        "kind": "open_url",
        "id": "open-login-link",
        "label": "Open link",
        "url": "https://example.test"
      }
    ]
  }
}
```

Current display renderers:

- Mobile modal display: `mobile/crystal-lattice-control-rn/src/components/ActionResultModal.tsx`
- Mobile inline display: `mobile/crystal-lattice-control-rn/src/components/ActionResultInlineCard.tsx`
- Mobile card renderer: `mobile/crystal-lattice-control-rn/src/components/ActionDisplayCard.tsx`
- Desktop modal display: `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionResultModal.tsx`
- Desktop inline display: `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionResultInlineCard.tsx`
- Desktop card renderer: `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionDisplayCard.tsx`

Current action dialog form support already exists in:

- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`
- `packages/frontend-sdk-react/src/usePluginActionDialog.ts`
- `packages/frontend-sdk/src/plugins/actionRunner.ts`

The existing action dialog supports a `dialog` object with `kind: "form"` and `inputs`. Inputs support at least:

- `type: "string"`
- `type: "multiline"`
- `type: "integer"`
- `type: "number"`
- `type: "boolean"` / `type: "checkbox"`
- app-provided custom field renderers such as mobile select chips

The embedded display form should reuse this schema rather than inventing a separate input format.

## Proposed Protocol Shape

Add an optional `form` object to `ActionDisplayPayload`:

```json
{
  "display": {
    "format": "markdown",
    "title": "Finish MCP login",
    "body": "Paste the callback URL from Safari.",
    "variant": "info",
    "presentation": "inline",
    "display_id": "mcp-login-finish-figma",
    "form": {
      "kind": "form",
      "inputs": [
        {
          "name": "redirect_url",
          "type": "multiline",
          "label": "Callback URL",
          "placeholder": "http://127.0.0.1:41793/callback?code=...&state=...",
          "required": true
        }
      ]
    },
    "actions": [
      {
        "kind": "run_action",
        "id": "submit-mcp-callback-url",
        "label": "Submit",
        "plugin": "mcp_runtime_app",
        "action_id": "mcp_finish_login_from_callback_url",
        "fixed_params": {
          "server_name": "figma"
        },
        "param_map": {
          "redirect_url": "$form.redirect_url"
        },
        "preserve_display": true
      },
      {
        "kind": "dismiss",
        "id": "cancel-mcp-callback-url",
        "label": "Cancel"
      }
    ]
  }
}
```

`$form.<field>` should map values from the display form. Existing `$dialog.<field>` mappings must continue to work for action dialogs.

Add a local follow-up action kind:

```json
{
  "kind": "dismiss",
  "id": "cancel",
  "label": "Cancel"
}
```

This should close/remove the current display without calling the backend.

## Implementation Notes

- Update `packages/frontend-sdk/src/types/plugins.ts`:
  - add `form?: any` or a typed display form interface to `ActionDisplayPayload`
  - add `param_map?: Record<string, string>` to `ActionDisplayRunActionAction`
  - add a `dismiss` follow-up action type
- Update `packages/frontend-sdk/src/plugins/actionRunner.ts`:
  - support `$form.` sources in addition to `$dialog.`
  - add a `formValues?: Record<string, any>` field to `RunActionContext`, or reuse `dialogValues` only if the naming remains clear and documented
  - preserve existing `$dialog.` behavior and tests
- Prefer factoring common form rendering logic out of `ApplicationActionDialogLayout` if practical, but keep the change scoped. Avoid moving components between mobile and desktop app packages; shared generic RN component changes belong only in `packages/frontend-rn-components` when they are already shared by both RN apps.
- Mobile should use its existing mobile field renderers from `mobile/crystal-lattice-control-rn/src/components/applicationActionDialogRenderers.tsx` for display forms where applicable.
- Desktop should use its existing desktop action display/card patterns and desktop dialog field rendering behavior where applicable.

## SDK Testing Requirements

Add or update tests under `packages/frontend-sdk/src/plugins/__tests__/`:

- `$form.redirect_url` maps into a follow-up `run_action` input.
- `fixed_params` and `param_map` merge correctly for display form actions.
- `$dialog` mapping still works for existing action dialog flows.
- A `dismiss` follow-up action is accepted by types/helpers without attempting backend execution.

Add or update SDK integration tests under `packages/frontend-sdk/src/integration/__tests__/` using the established real-backend patterns:

- Use a deterministic dummy application plugin or existing dummy MCP OAuth flow.
- Execute an action that returns a display with embedded form fields.
- Submit a follow-up action with form values through the SDK.
- Assert the backend action receives the mapped value and returns the expected result/display.

## Manual Testing Dummy Plugin

Add a small deterministic dummy application plugin under `plugins/`, similar in spirit to `plugins/dummy-settings-app`, so this generic feature can be tested without MCP:

- one action returns a display with markdown/plain text body, a `multiline` field, a `string` field, Submit, and Cancel
- Submit maps values through `$form.<field>` and returns a confirmation display that echoes safe non-secret values
- Cancel uses the generic `dismiss` follow-up action
- the plugin should be easy to add to local config for manual mobile and desktop testing

Document the config snippet and manual test flow in the plugin README or a short test README near the plugin. The manual test should prove:

- mobile can render and submit embedded display forms
- desktop can render and submit embedded display forms
- SDK/action execution receives the same values that the user typed
- dismiss works without calling the backend

## React Native Testing Requirements

Mobile:

- Add component/integration coverage in `mobile/crystal-lattice-control-rn/__tests__/`.
- Render an `ActionDisplayCard` or screen-level action result display with:
  - markdown/plain text body
  - a `multiline` form field
  - Submit and Cancel actions
- Assert that entering text and pressing Submit calls the follow-up handler with form values available.
- Assert that pressing Cancel/dismiss removes or closes the display.

Desktop:

- Add coverage in the desktop RN test location if present; otherwise document the current desktop RN test limitation and add the closest available unit/component coverage for the desktop `ActionDisplayCard`.
- Verify that the desktop display renders the form field and passes submitted values to the follow-up action handler.

## Documentation Requirements

Update `plugins/docs/actions.md`:

- Document `display.form`.
- Document supported form input schema and state that it reuses action dialog form inputs.
- Document `$form.<field>` param mapping for display follow-up actions.
- Document `dismiss` follow-up actions.
- Include an MCP login-style example with body, form, Submit, and Cancel.

Document the dummy plugin manual test flow, including:

- the local plugin config snippet
- how to open the action from mobile and desktop
- what text to enter
- what confirmation output to expect

Update frontend SDK docs if a relevant README exists near `packages/frontend-sdk/src/plugins/` or `packages/frontend-sdk/src/integration/__tests__/README.md`:

- Mention the SDK integration test and how to run it.

Update mobile/desktop documentation only if there is an existing app-level developer README for action displays; otherwise keep the user-facing protocol docs in `plugins/docs/actions.md`.

## Acceptance Criteria

- A plugin can return an action display containing text, form fields, and actions.
- Mobile and desktop both render the form fields in the display.
- Form values can be submitted via follow-up `run_action` using `$form.<field>`.
- Cancel/dismiss can close the display without backend execution.
- Existing displays without `form` are unchanged.
- Existing action dialogs using `$dialog.<field>` are unchanged.
- SDK tests, React Native tests, and relevant integration tests pass.
- A dummy plugin can be used manually to exercise the embedded form flow without any MCP server.
- MCP runtime integration is not implemented until Figma has been manually tested enough to prove the pasted callback URL flow can complete login and call at least one Figma MCP tool.

## MCP Integration Gate

Before adding MCP runtime actions that depend on embedded forms, finish the Figma compatibility check:

- use configurable OAuth client metadata and redirect URL settings
- start the Figma login flow with Codex-like settings or any settings known to be accepted by Figma
- open the authorization URL manually
- complete login in the browser
- copy the resulting callback URL from Safari or the browser
- feed that callback URL into the runtime/login completion path
- verify the token is stored and the Figma MCP server can list or call at least one tool

If Figma still rejects registration, redirect URI, token exchange, or subsequent tool calls, document the exact failing step and do not wire MCP runtime UX to the embedded form flow yet. The generic embedded-form feature and dummy plugin can still be completed independently.

## Proposed Future Work

This task intentionally does not implement follow-up actions that open a separate dialog. That related capability is tracked separately in `tasks/20260620-action-display-followup-dialogs.md`.

## Completion Notes

Added during implementation:

- Added `display.form`, display follow-up `param_map`, `$form.<field>` mapping, and `dismiss` follow-up actions to the generic frontend SDK action display protocol.
- Added `ApplicationActionForm` in `packages/frontend-rn-components/src/ApplicationActionDialog.tsx` so embedded display forms reuse the action-dialog form schema, parser, validation, and app-provided field renderers.
- Updated mobile and desktop action display cards and follow-up handlers to render embedded forms and pass submitted values into `runApplicationAction`.
- Added `plugins/dummy-action-display-form-app` for manual testing without MCP.
- Added SDK unit and real-backend integration tests for the dummy display form flow.
- Added mobile component and real-backend integration tests, plus desktop component coverage.
- Updated `plugins/docs/actions.md` with `display.form`, `$form.<field>`, `dismiss`, the dummy plugin manual test pointer, and a future note for follow-up dialogs.

MCP runtime UX was intentionally not wired in this slice. The Figma compatibility gate remains open: before adding MCP-specific login actions that depend on pasted callback URLs, manually verify that Figma accepts the configured client metadata/redirect URL, completes token exchange from a copied callback URL, and can call at least one MCP tool after login.
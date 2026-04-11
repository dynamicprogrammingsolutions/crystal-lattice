# Action Display Follow-Up

Add richer generic frontend handling for plugin action results so plugins can return follow-up actions and presentation hints, without introducing auth-specific UI contracts.

## Requirements checklist

- [x] Define and document a richer `result.display` contract that supports:
  - follow-up actions
  - presentation hints
  - dismissibility control
- [x] Propose a safe generic action model that can support:
  - `Open link`
  - `Copy code`
  - `Check status`
- [x] Preserve current `display` compatibility so existing markdown-only payloads continue to work unchanged.
- [x] Specify frontend behavior for `presentation: "inline"` so executing a follow-up action such as `Check status` does not automatically hide the existing inline notification.
- [x] Identify the backend/frontend files that would need implementation changes if this proposal is approved.

## Context

Current implemented contract:

- Shared type:
  - `packages/frontend-sdk/src/types/plugins.ts`
- Shared action runner passthrough:
  - `packages/frontend-sdk/src/plugins/actionRunner.ts`
- Mobile popup renderer:
  - `mobile/crystal-lattice-control-rn/src/components/ActionResultModal.tsx`
- Desktop popup renderer:
  - `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionResultModal.tsx`

Current `display` shape is intentionally minimal:

```ts
interface ActionDisplayPayload {
  format: 'markdown' | 'text';
  body: string;
  title?: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
}
```

This is enough to render login instructions, but not enough to express rich, generic next-step affordances like `Open link`, `Copy code`, or `Check status`.

## Proposed interface

Extend the payload shape to:

```ts
interface ActionDisplayPayload {
  format: 'markdown' | 'text';
  body: string;
  title?: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
  presentation?: 'modal' | 'inline' | 'banner';
  dismissible?: boolean;
  actions?: ActionDisplayFollowupAction[];
  display_id?: string;
}
```

Where:

```ts
type ActionDisplayFollowupAction =
  | {
      kind: 'open_url';
      id: string;
      label: string;
      url: string;
    }
  | {
      kind: 'copy_text';
      id: string;
      label: string;
      text: string;
      copied_label?: string;
    }
  | {
      kind: 'run_action';
      id: string;
      label: string;
      plugin: string;
      action_id: string;
      action_owner?: string;
      fixed_params?: Record<string, unknown>;
      preserve_display?: boolean;
    };
```

Notes:

- `presentation` is a frontend hint, not a guarantee.
- `dismissible` defaults can be frontend-defined if omitted.
- `display_id` lets the frontend update or replace an existing inline/banner display in the future, instead of always appending a new one.
- `actions` should be intentionally small and safe. This should not become a generic remote UI scripting channel.

## Allowed action kinds

### 1. `open_url`

Purpose:
- open an external URL in the platform browser

Example:

```json
{
  "kind": "open_url",
  "id": "open-login-link",
  "label": "Open ChatGPT login",
  "url": "https://auth.openai.com/codex/device"
}
```

Constraints:

- `url` must be a non-empty absolute URL string.
- Frontends should validate scheme and only allow known-safe schemes such as `https` and `http` unless explicitly expanded later.
- This action is frontend-only and should not call back to the backend.

### 2. `copy_text`

Purpose:
- copy a provided string to the platform clipboard

Example:

```json
{
  "kind": "copy_text",
  "id": "copy-user-code",
  "label": "Copy code",
  "text": "BGSK-G31A4",
  "copied_label": "Copied"
}
```

Constraints:

- `text` must be a string.
- This action is frontend-only and should not call back to the backend.
- `copied_label` is optional UI sugar for button state or toast copy.

### 3. `run_action`

Purpose:
- execute another plugin/application action from the frontend

Example:

```json
{
  "kind": "run_action",
  "id": "check-status",
  "label": "Check status",
  "plugin": "chatgpt_auth",
  "action_id": "check_status",
  "fixed_params": {},
  "preserve_display": true
}
```

Constraints:

- This should reuse the existing action execution pipeline.
- The frontend should not allow arbitrary code or shell execution through this channel.
- It should only dispatch through the same validated backend action API already used for plugin actions.
- `fixed_params` should be optional and JSON-serializable.

## Proposed frontend behavior

### `presentation: "modal"`

- Render the current popup behavior.
- Follow-up buttons may appear below the markdown/text body.
- Executing a follow-up action may:
  - replace the modal content with the new result
  - close and reopen with the new result
  - leave the modal open if `preserve_display` is true and the frontend chooses to support that

### `presentation: "inline"`

- Render a persistent inline notification/card within the relevant screen context.
- It should remain visible until:
  - dismissed by the user, if dismissible
  - replaced by another display with the same `display_id`
  - or explicitly removed by later frontend logic

Important rule for this task:

- If a follow-up `run_action` button such as `Check status` is pressed and the current display has `presentation: "inline"`, the frontend should **not** automatically hide the current notification just because a follow-up action was triggered.
- If the follow-up action returns a new display:
  - with the same `display_id`, frontend may replace/update the existing inline card
  - without a `display_id`, frontend may either show a second display or keep the old one and surface the new result separately, depending on the chosen UX

### `presentation: "banner"`

- Render a compact banner/toast-like status area.
- Good for short success/error confirmations.
- Likely lower priority than `modal` and `inline`.

## Suggested first use case

ChatGPT login could eventually return:

```json
{
  "display": {
    "title": "ChatGPT Login",
    "format": "markdown",
    "variant": "info",
    "presentation": "inline",
    "dismissible": true,
    "display_id": "chatgpt-auth-login",
    "body": "1. Open [ChatGPT device login](https://auth.openai.com/codex/device)\n2. Enter code `BGSK-G31A4`\n\nThen return here and check the login status.",
    "actions": [
      {
        "kind": "open_url",
        "id": "open-login",
        "label": "Open link",
        "url": "https://auth.openai.com/codex/device"
      },
      {
        "kind": "copy_text",
        "id": "copy-code",
        "label": "Copy code",
        "text": "BGSK-G31A4"
      },
      {
        "kind": "run_action",
        "id": "check-status",
        "label": "Check status",
        "plugin": "chatgpt_auth",
        "action_id": "check_status",
        "fixed_params": {},
        "preserve_display": true
      }
    ]
  },
  "auth_status": {
    "state": "pending"
  }
}
```

## Files likely involved if implemented

Shared types and action runner:

- `packages/frontend-sdk/src/types/plugins.ts`
- `packages/frontend-sdk/src/plugins/actionRunner.ts`

Mobile UI:

- `mobile/crystal-lattice-control-rn/src/components/ActionResultModal.tsx`
- likely a new inline result component in `mobile/crystal-lattice-control-rn/src/components/`
- consumers in:
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

Desktop UI:

- `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionResultModal.tsx`
- likely a desktop inline result component in `desktop/crystal-lattice-control-desktop-rn/src/ui/`
- consumers in:
  - `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Plugin/action docs:

- `plugins/docs/actions.md`

Likely first backend/plugin consumer:

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`

## Proposed implementation phases

1. Extend shared `display` types with `presentation`, `dismissible`, `display_id`, and `actions`.
2. Add generic frontend action-button rendering to the modal renderer.
3. Implement frontend-only action kinds:
   - `open_url`
   - `copy_text`
4. Implement `run_action` using the existing action runner.
5. Add inline presentation support with persistence/replacement rules.
6. Update ChatGPT auth action results to use the richer payload.
7. Add tests for:
   - type passthrough
   - button handling
   - inline preservation when `run_action` is triggered

## Open questions

- Should `run_action` be restricted to the same plugin that produced the display by default?
- Should `display_id` be mandatory for `presentation: "inline"`?
- Should `copy_text` support masked display vs copied value for secrets or short-lived codes?
- Should `open_url` allow only `https` in the first version?

## Completion Notes

Added the richer generic `display` contract to the shared frontend SDK with
`presentation`, `dismissible`, `display_id`, and generic follow-up `actions`.
The action runner now passes this payload through unchanged, preserving
backward compatibility for existing markdown/text-only displays.

Implemented generic rendering for both modal and inline action results in the
mobile and desktop React Native frontends. Supported follow-up actions are:

- `open_url`
- `copy_text`
- `run_action`

The frontend preserves existing inline notifications when a follow-up
`run_action` is executed, and replaces inline displays by `display_id` when a
new payload with the same id arrives.

Updated the ChatGPT auth application plugin to use the richer payload for the
pending login state, including `Open link`, `Copy code`, and `Check status`
follow-up actions.

Documentation was updated in `plugins/docs/actions.md` to describe the richer
payload and the supported action kinds.

Verification completed:

- `npm test -- --testNamePattern='runApplicationAction'` in
  `packages/frontend-sdk`
- `pytest plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py -q`
- targeted desktop lint for:
  - `src/ui/ActionResultModal.tsx`
  - `src/ui/ActionDisplayCard.tsx`
  - `src/ui/ActionResultInlineCard.tsx`

Residual verification notes:

- The mobile package does not expose a working local ESLint configuration via
  direct targeted `npx eslint ...` invocation in this environment, so mobile
  validation here was limited to code inspection rather than a clean targeted
  lint pass.
- Targeted desktop lint on larger existing files
  (`SessionsPanel.tsx`, `ChatPane.tsx`) still reports pre-existing unrelated
  hook-dependency and local-style warnings/errors outside this follow-up
  change.

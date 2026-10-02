# Add Plugin-Driven Actions To Session Settings

Let plugins place their existing actions beside related fields in the session
settings window, and add a reusable client-assisted directory input so native
folder selection can participate in an ordinary plugin action.

## Requirements checklist

- [x] A plugin can place a `session_action` in the session settings surface
  without also exposing it in the session header or composer.
- [x] A settings-placed action can identify a config-field anchor and render
  directly after that field; an action with no usable anchor appears in a
  general settings-actions section.
- [x] Settings actions retain the existing action owner, input validation,
  dialog, execution, mutation, display, idempotency, and UI-invalidation
  behavior.
- [x] A plugin action can request a user-mediated directory input; the mobile
  host opens the native directory picker and supplies an opaque persistent
  grant identifier rather than a raw security-scoped bookmark.
- [x] Canceling a client input does not execute the plugin action or change
  settings.
- [x] The OpenAI Responses prompt-cache regeneration action is rendered under
  its cache-key setting instead of occupying the ordinary session-action
  surface.
- [x] Existing config controls and session actions without the new placement
  retain their current behavior.
- [x] The contract is defined in the shared frontend SDK and documented for
  plugin authors rather than existing only as mobile component behavior.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

## Settled direction

- Reuse `ui_type: "session_action"` and the existing action execution
  endpoints. Settings placement is presentation, not a new action type.
- Add `session_settings` to the recognized session-action placements.
- Add a first-class button rich presentation with an optional settings anchor:

  ```json
  {
    "rich_ui": {
      "kind": "button",
      "placements": ["session_settings"],
      "anchor_key": "prompt_cache_key",
      "position": "after"
    }
  }
  ```

- Let unknown or missing anchors fall back to a bottom **Actions** section.
- Model native directory acquisition as client-assisted action input. The
  frontend obtains and stores the native grant before invoking the action and
  submits only its opaque identifier.
- Keep action placement independent of action ownership. Provider-extension,
  feature, and application actions may all appear in session settings.
- Use the existing prompt-cache action as a second, non-workspace consumer of
  the contract.

## Supporting facts

- Session settings currently merge core and application UI schema, then
  discard every element except config controls.
- The shared action runner already handles application, feature, and
  provider-extension actions, parameter mapping, dialogs, standard results,
  and session-scoped endpoints.
- Successful actions already invalidate affected session UI schema through
  the production REST backend.
- The OpenAI Responses prompt-caching extension already implements
  `regenerate_prompt_cache_key`; only its UI placement needs to change.
- `@react-native-documents/picker` 12.0.1 already provides native iOS
  directory selection and long-term bookmark creation. Bookmark persistence
  and restoration belong to the native host, not the generic action payload.

## Execution plan

Status: Approved

Extend the shared rich-UI contract with a `session_settings` placement and a
normalized button presentation carrying an optional field anchor and
position. Preserve unknown placement compatibility and the existing default
session-header behavior for actions without explicit placement.

Split the session-settings controller output into editable config elements and
settings-placed actions. Retain both core and application-plugin
contributions, normalize the actions through the existing session-action
contract, and keep cached snapshots compatible.

Render settings actions in the mobile settings modal. Anchored buttons appear
after their field; unanchored buttons appear in a final **Actions** section.
Execution uses the shared action runner, current session context, existing
dialogs, and existing action result/display handling. Successful execution
refreshes settings and schema through the established invalidation path.

Add a generic client-input description for persistent read/write directories.
The mobile frontend invokes a directory-grant adapter before action
execution. The adapter owns native picker presentation and grant persistence
and returns an opaque grant ID. The action is skipped on cancellation and
receives the grant ID through its normal input mapping on success.

Move the prompt-cache regeneration UI declaration to
`session_settings`, anchored after `prompt_cache_key`, while preserving its
existing provider-extension implementation and action tests.

### Implementation decisions and open questions

- **Approved:** settings placement extends `session_action`; it is not a new
  action execution surface.
- **Approved:** the first anchor position is `after`; unsupported positions
  fall back to the settings action section.
- **Approved:** buttons without a usable anchor remain visible at the bottom
  of settings rather than disappearing.
- **Approved:** the generic client-input payload contains only an opaque grant
  ID. Raw bookmarks and external paths are not action parameters.
- **Approved:** the prerequisite defines the client-input contract and mobile
  adapter seam. Workspace-specific native persistence and restoration are
  completed by subtask `025`.

### Documentation

- Document settings action placement, anchoring, fallback behavior, and action
  ownership in the plugin action guide.
- Document the client-assisted directory input and the opaque-grant boundary.
- Update OpenAI Responses documentation to locate cache-key regeneration in
  session settings.

### Task checklist

- [x] Add and test the shared settings-action rich-UI contract.
- [x] Preserve settings actions in the session-settings controller.
- [x] Render and execute anchored and fallback actions in mobile settings.
- [x] Add the client-assisted directory input adapter contract.
- [x] Move prompt-cache regeneration to session settings.
- [x] Add focused SDK, React binding, mobile component, provider, and
  production-backend coverage.
- [x] Update plugin and provider documentation.

### Requirement verification

- Feed mixed config and session-action elements through the production
  session-settings controller and prove only explicitly settings-placed
  actions are returned as settings actions.
- Render an anchored action and an unanchored action in the production mobile
  settings modal, execute each through `RestAgentBackend`, and prove settings
  refresh after the reported session mutation.
- Cancel a directory client input and prove no action request is sent; complete
  it and prove the action receives only the opaque grant ID.
- Load an OpenAI Responses session, confirm **Regenerate cache key** appears
  after the prompt-cache field and not in the normal session header, execute
  it, and prove the key changes.

### Additional implementation verification

- Run the focused frontend SDK and React package tests, mobile Jest and
  TypeScript checks, OpenAI Responses prompt-caching tests, documentation
  preparation, and `git diff --check`.

## Implementation Notes

- 2026-09-30: Added the normalized `button` rich-UI kind and
  `session_settings` placement, including field anchoring and bottom-section
  fallback.
- 2026-09-30: Session settings now retain settings-placed actions separately
  from editable config controls and render them through the existing action
  runner and dialog components.
- 2026-09-30: Added `$client.*` action parameter mapping and the persistent
  directory client-input adapter. Cancellation returns without sending an
  action request; success submits only the opaque native grant ID.
- 2026-09-30: Moved OpenAI Responses cache-key regeneration under
  `prompt_cache_key`; the action implementation and provider-extension owner
  are unchanged.

## Completion Notes

Completed on 2026-09-30.

- Shared frontend SDK: 48 files and 357 tests passed.
- Shared React bindings: 6 files and 24 tests passed.
- Mobile: TypeScript passed; all 55 Jest suites and 283 tests passed.
- OpenAI Responses prompt-cache application integration: 5 non-API
  integration tests passed.
- The Release iOS simulator build passed with the client-input/native grant
  bridge compiled.
- Plugin action documentation and OpenAI Responses user documentation now
  describe settings placement and opaque directory grants.
# Rich session UI implementation

The frontend SDK normalizes compact configuration controls and rich
session-action placement before mobile or desktop renders them.

Maintainer entry points:

- `src/uiSchema/richUi.ts`
- `src/sessionSettings/sessionSettingsController.ts`
- `src/sessions/sessionListContracts.ts`
- `src/sessions/sessionListRichActions.ts`
- `src/plugins/actionSources.ts`

## Configuration controls

`normalizeConfigRichUiElement()` validates the containing config element and
its self-contained `rich_ui`. Supported renderer kinds are `dropdown` and
Boolean `toggle`.
`selectConfigRichUiControls()` selects normalized controls for
`session_header` or `composer`.

The containing config element supplies the setting key, ordinary label/icon,
and ordinary session-settings semantics. Normal action menus and frontends
without rich-UI support render those outer presentation fields without
interpreting `rich_ui`. `SessionSettingsController` remains the only mutation
path:

- `patchOverride(key, value)` selects a declared/custom value or toggles a
  Boolean setting;
- `deleteOverride(key)` resets to configured/default state;
- ordinary type coercion still follows the containing config element.

The rich dropdown repeats its own compact label, options, placeholder, nested
`custom_value`, placement, and pin preference. One query field filters
declared options and produces a synthetic custom row after full regex
validation. The normalized suggestion engine is
`createConfigDropdownSuggestionEngine()`.

Options may declare theme-aware semantic tones and icons. The selected option
controls compact appearance; its icon overrides the outer fallback icon only
on compact surfaces. `show_icon: false` keeps compact controls text-only while
retaining the outer icon for ordinary UI. Disabled controls are muted.
`show_label: false` removes only the visual prefix. Mobile and desktop apply
different visual character limits while preserving the full accessibility
label.

The opt-in `plugins/dummy-rich-config-ui` feature is the reference manual-test
consumer for the complete semantic option palette. Production providers adopt
rich presentation only within their own contracts.

A rich config toggle has one false and one true option and immediately patches
the ordinary checkbox setting. Unknown kinds remain transportable and are not
selected by the current renderer.

## Session actions

`normalizeSessionActionRichUiElement()` reuses the existing session-list
action/dialog/rich normalization and maps it back to `session_action`.
`isSessionActionPlacedAt()` applies the chat placement contract:

- missing rich placement defaults to `session_header`;
- explicit `composer` moves or adds the action to the composer surface.

The ordinary action remains authoritative. Rich toggle/list controls invoke
the existing action runner and submit the same mapped dialog values.

An active model request is status, not a global mutation lock. Hosts keep
ordinary/rich config controls and unrelated session/application actions
invokable and let their existing backend paths accept or reject concurrent
work. Request-start actions such as Send and Resend remain individually
guarded. A config override changed during streaming is available to a later
request; it does not rewrite the request already created by the server.

## Verification

Focused contract tests:

```bash
npm --workspace @crystal-lattice/frontend-sdk test -- src/uiSchema/richUi.test.ts
npm --workspace @crystal-lattice/frontend-sdk run integration:anthropic-rich-ui
```

The integration test starts the real Python HTTP application, loads the
Anthropic provider, session-status application plugin, and opt-in dummy rich
config feature, discovers models from a local protocol server, and uses
`RestAgentBackend` plus `SessionSettingsController` to verify model overrides,
portable option appearance, and the status session-action declaration.
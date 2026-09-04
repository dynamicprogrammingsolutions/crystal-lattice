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
its self-contained `rich_ui`. The initial renderer kind is `dropdown`.
`selectConfigRichUiControls()` selects normalized controls for
`session_header` or `composer`.

The containing config element supplies the setting key and ordinary
session-settings semantics. `SessionSettingsController` remains the only
mutation path:

- `patchOverride(key, value)` selects a declared or custom value;
- `deleteOverride(key)` resets to configured/default state;
- ordinary type coercion still follows the containing config element.

The rich dropdown repeats its own label, options, custom-entry text, icon,
placement, and pin preference. Unknown kinds remain transportable and are not
selected by the current renderer.

## Session actions

`normalizeSessionActionRichUiElement()` reuses the existing session-list
action/dialog/rich normalization and maps it back to `session_action`.
`isSessionActionPlacedAt()` applies the chat placement contract:

- missing rich placement defaults to `session_header`;
- explicit `composer` moves or adds the action to the composer surface.

The ordinary action remains authoritative. Rich toggle/list controls invoke
the existing action runner and submit the same mapped dialog values.

## Verification

Focused contract tests:

```bash
npm --workspace @crystal-lattice/frontend-sdk test -- src/uiSchema/richUi.test.ts
npm --workspace @crystal-lattice/frontend-sdk run integration:anthropic-rich-ui
```

The integration test starts the real Python HTTP application, loads the
Anthropic provider, discovers models from a local protocol server, and uses
`RestAgentBackend` plus `SessionSettingsController` to select, enter, and reset
model overrides.
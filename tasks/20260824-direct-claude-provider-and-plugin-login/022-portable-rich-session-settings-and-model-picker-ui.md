# Portable Rich Session Settings And Model Picker UI

Replace the provider-specific composer model-picker contract with a portable
rich configuration contract, correct provider model dropdowns, and make the
same setting/action presentation available in mobile and desktop chat.

Parent Task: `tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

## Requirements checklist

- [x] `AnthropicProvider` emits the established model dropdown configuration
  element when discovered models are available and a text input fallback when
  discovery is unavailable.
- [x] Provider model dropdowns permit a manually entered model ID in frontends
  that support session configuration overrides.
- [x] Desktop session settings render `type: "dropdown"` through a
  desktop-specific native dropdown rather than the text fallback.
- [x] Mobile model selection permits both discovered options and an arbitrary
  model ID.
- [x] Ordinary `ui_type: "config"` elements can opt into compact rich
  presentation at documented chat placements without an application plugin or
  action endpoint.
- [x] Ordinary `ui_type: "session_action"` elements can use the established
  rich toggle/list presentation in chat and can be placed in the session
  header or composer action area.
- [x] The mobile-only `ui_type: "model_picker"` contract is removed and all
  current provider emitters migrate to the standard config-rich-UI contract.
- [x] Shared frontend packages normalize, validate, resolve, mutate, and render
  the portable contract consistently.
- [x] The portable provider specification and public plugin-authoring
  documentation define model dropdown and rich configuration requirements
  accurately.
- [x] Deterministic, component, native desktop, mobile, and public-backend
  integration tests cover the migrated behavior.

## Resolved requirement decisions

1. Placement is represented as ordered `rich_ui.placements` to match the
   existing session-list rich-action contract and permit one declaration to
   appear in both `session_header` and `composer`.
   - Initial supported chat placements would be `session_header` and
     `composer`.
2. A rich config element remains visible in the full Session Settings view.
   Rich placement is an additional compact surface; Session Settings remains
   the complete discoverable editor and reset surface.
3. Dropdowns declare manual entry through `allow_custom_value: true` on both
   the ordinary config element and the rich dropdown. Both surfaces expose an
   explicit “Other model…” text-entry path. Custom entry is supported only for
   string-valued settings.
4. `rich_ui` is self-contained for its presentation and repeats `label`,
   `options`, `allow_custom_value`, placeholder/help text, icon, pinning, and
   placements as applicable.
   - The outer config element remains authoritative for mutation identity and
     full settings behavior through `key`, `config_path`, `type`, schema
     defaults, and override resolution.
5. Rich config uses presentation-specific kinds. The model selector uses
   `kind: "dropdown"`. Future compact settings may define `select`, `toggle`,
   `text`, or other kinds with their own validated fields and renderers.
6. Every current `model_picker` emitter (`openrouter`,
   `openrouter_responses`, and `openai_responses`) migrates in the same
   contract change. Anthropic adopts the standard contract directly.
7. Ordinary session actions default to `session_header` when no rich placement
   is declared. `composer` placement is explicit and placement remains inside
   `rich_ui`.
8. Compact config settings default to not pinned. Provider model selectors
   explicitly use `default_pinned: true` so the selected model remains visible
   near the composer.

## Proposed contract

### Model configuration element

```json
{
  "ui_type": "config",
  "type": "dropdown",
  "key": "model",
  "label": "Model",
  "options": [
    {"value": "claude-sonnet-5", "label": "Claude Sonnet 5"}
  ],
  "allow_custom_value": true,
  "rich_ui": {
    "kind": "dropdown",
    "placements": ["composer"],
    "default_pinned": true,
    "icon": "cpu",
    "label": "Model",
    "options": [
      {"value": "claude-sonnet-5", "label": "Claude Sonnet 5"}
    ],
    "allow_custom_value": true,
    "custom_value_label": "Other model…",
    "custom_value_placeholder": "Enter a model ID"
  }
}
```

When model discovery returns no options, the provider emits:

```json
{
  "ui_type": "config",
  "type": "text",
  "key": "model",
  "label": "Model",
  "rich_ui": {
    "kind": "dropdown",
    "placements": ["composer"],
    "default_pinned": true,
    "icon": "cpu",
    "label": "Model",
    "options": [],
    "allow_custom_value": true,
    "custom_value_label": "Other model…",
    "custom_value_placeholder": "Enter a model ID"
  }
}
```

The full settings editor reads and writes the ordinary config key. Compact
rich presentation uses the same effective value and the same session override
mutation; it does not call an application action. The repeated rich fields are
authoritative for the compact surface and may intentionally use a shorter
label or a smaller option set than the full settings editor.

### Rich session action

```json
{
  "ui_type": "session_action",
  "id": "set_session_status",
  "label": "Set status",
  "icon": "circle",
  "action_id": "set_session_status",
  "dialog": {
    "kind": "form",
    "inputs": [
      {
        "name": "status",
        "type": "select",
        "options": [
          {"value": "todo", "label": "To do"},
          {"value": "done", "label": "Done"}
        ]
      }
    ]
  },
  "rich_ui": {
    "kind": "list",
    "value_path": "metadata.status",
    "missing_value": "todo",
    "input_name": "status",
    "placements": ["session_header", "composer"],
    "options": [
      {"value": "todo", "label": "To do"},
      {"value": "done", "label": "Done"}
    ]
  }
}
```

The ordinary dialog remains the fallback. A recognized rich kind renders the
compact control and executes the same action with the same parameter mapping.

## Supporting facts

- Before this task, `AnthropicProvider.get_ui_elements` emitted `type:
  "select"` for a
  discovered model list and omitted explicit `ui_type: "config"`.
- OpenRouter, OpenRouter Responses, OpenAI Responses, image-generation, and
  the reference OpenAI-compatible provider already use `type: "dropdown"` for
  discovered model lists and text fallback when no list exists.
- Before this task, OpenRouter, OpenRouter Responses, and OpenAI Responses
  additionally emitted a
  special `ui_type: "model_picker"` element with
  `display_placement: "left"`. Only the mobile chat currently consumes it.
- Before this task, `plugins/docs/ui-elements.md` correctly described `select` as an
  all-options-visible control and `dropdown` as collapsed, but its two
  model-driven provider examples incorrectly used `select`.
- The `model_picker` documentation does not describe its actual
  `attachment_type`, options, placement, pinning, effective-value, or mutation
  behavior.
- Before this task, desktop `SessionSettingsWindow` implemented renderers for `select`, text,
  multiline, checkbox, and readonly values. `dropdown` therefore falls through
  to the text renderer even though the desktop already has `MacSelect`.
- Before this task, Mobile Session Settings had a dropdown renderer and searchable
  `OptionsPickerModal`, but the picker can only submit a declared option.
- Before this task, mobile chat had a dedicated `model_picker` path that read session base
  config and overrides, patches one override key, and invalidates the UI
  schema. This behavior is the natural generic config-rich mutation path.
- Chat session actions already merge application and core-plugin
  `session_action` elements. Both frontends currently present those actions in
  the header action bar without a placement contract or rich toggle/list
  renderer.
- Session-list rich actions already normalize toggle/list kinds, option values,
  semantic tones, default pinning, and ordered placements in the frontend SDK.
  That implementation is currently coupled to `session_list_action`.

## Execution plan

Status: Approved

Implement this as a shared UI-contract migration rather than an
Anthropic-specific frontend exception.

First, finalize the schema in the frontend SDK and public authoring docs.
Extract or generalize the current session-list rich-action normalization so
ordinary `session_action` elements can use the same toggle/list contract and
diagnostics. Add a separate discriminated config-rich normalizer whose
presentation is self-contained by kind, while the containing config element
supplies mutation identity, effective-value resolution, and reset behavior.

Second, replace the mobile-only model picker. Providers emit one ordinary model
config element with dropdown options, manual-entry capability, and composer
rich placement. Remove `ui_type: "model_picker"` from providers, frontend
types, fixtures, and mobile chat. The composer consumes normalized rich config
elements and uses the session-settings controller/backend override path.

Third, implement frontend rendering:

- desktop Session Settings adds a native `dropdown` renderer using
  `MacSelect`;
- mobile dropdowns expose an explicit custom-value text entry when allowed;
- mobile and desktop chat split session actions by placement;
- both chats render rich session-action toggle/list controls at
  `session_header` or `composer`;
- both chats render config-rich controls with the same current value, reset,
  option, custom-entry, disabled, and pin semantics as Session Settings;
- unsupported rich kinds fall back to the ordinary action or remain available
  in Session Settings.

Fourth, migrate providers and documentation. Anthropic uses the portable model
dropdown. Existing special model-picker emitters move to the same config
contract in one change because backward compatibility is not required.

### Implementation decisions and open questions

- Decision: this work is subtask 022 and does not reopen task 010 Stage 1.
- Decision: model selection remains a normal session config override.
- Decision: config-rich UI does not require an action definition or
  application plugin.
- Decision: action-rich UI invokes the existing action and retains the
  ordinary dialog as fallback.
- Decision: provider discovery failure preserves manual model entry.
- Decision: remove `ui_type: "model_picker"` rather than supporting both
  contracts.
- Decision: compact config placement is additive to the full settings editor.
- Decision: compact rich config uses presentation-specific discriminators;
  model selection uses `rich_ui.kind: "dropdown"`.
- Decision: rich UI repeats its presentation fields and does not implicitly
  inherit label, options, custom-entry text, icon, or appearance from the
  ordinary config element.
- Decision: the containing config element remains the binding for `key`,
  `config_path`, effective value, override mutation, schema/default source, and
  reset behavior. Those behavioral fields are not duplicated in `rich_ui`.
- Decision: compact settings may declare both header and composer placements;
  ordered placement values are deduplicated during normalization.
- Decision: arbitrary custom entry is available only for string-valued
  settings whose ordinary and rich dropdown declarations both set
  `allow_custom_value: true`.
- Decision: rich session-action placement belongs inside `rich_ui` for
  consistency with session-list actions.

### Documentation

Update current public authoring documentation:

- `plugins/docs/ui-elements.md`:
  - define config-rich presentation and placement;
  - define manual-value dropdown behavior;
  - define rich `session_action` placement;
  - remove the special model-picker type;
  - correct model examples from `select` to `dropdown`;
- `plugins/docs/provider-plugins.md`:
  - require discovered model lists to use dropdown;
  - retain text fallback and manual model entry;
- `plugins/docs/provider-implementation-standard/runtime-contract.md` and
  package/documentation guidance:
  - add the portable model UI expectation;
- `docs/development/specifications/portable-provider-implementation/`:
  - add target behavior and a stable requirement for model discovery UI,
    manual fallback, and portable rich placement;
- provider package docs for Anthropic, OpenRouter, OpenRouter Responses, and
  OpenAI Responses as affected.

Update current frontend development documentation:

- shared frontend SDK UI-schema normalization and rich-action ownership;
- shared React session-settings behavior;
- mobile composer and arbitrary model entry;
- desktop native dropdown and chat placement behavior.

Public docs describe the delivered standard contract without task IDs or
migration-phase language.

### Task checklist

- [x] Resolve the open contract questions and update requirements without
  changing scope silently.
- [x] Add shared SDK types and normalization for config-rich UI and chat
  placements.
- [x] Generalize rich toggle/list action behavior from session-list actions to
  chat session actions.
- [x] Add a shared config-rich value/mutation model backed by session settings.
- [x] Add desktop native dropdown rendering.
- [x] Add custom dropdown values on mobile and desktop where supported.
- [x] Add mobile and desktop session-header/composer placement rendering.
- [x] Remove the special mobile model-picker contract and code path.
- [x] Change Anthropic and all existing model-picker providers to the portable
  config-rich dropdown.
- [x] Update portable specification, provider standard, and UI authoring docs.
- [x] Add deterministic SDK, React, provider, application, mobile, desktop,
  native, and public-backend integration tests.
- [x] Update requirement evidence and consumer/development documentation.
- [x] Run package, application, frontend, native, and docs verification.

### Requirement verification

- Provider unit tests prove discovered models produce a `dropdown` config
  element, no models produce text fallback, and manual entry remains enabled.
- Shared SDK tests prove config-rich and action-rich elements normalize
  consistently, malformed rich data degrades safely, and placements are
  deterministic.
- Session-settings tests prove desktop dropdowns no longer render as text and
  mobile/desktop custom model IDs patch the normal session override.
- Mobile and desktop component tests prove ordinary settings and rich session
  actions can be contributed through the same contract, with only model
  enabled in the Anthropic provider.
- A public backend/frontend-adapter integration loads real provider UI schema,
  selects a discovered model, selects an arbitrary model, reloads effective
  config, and verifies the override.
- Existing session-list rich-action behavior remains intact.

### Additional implementation verification

- Verify composer and header placements on both mobile and desktop.
- Verify pin persistence is scoped per connection/session UI contract and does
  not retain removed element keys.
- Verify custom values remain visible even when absent from a later discovery
  response.
- Verify reset removes the override and returns to the config/default model.
- Verify disabled and active-request states prevent conflicting mutations.
- Verify native desktop dropdown/popover behavior with stable production test
  identifiers.
- Verify unknown rich kinds retain ordinary action/settings fallback.
- Run:
  - Anthropic, OpenRouter, OpenRouter Responses, OpenAI Responses, and reference
    provider model-UI unit tests;
  - `npm --workspace @crystal-lattice/frontend-sdk test`;
  - `npm --workspace @crystal-lattice/frontend-sdk-react test`;
  - `npm --workspace @crystal-lattice/frontend-rn-components test`;
  - focused mobile and desktop Jest suites;
  - desktop macOS native UI tests;
  - application public-backend integration;
  - documentation preparation and MkDocs build.

## Implementation Notes

- September 2, 2026: execution started after user approval. Native macOS
  XCUITest execution remains intentionally blocked pending separate user
  confirmation because it requires desktop interaction/permission.
- September 3, 2026: provider emission, portable SDK normalization,
  config-rich dropdowns, rich session-action placement, mobile and desktop
  hosts, custom model entry, public HTTP/frontend integration, package
  specifications, authoring guidance, and frontend implementation
  documentation are implemented. Deterministic and component tests pass.
  iOS Detox passes the production-screen harness for discovered selection,
  arbitrary entry, reset, header toggle, and composer list action. The Android
  APK and instrumentation APK build, but Android Detox execution is blocked by
  the local API 36.1 AVD: repeated system-package ANRs, package-manager stalls,
  lost application-window focus, and failed instrumentation readiness occur
  before assertions. The focused macOS XCUITest source and harness are
  prepared but have not been executed pending user confirmation.
- September 3, 2026: final passing verification includes provider and template
  unit tests, the default-config application integration, 326 frontend SDK
  tests, 20 React-binding tests, 51 shared React Native component tests, 164
  mobile tests plus TypeScript checking, 139 desktop tests plus focused
  production-`ChatPane` coverage, the real HTTP/`RestAgentBackend` Anthropic
  rich-UI integration, iOS release build and Detox, Android APK and
  instrumentation APK builds, Ruff/Black/Prettier checks, and MkDocs
  preparation/build. Desktop package-wide TypeScript checking reaches only
  pre-existing URL, attachment-plugin-ID, and theme-shadow errors after the new
  harness error was fixed.
- September 4, 2026: native verification completed. The focused macOS XCUITest
  passes discovered model selection, custom model entry, reset, header toggle,
  and composer list-action state through production controls. The final iOS
  and Android Detox binaries pass the same model/action scenario. Android
  required a clean AVD boot with 4 CPU cores, 4 GB RAM, software rendering,
  nonessential Play Store services disabled, and preinstalled APK reuse; the
  earlier failures were AVD resource/system-service failures rather than
  product assertions.

## Completion Notes

Completed September 4, 2026.

The portable rich-session UI contract is implemented across provider emission,
shared frontend normalization/components, mobile, and desktop. Anthropic,
OpenRouter, OpenRouter Responses, and OpenAI Responses expose model selection
through one ordinary config element with optional compact rich presentation;
the mobile-only model-picker contract is removed. Mobile and desktop support
discovered values, arbitrary string model IDs, ordinary override/reset
semantics, persistent pinning, and rich session actions in the session header
or composer.

Requirement evidence:

- provider, template, and default-config tests verify dropdown-or-text model
  emission, manual entry, rich UI, and removal of `model_picker`;
- shared SDK, React binding, and React Native component suites verify
  normalization, placement, action reuse, settings mutation, and rendering;
- the real HTTP application plus `RestAgentBackend` integration verifies
  Anthropic discovery and select/custom/reset mutations at the public boundary;
- full mobile and desktop Jest suites pass;
- final iOS and Android release/E2E binaries pass the focused Detox scenario;
- the focused macOS XCUITest passes native popovers, custom entry, reset, and
  placed rich actions;
- documentation preparation and MkDocs build pass with existing repository
  warnings.

Implementation findings and deviations:

- mobile compact controls use the established options picker as an inline chat
  overlay because transparent native modals did not reliably receive
  synchronized simulator input from the production polling screen;
- custom mobile entry uses an explicit keyboard-aware Done submission path;
- toggle controls expose `On`/`Off` in their accessibility label because
  React Native macOS does not expose `accessibilityState.selected` through
  `XCUIElement.isSelected`;
- the existing iOS fmt post-install compatibility hook now makes its generated
  read-only header owner-writable before patching it, allowing the documented
  CocoaPods workflow to complete.

No task-022 behavior remains unresolved. Desktop package-wide TypeScript
checking still reports the unrelated pre-existing URL, attachment-plugin-ID,
and theme-shadow errors recorded in the implementation notes.

## Post-completion follow-up

- September 4, 2026: completed the previously pending native verification.
  The desktop harness now propagates backend summary changes into the
  production `ChatPane`; rich toggles expose explicit `On`/`Off`
  accessibility labels; and the mobile custom-model test explicitly focuses
  and submits the keyboard-aware input. Final rebuilt iOS and Android binaries
  pass Detox, and the focused macOS XCUITest passes all model and placed-action
  assertions.
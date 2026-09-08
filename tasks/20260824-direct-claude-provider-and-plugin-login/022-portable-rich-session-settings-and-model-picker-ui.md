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
4. `rich_ui` is self-contained for its compact presentation and repeats
   `label`, `options`, `allow_custom_value`, placeholder/help text, pinning,
   and placements as applicable. The containing config element owns the
   ordinary/fallback `label` and `icon`.
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
  "icon": "cpu",
  "options": [
    {"value": "claude-sonnet-5", "label": "Claude Sonnet 5"}
  ],
  "allow_custom_value": true,
  "rich_ui": {
    "kind": "dropdown",
    "placements": ["composer"],
    "default_pinned": true,
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
  "icon": "cpu",
  "rich_ui": {
    "kind": "dropdown",
    "placements": ["composer"],
    "default_pinned": true,
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
- Decision: rich UI repeats its compact label, options, custom-entry text, and
  appearance fields. The ordinary action-menu and non-rich fallback label and
  icon come from the containing config element.
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
- September 4, 2026: reopened this task for a correction to the custom-value
  dropdown interaction. The correction remains part of task 022 rather than a
  new subtask.
- September 4, 2026: the user approved the unified custom-value field,
  empty-catalog dropdown behavior, and native macOS `MacComboBox` direction,
  then expanded the correction to compact presentation, reasoning and web
  search controls, two-row pinned actions, and mobile composer controls. The
  combined expanded plan remains Draft pending approval.
- September 5, 2026: the user clarified that the composer must enable the
  two-row pinned-action mode, request Cancel belongs beside the composer in a
  vertical stack with Send, and the mobile composer needs a maximized editing
  mode suitable for iOS three-finger text-editing gestures.
- September 5, 2026: the user approved the expanded follow-up with Cancel above
  Send in the mobile side stack and added the session-status rich selector to
  chat session actions. Follow-up execution started.
- September 6, 2026: the user corrected an implementation overreach.
  Reasoning-effort migration is limited to Anthropic, Anthropic uses uniform
  option presentation, `request_options_ui` remains unchanged, and semantic
  option icon/tone testing moves to the opt-in
  `plugins/dummy-rich-config-ui` package for automated and physical-device
  validation.
- September 6, 2026: the corrected scope is implemented. The default
  configuration, `feature-request-options`, OpenRouter reasoning, and OpenAI
  Responses reasoning have no task-022 diff. `dummy-rich-config-ui` is a
  normal disabled-by-default feature package with documented
  `enabled_plugins` activation. Final automated evidence includes 27 unchanged
  request-options tests, 30 OpenRouter reasoning tests, 86 OpenAI Responses
  reasoning tests, 17 Anthropic reasoning-control tests, 2 dummy-plugin tests,
  331 frontend SDK tests, 51 shared React Native component tests, 168 mobile
  tests plus type checking, 139 desktop tests, the real HTTP frontend
  integration, successful macOS/iOS/Android builds, passing iOS and Android
  Detox, passing focused macOS XCUITest, and successful documentation
  preparation/build. Human confirmation of the iOS three-finger system gesture
  remains open.
- September 6, 2026: verification gaps for dropdown edge cases, native
  `MacComboBox`, semantic option appearance, and the real dummy plugin were
  closed. SDK coverage now explicitly verifies empty queries, malformed custom
  labels, absent-pattern semantics, and trimmed exact matching. Component tests
  assert every dummy option icon against all six semantic theme colors plus
  fallback and disabled-muted behavior. A real-backend mobile component
  integration loads `dummy-rich-config-ui` through HTTP into the production
  `SessionChatScreen` and verifies dropdown and toggle overrides. The macOS
  `MacComboBox` uses the standard separate input, selection, and submit event
  callbacks; its XCUITest opens full Session Settings, verifies the actual
  AppKit `ComboBox`, selects a declared value and a synthetic custom value,
  rejects an invalid value, observes backend mutation, and resets the
  override. Final regression evidence is 335 frontend SDK tests, 51 shared
  React Native component tests, 175 mobile tests plus type checking, the real
  dummy-plugin backend integration, 139 desktop tests, and all 6 macOS
  `SessionFiltersPopoverUITests`. Native diagnostics confirmed the standard
  AppKit selection callback and React event block were working; the initial
  failure incorrectly asserted immediate refresh in a separate ChatPane
  settings controller instead of the backend mutation owned by the full
  settings window.
- September 6, 2026: the user completed the remaining manual test and
  confirmed the maximized mobile editor supports the intended native editing
  interaction. The follow-up requirements are complete.
- September 6, 2026: applied post-completion visual and interaction
  corrections without reopening requirements. Two-row action bars now retain
  one-row height until wrapping is necessary, the desktop composer bar
  stretches and aligns its pins to the right, and rich controls have compact
  horizontal spacing. Ordinary action popovers project rich state as neutral
  text and keep toggle rows one-click, while pinned controls retain rich
  colors and icons. OpenRouter, OpenRouter Responses, and OpenAI Responses now
  expose text-only reasoning-effort rich dropdowns whose option labels equal
  their values. Directly pressed rich list controls pass their own native
  event target as the desktop popover anchor, overriding any stale remembered
  menu anchor. Verification passed with 336 frontend SDK tests, 51 shared
  React Native component tests, 177 mobile tests plus type checking, 142
  desktop tests, 31 OpenRouter reasoning tests, 6 OpenRouter Responses
  reasoning tests, 86 OpenAI Responses reasoning tests, focused default-config
  smoke tests, and Python lint checks. No Detox or XCTest was run for these
  small corrections.
- September 7, 2026: corrected the ordinary-versus-rich presentation
  boundary without reopening requirements. Known rich config elements now
  declare their fallback label and icon on the containing config element.
  Normal action menus use only those outer fields on the left and show the
  selected rich option as neutral state text on the right. Compact controls
  use a selected option icon when present, otherwise the outer icon, while
  `rich_ui.show_icon: false` preserves text-only pinned controls such as
  reasoning effort. Action-menu title and state text shrink and ellipsize
  adaptively so a short title leaves the remaining width to a long value,
  while accessibility retains the complete strings. Verification passed with
  337 frontend SDK tests, 51 shared React Native component tests, 179 mobile
  tests plus mobile TypeScript checking, 142 desktop tests, the public
  Anthropic-rich-UI HTTP/backend integration, and focused UI declaration tests
  for every migrated provider/tool plugin and the provider template. The
  desktop repository-wide TypeScript check remains blocked by unrelated
  pre-existing URL, declaration-order, attachment typing, and theme errors.

### Follow-up completion notes

Completed September 6, 2026.

The corrected custom-value dropdown, rich configuration controls, native
desktop combobox, two-row composer actions, mobile composer controls,
maximized editor, session-status chat action, and opt-in dummy rich UI plugin
are implemented and verified. Automated evidence includes package and
component suites, real HTTP/backend integrations, iOS and Android Detox, and
the complete macOS native UI suite. Human verification confirmed the remaining
native mobile editing interaction. Later visual refinements requested after
this completion are recorded as implementation follow-up rather than reopening
the completed requirements.

### Follow-up requirements checklist

- [x] A custom-capable dropdown uses one text field for both filtering
  declared options and entering a new value; no separate custom-value field or
  submit section remains.
- [x] Plugins control the shared input placeholder so it can describe both
  search and custom-entry behavior.
- [x] Custom-value configuration is nested under `custom_value`, with
  `enabled`, `pattern`, and `option_label` fields, and is repeated inside
  self-contained `rich_ui`.
- [x] A non-empty query that does not exactly match a declared option and
  satisfies the plugin pattern produces a synthetic selectable option whose
  text is rendered from the plugin-provided label template.
- [x] Invalid or non-matching custom candidates cannot be submitted, while
  declared dropdown options remain usable.
- [x] Anthropic and all providers migrated by task 022 emit the corrected
  nested contract without the superseded flat custom-value fields.
- [x] Mobile, desktop, full Session Settings, and compact chat dropdowns share
  the same query, validation, suggestion, selection, and reset semantics.
- [x] The pinned model selector omits the visual `Model:` prefix, truncates its
  displayed value to a host-configured character limit, and retains the full
  label and value for accessibility.
- [x] Rich dropdown and toggle options support a theme-aware semantic `tone`
  and an icon, and the selected option controls the pinned presentation.
- [x] Anthropic reasoning effort is available as a simple rich composer
  dropdown with uniform option presentation.
- [x] An opt-in `dummy-rich-config-ui` plugin exposes per-option icon/tone,
  toggle, placement, pinning, and disabled-state controls for automated and
  physical-device testing without changing production provider contracts.
- [x] Web search enablement is available as a rich composer toggle for the
  applicable first-party provider extensions and tool plugins.
- [x] The shared pinned-actions component supports an explicitly enabled
  second row above or below the primary row, packs leftover controls from the
  right, and preserves its existing one-row behavior by default.
- [x] The composer explicitly enables two-row pinned actions with its second
  row below the primary row.
- [x] The mobile composer displays Append and Resend in the action area and
  places icon-only Send and request-Cancel controls in a vertical stack to the
  input's right, with Cancel above Send.
- [x] The mobile input has a maximize affordance that opens a full-screen
  editor backed by the same draft and attachments, supports normal native iOS
  text-editing gestures, and can collapse without discarding changes.
- [x] Mobile Resend uses the same `repeat` icon as desktop.
- [x] The session-status application plugin contributes its existing status
  selector to chat session actions, reusing the same action, metadata path,
  options, rich list, and fallback form as its session-list action.
- [x] Public authoring docs, portable/provider specifications, and frontend
  development docs describe the corrected contract and its verification.

### Follow-up execution plan

Status: Approved

Correct the existing custom-value dropdown rather than layering another
custom-entry UI onto it. The containing config element remains authoritative
for the setting key, effective value, session override, and reset. The ordinary
and rich dropdown declarations each own a self-contained presentation:

```json
{
  "ui_type": "config",
  "type": "dropdown",
  "key": "model",
  "label": "Model",
  "icon": "cpu",
  "options": [
    {"value": "claude-sonnet-5", "label": "Claude Sonnet 5"}
  ],
  "placeholder": "Search models or enter a model ID",
  "custom_value": {
    "enabled": true,
    "pattern": "^[^\\s]+$",
    "option_label": "Use '{value}' as a custom model ID"
  },
  "rich_ui": {
    "kind": "dropdown",
    "label": "Model",
    "show_label": false,
    "options": [
      {"value": "claude-sonnet-5", "label": "Claude Sonnet 5"}
    ],
    "placeholder": "Search models or enter a model ID",
    "custom_value": {
      "enabled": true,
      "pattern": "^[^\\s]+$",
      "option_label": "Use '{value}' as a custom model ID"
    },
    "placements": ["composer"],
    "default_pinned": true
  }
}
```

The shared input filters option labels and values case-insensitively. Its
trimmed query becomes a custom candidate only when it is non-empty, does not
exactly equal a declared option value, and fully matches
`custom_value.pattern`. Matching declared options remain first; a visually
distinct synthetic custom option follows them. Selecting that row performs the
ordinary config override mutation. Enter/Done selects an exact declared value
when present, otherwise the valid synthetic option, and otherwise performs no
mutation.

Add one pure frontend SDK derivation helper that accepts the dropdown
declaration and query and returns filtered declared options, an optional
synthetic custom option, and diagnostics. Compile the pattern once per
declaration. An invalid pattern or malformed option-label template disables
the custom suggestion with a diagnostic but does not discard the declared
options or the entire dropdown.

Use the shared derivation in:

- the mobile options picker used by full Session Settings and compact chat;
- the shared React Native rich dropdown panel used by desktop chat popovers;
- desktop full Session Settings.

The current desktop `MacSelect` wraps `NSPopUpButton` and cannot accept typed
search. Add a separate `MacComboBox` backed by `NSComboBox` for custom-capable
dropdowns. JavaScript remains responsible for filtering, pattern matching, and
synthetic-option derivation; the native component owns text entry, native menu
presentation, focus, and selection events. Non-custom ordinary dropdowns
continue using `MacSelect`.

Compact config presentation gains one optional `show_label` field. It defaults
to `true`; model, reasoning-effort, and web-search composer controls set it to
`false`. Omitting the visual prefix does not change accessibility labels. Add a
`maxValueCharacters` renderer prop to compact config controls and truncate
only the visual selected-option label, using an ellipsis while preserving the
full value in the picker and accessibility tree. The initial host limits are
24 characters on desktop and 16 characters on mobile.

Make option appearance portable and shared across rich config dropdowns,
config toggles, session status, and their selection lists:

```json
{
  "value": "high",
  "label": "High",
  "icon": "chevron-up",
  "tone": "highlight"
}
```

`tone` continues to use the theme-aware semantic vocabulary `primary`,
`highlight`, `warning`, `success`, `danger`, and `muted`; plugins do not send
raw colors. A selected option's icon and tone take precedence over the
containing config element's ordinary icon and the primary tone in compact
presentation. A disabled control always uses the muted/gray tone while
retaining the selected option's icon. Validate rich
dropdown tones against the same vocabulary already used by session status,
render option tone and icon in both the pinned control and picker, and add
icons to the built-in session-status options as the cross-feature reference
consumer.

Add an opt-in `plugins/dummy-rich-config-ui` feature package for deliberate
manual and automated presentation testing. It is disabled by default and
becomes active through the ordinary `enabled_plugins` configuration. It
provides a dropdown covering every semantic tone with distinct icons, a rich
Boolean composer toggle, and a disabled session-header toggle. These controls
mutate ordinary session overrides and never change provider requests.

Add an ordinary-config `rich_ui.kind: "toggle"` for Boolean checkbox settings:

```json
{
  "type": "checkbox",
  "key": "enable_web_search",
  "label": "Enable web search",
  "icon": "globe",
  "rich_ui": {
    "kind": "toggle",
    "label": "Web search",
    "show_label": false,
    "placements": ["composer"],
    "default_pinned": true,
    "options": [
      {
        "value": false,
        "label": "Off",
        "icon": "globe",
        "tone": "primary"
      },
      {
        "value": true,
        "label": "On",
        "icon": "globe",
        "tone": "success"
      }
    ]
  }
}
```

A config toggle requires exactly one `false` and one `true` option. Plugin
options may override their icons and tones. Defaults are muted/gray while the
control is disabled, primary/blue when false, and success/green when true.
Selecting a pinned toggle immediately patches the ordinary Boolean session
override; the normal Session Settings checkbox remains the fallback and reset
surface.

Add simple rich composer presentation only to the existing reasoning-effort
setting owned by `AnthropicReasoningControlsExtension`. Its model-dependent
option list remains authoritative. Options retain ordinary value/label data
without production icon or tone differences. Do not change OpenRouter,
OpenAI Responses, compatible-provider defaults, or the `request_options_ui`
contract in this task.

Add rich web-search toggles to the first-party plugins that currently own
`enable_web_search` or `web_search_enabled`: OpenRouter web search, OpenAI
Responses web search, Claude WebSearch, Gemini web search, and Kimi web search.
The Claude tool gains an ordinary config UI element because it currently owns
the setting but exposes no UI. A plugin that has no configured search backend
keeps its ordinary control disabled, which renders the compact toggle gray.

Extend `session-status-app` with a chat `session_action` declaration in
addition to its existing `session_list_action`. Both declarations reuse
`set_session_status`, the configured metadata key, the same fallback select
form, and the same rich status options. The chat declaration uses
`rich_ui.kind: "list"` with `placements: ["session_header"]`; it is available
in the ordinary session-actions menu and may be pinned in the session header.
No second mutation implementation or status storage path is introduced.

Route rich config controls through `ActionsMenuBar`'s existing
`renderPinnedAction` path instead of rendering them in a separate composer
container. Extend the shared component with:

```typescript
pinnedRows?: 1 | 2;
secondPinnedRowPlacement?: "above" | "below";
```

The default remains one row. With two rows, the component measures the
available width and compact control widths, fills the primary row in resolved
action order, and places the remaining controls in the second row in the same
order. Both rows are right-aligned. The overflow-menu button remains at the
far right of the primary row. Controls that do not fit within two rows remain
available in the ordinary menu but are not rendered as compact pins.
`secondPinnedRowPlacement` controls whether the leftover row is rendered above
or below the primary row.

The composer passes `pinnedRows={2}` and
`secondPinnedRowPlacement="below"`. Order the default compact config controls
before the built-in composer actions so Model, Reasoning, and Web Search occupy
the primary row when available, while Append and Resend form the right-aligned
lower row. Request Cancel moves out of the pinned row and into the input-side
button stack; its ordinary action remains available in the overflow menu.
`appendAs` also remains in the overflow menu. Existing stored pin choices
remain authoritative; defaults are applied only when no composer pin
preference exists.

On mobile, remove the separate full-width Append/Send button row. Add Append
to the default pinned composer actions, retain Resend, remove Cancel from the
default pinned set, and change Resend's icon from `rotate-ccw` to desktop's
`repeat`. Place two 44-by-44 icon buttons in a vertical stack to the right of
the text input: request `cancel` above and paper-plane `send` below, separated
by a 6-point gap. Cancel remains visible but disabled when no request is active
so the composer geometry does not jump. The input uses a 94-point minimum
height to match the two-button stack, grows to its existing maximum, and
bottom-aligns the stack when multiline content grows. Send loading uses the
existing spinner in the same button. The four built-in direct controls are
Append, Resend, Send, and Cancel; plugin-contributed settings and attachment
controls remain separate capabilities.

Add a small secondary `maximize-2` button inside the upper-right corner of the
mobile input frame, with sufficient input padding so text does not flow under
it. It is a host composer affordance, not a pinnable plugin action. Selecting
it opens a full-screen mobile editor using the same controlled draft state,
attachment state, save path, send path, and validation as the inline composer.
Do not copy the draft into a separate commit/cancel buffer.

The full-screen editor uses a native multiline `TextInput` inside a safe-area
and keyboard-aware full-screen modal. Its header has a `minimize-2` control
with the accessibility label `Collapse composer`, the title `Compose message`,
and the same paper-plane Send action. “Collapse” is used instead of “Cancel”
so it cannot be confused with request cancellation. Collapsing, interactive
dismissal, or returning to the inline composer preserves all edits. Sending
from the full-screen editor uses the ordinary atomic send path and closes the
expanded editor only after the request is accepted. Existing attachment strips
remain visible in compact form and participate in the same send.

The maximized editor is available on both iOS and Android for consistent
mobile behavior, while its primary acceptance case is iOS: the large native
text surface must permit the operating system's three-finger undo/redo editing
gestures. Automated tests cover shared-draft behavior, focus, collapse, and
send; actual three-finger gesture recognition requires a human simulator or
device confirmation because Detox does not synthesize that system gesture
reliably.

Migrate Anthropic, OpenRouter, OpenRouter Responses, OpenAI Responses, the
provider template, deterministic fixtures, and default-config expectations.
Remove `allow_custom_value`, `custom_value_label`, and
`custom_value_placeholder` from the corrected contract rather than retaining
compatibility aliases.

#### Implementation decisions and open questions

- Decision: this correction remains a post-completion follow-up in task 022.
- Decision: `placeholder` belongs at the dropdown presentation level because
  the one field serves both search and custom entry.
- Decision: custom behavior is configured by a nested `custom_value` object.
- Decision: `custom_value.option_label` supports the single interpolation
  token `{value}`.
- Decision: `custom_value.pattern` uses ECMAScript regex syntax and full-value
  matching; no separate flags are supported initially.
- Decision: an absent pattern permits any non-empty trimmed value, while the
  migrated model providers explicitly use `^[^\s]+$`.
- Decision: exact declared-value matching is case-sensitive; option filtering
  is case-insensitive.
- Decision: no backward-compatibility aliases are retained for the flat
  custom-value fields introduced by the initial task-022 implementation.
- Decision: the approved desktop implementation uses a separate native
  `MacComboBox` for custom-capable dropdowns and leaves `MacSelect` unchanged
  for ordinary fixed-option dropdowns.
- Decision: custom-enabled model selectors remain `type: "dropdown"` when
  discovery returns no options. An empty catalog still presents the unified
  field and synthetic custom option, eliminating the separate text-fallback
  path.
- Decision: compact option colors are semantic tones, not raw plugin-provided
  color values.
- Decision: the pinned model control sets `show_label: false`; desktop and
  mobile renderer props cap its visual value at 24 and 16 characters,
  respectively.
- Decision: config toggles use Boolean options with optional per-option icon
  and tone; disabled overrides the tone to muted, while the default false and
  true tones are primary and success.
- Decision: `request_options_ui`, OpenRouter reasoning, and OpenAI Responses
  reasoning remain unchanged; this task does not generalize Anthropic's
  reasoning control to other providers.
- Decision: semantic icon/tone permutations are exposed by the opt-in
  `dummy-rich-config-ui` plugin rather than production reasoning settings.
- Decision: the composer uses two pinned rows with its second row below, and
  compact overflow is right-aligned.
- Decision: the composer explicitly passes `pinnedRows={2}` and
  `secondPinnedRowPlacement="below"`.
- Decision: mobile's four direct composer controls are Append, Resend,
  icon-only Send, and icon-only request Cancel; Append as remains in overflow.
- Decision: Send and Cancel form a fixed vertical stack to the right of the
  mobile input, with Cancel above Send, and Cancel remains disabled rather than
  disappearing when no request is active.
- Decision: the inline input minimum height is 94 points to match two 44-point
  controls and their 6-point gap.
- Decision: use an in-frame `maximize-2` affordance
  and a shared-state full-screen editor with `minimize-2`/Collapse and Send in
  its header. This gives iOS a large native editing surface without introducing
  draft commit/discard semantics or another meaning of “Cancel.”
- Decision: the status plugin contributes a rich chat session action in the
  session header while retaining its existing session-list action.

#### Documentation

- Update `plugins/docs/ui-elements.md` with the nested contract, full-match
  regex semantics, `{value}` interpolation, synthetic-option ordering, and
  Enter/Done behavior.
- Update provider authoring and runtime-contract guidance to require the same
  model combobox behavior and empty-catalog handling.
- Revise PPI-015 and ANTH-019 plus their technical specifications to replace
  the flat custom fields and text fallback and to cover compact model and
  Anthropic reasoning presentation.
- Update shared frontend SDK, shared React Native component, mobile, and
  desktop development docs, including `MacComboBox` ownership and native event
  boundaries.
- Document config rich toggles, per-option icon/tone behavior,
  `show_label`, host character limits, two-row pinned-action props and packing,
  the mobile four-button composer layout, and maximized-editor behavior.
- Add package documentation and plugin-index guidance for enabling
  `dummy-rich-config-ui` on real devices.
- Update session-status documentation and examples when adding option icons.
- Document that session status is available from both session-list actions and
  chat session actions through one application action and metadata path.
- Update the owning Claude tools, Gemini tools, Kimi tools, OpenRouter, and
  OpenAI Responses documentation only for the web-search/model controls
  changed in this task.
- Update provider package documentation only where it currently shows the
  superseded task-022 custom-value shape.

#### Task checklist

- [x] Approve unified custom entry, empty-catalog dropdown behavior, and the
  native macOS combobox direction.
- [x] Approve the expanded compact appearance, reasoning/web-search controls,
  two-row pinned actions, and mobile composer plan.
- [x] Add nested contract types, normalization, diagnostics, and suggestion
  derivation to the frontend SDK.
- [x] Migrate provider emitters, templates, fixtures, and application
  expectations.
- [x] Replace separate custom-entry sections in shared and mobile pickers.
- [x] Add the desktop native `MacComboBox` and use it for custom-capable full
  settings dropdowns.
- [x] Add shared option appearance, `show_label`, visual truncation, and the
  config rich toggle renderer.
- [x] Add a simple Anthropic reasoning-effort composer dropdown and
  web-search composer toggles to their approved owning plugins.
- [x] Add the opt-in `dummy-rich-config-ui` package for semantic option
  appearance and real-device testing.
- [x] Add the session-status rich selector to chat session actions.
- [x] Add width-aware two-row pinned-action layout and route rich config
  controls through it.
- [x] Restructure the mobile composer, add the Send/Cancel side stack, and
  align the Resend icon with desktop.
- [x] Add the shared-state maximized mobile composer and its collapse/send
  lifecycle.
- [x] Update public docs, package specifications, and frontend development
  guidance.
- [x] Run deterministic, package, public-backend, iOS/Android Detox, and macOS
  XCUITest verification; request separate user confirmation before starting
  the new desktop XCUITest run.
- [x] Update requirement evidence.
- [x] Append immutable follow-up completion notes after the remaining human
  iOS gesture confirmation.

#### Requirement verification

- Frontend SDK tests prove case-insensitive filtering, exact-value
  suppression, full-match validation, empty-query behavior, malformed-pattern
  degradation, `{value}` interpolation, synthetic-option ordering, and
  Enter/Done selection.
- Provider tests prove the outer and rich declarations repeat the nested
  custom-value object and no superseded flat fields remain.
- Mobile and desktop component tests prove one input drives both search and
  custom selection, invalid candidates have no custom row, valid candidates
  mutate the ordinary override, and reset remains unchanged.
- Shared component tests prove selected-option icons and tones, label
  suppression, host-specific truncation, full accessibility text, config
  toggle defaults/overrides, and disabled muted presentation.
- Pinned-action tests prove one-row compatibility, both second-row placements,
  width-aware right-aligned packing, stable order, primary-row overflow-menu
  anchoring, and fallback of excess pins to the ordinary menu.
- Plugin tests prove Anthropic's model-dependent reasoning options use a
  uniform self-contained rich UI, web-search Boolean settings emit rich
  toggles, and the dummy plugin covers semantic option icons/tones without
  provider request changes.
- Session-status tests prove the list and chat declarations share one action,
  configured metadata path, option set, fallback form, and rich-list
  semantics.
- The public HTTP/`RestAgentBackend` integration proves discovered selection,
  custom synthetic selection, dummy rich-control declaration, status action,
  invalid-candidate rejection, reload, and reset.
- Mobile tests prove Append and Resend occupy the pinned action area while
  Send and Cancel occupy a stable right-side vertical stack, including active
  and inactive request states, Cancel-above-Send order, aligned input/button
  heights, and the `repeat` Resend icon.
- Maximized-composer tests prove the inline and full-screen editors share one
  draft, attachments and validation remain effective, collapse preserves
  edits, accepted send closes the editor, failed send keeps it open, and
  accessibility labels distinguish Collapse from request Cancel.
- Native tests prove the same production settings flows and composer layout
  through iOS and Android Detox and, after user confirmation, the macOS
  popover XCUITest. A dedicated full-settings XCUITest proves the custom model
  control is an AppKit `NSComboBox`, declared and synthetic values mutate the
  backend, invalid values are not offered, and reset removes the override.
- The real-backend mobile component integration proves the normal plugin
  loader, public HTTP backend, production `SessionChatScreen`, rich dropdown
  and toggle renderers, and session-override persistence work together for
  `dummy-rich-config-ui`.
- Human iOS simulator or device verification confirms that the maximized
  native text surface accepts the system three-finger undo/redo gestures.

#### Additional implementation verification

- Verify custom values already selected but absent from a later discovery
  response remain visible and editable.
- Verify a query equal to a declared value never creates a duplicate synthetic
  row.
- Verify invalid plugin regex disables only custom entry and emits an
  inspectable diagnostic.
- Verify selected option appearance falls back cleanly when icon or tone is
  absent and that invalid tones produce diagnostics without discarding the
  ordinary setting.
- Verify the session-status plugin displays its newly declared option icons in
  list and pinned presentations and exposes the same selector in chat session
  actions.
- Verify an unavailable web-search backend leaves the toggle visible but
  disabled and muted.
- Verify two-row packing remains stable with variable-width rich controls,
  narrow mobile widths, hidden labels, and truncated model IDs.
- Verify the composer actually enables the two-row props rather than merely
  supporting them in the shared component.
- Verify Cancel stays in the side stack and does not also consume a default
  pinned slot.
- Verify maximized and inline editing do not race draft persistence during
  focus changes, modal presentation, collapse, or send completion.
- Verify stored pin preferences are not overwritten when new default-pinned
  Anthropic reasoning, dummy, or web-search controls become available.
- Verify keyboard focus, Enter/Done submission, popup refresh, and
  accessibility labels on all three frontend platforms.
- Re-run full frontend SDK, React binding, shared component, mobile, desktop,
  provider, application, documentation, and formatting/type checks.

## Post-completion follow-up

### Request progress and concurrent chat actions

Status: Approved

Restore a visible full-lifecycle request indicator in the Send control and
remove the frontend assumption that an active model request is a global chat
action lock. Execution waits for explicit user confirmation.

Mobile shows the existing Send spinner, and desktop replaces its temporary
`…` text with an `ActivityIndicator`, while either request submission is
pending or `activeRequestId` is present. Inline and maximized mobile composers
use the same state. The Send control keeps stable dimensions and exposes busy
state through accessibility. Existing session-level request indicators remain
complementary rather than becoming the only progress indication.

Replace broad disable predicates with action-specific eligibility. An active
request continues to disable Send and Resend and enables Cancel, but does not
by itself disable:

- model, reasoning, web-search, or other ordinary/rich config settings;
- ordinary or rich session/application actions;
- attachment selection, drafting, metadata editing, or management;
- Append or Append as;
- reload or other unrelated session actions.

The server remains authoritative for accepting or rejecting each concurrent
action or setting mutation. Frontends invoke the existing backend path and
show its normal error when the server rejects the operation. Configuration
changes made during a running response apply to a subsequent request unless
the server explicitly defines different behavior.

The current mobile `sendInProgress` and desktop `sendInFlight` flags cover
multiple operation types. Refine them into an operation identity or equivalent
action-specific state so allowing unrelated work during Send does not permit a
duplicate Append, Resend, attachment mutation, or other operation against the
same local resource. Offline/read-only state, an element's declared disabled
state, unresolved attachment data, and an already-running operation against
the same local resource remain valid frontend constraints.

No governing provider specification changes for this follow-up. The portable
provider specification is limited to provider-plugin implementation and
authoring requirements. The Sessions-actions specification governs the
top-level Sessions surface rather than chat-composer concurrency. This
frontend behavior therefore remains owned by this task and current-behavior
frontend documentation.

#### Implementation decisions and open questions

- Decision: use the Send spinner as the primary immediate progress indicator
  and retain existing session-level request status.
- Decision: active request state is not a global disabled condition.
- Decision: request start, cancel, append, attachment, config, and plugin
  actions receive separate local eligibility checks.
- Decision: backend rejection remains the concurrency authority.
- Open question: none; implementation is pending user confirmation.

#### Documentation

- After implementation, update
  `packages/frontend-sdk/docs/development/rich-session-ui.md` with backend
  authority and concurrent config/action behavior.
- Update
  `packages/frontend-rn-components/docs/development/actions-menu-components.md`
  with action-specific disablement and busy presentation.
- Update mobile and desktop development guidance for their request-progress
  and composer-operation state.
- Do not add this platform behavior to provider authoring documentation or the
  portable provider specification.

#### Task checklist

- [x] Obtain explicit approval to begin this follow-up.
- [x] Refine mobile and desktop operation state and action-specific disable
  predicates.
- [x] Restore full-lifecycle Send progress on inline mobile, maximized mobile,
  and desktop.
- [x] Keep unrelated settings, rich controls, plugin actions, attachments,
  Append, and reload invokable during an active request.
- [x] Update current-behavior frontend documentation.
- [x] Run focused and package regression tests.

#### Requirement verification

- Mobile and desktop tests prove request submission and `activeRequestId` both
  keep the Send control busy until the active request clears.
- With an active request, tests prove Send and Resend are disabled, Cancel is
  enabled, and representative model/reasoning/web settings plus a plugin
  action remain enabled and invoke their existing backend paths.
- Tests prove Append and attachment drafting are not disabled merely by the
  active request, while duplicate operations against the same local resource
  remain blocked.
- A backend-rejection test proves an eligible concurrent mutation reaches the
  backend and its normal error is surfaced instead of being preemptively
  suppressed by the frontend.

#### Additional implementation verification

- Verify a config change during streaming does not rewrite the already-created
  request and is available to the next request.
- Verify pending-send recovery does not become an accidental global UI lock.
- Verify spinner, disabled, cancel, and accessibility states during request
  submission, streaming, cancellation, failure, and completion.
- Run frontend SDK/shared-component tests, full mobile and desktop component
  suites, mobile TypeScript, and the existing public-backend rich-UI
  integration. No Detox or XCUITest is planned unless component verification
  exposes native-only behavior.

#### Completion notes

Completed September 7, 2026.

Mobile and desktop now render Send as busy through both request submission and
the complete `activeRequestId` lifetime. Mobile inline and maximized composers
share the same spinner state; desktop uses an `ActivityIndicator` instead of
the temporary ellipsis. Both Send controls expose accessibility busy state.

Append has separate local in-flight state from request start. Active request
state continues to gate Send/Resend and enable Cancel, but no longer disables
rich config controls, session/application actions, attachment drafting,
Append/Append as, or reload. Explicit plugin disabled state, offline/read-only
state, unresolved attachment data, and duplicate operations against the same
local resource remain enforced. Concurrent config and action mutations use
their existing backend paths, leaving acceptance or rejection to the server.

Frontend development documentation records the delivered behavior. No
portable-provider, provider-package, provider-authoring, or Sessions-actions
specification was changed because chat concurrency is outside those document
scopes.

Verification passed with 337 frontend SDK tests, 51 shared React Native
component tests, 180 mobile tests plus mobile TypeScript checking, 143 desktop
tests, and the public Anthropic-rich-UI HTTP/backend integration. The active
request production-screen tests assert full-lifecycle Send progress and prove
that model/web config, session action, Append, and attachment controls remain
enabled. Existing SDK controller coverage proves rejected config mutations
reach the backend, roll back optimistic state, and expose the backend error.
The desktop repository-wide TypeScript command remains blocked only by the
previously recorded URL typing, declaration-order, attachment typing, and
theme errors; no new error category was introduced. No Detox or XCUITest was
run because the change has no native-only interaction.

September 7, 2026 correction: custom pinned controls now occupy the same
40-point vertical action slot as simple icon actions, keeping rich toggles
aligned with the ellipsis even when Resend wraps to another row. On mobile,
request Cancel remains permanently above Send beside the composer and is
removed from Composer actions. Composer actions retain Resend, Append, and
Append as; the top Session actions now also expose Resend and request Cancel
through the existing handlers. The focused iOS rich-session Detox scenario
passes permanent action-placement coverage. A temporary Detox screenshot and
frame-center check verified the Web-search toggle/ellipsis alignment and were
removed after verification.

September 7, 2026 correction: ordinary `type: "dropdown"` config elements now
enable unrestricted custom values by default when outer `custom_value` is
absent. An explicit outer declaration is needed only to disable custom entry,
constrain it with a full-match pattern, or customize the synthetic-option
label. Rich dropdown metadata remains self-contained and repeats
`custom_value` when its compact control should also accept custom values. This
keeps ordinary provider dropdowns custom-capable without turning fixed-choice
rich controls such as reasoning effort into free-form fields.

## Post-completion follow-up

### Reference OpenAI-compatible model and request-options composer controls

Status: Draft

Migrate the reference OpenAI-compatible provider to the standard rich model
selector and add an opt-in fixed-choice rich descriptor to
`request_options_ui`. This follow-up targets the
[request options UI specification](../../plugins/feature-request-options/docs/development/specifications/request-options-ui/index.md)
and requirements `ROUI-006` through `ROUI-014`. Implementation must not begin
until the user reviews these planning and specification files and explicitly
approves execution.

The provider-owned model element becomes one custom-capable `dropdown` even
when discovery returns no models. It includes the ordinary `cpu` fallback icon
and a self-contained rich dropdown placed and pinned around the composer. The
ordinary dropdown relies on the platform default that permits unrestricted
custom values when outer `custom_value` is absent. The self-contained rich
dropdown explicitly enables unrestricted custom model IDs and supplies its
synthetic-option label.

The request-options feature retains every existing shorthand and adds this
fixed-choice leaf descriptor:

```json
"reasoning_effort": {
  "type": "select",
  "options": ["high", "max"],
  "rich_ui": true
}
```

`type: "select"` distinguishes the descriptor from a nested subtree.
`rich_ui: true` expands to the standard text-only composer dropdown with a
static ordinary `sliders` fallback icon, copied label and options,
`placements: ["composer"]`, `default_pinned: true`, `show_label: false`, and
`show_icon: false`. It does not enable custom values, tones, or per-option
icons. The generated flat override key, nested `config_path`, default
resolution, deep merge, and request injection remain unchanged.

The descriptor works at nested request-option paths. The initial contract does
not support rich numeric, text, or boolean controls or configurable rich
appearance. A future extension may allow `rich_ui` to accept an object while
retaining `true` as the concise default, but that is outside this follow-up.

Representative Fireworks and Ollama configurations will replace only the
existing reasoning-effort array shorthand with the descriptor. Temperature,
top-p, seed, reasoning-history, and other request-option controls remain
ordinary Session Settings elements. Repository implementation does not edit
the user's home config; after verification, equivalent copyable configuration
can be applied there separately.

#### Implementation decisions and open questions

- Decision: the reference provider owns model discovery and its ordinary/rich
  model UI.
- Decision: `feature-request-options` owns reasoning-effort UI generated from
  `request_options_ui` and continues to own flat-key inflation and request
  injection.
- Decision: descriptor fields are ordinary plugin configuration and therefore
  do not use dollar-prefixed names.
- Decision: the initial descriptor supports only `type: "select"`,
  non-empty string `options`, and optional `rich_ui: true`.
- Decision: `rich_ui: true` has one fixed composer presentation and does not
  introduce a second mutation or persistence path.
- Decision: existing array and primitive shorthand forms remain supported
  without output changes.
- Open question: none; execution awaits review and explicit approval.

#### Documentation

- The target contract is defined by the package-owned
  [product specification](../../plugins/feature-request-options/docs/development/specifications/request-options-ui/product-spec.md)
  and
  [requirements](../../plugins/feature-request-options/docs/development/specifications/request-options-ui/requirements.md).
- After implementation, update
  `plugins/feature-request-options/README.md` with the delivered descriptor and
  generated rich presentation.
- Update the reference OpenAI-compatible provider README with its delivered
  model discovery, manual-entry, and composer-selector behavior.
- Review shared plugin UI authoring guidance only for a concise current
  example; do not duplicate the request-options package contract there.

#### Task checklist

- [x] Record the approved design as a Draft follow-up for review.
- [x] Create the request-options UI product specification and requirements.
- [ ] Obtain explicit approval to begin implementation.
- [ ] Add fixed-choice descriptor parsing and generated rich UI.
- [ ] Migrate the reference provider model element to the standard rich
  dropdown.
- [ ] Update representative default/example Fireworks and Ollama
  configurations.
- [ ] Update current package and provider documentation.
- [ ] Run focused, package, integration, and frontend verification.

#### Requirement verification

- `ROUI-006` and `ROUI-007`: deterministic feature tests compare descriptor
  output with existing shorthand output and reject malformed descriptors
  without losing valid siblings.
- `ROUI-008` and `ROUI-009`: deterministic schema tests assert the exact
  ordinary fallback and self-contained text-only composer declaration, then
  validate it through the shared frontend SDK normalizer.
- `ROUI-010`: nested descriptor and full-flow tests prove the selected value
  reaches the same nested provider request payload without replacing sibling
  fields.
- `ROUI-011`: the complete existing request-options unit suite remains green.
- `ROUI-012`: mobile and desktop production-screen tests render and mutate the
  generated reasoning-effort control through the standard rich-UI path.
- `ROUI-014`: malformed and unsupported descriptors are ignored while valid
  sibling shorthand and descriptor elements remain available.
- Reference-provider model tests cover discovery results, empty discovery,
  unrestricted custom IDs, and exact ordinary/rich schema output.
- Default-config or realistic application integration proves representative
  Fireworks and Ollama agents expose both model and reasoning-effort composer
  controls.
- `ROUI-013`: documentation review checks package examples against generated
  schemas and focused tests.

#### Additional implementation verification

- Run the complete `feature-request-options` unit suite.
- Run focused reference OpenAI-compatible model UI tests and the package's
  default non-API suite, reporting unrelated baseline failures separately.
- Run frontend SDK rich-UI tests, focused mobile and desktop component tests,
  and mobile TypeScript checking.
- Run a realistic application/default-config schema integration without
  requiring a paid model response.
- No Detox or XCUITest is planned unless component verification exposes
  native-only behavior.

# Move The Embedded Runtime To Python-Owned Config And Restore Plugin Parity

Replace the duplicated Swift/Python embedded-agent graph with a reviewable
Python-application-owned JSON configuration, restore the useful default
plugins, correct the legacy Reviewer/Qwen seam, and make the on-device settings
behavior consistent without finalizing unapproved product names.

## Requirements checklist

- [ ] The embedded runtime's providers, agents, plugins, application settings,
  and mixins are maintained in a JSON configuration under the Python
  application rather than reconstructed independently in the mobile app.
- [ ] Native/mobile settings supply URLs, models, workspace paths,
  authentication mode, credential paths or values, reviewer visibility, and
  other mutable values through explicit env-like placeholder overrides.
- [ ] API keys and ChatGPT credentials remain outside the maintained JSON;
  secrets stay in Keychain or the plugin-owned credential store and are not
  persisted into generated configuration files.
- [ ] The embedded runtime includes the useful, iOS-feasible default-config
  plugins, including system message, request options, timestamp/duration,
  summarize range, rebuild native history, and cost tracking. Omitted default
  plugins have documented compatibility or product reasons.
- [ ] A global on-device setting controls Reviewer visibility. Reviewer is
  absent from ordinary settings and agent selection while disabled and appears
  at the bottom when enabled.
- [ ] Reviewer deployment URL, model, and CA path are fixed by the maintained
  config and hidden from the on-device form; only its caller API key is
  editable.
- [ ] Every edit in the on-device provider form is persisted without requiring
  a separate Save action, with clear saving, saved, and error states.
- [ ] OpenAI API-key versus ChatGPT authentication is controlled only from the
  on-device provider settings. The corresponding ordinary plugin/session
  setting is hidden or disabled for embedded agents and cannot override the
  saved global choice.
- [ ] The embedded ChatGPT integration remains plugin-driven and may use an
  embedded-specific plugin variant to customize UI schema/actions without
  changing the ordinary OpenAI Responses or ChatGPT plugin behavior.
- [ ] The built-in connection and session creation use and display the actual
  selected profile; legacy generic-compatible aliases or the old connection
  wizard cannot silently display or activate Qwen when Reviewer is selected.
- [ ] Consumer-facing connection labels, profile/agent display names, profile
  ordering outside the settled Reviewer-last rule, default profile, and
  smoke-agent exposure remain explicitly provisional until user approval.
- [ ] Existing local sessions, provider credentials, Reviewer, direct OpenAI,
  OpenRouter, Anthropic, and generic compatible flows remain compatible across
  configuration migration and relaunch.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/017-openai-responses-reviewer-and-chatgpt-settings.md

## Settled direction

- The maintained embedded config belongs to the Python application. Recommended
  source location:
  `application/python/agent_terminal_app/default_config/embedded-ios/config.json`.
- Use `AgentApplication`'s existing placeholder environment contract and
  explicit `env_overrides`; do not mutate process-global environment state.
- Reviewer is an opt-in global capability, hidden by default and listed last
  when enabled.
- Reviewer URL, model, CA path, provider type, and tool family are deployment
  configuration, not editable user preferences. The caller API key remains
  editable and Keychain-backed.
- Provider form edits autosave. The implementation should debounce ordinary
  text edits and immediately persist discrete controls, while serializing
  writes so older saves cannot overwrite newer state.
- Embedded OpenAI authentication has one control surface. Session/plugin
  settings may display the effective mode as read-only but must not offer a
  second API/ChatGPT selector.
- The normal provider and ChatGPT plugins remain generic. Embedded-specific
  behavior should be a small package/plugin variant or config-owned UI-schema
  customization rather than conditionals keyed to React Native inside the
  generic provider.

## Supporting facts

- The runtime currently writes an app-support `config/config.json`, but
  `_config_payload()` constructs it from hardcoded Python dictionaries.
- Swift independently owns provider definitions/defaults and TypeScript owns a
  third profile order and form policy.
- `agent_app.config` already resolves `${env:...}` and `${file:...}` values and
  accepts explicit `env_overrides`.
- Fresh settings migration currently enables the compatible Qwen profile and
  makes it default even when no legacy setting exists.
- The built-in connection record displays legacy `proxyUrl` and `model`
  aliases bound to the compatible profile. The old on-device connection wizard
  also writes those aliases and changes the default.
- The current embedded bundle includes 12 application plugins but not the
  default system-message, request-options, timestamp/duration,
  summarize-range, rebuild-native, or cost-tracking plugins.
- File context depends on GitPython and web context depends on trafilatura.
  MCP and cloud application plugins have runtime responsibilities that are not
  automatically appropriate for iOS.

## Decisions requiring confirmation

- Final built-in connection label and whether it should mention Python,
  on-device execution, or agents.
- Final user-facing provider and agent names. Stable internal ids may remain
  for migration, but their display is not approved.
- Whether the diagnostic smoke provider is hidden, removed from production,
  or retained under an approved recovery/debug surface.
- Normal-user default provider and first-run presentation. Reviewer-last and
  reviewer-opt-in are settled; Reviewer is not assumed to be the normal
  default.
- Whether file context should be bundled with GitPython and whether web context
  should be bundled before Tavily work adds a different web capability.
- Whether MCP observability, application-config actions, cloud-agent actions,
  and cost UI should be visible on iOS even when their underlying capability
  is absent or limited.

## Execution plan

Status: Approved

First add focused failing coverage for the current Qwen alias/default behavior,
Reviewer visibility and field exposure, explicit-save form, and duplicate
session auth selector. Preserve the previously passing Reviewer and ChatGPT
Release-simulator paths as the decisive regression boundary.

Move the source graph into an embedded JSON configuration owned by
`agent_terminal_app`. Package that config and its required system-message
assets into the immutable iOS archive. Keep a small Python embedding adapter
that copies the template to app support and constructs explicit
`env_overrides` from native settings. The adapter may select a config variant
or supply boolean/string placeholders, but it must not rebuild provider,
agent, plugin, or mixin structures.

Add the settled iOS-feasible plugin set and exercise each contribution through
the production embedded `AgentApplication`. Record exclusions rather than
silently diverging from the ordinary default config.

Refactor native settings into persisted values rather than graph definitions.
Introduce global Reviewer visibility; hide its fixed deployment fields and
place it last when enabled. Replace explicit Save with serialized autosave and
keep Test as a non-persisting validation action.

Add an embedded-specific OpenAI/ChatGPT customization at the plugin/config
boundary so session UI schema does not expose `auth_mode`, while global
settings still drive the effective mode and plugin-owned login actions.

Remove the legacy embedded connection configuration path or make it navigation
to the single settings surface. Correct connection metadata to represent the
effective selected profile. Do not finalize unresolved display names or
smoke-agent product behavior; preserve internal ids for migration as needed
and collect those decisions for user confirmation.

### Implementation decisions and open questions

- **Approved:** Reviewer is hidden unless a global setting enables it and is
  placed last when visible.
- **Approved:** Reviewer URL/model/CA are hidden and immutable in the app;
  caller API key is the only editable Reviewer field.
- **Approved:** provider-form edits autosave; Test remains non-persisting.
- **Approved:** API/ChatGPT selection exists only in the global on-device
  settings for embedded agents.
- **Approved:** use a customized embedded plugin/config variant when needed;
  do not specialize the generic provider for React Native.
- **Open:** final display names, normal default profile, and smoke-agent
  exposure.
- **Open:** optional dependency-heavy plugin inclusion and UI exposure for
  capabilities unavailable on iOS.

### Documentation

- Document the embedded JSON source, placeholder contract, native-setting
  ownership, secret boundaries, and bundle provenance.
- Add a default-plugin parity table listing included and intentionally omitted
  plugins with reasons.
- Update the mobile guide for autosave, Reviewer visibility, hidden deployment
  fields, single auth-control location, and removal of the legacy wizard.
- Keep provisional naming explicitly labeled until approved.

### Task checklist

- [ ] Add regression tests for Reviewer/Qwen, visibility, hidden fields,
  autosave, and duplicate auth controls.
- [ ] Add and package the Python-owned embedded JSON configuration.
- [ ] Replace generated graph construction with placeholder overrides.
- [ ] Add the settled default-config plugin subset and focused integration
  coverage.
- [ ] Implement Reviewer opt-in visibility, last placement, and hidden fixed
  fields.
- [ ] Implement serialized autosave and remove the explicit-save dependency.
- [ ] Add embedded-specific ChatGPT/session UI customization.
- [ ] Remove or neutralize the legacy embedded connection configuration path.
- [ ] Run source, immutable ZIP, component, TypeScript, and Release-simulator
  regression coverage.
- [ ] Present unresolved product and optional-plugin decisions for approval.
- [ ] Update documentation, requirement evidence, and completion notes.

### Requirement verification

- Inspect the immutable ZIP and app-support runtime to prove the maintained
  JSON comes from the Python application and the generated graph no longer
  originates in Swift/TypeScript/Python dictionaries.
- Run embedded runtime integration tests proving placeholder values select the
  expected providers, agents, plugins, workspace, and auth mode without
  writing secrets into the maintained or generated config.
- Run production settings component and Release-simulator tests proving
  Reviewer is absent by default, visible last when enabled, exposes only the
  API key, and persists every edit without an explicit Save action.
- Run session-settings UI coverage proving no editable API/ChatGPT selector is
  returned for embedded OpenAI sessions while the global mode drives actual
  API and ChatGPT requests.
- Run a migration/relaunch test proving a Reviewer selection cannot display or
  activate Qwen and existing credentials/sessions remain usable.
- Exercise each added default plugin through its public feature or application
  boundary, with system-message compilation as a mandatory decisive check.
- Re-run the real Reviewer and manually gated ChatGPT Release-simulator paths
  after the configuration and plugin changes.

### Additional implementation verification

- Verify the bundle contains no dev dependencies and no plugin is imported
  from the repository during simulator execution.
- Verify Reviewer fixed values and secrets are absent from editable UI and
  logs, and caller/upstream keys are never confused.
- Verify autosave coalesces rapid text edits, serializes writes, and surfaces
  failures without losing the current draft.
- Run `git diff --check`, focused Ruff, TypeScript, documentation preparation,
  and the selected provider-package tests from the immutable ZIP.
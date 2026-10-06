# Move The Embedded Runtime To Python-Owned Config And Restore Plugin Parity

Replace the duplicated Swift/Python embedded-agent graph with a reviewable
Python-application-owned JSON configuration, restore the useful default
plugins, correct the legacy Reviewer/Qwen seam, and make the on-device settings
behavior consistent without finalizing unapproved product names.

## Requirements checklist

- [x] The embedded runtime's providers, agents, plugins, application settings,
  and mixins are maintained in a JSON configuration under the Python
  application rather than reconstructed independently in the mobile app.
- [x] Native/mobile settings supply URLs, models, workspace paths,
  authentication mode, credential paths or values, reviewer visibility, and
  other mutable values through explicit env-like placeholder overrides.
- [x] API keys and ChatGPT credentials remain outside the maintained JSON;
  secrets stay in Keychain or the plugin-owned credential store and are not
  persisted into generated configuration files.
- [x] The embedded runtime includes the useful, iOS-feasible default-config
  plugins, including system message, request options, timestamp/duration,
  summarize range, rebuild native history, and cost tracking. Omitted default
  plugins have documented compatibility or product reasons.
- [x] The embedded OpenAI Responses and OpenRouter profiles register their
  provider-native web-search, attachment, and API-control extensions where the
  bundled transport supports them, without advertising upload modes that
  cannot work on iOS.
- [x] Direct OpenAI exposes its applicable flex, fast, prompt-caching, and
  verbosity controls; ChatGPT and Reviewer do not expose unsupported or
  incorrectly accounted API service tiers.
- [x] A global on-device setting controls Reviewer visibility. Reviewer is
  absent from ordinary settings and agent selection while disabled and appears
  at the bottom when enabled.
- [x] Reviewer deployment URL, model, and CA path are fixed by the maintained
  config and hidden from the on-device form; only its caller API key is
  editable.
- [x] Every edit in the on-device provider form is persisted without requiring
  a separate Save action, with clear saving, saved, and error states.
- [x] OpenAI API-key versus ChatGPT authentication is controlled only from the
  on-device provider settings. The corresponding ordinary plugin/session
  setting is hidden or disabled for embedded agents and cannot override the
  saved global choice.
- [x] The embedded ChatGPT integration remains plugin-driven and may use an
  embedded-specific plugin variant to customize UI schema/actions without
  changing the ordinary OpenAI Responses or ChatGPT plugin behavior.
- [x] The built-in connection and session creation use and display the actual
  selected profile; legacy generic-compatible aliases or the old connection
  wizard cannot silently display or activate Qwen when Reviewer is selected.
- [x] Consumer-facing connection labels, profile/agent display names, profile
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
- The OpenAI Responses and OpenRouter packages already bundled for iOS also
  contain provider-native web-search and attachment extensions. The embedded
  JSON currently does not register those extensions.
- OpenAI Responses also contains flex, fast-mode, prompt-caching, native
  compaction, and verbosity extensions. Flex is API-auth only and must not be
  presented as effective under ChatGPT auth. Native compaction imports the
  OpenAI SDK and is not compatible with the lightweight requests-only iOS
  dependency set.
- The bundled OpenAI Responses requests transport supports inline image
  requests but does not currently implement Files API upload. PDF and
  upload-backed image controls must therefore remain hidden for that transport
  until multipart upload support exists.

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
  Provider-native OpenAI/OpenRouter web search is approved and does not resolve
  the later provider-neutral Tavily requirement.
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

Register the provider extensions already shipped inside the OpenAI Responses
and OpenRouter packages. Expose native web search for direct OpenAI, Reviewer,
and OpenRouter; expose session-owned inline image attachment handling for
OpenAI and OpenRouter; and expose direct-OpenAI API controls with auth-aware
visibility. Keep upload-backed PDF controls hidden under the requests
transport, keep Flex disabled for ChatGPT and Reviewer, and omit SDK-only
native compaction from the requests-only iOS bundle.

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
- **Approved:** enable provider-native OpenAI Responses and OpenRouter web
  search in addition to the later provider-neutral Tavily tool.
- **Approved:** enable image attachment handling where the current bundled
  transport works, initially limiting OpenAI requests transport to inline
  images.
- **Approved:** expose direct-OpenAI API controls, while hiding Flex from
  ChatGPT and excluding Flex from Reviewer until its proxy pricing and
  service-tier accounting explicitly support it.
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

- [x] Add regression tests for Reviewer/Qwen, visibility, hidden fields,
  autosave, and duplicate auth controls.
- [x] Add and package the Python-owned embedded JSON configuration.
- [x] Replace generated graph construction with placeholder overrides.
- [x] Add the settled default-config plugin subset and focused integration
  coverage.
- [x] Implement Reviewer opt-in visibility, last placement, and hidden fixed
  fields.
- [x] Implement serialized autosave and remove the explicit-save dependency.
- [x] Add embedded-specific ChatGPT/session UI customization.
- [x] Remove or neutralize the legacy embedded connection configuration path.
- [x] Run source, immutable ZIP, component, TypeScript, and Release-simulator
  regression coverage.
- [x] Present unresolved product and optional-plugin decisions for approval.
- [x] Register and configure the applicable OpenAI Responses and OpenRouter
  provider-native extensions.
- [x] Add transport-aware attachment UI and auth-aware API-control coverage.
- [x] Run focused source, immutable-ZIP, mobile component, and Release-simulator
  verification for native search and attachment availability.
- [x] Update documentation and requirement evidence.

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
- Inspect the embedded session UI schema for direct OpenAI, ChatGPT, Reviewer,
  and OpenRouter to prove native search and attachment controls are present
  only where supported and Flex is absent from ChatGPT and Reviewer.
- Run an inline image request through the production mobile attachment path
  and one provider-native web-search request through a Release-simulator
  hosted-provider row.
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

## Implementation Notes

- 2026-09-29: Added the maintained embedded JSON under the Python application
  at `agent_terminal_app/default_config/embedded-ios/config.json`. The iOS
  packaging script now stages that config and the newly selected pure-Python
  plugins into the immutable archive.
- 2026-09-29: The embedded Python adapter now copies the maintained JSON
  unchanged into app support and supplies a config-only placeholder map for
  provider values, credentials, workspace paths, agent availability, ChatGPT
  storage, and cost storage. It no longer builds provider/agent/plugin
  topology in `_config_payload()`.
- 2026-09-29: `AgentApplication` now supports config-disabled agents, including
  string values supplied by environment placeholders, and removes the control
  key from effective runtime configuration. Focused core tests pass.
- 2026-09-29: Added system-message, request-options, timestamp/duration,
  summarize-range, rebuild-native, and cost-tracking packages to the embedded
  configuration and bundle input. Embedded runtime tests prove the maintained
  graph loads the new feature/application plugin ids.
- 2026-09-29: An explicit empty OpenAI Responses `auth_mode_options` list now
  suppresses the provider's session auth selector while preserving the model,
  retry, and attachment UI. The generic provider retains its existing UI when
  the option is absent.
- 2026-09-29: Native settings now persist a global `reviewerVisible` flag.
  Reviewer is hidden by default, rendered last when enabled, and its form
  exposes only the Keychain-backed caller key, Test, and default selection.
  URL, model, CA, provider, and tools come from the maintained JSON.
- 2026-09-29: Provider settings autosave through a debounced serialized queue.
  Successful saves clear only the just-persisted key draft, preserve newer
  edits, update connection metadata, and report saving/saved/error state.
  Test remains a non-persisting validation action.
- 2026-09-29: Removed the legacy on-device option from the New Connection
  chooser. The built-in connection record now follows the selected profile
  instead of the generic-compatible aliases. A Release-simulator Ollama setup
  against a disposable authenticated proxy proved model/URL metadata,
  autosave, Keychain persistence, connection activation, and relaunch.
- 2026-09-29: Added application-owned developer documentation for the embedded
  JSON and updated the mobile runtime guide for autosave, Reviewer opt-in,
  fixed deployment fields, single auth control, plugin parity, and the removed
  legacy form.
- 2026-09-29: Verification passed for 30 focused Python config/runtime tests,
  278 mobile Jest tests, TypeScript, Swift parsing, docs preparation, Release
  simulator build, immutable ZIP provider tests, the local Ollama setup Detox
  flow, and the ungated real ChatGPT login-start/cancel Detox flow.
- 2026-09-29: Selected source package results: request-options/timestamp 58
  passed; summarize-range 10 passed; rebuild-native 6 passed; cost-tracking 68
  passed; system-message pure feature tests 34 passed. Seven existing
  system-message AgentApplication/default-config integration tests fail in the
  current worktree on request-checkpoint and omitted-mixin assumptions; the
  embedded maintained-config and system-message UI boundary passes and those
  tests were not weakened.
- 2026-09-29: Removed the remaining native/Python profile-definition
  duplication. The maintained JSON now owns profile order, stable ids, current
  labels, tool-family metadata, editable-provider defaults, and fixed Reviewer
  values. Runtime preparation stages the identical JSON both inside the Python
  ZIP and as a native-readable resource; the final built app resource matched
  the maintained source byte-for-byte.
- 2026-09-29: Final rebuild verification passed again: Release simulator
  build, local authenticated Ollama setup/autosave/relaunch flow, ungated real
  ChatGPT login start/cancel, immutable ZIP provider tests, TypeScript, Swift
  parsing, and 30 focused Python config/runtime tests. The hosted Reviewer and
  manually authorized ChatGPT tool requests remain explicit final gates
  because their credentials/human approval are not available unattended.
- 2026-09-29: User approved extending plugin parity to the already-bundled
  OpenAI Responses and OpenRouter native web-search, attachment, and API
  extensions. OpenAI requests-transport attachment UI will initially remain
  inline-image-only; Flex remains direct-API-only and excluded from Reviewer.
- 2026-09-29: Registered OpenAI Responses attachments, Flex, Fast mode, prompt
  caching, native web search, and verbosity plus OpenRouter attachments,
  Claude caching, native web search, and verbosity. Focused
  provider tests passed (71), and the embedded runtime/config tests passed
  (25), including direct-API, ChatGPT, Reviewer, and OpenRouter UI-schema
  boundaries.
- 2026-09-29: Release-simulator startup exposed that native compaction imports
  the OpenAI SDK, which is intentionally absent from the lightweight
  requests-only iOS runtime. Native compaction was removed from the embedded
  config and recorded as an explicit compatibility exclusion rather than
  adding the unused SDK dependency tree.
- 2026-09-30: The final OpenAI Responses Release-simulator matrix reported
  `web_search,image,flex,fast` from the bundled session UI schema, completed a
  real `apply_patch` request, verified the workspace selector and boundary,
  and retained the evidence after relaunch. Focused provider-extension tests
  passed (51), the immutable ZIP provider suite passed, and the archive
  remained unchanged.
- 2026-09-30: Provider Test, Enable, and Make-default controls now expose
  explicit accessibility activation boundaries. This corrected the
  simulator-observed modal interaction where a visible control could miss a
  coordinate tap and leave the selected provider disabled or non-default.

## Post-completion follow-up

### 2026-10-05 — Declarative embedded dependencies and release smoke

Status: Approved

The TestFlight build exposed `No module named 'jsonpath'` while invoking
ChatGPT application actions. Source development remained healthy because the
developer environment had `python-jsonpath` installed. The generated iOS ZIP
contained the newly merged `agent_app.json_projection` consumer and the
unrelated `jsonpath_ng` package, but not the `jsonpath` package supplied by
the `python-jsonpath` distribution.

The correction replaces the preparation script's duplicated hardcoded pip
requirement and import-package copy lists with one fully pinned requirements
file owned beside the Python embedded config. Preparation installs
platform-neutral wheels into a clean staging tree, rejects native extensions
and development distributions, and archives the complete validated tree.
Distribution-to-import naming differences no longer require bundler changes.

The TestFlight verification boundary also gains a separate
embedded-application ZIP smoke. It runs without source or site-package
fallback, imports `jsonpath`, `agent_app`, the ChatGPT application plugin, and
the mobile runtime from the generated ZIP, then executes the credential-free
ChatGPT status action. The existing provider-package ZIP suites retain their
provider-only scope.

Follow-up checklist:

- [x] Add the pinned embedded requirements file, including
  `python-jsonpath==2.2.1`.
- [x] Install only platform-neutral wheels and archive the complete validated
  dependency staging tree.
- [x] Reject native extensions, symlinks, and known development
  distributions.
- [x] Include the requirements file in runtime rebuild provenance.
- [x] Add a root package command for the isolated embedded-application bundle
  smoke.
- [x] Run the bundle smoke from Fastlane release verification.
- [x] Rebuild the immutable archive and record passing source, archive, and
  release-gate evidence.

Follow-up evidence:

- The rebuilt archive has SHA-256
  `3f4b7034d4fdfa7ea9a18922454de3599ef83ead2779c6576c7b7ab44894ede5`
  and contains `jsonpath`, `python_jsonpath-2.2.1.dist-info`, and
  `agent_app/json_projection.py` with no native extensions or known
  development packages.
- `npm run test:ios:embedded-runtime:bundle` imported `jsonpath`,
  `agent_app`, `chatgpt_auth_app`, and `crystal_lattice_mobile_runtime`
  directly from the ZIP and completed the credential-free
  **ChatGPT Login Status** action.
- The existing immutable provider suite passed from the same archive:
  2 OpenRouter integration tests passed and 9 were intentionally deselected;
  the archive digest remained unchanged during that suite.
- Mobile Python verification passed 37 tests; focused embedded-config and
  root-script verification passed 17 tests; the final focused preparation and
  root-script rerun passed 21 tests. Focused Ruff and `git diff --check`
  passed.
- The exact `fastlane ios verify` lane passed under the pinned Ruby/Bundler
  environment: 5 build-number tests, embedded runtime preparation, the new
  archive action smoke, TypeScript, and 56 Jest suites / 290 tests.
- Public documentation preparation completed successfully with
  `docs_site/scripts/prepare_mkdocs_site.py`.

### 2026-10-06 — Local provider settings usability

The user's subsequent settings corrections and proposed execution plan are
recorded in
`tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md`.
That task permits independent session API/ChatGPT overrides, replacing this
task's earlier global-only authentication policy. The original requirements
and implementation evidence above retain the historical behavior.

Subtask `027` also records the requested Local-agent/OpenAI/Default-model
labels, always-available API-key and ChatGPT controls, separate Global
Settings Reviewer exposure and provider enablement, and removal of
Make-default controls. Its OpenAI card grouping remains an open decision and
its execution plan is Draft; creating the task does not start implementation.
# Embedded iOS Agent Runtime Proof Of Concept

Create the first working embedded Python agent runtime in the real iOS
application, make it minimally useful with provider, tool, settings, and
session-management parity, then add the next research-oriented capabilities.

## Requirements checklist

- [x] The iOS app hosts a working embedded Python/Crystal Lattice runtime and
  exercises it through the production mobile backend and screens.
- [x] A real OpenAI-compatible model path uses an API-key-protected proxy
  backed by Ollama.
- [x] The initial runtime exposes general `Read` and `Write` tools restricted
  to one application workspace.
- [x] A simple multi-round request is verifiable in the simulator, including
  bounded background continuation or recovery. Simulator evidence is
  sufficient for this proof of concept.
- [x] Separate iOS-safe Claude-like and Codex-like plugin sets provide useful
  workspace and public-fetch tools with model-family-appropriate names,
  schemas, and result formatting.
- [x] The embedded runtime offers separate generic OpenAI-compatible,
  dedicated OpenAI Responses reviewer, direct OpenAI Responses, OpenRouter,
  and Anthropic profiles with provider-specific settings and tool families.
- [x] The local connection is preconfigured, and Home exposes a separate local
  runtime settings window for provider credentials, URLs, models, and default
  selection.
- [x] The iOS-safe application plugins from the ordinary default configuration
  expose session actions, message deletion, titles, search, metadata, status,
  pinning, archive, ordering, and attachments through the production mobile
  UI.
- [ ] Tavily web search is added as the next fixed tool, with an equivalent
  reviewer proxy path.
- [ ] A restricted Python interpreter is exposed as a later fixed tool without
  access to application/runtime mutation.
- [x] No deterministic product or reviewer model is introduced.
- [x] Provider packages intended for the embedded ZIP pass their existing unit
  and integration suites while imported from that ZIP, and the root
  `package.json` exposes the important bundle and Detox matrix commands.
- [x] Release-simulator real-API Detox covers the generic OpenAI-compatible,
  OpenAI Responses API-key, OpenAI Responses ChatGPT-action login, OpenRouter,
  Anthropic, and external reviewer paths.
- [x] An externally reachable, authenticated, model-limited, cost-limited
  GPT-5.6 Luna proxy makes the app usable by App Review without exposing the
  upstream OpenAI credential.
- [x] Sessions created with the credential-free `local` agent remain usable
  after a provider profile is enabled and the embedded application reloads.
- [x] On-device OpenAI settings use an explicit API-key or ChatGPT default,
  expose plugin-driven ChatGPT login controls, and retain independent
  per-session overrides.
- [x] The embedded runtime is defined by a reviewable JSON configuration owned
  by the Python application, structurally aligned with the ordinary default
  config; the mobile/native layer supplies user settings through explicit
  env-like placeholder values instead of reconstructing the agent graph.
- [x] The embedded runtime includes the default-config plugins that are useful
  and feasible on iOS, including the system-message feature, while every
  omitted default plugin has an explicit compatibility or product rationale.
- [x] Provider-native OpenAI Responses and OpenRouter web search, image
  attachments, and applicable API controls are enabled where the embedded
  transport supports them.
- [x] Each session can select a working directory contained by the fixed
  application workspace through a dedicated directory setting without
  expanding filesystem access.
- [ ] A session can create or select an app-private sandbox, create or reuse
  an app-owned workspace shared with other sessions, or select an authorized
  folder from iOS Files without copying its contents.
- [x] Consumer-facing connection names, profile labels, agent names, default
  selection, profile order, and exposure of the proof-of-concept smoke agent
  are treated as provisional until explicitly approved.
- [x] Selecting or displaying the reviewer path cannot silently show or
  activate the legacy Qwen/Ollama-compatible profile.

## Deferred configuration and product review

These items were discovered after subtask `017` acceptance. They are recorded
for later planning and are not approved implementation decisions.

### Current facts

- The checked-in embedded runtime writes an actual `config/config.json`, but
  its source is the Python `_config_payload()` function rather than a
  maintained JSON template.
- Provider defaults and identities are duplicated across Python
  `_config_payload()`, Swift `providerDefinitions`, TypeScript settings types
  and ordering, and tests.
- `agent_app` already supports `${env:...}` and `${file:...}` resolution plus
  explicit `env_overrides`, so an embedding application can provide mobile
  settings without mutating process-global environment state.
- The embedded plugin list currently includes the selected provider/tool
  packages and 12 application plugins for ChatGPT auth, title generation,
  session actions, archive, search, metadata/status, ordering, pinning, and
  attachments.
- Compared with the ordinary default config, the embedded bundle omits
  generally useful pure-Python candidates such as system message, request
  options, timestamp/duration, summarize range, rebuild native history, and
  cost tracking. File context and web context add GitPython/trafilatura
  dependencies; MCP and cloud plugins have runtime responsibilities that may
  be inappropriate for this first embedded runtime. Each inclusion and
  exclusion still needs a deliberate compatibility review.
- The runtime always exposes a `local` agent backed by
  `EmbeddedSmokeProvider`, including when real providers are configured. This
  began as proof-of-concept/recovery support and was not approved as final
  product behavior.
- Internal/provider-facing ids currently visible to users include
  `compatible-claude`, `reviewer-codex`, `openai-codex`,
  `openrouter-claude`, and `anthropic-claude`. The Codex-like and Claude-like
  tool-family split was approved, and `reviewer-codex` was approved in
  subtask `017`; that does not constitute approval of all final user-facing
  names or of exposing internal ids as labels.
- Connection labels currently vary among `On-device Python agents`,
  `On-device Python agent`, and `On-device Python Agent`.

### Reviewer/Qwen finding

- The built-in connection record always projects its displayed `proxyUrl` and
  `model` from legacy aliases bound to the generic compatible profile.
  Consequently it can show `qwen3.5:0.8b` even when the runtime default is the
  reviewer.
- On a settings store with neither V3 nor V2 data, the compatibility migration
  unconditionally enables the compatible profile and changes the default to
  `compatible-claude`, even if no legacy URL/model/key exists.
- The old **New connection → On-device Python Agent** wizard writes the legacy
  `proxyUrl`/`model` shape, which enables the compatible profile and changes
  the actual default to `compatible-claude`.
- Selecting the already-created built-in connection does not itself rewrite
  provider settings. Until the seam is corrected, reviewer verification
  should use **Home → On-device providers**, enable and make the reviewer
  default, save, then select the existing built-in connection. The old
  on-device new-connection wizard should not be used.

### Decisions requiring approval

- Final user-facing connection name and whether the embedded runtime is
  presented as one connection, one agent, or a set of local agents.
- Final display names versus stable internal ids for each provider/tool-family
  combination.
- Whether the smoke/recovery provider remains hidden, remains visible under an
  approved name, or is removed from production configuration.
- Default profile, profile ordering, and whether the reviewer profile should
  be preselected outside App Review.
- Exact default-config plugin subset and explicit exclusions for iOS.
- Exact Python-application location and ownership of the embedded JSON
  template; the recommended direction is a maintained Python application
  config copied into the iOS bundle, with native settings passed as
  `env_overrides`.

Related Task:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

OVERLAP:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

The related task retains the broader App Review, local-model fallback,
privacy, reviewer-service, and external TestFlight outcomes. This task owns
the embedded implementation and its staged tool/provider enhancements.

## Scope boundaries

- Subtask `010` is complete.
- Subtask `015` is complete historical implementation and verification.
- Subtask `017` completed the approved reviewer Responses and ChatGPT
  settings/TLS correction.
- Subtask `018` owns the approved JSON-config, plugin-parity, Reviewer
  visibility, autosave, and single-auth-control follow-up and is under
  execution.
- Subtask `019` owns the approved workspace-internal per-session working
  directory selector and filesystem-boundary enforcement.
- Subtask `022` owns the approved reusable plugin contract for placing actions
  next to fields in session settings, including client-assisted directory
  selection.
- Subtask `025` owns the proposed user-selectable workspace UX, internal
  directory creation, and persistent security-scoped iOS Files access on top
  of the settings-action contract.
- Subtask `027` records the requested local-agent naming, OpenAI credential
  layout/defaults, restored session authentication overrides, separate Global
  Settings Reviewer exposure, and removal of Make-default controls. Its
  approved implementation is complete. Reviewer starts hidden/disabled
  and is configured with global opt-in followed by caller-key entry.
- Subtasks `020` and `030` record later increments but have no approved
  execution plan.
- ChatGPT authorization settings and the corrected production reviewer
  Responses path are in approved subtask `017`. Local-model fallback, email,
  cross-platform external workspace support, and polished cross-platform
  credential hardening remain outside this task.

## Subtasks

- [x] `tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/017-openai-responses-reviewer-and-chatgpt-settings.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/018-embedded-json-config-plugin-parity-and-product-review.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/019-session-working-directory-selector.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/020-tavily-web-search.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/022-plugin-driven-session-settings-actions.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/025-user-selectable-ios-workspaces.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/030-restricted-python-executor.md`

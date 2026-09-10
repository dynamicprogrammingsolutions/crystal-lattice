# Make The Embedded Runtime Minimally Useful

Turn the completed iOS proof of concept into a preconfigured local runtime with
a reusable workspace tool package, four supported provider profiles, dedicated
Home-menu settings, and the iOS-safe application actions from the ordinary
default configuration.

## Requirements checklist

- [ ] A first-party package under `plugins/` owns the embedded runtime tools;
  the tools are no longer implemented inside the mobile bridge module.
- [ ] The supported tool package provides fully implemented, iOS-safe
  `Read`, `Write`, `Edit`, `Glob`, `Grep`, `WebFetch`, and `apply_patch`
  behavior for its documented scope.
- [ ] Every filesystem-mutating or inspecting tool is restricted to the
  canonical app workspace and rejects absolute paths, traversal, and symlink
  escape.
- [ ] `WebFetch` accepts only public HTTP(S) URLs, revalidates redirects,
  rejects local/private/reserved destinations, and bounds time, redirects,
  downloaded bytes, and returned text.
- [ ] Four fixed provider-backed agents are available through the local
  runtime: generic OpenAI-compatible, OpenAI Responses, OpenRouter, and the
  official Anthropic API.
- [ ] All four providers use the same common tools. Generic
  OpenAI-compatible, OpenRouter, and Anthropic expose `Write`; OpenAI
  Responses exposes `apply_patch` in the writer slot instead of `Write`.
- [ ] The local connection is created automatically and can list existing
  sessions before any provider credential is configured.
- [ ] A separate Local Runtime Settings window is accessible from the Home
  menu and configures each provider's API key, base URL, model, enabled state,
  and the default agent.
- [ ] Provider API keys are stored in the native credential owner rather than
  saved connection records, AsyncStorage, sessions, tool results, logs, or
  committed configuration.
- [ ] Saving settings validates a candidate provider configuration and performs
  a complete embedded `AgentApplication` reconstruction while preserving
  sessions and workspace files.
- [ ] The embedded application loads the selected iOS-safe default application
  plugins and exposes their real application/session/message actions through
  the production mobile UI.
- [ ] Users can at minimum fork/copy/delete sessions, delete message ranges,
  restore automatic snapshots, edit/generate titles, search/filter sessions,
  and use pin/archive/status metadata.
- [ ] Simulator acceptance covers the preconfigured connection, settings and
  reload, provider/tool interoperability, simple web fetch, application
  actions, persistence, and background lifecycle without a deterministic
  product provider.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md

## Proposed scope decisions

- **Tool package:** create `plugins/embedded-runtime-tools` rather than loading
  `claude-tools` directly. Reuse investigated schemas and pure helper logic
  where appropriate, but keep the package provider-neutral and iOS-safe.
- **Supported tools:** `Read`, `Write`, `Edit`, `Glob`, `Grep`, `WebFetch`, and
  `apply_patch`. Bash, TaskStop, MCP, WebSearch, image/PDF reading, and package
  installation are not included.
- **Provider shape:** expose four fixed agents rather than dynamically changing
  one provider identity. Settings select the default new-session agent while
  all configured agents remain selectable.
- **OpenAI Responses mutation tools:** retain the common `Edit` tool and replace
  only `Write` with `apply_patch`, following the request literally.
- **Credential ownership:** store API keys in iOS Keychain. Keep provider
  enabled state, non-secret URLs, models, and default-agent selection in
  app-owned preferences.
- **Application plugins:** bundle the iOS-safe session/title/search/metadata
  plugins listed in the plan. Do not bundle desktop environment writing,
  cloud orchestration, native rebuild, MCP runtime, or subprocess-dependent
  export plugins.
- **Web fetch:** implement bounded fetch and simple text/HTML extraction with
  the standard library or an otherwise proven pure-Python closure. Tavily
  search remains in subtask `020`.

## Supporting details

### Existing implementation

- Subtask `010` already supplies bundled CPython, the native owner, an
  `inProcess` backend, session/workspace persistence, API-key configuration,
  one OpenAI-compatible provider, two inline file tools, and lifecycle
  diagnostics.
- The embedded Python router still returns empty application actions/UI schema
  and placeholder snapshot/plugin mutation results. It must delegate to the
  real `AgentApplication` APIs before default application plugins are useful.
- The saved embedded connection currently appears only after setup. The local
  connection can instead be inserted during iOS connection hydration and
  opened without requiring provider validation merely to browse sessions.

### Tool feasibility

- `claude-tools` provides useful behavior references for `Read`, `Write`,
  `Edit`, `Glob`, `Grep`, and `WebFetch`, but the package also imports
  subprocess/PDF, `aiohttp`, `trafilatura`, MCP, Bash, and web-search paths that
  are unsuitable for the fixed iOS closure.
- `tool-compat-shared` has reusable pure filesystem logic, but its package
  initializer and dependency declaration include subprocess and `aiohttp`
  surfaces. The new package should extract or directly reuse only proven
  iOS-safe modules rather than bundling the complete package accidentally.
- The existing Codex `apply_patch` parser/runtime is pure Python and can be
  adapted into the new package with the same workspace authorization boundary.
- A simple `WebFetch` does not need Claude's prompt-driven nested model call or
  `trafilatura`. Bounded HTTP(S), redirect validation, charset handling,
  standard-library HTML text extraction, and truncation are sufficient here.

### Provider feasibility

- Generic OpenAI-compatible and OpenRouter already use the `requests` closure
  proven by subtask `010`.
- OpenAI Responses imports the OpenAI Python SDK; Anthropic imports the
  Anthropic Python SDK. Their current transitive closures have not been proven
  in the embedded iOS interpreter and may include native extensions.
- The first provider checkpoint must therefore import and execute minimal
  network calls for both SDK-backed providers in the simulator. If their
  closures are not iOS-compatible, prefer adding an iOS-safe transport path to
  the existing provider packages while preserving their public provider and
  extension contracts. Do not introduce replacement product providers with
  divergent history/tool semantics merely to pass packaging.

### Provider profiles

Recommended fixed agents:

- reviewer/OpenAI-compatible, using
  `reference-openai-compatible-provider`;
- OpenAI Responses, using `openai_responses`;
- OpenRouter, using `openrouter`;
- Anthropic, using `anthropic-compatible` against the official API by default.

Each profile has enabled state, base URL, model, API-key presence, and a
connection test/model refresh action. Official service URLs are defaults for
OpenAI Responses, OpenRouter, and Anthropic. The review-compatible profile
keeps a configurable URL and model so it can point at the authenticated Ollama
proxy.

Real hosted completion requires valid OpenAI, OpenRouter, and Anthropic
credentials. Missing credentials are a verification dependency, not
permission to declare an untested provider complete.

### Application plugin selection

The initial iOS-safe default subset should include:

- `session-actions-app`;
- `summarize-range-app`;
- `session-title-app`;
- `session-main-search-app`;
- `generate-title-app`;
- `session-message-count-meta-app`;
- `session-pinned-app`;
- `session-archive-app`;
- `session-status-app`;
- `session-timestamp-meta-app`;
- `session-ordering-buckets-app`;
- `session-asset-attachments`.

`application-config-app` is replaced by the native Local Runtime Settings
owner. `chatgpt-auth-app`, `rebuild-native-app`, `mcp-runtime-app`, and
`cloud-agent-app` remain outside this task. Provider-specific application
plugins are included only when their dependencies and mobile UI behavior are
proven in scope.

## Execution plan

Status: Draft

Implement this as a sequence of working vertical checkpoints. Preserve the
completed `010` simulator flows while replacing inline proof-of-concept pieces
incrementally.

First create `plugins/embedded-runtime-tools` with its own descriptor,
packaging, tests, README, and development documentation. Move the current
workspace `Read`/`Write` implementation into it without changing the visible
tool behavior, then bundle that package into iOS and rerun the existing real
Ollama file-tool scenario. This is the first checkpoint and proves that plugin
discovery, app-zip staging, and workspace configuration work from a separate
package.

Add the remaining filesystem tools one at a time: `Edit`, `Glob`, `Grep`, and
`apply_patch`. Use provider-neutral canonical schemas/results and rely on the
existing tool-interop registry to convert them for OpenAI Chat, OpenAI
Responses, and Anthropic Messages. Keep all path resolution in one shared
authorization helper so every tool has identical logical-path, traversal,
symlink, size, and encoding behavior. `Write` creates/replaces complete text,
`Edit` performs exact bounded replacements, `Glob` enumerates bounded relative
matches, `Grep` performs bounded Python-regex searches without spawning
`rg`, and `apply_patch` creates/updates/deletes files through the same root.

Add `WebFetch` to the same package using an iOS-compatible HTTP closure. Resolve
and validate every destination before connecting and after every redirect;
block loopback, link-local, private, multicast, reserved, and non-HTTP(S)
targets. Bound DNS/connection/read time, redirect count, response bytes, and
returned characters. Support text and HTML with simple extraction and return a
structured result containing requested URL, final URL, status, content type,
title when available, extracted text, truncation state, and a safe error.

Before building provider settings, run an iOS provider-closure spike. Bundle
the minimal OpenAI Responses and Anthropic provider/extension entries with
their declared SDK closures, import them in the release simulator, and perform
the smallest model-discovery or mocked-network call that crosses their actual
transport construction. Record native-extension or resource failures. If an
SDK closure cannot run, add a narrowly scoped iOS-safe transport adapter inside
the owning provider package and verify that desktop behavior and public
history/tool contracts remain unchanged. Generic OpenAI-compatible and
OpenRouter remain on their existing `requests` paths.

Replace the single embedded provider config with four fixed provider profiles
and agents. Enable only the provider extensions needed for text streaming,
tools, reasoning/usage presentation, cancellation, and model discovery.
Attachments, native compaction, provider web search, ChatGPT auth, and other
extensions stay disabled until separately proven. Configure the tool matrix:

| Agent/provider | Common tools | Mutation slot |
| --- | --- | --- |
| OpenAI-compatible reviewer | `Read`, `Edit`, `Glob`, `Grep`, `WebFetch` | `Write` |
| OpenRouter | `Read`, `Edit`, `Glob`, `Grep`, `WebFetch` | `Write` |
| Anthropic | `Read`, `Edit`, `Glob`, `Grep`, `WebFetch` | `Write` |
| OpenAI Responses | `Read`, `Edit`, `Glob`, `Grep`, `WebFetch` | `apply_patch` |

Generalize the native configuration owner to a versioned multi-provider
settings document. Store each API key under a provider-specific Keychain item
and return only key-presence state to JavaScript. Store non-secret provider
URLs, models, enabled flags, and default agent in preferences. Implement
candidate validation, complete application reconstruction, and rollback to the
last usable config when validation or startup fails. Existing sessions remain
bound to their agent/provider identity and remain loadable after reload.

Add a dedicated `LocalRuntimeSettingsModal` opened from a new **Local runtime
settings** item in the Home menu. Show one provider section at a time with
enabled/default controls, URL, model, masked API key, saved-key state, model
refresh/test action, save, and cancel. The local connection is inserted
automatically on iOS and opens the embedded backend without requiring a
provider key merely to browse sessions. Sending with an unconfigured agent
returns an actionable route to the settings window.

Bundle the selected default application plugins and implement embedded route
parity by delegating to `AgentApplication` rather than copying business logic.
Replace placeholder application actions/UI schema, session plugin mutations,
snapshots, server settings, fork, delete, restore, and action execution routes
with the same public payload contracts used by `RestAgentBackend`. Verify the
mobile's existing action, settings, session-list, and generated-file consumers
against the in-process backend.

Finish with a provider/tool/application-action matrix. Deterministic local HTTP
fixtures may verify protocol edge cases, but product acceptance uses real
providers: the authenticated Ollama reviewer proxy for OpenAI-compatible and
credential-gated hosted smoke tests for OpenAI Responses, OpenRouter, and
Anthropic. Each provider must complete at least one common tool call; the
writer-slot provider must also complete `Write` or `apply_patch` as applicable.
The production-screen simulator scenario should configure a provider from
Home, fetch a small public page, save or patch a workspace file, reload it,
fork the session, delete a message with an automatic snapshot, and survive
process relaunch/backgrounding.

### Implementation decisions and open questions

- **Recommendation — tool package name:** use
  `plugins/embedded-runtime-tools`. Rename before execution if a broader
  cross-runtime package name is preferred.
- **Recommendation — exact tool set:** approve
  `Read`, `Write`, `Edit`, `Glob`, `Grep`, `WebFetch`, and `apply_patch` as the
  complete supported set for this task. “Fully working” means complete within
  the documented text/workspace/public-fetch scope, not all Claude Code tools.
- **Decision proposed — OpenAI Responses:** retain `Edit`, omit `Write`, and
  expose `apply_patch`.
- **Decision proposed — agents:** expose four fixed agents and a default-agent
  setting rather than hot-swapping one agent's provider identity.
- **Decision proposed — secrets:** move provider API keys from `UserDefaults`
  to iOS Keychain during this task.
- **Decision proposed — default application plugins:** use the explicit
  iOS-safe list above; additions require dependency and UI verification.
- **Material feasibility question — vendor SDKs:** the OpenAI and Anthropic SDK
  closures may require native extensions unavailable in the current Python
  Apple Support bundle. The recommended fallback is an iOS-safe transport path
  inside the existing provider packages. A separate reduced provider fork
  would require renewed approval.
- **External dependency — hosted credentials:** final real-service evidence
  needs valid OpenAI, OpenRouter, and Anthropic keys and may incur API cost.
- **Excluded:** Bash/TaskStop, MCP, WebSearch/Tavily, restricted Python,
  ChatGPT login, local-model fallback, arbitrary roots, image/PDF file reading,
  cloud/rebuild plugins, and polished cross-platform settings.

### Documentation

- Add package-user and development documentation under
  `plugins/embedded-runtime-tools/`.
- Update the mobile embedded-runtime guide with the preconfigured connection,
  Home settings, four providers, Keychain ownership, tool matrix, application
  actions, setup, and verification.
- Update provider docs only when an owning provider gains an iOS-safe transport
  or documented embedded-runtime behavior.
- Update the existing embedded-runtime specification requirements/evidence
  rather than creating another specification unless implementation reveals a
  materially separate long-lived contract.
- Keep public docs explicit that `WebFetch` is not Tavily search and that
  provider API use sends user/tool content to the selected external service.

### Task checklist

- [ ] Prove the separate tool-package staging path by moving `Read`/`Write` and
  rerunning the existing real-model simulator flow.
- [ ] Implement and unit-test shared workspace authorization plus `Edit`,
  `Glob`, `Grep`, and `apply_patch`.
- [ ] Implement and unit/integration-test bounded public `WebFetch`.
- [ ] Run the OpenAI Responses and Anthropic iOS dependency/import spike.
- [ ] Bundle and configure the four provider profiles and minimal extension
  sets.
- [ ] Implement the provider-specific tool matrix and interop tests.
- [ ] Add versioned native settings with Keychain-backed provider keys,
  validation, reload, and rollback.
- [ ] Preconfigure and auto-open the local iOS connection.
- [ ] Add the Home-menu Local Runtime Settings window and focused component
  tests.
- [ ] Bundle the selected application plugins and replace embedded router
  stubs with real application/action/snapshot/settings parity.
- [ ] Verify fork, copy, delete, snapshot restore, title, search, pin, archive,
  status, ordering, and attachment behavior through production mobile
  consumers.
- [ ] Run real-provider tool smokes for the reviewer proxy, OpenAI Responses,
  OpenRouter, and Anthropic.
- [ ] Pass production-screen simulator acceptance for settings, web fetch,
  file mutation, application actions, persistence, and backgrounding.
- [ ] Update package/mobile/provider documentation, requirement evidence, and
  completion notes.

### Requirement verification

- Tool package: package tests and archive inspection prove all tools come from
  the separate package, share one workspace guard, and expose no out-of-root
  filesystem path.
- Web fetch: deterministic DNS/redirect/size/timeout tests plus a simulator
  fetch of a public page prove bounded public HTTP(S) behavior and private
  destination rejection.
- Providers: release-simulator import/build evidence covers all four provider
  closures; app-layer tests prove each provider receives the intended common
  schemas and writer slot; real API smokes complete representative tool loops.
- Settings and connection: production component/Detox tests prove the local
  connection exists before setup, Home opens the dedicated modal, secrets are
  masked/not returned, invalid candidates preserve the current runtime, and a
  valid save reloads while retaining sessions/workspace.
- Application plugins: in-process backend integration and production mobile
  tests prove real action/UI-schema contracts for fork/delete/snapshots,
  titles, list metadata/actions/filters, and attachments.
- End-to-end: one release-simulator flow configures the review-compatible
  provider, uses `WebFetch` plus file mutation/readback, performs session and
  message actions, relaunches, and backgrounds without losing or duplicating
  work.

### Additional implementation verification

- Run the new tool package's default tests and Ruff checks.
- Run affected provider package suites:
  `reference-openai-compatible-provider`, `openai_responses`, `openrouter`, and
  `anthropic-compatible`.
- Run focused Core/application tests for plugin loading, application actions,
  snapshots, configuration reload, and embedded routing.
- Run the full frontend SDK and relevant mobile Jest suites plus
  `npm run tsc`.
- Build the Release iOS simulator app and inspect the bundled Python archive
  for all selected source/data files and unsupported native modules.
- Run focused Detox setup/provider/tool/application-action/persistence/
  background scenarios before broader mobile E2E.
- Run credential scans over config, sessions, logs, connection persistence,
  and committed files.
- Treat skipped credential-gated hosted tests as not run, not as passing
  evidence.

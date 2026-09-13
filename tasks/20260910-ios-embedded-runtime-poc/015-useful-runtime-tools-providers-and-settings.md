# Make The Embedded Runtime Minimally Useful

Turn the completed iOS proof of concept into a preconfigured local runtime with
separate Claude-like and Codex-like workspace tool packages, four supported
provider profiles, dedicated Home-menu settings, and the iOS-safe application
actions from the ordinary default configuration.

## Requirements checklist

- [x] Separate first-party Claude-like and Codex-like plugin packages under
  `plugins/` own the embedded runtime's model-visible tools; the tools are no
  longer implemented inside the mobile bridge module.
- [x] A shared, model-invisible iOS-safe engine package owns workspace
  authorization, text reading/writing/editing, file enumeration, text search,
  patching, and public HTTP fetching without imposing one vendor's schemas.
- [x] The Claude-like plugin package exposes fully implemented `Read`, `Write`,
  `Edit`, `Glob`, `Grep`, and `WebFetch` tools with Claude-like names, schemas,
  and result presentation for their documented text/workspace scope.
- [x] The Codex-like plugin package exposes fully implemented lowercase
  `sed`, `rg`, `find`, `curl`, and `apply_patch` tools with command-oriented
  parameter descriptions and Bash-like result presentation.
- [x] Every filesystem-mutating or inspecting tool is restricted to the
  canonical app workspace and rejects absolute paths, traversal, and symlink
  escape.
- [x] Claude-like `WebFetch` and Codex-like `curl` accept only public HTTP(S)
  URLs, revalidate redirects, reject local/private/reserved destinations, and
  bound time, redirects, downloaded bytes, and returned text.
- [x] Four fixed provider-backed agents are available through the local
  runtime: generic OpenAI-compatible, OpenAI Responses, OpenRouter, and the
  official Anthropic API.
- [x] Each fixed agent explicitly identifies its tool family. Generic
  OpenAI-compatible, OpenRouter, and Anthropic use the Claude-like set in this
  task; OpenAI Responses uses the Codex-like set.
- [x] The local connection is created automatically and can list existing
  sessions before any provider credential is configured.
- [x] A separate Local Runtime Settings window is accessible from the Home
  menu and configures each provider's API key, base URL, model, enabled state,
  and the default agent.
- [x] Provider API keys are stored in the native credential owner rather than
  saved connection records, AsyncStorage, sessions, tool results, logs, or
  committed configuration.
- [x] Saving settings validates a candidate provider configuration and performs
  a complete embedded `AgentApplication` reconstruction while preserving
  sessions and workspace files.
- [x] The embedded application loads the selected iOS-safe default application
  plugins and exposes their real application/session/message actions through
  the production mobile UI.
- [x] Users can at minimum fork/copy/delete sessions, delete message ranges,
  restore automatic snapshots, edit/generate titles, search/filter sessions,
  and use pin/archive/status metadata.
- [x] Simulator acceptance covers the preconfigured connection, settings and
  reload, provider/tool interoperability, simple web fetch, application
  actions, persistence, and background lifecycle without a deterministic
  product provider.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md

## Proposed scope decisions

- **Tool package structure:** create model-invisible
  `plugins/embedded-tools-shared`, model-visible
  `plugins/embedded-claude-tools`, and model-visible
  `plugins/embedded-codex-tools`. This leaves room for later
  `embedded-kimi-tools` and `embedded-gemini-tools` wrappers over the same
  engines.
- **Claude-like set:** expose `Read`, `Write`, `Edit`, `Glob`, `Grep`, and
  `WebFetch` with Claude-like schemas and results.
- **Codex-like set:** expose lowercase `sed`, `rg`, `find`, `curl`, and
  `apply_patch`. Each safe in-process tool describes the shell command it
  emulates and returns a Bash-like command/exit-code/wall-time/output envelope.
- **Unsupported tools:** Bash/shell execution, TaskStop, MCP, WebSearch,
  image/PDF reading, and package installation are not included.
- **Provider shape:** expose four fixed agents rather than dynamically changing
  one provider identity. Agent labels explicitly include the provider and tool
  family; settings select the default new-session agent while all configured
  agents remain selectable.
- **Initial tool-family mapping:** generic OpenAI-compatible, OpenRouter, and
  Anthropic agents are Claude-like; OpenAI Responses is Codex-like.
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
  surfaces. The new shared engine should extract or directly reuse only proven
  iOS-safe modules rather than bundling the complete package accidentally.
- The first Luna probe initially failed before reaching the API because
  importing `codex-tools` eagerly imported its MCP wrapper and a transitive
  runtime module was absent. The embedded Codex-like package must import only
  its five declared tools and shared engines.
- The existing Codex `apply_patch` parser/runtime is pure Python and can be
  adapted into the Codex-like package with the same workspace authorization
  boundary.
- A simple `WebFetch` does not need Claude's prompt-driven nested model call or
  `trafilatura`. The shared engine can provide bounded HTTP(S), redirect
  validation, charset handling, standard-library HTML text extraction, and
  truncation. The Claude-like wrapper presents extracted page content; the
  Codex-like `curl` wrapper presents a bounded response body in a shell-shaped
  result.

### Codex tool-shape investigation

On September 10, 2026, a real OpenAI Responses API investigation used
`gpt-5.6-luna`, the repository's current Codex instructions, and a synthetic
isolated workspace. The only tool-visible workspace data was generated fixture
text; the URL case used `https://example.com`. API keys and private user data
were neither printed nor committed.

With the existing unrestricted `shell_command` plus `apply_patch`, Luna chose:

- line-range read:
  `sed -n '8,13p' notes.txt`;
- recursive content search:
  `rg -n --hidden --no-heading --color=never 'ORBITAL_MARKER' .`;
- recursive Markdown listing:
  `find docs -type f \( -iname '*.md' -o -iname '*.markdown' \) -print | LC_ALL=C sort`;
- edit and verification:
  `sed -n '1,120p'`, then `apply_patch`, then the same `sed` read;
- URL retrieval:
  `curl -L --fail --silent --show-error https://example.com`.

A second API run removed `shell_command` and advertised only candidate
in-process lowercase tools. Luna selected `sed`, `rg`, `find`, `apply_patch`,
and `curl` for the corresponding five cases without prompting for a generic
shell. It also accepted Bash-like synthetic results containing the equivalent
command, exit code, wall time, and output. The edit case again used `sed` →
`apply_patch` → `sed`.

These results support the following Codex-like initial contracts:

- `sed(path, from_line, to_line, show_line_numbers)` for bounded text reads;
- `rg(pattern, path, fixed_strings, case_sensitive, include_hidden, glob,
  context_lines, max_results)` for recursive content search;
- `find(path, name, type, include_hidden, max_depth, sort, max_results)` for
  path enumeration;
- `curl(url, follow_redirects, fail_on_http_error, timeout_seconds, max_bytes,
  include_headers)` for bounded public GET requests;
- freeform `apply_patch` for file creation, update, and deletion.

The model requested very large result limits in the candidate run. Tool
implementations must clamp model-supplied values to app-owned limits rather
than treating requested limits as authority.

### Provider feasibility

- Generic OpenAI-compatible and OpenRouter already use the `requests` closure
  proven by subtask `010`.
- OpenAI Responses imports the OpenAI Python SDK; Anthropic imports the
  Anthropic Python SDK. Their current transitive closures have not been proven
  in the embedded iOS interpreter and may include native extensions.
- The Luna investigation confirmed that an unconstrained development install
  currently pulls native packages including `jiter`, `pydantic-core`, and
  `lxml`, as well as unrelated MCP/web-fetch dependencies through eager
  `codex-tools` imports. The embedded packages must not inherit that closure.
- The declared `openai>=2` range also resolved to OpenAI SDK 3.11.0 during the
  probe, and the current provider's follow-up tool request failed because the
  SDK serialized an API alias as `async_`. Pinning the probe to the 2.x line
  resolved the request. The iOS bundle therefore needs an exact, tested
  provider dependency lock rather than a floating vendor-SDK major version.
- The first provider checkpoint must therefore import and execute minimal
  network calls for both SDK-backed providers in the simulator. If their
  closures are not iOS-compatible, prefer adding an iOS-safe transport path to
  the existing provider packages while preserving their public provider and
  extension contracts. Do not introduce replacement product providers with
  divergent history/tool semantics merely to pass packaging.

### Provider profiles

Recommended fixed agents:

- reviewer/OpenAI-compatible with Claude-like tools, using
  `reference-openai-compatible-provider`;
- OpenAI Responses with Codex-like tools, using `openai_responses`;
- OpenRouter with Claude-like tools, using `openrouter`;
- Anthropic with Claude-like tools, using `anthropic-compatible` against the
  official API by default.

Each profile has enabled state, base URL, model, API-key presence, and a
connection test/model refresh action. Official service URLs are defaults for
OpenAI Responses, OpenRouter, and Anthropic. The review-compatible profile
keeps a configurable URL and model so it can point at the authenticated Ollama
proxy.

The provider profile and tool family remain separate configuration concepts
even though this task supplies only the four fixed pairings above. A later
agent can pair OpenRouter with Codex-, Kimi-, or Gemini-like tools without
changing provider credentials or the shared engines.

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

Status: Approved

Implement this as a sequence of working vertical checkpoints. Preserve the
completed `010` simulator flows while replacing inline proof-of-concept pieces
incrementally.

First create the model-invisible `plugins/embedded-tools-shared` library with
one canonical workspace resolver and pure-Python engines for bounded text
read/write/edit, enumeration, regex search, patch application, and public URL
fetch. The shared package exposes no model-visible tool names or schemas.

Create `plugins/embedded-claude-tools` with its own descriptor, packaging,
tests, README, and development documentation. Move the current workspace
`Read`/`Write` behavior into this package, backed by the shared engine, without
changing the completed proof-of-concept's visible behavior. Bundle the two
packages into iOS and rerun the authenticated Ollama `Read`/`Write` scenario.
This is the first implementation checkpoint and proves separate-package
discovery, app-zip staging, and shared workspace configuration.

Add Claude-like `Edit`, `Glob`, `Grep`, and `WebFetch` wrappers. Preserve the
useful Claude-facing names, parameter vocabulary, read-before-mutation guards,
and concise result shapes where they fit the supported text-only scope.
`Write` creates or replaces complete text, `Edit` performs exact bounded
replacements, `Glob` enumerates relative matches, and `Grep` performs bounded
Python-regex searches without spawning `rg`.

Create `plugins/embedded-codex-tools` as a separate plugin set backed by the
same shared engines. Implement the API-proven lowercase command tools:

- `sed` reads an inclusive 1-based line range and optionally prefixes line
  numbers;
- `rg` searches content with regex/fixed-string, case, hidden, glob, context,
  and result-limit options;
- `find` enumerates files/directories by starting path, filename glob, type,
  hidden policy, depth, sorting, and result limit;
- `curl` performs one bounded public HTTP(S) GET with redirect/error/header
  options;
- `apply_patch` accepts the established Codex freeform patch grammar.

Descriptions must state the representative command-line equivalent so Codex
can transfer its shell-trained behavior directly. `sed`, `rg`, `find`, and
`curl` results use a stable Bash-like envelope containing the equivalent
command, exit code, measured wall time, and bounded stdout/stderr. Preserve
command conventions such as `rg` exit code `1` for no matches. `apply_patch`
keeps the established Codex patch-result presentation. Tool implementations
never parse or execute a general command string.

Implement the shared public-fetch engine once. Resolve and validate every
destination before connecting and after every redirect; block loopback,
link-local, private, multicast, reserved, and non-HTTP(S) targets. Bound
DNS/connection/read time, redirect count, response bytes, and returned
characters. Support text and HTML with charset handling. The Claude-like
`WebFetch` wrapper returns extracted page text and metadata; the Codex-like
`curl` wrapper returns the bounded body and optional headers in its Bash-like
envelope.

Before building provider settings, run an iOS provider-closure spike. Define an
exact dependency lock for the embedded provider set rather than consuming
unbounded plugin requirements. Bundle the minimal OpenAI Responses and
Anthropic provider/extension entries, import them in the release simulator,
and perform the smallest model-discovery or mocked-network call that crosses
their actual transport construction. Record native-extension or resource
failures. If an SDK closure cannot run, add a narrowly scoped iOS-safe
transport adapter inside the owning provider package and verify that desktop
behavior and public history/tool contracts remain unchanged. Generic
OpenAI-compatible and OpenRouter remain on their existing `requests` paths.

Replace the single embedded provider config with four fixed provider profiles
and agents. Enable only the provider extensions needed for text streaming,
tools, reasoning/usage presentation, cancellation, and model discovery.
Attachments, native compaction, provider web search, ChatGPT auth, and other
extensions stay disabled until separately proven. Configure explicit
provider/tool-family pairings:

| Fixed agent | Provider package | Tool family and plugin package |
| --- | --- | --- |
| OpenAI-compatible reviewer · Claude-like | `reference-openai-compatible-provider` | Claude-like · `embedded-claude-tools` |
| OpenAI Responses · Codex-like | `openai_responses` | Codex-like · `embedded-codex-tools` |
| OpenRouter · Claude-like | `openrouter` | Claude-like · `embedded-claude-tools` |
| Anthropic · Claude-like | `anthropic-compatible` | Claude-like · `embedded-claude-tools` |

Keep provider definitions, tool-family definitions, and agent pairings as
separate config objects. This makes later Kimi-like, Gemini-like, or
OpenRouter/Codex pairings additive instead of requiring tool-engine changes.

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

Finish with a provider/tool-family/application-action matrix. Deterministic
local HTTP fixtures may verify protocol edge cases, but product acceptance
uses real providers: the authenticated Ollama reviewer proxy for
OpenAI-compatible and credential-gated hosted smoke tests for OpenAI
Responses, OpenRouter, and Anthropic. Each Claude-like provider must complete
representative `Read`, `Write`, and `WebFetch` behavior. OpenAI Responses must
complete a Codex-like sequence using at least `sed`, `apply_patch`, and `curl`;
app-layer real-API coverage also exercises `rg` and `find`.

The production-screen simulator scenario should configure a provider from
Home, visibly identify the active tool family, fetch a small public page, save
or patch a workspace file, reload it, fork the session, delete a message with
an automatic snapshot, and survive process relaunch/backgrounding.

### Implementation decisions and open questions

- **Decision proposed — package structure:** use
  `embedded-tools-shared`, `embedded-claude-tools`, and
  `embedded-codex-tools` as separate packages. Only the latter two are plugin
  sets with model-visible schemas.
- **Decision proposed — Claude-like set:** `Read`, `Write`, `Edit`, `Glob`,
  `Grep`, and `WebFetch`.
- **Decision proposed — Codex-like set:** `sed`, `rg`, `find`, `curl`, and
  `apply_patch`, based on the successful Luna investigation.
- **Decision proposed — Codex presentation:** command names are lowercase;
  schemas explain their command-line equivalents; command results are
  Bash-like. No general shell parser or executor is added.
- **Decision proposed — agents:** expose the four fixed provider/tool-family
  pairings above and a default-agent setting rather than hot-swapping one
  agent's provider or tool identity.
- **Decision proposed — extensibility:** future Kimi-like and Gemini-like
  packages wrap the shared engines but are not implemented or planned in
  detail here.
- **Decision proposed — secrets:** move provider API keys from `UserDefaults`
  to iOS Keychain during this task.
- **Decision proposed — default application plugins:** use the explicit
  iOS-safe list above; additions require dependency and UI verification.
- **Material feasibility question — vendor SDKs:** the OpenAI and Anthropic SDK
  closures may require native extensions unavailable in the current Python
  Apple Support bundle. The recommended fallback is an iOS-safe transport path
  inside the existing provider packages. A separate reduced provider fork
  would require renewed approval.
- **Decision proposed — provider dependencies:** use an exact embedded-runtime
  lock and reject unreviewed vendor-SDK major upgrades. The planning probe
  demonstrated that `openai>=2` is not a sufficient reproducibility boundary.
- **External dependency — hosted credentials:** final real-service evidence
  needs valid OpenAI, OpenRouter, and Anthropic keys and may incur API cost.
- **Excluded:** Bash/TaskStop, MCP, WebSearch/Tavily, restricted Python,
  ChatGPT login, local-model fallback, arbitrary roots, image/PDF file reading,
  cloud/rebuild plugins, and polished cross-platform settings.

### Documentation

- Add package-user and development documentation under
  `plugins/embedded-claude-tools/` and `plugins/embedded-codex-tools/`, plus a
  concise engine contract under `plugins/embedded-tools-shared/`.
- Update the mobile embedded-runtime guide with the preconfigured connection,
  Home settings, four providers, Keychain ownership, explicit Claude-like/
  Codex-like agent labels, tool-family matrix, application actions, setup, and
  verification.
- Update provider docs only when an owning provider gains an iOS-safe transport
  or documented embedded-runtime behavior.
- Update the existing embedded-runtime specification requirements/evidence
  rather than creating another specification unless implementation reveals a
  materially separate long-lived contract.
- Keep public docs explicit that `WebFetch` is not Tavily search and that
  `curl` is not a general shell command. State that provider API use sends
  user/tool content to the selected external service.

### Task checklist

- [x] Create and test the model-invisible `embedded-tools-shared` engine
  package.
- [x] Prove the Claude-like plugin-package staging path by moving
  `Read`/`Write` and rerunning the existing real-model simulator flow.
- [x] Implement and unit-test Claude-like `Edit`, `Glob`, `Grep`, and
  `WebFetch`.
- [x] Implement and unit-test Codex-like `sed`, `rg`, `find`, `curl`, and
  `apply_patch` with lowercase schemas and Bash-like results.
- [x] Add cross-package conformance tests proving both tool families use the
  same workspace and public-network authorization engines.
- [x] Run the OpenAI Responses and Anthropic iOS dependency/import spike.
- [x] Produce an exact embedded provider dependency lock and reject unsupported
  native modules or unreviewed major upgrades.
- [x] Bundle and configure the four provider profiles and minimal extension
  sets.
- [x] Implement the four explicit provider/tool-family pairings and interop
  tests.
- [x] Add versioned native settings with Keychain-backed provider keys,
  validation, reload, and rollback.
- [x] Preconfigure the local iOS connection and allow credential-free opening.
- [x] Add the Home-menu Local Runtime Settings window and focused component
  tests.
- [x] Bundle the selected application plugins and replace embedded router
  stubs with real application/action/snapshot/settings parity.
- [x] Verify fork, copy, delete, snapshot restore, title, search, pin, archive,
  status, ordering, and attachment behavior through production mobile
  consumers.
- [x] Run real-provider Claude-like smokes for the reviewer proxy, OpenRouter,
  and Anthropic, plus a Codex-like OpenAI Responses smoke.
- [x] Pass production-screen simulator acceptance for settings, web fetch,
  file mutation, application actions, persistence, and backgrounding.
- [x] Update package/mobile/provider documentation, requirement evidence, and
  completion notes.

### Requirement verification

- Tool packages: descriptor/package tests and archive inspection prove
  Claude-like and Codex-like schemas come from separate plugin sets, while
  shared engines remain model-invisible.
- Claude-like tools: package and real-provider tests prove the PascalCase
  `Read`/`Write`/`Edit`/`Glob`/`Grep`/`WebFetch` contracts are complete within
  the documented text/workspace scope.
- Codex-like tools: schema/result tests prove lowercase
  `sed`/`rg`/`find`/`curl`/`apply_patch` contracts, command-equivalent
  descriptions, Bash-like command results, and absence of a general shell
  executor. A real Luna tool loop proves the model uses the decomposed set.
- Shared authorization: cross-family tests prove all filesystem tools use one
  workspace guard and expose no out-of-root path.
- Public fetching: deterministic DNS/redirect/size/timeout tests plus simulator
  `WebFetch` and `curl` calls prove bounded public HTTP(S) behavior and private
  destination rejection.
- Providers: release-simulator import/build evidence covers all four provider
  closures and their exact locked dependencies; app-layer tests prove each
  fixed agent receives only its intended tool family; real API smokes complete
  representative Claude-like or Codex-like loops.
- Settings and connection: production component/Detox tests prove the local
  connection exists before setup, Home opens the dedicated modal, secrets are
  masked/not returned, invalid candidates preserve the current runtime, and a
  valid save reloads while retaining sessions/workspace.
- Application plugins: in-process backend integration and production mobile
  tests prove real action/UI-schema contracts for fork/delete/snapshots,
  titles, list metadata/actions/filters, and attachments.
- End-to-end: release-simulator flows configure the review-compatible
  Claude-like provider and the OpenAI Responses Codex-like provider, exercise
  public fetch plus file mutation/readback, perform session and message
  actions, relaunch, and background without losing or duplicating work.

### Additional implementation verification

- Run all three embedded tool packages' default tests and Ruff checks.
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

## Implementation Notes

- 2026-09-10: The user approved the Draft execution plan. Execution begins
  with the shared engine package and Claude-like `Read`/`Write` extraction,
  followed by the existing authenticated Ollama simulator regression.
- 2026-09-10: Added model-invisible `embedded-tools-shared` workspace/text
  primitives and the separate `embedded-claude-tools` plugin package. Removed
  the model-visible `Read`/`Write` implementations from the mobile bridge and
  staged both packages in the fixed iOS archive.
- 2026-09-10: Thirteen focused package/mobile runtime tests and Ruff passed,
  archive inspection found the new modules and no inline bridge tool classes,
  and the Release simulator build succeeded.
- 2026-09-10: The unchanged authenticated Ollama
  `qwen3.5:0.8b` Detox scenario passed in 71.6 seconds. It completed the
  production-screen `Read`/`Write` flow, verified output, relaunched with the
  same session/workspace, and did not expose the temporary proxy key in logs.
- 2026-09-10: Extended `embedded-tools-shared` with exact editing, bounded
  enumeration/search, Codex-style patch parsing, and a public-only HTTP(S)
  client that pins validated DNS addresses, revalidates redirects, and verifies
  TLS with the bundled CA store.
- 2026-09-10: Completed the Claude-like
  `Read`/`Write`/`Edit`/`Glob`/`Grep`/`WebFetch` package and the separate
  lowercase Codex-like `sed`/`rg`/`find`/`curl`/`apply_patch` package. The
  existing reviewer agent now advertises the full Claude-like set; the Codex
  set is staged but not yet assigned to an iOS agent.
- 2026-09-10: Thirty-nine package/mobile tests and Ruff passed; archive
  inspection found all shared and model-facing modules. A verified live fetch
  of `https://www.python.org/` returned HTTP 200 and the expected page title.
- 2026-09-10: A credential-gated real OpenAI Responses test using
  `gpt-5.6-luna` passed in 22.3 seconds and used all five implemented Codex-like
  tools, including a successful workspace patch and public fetch.
- 2026-09-10: The Release simulator build passed with both tool families. The
  unchanged authenticated Ollama `qwen3.5:0.8b` production-screen test passed
  in 84.1 seconds with all six Claude-like tools advertised, preserved the
  expected file output across relaunch, and did not log the temporary key.
- 2026-09-10: Added opt-in package-owned `requests` transports for OpenAI
  Responses and Anthropic, including models, non-streaming/streaming messages,
  provider error shape, and lazy vendor-SDK imports. Existing configurations
  remain on the official SDK transports.
- 2026-09-10: The requests transports passed 106 focused OpenAI Responses tests
  and 24 Anthropic tests, including subprocess imports with each vendor SDK
  deliberately blocked. The real Luna five-tool test passed through the
  requests transport in 19 seconds.
- 2026-09-10: The iOS archive now contains provider source/data and the exact
  pinned requests closure while excluding `openai`, `anthropic`, `jiter`,
  `pydantic`, and `pydantic-core`. Release simulator build and credential-free
  Detox passed; the production diagnostic constructed both requests clients
  inside embedded CPython.
- 2026-09-10: Full fast provider verification passed: 425 OpenAI Responses
  tests with 92 hosted/manual tests deselected, and 63 Anthropic tests with 24
  hosted tests deselected. Three OpenAI native-history tests were corrected to
  set `image_attachment_mode: "upload"` explicitly because their assertions
  required image upload while the current documented default is inline.
- 2026-09-11: Replaced the single embedded proxy configuration with four
  versioned profiles and fixed agents: reviewer/OpenAI-compatible,
  OpenAI Responses, OpenRouter, and Anthropic. Source integration constructs
  all four agent cores, assigns Claude-like tools to reviewer, OpenRouter, and
  Anthropic, assigns Codex-like tools to OpenAI Responses, and honors the
  configured default agent.
- 2026-09-11: Added a dedicated Home settings window with enabled/default,
  endpoint, model, masked API-key, removal, candidate validation, and save
  controls. URLs/models/enabled state persist in `UserDefaults`; per-provider
  keys persist as Keychain generic-password items. The legacy reviewer key is
  migrated and removed from `UserDefaults`.
- 2026-09-11: The built-in on-device connection is seeded during iOS
  connection hydration and opens before credential validation. Candidate
  validation runs without replacing stored settings, so a failed test leaves
  the prior configuration intact.
- 2026-09-11: Release simulator setup Detox passed in 91.3 seconds against an
  isolated authenticated Ollama proxy: the built-in connection was present,
  a wrong key was rejected, the correct reviewer profile validated and saved,
  the connection opened, and relaunch showed a masked Keychain-backed key.
  The authenticated multi-turn Claude-like Read/Write test then passed in 66.9
  seconds and preserved the expected workspace output across relaunch.
- 2026-09-11: Bundled the iOS-safe default application plugins for session
  actions, title editing/generation, search, message-count/timestamp metadata,
  pin, archive, status, ordering, and generic attachment download. Replaced
  embedded stubs with `AgentApplication` delegation for action/UI discovery,
  action execution, plugin overrides, snapshots, readonly selection, restore,
  fork, message deletion, and server settings.
- 2026-09-11: The public in-process route matrix passed five tests and covered
  title/archive/pin/status actions, copy/delete/fork, Python-style range
  deletion with an automatic snapshot, readonly selection and restore, search
  and ordering UI schema, server settings, plugin overrides, generated-title
  discovery, and attachment download. Generate-title's own fast suite passed
  13 tests with two integration tests deselected.
- 2026-09-11: Real provider checks passed using the production embedded tool
  packages: OpenRouter Claude-like `Write`/`Read`/`WebFetch` in 9.8 seconds,
  official Anthropic through `provider_transport: requests` in 9.5 seconds,
  and OpenAI Responses Luna with all five Codex-like tools in 20.1 seconds.
  The authenticated reviewer simulator previously passed the persisted
  Read/Write workflow and application-action matrix; an isolated real Ollama
  probe also emitted and executed `WebFetch` with the single-tool required
  configuration.
- 2026-09-11: Fixed bounded gzip/deflate decoding in the shared public fetcher
  after Python.org ignored `Accept-Encoding: identity`. Ten focused fetch
  tests and a live host fetch passed. The dedicated Release simulator WebFetch
  test then extracted `Welcome to Python.org` in 38 seconds.
- 2026-09-11: Final simulator checks passed on the Release build: Home provider
  setup/preconfigured connection in 77.5 seconds and delayed background
  continuation in 88.9 seconds. Credential/archive scanning found no
  credential-like values in changed files and no bundled OpenAI/Anthropic SDK
  or native `jiter`/`pydantic-core` closure.
- 2026-09-11: Full frontend verification passed: 182 mobile Jest tests, 342
  frontend SDK tests, 51 shared React Native component tests, and TypeScript.
  Default embedded-package tests passed with 26 shared-engine, seven
  Claude-like, and four Codex-like tests; hosted tests remained explicitly
  gated.
- 2026-09-11: Broad suites in untouched neighboring code still expose known
  baseline/test-harness failures: three OpenRouter metadata/web-search
  assertions, reference-provider rate-limit tests that monkeypatch
  `requests.post` while runtime code uses `Session.post`, and standalone
  session-plugin tests with stale event-store assumptions, unknown-agent
  deletion expectations, or cross-package runtime-overlay/pip isolation.
  Changed-file provider tests, focused OpenRouter tests (38), the embedded
  route matrix, and all acceptance tests above passed.

## Completion Notes

- Completed the minimally useful embedded runtime with separate shared,
  Claude-like, and Codex-like tool packages; four configurable provider
  profiles; Keychain-backed settings; a preconfigured local connection; and
  iOS-safe application/session actions.
- Requirement evidence includes package and route tests, exact archive
  inspection, real OpenRouter/Anthropic/OpenAI tool loops, authenticated
  reviewer simulator runs, Home settings and Keychain persistence, dedicated
  simulator WebFetch, application action/snapshot behavior, relaunch
  persistence, and background continuation.
- OpenAI Responses and Anthropic use package-owned requests transports in the
  embedded archive. Ordinary installations retain official SDK transports.
  The archive deliberately excludes the vendor SDK/native dependency closure.
- The implementation added opt-in OpenAI-compatible `tool_choice` forwarding
  after real Ollama investigation. Its default remains `auto`.
- App Review deployment hardening, ChatGPT login, Tavily search, restricted
  Python execution, email tools, arbitrary workspaces, and future Kimi/Gemini
  tool families remain outside this subtask. Tavily and Python are tracked by
  subtasks `020` and `030`.
- The unrelated user-owned SSH resolution change in
  `mobile/crystal-lattice-control-rn/package-lock.json` was preserved and not
  committed.

## Post-completion follow-up

The user reopened this subtask on September 13, 2026 after a real-device
OpenAI Responses request exposed a package-resource path that worked from an
editable source checkout but failed when imported from
`crystal_lattice_app.zip`.

### Follow-up requirements checklist

- [ ] The existing unit and integration tests in each provider package
  intended for the embedded ZIP run with that provider imported from the
  generated ZIP rather than from an editable/source installation.
- [ ] Root `package.json` provides discoverable commands for the important
  embedded-provider bundle suites, automated real-API Detox matrix, manually
  gated ChatGPT-action Detox path, and reviewer-proxy tests.
- [ ] Release-simulator real-API Detox covers the generic OpenAI-compatible
  provider through Ollama, OpenAI Responses with an API key, OpenAI Responses
  with the existing ChatGPT login actions, OpenRouter, Anthropic, and the
  deployed reviewer proxy.
- [ ] The embedded ZIP contains and configures the existing OpenAI Responses
  ChatGPT authentication/action plugins; no new login-specific UI is required.
- [ ] The generic OpenAI-compatible provider remains endpoint-agnostic and is
  not specialized for OpenAI or the reviewer deployment.
- [ ] Enabling a provider after using the credential-free `local` agent does
  not make existing local sessions unloadable or otherwise unusable.
- [ ] `tools/openai-proxy` accepts a JSON configuration path from its CLI,
  supports separate incoming and outgoing API keys through environment
  variables, and preserves its existing general-purpose mode.
- [ ] Reviewer-proxy, deployment, TLS, pricing, budget, model, authentication,
  logging, test-matrix, and path values are configuration rather than
  hard-coded behavior.
- [ ] The reviewer proxy exposes only `gpt-5.6-luna`, rejects requests for
  other models, and forwards successful requests with the configured upstream
  OpenAI API key rather than the caller credential.
- [ ] The reviewer proxy calculates standard-tier GPT-5.6 Luna cost from
  returned input, cached-input, and output usage; ignores web-search charges;
  persists accumulated cost; and rejects model/inference requests for 24 hours
  after the configured USD 1 threshold is reached.
- [ ] Ireland hosts the reviewer proxy on an explicitly approved TCP port over
  self-signed HTTPS, with a trusted/pinned app path, Docker Compose lifecycle,
  JSON configuration, protected environment file, certificate material, and
  persistent limiter state.
- [ ] App Review instructions can provide the HTTPS endpoint, allowed model,
  and private caller API key, and an external Release-simulator test proves
  that this reviewer path completes a real tool-using request.

### Approved testing amendment

Status: Approved

- Build the iOS application ZIP before provider tests.
- Run the existing tests from
  `plugins/reference-openai-compatible-provider/tests`,
  `plugins/openai_responses/tests`, `plugins/openrouter/tests`, and
  `plugins/anthropic-compatible/tests` with their runtime package imports
  forced to the generated `crystal_lattice_app.zip`.
- Do not duplicate the provider suites or invent replacement behavior tests.
  Test files and development-only helpers may remain in their package trees,
  but provider runtime modules and packaged resources must resolve from the
  ZIP. The runner must fail if import provenance falls back to a source or
  editable installation.
- Apply each package's existing marker policy. Existing non-API integration
  tests and credential-gated hosted integration tests also run from the ZIP;
  manual tests remain explicitly gated and skipped tests count as not run.
- Add root scripts backed by a small orchestrator rather than long inline
  commands:
  - `test:ios:embedded-providers:bundle`
  - `test:ios:embedded-providers:bundle:api`
  - `test:ios:embedded-providers:detox:api`
  - `test:ios:embedded-providers:detox:chatgpt`
  - `test:reviewer-proxy`
- The automated Release-simulator real-API matrix configures and sends a
  minimal tool-using request through the generic Ollama path, OpenAI Responses
  API-key path, OpenRouter, Anthropic, and the deployed reviewer endpoint.
- The OpenAI Responses ChatGPT path is collected with the matrix but has a
  separate manual-integration gate. It uses the existing authentication
  actions and generic action UI, waits for the human login step, then verifies
  a real Codex-like tool request and credential reuse after relaunch.
- Provider acceptance requires a terminal assistant response, no error
  card/event, the intended tool-family round trip, and session persistence.
- The matrix begins with a credential-free local session, enables a provider,
  reloads the embedded application, and verifies that the pre-existing local
  session remains usable. This transition is intended to expose the currently
  reported local-agent issue.

### Execution plan

Status: Approved

Implement and deploy a narrowly scoped App Review proxy in the same follow-up
change, then use it as the external-review row of the approved Detox matrix.
The user approved execution on September 13, 2026 with the additional
constraint that all operational values remain configurable.

#### Proxy configuration and behavior

- Extend `tools/openai-proxy` with an optional
  `--config <reviewer-proxy.json>` mode while keeping the existing positional
  CLI compatible.
- Keep the proxy implementation generic: endpoint, listen host/port, base
  path, environment-variable names, allowed models, service tiers, budget,
  cooldown, pricing, long-context thresholds/multipliers, state path, logging,
  and status behavior all come from configuration. Reviewer-specific values
  belong only in the deployment JSON and environment file.
- Keep secrets out of JSON. The configuration names two environment
  variables:
  - `OPENAI_UPSTREAM_API_KEY` for outgoing OpenAI requests;
  - `REVIEWER_PROXY_API_KEY` for incoming bearer authentication.
- Use a schema like:

  ```json
  {
    "upstream": {
      "base_url": "https://api.openai.com/v1",
      "api_key_env": "OPENAI_UPSTREAM_API_KEY"
    },
    "client_auth": {
      "api_key_env": "REVIEWER_PROXY_API_KEY"
    },
    "models": {
      "allowed": ["gpt-5.6-luna"]
    },
    "budget": {
      "limit_usd": 1.0,
      "cooldown_seconds": 86400,
      "state_path": "/data/rate-limit.json",
      "pricing_per_million": {
        "input": 0.20,
        "cached_input": 0.02,
        "output": 1.20
      },
      "long_context": {
        "input_token_threshold": 272000,
        "input_multiplier": 2.0,
        "cached_input_multiplier": 2.0,
        "output_multiplier": 1.5
      },
      "ignored_charges": ["web_search"]
    },
    "logging": {
      "headers": false,
      "bodies": false
    }
  }
  ```

- Treat total input as including cached input and calculate:
  `uncached_input = max(0, input_tokens - cached_tokens)`, then price uncached
  input, cached input, and output separately. Support equivalent usage fields
  from Responses and Chat Completions so the generic reviewer profile remains
  protocol-compatible.
- Restrict model listing to `gpt-5.6-luna` and reject any request body naming a
  different model. Use standard/default service tier pricing and reject
  explicitly requested pricing modes not represented by the configured rate
  table.
- Parse completed JSON and streaming SSE usage without delaying ordinary
  streaming delivery. Atomically persist cost after a completed response.
- Let the request that reaches/crosses the USD 1 limit finish, set
  `blocked_until` to 24 hours after that completion, and return HTTP 429 with
  `Retry-After` for subsequent model-listing and inference requests. Serialize
  charged requests for this single-key reviewer deployment so concurrent
  requests cannot bypass the ledger.
- Keep health/status output free of secrets and private request content. It
  may expose the configured model, blocked state, remaining cooldown, and
  aggregate spend.

The current official standard GPT-5.6 Luna prices, verified September 13,
2026, are USD 0.20 per million input tokens, USD 0.02 per million cached input
tokens, and USD 1.20 per million output tokens. Requests above 272,000 input
tokens price the full request at 2x input and 1.5x output. Pricing remains
configuration data so it can be updated without changing proxy code.

#### Self-signed TLS and generic-provider trust

- Recommend TCP port `3443` for the reviewer endpoint.
- Make the TLS listen port, hostname, certificate paths, upstream proxy
  address, and trust-bundle path configurable; `3443` is only the Ireland
  deployment value.
- Terminate TLS in a small reverse-proxy container in front of the Node proxy,
  using a self-signed certificate whose SAN matches
  `ireland-s1.dynamicprogrammingsolutions.com`.
- Do not disable certificate verification. Add an optional custom-CA setting
  to the generic OpenAI-compatible provider and stage the public reviewer CA
  certificate as an ordinary app/runtime resource. Preconfigure only the
  reviewer profile with that CA path; other OpenAI-compatible endpoints remain
  configurable and use normal trust by default.
- Certificate rotation requires updating the pinned public certificate in a
  later app build. Private certificate keys stay only in the protected server
  directory.

#### Ireland deployment

- Create `/home/irelandsrv/reviewer-openai-proxy/` containing:
  - `docker-compose.yml`;
  - `config/reviewer-proxy.json`;
  - `.env` with mode `0600`;
  - `certs/` with protected private key and public certificate;
  - `data/` for the persisted rate-limit ledger.
- Transfer the current root `.env` OpenAI key without printing it or embedding
  it in commands, logs, images, configuration, or git history. Generate a
  separate high-entropy incoming reviewer key and protect both values in the
  remote `.env`.
- Inspect the Ireland instance/security-group identity read-only, then propose
  the exact AWS CLI ingress command for TCP `3443`. Because opening a public
  ingress rule and starting remote containers are high-impact operations,
  pause for the required explicit confirmation before running those exact
  commands.
- Open only the selected TCP port, bind the public TLS service there, keep the
  inner Node port on the Compose network, and verify restart persistence and
  Docker Compose start/stop commands.

#### Runtime behavior and acceptance

- Keep the OpenAI-compatible provider generic. Its automated local matrix row
  continues to use Ollama; the reviewer row proves the same provider against
  the configured HTTPS/OpenAI-backed endpoint.
- Preserve loadability of sessions created with the credential-free `local`
  agent when real profiles are enabled. Recommendation: retain the legacy
  `local` agent internally while referenced sessions exist, but stop making it
  the default or offering it for new sessions after a real provider is
  available.
- Add/configure the existing OpenAI Responses ChatGPT authentication plugins
  and actions in the embedded ZIP. Use the generic action UI for login and
  status; do not create a new login-specific settings flow.
- Complete acceptance only after the Release simulator, using the external
  Ireland endpoint and caller key, validates the reviewer profile and finishes
  a real Claude-like tool request with persisted session/workspace results.

### Implementation decisions and open questions

- **Recommendation — port:** use public TCP `3443`. Approval of this Draft
  selects that Ireland deployment value unless the user requests another one;
  proxy and Compose code must not hard-code it.
- **Recommendation — cooldown:** one persisted global ledger for the single
  configured reviewer key; the threshold-crossing request completes and all
  subsequent model/inference requests are blocked for 24 hours.
- **Recommendation — TLS trust:** bundle/pin the public reviewer CA and retain
  certificate verification. Do not use `verify=false`.
- **Recommendation — local sessions:** preserve legacy local-session
  loadability without continuing to advertise the smoke agent for new
  sessions after a real provider is enabled.
- **Deployment confirmation:** even after plan approval, present the exact AWS
  ingress and remote Docker commands and obtain “yes, run exactly that” before
  changing the server or security group.
- **Approved constraint — configurability:** all operational and pricing
  values are represented in JSON, environment, Compose variables, or test
  inputs. Code may provide backward-compatible defaults but must not encode
  the Ireland reviewer deployment as the only supported behavior.

### Documentation

- Update `tools/openai-proxy` configuration, authentication, model-limit,
  budget, state, TLS, and Docker Compose operating documentation.
- Update embedded-runtime testing docs with the root bundle/API/Detox commands,
  ZIP import provenance, provider matrix, ChatGPT manual gate, and local-agent
  transition.
- Add an Ireland reviewer-proxy runbook covering secret transfer, certificate
  rotation, security-group ingress, deployment, logs, budget reset/cooldown,
  start/stop, and rollback.
- Update the App Review task/instructions with only the externally usable URL,
  `gpt-5.6-luna`, caller key handoff procedure, and minimal reviewer scenario;
  never include the upstream OpenAI key.

### Task checklist

- [x] Obtain approval for the testing and reviewer-proxy follow-up, including
  the all-values-configurable constraint.
- [ ] Add bundle-import orchestration for the existing four provider test
  suites and root `package.json` commands.
- [ ] Fix provider/package behavior exposed by running the existing tests from
  the ZIP, including packaged resource access.
- [ ] Add/configure the existing ChatGPT authentication/action plugins in the
  embedded runtime and add the manual Detox gate.
- [ ] Add the automated real-API Detox matrix and local-session transition
  scenario.
- [ ] Add JSON-configured model/auth/cost/cooldown behavior to
  `tools/openai-proxy` with focused proxy tests.
- [ ] Add generic-provider custom-CA support and stage the reviewer public
  certificate.
- [ ] Add reviewer Docker Compose/configuration/runbook assets without
  secrets.
- [ ] Present and obtain exact-command confirmation for AWS ingress and remote
  deployment.
- [ ] Transfer secrets securely, deploy on Ireland, and verify TLS,
  authentication, model filtering, ledger persistence, and restart behavior.
- [ ] Pass the external reviewer Release-simulator matrix row and update
  acceptance evidence.

### Requirement verification

- Provider ZIP suitability: the existing unit and integration suites for all
  four bundled providers pass while import provenance points into
  `crystal_lattice_app.zip`.
- Root test discoverability: each important bundle, API, Detox, manual
  ChatGPT, and proxy command is callable from root `package.json`.
- Provider matrix: Release Detox completes terminal, persisted, tool-using
  responses for Ollama-compatible, OpenAI Responses API-key, OpenRouter,
  Anthropic, and deployed reviewer paths; the gated ChatGPT action path does
  the same after manual login.
- Local transition: a session created with `local` before enabling a profile
  remains listable, loadable, and usable after settings save and application
  reconstruction.
- Proxy controls: caller authentication, upstream-key replacement, exact
  model allowlist, both usage shapes, long-context pricing, persistent USD 1
  threshold, 24-hour cooldown, restart recovery, and secret-free logging pass
  proxy tests.
- External review: a clean Release simulator reaches the public self-signed
  HTTPS endpoint using the pinned CA and private caller key and completes the
  documented reviewer scenario.

### Additional implementation verification

- Confirm the app ZIP contains the ChatGPT auth/action plugins and reviewer CA
  but no private key or API credential.
- Verify invalid caller keys and non-Luna model requests never reach OpenAI.
- Verify the incoming caller key is removed before forwarding and the
  configured upstream key is never returned or logged.
- Verify streaming and non-streaming usage are charged once, failed requests
  without completed usage are not fabricated, and limiter-state writes are
  atomic.
- Verify the blocked response survives container restart and automatically
  expires after the configured 24-hour cooldown.
- Verify only TCP `3443` is added for this service and the internal proxy port
  is not publicly bound.
- Verify repository, app logs, server logs, Compose output, and task evidence
  contain no secret values.

## Post-completion follow-up implementation notes

- 2026-09-13: The user approved the testing and reviewer-proxy execution plan
  and required every operational value to remain configurable. Local
  implementation begins before the mandatory exact-command confirmation for
  AWS ingress and Ireland deployment.

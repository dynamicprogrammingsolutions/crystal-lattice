# Make The Embedded Runtime Minimally Useful

Turn the completed iOS proof of concept into a preconfigured local runtime with
separate Claude-like and Codex-like workspace tool packages, four supported
provider profiles, dedicated Home-menu settings, and the iOS-safe application
actions from the ordinary default configuration.

## Requirements checklist

- [ ] Separate first-party Claude-like and Codex-like plugin packages under
  `plugins/` own the embedded runtime's model-visible tools; the tools are no
  longer implemented inside the mobile bridge module.
- [ ] A shared, model-invisible iOS-safe engine package owns workspace
  authorization, text reading/writing/editing, file enumeration, text search,
  patching, and public HTTP fetching without imposing one vendor's schemas.
- [ ] The Claude-like plugin package exposes fully implemented `Read`, `Write`,
  `Edit`, `Glob`, `Grep`, and `WebFetch` tools with Claude-like names, schemas,
  and result presentation for their documented text/workspace scope.
- [ ] The Codex-like plugin package exposes fully implemented lowercase
  `sed`, `rg`, `find`, `curl`, and `apply_patch` tools with command-oriented
  parameter descriptions and Bash-like result presentation.
- [ ] Every filesystem-mutating or inspecting tool is restricted to the
  canonical app workspace and rejects absolute paths, traversal, and symlink
  escape.
- [ ] Claude-like `WebFetch` and Codex-like `curl` accept only public HTTP(S)
  URLs, revalidate redirects, reject local/private/reserved destinations, and
  bound time, redirects, downloaded bytes, and returned text.
- [ ] Four fixed provider-backed agents are available through the local
  runtime: generic OpenAI-compatible, OpenAI Responses, OpenRouter, and the
  official Anthropic API.
- [ ] Each fixed agent explicitly identifies its tool family. Generic
  OpenAI-compatible, OpenRouter, and Anthropic use the Claude-like set in this
  task; OpenAI Responses uses the Codex-like set.
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

Status: Draft

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

- [ ] Create and test the model-invisible `embedded-tools-shared` engine
  package.
- [ ] Prove the Claude-like plugin-package staging path by moving
  `Read`/`Write` and rerunning the existing real-model simulator flow.
- [ ] Implement and unit-test Claude-like `Edit`, `Glob`, `Grep`, and
  `WebFetch`.
- [ ] Implement and unit-test Codex-like `sed`, `rg`, `find`, `curl`, and
  `apply_patch` with lowercase schemas and Bash-like results.
- [ ] Add cross-package conformance tests proving both tool families use the
  same workspace and public-network authorization engines.
- [ ] Run the OpenAI Responses and Anthropic iOS dependency/import spike.
- [ ] Produce an exact embedded provider dependency lock and reject unsupported
  native modules or unreviewed major upgrades.
- [ ] Bundle and configure the four provider profiles and minimal extension
  sets.
- [ ] Implement the four explicit provider/tool-family pairings and interop
  tests.
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
- [ ] Run real-provider Claude-like smokes for the reviewer proxy, OpenRouter,
  and Anthropic, plus a Codex-like OpenAI Responses smoke.
- [ ] Pass production-screen simulator acceptance for settings, web fetch,
  file mutation, application actions, persistence, and backgrounding.
- [ ] Update package/mobile/provider documentation, requirement evidence, and
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

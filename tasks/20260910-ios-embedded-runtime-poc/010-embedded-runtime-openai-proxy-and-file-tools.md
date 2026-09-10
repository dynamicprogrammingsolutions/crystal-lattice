# Embed Python Runtime With Ollama Proxy And Workspace File Tools

Deliver a deliberately small but complete proof of concept in which the real
iOS app hosts Python, runs a Crystal Lattice agent through an
API-key-protected OpenAI-compatible Ollama proxy, and completes a multi-round
workspace `Read`/`Write` request.

## Requirements checklist

- [ ] The production iOS application bundle contains an embedded CPython
  runtime and the fixed Python package/plugin closure needed by the proof of
  concept.
- [ ] The app starts and stops the embedded runtime through a native bridge
  without requiring a desktop CLI process or loopback application server.
- [ ] A production `AgentBackend` implementation exposes enough local runtime
  behavior for agent listing, session creation/listing, messages, request
  execution, events, and the relevant application configuration action.
- [ ] One fixed proof-of-concept agent calls an OpenAI-compatible endpoint and
  supports the real Crystal Lattice tool loop.
- [ ] `tools/openai-proxy` can target Ollama, supports streaming and
  non-streaming OpenAI-compatible requests used by the agent, and requires a
  configured incoming API key by the final proof-of-concept stage.
- [ ] The app exposes a basic API-key input for this local runtime and applies
  it through owner-supplied configuration plus complete application reload.
- [ ] The agent exposes simplified Claude-equivalent `Read` and `Write` tools
  rooted in one app-owned workspace; paths outside that workspace are
  rejected.
- [ ] A real small Ollama model completes a deliberately simple request that
  causes multiple provider rounds and visible file-tool calls; exact prose is
  not an acceptance dependency.
- [ ] Session and workspace state survive ordinary navigation and process
  relaunch.
- [ ] The app can place the request in the background, records bounded
  continuation/expiration state, and either completes or recovers without
  silently losing the request.
- [ ] Automated simulator coverage uses production screens/runtime adapters,
  and physical-device evidence records startup plus foreground/background
  behavior.
- [ ] The proof of concept is explicitly limited: production credential
  hardening, polished onboarding, Tavily search, restricted Python execution,
  ChatGPT authorization, and local-model fallback are not required here.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Specification:
mobile/crystal-lattice-control-rn/docs/development/specifications/embedded-python-runtime-poc/index.md

Depends On:
tasks/20260729-staged-application-config-and-full-reload.md

Uses committed bundling work from:
`task/20260908-cli-distribution-test-levels`

## Supporting details

The selected CLI-distribution work provides isolated package staging,
selected-plugin discovery, relocatable-runtime checks, and smoke-test patterns.
The iOS runtime still needs a CPython framework, native embedding, an
iOS-compatible dependency closure, and application-bundle resource staging.

The first model prompt is intentionally simple. A representative acceptance
scenario is:

> Read `input.txt`, write a short transformed version to `output.txt`, read
> `output.txt` back, and tell me what changed.

The proxy or test configuration may add bounded response delay so the request
stays active during a background transition. This is lifecycle test support,
not a deterministic model or replacement provider.

## Execution plan

Status: Approved

Implement one working vertical slice through small executable checkpoints.
Commit each checkpoint that establishes a coherent, passing boundary.

First create the iOS runtime bundle input from the fixed proof-of-concept
configuration. Reuse selected-plugin and immutable-bundle staging concepts
from the bundled-Python CLI distribution, but produce an iOS resource tree
rather than a desktop archive. Add or obtain an iOS-compatible CPython
framework through reproducible build inputs, bundle the standard library and
the minimal pure-Python Crystal Lattice closure, and fail the build when an
unsupported native or subprocess dependency enters the selected closure.

Add a small Swift native runtime host. It initializes Python once per runtime
generation, supplies app-support paths for config, sessions, workspace, and
temporary data, and invokes a focused Python bridge module through serialized
commands/events. It does not start FastAPI or bind a local TCP port. Expose the
host to React Native and adapt it to the existing `AgentBackend` contract with
only the methods required by the production Sessions and Messages flows.

Begin with a foreground, no-authentication, no-tool smoke. The simulator build
must launch the actual app, start Python, create a local session, and return a
minimal response through the production backend adapter. This is the first
successful implementation checkpoint.

Adapt `tools/openai-proxy` into a small development/reviewer model proxy. Keep
its existing transparent forwarding and stream support, add an explicit
Ollama-friendly configuration, add optional bounded response delay for
lifecycle tests, and add incoming bearer-key verification. Temporary
unauthenticated mode may be used only before the API-key checkpoint. Proxy
tests must cover missing, wrong, and correct keys without logging the key.

Configure one bundled proof-of-concept agent through the existing reference
OpenAI-compatible provider. Add a basic local-runtime settings action and UI
field for endpoint/key input. The owner persists the proof-of-concept overlay
in app-owned storage and reconstructs `AgentApplication`; the implementation
does not generalize the desktop environment writer or claim the still-open
production credential-security requirement is complete.

Add focused iOS workspace tools. Use the existing Claude `Read`/`Write` schema
and formatting only where useful, while reducing the implementation to text
files and a single canonical app-owned root. Treat model-provided paths as
workspace-relative, reject absolute paths and escape attempts, and keep auth,
runtime, config, sessions, and bundled source outside the tool root.

Exercise the real tool loop against a small Ollama model. Acceptance asserts
that the session contains the expected tool-call/result structure and that the
workspace output exists and is readable; it does not assert exact wording or
use a deterministic product model.

Add bounded background handling after foreground execution is stable. The
native host records request start/progress/completion, requests permitted iOS
background time, checkpoints durable state before expiration, and exposes an
interrupted/recoverable state when work cannot finish. Add a production-facing
diagnostic/status view or action sufficient to inspect these timestamps.
Detox backgrounds and foregrounds the real app. A physical-device run records
observed behavior without converting one observed duration into a product
guarantee.

Finish by running focused Python, proxy, TypeScript/Jest, iOS build, Detox, and
physical-device verification available in the environment. Update
requirements and task evidence continuously. If a usable physical device or
signing identity is unavailable, leave that requirement incomplete and record
the exact prepared command/checklist rather than substituting simulator
evidence.

### Implementation decisions and open questions

- **Decision — distribution base:** the branch includes the committed
  CLI-distribution work and reuses its staging/build concepts. The desktop
  archive itself is not embedded in iOS.
- **Decision — in-process boundary:** the app uses a native bridge and local
  `AgentBackend`, not a local FastAPI server.
- **Decision — proof-of-concept provider:** one reference
  OpenAI-compatible provider targets an API-key-protected proxy backed by
  Ollama.
- **Decision — no model benchmark:** the real small model only needs to
  complete a deliberately simple multi-round file-tool scenario.
- **Decision — staged authentication:** no-auth proxy access is allowed only
  before the authentication checkpoint; end-state tests require the API key.
- **Decision — workspace scope:** initial tools support text `Read` and
  `Write` under one app-owned workspace. They do not expose app/config/session
  files or arbitrary user-selected roots.
- **Decision — proof-of-concept secrets:** use a small owner-supplied overlay
  and masked input. Do not claim completion of production credential
  provenance/security work.
- **Decision — lifecycle evidence:** simulator tests verify state transitions;
  physical-device evidence measures actual background behavior.
- **Open question — CPython input:** implementation inspection will choose the
  smallest reproducible iOS CPython framework source compatible with the
  current Xcode target. Changing away from CPython or downloading executable
  code at runtime would be material and requires user direction.
- **Open question — physical device:** signing/device availability is an
  environmental verification question, not permission to weaken the
  requirement.

### Documentation

- Target specification:
  `mobile/crystal-lattice-control-rn/docs/development/specifications/embedded-python-runtime-poc/`.
- Add a mobile development implementation page only when the first working
  behavior exists; do not present target behavior as current before then.
- Add concise build/test commands to the mobile development index or README
  with the implementation commit that makes them true.
- Update the specification requirements with concrete code, test, device, and
  delivery evidence.

### Task checklist

- [x] Create and commit task tracking, cross-links, and the approved
  mobile-owned specification.
- [x] Select and reproduce the iOS CPython framework/runtime input.
- [x] Stage `agent_core`, `agent_app`, the initial fixed config/provider, and
  their current pure-Python dependency closure.
- [x] Add the initial Swift runtime host and React Native bridge.
- [x] Pass the foreground embedded-Python no-auth/no-tool smoke.
- [ ] Add the production local `AgentBackend`.
- [ ] Adapt and test the Ollama-targeted OpenAI proxy.
- [ ] Add bounded background diagnostics, continuation, and recovery.
- [ ] Add workspace-restricted `Read` and `Write` tools.
- [ ] Add basic API-key input, proxy enforcement, and application reload.
- [ ] Add the complete real-model multi-round simulator test.
- [ ] Run and record physical-device foreground/background verification.
- [ ] Update requirement evidence, current implementation documentation, and
  completion notes.

### Requirement verification

- Runtime and backend: a release-like iOS simulator build launches the real
  app, starts bundled Python, lists the fixed agent, creates a session, and
  executes requests through the production `AgentBackend`.
- Provider/proxy/authentication: focused proxy tests reject absent/wrong keys,
  accept the configured key, and a real Ollama request succeeds through the
  proxy after the app applies its key and reloads.
- File tools: unit and integration tests reject path escapes and show a real
  agent `Read`/`Write`/`Read` sequence whose file persists under the app
  workspace across runtime reconstruction.
- Lifecycle: Detox verifies real-screen background/foreground transitions and
  completion or recoverable interruption; a physical device records observed
  timestamps and outcome.
- Packaging: archive/resource inspection proves the selected fixed source and
  plugin closure is bundled and no runtime plugin download is needed for the
  acceptance scenario.

### Additional implementation verification

- Run focused Core/application tests for the embedded bridge module and tool
  loop.
- Run `npm --prefix tools/openai-proxy test`.
- Run the relevant mobile Jest tests and `npm run tsc`.
- Build the iOS simulator application with the production Xcode workspace.
- Run the new focused Detox scenario rather than the entire mobile E2E suite
  initially.
- Run existing local mobile/runtime regressions affected by shared interfaces.
- Inspect logs and committed files for credentials before every commit.

## Implementation Notes

- 2026-09-10: Created the approved task set and mobile-owned specification in
  commit `124be8b7`. The implementation branch includes the completed
  CLI-distribution work through merge commit `0d2e2f83`.
- 2026-09-10: Selected Python Apple Support `3.12-b10`, containing CPython
  3.12.14 device and simulator slices. Added a checksum-pinned preparation
  script that keeps the generated 132 MB XCFramework and standard library out
  of Git.
- 2026-09-10: Added a local CocoaPod, mixed Swift/Objective-C native host,
  React Native promise bridge, production diagnostics screen, and focused
  Detox launch path. The stdlib is stored as an uncompressed importable zip so
  startup codecs do not depend on an extension module before initialization.
- 2026-09-10: The release simulator build passed with the Python framework and
  resource bundle embedded. `npm run tsc` passed. The focused Detox test passed
  on an iPhone 17 Pro simulator in 31.5 seconds and confirmed CPython 3.12
  executed the smoke program with result `42`.
- 2026-09-10: Added the real Core/application source archive and a fixed-source
  `AgentApplication` construction path. Refactored default plugin sources and
  SQLite loading to stay lazy when an embedded owner supplies only dotted
  sources and in-memory notifications; focused Core tests passed.
- 2026-09-10: Added the Python support package's official post-processing build
  phase. It installs the stdlib in the app, converts extension modules to
  signed frameworks, and creates `.fwork` markers. The focused Detox test then
  imported `agent_core`/`agent_app`, constructed `AgentApplication`, created a
  `local` session, persisted one user message, and loaded it back successfully.
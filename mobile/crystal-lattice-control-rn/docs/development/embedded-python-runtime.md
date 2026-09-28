# Embedded Python runtime

The iOS app runs a fixed Crystal Lattice `AgentApplication` in process. It
bundles CPython, `agent_core`, `agent_app`, four provider packages, separate
Claude-like and Codex-like tool packages, and selected session-management
application plugins. React Native uses the ordinary `RestAgentBackend` over an
`inProcess` transport; the app does not start FastAPI, bind a loopback server,
or launch a desktop Python process.

The runtime exposes these fixed profile/agent pairings when their profile is
enabled and has a key, URL, and model:

| Agent | Provider | Tool family |
| --- | --- | --- |
| `reviewer-claude` | generic OpenAI-compatible reviewer endpoint | Claude-like |
| `openai-codex` | OpenAI Responses | Codex-like |
| `openrouter-claude` | OpenRouter | Claude-like |
| `anthropic-claude` | official Anthropic Messages API | Claude-like |

If no profile is complete, the local connection still opens with the
credential-free smoke agent so existing session summaries and runtime
diagnostics remain accessible.

The `local` agent remains registered after real profiles are enabled so
sessions created before configuration remain loadable. A successfully tested
real profile becomes the default for subsequent sessions.

Provider URLs, models, enabled flags, and the default agent are stored in a
versioned iOS preference document. Each provider API key is stored as a
separate iOS Keychain generic-password item. JavaScript receives only
`hasApiKey`; keys are not written to connection records or AsyncStorage. The
old single reviewer key is migrated from `UserDefaults` to Keychain.

## Runtime layout

The build uses the checksum-pinned Python Apple Support `3.12-b10` archive.
Generated framework and resource trees stay ignored by Git. The preparation
script builds an importable application archive containing the fixed Python
source and pure-Python dependency closure.

OpenAI Responses and Anthropic use their package-owned
`provider_transport: "requests"` path in the embedded runtime. Their vendor
SDKs and native dependencies such as `jiter` and `pydantic-core` are not
bundled. The embedded dependency list pins the requests/certificate closure,
and the Release simulator smoke constructs both provider clients.

OpenRouter and the reviewer provider use their existing `requests`
implementations. Provider API requests send user messages, provider history,
and relevant tool inputs/results to the selected external service.

OpenAI Responses supports `api`, `auto`, and `chatgpt` authentication modes.
The bundle includes `chatgpt-auth-app` and the Responses ChatGPT auth feature.
Login uses ordinary application/session actions and the generic action UI.

The reviewer profile accepts a custom CA bundle. The App Review build includes
the public Ireland reviewer certificate and retains TLS verification; private
certificate keys and API credentials are not bundled.

At runtime, mutable data lives under:

```text
Application Support/CrystalLatticeEmbeddedRuntime/
├── config/
├── sessions/
├── session_assets/
├── runtime/
└── workspace/
```

Only `workspace/` is visible to model file tools. The tools reject absolute
paths, traversal outside the canonical root, and symlink escapes. Reads,
writes, search, enumeration, and patches are bounded UTF-8 text operations.
Session snapshots, selected-snapshot state, application settings, and
session-owned attachments stay under the app-support root.

Prepare the runtime and CocoaPods dependencies from the mobile package:

```bash
npm run pod-install
```

To refresh only the generated Python input:

```bash
npm run ios:prepare-python
```

## Authenticated Ollama proxy

From the repository root, start the development/reviewer proxy:

```bash
export CRYSTAL_PROXY_API_KEY="replace-with-a-random-key"
node tools/openai-proxy/proxy.js \
  http://127.0.0.1:11434/v1 \
  3000 \
  /v1 \
  --hide-headers \
  --require-api-key-env CRYSTAL_PROXY_API_KEY
```

For simulator testing, enter `http://127.0.0.1:3000/v1` in the app. A physical
device must use the Mac's reachable LAN address, for example
`http://192.168.1.20:3000/v1`.

The proxy rejects missing or incorrect bearer keys, redacts credentials from
logs, and strips the client authorization header before forwarding to Ollama.
Add `--delay-ms 2000` when exercising background continuation.

## Using the app

On iOS:

1. The **On-device Python agents** connection is already present under
   **Connections**.
2. From Home, open **On-device providers** in the Home actions bar or
   **On-device Provider Settings** in the Home menu.
3. Enable a profile and set its URL, model, and API key. Choose the default
   agent used when callers do not specify one.
4. **Test** validates a candidate without replacing saved settings. **Save
   Settings** writes non-secrets to preferences and keys to Keychain.
5. Open the built-in connection, create a session with an available agent, and
   use the ordinary Sessions and Messages screens.

The legacy new-connection reviewer setup remains compatible. A failed
candidate test leaves the saved configuration untouched. The next in-process
request reconstructs `AgentApplication` when settings change while preserving
sessions and workspace files.

The Claude-like plugin package contains:

- `Read`: read a workspace-relative UTF-8 text file with optional line offset
  and limit.
- `Write`: create or replace a workspace-relative UTF-8 text file.
- `Edit`: perform an exact replacement after the file has been read.
- `Glob`: list files matching a workspace-relative pattern.
- `Grep`: search workspace text with bounded regular expressions and result
  modes.
- `WebFetch`: retrieve bounded text from public HTTP(S) pages.

`WebFetch` is a page fetch/extraction tool, not Tavily search. It rejects
private/local/reserved destinations and revalidates redirects.

The Codex-like plugin package contains:

- `sed`: bounded line-range reads.
- `rg`: bounded recursive workspace text search.
- `find`: bounded workspace path enumeration.
- `curl`: bounded public HTTP(S) GET requests.
- `apply_patch`: safe Add/Update/Move/Delete workspace patches.

The Codex-like commands return Bash-shaped command, exit-code, wall-time, and
bounded-output envelopes, but `curl` and the other tools do not execute a
shell.

The model-visible schemas and result presentation belong to
`embedded-claude-tools`. Canonical workspace path authorization and UTF-8 text
operations, enumeration, search, patching, and public URL validation belong to
`embedded-tools-shared`; the mobile bridge does not define tool classes.

Tavily web search and Python execution are intentionally not part of this
runtime configuration yet.

## Application plugins and route parity

The embedded runtime loads the iOS-safe default session plugins for:

- copy/fork/delete actions;
- title/subtitle editing and provider-backed title generation;
- search and ordering descriptors;
- message-count and timestamp metadata;
- pin, archive, and status metadata;
- generic session-asset download.

The in-process router delegates application actions and UI schema, session
plugin overrides, snapshots, readonly snapshot selection, restore/delete,
fork, message deletion, and server settings to `AgentApplication`. Message
deletion creates an automatic pre-delete snapshot. The dotenv-writing
`application-config-app`, MCP, cloud, rebuild, subprocess export, and
provider-native attachment extensions are not included.

## Persistence and background behavior

Sessions and workspace files use app-support storage and survive runtime
reconstruction and process relaunch. An inspection launch can load the prior
session and workspace without replaying a provider request.

For each embedded request, the native host starts a bounded iOS background
task and persists request/session identity plus lifecycle timestamps. Visible
states are:

- `running`
- `background`
- `completed`
- `failed`
- `cancelled`
- `expired`
- `interrupted`

If a process ends while a request is active, the next process records a
recoverable `interrupted` state. It does not automatically repeat the provider
request. Actual background duration remains controlled by iOS and is not a
product guarantee.

## Focused verification

Run source-level checks:

```bash
npm run tsc
pytest python_tests/test_crystal_lattice_mobile_runtime.py -q
npm --prefix ../../tools/openai-proxy test
```

Build the release simulator app:

```bash
npm run detox:build:ios
```

Run credential-free runtime smoke:

```bash
npm run detox:test:embedded-python-runtime:ios
```

With the authenticated proxy running, export owner inputs and run the real
provider tests:

```bash
export CRYSTAL_EMBEDDED_PROXY_URL="http://127.0.0.1:3000/v1"
export CRYSTAL_EMBEDDED_PROXY_API_KEY="$CRYSTAL_PROXY_API_KEY"
export CRYSTAL_EMBEDDED_MODEL="qwen3.5:0.8b"

npm run detox:test:embedded-python-setup:ios
npm run detox:test:embedded-python-web-fetch:ios
npm run detox:test:embedded-python-ollama:ios
npm run detox:test:embedded-python-background:ios
```

The real-model tests assert tool/message structure, persisted file content,
process-relaunch state, and lifecycle timestamps. They do not assert exact
assistant prose.

Run the hosted tool-family matrix from the repository root:

```bash
pytest plugins/embedded-claude-tools/tests/test_provider_real_api.py \
  -m 'integration and api and openrouter' -q
pytest plugins/embedded-claude-tools/tests/test_provider_real_api.py \
  -m 'integration and api and anthropic' -q
pytest plugins/embedded-codex-tools/tests/test_luna_real_api.py \
  -m 'integration and api and openai' -q
```

After building the iOS ZIP, run the selected direct provider integrations from
that immutable artifact:

```bash
npm run build:ios:embedded-providers:bundle
npm run test:ios:embedded-providers:bundle
npm run test:ios:embedded-providers:bundle:api
```

The build entry delegates to the mobile package's `ios:prepare-python`
command. The test entries select positively marked OpenAI Responses and
OpenRouter provider tests only and never rebuild the artifact. They exclude
unit, `AgentApplication`, plugin-install, and non-embedded-extension tests.
Each provider gets a disposable dev-only dependency overlay; provider,
`agent_core`, and `requests` imports must remain inside the prebuilt ZIP, and
the archive hash must not change.

Run the Release simulator API matrix separately:

```bash
npm run test:ios:embedded-providers:detox:api
```

The ChatGPT action flow is collected but manually gated:

```bash
CRYSTAL_RUN_CHATGPT_LOGIN_E2E=1 \
  npm run test:ios:embedded-providers:detox:chatgpt
```

## Current limits

- iOS only.
- Fixed provider and tool-family profiles rather than arbitrary plugin
  installation or runtime-defined agents.
- Profiles without complete enabled settings are omitted from the live agent
  list; `auto`/`chatgpt` OpenAI profiles may use saved ChatGPT credentials.
- Ollama runs behind an external proxy; no model runs inside the app.
- No Tavily search, restricted Python executor, email integration, dynamic
  plugin installation, or arbitrary user-selected workspace.
- The reviewer proxy still requires deployed monitoring and credential/
  certificate rotation procedures.
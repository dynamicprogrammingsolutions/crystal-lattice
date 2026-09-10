# Embedded Python runtime

The iOS app can run one fixed Crystal Lattice agent in process. The app bundles
CPython, `agent_core`, `agent_app`, the reference OpenAI-compatible provider,
the model-invisible `embedded-tools-shared` workspace engine, and the
`embedded-claude-tools` plugin package. The fixed archive also contains the
separate `embedded-codex-tools` package plus the OpenAI Responses and Anthropic
provider packages. The current single agent does not enable those providers
yet. React Native talks to the runtime through an `inProcess` `AgentBackend`;
the app does not start FastAPI, bind a loopback server, or launch a desktop
Python process.

This is a proof of concept. The endpoint and model are saved with the embedded
connection record. The masked proxy API key is kept in iOS app-owned
`UserDefaults`, outside the connection record and Python config committed to
the repository. This storage is not the final credential-security design.

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

At runtime, mutable data lives under:

```text
Application Support/CrystalLatticeEmbeddedRuntime/
├── config/
├── sessions/
└── workspace/
```

Only `workspace/` is visible to model file tools. The tools reject absolute
paths, traversal outside the canonical root, and symlink escapes. Reads are
UTF-8 text-only and bounded to 256 KB; writes create or replace UTF-8 files
under the workspace.

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

1. Open **Connections** and choose **New connection**.
2. Select **On-device Python Agent**.
3. Enter the OpenAI-compatible proxy URL, Ollama model name, and proxy API key.
4. Select **Start On-device Agent**.
5. Create a session and use the normal Messages screen.

The setup validates that the key can list the configured model before opening
the connection. The saved connection omits the key. Reopening the saved
connection uses the native owner configuration and reconstructs the complete
`AgentApplication` when endpoint, model, or key changes.

The fixed Claude-like tool set currently contains:

- `Read`: read a workspace-relative UTF-8 text file with optional line offset
  and limit.
- `Write`: create or replace a workspace-relative UTF-8 text file.
- `Edit`: perform an exact replacement after the file has been read.
- `Glob`: list files matching a workspace-relative pattern.
- `Grep`: search workspace text with bounded regular expressions and result
  modes.
- `WebFetch`: retrieve bounded text from public HTTP(S) pages.

The model-visible schemas and result presentation belong to
`embedded-claude-tools`. Canonical workspace path authorization and UTF-8 text
operations, enumeration, search, patching, and public URL validation belong to
`embedded-tools-shared`; the mobile bridge does not define tool classes.

Tavily web search and Python execution are intentionally not part of this
runtime configuration yet.

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
npm run detox:test:embedded-python-ollama:ios
npm run detox:test:embedded-python-background:ios
```

The real-model tests assert tool/message structure, persisted file content,
process-relaunch state, and lifecycle timestamps. They do not assert exact
assistant prose.

## Current limits

- iOS only.
- One fixed OpenAI-compatible agent and provider profile.
- One active Claude-like text/workspace/public-fetch tool set. The separate
  Codex-like package is bundled but not yet assigned to an agent.
- API-key authentication only; ChatGPT authorization is not included.
- Ollama runs behind an external proxy; no model runs inside the app.
- No Tavily search, restricted Python executor, email integration, dynamic
  plugin installation, or arbitrary user-selected workspace.
- The proxy still needs deployment-level TLS, rate limiting, monitoring, and
  credential rotation before use as a public reviewer service.
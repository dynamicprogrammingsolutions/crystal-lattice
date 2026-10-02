# Embedded Python runtime

The iOS app runs a fixed Crystal Lattice `AgentApplication` in process. It
bundles CPython, `agent_core`, `agent_app`, five provider profiles, separate
Claude-like and Codex-like tool packages, and selected session-management
application plugins. React Native uses the ordinary `RestAgentBackend` over an
`inProcess` transport; the app does not start FastAPI, bind a loopback server,
or launch a desktop Python process.

The runtime exposes these fixed profile/agent pairings when their profile is
enabled and has a key, URL, and model:

| Agent | Provider | Tool family |
| --- | --- | --- |
| `compatible-claude` | generic OpenAI-compatible endpoint, including Ollama | Claude-like |
| `reviewer-codex` | preconfigured Ireland OpenAI Responses reviewer | Codex-like |
| `openai-codex` | OpenAI Responses | Codex-like |
| `openrouter-claude` | OpenRouter | Claude-like |
| `anthropic-claude` | official Anthropic Messages API | Claude-like |

If no profile is complete, the local connection still opens with the
credential-free smoke agent so existing session summaries and runtime
diagnostics remain accessible.

The `local` agent remains registered after real profiles are enabled so
sessions created before configuration remain loadable. A successfully tested
real profile becomes the default for subsequent sessions.

Editable provider URLs, models, enabled flags, and the default agent are stored in a
versioned iOS preference document. Version 3 splits the old overloaded
reviewer profile into generic-compatible and dedicated Responses reviewer
profiles. Each provider API key is stored as a
separate iOS Keychain generic-password item. JavaScript receives only
`hasApiKey`; keys are not written to connection records or AsyncStorage. The
old single reviewer key is migrated from `UserDefaults` to Keychain.

The provider/agent/plugin graph is maintained by the Python application in
`agent_terminal_app/default_config/embedded-ios/config.json`. Runtime
preparation copies that JSON into the immutable Python archive. Native
settings provide config-only `${env:...}` placeholder values for mutable
settings, paths, readiness, and Keychain-backed credentials; Swift and
TypeScript do not maintain a second agent graph.

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

The OpenAI Responses profile registers native web search, inline-image
attachments, Flex, Fast mode, prompt caching, and verbosity. OpenRouter
registers its native web search, image attachments, Claude caching, and
verbosity extensions. Flex and Fast settings are available for direct OpenAI
API authentication but hidden for ChatGPT and Reviewer. Reviewer still
receives native Responses web search, while its service tier remains fixed.

The requests transport sends OpenAI images inline. It does not implement the
OpenAI Files API, so the embedded UI does not advertise PDF or upload-backed
image modes. OpenAI native compaction is also omitted because that extension
imports the OpenAI SDK, which is deliberately outside the lightweight
requests-only iOS dependency set.

Embedded `/send` and `/send_message` start streamed requests when the
effective OpenAI Responses authentication mode is ChatGPT (including a
session or request override). The other embedded profiles retain their
existing request mode. ChatGPT's Responses endpoint requires streaming.

OpenRouter and the generic compatible provider use their existing `requests`
implementations. The dedicated reviewer uses OpenAI Responses through the
package-owned requests transport and sends `/responses`, not
`/chat/completions`. Provider API requests send user messages, provider
history, and relevant tool inputs/results to the selected external service.

The reusable OpenAI Responses provider supports `api`, `auto`, and `chatgpt`
authentication modes. The embedded mobile profile deliberately exposes only
**API key** and **ChatGPT** in On-device Provider Settings. Existing mobile
`auto` values migrate to `api`. The ordinary session/plugin auth selector is
suppressed for embedded agents so one session cannot accidentally switch away
from the saved on-device choice.

The bundle includes `chatgpt-auth-app` and the Responses ChatGPT auth feature.
The OpenAI authentication card in On-device Provider Settings invokes the
plugin's ordinary **Sign in**, **Check status**, **Cancel**, and **Log out**
actions. The generic action display renders the returned login URL, user code,
Open-link, Copy-code, and follow-up status action. React Native does not
implement the authorization protocol itself.

ChatGPT HTTPS calls use the bundled Certifi roots with verification enabled.
OpenAI's device-auth endpoint can return a Cloudflare route error to
`urllib`; the plugin retries that response with the bundled in-process
`requests` client. It does not depend on `curl` or any other subprocess on
iOS. The same verified CA setup covers login polling, token exchange,
credential refresh, and ChatGPT/Codex discovery requests.

The Reviewer profile is globally hidden by default. Enabling **Reviewer
access** adds it at the bottom of the provider list and makes it available to
the runtime once its caller key is present. Its Ireland HTTPS URL,
`gpt-5.6-luna` model, provider protocol, tool family, and CA path are fixed by
the maintained Python configuration and are not editable in the app. The App
Review build includes the
public Ireland reviewer certificate and retains TLS verification; private
certificate keys and API credentials are not bundled. Runtime preparation
preserves the tracked public certificate when regenerating resources.

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

The app-owned workspace remains available, but **Session settings → Working
directory** now presents opaque workspace choices:

- **Private** workspaces created for and listed only to the current session;
- **Shared** app workspaces, including the existing workspace root and named
  directories reusable by other sessions; and
- **Files** folders selected directly from iOS Files or another available file
  provider.

The workspace plugin places **Use a new private workspace**, **New shared
workspace…**, and **Choose folder from Files…** action buttons directly under
the setting. Known choices save immediately. Creation and Files authorization
run through normal plugin actions and refresh the setting after success.

The Files picker requests persistent read/write access. Native code retains
the security-scoped bookmark and supplies the embedded runtime only an opaque
grant ID and active resolved root. The selected folder is used in place; its
contents are not copied into the app sandbox.

The in-process override adapter delegates to `AgentApplication`, which rejects
unknown workspace IDs, another session's private workspace, traversal,
unregistered external paths, and attempts to override fixed authorization
fields. The shared Claude-like and Codex-like tool engine repeats the
effective-root boundary check before tool execution.

### Manual Files-folder verification in the simulator

After building and installing the Release app:

1. Open the on-device connection and create a session using a configured
   provider.
2. Open **Session settings → Working directory**.
3. Confirm **Workspace root** remains available.
4. Run **Use a new private workspace** and confirm the value changes to
   **Private**.
5. Run **New shared workspace…**, enter a name, and confirm another session can
   select it under **Shared**.
6. Run **Choose folder from Files…**. In the native picker, create or select a
   simulator folder and approve it.
7. Ask the agent to write and read a marker file. Inspect the selected Files
   folder to confirm the marker is there and was not copied into the app-owned
   workspace.
8. Terminate and relaunch the app, reopen the same session, and confirm the
   **Files** workspace remains selected and the marker can still be read.
9. Move or remove the folder, relaunch, and confirm the setting reports
   **Unavailable** and offers **Restore access…** rather than silently
   switching workspaces.

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
3. For ordinary OpenAI Responses, choose **API key** or **ChatGPT** in the
   OpenAI authentication card. API-key mode uses the profile's key field.
   ChatGPT mode enables the plugin-driven login/status controls in the same
   settings window.
4. Enable a profile and set its URL, model, and credentials when required.
   Choose the default agent used when callers do not specify one. To use the
   Reviewer, enable **Reviewer access** and enter only its private caller key.
5. Every edit saves automatically after a short debounce. The status line
   reports saving, success, or failure. **Test** validates the current
   candidate without changing settings by itself.
6. Open the built-in connection, create a session with an available agent, and
   use the ordinary Sessions and Messages screens.
7. To scope relative file operations for one session, open its **Session
   settings**, choose **Working directory**, and select the workspace root or
   an existing descendant.

The built-in on-device connection is created automatically. The old
new-connection form is no longer offered because it wrote the legacy
compatible-provider aliases and could silently select Qwen. A failed candidate
test leaves the autosaved configuration untouched. The next in-process request
reconstructs `AgentApplication` when settings change while preserving sessions
and workspace files.

The maintained config also includes the default system-message,
request-options, timestamp/duration, summarize-range, rebuild-native-history,
cost-tracking, and workspace-settings plugins. Provider-native OpenAI
Responses and OpenRouter web search and image attachments are included.
Provider-neutral Tavily search, file context, web context, MCP, cloud-agent,
and dotenv-editing plugins remain excluded or deferred for explicit iOS
compatibility and product review.

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

Tavily provider-neutral web search and Python execution are intentionally not
part of this runtime configuration yet. OpenAI Responses and OpenRouter native
web search are already available through their provider extensions.

## Application plugins and route parity

The embedded runtime loads the iOS-safe default session plugins for:

- copy/fork/delete actions;
- title/subtitle editing and provider-backed title generation;
- search and ordering descriptors;
- message-count and timestamp metadata;
- pin, archive, and status metadata;
- generic session-asset download.

The in-process router delegates application actions and UI schema, validated
session overrides, snapshots, readonly snapshot selection, restore/delete,
fork, message deletion, and server settings to `AgentApplication`. Message
deletion creates an automatic pre-delete snapshot. The dotenv-writing
`application-config-app`, MCP, cloud, and subprocess export plugins are not
included.

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

The hosted provider matrix also reports provider-native search/attachment
availability and verifies that a model-created descendant can be selected as
one session's working directory without changing another session. It rejects
an outside override through the production in-process transport and confirms
the selection after relaunch.

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

The production Reviewer row always uses the maintained Ireland URL, model,
and bundled public CA. Local proxy development should use the generic
OpenAI-compatible profile; the production Reviewer settings UI intentionally
has no URL, model, or CA override.

The default ChatGPT simulator command starts a real device-code login, proves
that the plugin-driven URL/code actions are displayed, and cancels the
attempt. It does not require a human account:

```bash
npm run test:ios:embedded-providers:detox:chatgpt
```

The human authorization, real Responses tool request, and relaunch portion is
separately gated. This run opens a fresh login attempt and waits up to 15
minutes for a person to approve its code. The gated test prints
`ChatGPT login URL` and `ChatGPT login code` to its console as soon as the
plugin returns them. Open that URL on your computer, enter the code printed
for this run, approve authorization in the browser, and return to the app.
The same details remain visible in the simulator's **ChatGPT Login** card. The
**ChatGPT status** line updates from `pending` to `authenticated` when the
plugin completes login; the test then sends a real tool request and checks
relaunch persistence. If no one completes the browser step, the test fails
with the last observed status; that is not evidence of a completed login.
The ungated start/cancel test checks the values without printing its
short-lived code.

```bash
CRYSTAL_RUN_CHATGPT_LOGIN_E2E=1 \
  npm run test:ios:embedded-providers:detox:chatgpt
```

Each gated run starts a fresh login. After autosave succeeds, it closes the
settings modal before relaunching the app. Detox cleanup removes the installed
simulator app and its saved credentials between runs.

For the focused physical-device check, open On-device Provider Settings,
select **ChatGPT**, and press **Sign in with ChatGPT**. Acceptance for that
check is the **ChatGPT Login** display with an Open-link and Copy-code action;
`CERTIFICATE_VERIFY_FAILED` must not appear. The broader capability acceptance
remains the Release simulator flow.

## Current limits

- iOS only.
- Fixed provider and tool-family profiles rather than arbitrary plugin
  installation or runtime-defined agents.
- Profiles without complete enabled settings are omitted from the live agent
  list; ChatGPT OpenAI profiles may use saved ChatGPT credentials.
- Ollama runs behind an external proxy; no model runs inside the app.
- No Tavily search, restricted Python executor, email integration, dynamic
  plugin installation, or arbitrary user-selected workspace.
- The reviewer proxy still requires deployed monitoring and credential/
  certificate rotation procedures.
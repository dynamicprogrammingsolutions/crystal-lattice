# Embedded Python runtime proof-of-concept technical specification

## Architecture

```text
React Native Sessions / Messages / Settings
                    |
                    v
          local AgentBackend adapter
                    |
                    v
          Swift embedded-runtime host
                    |
                    v
         bundled CPython bridge module
                    |
                    v
        AgentApplication + fixed config
          |                       |
          v                       v
OpenAI-compatible provider   workspace Read/Write
          |
          v
API-key proxy -> Ollama
```

The mobile screens consume the existing `AgentBackend` contract. The adapter
serializes commands to the native host and receives normalized application
events. The host invokes Python in process; it does not run FastAPI, bind a
loopback application port, or launch a child process.

## Runtime distribution

The iOS target bundles:

- an iOS-compatible CPython framework/runtime;
- the Python standard-library subset required by the selected runtime;
- `agent_core` and `agent_app`;
- a focused embedded bridge module;
- the reference OpenAI-compatible provider;
- the initial workspace tool package;
- one fixed proof-of-concept configuration and system message.

The committed bundled-Python CLI distribution provides reusable build
concepts:

- select packages/plugins from the effective configuration;
- stage immutable runtime source separately from mutable user state;
- build in an isolated environment;
- inspect the staged closure before acceptance;
- boot the staged runtime through a focused smoke.

The desktop archive launcher and desktop Python executable are not iOS bundle
inputs. The iOS build owns framework linking, standard-library resource
placement, dependency compatibility, and native startup.

The selected closure must not require subprocess, Node, Bash, dynamic plugin
installation, Git, a package manager, or a runtime download. A build-time
closure check fails when an unsupported selected dependency is detected.

## Native host

One Swift host instance owns one active interpreter and application
generation. Its public operations are intentionally small:

- `start()`;
- `execute(command:)`;
- `configure(configuration:)`;
- `getConfiguration()`;
- `noteAppState(state:)`;
- `getLifecycleStatus()`.

Commands and events use serialized dictionaries/JSON rather than exposing
Python objects to React Native. The host supplies canonical application-support
paths:

```text
Application Support/CrystalLatticeEmbeddedRuntime/
├── config/
├── sessions/
└── workspace/
```

Temporary files use the application cache/temp directories. Bundled source,
credentials, runtime state, and session persistence are not descendants of the
model-visible workspace root.

Python initialization and commands are serialized at the native bridge.
Changing owner configuration causes the Python bridge to close and reconstruct
the complete `AgentApplication` before handling the next command.

## Python bridge

The bridge creates the fixed `AgentApplication` and adapts local operations to
plain request/response/event payloads. It implements only the backend behavior
needed for the proof of concept:

- list the fixed agent;
- create, list, load, and delete proof-of-concept sessions where required by
  production screens;
- append/list messages;
- start/cancel a request;
- poll or subscribe to request/application events;
- accept app-owned runtime configuration;
- reconstruct the application from the current owner overlay.

Session persistence uses the app-sandboxed filesystem store. The bridge does
not expose Python evaluation, plugin installation, arbitrary imports, or
filesystem paths to JavaScript.

## Local backend adapter

The TypeScript adapter identifies itself as `inProcess` and implements the
existing `AgentBackend` surface used by production controllers. Unsupported
optional operations return explicit capability errors rather than silently
pretending success.

The initial connection appears as a built-in local runtime record. Existing
manual, bridge, and cloud records remain compatible. Backgrounding the app
does not run ordinary network-disconnect behavior against this runtime;
instead, the host receives lifecycle preparation.

## Configuration and credentials

The fixed configuration has one agent and one provider profile. The provider
uses the reference OpenAI-compatible implementation with:

- one configured proxy base URL;
- one selected small Ollama model;
- one owner-injected API key;
- the two workspace tools.

The proof-of-concept UI may use a simple masked field and app-owned persisted
overlay. It must not put the key in prompts, events, tool results, logs, or
committed configuration. Saving or deleting the value reconstructs
`AgentApplication` through the existing owner reload contract.

This is not the final credential-provenance/security contract. Current UI and
implementation documentation must label the feature appropriately until the
broader credential hardening requirement is complete.

## Ollama proxy

`tools/openai-proxy` is extended rather than duplicated. End-state startup
requires:

- target endpoint;
- listen port and base path;
- expected incoming API key;
- optional hidden-header logging;
- optional bounded response delay for lifecycle tests.

The proxy accepts `Authorization: Bearer <key>`, compares it without logging
the credential, and returns `401` for missing or incorrect credentials.
Development-only unauthenticated mode is explicit and cannot be the default
used by final acceptance.

After validation, the proxy strips or replaces the incoming authorization
header before forwarding to Ollama. It preserves request bodies, tool
definitions, status codes, JSON responses, and streaming chunks required by
the selected provider.

The proxy remains a development/reviewer component. The iOS app does not
bundle or launch Node.

## Workspace tools

The initial tools are text-only `Read` and `Write` operations. Their schemas
may use Claude-compatible names and result shapes, but paths are interpreted
relative to the one configured workspace.

`Read` accepts:

- relative file path;
- optional bounded text offset/limit when retained by the simplified schema.

`Write` accepts:

- relative file path;
- complete text content.

Both tools:

- reject absolute paths;
- resolve `.` and `..` before authorization;
- reject a resolved path outside the canonical workspace;
- reject symlink traversal outside the workspace;
- bound read/result size;
- create parent directories only inside the workspace when explicitly allowed;
- return model-visible logical paths instead of app-container absolute paths.

The initial implementation does not read media, PDFs, credentials, config,
sessions, bundled source, or arbitrary document-provider locations.

## Foreground and background lifecycle

The first smoke runs entirely in the foreground. Once that passes, the host
adds bounded lifecycle handling.

For an active request, the native host records:

- request identifier;
- start time;
- latest progress time;
- background transition time;
- background-task expiration when observed;
- completion, interruption, or cancellation;
- foreground recovery time.

On background:

1. Record the app-state transition and current request identity.
2. Continue under the bounded background task already acquired for the active
   request.
3. Persist `expired` if the operating system invokes the expiration handler.

On foreground:

1. Reconcile the persisted native request record and Python session state.
2. Surface completed output or an explicit interrupted/retryable state.
3. Do not duplicate a provider request automatically.

The simulator verifies transitions and persistence and is sufficient
acceptance evidence for this proof of concept. Actual background duration
remains controlled by iOS and is not a guaranteed number of minutes.

## Staged acceptance

The implementation proceeds through executable checkpoints:

1. Bundled Python starts in the foreground with no provider or tools.
2. One unauthenticated development-proxy model request succeeds.
3. Background transition diagnostics and recovery work.
4. Workspace `Read` and `Write` work in a real multi-round tool loop.
5. Proxy API-key enforcement and app key input/reload work.
6. Simulator and physical-device acceptance exercise the combined path.

Intermediate unauthenticated behavior is development-only. Requirement state
is complete only for the final authenticated combined path.

## Verification boundaries

- Swift/native tests own host initialization, lifecycle mapping, and path
  provisioning.
- Python tests own bridge commands, fixed configuration, workspace
  authorization, sessions, and tool behavior.
- Proxy tests own authentication, forwarding, streaming, delay, and redacted
  diagnostics.
- Mobile Jest tests own adapter and settings state.
- Detox owns the real production-screen simulator flow.
- A real Ollama model owns final provider/tool-loop evidence. Deterministic
  test providers may support lower-level tests but are not acceptance evidence
  for the product path.

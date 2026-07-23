# Support Plugin-Driven Application Configuration Reload

Allow trusted application plugins to expose application-wide actions that update supported application configuration, including provider API keys, and atomically activate the updated configuration without restarting the CLI process.

Each request's expanded `ToolLoopRunner` retains the configuration generation, plugins, lifecycle handlers, and runtime dependencies with which it started. Existing requests finish on their original generation while subsequent requests use the newly activated generation.

Configuration changes remain plugin-driven. The platform adds only the runtime, action, secret-handling, and UI capabilities that plugins cannot safely implement themselves.

## Requirements checklist

- [ ] A configured application plugin can update configuration that it explicitly supports and activate the resulting configuration without requiring a CLI process restart.
- [ ] Configuration activation is atomic from the runtime's perspective: subsequent requests use the successfully activated generation, requests already in progress continue with their original generation, and a failed activation leaves the previous generation active and usable.
- [ ] Each request's `ToolLoopRunner` retains all configuration-sensitive runtime dependencies needed to complete the request, including its `AgentCore`, effective configuration, plugin and lifecycle generation, application context, cancellation controller, and checkpoint coordination.
- [ ] Supported plugin catalog changes are activated through a new runtime generation without interrupting requests using the previous generation, subject to documented constraints for process-global environment, imports, native libraries, singleton resources, and background services.
- [ ] A supporting application plugin can securely set or replace a provider API key, and provider operations started after successful activation use the changed key without exposing the key as a readable configuration value.
- [ ] Application-wide plugin actions can be contributed to and executed from the Sessions screen without requiring a session context. They use the existing application-action HTTP path and production frontend backend adapter.
- [ ] User-visible configuration mutation and reload operations remain application-plugin capabilities. No generic public configuration CRUD or reload endpoint is added unless implementation proves that the plugin action path cannot safely provide a required operation.

## Supporting details and ground truths

### Current configuration and runtime ownership

`AgentApplication` currently resolves configuration during construction and stores configuration-dependent state directly on the application object. This includes plugin classes and catalogs, application-plugin instances, per-agent plugin runtimes, agent base-configuration caches, the model-discovery cache, runtime store, async runtime host, and application context.

Relevant code:

- `core/python/agent_app/application_future.py:328-686`
- `core/python/agent_app/config.py:30-116`
- `core/python/agent_app/runtime_env.py:10-130`

There is no current operation that reloads this state after construction.

### Current request and tool-loop ownership

A fresh `AgentCore` is constructed when resolving a request runtime, and `ToolLoopRunner` is instantiated per request. Provider, feature, extension, and tool wrappers therefore already have substantial request-local ownership.

However, `AgentApplication.send_request` still owns the request lifecycle around `ToolLoopRunner`. It passes callbacks and `ApplicationContext` objects that reach back into the live application for:

- lifecycle action discovery and execution;
- effective configuration refresh between phases;
- session reconciliation and checkpoints;
- generation-sensitive runtime context;
- cancellation registration;
- model and plugin state.

Changing application fields in place while a request is active could therefore produce a hybrid request, such as an old provider/tool core completing with new application lifecycle plugins.

Relevant code:

- `core/python/agent_app/application_future.py:976-1034`
- `core/python/agent_app/application_future.py:1480-1557`
- `core/python/agent_app/application_future.py:3602-3945`
- `core/python/agent_app/tool_loop.py:64-666`
- `core/python/agent_app/app_context.py:8-160`

### Current server request lifetime

The HTTP server starts sends in background threads. A background worker captures the `AgentApplication` instance supplied when the request starts, which is favorable for generation draining, but generation selection is not currently reserved before the background handoff.

Request cancellation is stored on one `AgentApplication`. After a generation switch, cancellation must still reach requests owned by a retired generation.

Relevant code:

- `application/python/agent_terminal_app/server.py:989-1063`
- `application/python/agent_terminal_app/server.py:1760-1930`
- `core/python/agent_app/application_future.py:2225-2239`

### Shared persistence

Sessions, events, snapshots, locks, and assets should remain stable across configuration generations. `FilesystemSessionStore` currently retains an `AgentCore` for session serialization; that dependency should be made generation-independent through a stable codec or equivalent boundary.

Relevant code:

- `core/python/agent_app/sessions.py:150-280`
- `core/python/agent_app/events.py:21-145`

### Existing application action path

Application plugins already define and execute application actions. The server and production frontend adapter already support:

- `GET /application/actions`
- `GET /application/ui-schema`
- `POST /actions`

The reload/configuration capability should extend this path instead of adding a generic public configuration endpoint.

Relevant code:

- `core/python/agent_app/app_plugins.py:22-226`
- `core/python/agent_app/application_future.py:2332-2411`
- `core/python/agent_app/application_future.py:2486-3050`
- `application/python/agent_terminal_app/server.py:2700-2916`
- `packages/frontend-sdk/src/backend/restBackend.ts:609-725`
- `packages/frontend-sdk/src/plugins/actionRunner.ts:240-317`

### Existing Sessions-screen action surface

The Sessions screen already renders plugin-contributed `session_list_action` elements, but those actions are attached to individual session rows and naturally receive session context. There is no application-wide plugin action rendered once for the Sessions screen.

Relevant code:

- `packages/frontend-sdk/src/plugins/pluginsRegistry.ts:60-116`
- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:588-730`
- `packages/frontend-rn-components/src/actions/SessionListActionsBar.tsx:38-280`

The application-wide action requirement needs a distinct global UI contribution or placement rather than overloading a session-row action.

### Current credential exposure and transport

Provider credentials are commonly resolved from environment-backed placeholders. `.env` values are used for configuration resolution, while process environment values take precedence.

The shared action dialog has no password/secret field type; unknown field types fall back to an ordinary visible `TextInput`.

The server exposes resolved session base configuration through `GET /sessions/{session_id}/config/base`. That mapping can contain a resolved provider key and must be redacted as part of credential support.

Direct HTTP connections currently have no general server authentication or TLS requirement. Bridge authorization uses pairing, while transport encryption depends on whether the bridge uses `ws://` or `wss://`.

Relevant code:

- `application/python/agent_terminal_app/__main__.py:348-400`
- `application/python/agent_terminal_app/server.py:1585-1603`
- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx:252-286`
- `packages/frontend-sdk/src/transport/fetchTransport.ts:1-115`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:1-90`

### Combined server and console mode

`--server --console` currently constructs separate server and terminal `AgentApplication` instances that share the event store. Configuration activation must not leave the two request entry points on different active configurations.

Relevant code:

- `application/python/agent_terminal_app/__main__.py:1227-1298`

### Plugin update constraints

Plugin identity currently uses the class-level `name`; the `version` attribute is metadata and does not participate in deduplication. The first class for a plugin id wins within a catalog.

Plugin installation may use revision-specific directories and evict stale Python modules before importing a new revision. Existing classes and instances can remain referenced, but Python imports, `os.environ`, native modules, ports, module-level singletons, and plugin-owned background services remain process-global coexistence risks.

Relevant code:

- `core/python/agent_app/application_future.py:820-858`
- `core/python/agent_app/plugin_sources/install.py:55-220`
- `core/python/agent_app/plugin_sources/local_path.py:45-320`

The preferred version model is generation-specific implementation behind one logical plugin id:

```text
Generation V1: logical plugin "example" -> implementation V1
Generation V2: logical plugin "example" -> implementation V2
```

Versions should not need to appear as separate user-facing plugin ids solely to keep old requests alive.

Hot activation is not guaranteed for plugins that depend on incompatible process-global state, including:

- conflicting environment variables read dynamically;
- Python modules or native libraries that cannot coexist across revisions;
- module-level mutable singletons shared across generations;
- plugins binding the same port or owning another exclusive external resource;
- background services that cannot perform generation-aware handover.

Additive plugins with unique, import-safe package namespaces are the safest initial plugin-change case.

## Intended generation behavior

```text
Request A starts on V1
Request B starts on V1
        |
Candidate V2 is built and validated
        |
Active generation switches V1 -> V2
        |
Request C starts on V2

Request A finishes on V1
Request B finishes on V1
V1 closes after its last lease is released
```

A request must not mix configuration generations across LLM phases, tool calls, lifecycle actions, contexts, or checkpoints.

## Open questions

### Requirement question: credential security boundary

What does "securely set or replace a provider API key" require for transport?

The minimum proposed behavior is:

- masked secret input;
- no prefill of the existing key;
- no key in action responses, UI schemas, configuration endpoints, displays, or errors;
- protected user-owned storage with atomic replacement;
- trusted application plugins;
- explicit secret redaction.

Direct HTTP can currently be unauthenticated and unencrypted. If secure transmission is required, the task must either restrict credential actions to authenticated encrypted connections or expand scope to add authentication and TLS for direct connections.

The answer changes a required security constraint and the server/mobile scope.

### Requirement question: credential persistence and precedence

Should a UI-managed API key:

- survive a complete CLI restart;
- override an already-exported process environment value;
- be stored in an OS credential store or a protected user-owned secret file?

The recommended behavior is persistent protected storage with explicit precedence and no readable-key endpoint. The exact persistence and precedence contract must be decided before credential implementation.

## Related work

The iOS App Review local-runtime task depends on this generic capability:

- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`

## Execution plan
Status: Draft

Direction A keeps `AgentApplication` as the stable process-level object, introduces immutable application configuration generations, and expands `ToolLoopRunner` into the complete owner of one request's runtime dependencies and lifecycle.

This plan does not authorize execution. The open requirement questions must be resolved and the plan approved before implementation begins.

### Requirement verification

#### Plugin-driven configuration activation

- Add an application-layer integration fixture whose application plugin stages a supported configuration change and requests activation through the application-action path.
- Verify the capability through application-plugin action discovery/execution, not a generic configuration endpoint.
- Verify the same CLI/server process remains running and an existing session remains usable.

#### Atomic generation activation and request isolation

- Use a deterministic slow fake provider to start request A on V1, pause it during streaming, activate V2, start request B, and prove A completes on V1 while B uses V2.
- Use a deterministic multi-phase provider/tool fixture to pause a V1 tool, activate changed provider/tool/lifecycle behavior in V2, and prove the remaining V1 tool, LLM, and `request_complete` phases stay on V1.
- Verify V1 closes only after its last request/action lease is released.
- Verify a failed candidate never changes the active-generation identity, is cleaned up, and leaves V1 able to accept new requests.
- Verify concurrent reload attempts are serialized and only a fully validated candidate is published.

#### Expanded ToolLoopRunner ownership

- Add focused tests proving `ToolLoopRunner` owns generation-bound configuration resolution, lifecycle execution, application/tool context, checkpoint coordination, and cancellation without consulting the current active generation.
- Verify between-phase refresh incorporates allowed session/request overrides against the captured generation.
- Verify structural session changes that would switch agent/plugin generation are rejected or deferred rather than applied mid-request.

#### Cancellation and shared persistence

- Start a request on V1, activate V2, cancel the V1 request by request id, and verify cancellation reaches the retired generation.
- Run overlapping V1 and V2 requests and verify both publish to the shared event store and checkpoint through the shared session persistence/reconciliation boundary without losing history.
- Verify server shutdown closes active and retired generations safely.

#### Plugin catalog changes

- Add an import-safe application or tool plugin in V2.
- Verify V1 requests do not see it and V2 requests/actions do.
- Verify application-plugin initialization occurs once per generation and its close hook runs after generation drain.
- Verify one logical plugin id can map to different implementations in V1 and V2 without exposing duplicate user-facing plugin ids.
- Document and test rejection or clear failure for at least one unsupported conflicting plugin case where practical.

#### HTTP and frontend adapter

- Use FastAPI `TestClient` to discover the plugin action and global UI contribution, execute the action through `POST /actions`, and verify subsequent requests use the activated generation.
- Verify application-wide action execution does not require a session id.
- Verify no generic configuration mutation/reload endpoint is introduced.
- Start a real local backend and use `FetchTransport` plus `RestAgentBackend` to discover and execute the action, receive activation status, refresh application schema/actions, and start a request using the new generation.

#### Sessions-screen flow

- Add a global application-action contribution distinct from `session_list_action`.
- Verify the production Sessions screen renders it once rather than once per session row.
- Verify it executes through the production backend adapter without accidental session context.
- Verify success refreshes relevant application actions/schema and failure preserves usable screen state.
- Include at least one frontend integration using the production Sessions screen, real local HTTP routes, `RestAgentBackend`, and a real fixture application plugin.

#### API-key handling

- Use a synthetic key and fake provider; do not require a hosted-provider credential.
- Verify the action field uses masked input, is never prefilled, and is cleared after submission or dismissal.
- Verify action responses, application UI schema, session base configuration, displays, and errors do not contain the key.
- Verify a request started after activation receives the exact new synthetic key.
- Verify a request started before activation keeps its original key through all LLM/tool phases.
- After the persistence question is resolved, verify restart persistence and protected storage behavior where required.
- After the transport-security question is resolved, verify the permitted and rejected connection modes.

#### Combined server and console mode

- Verify configuration activation is coordinated across server and terminal request entry points in `--server --console` mode, so subsequent requests do not use different active generations.

### Documentation

Update plugin-author documentation to explain:

- how an application plugin contributes a supported configuration action;
- how it requests generation activation;
- activation success and failure behavior;
- request generation pinning;
- per-generation application-plugin initialization and cleanup;
- additive plugin and hot-upgrade constraints;
- process-global environment, import, native-resource, and background-service restrictions;
- secret input, storage, redaction, and result rules.

Update application/server/frontend documentation to explain:

- what configuration reload changes;
- when changes affect requests;
- how active requests drain;
- how failures are surfaced;
- how application-wide Sessions-screen actions are contributed and executed;
- the final API-key storage, precedence, and transport-security contract after the open questions are resolved.

### Task checklist

- [ ] Resolve the credential security-boundary requirement question and update the requirements and plan.
- [ ] Resolve the credential persistence/precedence requirement question and update the requirements and plan.
- [ ] Extract stable application services from configuration-generation state.
- [ ] Introduce immutable `ApplicationGeneration` construction, validation, activation, retirement, and cleanup.
- [ ] Expand `ToolLoopRunner` to own the complete request lifecycle and all generation-sensitive request dependencies.
- [ ] Replace callbacks into live `AgentApplication` state with request-owned configuration, lifecycle, context, checkpoint, and persistence collaborators.
- [ ] Make request creation and generation leasing atomic before HTTP background handoff.
- [ ] Add application-wide request registration and generation-aware cancellation.
- [ ] Make session serialization/persistence generation-independent.
- [ ] Implement staged plugin-driven configuration changes and serialized atomic generation activation.
- [ ] Support and document constrained plugin catalog changes across generations.
- [ ] Implement the provider API-key plugin flow after the credential questions are resolved.
- [ ] Add secret redaction and shared masked-input support.
- [ ] Add global application actions to the frontend SDK and Sessions screen.
- [ ] Coordinate generation activation in combined server and console mode.
- [ ] Add the application, HTTP, SDK, frontend, concurrency, failure, cancellation, plugin-change, and credential verification described above.
- [ ] Update plugin-author and application/user documentation.

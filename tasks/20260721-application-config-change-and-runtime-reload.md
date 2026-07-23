# Support Plugin-Driven Configuration Reload and Reusable Application Actions

Deliver two related but independently understandable capabilities:

1. Allow trusted application plugins to update supported application configuration, including provider API keys, and atomically activate the updated configuration without restarting the CLI process.
2. Provide a reusable frontend SDK and UI capability for discovering, presenting, and executing actions owned by the application represented by a specific backend connection.

Configuration changes remain plugin-driven. The platform adds only the runtime, action, secret-handling, SDK, and UI capabilities that plugins cannot safely implement themselves.

## Requirements checklist

### Workstream A: plugin-driven configuration reload

- [ ] **A1. Plugin-supported configuration activation:** A configured application plugin can update configuration that it explicitly supports and activate the resulting configuration without requiring a CLI process restart.
- [ ] **A2. Atomic request behavior:** Requests already in progress finish using the configuration and plugin generation with which they started, while requests started after successful activation use the new generation.
- [ ] **A3. Safe activation failure:** A failed candidate configuration or plugin generation is not activated, the failure is reported, and the previously active generation remains usable for subsequent requests.
- [ ] **A4. Supported plugin catalog changes:** Supported plugin catalog changes can be activated without interrupting requests using the previous generation, subject to documented constraints for process-global environment, imports, native libraries, singleton resources, exclusive resources, and background services.
- [ ] **A5. Secure provider credential changes:** A supporting application plugin can securely set or replace a provider API key, and provider operations started after successful activation use the changed key without exposing the key as a readable configuration value.
- [ ] **A6. Generic action delivery:** Configuration reload and provider-credential operations use Workstream B's reusable application-level action capability. No feature-specific frontend API or generic public configuration CRUD/reload endpoint is added unless implementation proves that the application-action path cannot safely provide a required operation.

### Workstream B: reusable application-level actions

- [ ] **B1. Connection-scoped SDK capability:** The frontend SDK exposes application-level actions as a reusable capability scoped to an explicit `AgentBackend` connection. A client can discover and execute these actions without a session id or session context, and execution affects only the application represented by that backend.
- [ ] **B2. Screen-independent plugin declarations:** Application plugins can contribute application-level action UI declarations that are independent of any particular screen. Frontends can use those declarations with the existing application-action HTTP endpoints and standard result contract without implementing action-specific request logic.
- [ ] **B3. Production Sessions-screen access:** At least one production frontend exposes application-level actions from the Sessions screen using the reusable SDK capability. The exact visual presentation is selected through the open UI-design decision rather than prescribed by this requirement.
- [ ] **B4. Correct behavior across connection changes:** When the selected backend connection changes, the frontend presents and executes only the application-level actions belonging to the newly selected application.
- [ ] **B5. Publicly documented capability:** Public plugin-author, SDK, and frontend-integration documentation explains application-level action discovery, execution, UI declarations, result handling, invalidation, and the distinction between application-level and session-level actions.

## Workstreams

### Workstream A: plugin-driven configuration reload

Provide atomic application configuration generations, request isolation through an expanded `ToolLoopRunner`, constrained plugin changes, and provider credential management.

The user-visible operation is configuration reload. Internally, a stable `AgentApplication` activates immutable application generations. Each request's expanded `ToolLoopRunner` retains the generation, plugins, lifecycle handlers, and runtime dependencies with which it started.

### Workstream B: reusable application-level actions

Provide a reusable frontend SDK and UI capability for discovering, presenting, and executing actions owned by the application represented by a specific backend connection.

This workstream is independent of configuration reload semantics. Configuration reload and credential actions are its first production consumers.

The canonical server-side term is **application-level action** because the action is owned by an `AgentApplication`. From the frontend's perspective, the capability is **connection-scoped** because the selected `AgentBackend` determines which connected application discovers and executes the action.

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

### Design decision: frontend presentation of application-level actions

How should a frontend present application-level actions for the selected connection?

Viable initial presentations include:

- a global actions menu in the Sessions-screen header;
- an application-actions section alongside connection settings;
- a reusable action bar or menu that multiple screens can host;
- more than one host surface using the same SDK action model.

Recommendation:

- implement a reusable application-actions model and shared menu/presentation component;
- use the Sessions screen as the first production host;
- let the host frontend control placement and grouping;
- let plugin UI declarations provide action identity, label, icon, input/dialog metadata, ordering hints, and conditions without requiring a particular screen layout;
- limit the initial implementation to the currently active connection.

Supporting actions against inactive saved connections would require separate connection lifecycle and authentication behavior. The answer affects shared UI component boundaries, placement metadata, accessibility behavior, and frontend verification, but not the underlying application-action HTTP protocol.

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

The backend interface already exposes low-level application action discovery and execution. Workstream B should build a reusable connection-scoped state and presentation capability on this transport foundation rather than add feature-specific request paths.

Relevant code:

- `core/python/agent_app/app_plugins.py:22-226`
- `core/python/agent_app/application_future.py:2332-2411`
- `core/python/agent_app/application_future.py:2486-3050`
- `application/python/agent_terminal_app/server.py:2700-2916`
- `packages/frontend-sdk/src/backend/backend.ts:206-232`
- `packages/frontend-sdk/src/backend/restBackend.ts:609-725`
- `packages/frontend-sdk/src/plugins/actionRunner.ts:240-317`

### Existing frontend action state

The frontend SDK's application plugin registry is connection-keyed and already loads application action definitions and UI schema. It currently normalizes recognized elements into session, message, and session-list action surfaces; it does not expose a reusable screen-independent application action surface.

Relevant code:

- `packages/frontend-sdk/src/plugins/pluginsRegistry.ts:20-220`
- `packages/frontend-sdk-react/src/applicationPlugins.tsx:1-107`

The reusable capability may extend the existing registry or extract a dedicated application-actions controller. The hard requirement is the public behavior and ownership boundary, not a specific class name.

### Existing Sessions-screen action surface

The Sessions screen already renders plugin-contributed `session_list_action` elements, but those actions are attached to individual session rows and naturally receive session context. There is no application-wide plugin action rendered once for the connected application.

Relevant code:

- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:588-730`
- `packages/frontend-rn-components/src/actions/SessionListActionsBar.tsx:38-280`

The application-level action capability needs a screen-independent declaration and a global host presentation rather than overloading a session-row action.

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

## Related work

The iOS App Review local-runtime task depends on the configuration reload capability:

- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`

## Execution plan
Status: Draft

Direction A keeps `AgentApplication` as the stable process-level object, introduces immutable application configuration generations, and expands `ToolLoopRunner` into the complete owner of one request's runtime dependencies and lifecycle.

Workstream B adds a reusable, connection-scoped application-action capability to the frontend SDK and shared frontend layers. Workstream A consumes this generic capability for configuration reload and credential actions.

This plan does not authorize execution. The open requirement questions and material UI design decision must be resolved and the plan approved before implementation begins.

### Requirement verification

This section records concise, user-observable acceptance evidence for each hard requirement. Detailed tests needed for the selected implementation are listed separately under `Additional implementation verification`.

#### Workstream A: plugin-driven configuration reload

- **A1 — Configuration can be changed without restarting:** Execute a supporting plugin action that changes an observable application configuration value. Verify that a subsequent request uses the changed value while the same CLI/server process and an existing session remain available.
- **A2 — Activation is atomic for active requests:** Start a multi-phase request using configuration V1 and pause it during provider or tool work. Activate V2 and start another request. Verify that the original request completes entirely with V1 while the later request uses V2.
- **A3 — Failed activation preserves the working application:** Attempt to activate invalid configuration. Verify that the action reports failure, the previously active configuration remains in effect, and subsequent requests continue to succeed without a process restart.
- **A4 — Supported plugin changes respect request generations:** Start a request using the existing plugin generation, activate a supported plugin catalog change, and then start another request. Verify that the original request finishes with its original plugins and the later request uses the activated plugin generation.
- **A5 — Provider credentials can be changed safely:** Set a synthetic provider API key through the supporting plugin action. Verify that a subsequent provider operation uses the new key and that the key is not displayed or returned through the user-visible action, settings, or configuration flow. Extend this evidence with the final storage and transport behavior after the credential open questions are resolved.
- **A6 — Reload and credential operations use generic application actions:** From the production application-action surface, execute the reload and credential flows against the selected application. Verify that the frontend uses Workstream B's reusable capability and does not require a configuration-specific frontend API or generic configuration endpoint.

#### Workstream B: reusable application-level actions

- **B1 — Actions target the selected application connection:** Run two independently observable fixture applications. Discover and execute an application-level action through the frontend SDK against the first connection and verify that only the first application changes. Repeat against the second connection and verify that the action is directed there. No session is selected or supplied in either flow.
- **B2 — Plugin-contributed actions require no feature-specific frontend implementation:** Configure a real application plugin that contributes an application-level action and its UI declaration. Using a production frontend and production backend adapter, verify that the action is discovered, presented, accepts its declared input, executes successfully, and displays its standard result without adding frontend code specific to that action.
- **B3 — Actions are available from the Sessions screen:** Connect the production frontend to an application that contributes an application-level action. Verify that the user can find and execute the action from the Sessions screen using the selected UI presentation, without first choosing a session, and that success and failure are both communicated clearly.
- **B4 — Connection changes select the correct action capability:** Connect the frontend to one application, observe its available application-level actions, and then change to another connection with a different action set. Verify that the frontend presents and executes only the actions belonging to the currently selected application.
- **B5 — The capability is publicly understandable:** Verify that public plugin, SDK, and frontend documentation describes how to contribute, discover, present, and execute an application-level action for a specific backend connection, including a complete tested example that does not require reading implementation source.

### Additional implementation verification

The selected implementation must add focused verification for its technical risks. These checks support the acceptance evidence above but are not themselves the requirement-level acceptance checklist.

#### Workstream A implementation risks

- Application generation construction, validation, atomic publication, retirement, lease accounting, and cleanup.
- Expanded `ToolLoopRunner` ownership of generation-bound configuration resolution, lifecycle execution, application/tool context, checkpoint coordination, cancellation, and generation release.
- Between-phase refresh using the captured generation plus allowed session/request overrides.
- Rejection or deferral of structural session changes that would switch agents or plugins mid-request.
- Request creation and generation leasing before HTTP background handoff.
- Cancellation routing to requests owned by retired generations.
- Concurrent reload serialization.
- Failed candidate resource cleanup.
- Shared event publication and session checkpoint reconciliation across overlapping generations.
- Generation-independent session serialization.
- Application-plugin initialization and close hooks per generation.
- Supported additive/import-safe plugin activation.
- Clear failure for unsupported process-global plugin conflicts where practical.
- Shutdown while active and retired generations are draining.
- Coordinated activation across server and terminal request entry points in `--server --console` mode.

#### Workstream B implementation risks

- Application-action declaration normalization and validation.
- Action identity keyed by both plugin id and action id.
- Connection-scoped action caching and invalidation.
- Correct action/schema refresh after generation activation.
- Standard success, validation-failure, display, and UI-effect handling.
- HTTP response envelopes and idempotency through the existing routes.
- React controller/provider state transitions.
- Shared presentation behavior selected through the UI design decision.
- Accessibility labels and stable production test identifiers.
- Connection switching without stale actions leaking between backends.
- Public HTTP integration using a real fixture application plugin.
- Production adapter and production Sessions-screen integration.

#### Credential implementation risks

- Masked secret input, no prefill, and clearing after submission or dismissal.
- Redaction from action responses, UI schema, session base configuration, displays, and errors.
- A request started after activation receiving the new synthetic key.
- A request started before activation retaining its original key through all LLM/tool phases.
- Restart persistence and protected storage after the persistence question is resolved.
- Permitted and rejected connection modes after the transport-security question is resolved.

### Workstream A plan: configuration generations and ToolLoopRunner isolation

1. Separate stable application services from generation-specific configuration and runtime state.
2. Introduce immutable `ApplicationGeneration` construction, validation, activation, retirement, and cleanup.
3. Expand `ToolLoopRunner` to own the complete request lifecycle and all generation-sensitive request dependencies while keeping the existing name.
4. Replace callbacks into live `AgentApplication` state with request-owned configuration, lifecycle, context, checkpoint, and persistence collaborators.
5. Provide a generation-bound application facade for tools and plugins so active requests cannot accidentally consult the newly active generation.
6. Make request creation, generation leasing, cancellation registration, and background handoff atomic.
7. Add application-wide request registration and generation-aware cancellation.
8. Make session serialization and shared persistence generation-independent.
9. Implement staged plugin-driven configuration changes and serialized atomic generation activation.
10. Support and document constrained plugin catalog changes across generations.
11. Coordinate generation activation in combined server and console mode.
12. Implement provider credential changes after the credential questions are resolved.
13. Expose reload and credential operations through Workstream B rather than feature-specific frontend APIs.

### Workstream B plan: reusable application-level actions

1. Define a screen-independent application-level action UI declaration distinct from session, message, and session-list actions.
2. Build reusable connection-scoped application-action state on the existing `AgentBackend` discovery and execution methods.
3. Normalize and expose action definitions, UI declarations, loading/error state, refresh, invalidation, and standard result handling without coupling the SDK to configuration reload.
4. Ensure action identity and caches remain scoped to the plugin and selected backend connection.
5. Add React bindings for application-action discovery and execution.
6. Resolve the frontend presentation design decision.
7. Add the selected shared React Native application-action presentation.
8. Integrate the reusable capability into the production Sessions screen as its first host.
9. Add two-backend connection-isolation verification.
10. Add public HTTP, production adapter, and production frontend integration coverage.
11. Document plugin-author, SDK-consumer, and frontend-host contracts.

### Shared plan concerns

- Reuse `GET /application/actions`, `GET /application/ui-schema`, and `POST /actions` unless a concrete verified gap requires extending the protocol.
- Define a reserved internal application effect for generation activation that is consumed after the contributing plugin action returns.
- Refresh connection-scoped application actions and UI declarations after activation where the active generation changes them.
- Keep configuration-specific semantics in Workstream A plugins rather than the generic Workstream B SDK and UI layers.

### Documentation

#### Workstream A audiences

Update plugin-author documentation to explain:

- how a plugin stages a supported configuration change;
- how it requests generation activation;
- activation success and failure behavior;
- request generation pinning;
- per-generation application-plugin initialization and cleanup;
- additive plugin and hot-upgrade constraints;
- process-global environment, import, native-resource, and background-service restrictions;
- secret input, storage, redaction, and result rules.

Update application/server documentation to explain:

- what configuration reload changes;
- when changes affect requests;
- how active requests drain;
- how failures are surfaced;
- the final API-key storage, precedence, and transport-security contract after the open questions are resolved.

#### Workstream B audiences

Document application-level actions for:

- plugin authors defining actions and screen-independent UI declarations;
- SDK consumers discovering, caching, invalidating, and executing actions for an explicit backend connection;
- frontend authors hosting application actions, rendering standard dialogs/results, and distinguishing application-level actions from session, message, and session-list actions.

Documentation must clarify:

| Term | Meaning |
|---|---|
| Application-level action | Owned and executed by one `AgentApplication` |
| Connection-scoped frontend state | The selected `AgentBackend` connection identifies that application |
| Session action | Requires or operates on a specific session |
| Session-list action | Repeated for or mapped from an individual session row |
| Application action UI host | A frontend location that presents actions for the connected application |

Documentation verification includes a successful docs build, validated links and exports, and tested examples or snippets where practical.

### Task checklist

#### Workstream A

- [ ] Resolve the credential security-boundary requirement question and update A5 and its verification.
- [ ] Resolve the credential persistence/precedence requirement question and update A5 and its verification.
- [ ] Extract stable application services from configuration-generation state.
- [ ] Introduce immutable `ApplicationGeneration` construction, validation, activation, retirement, and cleanup.
- [ ] Expand `ToolLoopRunner` to own the complete request lifecycle and all generation-sensitive request dependencies.
- [ ] Replace callbacks into live `AgentApplication` state with request-owned collaborators and a generation-bound application facade.
- [ ] Make request creation and generation leasing atomic before HTTP background handoff.
- [ ] Add application-wide request registration and generation-aware cancellation.
- [ ] Make session serialization/persistence generation-independent.
- [ ] Implement staged plugin-driven configuration changes and serialized atomic generation activation.
- [ ] Support and document constrained plugin catalog changes across generations.
- [ ] Coordinate generation activation in combined server and console mode.
- [ ] Implement provider credential changes, protected storage, redaction, and masked input after the credential questions are resolved.
- [ ] Expose reload and credential operations through Workstream B.

#### Workstream B

- [ ] Define the screen-independent application-level action UI declaration.
- [ ] Add reusable connection-scoped application-action state to the frontend SDK.
- [ ] Add React bindings for application-action discovery and execution.
- [ ] Resolve the application-action UI presentation design decision.
- [ ] Add the selected shared React Native application-action presentation.
- [ ] Integrate the reusable capability into the production Sessions screen.
- [ ] Add two-backend connection-isolation verification.
- [ ] Add public HTTP and production-adapter integration coverage.
- [ ] Document the plugin, SDK, and frontend application-action contracts.

#### Shared verification and documentation

- [ ] Add the concise requirement acceptance evidence for A1-A6 and B1-B5.
- [ ] Add the additional implementation verification required by the selected solution.
- [ ] Verify Workstream A consumers use Workstream B without feature-specific frontend request logic.
- [ ] Build and validate the affected public documentation and tested examples.

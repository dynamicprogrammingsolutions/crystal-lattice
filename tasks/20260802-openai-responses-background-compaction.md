# OpenAI Responses Background Native Compaction

Run OpenAI Responses native compaction as observable background work, support
optional request continuation after compaction, and move request-start
orchestration out of the FastAPI adapter into shared application-layer code.

## Requirements checklist

- [x] OpenAI Responses native compaction runs in the background, allowing the
  initiating action to return promptly.
- [x] The user can follow compaction progress through a persistent session
  notification that reports current activity and elapsed time approximately
  every 15 seconds.
- [x] The compaction notification reports successful completion or failure
  and allows the user to request cancellation while compaction is running.
- [ ] The user can choose whether successful compaction stops after updating
  the session or immediately starts a normal model request without appending a
  new message.
- [x] Request-start orchestration is moved out of the FastAPI server into
  shared application-layer functionality available to application
  entrypoints, plugins, and background work.
- [ ] Requests started after compaction have the same behavior, events,
  persistence, cancellation, and frontend visibility as requests started
  through the ordinary send flow.
- [ ] Background compaction, session updates, and optional request
  continuation are coordinated safely with concurrent session activity and
  application reload or shutdown.
- [x] The background-operation lifecycle support introduced for compaction is
  reusable by other plugins while notification, progress, and cancellation
  behavior remain controlled by the owning plugin.
- [ ] Existing user-visible send behavior and compatibility are preserved
  after request orchestration moves out of FastAPI.

## Scope

In scope:

- the OpenAI Responses native compaction action and package;
- shared application-layer request-start orchestration;
- application-lifetime background-process registration and cleanup;
- persistent compaction progress, cancellation, success, and failure;
- optional no-message request continuation;
- server and terminal/application entrypoint delegation where needed for one
  authoritative request-start workflow;
- plugin-authoring and package documentation needed to use the resulting
  contracts.

Out of scope:

- migrating existing MCP runtime ownership to the new background-process
  registry;
- migrating Claude, Gemini, or Qwen shell background execution;
- implementing generic notification history UI;
- making all request/action errors persistent notifications;
- standardizing every transient frontend loading indicator;
- changing provider-native compaction semantics or compacted-output mapping
  beyond what asynchronous execution requires.

## Open requirement questions

1. While compaction is active, should a new send for the same session be
   rejected or allowed to proceed with compaction failing safely if history
   changes?
   - Recommendation: reject the new send so the user does not pay for
     compaction that cannot be committed.
2. Is transport cancellation sufficient when the current OpenAI compact
   endpoint has no background operation ID or explicit cancel method?
   - Recommendation: yes. Run compact through the async SDK and cancel its
     task, which closes/resets the underlying HTTP exchange. Retain
     late-result and guarded-commit checks as defense in depth.
3. What should application reload do with active compaction?
   - Recommendation: close the application-generation-owned process, mark it
     interrupted, and discard a late provider result rather than delaying
     reload for an unbounded provider call.
4. Which configuration should an automatic post-compaction request use?
   - Recommendation: resolve the latest effective session configuration after
     compaction commits.
5. What happens when compaction succeeds but automatic continuation cannot
   obtain request admission?
   - Recommendation: keep compaction successful and present a persistent
     manual Continue action.
6. How should active operation registration relate to plugin status and
   notifications before an operations-menu UI exists?
   - Decision: the application service stores only active identity and
     admission. Plugins own all additional status and notification fields.
     A future menu may accept arbitrary optional owner-provided details without
     predefining them in the admission service.

## Supporting facts

### Current native compaction

- The implementation is
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`.
- Its `compact_native_history` provider-extension action calls
  `client.responses.compact(...)` synchronously and returns replacement native
  history after the provider call completes.
- The action commonly exceeds the normal two-minute interaction window.
- `AgentApplication.execute_session_action(...)` snapshots the session and
  file state, releases the session lock while plugin work runs, and later
  saves through optimistic reconciliation.
- Reconciliation preserves compatible non-protected metadata changes and
  rejects changed message history rather than silently overwriting it.

### Notifications

- Persistent session notifications already support stable IDs and keys,
  revisions, progress-style updates, follow-up actions, dismissal,
  resolution, retention, reconnect hydration, and future history display.
- Provider-extension actions invoked through `AgentApplication` receive
  application context, but the long-running process should receive only the
  narrow notification and persistence dependencies it needs.
- Notification behavior is domain behavior owned by the compaction process,
  not by generic process-registration infrastructure.

### Runtime ownership

- `AgentApplication.RuntimeStore` can retain arbitrary application-lifetime
  runtime objects and calls their `close()` method when the application
  closes or is replaced.
- MCP uses this pattern for application-lifetime runtime managers.
- Claude Bash uses a more specialized filesystem-backed process registry for
  detached OS commands.
- A minimal shared registry can provide registration, lookup,
  identity-safe removal, and close-on-application-close without knowing about
  notifications, sessions, OpenAI, or cancellation policy.
- MCP and shell implementations may use adapters later, but wrapping or
  migrating them provides no required benefit for this task.

### Request initiation

- `POST /sessions/{session_id}/send` already starts a request without
  appending a message.
- `AgentApplication.send_request(...)` executes the request, but FastAPI
  currently owns additional orchestration such as session admission,
  background worker startup, event publication, and active-request cleanup.
- A plugin can technically invoke `AgentApplication.send_request(...)`, but it
  cannot obtain full parity safely while ordinary HTTP sends use separate
  server-owned admission state.
- The blocker is therefore fragmented request ownership, not an inability for
  `AgentApplication` to execute a no-message request.

### Documentation baseline

- Current plugin docs describe provider-extension actions, application
  context, notifications, application plugin cleanup, and low-level request
  execution.
- They do not yet provide a complete standalone pattern for background action
  lifetime, lookup, cooperative cancellation, periodic notification updates,
  safe long-running session commits, or request continuation.

## Execution plan

Status: Draft

Implement the work in independently verifiable stages. Each stage should
preserve existing public behavior and stop for review if completing it requires
substantially broader ownership changes than described here.

### Stage A — Shared request-start orchestration

Stage A plan status: Implemented on August 2, 2026; manual checkpoint pending.

#### Target ownership

Add an application-layer request coordinator, tentatively in
`core/python/agent_app/request_execution.py`, and construct one coordinator per
`AgentApplication`.

The coordinator becomes the single authority for:

- one active request per session;
- request ID allocation;
- loading and validating the writable live session;
- optional atomic message append before request start;
- request-level config overrides;
- execution of `AgentApplication.send_request(...)`;
- filtering internal `session_checkpoint` events;
- publishing public events to the application event store;
- active-request lookup;
- release of request admission and application-generation ownership.

`AgentApplication.send_request(...)` remains the low-level event generator. The
coordinator owns the higher-level operation that applications and plugins
actually start.

Expose thin application methods around the coordinator. The proposed public
shape is:

```python
app.start_session_request(
    session_id,
    overrides=None,
    *,
    stream=True,
) -> SessionRequestStart

app.start_session_request_with_message(
    session_id,
    *,
    role,
    content,
    metadata=None,
    multipart_content=None,
    overrides=None,
    stream=True,
) -> SessionRequestStart

app.run_session_request(
    session_id,
    overrides=None,
    *,
    stream=True,
    on_checkpoint=None,
) -> SessionRequestResult

app.get_active_session_request_id(session_id) -> str | None
```

Names may be adjusted during implementation, but Stage A should retain these
three capabilities:

1. start an existing session in the background;
2. atomically append and start in the background;
3. run the same coordinated request synchronously for non-HTTP consumers that
   need a completion result.

`SessionRequestStart` should distinguish `started` from `already_running` and
always carry the authoritative request ID. `SessionRequestResult` should carry
the final session/result information currently returned by
`TerminalApplication.send_request(...)`.

#### Admission and application-generation lifetime

Move `_active_send_request_by_session` and its lock from FastAPI into the
coordinator.

Admission must occur before an optional message append. If the session already
has an active request:

- starting an existing session returns `already_running`;
- append-and-start does not append the message and returns the same
  authoritative active request ID;
- the HTTP adapter preserves its current response distinction: `/send` returns
  the existing request, while `/send_message` maps this result to HTTP 409.

Extend the application lifecycle control boundary so the coordinator can
acquire an operation for the exact `AgentApplication` generation it will use.
The recommended contract is an owner operation-acquisition method rather than
passing FastAPI's middleware-owned operation into application code.

For a background start:

1. acquire generation ownership;
2. validate that the acquired application is the initiating application;
3. reserve the session and prepare the request;
4. start the worker;
5. return accepted while the worker retains generation ownership;
6. release ownership and admission in one `finally` path.

This keeps reload behavior correct for HTTP, terminal, plugins, and the future
compaction continuation. A stale application generation or reload-pending
application must reject new request admission before appending a message.

The coordinator should also be closed explicitly by `AgentApplication.close()`.
With an application owner, admitted request workers should already have drained
before application close. Without an owner, coordinator close should reject new
starts, request cooperative cancellation for active requests, and prevent a
late worker from publishing through a disposed application.

Keep the existing `AgentApplication.cancel_request(request_id)` contract.
Once the coordinator starts the low-level generator with its chosen request
ID, cancellation continues through the existing application-owned
`RequestCancellation`.

#### Shared preparation and execution

Under the session lock, the coordinator should:

- reject readonly snapshot views through the existing application error;
- load the current core, base config, session, and file state;
- reserve the active request;
- when requested, resolve effective config, append the normalized message,
  persist it, publish `message_appended`, and record its checkpoint;
- capture the post-append session/file baseline for the request worker.

The request worker should:

- call the existing low-level generator with the prepared core, session,
  base config, overrides, request ID, and baseline file state;
- route live `session_checkpoint` objects only to an optional in-process
  callback;
- publish every public event through `AgentApplication.publish_event(...)`;
- collect final information for synchronous callers;
- log unexpected worker failures consistently;
- clear admission and release generation ownership regardless of completion,
  cancellation, provider error, or unexpected exception.

Use `AgentApplication`'s existing effective-config resolution rather than
duplicating session-override merging in HTTP code.

#### FastAPI migration

Keep the following in `server.py`:

- request payload and multipart-message validation;
- HTTP idempotency cache behavior;
- HTTP status/error translation;
- response serialization;
- route declarations and dependency injection.

Remove or stop using the following server-owned business logic:

- `_active_send_request_by_session` and its helper functions;
- `_generate_request_id(...)`;
- `_load_session_ctx_for_send(...)`;
- `_merged_session_overrides(...)`;
- `_effective_session_config(...)` where only used by send orchestration;
- `_append_message_to_session_locked(...)` where only used by send;
- `_run_send_request_background(...)`.

Route behavior remains:

- `/sessions/{id}/send` delegates to
  `app.start_session_request(...)`;
- `/sessions/{id}/send_message` delegates normalized message content to
  `app.start_session_request_with_message(...)`;
- `/requests/{id}/cancel` remains a thin call to
  `app.cancel_request(...)`;
- snapshot select/restore and any other active-request guards query
  `app.get_active_session_request_id(...)`;
- `/sessions/{id}/messages` continues deriving frontend
  `active_request_id` from checkpoint/cursor state, preserving its snapshot
  consistency contract.

Do not move HTTP idempotency into the coordinator. Idempotency keys are an HTTP
transport concern; single-flight request admission is application behavior.

#### Terminal migration

Change `TerminalApplication.send_request(...)` to delegate to
`app.run_session_request(...)`, preserving its current tuple return contract
and local active-session updates through the checkpoint callback and final
result.

Add a terminal application operation that atomically appends a user message
and starts the request through
`app.start_session_request_with_message(...)`. The interactive terminal input
handler should use this operation instead of appending first and then creating
its own background request task.

Keep explicit append-without-send commands unchanged.

The terminal remains responsible for:

- terminal input handling;
- event polling and rendering;
- command-specific user messages.

It should no longer own request execution, application-owner retention, or a
separate background thread wrapper for ordinary user sends.

#### Compatibility and failure mapping

Preserve these existing public behaviors:

- `/send` acknowledges promptly with `status: "started"` and a request ID;
- repeated `/send` returns `status: "already_running"` and the original ID;
- `/send_message` does not double-append under retries or concurrent sends;
- HTTP idempotency replay returns the original response;
- readonly, missing-session, unknown-agent, and reload-pending conditions keep
  equivalent public status/error semantics;
- request events and checkpoint ordering remain unchanged;
- request cancellation still clears frontend active-request state;
- direct `AgentApplication` use without an `AgentApplicationOwner` remains
  supported.

Define application-layer exceptions/results without importing FastAPI. The
server translates them to the existing HTTP responses.

#### Stage A automated verification

Add focused application-layer coordinator tests covering:

- immediate background acknowledgement;
- synchronous coordinated execution;
- active request lookup;
- duplicate existing-session starts;
- duplicate append-and-start without a second append;
- cleanup after success, provider error, cancellation, and unexpected worker
  failure;
- readonly and missing session rejection before worker start;
- atomic append event/checkpoint behavior;
- public event publication and internal checkpoint filtering;
- terminal checkpoint callback/final result behavior;
- generation ownership preventing reload from replacing an application while
  its request worker is active;
- rejection of a start against a stale or reload-pending generation.

Update server tests to assert behavior only through application/public route
boundaries rather than polling private FastAPI active-request globals.
Retain coverage for:

- `/send` single-flight and idempotency;
- `/send_message` atomic append, 409 behavior, and idempotency;
- active request ID snapshots;
- cancellation;
- snapshot select/restore guards;
- request/event cursor alignment;
- attachment and request-override behavior.

Add a cross-entrypoint test proving that a request started by the terminal or
shared application API is visible to the HTTP send route as the same active
request, and vice versa.

Run the existing frontend SDK backend/idempotency tests and focused
mobile/desktop send smoke tests because the HTTP response and event contracts
must remain unchanged even though no frontend code is expected to change.

#### Stage A development documentation follow-up

Plan status: Approved on August 2, 2026.

Add one canonical implementation guide:

`application/python/docs/development/request-execution.md`

A specification directory is not justified for the current material. Request
execution has several phases, but they form one cohesive lifecycle with one
maintainer audience and one source-of-truth implementation boundary. Splitting
admission, execution, events, cancellation, and reload into separate pages
would duplicate terminology and force readers to navigate between files to
understand one request.

Reconsider a directory only if this documentation later needs independently
versioned product requirements, a public protocol specification, or separate
provider/tool-loop implementation guides.

The page should document:

1. **Purpose and scope**
   - distinguish the high-level `SessionRequestCoordinator` from the
     low-level `AgentApplication.send_request(...)` event generator and the
     `ToolLoopRunner`;
   - state that FastAPI and terminal are adapters, not request owners.
2. **Ownership map**
   - identify responsibilities of `AgentApplication`,
     `SessionRequestCoordinator`, `AgentApplicationOwner`, `ToolLoopRunner`,
     the event store, FastAPI, and terminal;
   - include one compact flow diagram or sequence table.
3. **Application request APIs**
   - explain existing-history background start, atomic append-and-start,
     synchronous run, active-request lookup, and cancellation;
   - document start/result objects and `started` versus `already_running`.
4. **Admission and preparation**
   - one active request per session;
   - application-generation acquisition;
   - writable/live-session and snapshot checks;
   - stored plus explicit override precedence;
   - request ID and baseline capture;
   - atomic append persistence, event, and checkpoint behavior.
5. **Execution lifecycle**
   - worker versus synchronous execution;
   - `request_prepare`, tool preparation, provider/tool-loop phases,
     `request_complete`, and `request_error`;
   - streaming fallback and request-specific cancellation.
6. **Persistence and events**
   - internal `session_checkpoint` handling;
   - public event publication;
   - checkpoint/cursor semantics and frontend `active_request_id`;
   - optimistic reconciliation and conflict behavior.
7. **Cancellation, reload, and close**
   - cancellation before and after the live cancellation object exists;
   - owner-operation retention while HTTP returns immediately;
   - reload-pending and stale-generation rejection;
   - direct application close behavior.
8. **Adapter behavior**
   - what remains in FastAPI, including validation and idempotency;
   - how terminal ordinary send and append-without-send differ;
   - how application plugins and future background compaction should start a
     no-message request.
9. **Failure semantics and invariants**
   - cleanup in every terminal path;
   - no second append on duplicate admission;
   - no FastAPI imports or HTTP errors in application-layer code;
   - public compatibility expectations.
10. **Source and test map**
    - link the coordinator, application generator, owner, tool loop, server,
      terminal, event documentation, and primary regression tests.

Keep the page implementation-focused. Do not duplicate provider streaming
algorithms, notification design, HTTP endpoint reference material, or the
runtime reload product specification; link those canonical documents instead.

Update:

- `application/python/docs/development/index.md` to list the new guide first;
- `application/python/docs/development/runtime-owner-integration.md` to replace
  detailed request-worker explanation with a concise summary and link;
- `application/python/agent_terminal_app/server_endpoints_parity.md`,
  `application/python/README.md`, and `docs/api/events.md` with focused links
  where they discuss request ownership.

Verification:

- inspect every referenced method/event against current code;
- verify relative links from the application development directory;
- run `mkdocs build -f docs_site/mkdocs.yml` for shared documentation
  regressions, while noting that package-local development pages are not
  currently part of the public MkDocs navigation;
- ensure the local development index provides the canonical discovery path.

Checkpoint A:

- ordinary mobile/desktop send behaves unchanged;
- duplicate sends remain prevented;
- cancellation remains visible and functional;
- a terminal-started request and an HTTP-started request share one active
  request authority;
- application reload waits for an admitted request worker and rejects new
  starts while reload is pending;
- FastAPI no longer owns active-request execution state, request threads,
  message-append request preparation, or event-publication worker logic.

### Stage B — Shared managed background-process lifecycle

Stage B plan status: Implemented on August 3, 2026.

#### Target package and ownership

Add a shared application-layer module:

`core/python/agent_app/managed_processes.py`

This location makes the contract available to every Python plugin that depends
on the `agent-core` distribution without creating a plugin-to-plugin
dependency. Export the public types through `agent_app`, but do not add new
managed-process methods to `AgentApplication`.

Plugins obtain the registry through the existing runtime store:

```python
registry = get_managed_process_registry(app.get_runtime_store())
```

The helper uses one stable runtime-store key and
`RuntimeStore.get_or_create(...)`. The runtime store remains the application
lifetime owner and invokes `registry.close()` during application close or
replacement.

#### Public contract

Define a minimal synchronous process protocol:

```python
class ManagedProcess(Protocol):
    def start(self) -> None:
        """Launch background work and return promptly."""

    def close(self) -> None:
        """Request shutdown, invalidate late work, and return promptly."""
```

The process object may expose any additional concrete API required by its
plugin, such as `request_cancel(...)`, `send(...)`, or state inspection. Those
methods are intentionally absent from the shared protocol.

Define a registry with this conceptual API:

```python
registry.start(process_id, process) -> process
registry.get(process_id) -> ManagedProcess | None
registry.remove(process_id, process) -> bool
registry.close() -> None
```

Use a type variable so `start(...)` and typed lookup helpers can preserve the
concrete process type where practical. Keep runtime behavior duck-typed.

Contract details:

- the plugin chooses the unique process ID;
- duplicate IDs fail explicitly rather than replacing live work;
- `start(...)` reserves the ID before invoking process code;
- `start()` must only launch work and return promptly;
- `close()` must perform bounded shutdown signaling and return promptly rather
  than waiting indefinitely for a non-interruptible provider or subprocess;
- startup failure removes the reservation, attempts best-effort process
  cleanup, and re-raises the original error;
- `remove(process_id, process)` removes only when both ID and object identity
  match, preventing an old completion callback from removing a replacement;
- normal completion does not imply `close()`; the process removes itself after
  it has completed its own terminal behavior;
- registry close rejects future starts, closes every still-registered process,
  and attempts all closes even when one fails;
- startup-cleanup and close failures are logged, while registry close remains
  best effort and does not stop at the first failing process;
- close is idempotent;
- the registry does not generate IDs, create threads, inspect process state,
  persist records, publish events, send notifications, or define cancellation
  semantics.

#### Start, completion, and close races

Use an internal entry state and condition variable so arbitrary process code is
not called while holding the registry lock.

The registry should distinguish `starting` from `running` entries:

1. reserve a `starting` entry under the registry lock;
2. call `process.start()` outside the lock;
3. promote the same entry to `running` after successful return;
4. remove and best-effort close it after startup failure;
5. allow identity-safe removal requested by an extremely fast completion while
   startup is still returning;
6. make `close()` reject new starts and wait for in-progress `start()` calls to
   finish their registry transition;
7. if close wins the race, close the newly started process before registry
   close returns.

The prompt-returning `start()` requirement prevents an application shutdown
from waiting on the actual long-running operation. The operation itself runs in
the process-owned thread, task, subprocess, or runtime.

`get(...)` may return the reserved process while it is starting. This keeps
lookup simple and allows operation-specific communication as soon as the
process has been registered.

#### Dependency injection and process responsibilities

Construct the process with its dependencies before registration. For
compaction this can later include narrow callbacks or capability objects for:

- notification creation/revision/resolution;
- session baseline loading and commit;
- request continuation;
- clocks and timers;
- provider invocation;
- identity-safe registry removal.

The generic registry must not import notification, session, request, OpenAI,
HTTP, or frontend modules.

The process is responsible for:

- its worker implementation;
- cooperative cancellation;
- progress and error reporting;
- refusing late commits after cancellation or close;
- terminal notification behavior;
- removing itself from the registry on normal completion.

#### MCP and shell compatibility boundary

Do not modify or wrap the existing MCP and shell registries in Stage B.

- MCP owns an aggregate registry of asynchronous server runtimes, discovery
  state, and tool calls. Its existing `RuntimeStore` ownership already provides
  application close.
- `tool-compat-shared.BackgroundProcessRegistry` owns durable subprocess
  manifests, detached-process reconciliation, output files, and shutdown
  policies. The new in-memory object registry must not duplicate or replace
  those semantics.

Document that future adapters may register an owning facade when useful, but
there is no requirement that every subprocess or MCP server become an
individual `ManagedProcess`.

#### Automated verification

Add focused core tests for:

- start, lookup, normal identity-safe removal, and close;
- duplicate process IDs;
- stale removal after a replacement uses the same ID;
- startup failure cleanup without affecting other processes;
- one failing `close()` not preventing remaining closes;
- idempotent registry close and rejection of later starts;
- concurrent starts for the same ID admitting exactly one process;
- completion/removal while `start()` is still returning;
- close racing with a controlled startup and closing the admitted process
  before registry close returns;
- `RuntimeStore.close()` closing the registry and all registered objects.

Add one application-level integration fixture plugin whose public actions:

1. construct and start a dummy managed process;
2. return immediately with its process ID;
3. find it in a later action;
4. call a process-specific communication method;
5. report observed state.

Run that flow through `AgentApplication.execute_application_action(...)`, then
replace the application through `AgentApplicationOwner` and assert that the old
generation closes the dummy process.

The fixture should live in the owning test package, not as a production plugin.

Retain the existing MCP owner-reload test and shell registry tests as
compatibility evidence; no new dependency on the shared registry should be
introduced.

#### Documentation

Add a generic plugin-authoring page:

`plugins/docs/managed-background-processes.md`

It should explain:

- when to use this in-memory application-lifetime registry;
- when to use a durable subprocess registry instead;
- process construction and dependency injection;
- start, lookup, communication, completion removal, and close;
- why notifications and cancellation stay process-owned;
- the non-blocking `start()` requirement;
- application reload and shutdown behavior;
- a minimal dummy process example.

Link it from:

- `plugins/docs/index.md`;
- `plugins/docs/actions.md`;
- `plugins/docs/application-plugins.md`;
- `plugins/docs/provider-extensions.md`.

Do not add compaction-specific notification examples until Stage C defines the
actual process behavior.

Checkpoint B:

- a dummy application plugin can start a process, return, find it in a later
  action, communicate with it, and observe it close during application
  replacement;
- registry concurrency tests prove duplicate admission, startup cleanup,
  identity-safe completion, and close/start race behavior;
- MCP and shell behavior remains unchanged.

### Stage C — Background native compaction and progress

Stage C plan status: Implemented on August 3, 2026.

#### Material admission decision

Stage A provides request-versus-request single-flight admission, and Stage B
provides managed-process identity, but there is not yet one atomic admission
boundary shared by ordinary requests and compaction.

Optimistic session reconciliation prevents a corrupt late compaction commit,
but by itself it allows this race:

1. compaction captures history and starts the provider call;
2. an ordinary request appends or generates new history;
3. compaction finishes and fails its commit safely.

The user still pays for compaction that can no longer be applied.

Recommended Stage C decision: add a small application-level operation service
that owns only active registration, lookup, and operation admission, while the
Stage B managed-process registry continues to own runtime-object lifetime.

Store the operation service in `RuntimeStore` rather than adding
`AgentApplication` methods for its registry contract. Both
`SessionRequestCoordinator` and the compaction application plugin receive the
same service instance.

The operation service should:

- atomically reserve an operation ID and opaque exclusivity keys;
- expose only `operation_id`, `owner_id`, and optional `session_id`;
- list active registrations globally, by owner, or by session;
- release registration and exclusivity by identity-bound lease;
- clear active registrations on application close;
- remain independent from status, progress, metrics, cancellation,
  presentation, worker threads, concrete process objects, and outcomes.

Ordinary requests and compaction reserve the same session exclusivity key:

- a competing request still returns `already_running` when the admitted
  operation is another request;
- a request competing with compaction receives an explicit session-busy
  application error that FastAPI maps to HTTP 409;
- compaction competing with a request or existing compaction returns a
  user-facing busy result without starting provider work.

The managed-process registry stores the concrete runtime object used for
lookup, cancellation, and close. The operation service stores only active
identity and admission. The plugin or request coordinator owns status,
progress, cancellation, outcomes, and notifications.

A future connection-level operations menu may add a separate owner-description
contract with arbitrary optional fields such as `description`,
`operation_actions`, or provider-specific status. Those fields do not need to
be predefined or interpreted by the admission service; frontends may recognize
them optionally and ignore unknown fields.

Persistent outcomes remain a separate future event/history concern rather than
bounded terminal records in the active operation service.

Alternative if strict rejection is not approved: leave ordinary requests
admitted and rely on optimistic reconciliation to fail compaction visibly.
That is data-safe but can waste provider work.

Add `application/python/docs/development/operations.md` as the canonical
technical document. Keep it separate from `request-execution.md`: request
execution is one concrete operation producer, while operations cover
cross-producer active identity, lookup, exclusivity, owner responsibility, and
the future extensible operations-menu boundary.

#### Package structure and action ownership

Extract provider-native compaction into a shared package-local backend/helper,
tentatively `openai_responses_native_compaction.py`.

The shared backend should own:

- compaction configuration and auth selection;
- model and timeout selection;
- native-prefix resolution and request preparation;
- OpenAI compact transport parameters and response interpretation;
- compacted-output validation and sanitation;
- suffix preservation;
- safe progress callback hooks at meaningful local stages.

Define the actual SDK call behind a small package-local transport dependency:

- the synchronous provider-extension adapter uses the normal `OpenAI`
  transport;
- the application process supplies an `AsyncOpenAI` transport whose task can
  be cancelled;
- both transports return the same compacted-response mapping to the shared
  backend.

Both the application plugin and provider extension use this backend. The
application plugin supersedes the extension as the supported visible
background implementation. The extension remains a synchronous
alternative/historical adapter and a useful compatibility demonstration.

Add a companion application plugin and process implementation in the same
package, tentatively:

- `openai_responses_native_compaction_app.py`;
- `openai_responses_native_compaction_process.py`.

Register the application plugin in `agent_plugin.json` with kind
`"application"` and export it from the package.

Move the user-facing `compact_native_history` action and UI element from the
provider extension to the application plugin:

- action ID remains `compact_native_history`;
- action owner becomes `application`;
- the existing end-index dialog and visible behavior remain;
- `toggle_compaction_transcript_mode` stays a provider-extension action because
  it is a quick synchronous native-history projection change.

Rename the synchronous provider-extension compaction action to an explicitly
alternative ID such as `compact_native_history_sync`. It has no default UI
element and is not the supported user-facing action.

The application process may initially invoke this adapter through
`AgentCore.execute_session_action(...)`, but the important compaction work is
owned by the shared backend rather than the extension class.

Pass the application-owned cancellable transport through the core action
context. The extension adapter remains synchronous from AgentCore's
perspective, while its transport blocks on an async compact task owned by the
process. This preserves the existing core preparation/rebuild pipeline and
still gives the process a real task handle to cancel.

Calling through `AgentCore` remains useful because it already:

- resolves the active provider, extensions, features, and state;
- validates action inputs;
- obtains canonical native history;
- initializes the action request and compiled instructions;
- rebuilds visible messages from returned native history;
- reapplies feature/provider transforms;
- recomputes native-history integrity;
- returns an unpersisted session suitable for the process's guarded commit.

A direct backend call from the application plugin would otherwise duplicate
or expose these core preparation/rebuild steps. Do not add public split-phase
AgentCore APIs in Stage C merely to avoid the extension adapter. Reassess that
only when a second background native-history operation needs the same seam.

This avoids returning an accepted no-op result through the provider-extension
session-action path, which would save the session after the background worker
had already started and introduce a startup/commit race.

#### Application action behavior

The application action should:

1. require a live writable session rather than a selected snapshot;
2. verify that the session's effective tags include the native-compaction
   extension;
3. validate the optional visible `end_index` shape without calling the
   provider;
4. choose one ID shared by the operation registration and managed process;
5. reserve the minimal operation registration and session exclusivity key;
6. construct the process with narrow dependencies;
7. register and start it through `ManagedProcessRegistry`;
8. return promptly with:
   - standard action `status: "ok"`;
   - `operation_status: "accepted"`;
   - `operation_id`;
   - `notification_id`.

Use the operation service's session exclusivity key to prevent duplicate
compactions and competing ordinary requests. Put the unique operation ID in
notification follow-up actions so a stale Cancel button can never target a
later process.

Add an application action such as `cancel_native_compaction` with `session_id`
and `operation_id`. It verifies owner and session registration, looks up the
concrete process under the same ID, and calls `request_cancel(...)`.

#### Captured execution and safe commit

The process must not call `AgentApplication.execute_session_action(...)` for
the long-running operation because that method runs the provider transform and
commits immediately. Cancellation or application close could arrive after the
provider call but before that commit.

Instead:

1. create the initial notification;
2. capture under the session lock:
   - core;
   - base and effective config;
   - immutable session baseline;
   - file-state baseline;
   - the generic application context values needed by core action execution;
3. launch a daemon provider worker that calls
   `core.execute_session_action(...)` with the internal compaction action;
4. receive an unpersisted `(new_session, result)` from the core;
5. before persistence, acquire the process state lock and session lock;
6. re-check cancellation/close while holding the state lock;
7. commit with `app.save_session(..., reconcile=True)` against the captured
   session and file-state baseline;
8. discard the result if cancellation or close won before commit;
9. report a `SessionConflictError` as a visible compaction failure without
   overwriting current history.

Holding the process state lock through the final guarded save gives close and
cancellation a precise authority boundary:

- if cancellation/close sets invalidation first, no commit occurs;
- if commit has already acquired authority, it completes before close or
  cancellation returns;
- no result is applied after `close()` has returned.

The process should pass the same application/core context capabilities used by
ordinary session actions so feature initialization, system-message
compilation, attachment/native-history behavior, and auth selection remain
unchanged.

#### Worker and heartbeat model

`start()` should create the notification, capture the baseline, launch the
daemon supervisor/provider work, and return.

The supervisor waits for the blocking SDK operation with a production
heartbeat interval of approximately 15 seconds. Each timeout publishes a new
operation revision and notification projection with:

- safe phase text;
- elapsed whole seconds;
- operation state;
- whether cancellation remains available.

Suggested safe phases:

- `preparing`;
- `waiting_for_provider`;
- `committing`;
- `cancellation_requested`.

Do not include conversation content, credentials, raw native history, or full
provider payloads in notification fields.

Use injected monotonic/wall clocks and a configurable heartbeat interval in
tests. Provider calls are controlled by events/futures; tests must not wait 15
real seconds.

The current OpenAI `/responses/compact` endpoint returns one final
`CompactedResponse`. Its request schema does not expose semantic model-output
streaming or `background`, and it does not provide an operation ID that can be
polled. The OpenAI Responses cancel endpoint only accepts IDs for responses
created with `background: true`, which compact does not support.

Therefore OpenAI native compaction has no authoritative intermediary provider
status, token count, polling state, or server-side cancellation in the current
API. Its progress consists of:

- client-known preparation stages;
- an indeterminate `waiting_for_provider` phase;
- elapsed-time heartbeats;
- output validation and commit stages.

The SDK's `with_streaming_response.compact(...)` wrapper exposes raw HTTP
response handling, not model output events or incremental compact output, so
it does not improve semantic progress reporting.

Transport-level cancellation is nevertheless feasible. The existing OpenAI
Responses provider already tracks in-flight requests and closes active SDK
clients/streams from `cancel_request(...)`. Real-API tests cover the streaming
Responses path, while the non-streaming path currently has mocked coverage.

For compact, do not rely only on closing the synchronous SDK client or raw
response from another thread. A local delayed-HTTP reproduction with the
installed OpenAI/httpx stack found that cross-thread synchronous close did not
unblock a compact call promptly either before headers or while reading the
body.

Use the async OpenAI SDK for the application-owned compact transport:

- schedule `AsyncOpenAI.responses.compact(...)` as a task;
- retain its event loop/task handle in the concrete process/transport;
- `request_cancel(...)` marks commit invalid immediately and calls
  `task.cancel()` on the owning loop;
- await task termination and async-client cleanup;
- resolve the operation as cancelled and release the session operation lease;
- preserve the guarded commit check so even an unexpected late result cannot
  apply.

The same local reproduction showed async task cancellation interrupting both
the pre-header wait and response-body wait promptly and resetting the HTTP
connection.

Represent the result as transport cancellation, not as a successful call to
OpenAI's explicit background-response cancel endpoint. Add a gated hosted
compact cancellation test to verify real-endpoint latency and cleanup when
credentials are available.

Design the shared operation progress API for richer producers:

- `set_phase(...)`;
- `heartbeat(...)`;
- `report_progress(completed, unit, total=None)`;
- `report_metric(name, value, unit=None)`;
- terminal success/failure/cancellation.

Claude, Kimi, and Gemini-style compaction currently call
`core.send_request_stream(...)` but discard partial events and only collect the
final message. Later migrations can consume partial events and report real
output chunks, characters, or provider-reported token metrics. Exact token
progress should only be shown when the provider stream supplies an
authoritative monotonic token count; otherwise use chunk/character progress
and final usage.

There is no implemented Qwen compaction under `plugins/qwen-tools` yet; it is
tracked separately. Its future implementation should use the same operation
progress callbacks rather than adding a Qwen-specific status channel.

#### Notification contract

Create one persistent session notification per operation:

- `kind: "notification"`;
- stable notification key derived from the operation ID;
- `status: "pending"` while active;
- `severity: "warning"`;
- `presentation: "banner"`;
- `dismissible: false` while running;
- `retention: until_resolved`;
- one `Cancel compaction` `run_action` follow-up carrying session and
  operation IDs.

`display.dismissible: false` is already part of the action-display contract and
is honored by the shared React Native notification banner. No notification
schema or frontend behavior change is needed to hide the dismiss control while
the operation is running.

The visible title/body should be sufficient for current frontends:

```text
Compacting native history
Waiting for OpenAI native compaction. Elapsed: 45 seconds.
```

Add an optional structured `operation` object while keeping
`kind: "notification"`:

```json
{
  "version": 1,
  "type": "openai_responses_native_compaction",
  "id": "<operation-id>",
  "state": "running",
  "phase": "waiting_for_provider",
  "started_at": "<RFC3339>",
  "elapsed_seconds": 45,
  "cancellable": true
}
```

Add the corresponding optional type to the frontend SDK notification contract.
Current frontends continue rendering title, body, variant, and actions; no
compaction-specific component is required.

All process notification mutations are serialized under a process-owned lock
and use `expected_revision`. On revision conflict:

- accept the authoritative current revision;
- retry only when the record is still pending and belongs to the same
  operation;
- notification failure must not alter commit/cancellation correctness.

Terminal behavior:

- success:
  retain a pending dismissible success banner, release active registration,
  then remove the process;
- provider, malformed-output, or reconciliation failure:
  retain a pending persistent error notification with dismissibility, concise
  retry guidance, and a Retry action carrying the original `end_index`;
- user cancellation:
  retain a pending dismissible warning banner after the provider call returns
  and its result is discarded;
- application replacement or shutdown:
  `close()` marks the notification interrupted, revokes commit authority, and
  returns promptly; any late provider result is discarded.

Do not add a generic notification cancel method to the managed registry.

#### Existing native behavior and compatibility

Keep unchanged:

- effective ChatGPT/API auth selection;
- compaction-model selection;
- timeout validation;
- request initialization and compiled instructions;
- native input sanitation;
- system/developer-message restoration;
- prefix compaction and suffix preservation;
- compacted-output sanitation;
- placeholder versus expanded transcript projection;
- native integrity rebuild.

Migrate existing synchronous unit tests to the internal action ID so they
continue proving the provider-native transform in isolation.

Add compatibility coverage proving the visible UI action now resolves to the
application plugin and returns accepted rather than blocking.

#### Automated verification

Process unit tests:

- action returns before a controlled provider call is released;
- operation admission, immutable snapshots, list-by-session, and bounded
  terminal retention;
- request-versus-compaction and compaction-versus-request atomic races;
- initial notification and repeated heartbeat revisions;
- elapsed-time and safe-phase updates;
- backend stage callbacks without OpenAI intermediary events;
- successful guarded commit and process removal;
- provider exception and malformed/empty output;
- async transport cancellation before response headers and while reading the
  response body;
- user cancellation before provider completion;
- close/replacement before provider completion;
- cancellation and close immediately before commit;
- stale notification revision handling;
- late provider results never commit;
- conflict after concurrent history change preserves current history;
- stale Cancel occurrence cannot target a later process.

Application/action integration:

- session UI exposes the application-owned compaction action only when the
  extension tag is active;
- HTTP action execution returns accepted promptly;
- notification events are observable through the ordinary event API;
- cancel follow-up routes through `action_owner: "application"`;
- readonly snapshot selection fails before provider work;
- strict admission, if approved, rejects ordinary sends and duplicate
  compaction while the process owns the session gate;
- live operation listing exposes both ordinary requests and compaction through
  one minimal active registration shape;
- application-owner replacement marks interruption and prevents late commit.

Provider compatibility:

- all existing native-compaction transform tests pass under the internal
  action ID;
- targeted OpenAI Responses package tests pass;
- the existing provider cancellation tests remain green;
- a local delayed-HTTP compact transport test proves task cancellation closes
  the exchange promptly;
- a gated hosted compact cancellation test verifies the real endpoint when
  credentials are available;
- the existing independently reproducible unrelated provider-suite failures
  remain reported separately if still present.

Frontend contract:

- frontend SDK accepts and merges operation-bearing notification revisions;
- shared RN notification components render revised bodies and Cancel/Retry
  actions without compaction-specific code;
- focused mobile and desktop component tests cover at least two progress
  revisions and the cancellation follow-up payload.

#### Documentation

Update:

- add `application/python/docs/development/operations.md` covering operation
  identity, owner, session association, admission, exclusivity, lookup,
  identity-safe release, managed-process relation, plugin-owned status, and the
  future extensible operations-menu boundary;
- link the operations document from
  `application/python/docs/development/request-execution.md` and the
  application README development section;
- `plugins/openai_responses/README.md` with asynchronous action behavior,
  heartbeat-only OpenAI provider progress, local cancellation semantics,
  interruption, errors, and conflict safety;
- `plugins/docs/notifications-and-action-displays.md` with the concrete
  heartbeat/revision example;
- `plugins/docs/managed-background-processes.md` with a link to the first
  production implementation;
- plugin action docs for the application-owned Cancel/Retry follow-ups;
- plugin authoring docs distinguishing minimal active operation registration
  from plugin-owned status, managed-process lifetime, and notification
  presentation.

Checkpoint C:

- from mobile, starting compaction returns promptly;
- the Chat screen shows repeated progress revisions and increasing elapsed
  time;
- Cancel prevents the result from being applied;
- success updates the session;
- provider and concurrent-history failures remain visible.

### Stage C follow-up — Notification-driven UI effects

Stage C follow-up plan status: Approved on August 4, 2026.

#### Outcome

A session or application notification revision may request the same
connection-scoped refresh behavior as a successful application-action
response. Native compaction will use a session reload only on successful
completion so the active chat reloads the compacted session without a manual
refresh.

#### Proposed contract

Add an optional `ui_effects` mapping to both session- and
application-notification contracts:

```json
{
  "ui_effects": {
    "reload_session_ids": ["session-1"],
    "reload_sessions_list": true,
    "reload_application_actions": true
  }
}
```

Define a shared refresh-effect type used by action responses and notifications:

- `reload_session_ids`;
- `reload_sessions_list`;
- `reload_application_actions`.

All three are scoped to the connection that receives the result or
notification. `reload_session_ids` invalidates listed session data and
refreshes mounted/open consumers, but it never opens or navigates to a session.

`navigate_to_session_id` remains action-only. Action execution has a direct
user gesture and navigation context; an asynchronously arriving notification
must not move focus. A notification follow-up may still invoke an action whose
response navigates after the user explicitly selects it.

Action `mutations` also remain action-only. Mutation-derived policies such as
automatic navigation to a created session or automatic session-list reload are
not inferred for notifications. Notification effects must be explicit.

The notification store already preserves additional JSON-compatible fields.
Add explicit validation and frontend typing for the three shared refresh
fields without making the server interpret or execute them. Preserve unknown
fields so frontends can add optional capabilities later.

#### Shared frontend behavior

Extract refresh-effect parsing and connection-scoped routing from the private
action runner into shared frontend SDK infrastructure so action responses,
session notifications, and application notifications use the same semantics.

Extend session-notification and application-notification consumers to report
effects once for each newly observed notification revision. Deduplicate by
connection, notification scope, notification ID, and revision so:

- heartbeat rerenders do not repeat an effect;
- refreshing a summary containing the same revision does not loop;
- a newer revision can deliberately request another effect;
- reconnecting or remounting may apply the latest persisted effect once,
  ensuring a stale client catches up.

Effect execution is best effort. A reload failure must not change notification
status, retry the compaction, or affect operation correctness.

#### Frontend integration

Mobile and desktop connection-level layers should route refresh effects through
generic connection-scoped invalidation channels:

- `reload_session_ids` invalidates listed session caches and refreshes matching
  mounted Chat consumers;
- `reload_sessions_list` refreshes the connection's session collection;
- `reload_application_actions` invalidates application action definitions and
  related application UI schema.

Mobile Chat should translate a matching session invalidation into its existing
message/session-context reload path.

Desktop Chat should translate it into the existing `handleReload()` path and
the desktop connection layer should publish the existing sessions-list and
application-action invalidations when requested.

The implementation should remain generic: neither frontend should contain
OpenAI-compaction-specific branching.

#### Compaction producer behavior

The compaction process should:

- omit `ui_effects` from preparing, waiting, committing, cancellation, and
  failure revisions;
- add `ui_effects.reload_session_ids: [session_id]` only to the successful
  completion revision;
- keep the success banner pending and dismissible after requesting the reload.

#### Verification

- frontend SDK unit tests cover parsing, ignored unknown fields, and
  revision-based deduplication;
- action-response tests prove the shared refresh parser preserves existing
  behavior, including making the currently declared
  `reload_application_actions` field operative;
- session- and application-notification tests prove one effect delivery per
  revision and strict connection scoping;
- mobile component coverage proves a successful notification reloads the
  current transcript without OpenAI-specific logic;
- connection-level mobile and desktop tests cover session-list and application
  action invalidation from application notifications;
- desktop component coverage proves session invalidation reaches
  `handleReload()`;
- plugin tests prove only the success revision carries the reload request;
- failure, cancellation, and heartbeat revisions never trigger a reload;
- existing action-response UI-effect tests remain green after extracting the
  shared parser.

#### Approval decision

Approve or revise this boundary:

- share the three refresh/invalidation fields between actions and both
  notification scopes;
- keep navigation and mutation-derived policies action-only;
- preserve unknown notification fields without executing them.

### Stage D — Selectable no-message continuation

Add a compaction action option for:

- compact only;
- compact and continue.

After successful compaction, the continue path should invoke the shared
request-start orchestration from Stage A against the freshly committed
session. It must not append a synthetic message and must produce the same
events, active-request state, cancellation behavior, tool loop, persistence,
and frontend updates as an ordinary send.

Resolve the effective configuration at continuation time. If request admission
fails after compaction succeeded, retain the successful compacted session and
update the notification with an explanation and manual Continue action.

Checkpoint D:

- mobile manual verification confirms both selectable modes;
- compact-only does not start a request;
- compact-and-continue starts exactly one visible normal request;
- session history contains no synthetic continuation message;
- cancellation and reconnect behave like an ordinary request.

### Stage E — Completion and integration hardening

Complete cross-boundary coverage and documentation after the product behavior
passes the prior checkpoints.

Cover:

- application reload and shutdown during preparation, provider wait, commit,
  and continuation;
- server restart treatment of an abandoned in-progress notification;
- duplicate compaction starts;
- notification revision races with cancellation;
- provider timeout and malformed output;
- session deletion and readonly snapshot behavior;
- automatic continuation admission failure;
- HTTP, application-layer, SDK, and frontend integration boundaries;
- a gated hosted OpenAI native compaction test where credentials are
  available.

Reassess whether notification history needs a distinct operation kind. Keep
ordinary notification semantics unless the completed behavior demonstrates a
real lifecycle or query distinction.

Checkpoint E:

- desktop and mobile visual/device smoke tests pass;
- all required automated suites pass;
- notification Stage E history planning can proceed with an established
  background-operation record shape.

### Stage F — Provider-extension background-action alternative

Treat this as a later follow-up within the same task after the application
plugin implementation is stable.

Investigate and, if justified, add a provider-extension authoring path that can
start the same background compaction safely while sharing:

- the OpenAI native compaction backend;
- application operation records;
- managed-process lifecycle;
- notification projection;
- cancellation semantics;
- compact-and-continue or manual resend follow-ups.

Do not start a background process directly inside the current synchronous
provider-extension action and return unchanged native history. The application
still saves the outer action result after the extension returns, creating a
race with the background process.

Preferred framework direction:

- allow a session action result to request a deferred application action or
  operation launch that runs only after the synchronous session-action save
  succeeds;
- optionally provide a failure-contained operation reporter in extension and
  feature action context for synchronous phases and richer streaming backends;
- let status records carry serializable follow-up action descriptors, including
  the Stage D no-message continuation action;
- document the application-plugin implementation and extension implementation
  side by side in provider-extension and application-plugin authoring docs.

The extension alternative should remain a demonstration of capabilities, not a
second compaction backend or separate operation model.

### Implementation decisions and open questions

- Recommended: shared request orchestration is an application-layer service or
  coordinator rather than new FastAPI helpers.
- Recommended: the background process registry is stored in `RuntimeStore`;
  no new `AgentApplication` registry/lookup methods are necessary.
- Recommended: the process receives narrow callbacks for notifications,
  session operations, and request continuation rather than using a registry
  that understands those domains.
- Recommended: a RuntimeStore-backed application operation service owns only
  active identity, lookup, and admission; managed processes and plugins own
  runtime behavior and status; notifications own presentation.
- Confirmed: OpenAI native compaction has no semantic output stream,
  background operation ID, or explicit server-side cancel API in the current
  compact endpoint. The async SDK request can still be cancelled at the HTTP
  transport level; guarded commit and late-result discard remain required.
- Recommended: new sends are rejected while compaction owns session
  admission.
- Recommended: application replacement closes and invalidates compaction
  rather than waiting indefinitely.
- Recommended: automatic continuation resolves current effective config and
  preserves successful compaction if request startup fails.
- Stage A approval decision: construct one request coordinator per
  `AgentApplication` and expose thin application methods for background start,
  atomic append-and-start, synchronous run, and active-request lookup.
- Stage A approval decision: extend application lifecycle control so the
  coordinator can acquire and retain the exact application generation for a
  request worker without depending on FastAPI middleware state.
- Stage A approval decision: keep HTTP idempotency in FastAPI while moving
  single-flight admission, request preparation, worker execution, and event
  publication into the application layer.
- Stage C proposed decision: the companion application plugin owns the visible
  background action; the provider extension remains a synchronous
  alternative/historical adapter over the same backend.
- Stage C proposed decision: use `AgentCore.execute_session_action(...)` for
  the in-memory adapter path because it preserves provider/feature
  initialization and native-history rebuild; do not add split-phase core APIs
  yet.
- Stage C decision: active operation registrations contain only operation ID,
  owner ID, and optional session ID. Terminal retention and status are outside
  the service.
- Future operations-menu decision: owner descriptions may add arbitrary
  optional fields such as `description` or `operation_actions`; the admission
  service and frontends need not predefine or interpret every field.
- Open: whether Stage F should add deferred application actions, an
  extension-facing operation reporter, or both.

### Documentation

- Add a standalone plugin-authoring guide for managed background processes or
  operations, linked from `plugins/docs/actions.md`,
  `plugins/docs/application-plugins.md`, and
  `plugins/docs/provider-extensions.md`.
- Update `plugins/docs/notifications-and-action-displays.md` with a
  progress-heartbeat and cancellation example.
- Update the OpenAI Responses package README with background compaction,
  cancellation, failure, and continuation behavior.
- Document the shared request-start ownership in application development/API
  documentation so HTTP and non-HTTP entrypoints do not reintroduce adapter
  business logic.
- Update notification specifications only for public record or presentation
  changes demonstrated by the implementation.
- Add the application operation technical guide under
  `application/python/docs/development/` and explicitly cover future
  connection-level operation lists, durable outcomes, retry/resend action
  descriptors, and the boundary between operation state, managed processes,
  events, and notifications.
- After Stage F, document both the application-plugin and provider-extension
  background-action patterns and explain when each is appropriate.

### Task checklist

- [ ] Resolve the open requirement questions and approve the execution plan.
- [x] Approve the detailed Stage A plan.
- [x] Implement and verify Stage A.
- [x] Write and verify the approved Stage A request-execution development guide.
- [ ] Complete manual checkpoint A.
- [x] Approve the detailed Stage B plan.
- [x] Implement and verify Stage B.
- [x] Complete checkpoint B.
- [x] Approve the detailed Stage C plan and shared session-operation admission.
- [x] Implement and verify Stage C.
- [ ] Complete mobile manual checkpoint C.
- [ ] Implement and verify Stage D.
- [ ] Complete mobile manual checkpoint D.
- [ ] Implement and verify Stage E.
- [ ] Complete desktop/mobile checkpoint E.
- [ ] Decide and, if approved, implement Stage F extension alternative.
- [ ] Complete documentation and requirement evidence.
- [ ] Record completion notes.

### Requirement verification

- Background action responsiveness:
  a real HTTP/application action returns accepted before a controlled
  compaction provider call is released.
- Persistent progress and cancellation:
  real backend plus SDK/frontend integration observes one notification receive
  multiple revisions, supports cancellation, and rehydrates correctly.
- Successful and failed compaction:
  provider integration and session-store assertions prove correct native
  history commit, visible success, visible failure, and conflict safety.
- Selectable continuation:
  public send/event/session tests prove compact-only versus
  compact-and-continue, exactly one request, and no appended continuation
  message.
- Shared request orchestration:
  HTTP and non-HTTP consumers exercise the same application-layer coordinator,
  with parity tests for send, send-message, cancellation, events, and
  duplicate admission.
- Lifecycle safety:
  application-owner replacement and shutdown tests prove registered work is
  closed and late results cannot mutate the old generation.
- Reusable process support:
  a dummy plugin proves registration, lookup, communication, completion,
  removal, and close without importing OpenAI or notification-specific code.
- Compatibility:
  existing server, terminal, OpenAI Responses, frontend SDK, mobile, and
  desktop relevant suites remain green.

### Additional implementation verification

- deterministic heartbeat tests use a fake clock or short injected interval;
- startup failure leaves no registered process;
- one process close failure does not prevent other process cleanup;
- stale notification revisions are handled without losing a user cancellation;
- readonly session snapshots reject compaction before provider work starts;
- provider timeout, malformed output, and empty output preserve the original
  session;
- hosted API verification is gated and reported as not run when credentials
  are unavailable rather than counted as passing.

## Implementation Notes

### Stage A — Shared request-start orchestration

Implemented on August 2, 2026.

Outcome:

- added one `SessionRequestCoordinator` per `AgentApplication`;
- added application methods for background existing-history start, atomic
  append-and-start, synchronous coordinated execution, and active-request
  lookup;
- moved request ID allocation, session single-flight admission, request worker
  execution, event publication, checkpoint filtering, and cleanup out of
  FastAPI;
- extended `ApplicationControl` with application-generation operation
  acquisition so HTTP, terminal, plugins, and future compaction continuation
  retain the correct generation;
- changed FastAPI send routes to retain only validation, HTTP idempotency,
  response mapping, and serialization;
- changed terminal ordinary sends to use the same coordinator, including
  atomic append-and-start;
- retained the low-level `AgentApplication.send_request(...)` generator and
  existing cancellation contract;
- updated request ownership and event documentation.
- added the canonical package-local request lifecycle guide at
  `application/python/docs/development/request-execution.md`, with ownership,
  APIs, admission, execution, events, persistence, cancellation, reload,
  adapter boundaries, invariants, sources, and tests;
- kept the guide as one file because the material describes one sequential
  implementation lifecycle for one maintainer audience; package-local
  application development docs remain outside the public MkDocs navigation.

Automated evidence:

- `pytest core/python/tests -q`: 430 passed, 26 deselected, 1 xfailed;
- `pytest application/python/tests -q`: 319 passed, 90 deselected;
- focused coordinator/reload/server/terminal run: 93 passed, 13 deselected;
- `npm --workspace @crystal-lattice/frontend-sdk test`: 40 files and 284 tests
  passed;
- mobile Jest: 26 suites and 110 tests passed;
- focused desktop Jest send/application smoke: 3 suites and 8 tests passed;
- MkDocs build through `docs_site/mkdocs.yml` passed with existing warnings;
- docs-site preparation followed by MkDocs build passed, and all
  package-local relative documentation targets were inspected successfully;
- Black and focused Ruff checks passed;
- `git diff --check` passed.

Additional verification findings:

- `pyright` is not installed in the current environment, so type checking was
  not run.
- The full desktop Jest suite passed all 19 suites and 104 assertions but
  exited nonzero because `DependencyFlatList.test.tsx` accessed the Jest
  environment from a React Native timer after teardown. The focused Stage A
  desktop suites exit successfully.
- OpenAI Responses, OpenRouter, and reference OpenAI-compatible provider
  default suites have independently reproducible failures in unchanged
  provider-specific tests:
  - OpenAI Responses attachment upload fixture/history expectations;
  - OpenRouter metadata and web-search default expectations;
  - reference provider tests patch module-level `requests.post` while the
    provider uses `requests.Session.post`.
  No provider package files changed in Stage A.

Manual checkpoint A remains open. Verify an ordinary send and cancellation
from mobile and desktop against the same server, then confirm that duplicate
sends are rejected without appending a second message.

### Stage B — Shared managed background-process lifecycle

Implemented on August 3, 2026.

Outcome:

- added `agent_app.managed_processes` as a shared library in the `agent-core`
  distribution;
- added a minimal `ManagedProcess` protocol with bounded synchronous
  `start()` and `close()` methods;
- added a `ManagedProcessRegistry` with unique-ID admission, lookup,
  identity-safe removal, startup cleanup, best-effort close, and idempotent
  shutdown;
- added `get_managed_process_registry(...)`, which stores one registry under a
  stable `RuntimeStore` key without adding another `AgentApplication` method;
- made close/start, duplicate-start, fast-completion, stale-removal, startup
  failure, and individual close-failure behavior explicit and thread-safe;
- kept notifications, progress, cancellation, communication, worker
  implementation, and late-result protection owned by the concrete process;
- retained existing MCP and durable shell process registries unchanged;
- added a test-only application plugin proving start, later lookup,
  process-specific communication, and close on application replacement;
- added the generic plugin-authoring guide
  `plugins/docs/managed-background-processes.md` and linked it from action,
  application-plugin, provider-extension, plugin-index, and public docs-site
  navigation.

Automated evidence:

- `pytest core/python/tests -q`: 442 passed, 26 deselected, 1 xfailed;
- `pytest application/python/tests -q`: 318 passed, 90 deselected;
- `pytest plugins/mcp-runtime-app/tests/test_application_owner_reload.py -q`:
  1 passed;
- `pytest plugins/tool-compat-shared/tests/test_background_processes.py -q`:
  4 passed;
- docs-site preparation and MkDocs build passed with existing warnings;
- focused Ruff and Black checks passed;
- `git diff --check` passed.

Checkpoint B is complete through automated public-boundary coverage. Stage C
can now build the first production process object without extending the
registry contract.

### Stage C — Background native compaction and application operations

Implemented on August 3, 2026.

Outcome:

- added `ApplicationOperationService` as a RuntimeStore-owned application
  service for atomic exclusivity and minimal active registration containing
  only operation ID, owner ID, and optional session ID;
- added global, owner, and per-session active lookup plus identity-safe
  release, without storing status, progress, cancellation, presentation, or
  outcomes;
- integrated ordinary coordinated requests with the operation service while
  preserving request IDs and existing request-versus-request behavior;
- added HTTP 409 `session_busy` mapping when a non-request operation owns the
  session;
- extracted a shared OpenAI native compaction backend and sync/async transport
  seam;
- retained `compact_native_history_sync` as the provider-extension
  compatibility adapter without a default UI action;
- added an application-owned `compact_native_history` action that returns
  a standard successful action result promptly and starts a managed process;
- added approximately 15-second revisioned notification heartbeats with
  elapsed time, nondismissible warning-banner presentation, and
  `Cancel compaction`;
- implemented async compact transport cancellation that interrupts delayed
  HTTP exchange before headers or during response-body reading;
- added guarded optimistic commit, conflict-safe failure, retry
  notifications, cancellation result discard, and reload/shutdown
  interruption;
- added optional frontend notification operation typing and progress-revision
  merge coverage;
- added the application operation development guide and updated application,
  plugin-authoring, notification, managed-process, and OpenAI package docs.
- documented that a future operations-menu owner-description contract may add
  arbitrary optional fields such as `description`, `operation_actions`, or
  provider details without expanding admission-service semantics.

Automated evidence:

- `pytest core/python/tests -q`: 447 passed, 26 deselected, 1 xfailed;
- `pytest application/python/tests -q`: 319 passed, 90 deselected;
- focused Stage C application/transport/extension tests: 27 passed;
- focused operation/request-admission tests: 8 passed;
- `pytest plugins/openai_responses/tests -q`: 394 passed, 76 deselected, with
  the same 3 independently reproducible attachment-history failures recorded
  before Stage C;
- `npm --workspace @crystal-lattice/frontend-sdk test`: 40 files and 285 tests
  passed;
- docs-site preparation and MkDocs build passed with existing warnings;
- focused Ruff and Black checks passed;
- `git diff --check` passed.

Additional verification findings:

- the hosted OpenAI compact cancellation test was not run because it requires
  credentials and incurs provider work;
- no OpenAI compact endpoint provides semantic intermediary output, so current
  progress is phase plus elapsed time;
- manual mobile checkpoint C remains open;
- Stage D selectable no-message continuation remains unimplemented.

Post-implementation corrections from manual testing on August 4, 2026:

- changed background start and cancellation actions to return standard action
  `status: "ok"` results with a separate `operation_status`, preventing
  accepted work from being reported as an immediate action failure;
- changed preparing, provider wait, commit, and cancellation-in-progress
  notifications to nondismissible warning banners;
- retained completion as a dismissible success banner and failures as
  dismissible error banners so terminal outcomes remain visible;
- changed the desktop Chat composer from the legacy append-then-send sequence
  to the atomic shared `sendMessage()` path, so admission rejects a competing
  send before its user message is persisted;
- added a regression test proving a rejected atomic send neither appends
  history nor invalidates the active compaction;
- recorded notification-driven reload integration as a separate Draft Stage C
  follow-up plan; no notification UI-effect execution was implemented without
  approval.

Correction verification:

- focused compaction application/transport/extension tests: 27 passed;
- focused HTTP send-message tests: 4 passed, 57 deselected;
- request-coordinator tests: 3 passed;
- targeted desktop atomic-send and notification-rail Jest: 2 suites and 4
  tests passed;
- full desktop Jest collected 20 suites and 105 passing assertions but exited
  nonzero because the existing `DependencyFlatList` test left a timer that
  accessed Jest after environment teardown; this run is not counted as
  successful;
- targeted desktop ChatPane ESLint: 0 errors and 4 existing warnings;
- frontend SDK: 40 files and 285 tests passed.
- full OpenAI Responses package: 395 passed and 76 deselected, with the same 3
  independently reproducible attachment-history failures recorded before this
  correction.
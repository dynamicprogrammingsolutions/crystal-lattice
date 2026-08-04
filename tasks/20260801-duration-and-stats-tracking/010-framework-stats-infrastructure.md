Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

# Framework Stats Infrastructure

Define the framework-level storage directory scopes, the session stats metadata key, and the lifecycle action hooks that plugins need to capture tool-call duration without implementing timing in `tool_loop.py` or `AgentCore`.

## Requirements checklist

- [ ] Three configurable storage directory paths exist: session-level, project-level, and user-level.
- [ ] The project-level directory defaults to a location within the project directory; the user can override via config.
- [ ] The user-level directory defaults to a location within the user home; the user can override via config.
- [ ] The session-level directory is defined and configurable.
- [ ] A configurable session metadata key exists for storing session-level summary stats (default `stats`).
- [ ] Plugins can resolve the active storage directory for each scope at runtime via a framework-provided mechanism.
- [ ] The framework provides lifecycle action hooks sufficient for a plugin to capture per-tool-call duration without framework timing logic in `tool_loop.py` or `AgentCore` tool execution code.
- [ ] Application plugins handling tool-call lifecycle triggers retain the normal application-action capability to load, transform, rebuild, and save the complete active session.
- [ ] Feature plugins can handle tool-call lifecycle triggers through the existing core session-action contract and transform the complete native/core session history.
- [ ] Tool-call duration can be implemented as either an application plugin or a feature plugin without changing the framework hooks.
- [ ] Config keys for all storage paths and the session metadata key are discoverable via the config schema.
- [ ] The framework does not capture, compute, or store tool-call timing itself; it only provides hook points.

## Supporting details

### Current state

- `AgentApplication.__init__` sets `self._runtime_state_root = session_root_path.parent / "runtime"` and stores server settings at `runtime/server_settings.json`.
- `FilesystemSessionAssetStore` uses `session_root_path.parent / "session_assets"` for per-session attachments.
- The runtime env contract exposes `CONFIG_DIR`, `WORKING_DIR`, `BUILTIN_PLUGINS` to plugins via `os.environ` (see `plugins/docs/application-plugins.md` "Runtime env contract").
- Standard built-in lifecycle triggers are listed in `plugins/docs/actions.md`: `session_create`, `session_save_prepare`, `request_prepare`, `request_complete`, `request_error`, `session_fork`, `agent_switch_prepare`, `agent_switch_complete`, `session_settings_changed`, `server_settings_changed`, `session_delete_prepare`, plus core-owned `response_finalize` and the special `session_list`.
- The tool loop (`core/python/agent_app/tool_loop.py::_apply_tool_calls`) executes each tool call via `core.iter_tool_messages` and emits `tool_calls`, `tool_partial`, and `tool_results` events. No lifecycle trigger fires per tool call.

### Constraints

- The framework must not choose concrete file names within the storage directories; that is plugin-owned.
- The framework must not capture timing itself; it only provides hook points that plugins use.
- New lifecycle triggers must follow the existing dynamic-lifecycle pattern (plugins declare `trigger` in action definitions; `AgentApplication` dispatches).
- Tool-call lifecycle actions must retain the established application-action and core session-action mutation contracts; the framework must not introduce duration-specific result fields.
- A synchronous application-plugin save performed from a tool-call lifecycle belongs to the active request and must not be mistaken for a competing tool loop.
- Storage path resolution must work with the existing `${env:...}` config placeholder mechanism.

## Execution plan

Status: Draft

This subtask will add application-owned stats configuration and general
full-session tool-call lifecycle stages. It will not capture timing, define any
stats value schema, or implement the duration plugin from subtask 020.

### Storage configuration and runtime access

1. Normalize a top-level `stats` configuration section during
   `AgentApplication` initialization, before application plugins receive their
   resolved `app_config`:
   - `stats.session_dir`: default
     `<session_root.parent>/stats/sessions`.
   - `stats.project_dir`: default
     `${env:WORKING_DIR}/.crystal/stats/project`.
   - `stats.user_dir`: default `~/.crystal/stats`.
   - `stats.session_metadata_key`: default `stats`.
2. Resolve `~` and relative configured paths once at startup. Relative paths
   are anchored to the resolved `WORKING_DIR`; all public accessors return
   absolute `Path` values.
3. Add side-effect-free accessors on `AgentApplication`:
   - `get_stats_dir(scope)` for `session`, `project`, and `user`.
   - `get_session_stats_dir(session_id)` for the validated per-session child
     of the session root.
   - `get_session_stats_metadata_key()`.
4. Reuse the path-component validation rule from the session asset store so a
   session id cannot escape the configured session stats root.
5. Do not create project or user directories merely by constructing or
   inspecting the application. A plugin creates its owned subdirectory when it
   first writes an artifact.
6. Do not add process-global `STATS_*` environment variables. Existing
   `${env:...}` placeholder resolution remains supported for configured path
   values, while plugins resolve the effective directories through the
   application accessors already available in action/tool contexts.

### Tool-call lifecycle dispatch

1. Add a typed full-session lifecycle callback to `ToolLoopRunner`, supplied
   by `AgentApplication` when constructing the runner.
2. Invoke `tool_call_prepare` immediately before each
   `core.iter_tool_messages([call], ...)` execution. The current session is
   checkpointed first so application plugins that load it see the exact
   in-flight assistant/tool-call history.
3. Append the raw final or synthesized tool-result message through
   `core.add_message`, checkpoint it, and then invoke `tool_call_complete`
   before the streaming end event, aggregate `tool_results` event, or next
   tool call.
4. Both triggers receive `session_id`, `request_id`, raw `tool_call`,
   `tool_call_id`, `tool_name`, and call index. The complete trigger also
   receives the raw execution result, matching tool-message index/id when
   available, and structured error/cancellation information.
5. Each trigger runs the established session lifecycle chain in its existing
   order:
   - matching application-plugin actions through `AgentApplication`;
   - matching provider-extension and feature actions through
     `AgentCore.execute_lifecycle_actions`.
6. The transformed/persisted session returned by the lifecycle becomes the
   runner's authoritative `current_session`. Re-resolve effective config and
   plugin runtime as existing phase refresh rules require before continuing.
7. The tool-call descriptor selected for the current execution remains fixed.
   A lifecycle may rewrite any session message or metadata, but changing,
   cancelling, or replacing the already selected tool invocation is outside
   these triggers.
8. A complete hook runs once for each call that reaches a final or synthesized
   tool result, including normal tool failures. Cancellation before a final
   result still dispatches completion for cleanup, without inventing a tool
   message.
9. The framework passes no timestamps, clocks, elapsed values, or duration
   fields. Duration generation and aggregation remain plugin-owned.

### Established application-plugin mutation semantics

1. Do not add a tool-result-specific return shape. Application actions keep
   the existing broad lifecycle result support (`session`,
   `session_metadata`, and opaque result fields) and may also use their normal
   imperative pattern:
   - acquire the session lock;
   - load the latest persisted session and effective core/config;
   - use `AgentCore` helpers such as `slice_session`, `add_message`,
     `modify_message`, or `rebuild_native_history`;
   - construct any immutable replacement `Session`;
   - save it through `app.save_session`.
2. Make the shared per-session lock reentrant. The framework holds it around a
   tool-call lifecycle stage, while an application plugin may nest its existing
   `app.acquire_session_lock(session_id)` block on the same thread without
   deadlocking.
3. Before each application action, persist the current in-loop session. Execute
   the action inside an internal same-thread save-observation scope. Each
   successful `AgentApplication.save_session` records its returned session and
   file state in that scope; saves from other threads are not recorded.
4. After the action returns, verify that the active file still matches the
   latest observed save, reload it while still holding the lock, and adopt that
   synchronous save. If no matching save was observed, retain the current
   in-flight session.
5. Apply any standard returned `session`/`session_metadata` transformation
   after adopting the action's saved session, persist the resulting session,
   and pass it to the next matching action. This preserves declaration-order
   composition for plugins that save imperatively, return transformations, or
   do both.
6. A save to the active session performed synchronously inside this locked
   lifecycle stage belongs to the active tool loop. Update the request's
   checkpoint session and file-state baseline to that saved revision instead
   of reporting it as a concurrent modification.
7. Saves from another thread/process, detached work that outlives the action,
   and raw filesystem writes that bypass `AgentApplication.save_session`
   remain external changes. Existing request reconciliation detects
   incompatible message/protected-metadata changes and retains the conflict
   backup behavior.
8. Do not hold the session lock while the tool itself executes. A genuinely
   concurrent tool loop may run, but only one loop can commit a lifecycle or
   checkpoint stage at a time; the losing stale loop is still rejected during
   reconciliation.

### Established core feature transformation semantics

1. Dispatch the same triggers through
   `AgentCore.execute_lifecycle_actions`, rather than creating a second
   feature hook protocol.
2. Feature actions keep the existing session-action inputs:
   `session`, full `native_messages`, params, enriched context, and shared
   provider state.
3. Feature actions keep the existing result contract: return the complete
   replacement `native_messages` plus optional `session_metadata`. Core rebuilds
   the complete immutable core message history and native-integrity metadata.
   This already permits arbitrary message additions, removals, replacements,
   reordering, and metadata transformations.
4. The application persists the transformed session before the next matching
   action or tool-loop step and updates the active request baseline.
5. Because the existing core lifecycle dispatcher includes both feature and
   provider-extension session actions, provider extensions declaring these
   triggers also retain the same native-history transformation contract.
6. A feature that needs transient state across prepare/complete actions may use
   the existing application `runtime_store` from the enriched context, keyed
   by session/request/tool-call identity. No duration-specific framework state
   is added.

### Authoritative session and event projection

1. After `tool_call_complete`, resume the tool loop from the lifecycle's final
   persisted session, even when a plugin rewrote the entire history.
2. Locate the current call's transformed tool message by `tool_call_id` in the
   authoritative session and use that message for the streaming end payload
   and aggregate `tool_results` event. This makes message metadata added by
   either application or feature plugins immediately visible to frontends.
3. If a plugin intentionally removes the matching tool message, preserve the
   original execution result in the execution event while the subsequent
   session checkpoint remains authoritative for stored history. Continuing
   from a history with an unresolved/removed tool result is the transforming
   plugin's responsibility.
4. Retain the existing public event ordering and final tool-phase checkpoint;
   intermediate persistence needed for lifecycle actions is internal.

### Tool-duration feasibility without choosing a plugin kind

1. An application-plugin implementation can keep the monotonic start value in
   application-plugin state, then load the completed session, rewrite the
   matching tool message and session stats using core history helpers, rebuild
   native history, and save.
2. A feature-plugin implementation can keep the monotonic start value in the
   application runtime store, then patch/replace the full native history and
   return `session_metadata` for aggregation. Core rebuilds the transformed
   session and the application saves it.
3. Either implementation can place per-call duration on the tool message and
   compute turn/session aggregates from the complete history. Subtask 020
   chooses the plugin kind; subtask 010 does not privilege either path.
4. No separate stats artifact file is required for per-session tool duration.
   The session-level directory remains available for plugin-owned artifacts
   that do not fit in session metadata.

### Config-schema discoverability

1. Add framework-owned flattened config schema entries for all four
   `stats.*` keys, marked as application-wide rather than per-session
   overrides.
2. Merge those entries into the session config-schema HTTP response alongside
   `AgentCore.get_config_schema()` output.
3. Show the same entries in `/help config` in a clearly labeled framework
   application section; do not imply that `/set` can mutate these process-wide
   paths.
4. Test both discovery surfaces so config discoverability is verified at the
   public boundaries named by the requirement.

### Implementation decisions and open questions

- **Resolved by human clarification — instrumentation seam**: lifecycle
  invocation and authoritative-session replacement belong directly in
  `ToolLoopRunner._apply_tool_calls`. The prohibition is against implementing
  clocks, elapsed-time calculation, or stats persistence in the tool loop, not
  against adding framework lifecycle plumbing there. A separate core adapter
  would add indirection without serving another requirement.
- **Resolved by human refinement — plugin capabilities**: the lifecycle
  originates in the application-owned tool loop, dispatches normal application
  actions, and also delegates to the existing core session lifecycle so
  feature plugins can transform the whole history. Plugin authors choose
  application or feature ownership for duration tracking.
- **Resolved by prior contracts — no narrow result shape**: application actions
  retain full-session return/save behavior; feature actions retain complete
  `native_messages` replacement plus `session_metadata`. Do not add
  `tool_result_metadata`, message-targeting patches, or a duration-specific
  lifecycle result envelope.
- **Human approval — reentrant lifecycle transaction**: approve changing the
  process-local per-session lock to a reentrant lock and holding it across each
  lifecycle stage. This lets existing application plugins nest their normal
  lock/load/rebuild/save pattern while preventing a second tool loop from
  committing during the stage.
- **Human approval — application-save adoption**: approve reloading and
  adopting active-session saves captured by an internal same-thread observer
  after each application action, then advancing the active request baseline.
  A detached/background save is not observed or adopted and remains an
  external concurrent modification.
- **Developer decision — core action breadth**: use
  `AgentCore.execute_lifecycle_actions` unchanged. Because that established
  dispatcher includes provider-extension and feature session actions, both can
  observe the triggers; adding a feature-only filter would create a novel
  lifecycle semantic.
- **Developer decision — current invocation stability**: arbitrary session
  rewrites do not retroactively replace or cancel the already selected tool
  call. The transformed session controls subsequent calls and LLM phases.
- **Developer decision — plugin kind deferred**: subtask 010 proves both
  application- and feature-plugin paths. Subtask 020 selects one based on the
  implementation's state/storage/UI needs.
- **Developer decision — directory creation**: accessors are
  side-effect-free. This avoids creating `~/.crystal/stats` for users who never
  enable a stats-writing plugin and keeps concrete plugin subdirectories
  plugin-owned.
- **Developer decision — no `STATS_*` env overlay**: runtime access uses the
  existing `app` capability rather than adding more process-global state. Path
  values can still use `${env:...}` in config.
- **Developer decision — hook failures**: retain the existing lifecycle
  behavior in which an action exception fails the active request and flows
  through `request_error`; do not silently discard plugin failures.

### Documentation

- Add docstrings and typed contracts for the new framework accessors,
  `ToolLoopRunner` callback, reentrant lifecycle transaction, save-adoption
  behavior, and lifecycle contexts as part of this subtask.
- Update feature/application action protocol docstrings only where needed to
  state that these triggers use the already-supported full-session contracts;
  do not document a new mutation envelope.
- User-facing plugin documentation remains owned by
  `tasks/20260801-duration-and-stats-tracking/070-docs.md`, which runs after the
  implementation contracts stabilize.
- The 070 draft must be reconciled with this plan before execution: it
  currently promises `STATS_*` environment variables, while this plan
  intentionally exposes runtime paths through `AgentApplication`.

### Task checklist

- [ ] Obtain human approval for the reentrant lifecycle transaction and
  synchronous application-save adoption
- [ ] Normalize and validate the four `stats.*` configuration values before
  application plugin initialization
- [ ] Add the three storage-scope/session-directory accessors and metadata-key
  accessor
- [ ] Add framework config-schema entries and expose them through HTTP and
  terminal help
- [ ] Change the shared process-local session lock to a reentrant lock and
  cover nested application-plugin locking
- [ ] Add the full-session lifecycle callback to `ToolLoopRunner` and wire it
  from `AgentApplication`
- [ ] Place prepare before execution and complete after raw result
  append/checkpoint, with full tool-call context
- [ ] Implement the locked application lifecycle coordinator that persists the
  current session, observes/adopts same-thread plugin saves, applies standard
  returned session transformations, and advances the request baseline
- [ ] Dispatch provider-extension/feature actions through the existing
  `AgentCore.execute_lifecycle_actions` contract and persist the rebuilt
  session
- [ ] Refresh the runner's authoritative session/config after every lifecycle
  and project transformed matching tool messages into tool events
- [ ] Add storage config/path tests, including overrides, tilde/relative paths,
  unknown scopes, and unsafe session ids
- [ ] Add lifecycle tests for ordering, context, full-history rewrites,
  failures, cancellation, multiple calls, and transformed event projection
- [ ] Add an application-plugin integration fixture that locks, reloads,
  rewrites multiple messages/metadata, rebuilds native history, and saves
- [ ] Add a feature-plugin integration fixture that replaces full native
  history and session metadata on prepare/complete
- [ ] Add concurrency tests proving synchronous lifecycle saves advance the
  active baseline while a genuinely concurrent loop still conflicts
- [ ] Prove equivalent duration annotation/aggregation is possible through
  both application and feature fixture paths without framework timing
- [ ] Add HTTP config-schema and terminal `/help config` coverage
- [ ] Run the focused core and application tests, then the default core and
  application suites if focused verification passes

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Three configurable storage directories | Application test constructs default and overridden apps and asserts all three absolute accessor results |
| Project-level default and override | Test proves the default is under resolved `WORKING_DIR` and an explicit placeholder/relative override wins |
| User-level default and override | Test proves `~/.crystal/stats` expands under the test home and an explicit override wins |
| Session-level directory | Test proves the default follows `session_root.parent`, an override wins, and the per-session helper returns a safe child path |
| Configurable metadata key | Test proves the normalized app config and accessor default to `stats` and expose an override to an initialized application plugin |
| Runtime plugin resolution | Lifecycle fixture resolves all scopes through the `app` object supplied by the framework, without consulting process env |
| Per-tool-call lifecycle hooks | Integration test records prepare → tool execution/result append → complete for every call and verifies both application and core actions receive the complete session/context |
| Full application-plugin freedom | Fixture uses the established application pattern to load, rewrite arbitrary messages and metadata, rebuild native history, and save; the next tool-loop step uses that exact persisted session |
| Full feature-plugin transformation | Fixture returns complete replacement native history and session metadata; core rebuilds it and the next tool-loop step uses the transformed session |
| Plugin-kind choice | Equivalent annotation/aggregation fixtures pass once as an application action and once as a feature action without changing framework hook code |
| Conflict-safe in-loop saves | A nested-lock application save during the lifecycle advances the active baseline without conflict, while a separate competing request still receives the normal conflict/backup outcome |
| Framework does not track duration | Source inspection and fixture assertions prove `tool_loop.py` contains lifecycle orchestration only, with no clock reads, elapsed-time computation, duration fields, or stats persistence; core execution uses the existing session lifecycle contract |
| Config keys discoverable | HTTP config-schema and terminal help tests list all four `stats.*` entries with application-wide scope |

### Additional implementation verification

- Exercise streaming and non-streaming application requests because both use
  `iter_tool_messages` but expose different event sequences.
- Exercise multiple sequential tool calls to prove lifecycle state and pending
  transformations are correlated by request/tool-call id and the authoritative
  rewritten session flows into each next call.
- Exercise a synthesized missing-tool result and cancellation before a final
  result.
- Exercise an application action that both saves and returns a standard
  session transformation, verifying declaration-order composition.
- Exercise a feature action that removes/reorders history and verify the
  checkpoint remains authoritative even when no matching tool message remains
  for event projection.
- Re-run existing tool-loop session concurrency and tool-plugin context tests
  to ensure the lifecycle callback preserves checkpoint reconciliation,
  cancellation, and layered context.
- Run:
  - focused new tests in `core/python/tests`
  - focused HTTP/terminal tests in `application/python/tests`
  - `pytest core/python/tests -q`
  - `pytest application/python/tests -q`

Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

# Framework Stats Infrastructure

Define the framework-level storage directory scopes, the session stats metadata key, and the lifecycle action hooks that plugins need to capture tool-call duration without modifying `tool_loop.py` or `AgentCore`.

## Requirements checklist

- [ ] Three configurable storage directory paths exist: session-level, project-level, and user-level.
- [ ] The project-level directory defaults to a location within the project directory; the user can override via config.
- [ ] The user-level directory defaults to a location within the user home; the user can override via config.
- [ ] The session-level directory is defined and configurable.
- [ ] A configurable session metadata key exists for storing session-level summary stats (default `stats`).
- [ ] Plugins can resolve the active storage directory for each scope at runtime via a framework-provided mechanism.
- [ ] The framework provides lifecycle action hooks sufficient for a plugin to capture per-tool-call duration without modifying `tool_loop.py` or `AgentCore` tool execution code.
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
- Storage path resolution must work with the existing `${env:...}` config placeholder mechanism.

## Execution plan

Status: Draft

### Storage directories

1. Add config keys under a top-level `stats` section in the application config:
   - `stats.session_dir` — default `${env:WORKING_DIR}/.crystal/stats/sessions` (or alongside the sessions root).
   - `stats.project_dir` — default `${env:WORKING_DIR}/.crystal/stats/project`.
   - `stats.user_dir` — default `~/.crystal/stats`.
   - `stats.session_metadata_key` — default `stats`.
2. Install these as environment variables during `AgentApplication` init (following the runtime-env overlay pattern), e.g. `STATS_SESSION_DIR`, `STATS_PROJECT_DIR`, `STATS_USER_DIR`, `STATS_SESSION_METADATA_KEY`.
3. Add an `AgentApplication` helper method `get_stats_dir(scope: str) -> Path` that resolves the directory for `"session"`, `"project"`, or `"user"`, creating it if needed.
4. Add a helper `get_session_stats_dir(session_id: str) -> Path` that returns the per-session subdirectory under the session-level root (e.g. `<session_dir>/<session_id>/`), creating it if needed.

### Session stats metadata key

1. The session metadata key is read from config (`stats.session_metadata_key`, default `stats`).
2. Plugins read this key from their `init(app_config)` state, not from a hardcoded string.
3. The framework does not enforce the structure of the value under this key; plugins own the schema.

### Lifecycle hooks for tool calls

1. Add two new application-layer lifecycle triggers:
   - `tool_call_prepare` — fired before each tool call executes. Context includes `session_id`, `request_id`, `tool_call` (the inspected call dict), `tool_call_id`, `tool_name`.
   - `tool_call_complete` — fired after each tool call completes (success or error). Context includes the same fields plus `tool_result` (the final tool message dict) and `error` (if the call failed).
2. Dispatch these from `tool_loop.py::_apply_tool_calls` by calling `AgentApplication.run_session_lifecycle(...)` (or a lightweight variant) before and after `core.iter_tool_messages`.
3. The framework does NOT pass timing data in the context. A plugin that wants duration captures its own `time.monotonic()` in `tool_call_prepare` and computes elapsed in `tool_call_complete`.
4. Plugins return `session_metadata` patches or `final_messages` replacements following the existing lifecycle action contract; the framework applies them.

### Config schema

1. Add the `stats.*` keys to the application config schema (via `AgentApplication.get_config_schema()` or a dedicated config-schema contributor).
2. Ensure the keys appear in `/help config` and the HTTP config-schema endpoint.

### Implementation decisions and open questions

- **Lightweight lifecycle dispatch**: `run_session_lifecycle` may be too heavy for per-tool-call hooks (it loads/saves sessions). Consider a lighter dispatch that only runs matching actions without full session reconciliation. *Recommendation*: add a `run_tool_lifecycle` method that runs actions with the tool-call context but does not persist; the plugin is responsible for returning metadata patches that the tool loop applies to the in-flight session.
- **Tool-call lifecycle and session locking**: the tool loop already holds the session lock during `_apply_tool_calls`. The lifecycle dispatch must not re-acquire the lock (would deadlock with a non-reentrant lock). *Recommendation*: the dispatch runs without acquiring the lock; it operates on the in-flight session object.
- **Open question**: should `tool_call_prepare` be able to cancel or skip a tool call? *Recommendation*: no for v1 — the hook is observational only. Cancellation remains via `RequestCancellation`.

### Documentation

- New `plugins/docs/stats-storage.md` describing the three scopes, config keys, env vars, and the plugin file-ownership contract.
- Update `plugins/docs/actions.md` with `tool_call_prepare` and `tool_call_complete` triggers.
- Update `plugins/docs/application-plugins.md` with the `get_stats_dir` / `get_session_stats_dir` helpers.

### Task checklist

- [ ] Add `stats.*` config keys and env-var installation in `AgentApplication.__init__`
- [ ] Add `get_stats_dir(scope)` and `get_session_stats_dir(session_id)` helpers on `AgentApplication`
- [ ] Add `tool_call_prepare` and `tool_call_complete` lifecycle triggers
- [ ] Add lightweight dispatch from `tool_loop.py::_apply_tool_calls` (no session save, no lock re-acquisition)
- [ ] Add config schema entries for `stats.*` keys
- [ ] Write unit tests for path resolution and lifecycle dispatch
- [ ] Write `plugins/docs/stats-storage.md`
- [ ] Update `plugins/docs/actions.md` with new triggers

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Three configurable storage directories | Config schema test confirming `stats.session_dir`, `stats.project_dir`, `stats.user_dir` are present with defaults |
| Project-level dir defaults to project directory | Test that default resolves under `WORKING_DIR` and can be overridden |
| User-level dir defaults to user home | Test that default resolves under `~` and can be overridden |
| Session-level dir is configurable | Test that `get_stats_dir("session")` returns the configured path |
| Session metadata key is configurable | Test that a plugin reads the key from `init(app_config)` state and it defaults to `stats` |
| Plugins can resolve directories at runtime | Unit test calling `app.get_stats_dir("session"/"project"/"user")` and `app.get_session_stats_dir(session_id)` |
| Lifecycle hooks for tool calls | Unit test that a plugin with `trigger: "tool_call_complete"` receives context with `tool_call_id` and `tool_result` |
| Framework does not capture timing | Grep verification that `time.monotonic` is not added to `tool_loop.py` for duration capture |
| Config keys discoverable | `/help config` or HTTP config-schema test listing all `stats.*` keys |
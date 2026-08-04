# Duration and Stats Tracking Enhancements

Enhance duration tracking to cover tool calls and human time, add frontend-reported usage telemetry, and revise session/project/user-level stats storage to use dedicated metadata keys and configurable directories instead of last-message stamping.

## Requirements checklist

- [ ] Tool call duration is captured per tool call by a plugin, not by framework code in `tool_loop.py` or `AgentCore`.
- [ ] Tool call duration is surfaced on tool-result message metadata and accumulates into per-turn and total stats.
- [ ] The existing LLM request `turn_duration_ms` is preserved as LLM-only; tool call duration is a separate field, not merged into LLM duration.
- [ ] Human time is tracked per session, split into human review time and human message composition time, computed from frontend-reported activity events.
- [ ] Frontend usage telemetry is sent via application plugin actions; each frontend owns its collection implementation and may share code across frontends.
- [ ] A server setting configures which plugin id handles usage telemetry; frontends read this setting to route telemetry calls.
- [ ] Session-level summary stats are stored under a dedicated configurable metadata key on the session, not scattered across the last assistant message.
- [ ] Project-level stats are stored as files under a configurable project-level directory (default in the project directory).
- [ ] User-level stats are stored as files under a configurable user-level directory (default in the user home directory).
- [ ] A session-level storage directory exists and is configurable, for per-session stats artifacts that do not fit in session metadata.
- [ ] The framework exposes the three storage scopes (session, project, user) to plugins; plugins own the concrete subdirectory and file names within each scope.
- [ ] Per-turn, per-message, and total stats are tracked where relevant for LLM duration, tool call duration, and human time.
- [ ] No backward compatibility is required for existing sessions; stats appear on the first opportunity to update them.
- [ ] The framework provides lifecycle action hooks sufficient for a plugin to capture per-tool-call duration without framework timing logic in `tool_loop.py` or `AgentCore` tool execution code.
- [ ] Application plugins handling tool-call lifecycle triggers retain their normal ability to load, transform, rebuild, and save the complete active session without their synchronous saves being treated as a competing tool loop.
- [ ] Feature plugins can handle the same tool-call lifecycle triggers through the existing full-session core action contract.
- [ ] Tool-call duration may be implemented as either an application plugin or a feature plugin without changing the framework hooks.

## Resolved requirement decisions

- **Telemetry transport**: Frontend-owned, sent via existing `executeAction`. No SDK method added. A server setting defines the telemetry plugin id.
- **Tool duration ownership**: Plugin-owned. The framework only adds lifecycle hooks; it does not capture timing in `tool_loop.py` or `AgentCore`.
- **Tool lifecycle plugin kinds**: The application-owned tool loop dispatches both normal application actions and the existing core session lifecycle. Application plugins retain full load/rebuild/save capability; feature plugins retain full native-history transformation capability. The duration implementation may choose either plugin kind.
- **Backward compatibility**: Not required. Stats appear on first update; old sessions are not backfilled.
- **Storage scopes**: Three configurable directories (session, project, user). Plugins own subdirs/files within them. Session summary stats also use a configurable metadata key.
- **Stat breakdown**: Keep existing LLM `turn_duration_ms`; add tool call duration, human review time, human composition time — each tracked per-message, per-turn, and total where relevant.
- **Telemetry storage format**: File-backed JSONL under the session-level storage directory. Consumers maintain a read pointer (line offset + event id) to avoid re-reading all telemetry on each aggregation pass.
- **Per-message human composition time**: Stored both on the user message metadata (for display) and in the session stats metadata (for aggregation).

## Supporting details

### Current state

- `DurationExtension` (`plugins/timestamp-extension/src/timestamp_extension/duration_extension.py`) captures LLM-only duration in `initialize_request`/`finalize` and stamps it on the "owner" assistant message's `_metadata`.
- The tool loop (`core/python/agent_app/tool_loop.py::_apply_tool_calls`) executes tool calls via `core.iter_tool_messages` with no timing instrumentation.
- Existing session-metadata apps (`session-status-app`, `session-title-app`, `session-pinned-app`) store state in `session.metadata[key]` using load→rebuild→save under `acquire_session_lock`.
- Server settings are stored at `runtime/server_settings.json` and exposed via `GET /server/settings` and `GET /server/settings/ui-schema`.
- The runtime env contract (`plugins/docs/application-plugins.md`) exposes `CONFIG_DIR`, `WORKING_DIR`, `BUILTIN_PLUGINS` to plugins via `os.environ`.
- `ProjectProfileManager` (`application/python/agent_terminal_app/project_profile.py`) keys user-level data by absolute project path in `~/.crystal/projects.json`.

### Constraints

- Plugin instances are short-lived per request; state lives in explicit `state: dict`, not instance attributes.
- `Session` and `Message` are immutable (`@dataclass(frozen=True)`); all transforms return new instances.
- First-party plugins go under repo-root `plugins/` with tests alongside.
- No defensive copying of returned structures (AGENTS.md §1).

## Subtasks

- [ ] `tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/020-tool-call-duration-plugin.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/030-llm-duration-stats-relocation.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/040-human-time-telemetry-plugin.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/050-human-time-tracking-plugin.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/060-project-and-user-stats-plugins.md`
- [ ] `tasks/20260801-duration-and-stats-tracking/070-docs.md`

## Execution plan

Status: Draft

The work is organized into seven subtasks with a foundation-first dependency chain. Subtask 010 delivers the framework storage and lifecycle infrastructure that all other subtasks depend on. Subtasks 020, 030, and 040 can proceed in parallel once 010 is complete. Subtask 050 depends on 040 (telemetry buffer must exist before tracking can consume it). Subtask 060 depends on 020, 030, and 050 (session stats must exist before they can be aggregated to project/user level). Subtask 070 (docs) runs last.

### Implementation decisions and open questions

- **Session-level directory shape**: per-session subdirectory (e.g. `<session_id>/`) under a session-stats root, matching the session-assets pattern. Each plugin owns its files within that subdirectory.
- **Human-time categories**: start with review + composition. A third "other active time" category is not required for v1.
- **Telemetry JSONL path**: `<session-level-dir>/<session_id>/telemetry/<plugin-chosen-name>.jsonl`. The telemetry plugin owns the `telemetry/` subdir name; the tracking plugin owns its read-pointer file location.
- **Read pointer storage**: the tracking plugin stores its read pointer (line count + last consumed event id) in a separate file under the session-level directory, owned by the tracking plugin.

### Documentation

- New `plugins/docs/stats-storage.md` describing the three storage scopes, config keys, and the plugin contract for file ownership.
- Updated `plugins/timestamp-extension/README.md` for tool-duration and stats relocation.
- Updated `plugins/docs/application-plugins.md` with the telemetry plugin contract and server setting.
- Updated `plugins/docs/actions.md` with any new lifecycle triggers.
- Config schema entries from all new and modified plugins.

### Task checklist

- [ ] 010: Framework stats infrastructure (storage directories, session metadata key, lifecycle hooks)
- [ ] 020: Tool call duration plugin
- [ ] 030: LLM duration stats relocation
- [ ] 040: Human time telemetry plugin (JSONL file-backed, server setting for plugin id)
- [ ] 050: Human time tracking plugin (review + composition, read-pointer consumption)
- [ ] 060: Project and user stats plugins
- [ ] 070: Documentation and config schema

### Requirement verification

| Requirement group | Verification evidence |
|---|---|
| Tool call duration (plugin-owned, per-message/turn/total) | Unit tests in `plugins/<tool-duration-plugin>/tests`; integration test in `application/python/tests` showing tool-result messages carry `duration_ms` and session stats metadata contains tool totals |
| LLM duration relocation (per-turn/total in session stats) | Unit tests in `plugins/timestamp-extension/tests`; session-list field test showing LLM totals surface from session metadata |
| Human time telemetry (JSONL, server setting) | Unit tests in `plugins/<telemetry-plugin>/tests` verifying JSONL append and read-pointer semantics; server-settings UI-schema test confirming the plugin-id setting is exposed |
| Human time tracking (review + composition, per-message/turn/total) | Unit tests in `plugins/<tracking-plugin>/tests` verifying max-idle rule, per-message composition time on user messages, and session stats totals |
| Three storage scopes (session, project, user) | Unit tests verifying plugins can resolve each scope's directory; config schema test confirming all path keys are discoverable |
| Project/user aggregate stats | Unit tests with tmp dirs verifying files land under configured directories; atomic write verification |
| No backward compatibility | Test that a fresh session (no prior stats) gets stats on first save without error |
| Framework lifecycle hooks for tool calls | Application- and feature-plugin fixtures both receive per-call prepare/complete context and rewrite the complete session through their established contracts while `tool_loop.py` contains lifecycle orchestration only and no timing or stats implementation |
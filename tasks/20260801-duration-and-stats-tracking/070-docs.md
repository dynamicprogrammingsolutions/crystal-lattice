Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md
- tasks/20260801-duration-and-stats-tracking/020-tool-call-duration-plugin.md
- tasks/20260801-duration-and-stats-tracking/030-llm-duration-stats-relocation.md
- tasks/20260801-duration-and-stats-tracking/040-human-time-telemetry-plugin.md
- tasks/20260801-duration-and-stats-tracking/050-human-time-tracking-plugin.md
- tasks/20260801-duration-and-stats-tracking/060-project-and-user-stats-plugins.md

# Documentation and Config Schema

Update documentation and config schemas to cover the new stats infrastructure, lifecycle hooks, telemetry contract, human-time categories, and stat breakdown.

## Requirements checklist

- [ ] Documentation describes the three storage scopes (session, project, user), their defaults, and their config keys.
- [ ] Documentation describes the session stats metadata key convention and its config key.
- [ ] Documentation describes the lifecycle hooks available for tool call duration capture (`tool_call_prepare`, `tool_call_complete`).
- [ ] Documentation describes the telemetry plugin contract: the action shape, the JSONL format, the server setting for plugin id, and the frontend's responsibility to collect and send events.
- [ ] Documentation describes the human time categories (review, composition), the max-idle-duration rule, and the config key for the threshold.
- [ ] Documentation describes the stat breakdown: per-message, per-turn, and total for LLM duration, tool call duration, and human time.
- [ ] Documentation describes the read-pointer convention for telemetry consumers.
- [ ] Config schema entries from all new and modified plugins are present and discoverable.
- [ ] `plugins/timestamp-extension/README.md` is updated to reflect tool-duration support and stats relocation.

## Supporting details

### Current state

- Plugin docs live under `plugins/docs/` with an index at `plugins/docs/index.md`.
- `plugins/docs/actions.md` documents lifecycle triggers and needs updating for the new tool-call triggers.
- `plugins/docs/application-plugins.md` documents the application plugin protocol and needs the telemetry/tracking plugin patterns.
- `plugins/docs/config-schema.md` documents how plugins expose config keys.
- `plugins/timestamp-extension/README.md` documents `TimestampExtension` and `DurationExtension`.
- Config schema entries are contributed via each plugin's `get_config_schema()` and aggregated by `AgentCore.get_config_schema()`.

### Constraints

- Documentation must be accurate against the implemented code, not aspirational.
- Config schema entries must use the JSON-schema-like shape described in `plugins/docs/config-schema.md`.
- New docs must be linked from `plugins/docs/index.md`.

## Execution plan

Status: Draft

### New and updated docs

1. **New**: `plugins/docs/stats-storage.md` — the three storage scopes, config keys (`stats.session_dir`, `stats.project_dir`, `stats.user_dir`, `stats.session_metadata_key`), env vars (`STATS_SESSION_DIR`, `STATS_PROJECT_DIR`, `STATS_USER_DIR`), the `get_stats_dir` / `get_session_stats_dir` helpers, and the plugin file-ownership contract.
2. **Update**: `plugins/docs/actions.md` — add `tool_call_prepare` and `tool_call_complete` to the standard lifecycle set with timing, ownership, and context keys.
3. **Update**: `plugins/docs/application-plugins.md` — add the telemetry plugin pattern (JSONL ingestion, server setting for plugin id) and the tracking plugin pattern (read-pointer consumption, human-time computation).
4. **Update**: `plugins/docs/index.md` — link to `stats-storage.md`.
5. **Update**: `plugins/timestamp-extension/README.md` — document tool-duration support (cross-reference the tool-duration plugin), stats relocation to session metadata, and the new session-level totals.
6. **New**: `plugins/tool-duration-app/README.md` — plugin description, config toggle, stats fields.
7. **New**: `plugins/llm-duration-stats-app/README.md` — session-level LLM totals, session-list field.
8. **New**: `plugins/usage-telemetry-app/README.md` — action contract, event types, JSONL format, server setting.
9. **New**: `plugins/human-time-tracking-app/README.md` — event classification, max-idle rule, read-pointer, stats fields.
10. **New**: `plugins/project-stats-app/README.md` and `plugins/user-stats-app/README.md` — aggregation, file paths, session-list fields.

### Config schema entries

1. `stats.session_dir`, `stats.project_dir`, `stats.user_dir`, `stats.session_metadata_key` — from `AgentApplication` or a dedicated config-schema contributor.
2. `tool_duration_show_footer` — from the tool-duration plugin.
3. `duration_extension_show_total_in_list` — from the LLM-duration-stats app.
4. `usage_telemetry_plugin_id` — server setting from the telemetry plugin.
5. `human_time_max_idle_seconds` — from the human-time-tracking plugin.
6. `human_time_show_in_list` — from the human-time-tracking plugin.

### Stat breakdown reference

Create a reference table in `plugins/docs/stats-storage.md`:

| Stat | Per-message | Per-turn | Total (session) | Project/User |
|------|-----------|---------|-----------------|--------------|
| LLM duration | `metadata.duration_ms` (existing) | `turn_duration_ms` (existing, LLM-only) | `stats.llm_duration_ms` | aggregated |
| Tool call duration | `metadata.duration_ms` (tool messages, new) | `stats.turn_tool_duration_ms` | `stats.tool_duration_ms` | aggregated |
| Human review time | n/a | `stats.turn_human_review_ms` | `stats.human_review_ms` | aggregated |
| Human composition time | `metadata.human_composition_ms` (user messages) | `stats.turn_human_composition_ms` | `stats.human_composition_ms` | aggregated |
| Human time (combined) | n/a | `stats.turn_human_time_ms` | `stats.human_time_ms` | aggregated |

### Task checklist

- [ ] Write `plugins/docs/stats-storage.md`
- [ ] Update `plugins/docs/actions.md` with `tool_call_prepare` / `tool_call_complete`
- [ ] Update `plugins/docs/application-plugins.md` with telemetry and tracking patterns
- [ ] Update `plugins/docs/index.md` to link `stats-storage.md`
- [ ] Update `plugins/timestamp-extension/README.md`
- [ ] Write README.md for each new plugin (020, 030, 040, 050, 060)
- [ ] Verify all config schema entries are present via `/help config` or HTTP config-schema endpoint
- [ ] Verify stat breakdown table matches implemented field names

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Three storage scopes documented | `plugins/docs/stats-storage.md` contains sections for session, project, user scopes with defaults and config keys |
| Session metadata key documented | `stats-storage.md` describes `stats.session_metadata_key` with default `stats` |
| Tool-call lifecycle hooks documented | `plugins/docs/actions.md` contains `tool_call_prepare` and `tool_call_complete` with context keys |
| Telemetry contract documented | `plugins/usage-telemetry-app/README.md` describes action shape, JSONL format, server setting, frontend responsibility |
| Human time categories documented | `plugins/human-time-tracking-app/README.md` describes review + composition, max-idle rule, config key |
| Stat breakdown documented | `stats-storage.md` contains the per-message/per-turn/total breakdown table |
| Read-pointer convention documented | `plugins/human-time-tracking-app/README.md` or `stats-storage.md` describes the read-pointer file format and semantics |
| Config schema entries present | HTTP config-schema endpoint or `/help config` lists all new keys |
| `timestamp-extension/README.md` updated | README mentions tool-duration and session-level totals |
Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md
- tasks/20260801-duration-and-stats-tracking/020-tool-call-duration-plugin.md
- tasks/20260801-duration-and-stats-tracking/030-llm-duration-stats-relocation.md
- tasks/20260801-duration-and-stats-tracking/050-human-time-tracking-plugin.md

# Project and User Stats Plugins

Plugins that aggregate session-level stats into project-level and user-level files under the configured storage directories, with the framework providing the directory paths and plugins owning the concrete file names.

## Requirements checklist

- [ ] A plugin writes project-level aggregate stats files under the project-level storage directory.
- [ ] A plugin writes user-level aggregate stats files under the user-level storage directory.
- [ ] Plugins choose the concrete subdirectory and file names within the configured directories; the framework does not dictate file names.
- [ ] Project-level and user-level stats include aggregate LLM duration, tool call duration, and human time totals across sessions.
- [ ] Project-level stats are scoped per project directory (keyed by project path, matching the `projects.json` pattern).
- [ ] Session-list UI can surface project-level or user-level totals from the stats files via `session_list_field` elements.
- [ ] Stats files are updated on session save or request complete, not requiring a separate manual trigger.
- [ ] Stats files use atomic writes (tmp-rename) to avoid corruption.
- [ ] The session stats metadata is the single source of truth; project/user files are derived caches that can be rebuilt from session stats.

## Supporting details

### Current state

- `FilesystemSessionStore.save` and `_write_server_settings_unlocked` both use tmp-path-then-rename for atomic writes (`core/python/agent_app/sessions.py`, `core/python/agent_app/application_future.py`).
- `ProjectProfileManager` (`application/python/agent_terminal_app/project_profile.py`) keys user-level data by absolute project path in `~/.crystal/projects.json`.
- The project-level and user-level storage directories are defined in subtask 010 (`stats.project_dir`, `stats.user_dir`, env `STATS_PROJECT_DIR`, `STATS_USER_DIR`).
- Session stats metadata (`session.metadata["stats"]`) is populated by subtasks 020 (tool duration), 030 (LLM duration), and 050 (human time).

### Constraints

- Aggregate stats must be recomputable from session stats metadata (single source of truth is the session; project/user files are derived caches).
- Plugins own the concrete subdirectory and file names; the framework only provides the directory path.
- Atomic writes (tmp-rename) are required to avoid corruption from concurrent writes or crashes.
- Project-level stats must be keyed by project path so multiple projects on the same machine do not collide.

## Execution plan

Status: Draft

### Plugin structure

1. Create `plugins/project-stats-app/` (application plugin) for project-level aggregation.
2. Create `plugins/user-stats-app/` (application plugin) for user-level aggregation.
3. Both plugins use `AgentApplication.get_stats_dir(scope)` to resolve their base directory.

### Project-level stats

1. The plugin owns a subdirectory under `STATS_PROJECT_DIR`, e.g. `project_stats_app/`.
2. File: `project_stats_app/daily.json` (or `totals.json`) containing aggregate stats across all sessions in the current project.
3. The project is identified by the absolute path of the working directory (`WORKING_DIR`), matching `ProjectProfileManager`'s keying.
4. On `session_save_prepare` or `request_complete`, the plugin:
   - Reads the current session's `session.metadata["stats"]`.
   - Loads the project-level file (or starts fresh).
   - Updates the aggregate totals (LLM duration, tool duration, human review, human composition, combined human time).
   - Writes the file atomically.

### User-level stats

1. The plugin owns a subdirectory under `STATS_USER_DIR`, e.g. `user_stats_app/`.
2. File: `user_stats_app/totals.json` containing aggregate stats across all projects.
3. On `session_save_prepare` or `request_complete`, the plugin:
   - Reads the current session's stats.
   - Loads the user-level file (or starts fresh).
   - Updates the aggregate totals.
   - Writes the file atomically.

### Aggregation approach

1. **Incremental**: on each session save, add the delta (new turn's stats) to the existing aggregate. This requires tracking which turns have been counted (similar to subtask 030).
2. **Recompute-from-sessions**: on each save, list all session files, read their stats metadata, and recompute the aggregate. Simpler but O(n) in the number of sessions.
3. *Recommendation*: incremental for v1, with a periodic recompute fallback (e.g. on startup or via a manual action) to correct any drift. Track a `last_aggregated_session_mtime` or `last_aggregated_turn_id` to avoid double-counting.

### Session-list surfacing

1. Add `session_list_field` elements that read from the project/user stats files (loaded into the session summary context):
   - `{"ui_type": "session_list_field", "id": "project_human_time", "data": "project_stats.human_time_ms", "template": "Project human: {{data}}", "metadata": {"format": "duration_ms"}}`
2. The application layer needs to load project/user stats into the session-list context so `session_list_field` elements can reference them. *Open question*: does the existing `session_list_field` mechanism support data sources beyond `metadata.*`? If not, the plugin can contribute fields via the `session_list` trigger action return.

### Implementation decisions and open questions

- **Incremental vs. recompute**: *Recommendation*: incremental with a startup recompute for correctness.
- **Project identity**: use `WORKING_DIR` absolute path as the project key, matching `ProjectProfileManager`. Store the project key in the stats file so it can be identified.
- **File format**: single JSON file per scope per plugin. For daily breakdowns, a `daily/` subdir with one file per day. *Recommendation*: single `totals.json` for v1; daily breakdown is a follow-up.
- **Open question**: how do `session_list_field` elements access project/user stats? The current mechanism reads from `metadata.*` on the session summary. Options: (a) the `session_list` trigger action loads project/user stats and returns them as contributed fields; (b) extend the session summary to include project/user stats context. *Recommendation*: option (a) — the plugin's `session_list` trigger action reads the stats file and returns the values as `session_list_fields`.

### Documentation

- `plugins/project-stats-app/README.md` and `plugins/user-stats-app/README.md`.
- Update `plugins/docs/stats-storage.md` with the aggregation pattern and file-ownership convention.

### Task checklist

- [ ] Create `plugins/project-stats-app/` package structure
- [ ] Create `plugins/user-stats-app/` package structure
- [ ] Implement project-level aggregation with atomic writes
- [ ] Implement user-level aggregation with atomic writes
- [ ] Implement incremental update with startup recompute fallback
- [ ] Add `session_list` trigger actions to surface project/user totals
- [ ] Write unit tests with tmp dirs (aggregation, atomic writes, project keying)
- [ ] Write integration test (session save → project/user files updated)
- [ ] Write `README.md` for both plugins

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Project-level stats file exists under project dir | Unit test: after a session save, file exists at `<STATS_PROJECT_DIR>/<plugin-subdir>/totals.json` |
| User-level stats file exists under user dir | Unit test: after a session save, file exists at `<STATS_USER_DIR>/<plugin-subdir>/totals.json` |
| Plugins choose file names | Test that the file path includes a plugin-owned subdirectory name not dictated by config |
| Aggregate includes LLM, tool, human time | Unit test: file contains `llm_duration_ms`, `tool_duration_ms`, `human_review_ms`, `human_composition_ms`, `human_time_ms` |
| Project scoped by project path | Unit test: two different `WORKING_DIR` values produce two different project-level files or entries |
| Session-list surfaces project/user totals | UI-schema or session-list test confirming `session_list_field` elements for project/user stats are present |
| Updated on session save | Integration test: `save_session` triggers a project/user file update |
| Atomic writes | Unit test: concurrent writes do not corrupt the file (content is valid JSON) |
| Derived from session stats | Test: deleting the project/user file and saving a session recreates it with correct values from session stats |
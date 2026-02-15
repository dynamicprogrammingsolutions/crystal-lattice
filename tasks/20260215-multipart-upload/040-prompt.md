Update provider/plugins to expose per-attachment-type composer UI schema elements (`ui_type: "composer_attachment"`), including optional `prepare_action` references that frontends can invoke via `/actions`.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`
- (for prepare action linkage) `tasks/20260215-multipart-upload/090-asset-prepare-upload-action.md`

2) Inspect how UI schema is currently exposed/flattened:
- `core/python/agent_core/core.py` (`AgentCore.get_ui_schema`)
- `core/python/agent_core/types.py` (`BasePlugin.get_ui_elements` docs)
- `application/python/agent_terminal_app/server.py` (`GET /sessions/{session_id}/ui-schema`)

3) Inspect candidate provider/plugin implementations to modify:
- `core/python/plugins/openrouter_provider.py`
- `core/python/plugins/openai_provider.py`

4) Decide and propose to the user:
- Which plugin(s) will emit the `composer_attachment` elements
- The exact element dictionaries (keys/values)
- Whether to add `prepare_action` now or just leave as optional placeholders

Share the plan with the user; do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement `get_ui_elements()` updates to emit `composer_attachment` elements.

2) Verify they appear in `GET /sessions/{session_id}/ui-schema` for a session using that provider.

3) Add/adjust a unit test if obvious (optional but recommended).

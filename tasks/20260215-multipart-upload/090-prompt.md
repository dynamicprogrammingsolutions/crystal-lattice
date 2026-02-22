Implement optional Phase 2: provider/extension-defined asset prepare/upload actions that use the same semantics as application actions, and wire them so UIs can invoke them via `prepare_action` referenced from `composer_attachment` UI schema.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/090-asset-prepare-upload-action.md`
- UI schema linkage: `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`

2) Inspect current action system in the server/application layer:
- `application/python/agent_terminal_app/server.py` (`GET /application/actions`, `POST /actions`)
- `core/python/agent_app/application_future.py` (application plugin wrappers and action execution paths)
- `core/python/agent_app/app_plugins.py` and related action plumbing (if present)

3) Inspect how plugins are loaded and instantiated for a session:
- `core/python/agent_app/application_future.py` (agent config resolution and plugin selection)
- `core/python/agent_core/core.py` plugin resolution helpers

4) Decide the high-level design and present it to the user:
- How non-application plugins define actions (duck-typed methods; exact names)
- How actions are listed (new endpoint vs extending existing)
- How `POST /actions` routes execution to application vs provider/extension vs feature/tool
- How session context/config is provided (session id, agent config, overrides)

Do not implement until user approves the plan.

## Step 2 — Complete (after user approval)

1) Implement action definition + execution support for non-application plugins.

2) Add at least one provider/extension action (e.g. `upload_image`) and reference it from a `composer_attachment.prepare_action` element.

3) Add tests (unit or integration) that:
- List actions and include the provider/extension action.
- Execute the action and verify it returns a normalized `part` payload.

4) Provide a short UI integration note (how to call the action using `plugin` + `prepare_action`).

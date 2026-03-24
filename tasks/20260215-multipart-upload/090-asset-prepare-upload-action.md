# Phase 2 (Optional): Provider/extension-defined asset prepare/upload actions + thumbnails

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Add an optional server-side mechanism for provider/extension (and other core plugin types) to define asset preparation/upload actions (e.g. resize/compress images, generate thumbnails, convert local files to provider-specific references, validate size limits) without changing the core message interface.

This phase is explicitly optional and can be implemented after v1 multipart messaging is stable.

## Depends On

- `tasks/20260215-multipart-upload/020-server-append-multipartcontent.md`
- `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`

## Rationale

v1 uses JSON-compatible attachment payloads (URLs/base64) because bridge transport only stringifies JSON bodies. However:

- Base64 payloads can be large.
- Some providers may prefer a specific upload workflow.
- Frontends benefit from thumbnails and consistent part shapes.

Instead of introducing a dedicated binary upload endpoint (which the bridge transport cannot currently support), expose a JSON-based "prepare asset" action.

## Requirements (Locked)

- The prepare step is defined in provider/extension plugins (and optionally features/tools).
- Prepare actions must use the same semantics as existing application actions (definition shape + `/actions` execution envelope).
- This implies expanding action support beyond application plugins to other plugin types.
- UI schema elements (`ui_type: "composer_attachment"`) refer to the prepare action by id via `prepare_action`.
  - Example: image attachment refers to `prepare_action: "upload_image"`.

## Proposed Approach (High-level Design)

### 1) Expand action definitions to core plugin types

Today, `GET /application/actions` and `POST /actions` are oriented around *application plugins*.

Add support for action definitions on provider/extension/feature/tool plugins using duck-typed optional methods, mirroring the application action semantics. Suggested method names (finalize when implementing):

- `get_actions(self) -> List[Dict[str, Any]]`
- `execute_action(self, action_id: str, params: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]`

Notes:

- Keep this optional so existing plugins do not break.
- Use the same action definition keys already used by application actions (`plugin`, `id`, `label`, `inputs`, etc.).

### 2) Unify listing endpoints

Provide a single endpoint for all action definitions regardless of plugin type.

Options (choose one during implementation):

- Extend `GET /application/actions` to include actions from all plugin types (despite the name).
- Add `GET /actions/definitions` (preferred for clarity) and keep `GET /application/actions` as a backwards-compatible alias.

### 3) Unify execution endpoint

Keep using `POST /actions` with the same request envelope:

```json
{ "plugin": "<plugin_id>", "action_id": "<action_id>", "inputs": { ... } }
```

Execution routing inside `AgentApplication` should become:

- If `plugin_id` refers to an application plugin: existing execution path.
- Else if `plugin_id` refers to a core plugin (provider/extension/feature/tool):
  - Load session to resolve the agent config (base + overrides).
  - Instantiate the plugin class for that config (and any required state init).
  - Execute the action and return the standard action envelope.

### 4) Prepare action contract

Inputs (suggested; finalize when implementing):

- `attachment_type`: e.g. `image`, `pdf` (or implicit from action)
- `filename`
- `mime_type`
- `data_base64` (or `url`)
- `metadata`: user-selected settings (e.g. quality)

Outputs:

- `part`: a normalized multipart part object to include in core message `multipartContent`
- `thumbnail` (optional): base64 or URL

This keeps the interface consistent across direct HTTP and bridge.

### 5) UI integration

- Frontends read `composer_attachment.prepare_action`.
- When a user selects an asset, the UI calls `POST /actions` with:
  - `plugin = element.plugin`
  - `action_id = element.prepare_action`
  - `inputs = { ...asset payload... }`
- UI stores returned `result.part` into composer attachments.
- If a thumbnail is returned, display it in the attachment list.

## Notes / Constraints

- Keep payload sizes in mind; consider enforcing size caps server-side.
- Avoid persisting prepared assets unless an explicit asset store is introduced.

## Definition of Done

- Action definitions can be provided by at least one provider/extension plugin.
- `POST /actions` can execute those provider/extension actions and returns a standard action envelope.
- At least one `composer_attachment` element references a `prepare_action` that works end-to-end.

## Overlap notes (added during verification)

### Relationship with completed task 140

This task has significant overlap with `tasks/20260310-openai-responses-provider/140-openai-image-pdf-upload-and-upload-modes.md` which is now completed.

### What was implemented in task 140

1. **Attachment upload mode config** in `openai_responses`:
   - `attachment_upload_mode: "direct" | "upload_before_send"` in `openai_responses_attachments_extension.py`
   - Upload-before-send via OpenAI Files API in provider

2. **Provider extension actions** in `openai_responses_attachments_extension.py`:
   - `get_actions(state)` method returning action definitions
   - `execute_action(action_id, params, context, state)` method for upload actions

3. **Attachment policy module** in `openai_responses_attachment_policy.py`:
   - `resolve_attachment_upload_mode(state)` helper
   - Config normalization for attachment mode

### What remains from this task's scope

1. **Generic action support for all plugin types** - The current implementation is specific to `openai_responses` provider extension. The generic "expand action definitions to core plugin types" (provider/extension/feature/tool) was not implemented.

2. **Unified action endpoints** - `GET /actions/definitions` and unified routing for all plugin types was not implemented.

3. **Cross-provider attachment actions** - The action-based upload is only available for `openai_responses`. Other providers (OpenRouter, etc.) do not have this capability.

### Resolution

The core functionality for asset preparation/upload actions was implemented in the `openai_responses` bundle as part of task 140. The generic cross-provider action infrastructure from this task remains undone. Consider:
- Marking this task as "partially completed via task 140"
- Creating a follow-up task for generic cross-provider action infrastructure if needed

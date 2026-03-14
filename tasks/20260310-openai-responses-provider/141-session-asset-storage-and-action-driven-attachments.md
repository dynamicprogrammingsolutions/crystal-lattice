# Session Asset Storage And Action-Driven Attachments

Short description: Implement Stage 3 attachment handling for `openai_responses` so frontends upload files to our server first, the application stores them as real per-session assets, the provider reuses or refreshes OpenAI uploads from that local source of truth, and both mobile and desktop support background upload UX plus preview of sent attachments.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/140-openai-image-pdf-upload-and-upload-modes.md`

## Why this follow-up exists

Stage 2 added direct-send image support plus config-gated upload-before-send for image/PDF. That is not enough for a durable action-driven attachment workflow because OpenAI file references are not a reliable long-term source of truth for session attachments.

This follow-up changes the architecture so:

1. Frontend upload means sending one file to our server through a provider-extension action.
2. Our server stores the original image/PDF in a real per-session asset store.
3. The frontend keeps a stable server-side `asset_ref` in the draft and final request payload.
4. The provider treats OpenAI file uploads as a reusable cache/transport target, not the source of truth.
5. If the OpenAI-side upload has expired, been deleted, or becomes invalid, the provider can re-upload from our local stored asset.

## Locked architectural decisions

### Source of truth

1. The stable attachment reference in frontend and session history is a server-side asset reference, not an OpenAI `file_id`.
2. Original file bytes must be stored on our server so requests can recover if the OpenAI upload expires or is deleted.
3. OpenAI upload references are provider-managed caches derived from the local stored asset.

### Separation of concerns

1. Application layer owns local asset storage and filesystem layout.
2. Attachment extension owns action definitions, validation, action semantics, and attachment-policy UI.
3. Provider owns OpenAI SDK calls, OpenAI upload reuse/refresh, final request conversion, and native-history replay correctness.
4. Attachment parsing/storage/cache helpers should move out of the provider into dedicated helper modules as much as possible.
5. Do not add provider-specific FastAPI routes for attachment upload or deletion; keep using the generic action pipeline.

### Request contract

1. Upload action accepts exactly one file at a time.
2. Frontends send base64 content to our server for the upload action.
3. Final chat requests should send `asset_ref`, not raw base64/data URLs, once the asset has been stored successfully.
4. Provider-specific remote refs stay server-side where possible; the frontend should not depend on OpenAI-specific `file_id` values for normal operation.

## Full desired workflow

### Upload/store flow

1. User picks an image or PDF in mobile or desktop.
2. Frontend calls the existing generic `POST /actions` endpoint with a provider-extension action.
3. The action stores the asset on our server in a session-specific asset directory.
4. The action returns a stable `asset_ref` describing the stored server-side asset.
5. Frontend replaces the large inline/base64 draft payload with that returned `asset_ref` and keeps lightweight display metadata such as filename, mime type, and preview-friendly metadata.

### Send flow

1. Frontend sends a normal chat request with `multipartContent` that contains the `asset_ref`.
2. Provider resolves the `asset_ref` to the locally stored asset.
3. Provider checks for a still-valid cached OpenAI upload for that asset.
4. If a cached OpenAI upload exists and is still valid, the provider reuses it.
5. If no valid cached OpenAI upload exists, the provider uploads from the locally stored asset, updates the cache, and continues.
6. Provider emits the final OpenAI Responses-native request items such as `input_image` or `input_file`.

### Delete flow

1. Frontend needs a delete path for uploaded attachments.
2. Deletion should support unsent draft removal immediately.
3. Local stored assets should not be eagerly deleted after send in the first pass if doing so would break replay or re-upload safety.
4. When an attachment is deleted before send, any cached OpenAI file for that asset should also be deleted when practical.

## Data contracts to implement

### Upload action request

The exact action id can be chosen during implementation, but the action must support a shape like:

```json
{
  "plugin": "openai_responses_attachments",
  "action_id": "store_attachment",
  "action_owner": "provider_extension",
  "inputs": {
    "session_id": "sess_123",
    "client_attachment_id": "draft_1",
    "attachment_type": "pdf",
    "filename": "report.pdf",
    "mime_type": "application/pdf",
    "data_base64": "<base64 bytes>"
  }
}
```

### Upload action response

The action must return a server-owned asset reference that the frontend can reuse later, in a shape like:

```json
{
  "status": "ok",
  "result": {
    "status": "ok",
    "attachment_asset": {
      "asset_ref": {
        "kind": "session_asset",
        "session_id": "sess_123",
        "asset_id": "asset_abc",
        "attachment_type": "pdf"
      },
      "filename": "report.pdf",
      "mime_type": "application/pdf",
      "provider_refs": {
        "openai_responses": {
          "status": "not_uploaded"
        }
      }
    }
  }
}
```

### Final request multipart payload

Once upload succeeds, the frontend should send attachment parts shaped like:

```json
[
  {
    "type": "pdf",
    "content": {
      "asset_ref": {
        "kind": "session_asset",
        "session_id": "sess_123",
        "asset_id": "asset_abc",
        "attachment_type": "pdf"
      },
      "filename": "report.pdf",
      "mime_type": "application/pdf"
    },
    "metadata": {}
  }
]
```

### Final provider-native OpenAI request item

The provider should translate the `asset_ref` into the appropriate OpenAI Responses item, for example:

```json
{
  "type": "input_file",
  "file_id": "file_abc123",
  "filename": "report.pdf"
}
```

## Storage design expectations

### Local server-side asset storage

Implement a real asset store owned by the application layer, not by the frontend and not by OpenAI.

Recommended layout:

1. Session JSON remains in the normal session store.
2. Add a sibling asset root such as:
   - `sessions/<session_id>.json`
   - `session_assets/<session_id>/<asset_id>/blob`
   - `session_assets/<session_id>/<asset_id>/manifest.json`

The exact naming can vary, but the implementation must preserve these properties:

1. Asset bytes live outside the session JSON.
2. Each asset has a manifest with filename, mime type, attachment type, and provider-cache metadata.
3. There is enough metadata to rebuild sent message previews and to re-upload to OpenAI later.

### Session metadata/index

The implementation may keep a lightweight asset index in session metadata in addition to on-disk manifests if that improves lookup and replay, but the original bytes must remain on disk.

## Upload policy expectations

Separate these concepts clearly:

1. `store_on_server`
   This should always happen in Stage 3.
2. `openai_upload_policy`
   This decides when the OpenAI-side upload happens.

Expected policies to support over time:

1. `before_send`
   Store locally during the action, upload to OpenAI only when needed for send.
2. `sync_preupload`
   Store locally and upload to OpenAI before the action returns.
3. `async_preupload`
   Optional later mode; do not treat it as required for the first implementation.

Recommended first implementation:

1. Implement `before_send` first.
2. `sync_preupload` is optional in the same subtask if it stays well-tested.
3. `async_preupload` can be deferred.

## Cache and retry expectations

Stage 2 upload-before-send must evolve so the file upload happens only once as long as the uploaded file is still valid.

Required behavior:

1. Resolve the incoming `asset_ref`.
2. Look up cached provider refs for `openai_responses`.
3. If a usable cached OpenAI `file_id` exists, reuse it.
4. If metadata indicates the cached upload is expired, re-upload from the local asset.
5. If no expiry is known, reuse until OpenAI rejects it.
6. If OpenAI rejects the cached ref as missing or expired, retry once by re-uploading from local storage and updating the cache.
7. This same reuse behavior must apply to the existing Stage 2 upload-before-send path so PDFs are not needlessly re-uploaded and reprocessed every time.

## Frontend requirements

### Mobile and desktop upload UX

Both frontends must support background upload initiated immediately after file selection.

Requirements:

1. Upload starts after file selection, before final send.
2. The upload runs in the background through the action path.
3. Mobile should use the same top area that already shows the in-progress indicator for reload/action-related work.
4. Desktop must add a matching top-of-chat indicator with the same capabilities; desktop currently has generic loading/action state but not the same dedicated indicator treatment.
5. Send should be blocked while a selected attachment is still uploading.
6. Draft attachment state should distinguish at least:
   - `local`
   - `uploading_to_server`
   - `stored`
   - `uploading_to_openai`
   - `ready`
   - `failed`
   - `deleting`

### Sent-message attachment previews

Add one missing UX requirement to this follow-up:

1. Frontends need a way to preview attachments when displaying sent messages.
2. A small thumbnail/attachment chip is sufficient, similar to what already exists for inline attachments.
3. This must continue to work when messages carry `asset_ref`-backed attachments rather than inline `data:` URLs.
4. The implementation must ensure there is enough data in stored metadata and message rendering payloads to show a stable preview for sent image/PDF attachments on both mobile and desktop.

### Shared frontend SDK work

Prefer implementing shared action/result helpers in `packages/frontend-sdk` so mobile and desktop do not duplicate upload/delete action contract parsing.

## Refactor requirement

The current `openai_responses` provider contains too much attachment logic. This follow-up must reduce that concentration of logic.

Expected direction:

1. Move attachment parsing/normalization helpers into dedicated modules.
2. Move server-asset reference helpers into dedicated modules.

## Live testing sequence (added during completion)

Implement and verify the remaining live integration coverage in this order before relying on an SDK end-to-end test:

1. Add the optional provider-level real API test for session-asset-backed PDF send so both image and PDF are covered at the provider/core boundary.
2. Add an AgentApplication real API test that executes `store_attachment`, sends a message with the returned `asset_ref`, and verifies provider-ref caching from the local asset store.
3. Add a FastAPI real API test that goes through the generic action endpoint to store an attachment, sends by `asset_ref`, and verifies the full server path with the real OpenAI backend.
4. Add an SDK real-backend real-OpenAI end-to-end test that uses the frontend SDK attachment helper against the live FastAPI server and real OpenAI API.

Execution notes:

1. Keep the provider/core, AgentApplication, FastAPI, and SDK tests isolated so failures can be attributed to the correct moving part.
2. Use generated local image/PDF fixtures where practical so the tests stay self-contained.
3. Load `OPENAI_API_KEY` from the repo root `.env` for the live tests when the surrounding test harness does not already do so.
4. Minor issues found while implementing or running these tests may be corrected in the same change; pause only for major design issues or significant architectural surprises.

## Live integration completion notes (added during completion)

Completed the staged live coverage in the planned order:

1. Added the optional provider/core real API test for session-asset-backed PDF send in `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`.
2. Added an AgentApplication real API test for `store_attachment` plus send-by-`asset_ref` in `plugins/openai_responses/tests/test_agent_application_openai_responses_attachments.py`.
3. Added a FastAPI real API test for `/actions` store plus `/messages` and `/send` by `asset_ref` in `application/python/tests/test_openai_responses_attachment_action_flow_real_api.py`.
4. Added an SDK real-backend real-OpenAI end-to-end test in `packages/frontend-sdk/src/integration/__tests__/backend.openai.integration.test.ts` using `storeSessionAttachment(...)`, a real spawned FastAPI backend, and the `openai_responses` plugin loaded via a local-path plugin spec.

Minor follow-up fixed during testing:

1. Registered `integration` and `openai` pytest markers in `application/python/pyproject.toml` so the new FastAPI live test does not emit unknown-mark warnings.

Tests run:

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q -k session_asset_pdf_real_api` -> `1 passed, 8 deselected`
2. `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_attachments.py -q` -> `1 passed`
3. `pytest application/python/tests/test_openai_responses_attachment_action_flow_real_api.py -q` -> `1 passed`
4. `npm test -- --run src/integration/__tests__/backend.openai.integration.test.ts` in `packages/frontend-sdk` with `RUN_BACKEND_OPENAI_INTEGRATION=1` -> `1 passed`
5. `git diff --check` -> clean

Notable implementation details:

1. The SDK live test explicitly loads `OPENAI_API_KEY` and optional `OPENAI_BASE_URL` from the repo root `.env` when they are not already present in the environment.
2. The spawned SDK backend loads `openai_responses` through the application plugin manager using a local-path plugin spec (`path:<repo>/plugins/openai_responses`) so the test does not depend on ambient Python import path configuration.
3. Generated local fixtures were used where practical to keep the live tests self-contained and avoid network dependencies for assets.
3. Move OpenAI file-cache/upload/retry helpers into dedicated modules.
4. Keep the provider focused on orchestrating request conversion and API execution.

It is acceptable for this refactor to happen incrementally as long as each stage leaves tests green and the boundaries are moving in the right direction.

## Suggested staging

This task includes all of the above changes, but it may be implemented in stages rather than as one large landing. If staged, each stage must include tests.

Suggested execution order:

### Stage A: server-owned asset repository + provider/extension contract

1. Add application-owned session asset storage.
2. Add attachment extension actions for storing and deleting assets.
3. Add shared helper modules and begin refactoring provider attachment logic out of the main provider file.
4. Add unit tests for asset repository and action validation.

### Stage B: provider send-path resolution from `asset_ref`

1. Teach the provider to resolve `asset_ref` payloads.
2. Add OpenAI upload cache reuse and retry-on-expired/missing behavior.
3. Update Stage 2 upload-before-send logic to use the same cache/reupload path.
4. Add provider unit tests, replay/native-history tests, and integration tests.

### Stage C: frontend upload and delete flow

1. Add shared frontend SDK helpers for upload/delete actions.
2. Update mobile and desktop to upload immediately after file selection.
3. Replace inline draft payloads with `asset_ref` after successful upload.
4. Add upload-progress indicators in the top-of-chat status area for both frontends.
5. Add tests for shared SDK helpers and frontend behavior where the repo already has good test seams.

### Stage D: sent-message previews and final end-to-end polish

1. Ensure sent messages render attachment previews from `asset_ref`-backed attachments.
2. Preserve enough server-side metadata and provider-native replay metadata for those previews to survive reload/slice/fork.
3. Add end-to-end/regression coverage for the final action-driven workflow.

## Acceptance criteria

1. The application stores original attachment bytes locally in a per-session asset store.
2. Upload actions return stable server-owned asset references.
3. Final chat requests use `asset_ref` after upload instead of continuing to depend on inline base64/data URLs.
4. The provider reuses cached OpenAI uploads when valid and re-uploads from local storage when they expire or are rejected.
5. The existing upload-before-send path is updated so repeated sends do not re-upload unnecessarily when a valid cached OpenAI file already exists.
6. Attachment deletion is supported for uploaded drafts.
7. Mobile and desktop both support background upload UX with clear in-progress and failure states.
8. Sent messages display stable attachment previews/chips for image/PDF attachments.
9. Attachment logic in `openai_responses_provider.py` is reduced through helper extraction or movement into the attachment extension where appropriate.
10. Every implemented stage lands with tests in the same change.

## Key repo references for the implementing agent

Application/session persistence:

- `core/python/agent_app/sessions.py`
- `core/python/agent_app/application_future.py`

Server action plumbing:

- `application/python/agent_terminal_app/server.py`

Current attachment provider/extension code:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachments_extension.py`

Current mobile composer attachment flow:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/attachmentPicking.ts`

Current desktop composer attachment flow:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Shared frontend action runner/backend layer:

- `packages/frontend-sdk/src/plugins/actionRunner.ts`
- `packages/frontend-sdk/src/backend/backend.ts`
- `packages/frontend-sdk/src/backend/restBackend.ts`

## Environment reminder

1. Use `OPENAI_API_KEY` from the repo root `.env` for any guarded integration tests.
2. Do not hardcode API keys in code, tests, docs, or task completion notes.

## Approved execution plan (added during completion)

1. Add an application-owned session asset store first.
   Introduce a small asset repository in `core/python/agent_app`, backed by a real per-session filesystem layout. This is the foundation for the rest of the work and stops OpenAI from being treated as the durable attachment store.

2. Add provider-extension attachment actions next.
   Extend `openai_responses_attachments` with `store_attachment` and `delete_attachment` actions that validate one-file upload input, persist to the application-owned asset store, return a stable `asset_ref`, and support unsent draft deletion.

3. Refactor provider attachment logic into helpers before adding more behavior.
   As later stages proceed, extract attachment parsing, `asset_ref` handling, and OpenAI file-cache logic into dedicated helper modules so the provider remains orchestration-focused.

4. Teach the provider send path to consume `asset_ref`.
   In later stages, update the provider so action-driven `asset_ref` attachments and the existing Stage 2 `upload_before_send` path go through the same reuse/reupload flow.

5. Add endpoint/API integration coverage before frontend wiring.
   Once the backend contract exists, cover generic `/actions` usage and send/append flows using `asset_ref` in application/server tests.

6. Add a shared frontend SDK helper.
   Introduce typed helpers in `packages/frontend-sdk` for storing and deleting attachment assets through the generic action endpoint.

7. Update mobile upload UX.
   After the backend contract is stable, update the mobile chat composer to upload immediately after file selection, replace raw drafts with `asset_ref`, block send while uploads are active, and surface upload state in the existing top status area.

8. Update desktop upload UX.
   Mirror the mobile flow in the desktop chat pane, including a matching top-of-chat status indicator and send blocking while uploads are active.

9. Preserve sent-message preview continuity.
   Ensure both frontends continue to render small thumbnails/chips for sent image/PDF attachments after requests switch to `asset_ref`-backed attachments.

### Planned verification

1. Asset repository unit tests for store/load/delete, manifest contents, session isolation, and invalid payload handling.
2. Attachment extension unit tests for action definitions, validation, `asset_ref` return shape, and deletion behavior.
3. Provider helper/unit tests in later stages for `asset_ref` resolution, OpenAI upload reuse, stale-cache refresh, and request conversion.
4. Native-history regression tests in later stages for reload/slice/fork continuity and preview metadata survival.
5. Application/server endpoint tests for `/actions` store/delete and later send/append flows using `asset_ref`.
6. Frontend SDK tests for typed upload/delete action result parsing.
7. Mobile/desktop tests where practical for upload state, send blocking, and preview rendering.
8. Guarded live OpenAI integration tests in later stages using generated image/PDF assets and `OPENAI_API_KEY` from the repo root `.env`.

## Stage 1 completion notes (added during completion)

Stage 1 landed the backend foundation only:

1. Added an application-owned filesystem session asset store in `core/python/agent_app/session_assets.py`.
2. Wired `AgentApplication` to create that asset store next to the session store and pass it into provider-extension session actions through action context.
3. Added `store_attachment` and `delete_attachment` session actions to `openai_responses_attachments`.
4. `store_attachment` now persists a single image/PDF asset locally, returns a stable `asset_ref`, and records a lightweight `session_assets` index in session metadata.
5. `delete_attachment` removes the local stored asset and updates the session metadata index.

Files touched:

1. `core/python/agent_app/session_assets.py`
2. `core/python/agent_app/application_future.py`
3. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachments_extension.py`
4. `core/python/tests/test_session_assets.py`
5. `plugins/openai_responses/tests/test_openai_responses_attachments_extension_unit.py`
6. `application/python/tests/test_openai_responses_attachment_actions_endpoints.py`

Tests run:

1. `pytest core/python/tests/test_session_assets.py -q` -> `3 passed`
2. `pytest plugins/openai_responses/tests/test_openai_responses_attachments_extension_unit.py -q` -> `8 passed`
3. `pytest application/python/tests/test_openai_responses_attachment_actions_endpoints.py -q` -> `1 passed`

Current intentional limits after Stage 1:

1. The provider send path does not consume `asset_ref` yet.
2. OpenAI-side upload caching/reupload logic is still in the provider and has not been refactored into helper modules yet.
3. Mobile/desktop background upload UX and sent-message attachment preview continuity are still pending later stages.

## Stage 2 completion notes (added during completion)

Stage 2 landed the backend `asset_ref` send path and local-asset-backed OpenAI upload reuse:

1. Added `openai_responses_attachment_assets.py` to centralize session-asset-ref parsing plus OpenAI provider-ref merging/reuse checks.
2. Decorated effective runtime request configs with the application-owned session asset store so provider send/add-message flows can resolve `asset_ref` attachments without changing the public API.
3. Updated the `openai_responses` provider so image/PDF `multipartContent` parts with `content.asset_ref` resolve against the local session asset store and normalize into the same native inline shapes used by the existing attachment path.
4. Extended the existing upload-before-send path so it reuses cached OpenAI `file_id` references from the local asset manifest, updates the manifest after fresh uploads, and retries once with re-upload if OpenAI rejects a stale cached file reference.
5. Preserved native-history replay by continuing to keep original multipart attachment source entries in `_openai_responses_attachment_sources`, which now round-trip `asset_ref`-backed attachments correctly.
6. Added an application-level regression test proving the action-store -> add message with `asset_ref` -> send request path works end-to-end and reuses the cached upload on a later request.
7. Added one guarded live OpenAI integration test for an `asset_ref`-backed image attachment stored locally and sent through the real Responses API.

Files touched:

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachment_assets.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
3. `core/python/agent_app/application_future.py`
4. `application/python/agent_terminal_app/server.py`
5. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
6. `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
7. `application/python/tests/test_openai_responses_session_asset_send_path.py`
8. `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`

Tests run:

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q` -> `54 passed`
2. `pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q` -> `6 passed`
3. `pytest application/python/tests/test_openai_responses_attachment_actions_endpoints.py -q` -> `1 passed`
4. `pytest application/python/tests/test_openai_responses_session_asset_send_path.py -q` -> `1 passed`
5. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q -k session_asset_image_real_api` -> `1 passed, 7 deselected`

Current intentional limits after Stage 2:

1. The OpenAI file-cache / asset-resolution logic is still partially inside `openai_responses_provider.py`; a later cleanup pass should move more of that orchestration into dedicated helpers.
2. Mobile and desktop still use inline composer attachments; background upload UX, send blocking, and sent-message preview continuity for `asset_ref` attachments are still pending.
3. There is not yet a dedicated server/frontend asset preview endpoint for rendering thumbnails of stored attachments in sent messages.

## Stage 3 completion notes (added during completion)

Stage 3 landed the shared frontend upload/delete helper plus composer-side background storage flows on mobile and desktop:

1. Added `packages/frontend-sdk/src/plugins/attachmentActions.ts` with typed helpers for `store_attachment` and `delete_attachment`, shared action constants, `session_asset` result validation, and a small `selectSessionAssetId(...)` helper for composer cleanup paths.
2. Exported those helpers from `packages/frontend-sdk/src/index.ts` and added focused Vitest coverage for action request shaping, data-URL base64 extraction, error surfacing, and `asset_ref` extraction.
3. Updated the mobile composer in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` so local file picks now call `store_attachment` immediately in the background, then add an `asset_ref`-backed draft instead of sending inline base64 content. URL-based image attachments still stay direct-send.
4. Added mobile send/append blocking while attachment uploads or deletions are in progress, surfaced upload/delete status in the existing top loading banner, and wired unsent draft removal plus metadata-dialog cancel to `delete_attachment` for stored assets.
5. Updated the desktop chat composer in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` with the same action-driven storage flow for picked files, the same send/append blocking rules, a matching top-of-chat loading row, and unsent draft deletion cleanup.
6. Extended both attachment thumbnail strip components to accept a local-only `previewUrl` so freshly picked image drafts can still render thumbnails in the composer even after their request payload switches to `asset_ref`.

Files touched:

1. `packages/frontend-sdk/src/plugins/attachmentActions.ts`
2. `packages/frontend-sdk/src/plugins/__tests__/attachmentActions.test.ts`
3. `packages/frontend-sdk/src/index.ts`
4. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
5. `mobile/crystal-lattice-control-rn/src/components/AttachmentThumbnailStrip.tsx`
6. `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
7. `desktop/crystal-lattice-control-desktop-rn/src/chat/AttachmentThumbnailStrip.tsx`

Tests and verification run:

1. `npm test -- --run src/plugins/__tests__/attachmentActions.test.ts src/plugins/__tests__/actionRunner.test.ts` in `packages/frontend-sdk` -> `9 passed`
2. `npm test -- --run src/plugins/__tests__/attachmentActions.test.ts` in `packages/frontend-sdk` -> `4 passed`
3. `git diff --check` -> clean
4. `npx eslint src/chat/ChatPane.tsx src/chat/AttachmentThumbnailStrip.tsx` in `desktop/crystal-lattice-control-desktop-rn` -> no errors, 2 pre-existing `no-shadow` warnings in `ChatPane.tsx`
5. `npm run tsc -- --noEmit` in `mobile/crystal-lattice-control-rn` -> blocked by pre-existing `ApiMessage` cast errors in `src/components/MessageBubble.tsx` and `@crystal-lattice/frontend-sdk/src/chat/presentation.ts`, not by the new upload flow changes
6. `npx tsc --noEmit` in `desktop/crystal-lattice-control-desktop-rn` -> blocked by the same pre-existing `ApiMessage` cast error in `@crystal-lattice/frontend-sdk/src/chat/presentation.ts`

Current intentional limits after Stage 3:

1. Sent-message preview continuity is only partial: composer drafts preserve local image thumbnails via `previewUrl`, but there is still no dedicated server asset-preview endpoint for reloaded/sent `asset_ref` attachments.
2. Mobile and desktop currently perform draft cleanup on metadata-cancel/delete, but sent attachments still rely on later stages for any broader post-send asset lifecycle UX.
3. The pre-existing TypeScript cast errors in frontend message rendering remain and still block whole-app typecheck runs unrelated to this stage.
# OpenAI Image/PDF Upload And Upload Modes

Short description: Add staged attachment support for `openai_responses`, starting with image input and cache-conscious URL handling, then adding config-gated server-side upload for image/PDF, and finally exposing upload through provider-extension actions wired into server/frontend flows.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`
- `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`
- `tasks/20260310-openai-responses-provider/120-model-discovery-provider-ui-and-doc-followup.md`

## Task family rule

This task is expected to be completed in stages. The implementing agent may create follow-up subtasks in this task family using slots `141+` when making design decisions or splitting execution by stage, provided those subtasks preserve the architecture boundaries defined here.

Expected examples if the work is split during implementation:

1. `141`: Stage 1 image URL support and caching decision
2. `142`: Stage 2 config-gated upload-before-send for image/PDF
3. `143`: Stage 3 provider-extension upload action integration tests
4. `144`: Stage 3 server/frontend action wiring

Do not feel obligated to create all of these up front; create them only when they improve execution clarity.

## Goals

1. Add real image attachment support to `openai_responses`.
2. Add real PDF attachment support, but only in the upload-before-send path.
3. Support two upload modes over time:
- direct send using request content items
- upload-before-send using OpenAI file upload APIs
4. Expose upload as an action-based workflow only after provider/extension integration is already proven.
5. Keep provider and extension responsibilities aligned with the parent task's architecture boundaries.

## Architecture boundaries (locked)

1. Provider remains transport/native-history/request-execution focused.
- provider may convert core `multipartContent` into OpenAI Responses-native `input_*` items
- provider may perform upload work during the actual long-running send path when config/policy says to do so
- provider must preserve native-history replay correctness across turns, reloads, slice/fork, and tool-loop continuity

2. Extension owns policy/UI/action behavior.
- whether upload-before-send is enabled belongs in provider-extension-owned config/request shaping
- action definitions and `execute_action(...)` belong in the provider extension layer
- frontend/server-visible upload mode toggles should come from extension or provider UI, not ad hoc route logic

3. `initialize_request(...)` must remain short-running.
- do not perform network file uploads inside `initialize_request(...)`
- long-running upload-before-send work must happen in the actual request/send path, where long-running provider work already exists

4. Respect existing separation of concerns.
- tools stay in tools extension
- reasoning stays in reasoning extension
- usage stays in usage extension
- verbosity stays in verbosity extension
- this task must not use attachment support as a reason to move domain logic into the provider

## Current repo context from investigation

1. Core/server/frontend attachment plumbing already exists.
- core messages support `multipartContent`
- server append endpoint accepts `multipartContent`
- mobile attachment UI already supports both image and PDF picking

Key references:

- `core/python/agent_core/types.py`
- `application/python/agent_terminal_app/server.py`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/attachmentPicking.ts`

2. Mobile currently sends attachments as JSON-friendly payloads.
- for picked local assets, frontend currently sends `content.url` as a `data:` URL
- frontend also includes `mime_type` and `filename`
- this is important because Stage 2 intentionally keeps frontend behavior unchanged while the provider/provider-extension add upload-before-send behavior server-side

3. Existing provider support in this repo is image-only.
- `openrouter` and `openrouter_responses` both convert image multipart content into provider-native multimodal items
- neither currently implements real PDF provider send support
- `openai_responses` currently converts only image multipart parts and exposes no attachment UI yet

Key references:

- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openrouter/tests/test_openrouter_provider_multipart_conversion_unit.py`
- `plugins/openrouter_responses/tests/test_openrouter_provider_multipart_conversion_unit.py`

4. PDF already exists in generic UI examples but not as working provider behavior.
- `plugins/openrouter/src/openrouter_plugins/attachment_plugin_sample.py` includes a PDF attachment example labeled UI-only

## OpenAI Responses/API requirements to treat as implementation input

The implementing agent should not need to re-discover the basic OpenAI attachment surface. The following requirements have already been collected from the installed OpenAI SDK type surface and should be treated as the starting contract to implement against.

### Responses input item types

OpenAI Responses request content supports these relevant item types:

1. `input_text`
2. `input_image`
3. `input_file`

### `input_image` requirements

`input_image` supports these relevant fields:

1. `type: "input_image"`
2. `image_url`
- may be a fully qualified URL
- may be a base64 image encoded as a `data:` URL
3. `file_id`
4. `detail`
- allowed values: `low`, `high`, `auto`, `original`

Implication for this task:

1. Stage 1 may use URL-based image sending without requiring file upload first.
2. Uploaded-file-based image sending is also possible later through `file_id`.

### `input_file` requirements

`input_file` supports these relevant fields:

1. `type: "input_file"`
2. `file_data`
- base64-encoded file content
3. `file_id`
4. `file_url`
5. `filename`
6. `detail`
- allowed values: `low`, `high`

Implication for this task:

1. PDF support should use `input_file`.
2. When sending file content directly, `filename` must be preserved.
3. Uploaded-file-based sending can use `file_id`.

### Files API requirements

The OpenAI SDK exposes file upload via `client.files.create(...)`.

Relevant constraints captured during investigation:

1. Upload is performed through the Files API, not the Responses call itself.
2. Supported `purpose` values include at least:
- `vision`
- `user_data`
3. The provider can therefore upload a file first and then reference it from the Responses request using `file_id`.

### Responses request execution surface

1. Non-streaming and streaming both use `client.responses.create(...)`.
2. Attachment changes must not break existing support for:
- streaming
- non-streaming
- tool-loop continuity
- native-history retention
- previous-response/native replay flows

## Required documentation check during implementation

The implementing agent should still verify the following against current OpenAI documentation during implementation and record the result in completion notes, because this is the product/behavior question that matters most for Stage 1 and Stage 2:

1. What OpenAI recommends for cache-friendly repeated image/file inputs.
- specifically, whether stable external URLs or uploaded file references are recommended over inline `data:` URLs for better prompt/request caching or reuse behavior

2. Any documented caveats for `data:` URLs versus uploaded files.
- request size considerations
- reuse/caching implications
- PDF/file-specific guidance

3. Whether OpenAI documentation distinguishes the recommended path for:
- image inputs
- PDF/file inputs

If the docs are ambiguous, the implementing agent must say so explicitly and choose the most conservative behavior rather than claiming stronger caching guarantees than documented.

## Stage plan (locked)

### Stage 1: Image support first, URL-oriented send path only

Scope:

1. Add image attachment support for `openai_responses` using the direct send path.
2. Focus on URL-oriented `input_image` handling first.
3. Research and document which image representation is most compatible with OpenAI caching guidance.

Stage 1 implementation expectations:

1. `openai_responses` provider accepts image multipart content and maps it to `input_image`.
2. The implementing agent must decide and document the preferred Stage 1 image representation for cache-friendly behavior.
3. The decision must explicitly compare at least:
- external URL
- inline `data:` URL
- uploaded file reference as a possible later-stage alternative
4. Stage 1 should not yet add server/frontend action workflow changes.
5. Stage 1 should not yet add PDF support.

Stage 1 acceptance criteria:

1. Image-bearing requests succeed through `openai_responses`.
2. The task completion notes document the OpenAI caching/reuse recommendation that drove the chosen Stage 1 behavior.
3. Unit tests cover image conversion.
4. Guarded integration tests cover at least one real image path.

### Stage 2: Config-gated upload-before-send, plus PDF support

Scope:

1. Add a config-controlled mode that uploads attachment data server-side before the request is sent to OpenAI.
2. Keep frontend behavior unchanged in this stage.
3. Add PDF support in this stage.

Stage 2 implementation expectations:

1. Frontend still sends attachments as `data:` URLs and related JSON metadata.
2. Provider extension owns the config/policy that enables upload-before-send.
3. Provider performs the actual upload work during the long-running request path, not in `initialize_request(...)`.
4. After upload, provider sends the Responses request using the uploaded reference shape required by OpenAI.
5. PDF support is added through `input_file`, using the OpenAI-supported direct fields or uploaded-file reference path as appropriate.

Stage 2 acceptance criteria:

1. There is a documented config to enable upload-before-send mode.
2. In that mode, image inputs are uploaded first and then sent using the OpenAI-supported uploaded reference path.
3. In that mode, PDF inputs are supported.
4. `initialize_request(...)` remains short-running and does not upload.
5. Streaming and non-streaming requests both continue to work.
6. Native-history replay remains correct after upload-before-send requests.
7. Integration tests cover image and PDF in upload-before-send mode.

### Stage 3: Upload through provider-extension actions, then server/frontend wiring

Scope:

1. Expose upload as an explicit provider-extension action path.
2. Prove the action-based upload flow in provider/extension integration tests first.
3. Only after that, wire server/frontend to use the action.

Stage 3 implementation expectations:

1. Provider extension exposes upload-related action definitions.
2. Provider extension `execute_action(...)` performs the potentially long-running upload work.
3. Provider/extension integration tests prove that action-produced upload results can be consumed by the provider send path.
4. Only after the integration proof exists should server and frontend be updated.
5. Server/frontend should then be able to use the upload action instead of only sending raw `data:` URLs through to the provider.

Stage 3 acceptance criteria:

1. Action-based upload is integration-tested at the provider/extension layer before route/UI work lands.
2. Server action execution supports the extension action path.
3. Frontend can invoke the upload action for attachments.
4. End-to-end tests cover the final action-driven workflow.

## Detailed implementation requirements

1. Preserve current frontend payload compatibility.
- Stage 1 and Stage 2 must accept the current mobile/server multipart payload shapes already used in the repo
- do not require frontend payload redesign before attachment support works

2. Preserve native-history ownership.
- if uploaded references replace inline content in provider-native history, replay/slice/fork behavior must still remain coherent
- if the core-visible message cannot fully reconstruct the uploaded file reference, native indices/ownership must still preserve future replay correctness

3. Be explicit about how core multipart parts map to OpenAI-native items.

Expected minimum mapping decisions to document/implement:

1. image part -> `input_image`
2. pdf part -> `input_file`
3. direct data payload handling
- how `content.url` data URLs are parsed
- whether generic `data_base64` + `mime_type` is also accepted for parity with other providers
4. uploaded reference handling
- whether the provider stores `file_id`, `file_url`, or both in native history/internal metadata

4. Provider UI/action exposure should be consistent with existing UI patterns.
- attachment UI elements should use the existing `composer_attachment` pattern when exposed from provider/provider-extension UI
- action wiring should use the existing provider-extension session-action/action infrastructure patterns already present in the repo

## Test expectations

### Unit tests

1. Image conversion tests.
- direct image URL
- image `data:` URL
- any supported base64 helper shape

2. PDF conversion tests.
- direct file URL if supported in chosen stage
- `data:` URL / extracted base64 path
- filename preservation

3. Upload-before-send request tests.
- upload is triggered only when enabled
- upload is not attempted in `initialize_request(...)`
- provider request uses uploaded reference shape after upload succeeds

4. Native-history regression tests.
- multi-turn continuity after image requests
- multi-turn continuity after PDF/upload requests
- slice/fork/reload safety where attachment-bearing turns are present

5. Extension action tests for Stage 3.
- action definition exposure
- `execute_action(...)` happy path
- action result shape compatibility with provider send path

### Integration tests

1. Stage 1 provider integration for image support.
2. Stage 2 provider integration for upload-before-send image support.
3. Stage 2 provider integration for upload-before-send PDF support.
4. Stage 3 provider/extension integration proving action-driven upload before any server/frontend changes.

Integration tests should:

1. be guarded by `OPENAI_API_KEY`
2. allow model override via env var when model capability is relevant
3. skip cleanly when required credentials or suitable model configuration are missing

### End-to-end tests

Only after Stage 3 provider/extension integration is already working:

1. server action execution tests
2. frontend or HTTP flow tests for action-driven upload
3. final end-to-end regression test proving the upload action path actually improves the user flow without breaking request send behavior

## Risks and non-goals

### Risks

1. Caching guidance may be underspecified.
- do not overstate what OpenAI guarantees if docs are ambiguous

2. Uploaded-file lifecycle may introduce retention/cleanup questions.
- if additional cleanup policy is needed, document it and split it into a follow-up subtask rather than burying it in provider logic

3. Model support may vary.
- PDF/file input support may not behave identically across all candidate models
- tests must avoid brittle assumptions about a single hardcoded model unless explicitly documented

4. Architecture drift is easy here.
- upload policy can easily leak into provider core if the split between extension policy and provider execution is not enforced carefully

### Non-goals

1. Do not redesign generic multipart core/server payloads for this task.
2. Do not move tools/reasoning/usage/verbosity into the provider.
3. Do not require frontend changes before Stage 3.
4. Do not implement speculative asset lifecycle/storage systems unless a concrete need emerges during implementation.

## Recommended execution order

1. Complete Stage 1 first and record the caching decision clearly.
2. Split Stage 2 into a dedicated follow-up subtask if upload-before-send policy or native-history handling becomes non-trivial.
3. Before touching server/frontend in Stage 3, create and pass provider/extension integration coverage for the action flow.
4. Only then implement server and frontend action wiring.

## References

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`
- `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `plugins/openrouter/src/openrouter_plugins/attachment_plugin_sample.py`
- `mobile/crystal-lattice-control-rn/src/attachmentPicking.ts`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `application/python/agent_terminal_app/server.py`
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/050-provider-mapping-multipartcontent.md`
- `tasks/20260215-multipart-upload/090-asset-prepare-upload-action.md`
- `tasks/20260312-provider-extension-session-actions/000-main.md`

## Approved plan (added during completion)

1. Complete this subtask as Stage 1 only.
- Keep `140` limited to direct-send image attachment support and the required caching-guidance documentation.
- Defer Stage 2 upload-before-send, PDF support, and Stage 3 action wiring to follow-up `141+` subtasks instead of broadening provider scope here.

2. Tighten provider-side direct image conversion in `openai_responses`.
- Update `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` so Stage 1 image handling explicitly supports:
  - `multipartContent[].content.url` with `http(s)` image URLs
  - `multipartContent[].content.url` with `data:image/...` URLs from the existing mobile flow
  - `multipartContent[].content.data_base64` plus `mime_type`, converted into a `data:` URL for parity with existing provider behavior elsewhere in the repo
- Keep the provider transport/native-history focused and do not add PDF, file-upload, or action logic in this step.

3. Add tests in the same change.
- Expand `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` with coverage for direct image URL conversion, `data:image/...` URL pass-through, `data_base64` plus `mime_type` conversion, and provider-native back-conversion preserving image attachments in `multipartContent`.
- Add one guarded integration test in `plugins/openai_responses/tests/test_openai_responses_provider_integration.py` that sends a real image-bearing request through `AgentCore` using `OPENAI_API_KEY` from the repo root `.env`.

4. Verify and document the Stage 1 caching/reuse guidance.
- Check current OpenAI documentation, if reachable from this environment, for recommendations comparing external URLs, inline `data:` URLs, and uploaded-file references for repeated image/file inputs.
- Record the result conservatively in completion notes and avoid claiming stronger caching guarantees than the documentation actually supports.

5. Update narrow bundle docs for the implemented Stage 1 behavior.
- Refresh `plugins/openai_responses/README.md` so it documents direct-send image attachment support and clearly states that PDF/upload-before-send/action workflows remain staged follow-up work.

6. Verify with focused test runs, append completion notes, and stop after this one subtask.

## Completion notes (added during completion)

### What changed

1. Completed `140` as Stage 1 only.
- Kept this subtask limited to direct-send image attachment support in the provider.
- Did not implement PDF handling, upload-before-send, or provider-extension action wiring in this change.

2. Tightened direct image conversion in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.
- Added explicit provider-side handling for image multipart parts using:
  - `content.url` with external image URLs
  - `content.url` with `data:image/...` URLs from the existing mobile flow
  - `content.data_base64` plus `mime_type`, converted into a `data:` URL before send
- Added validation errors for malformed image parts so bad payloads fail clearly instead of being silently ignored.

3. Added Stage 1 test coverage.
- Expanded `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` with unit tests for:
  - direct image URL conversion
  - `data:image/...` URL pass-through
  - `data_base64` plus `mime_type` conversion
  - malformed image payload rejection
  - provider-native back-conversion preserving image `multipartContent`
- Added a guarded real-API integration test in `plugins/openai_responses/tests/test_openai_responses_provider_integration.py` that sends a message with one image attachment using a small inline `data:image/gif` payload.
- Added a second guarded real-API integration test in `plugins/openai_responses/tests/test_openai_responses_provider_integration.py` that generates a local red PNG with ImageMagick, converts it to a `data:image/png` URL, and verifies the model recognizes the image content.
- The image integration test allows model override through `OPENAI_RESPONSES_VISION_MODEL` and otherwise defaults to `gpt-5-mini`.

4. Updated docs for the implemented Stage 1 behavior.
- Updated `plugins/openai_responses/README.md` to document direct-send image attachment support and to state clearly that PDF/upload-before-send/action workflows remain follow-up work.

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
3. `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`
4. `plugins/openai_responses/README.md`
5. `tasks/20260310-openai-responses-provider/140-openai-image-pdf-upload-and-upload-modes.md`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `39 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`
- result: `5 passed`

### OpenAI documentation verification result

1. Attempted to verify the current OpenAI image/file guidance directly from this environment via `https://platform.openai.com/docs/guides/images`.
- result: the docs page was blocked by a Cloudflare challenge in this terminal environment, so a direct documentation review was not possible here.

2. Conservative conclusion used for Stage 1.
- The OpenAI SDK surface and the task's pre-collected investigation notes confirm that `input_image.image_url` accepts both external URLs and base64 `data:` URLs.
- Because the current docs could not be directly reviewed from this environment, this change does **not** claim that inline `data:` URLs are cache-friendly or preferable for repeated reuse.
- Stage 1 therefore keeps compatibility-first direct-send image support for the existing frontend payloads, while leaving any stronger cache-optimized recommendation to the later upload-before-send follow-up work.

### Outcomes

1. `openai_responses` now explicitly supports the repo's current direct image attachment payload shapes, including `data_base64` plus `mime_type`.
2. Real API coverage confirms that an image-bearing request succeeds through the OpenAI Responses provider.
3. Provider scope remains transport/native-history focused; no upload policy, PDF logic, or action behavior was moved into the provider in this subtask.

### Open issues

1. Stage 2 remains open by design: config-gated upload-before-send and PDF support were not implemented in this subtask.
2. Stage 3 remains open by design: provider-extension upload actions and server/frontend wiring were not implemented in this subtask.
# Message Export Actions

Add two application-plugin-backed message actions: `Send to Kindle` and `Share as PDF`, reusing the existing Kindle SMTP config contract and extending the action follow-up/download path so mobile can show share options and desktop can show a save dialog.

## Requirements checklist

- [x] Add application plugin support for a `Send to Kindle` message action.
- [x] Add application plugin support for a `Share as PDF` message action.
- [x] Add session actions for both Kindle and PDF exports.
- [x] Add a config key for PDF engine selection with `auto`, `pandoc`, and `xhtml2pdf` modes.
- [x] Reuse the existing agent-level Kindle config keys:
  - `send_to_kindle_smtp_user`
  - `send_to_kindle_from_addr`
  - `send_to_kindle_default_to`
  - `send_to_kindle_keychain_service`
- [x] `Send to Kindle` should prompt only for `title`, and derive the EPUB filename from that title.
- [x] Make `Send to Kindle` title optional and use the same defaulting pattern as PDF exports.
- [x] `Share as PDF` should prompt for optional `title` and optional `filename`, and generate defaults when omitted.
- [x] Session export should include user messages and assistant messages with text content, while excluding tool and system messages.
- [x] Session export should add a top-level `H1` and per-message `H2` headings, and demote message-local headings to start at `H3`.
- [x] Generated PDFs should be delivered through a frontend flow that opens share options on mobile and a save dialog on desktop.
- [x] Reuse existing file-transfer and session-asset infrastructure where possible instead of inventing a second binary-delivery path.
- [x] Document runtime dependencies for export/conversion clearly, especially PDF conversion dependencies.
- [x] Keep the current plugin loader/install flow unchanged.
- [x] Add `xhtml2pdf` as a static Python dependency of the new export plugin.
- [x] Add backend and frontend tests that cover action discovery, dialog submission, generated output delivery, and host-specific share/save behavior.

## Purpose

This task adds two user-facing export actions to the chat UI as application plugins:

- `Send to Kindle`
- `Share as PDF`

The actions should appear as plugin-backed `message_action` entries in the session chat UI and should work off a selected message, not the whole session.

The goal is to keep the feature aligned with the platform’s current action model:

- application plugins define actions and UI elements
- the frontend shows an optional form dialog
- the backend executes the action with validated params
- the action can return a standardized `display` payload with follow-up actions

## Current state and relevant code

### Action system

- Application plugins are defined through the application-layer protocol in `core/python/agent_app/app_plugins.py`.
- Application actions are enumerated and executed in `core/python/agent_app/application_future.py`.
- The HTTP endpoint for executing actions is `POST /actions` in `application/python/agent_terminal_app/server.py`.
- Frontend action execution is handled in `packages/frontend-sdk/src/plugins/actionRunner.ts`.

### Session/message action UI

- Application plugin state is loaded into frontend registries in `packages/frontend-sdk-react/src/applicationPlugins.tsx`.
- Session-scoped application UI comes from `GET /sessions/{session_id}/application/ui-schema` in `application/python/agent_terminal_app/server.py`.
- Mobile merges application-provided `message_action` elements into chat actions in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.
- The generic action dialog already supports optional form inputs, prefill, and `submit_empty` semantics in `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`.

### Existing follow-up action/display model

- Action display payloads and follow-up action types live in `packages/frontend-sdk/src/types/plugins.ts`.
- Current follow-up action kinds are:
  - `open_url`
  - `copy_text`
  - `run_action`
- Mobile follow-up handling currently lives in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.

### Existing file download/share/save primitives

- There is already a generic application plugin for downloading stored session assets:
  - `plugins/session-asset-attachments/src/session_asset_attachments/__init__.py`
- Existing mobile attachment flows already:
  - download a stored asset
  - write it to a temp file
  - share it with `react-native-share`
  - save it with `@react-native-documents/picker`
  in `mobile/crystal-lattice-control-rn/src/components/AttachmentViewerHost.tsx`
- `saveDocuments(...)` is already available in the mobile app dependency graph and includes `macos` handling in the installed package sources:
  - `mobile/crystal-lattice-control-rn/node_modules/@react-native-documents/picker/src/saveDocuments.ts`
  - `mobile/crystal-lattice-control-rn/node_modules/@react-native-documents/picker/src/fileTypes.ts`

### Existing Kindle send path

- The current reusable Kindle SMTP tool plugin is:
  - `plugins/bash-send-kindle-icloud/`
- The current config contract is agent-level and already resolved through app config keys:
  - `send_to_kindle_smtp_user`
  - `send_to_kindle_from_addr`
  - `send_to_kindle_default_to`
  - `send_to_kindle_keychain_service`

## Product decisions captured so far

- These should be application plugins, not provider extensions and not ad hoc server endpoints.
- Both are `message_action`s, not `session_action`s.
- `Send to Kindle` should behave like the existing Kindle flow and reuse the same resolved config keys.
- `Send to Kindle` should ask only for a title and derive the filename from that title.
- `Share as PDF` should ask for optional `title` and `filename`.
- `Share as PDF` should generate a sensible fallback filename such as `session-xxxx-message-125.pdf` if no user input is provided.
- Generated files should be treated as transient export artifacts from the selected message.
- For `Share as PDF`, binary delivery should reuse the existing session-asset download path when practical.
- The frontend framework needs one addition: a follow-up action type or equivalent abstraction that means “download this generated file, then use host-appropriate share/save UX.”
- On mobile, the desired behavior is the OS share sheet.
- On desktop, the desired behavior is a save dialog.
- PDF engine selection should be runtime-configurable through a plugin/app config key, not through loader-time conditional dependency installation.
- The plugin loader should remain unchanged.
- `xhtml2pdf` should be included as a static dependency so the Python fallback engine is always available once the plugin is installed.
- `auto` mode should prefer `pandoc` when available on `PATH`, and otherwise fall back to `xhtml2pdf`.

## Recommended architecture

Create one new plugin repo with shared export utilities and two application plugin entries, for example:

- `plugins/message-export-actions/`

Suggested application plugins in that repo:

- `message_send_to_kindle`
- `message_share_as_pdf`

Shared code inside the repo should handle:

- locating the selected message from `session_id` and `message_index`
- rendering export markdown for a single message
- generating normalized titles and filenames
- converting markdown to EPUB or PDF
- temporary file handling

## Proposed action shapes

### `Send to Kindle`

UI element:

- `ui_type: "message_action"`
- label: `Send to Kindle`
- dialog:
  - kind: `form`
  - one required field:
    - `title`

Inputs:

- `session_id`
- `message_index`
- `title`

Behavior:

- render markdown for the target message
- convert to EPUB
- derive filename from title, e.g. `my-export-title.epub`
- send through the existing Kindle SMTP integration using the resolved config keys
- return a success display payload

### `Share as PDF`

UI element:

- `ui_type: "message_action"`
- label: `Share as PDF`
- dialog:
  - kind: `form`
  - optional `title`
  - optional `filename`
  - both should use `submit_empty: true`

Inputs:

- `session_id`
- `message_index`
- `title` optional
- `filename` optional

Behavior:

- render markdown for the target message
- convert to PDF
- normalize the filename, ensuring `.pdf`
- store the resulting PDF in the session asset store
- return an action display payload with a follow-up action that tells the client to download/share/save the generated asset

PDF engine selection should use a config key such as:

- `message_export_pdf_engine`

Supported values:

- `auto`
- `pandoc`
- `xhtml2pdf`

Recommended runtime behavior:

- `auto`: use `pandoc` if available, otherwise use `xhtml2pdf`
- `pandoc`: require `pandoc` and fail clearly if unavailable
- `xhtml2pdf`: force the Python fallback engine

## Needed framework addition

The current `ActionDisplayFollowupAction` model is not enough for generated binary files. A new follow-up action kind should be added in `packages/frontend-sdk/src/types/plugins.ts`, for example:

- `download_attachment_asset`

Suggested fields:

- `kind`
- `id`
- `label`
- `session_id`
- `asset_id`
- `filename`
- `mime_type`
- optional `plugin`
  - default can be `session_asset_attachments`
- optional `behavior`
  - `platform_default`
  - `share`
  - `save`

Recommended behavior for this task:

- `platform_default`
  - mobile: share sheet
  - desktop: save dialog

This keeps host-specific UX on the frontend while reusing the same backend asset/download path.

## Export scope recommendation

For v1, export only the message’s textual content plus lightweight metadata, not full multipart attachments.

Suggested content:

- role
- session id
- message index
- main `content` text
- optionally timestamp if available from metadata

This keeps the first version small and predictable.

## PDF conversion notes

There is no general-purpose PDF export utility in the repo yet.

Observed local/runtime availability in the current development environment:

- `pandoc` is installed
- `pdflatex` and `xelatex` are installed
- `magick` is installed
- `wkhtmltopdf` is not installed
- `weasyprint` is not installed

Recommended initial conversion approach for implementation:

- EPUB: `pandoc`
- PDF:
  - preferred path: `pandoc` with an explicit PDF engine, likely `xelatex` or `pdflatex`
  - fallback path: `xhtml2pdf`

Chosen direction for this task:

- do not change the plugin loader
- add `xhtml2pdf` as a static dependency in the new plugin package
- select the PDF engine at runtime through config

That means installation stays simple and deterministic, while runtime still prefers higher-quality `pandoc` output when it is available.

## Implementation plan

Added during implementation on 2026-05-17.

1. Create a new plugin repo under `plugins/message-export-actions/`.
2. Add two application plugin entries in its `agent_plugin.json`:
   - one for Kindle export
   - one for PDF export
3. Add static Python dependencies for the plugin package, including `xhtml2pdf`.
4. Add a config key for PDF engine selection, e.g. `message_export_pdf_engine`, with supported values `auto`, `pandoc`, and `xhtml2pdf`.
5. Add shared Python utilities in that repo for:
   - loading a session/message by `session_id` and `message_index`
   - rendering a single-message export document in markdown
   - slugifying titles and generating default filenames
   - selecting the PDF engine at runtime
6. Implement the `Send to Kindle` application plugin:
   - define one `message_action`
   - define one action with validated inputs
   - call shared EPUB conversion code
   - call the existing Kindle send logic or a shared send helper compatible with the same config keys
7. Implement the `Share as PDF` application plugin:
   - define one `message_action`
   - define one action with validated inputs
   - call shared PDF conversion code
   - in `auto` mode, prefer `pandoc` when found on `PATH`, otherwise use `xhtml2pdf`
   - in forced-engine modes, fail clearly if the selected engine cannot run
   - store the generated PDF in the session asset store
   - return a display payload with a binary follow-up action
8. Extend `ActionDisplayFollowupAction` in `packages/frontend-sdk/src/types/plugins.ts` with a new generated-file follow-up kind.
9. Update action display handling in the frontend SDK/mobile app to support that new follow-up action kind.
10. Factor reusable file download + temp-file write + share/save behavior out of `mobile/crystal-lattice-control-rn/src/components/AttachmentViewerHost.tsx` into a helper that can be reused by action results.
11. In mobile follow-up handling:
   - use `downloadSessionAttachment(...)`
   - write a temp file
   - on iOS/Android use `Share.open(...)`
   - on desktop/macOS use `saveDocuments(...)`
12. Add backend tests for:
   - UI schema contribution of both `message_action`s
   - action validation
   - title/filename defaulting
   - PDF engine selection behavior
   - PDF asset storage and returned follow-up payload
13. Add frontend tests for:
   - dialog submission
   - new follow-up action handling
   - mobile/desktop behavior branching
14. Document plugin dependencies and export limitations in the new plugin README, including:
   - `xhtml2pdf` is bundled as a static Python dependency
   - `pandoc` is optional but preferred in `auto` mode
   - LaTeX engine requirements for the `pandoc` PDF path

## Testing targets

- Backend:
  - application-plugin loading
  - UI schema exposure via session application UI schema endpoint
  - action execution through `POST /actions`
  - session asset storage/download integration
- Frontend/mobile:
  - dialog rendering and submission
  - follow-up action handling
  - temp-file write + share/save behavior

## Open questions to resolve during implementation

- Whether the Kindle action should invoke the existing bash tool plugin directly or reuse only its underlying Python/email helper logic.
- Whether the generated PDFs should remain stored as session assets indefinitely or be cleaned up as ephemeral export artifacts.
- Whether v1 exports should include markdown rendering of tool messages and multipart parts, or only plain `content`.
- Whether the new follow-up action kind should live only in mobile first or be added generically in the frontend SDK for future web/desktop clients too.

## Completion expectations

Done should include:

- the new application plugins
- frontend support for the generated-file follow-up action
- host-appropriate share/save behavior
- tests
- README/dependency docs for the new export plugin

## Completion Notes

Added during implementation on 2026-05-17.

- Implemented a new plugin package at `plugins/message-export-actions/` with two application plugins:
  - `message_send_to_kindle`
  - `message_share_as_pdf`
- Expanded both plugins to expose session actions in addition to message actions.
- Added shared export utilities for:
  - single-message markdown rendering
  - session transcript markdown rendering
  - heading demotion inside exported message bodies
  - EPUB conversion with `pandoc`
  - PDF conversion with runtime engine selection:
    - `auto`
    - `pandoc`
    - `xhtml2pdf`
- Updated Kindle export so title is optional and EPUB generation now uses bash-tool-aligned defaults for:
  - language
  - TOC
  - TOC depth
  - local-link Lua filtering
- Added a self-contained PDF download action under `message_share_as_pdf` so generated-file follow-up actions do not depend on a separate app plugin being loaded.
- Added a new follow-up action kind in the frontend SDK:
  - `download_attachment_asset`
- Added mobile/desktop generated-file handling:
  - mobile defaults to share sheet
  - desktop/macOS defaults to save dialog
- Reused and extracted local file save/share helpers so the existing attachment viewer and the new generated-file action path share the same primitives.
- Added targeted backend tests in `plugins/message-export-actions/tests/test_message_export_actions.py`.
- Added targeted mobile tests in `mobile/crystal-lattice-control-rn/__tests__/generatedFileActions.test.ts`.
- Verified implementation with:
  - `pytest plugins/message-export-actions/tests -q`
  - `npm test -- --runTestsByPath __tests__/generatedFileActions.test.ts __tests__/AttachmentViewerHost.test.tsx`
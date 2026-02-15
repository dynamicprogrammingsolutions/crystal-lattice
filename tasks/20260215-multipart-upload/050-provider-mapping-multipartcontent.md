# Providers: Map `{content, multipartContent}` to/from provider-native formats (+ OpenRouter integration test)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Implement provider/plugin logic to assemble the core message fields (`content`, `multipartContent`) into provider-native message content structures, and split them back during `from_native_messages`. Back the implementation with an OpenRouter integration test.

Note: exact provider-native schemas and sample code will be provided when completing the task; implement the plumbing and test harness to match those samples.

## Depends On

- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`

## Current State

- Providers typically implement `to_native_messages` as `{role, content}` only.
  - Example: `core/python/plugins/openrouter_provider.py`.
- OpenRouter integration tests already exist and are gated by `OPENROUTER_API_KEY`.
  - Example: `core/python/tests/test_openrouter_basic_integration.py`.

## Requirements

- In `to_native_messages`:
  - Treat `content` (string) as main text (may be empty string).
  - Treat `multipartContent` as attachments/additional parts.
  - Assemble provider-native shape in a provider-specific way.
  - Ordering (e.g. images-first vs text-first) is plugin responsibility and may align with UI display placement but is not required.

- In `from_native_messages`:
  - Reconstruct core `content` and core `multipartContent`.
  - Optionally use provider-native `_metadata` to preserve additional information for roundtrip.

- Preserve backward compatibility: if `multipartContent` is absent, behavior should match current text-only handling.

- Add an OpenRouter integration test that exercises multipart mapping.
  - Test should be marked `@pytest.mark.integration` and `@pytest.mark.openrouter`.
  - Test should skip cleanly when `OPENROUTER_API_KEY` is not set.

## Implementation Plan

1) Choose the first provider target

- Implement multipart mapping for `OpenRouterProvider` first (`core/python/plugins/openrouter_provider.py`).
- Optionally implement for `OpenAICompatibleProvider` once OpenRouter path works.

2) Define (temporary) v1 core part conventions

The core remains agnostic, but for provider mapping and tests we need a working convention.
Exact schema details will be provided at task execution time; for now assume each part object:

- has `type: str` (e.g. `"image"`, `"pdf"`)
- has `content: dict` with either:
  - `url` (including `data:` URL) OR
  - `data_base64` + `mime_type` + optional `filename`
- has `metadata: dict` (may be `{}`)

3) Implement `to_native_messages` assembly

- Read `multipartContent` from each core message.
- Convert `{content, multipartContent}` into provider-native message content.
- Ensure the outgoing provider-native messages still satisfy existing provider validators.

4) Implement `from_native_messages` split

- Convert provider-native assistant/user messages back into core message dicts that include:
  - `content` (string)
  - optional `multipartContent`
- If needed for stable roundtrip, preserve extra info in provider-native `_metadata`.

5) OpenRouter integration test

- Add a new test file:
  - `core/python/tests/test_openrouter_multipart_integration.py`

Test outline (exact details to be updated once samples are provided):

- Require `OPENROUTER_API_KEY` env var; skip otherwise.
- Use a model that supports multimodal inputs.
  - Recommendation: allow override via env var, e.g. `OPENROUTER_MULTIPART_MODEL`.
- Create a session and append a user message with:
  - `content` string (can be empty or a prompt)
  - `multipartContent` containing at least one image part
- Send request and assert:
  - assistant response exists
  - response `content` is a non-empty string

6) Keep test robust

- Ensure the test is minimal and does not require UI components.
- Ensure it skips cleanly if required env vars are missing.

## Definition of Done

- OpenRouter provider can handle multipart mapping without breaking text-only flows.
- OpenRouter integration test covers at least one multipart message path.

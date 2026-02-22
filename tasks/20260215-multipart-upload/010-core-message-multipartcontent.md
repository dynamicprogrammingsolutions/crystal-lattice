# Core: Add `multipartContent` to Message + roundtrip

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Extend the core SDK `Message` type to support an optional top-level `multipartContent` key (camelCase in JSON) while keeping `content` first-class and unchanged.

## Depends On

- None

## Current State

- `Message` is defined in `core/python/agent_core/types.py:1014` and includes only `role`, `content`, `metadata`.
- `Message.to_dict()` emits only `role/content/metadata`.
- `Message.from_dict()` reads only `role/content/metadata`.
- `AgentCore.add_message()` constructs message dict with only `role/content/metadata` in `core/python/agent_core/core.py:595`.

## Requirements

- Add an optional message field for multipart parts.
- JSON serialization key must be `multipartContent`.
- Core must treat multipart parts as opaque/extensible and should not enforce specific `type` values or per-type schemas.
- `content` remains important; do not derive it from multipart.

## Implementation Plan

1) Update `Message` dataclass

- File: `core/python/agent_core/types.py`
- Add a new optional attribute (python name suggestion: `multipart_content: Optional[List[Dict[str, Any]]] = None`).
- Keep `metadata` unchanged.

2) Update serialization

- In `Message.to_dict()`:
  - Include `multipartContent` when present (non-empty list or non-None; choose consistent behavior).
  - Continue deep-copy semantics consistent with existing `metadata` behavior.
- In `Message.from_dict()`:
  - Read `multipartContent` if present.
  - Be permissive: if missing, treat as `None`.
  - If present but not a list, either coerce to `None` or raise; pick behavior and lock it in tests.

3) Update message creation paths

- Update `AgentCore.add_message()` in `core/python/agent_core/core.py:595` to accept an optional multipart argument and include it in the constructed `message_dict`.
  - This keeps `multipartContent` a first-class message key rather than hiding it in `metadata`.

4) Maintain native history behavior

- Ensure any logic that depends on `msg.to_dict()` continues to work.
- Do not add core-level schema validation for multipart parts.

## Tests

- Update/add tests in `core/python/tests/test_types.py`:
  - Roundtrip: `Message.to_dict()` then `Message.from_dict()` preserves `multipartContent`.
  - Missing multipart behaves as expected.

- Add a session export/import roundtrip test:
  - Build a `Session` with a message containing multipart.
  - `AgentCore.export_session()` then `AgentCore.import_session()` preserves it.

## Definition of Done

- Core can persist `multipartContent` through all serialization layers.
- `AgentCore.add_message()` can create messages with multipart.
- Unit tests cover roundtripping.

---

## Implementation Notes (Added 2026-02-15)

- Implemented `Message.multipart_content` as an optional field on the core dataclass, serialized with the JSON key `multipartContent`.
  - `core/python/agent_core/types.py:1015` defines the new field.
  - `core/python/agent_core/types.py:1036` (`to_dict`) includes `multipartContent` only when `multipart_content` is a non-empty list.
  - `core/python/agent_core/types.py:1050` (`from_dict`) accepts missing/`null`; raises `TypeError` if `multipartContent` is present but not a list.

- Extended core message creation helpers so multipart survives both core-only and native-history paths.
  - `core/python/agent_core/core.py:609` (`AgentCore.add_message`) adds kw-only `multipart_content` and forwards it into the internal `message_dict` as `multipartContent`.
  - `core/python/agent_core/core.py:177` (`_append_single_message_with_native`) persists multipart both in the core-only append (`Message(...)`) and in the core→native suffix dict.
  - `core/python/agent_core/core.py:316` (`_insert_single_message_with_native`) persists multipart in the core-only insertion path.
  - `core/python/agent_core/core.py:719` (`_slice_session_core_only`) preserves multipart when reconstructing messages.
  - `core/python/agent_core/core.py:421` (`_modify_single_message_with_native` core-only path) preserves multipart when reconstructing messages.

- Added regression tests.
  - `core/python/tests/test_types.py:33` and `core/python/tests/test_types.py:58` cover `Message` dict roundtrips for `multipartContent`.
  - `core/python/tests/test_core.py:208` covers `AgentCore.export_session()`/`import_session()` roundtrip preserving multipart.

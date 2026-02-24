Implement core SDK support for `multipartContent` on messages, including serialization roundtrips and core message creation helpers.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`

2) Inspect the current core implementation to understand existing message and session serialization flows:
- `core/python/agent_core/types.py` (Message dataclass + to_dict/from_dict)
- `core/python/agent_core/core.py` (`AgentCore.add_message`, export/import helpers)
- Any related unit tests under `core/python/tests` (especially `test_types.py`)

3) Identify design details that must be decided before coding (e.g., whether `multipartContent` is included when empty vs omitted, how permissive `from_dict` should be on invalid values, and how to extend `AgentCore.add_message` signature).

4) Write a short plan to the user that includes:
- Exact API changes (Python attribute name vs JSON key)
- Serialization behavior (when the key is present)
- Test changes/additions

Do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement `Message` changes:
- Add optional multipart field.
- Ensure JSON key is exactly `multipartContent`.

2) Update core message creation:
- Extend `AgentCore.add_message` to accept optional multipart and persist it on the created message.

3) Add/adjust unit tests:
- Message dict roundtrip.
- Session export/import roundtrip.

4) Run the smallest relevant test set and report results.

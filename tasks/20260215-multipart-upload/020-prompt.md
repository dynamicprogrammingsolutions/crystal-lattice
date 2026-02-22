Update the FastAPI server so `POST /sessions/{session_id}/messages` accepts optional `multipartContent` while keeping `content` as the main text field (which may be empty if multipart is present).

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/020-server-append-multipartcontent.md`

2) Inspect the current server endpoint implementation:
- `application/python/agent_terminal_app/server.py` (the `add_message` route)

3) Inspect the core API you will call (to ensure correct signature):
- `core/python/agent_core/core.py` (`AgentCore.add_message`)
- `core/python/agent_core/types.py` (`Message.to_dict` output)

4) Inspect existing server tests to follow conventions:
- `application/python/tests` (look for server endpoint tests involving message append/list)

5) Decide and propose to the user:
- Validation rules for allowing empty `content` when multipart exists
- Minimal validation for `multipartContent` (shape checks only)
- Whether and how to adjust session list preview behavior (optional)

Share a concise plan with the user; do not implement yet.

## Step 2 — Complete (after user approval)

1) Update the append endpoint to:
- Parse `multipartContent`.
- Validate `content` is a string and allow empty iff multipart is non-empty.
- Persist via core `add_message`.

2) Ensure the returned session/message dict includes `multipartContent`.

3) Add/update tests under `application/python/tests`.

4) Run the relevant test subset and report results.

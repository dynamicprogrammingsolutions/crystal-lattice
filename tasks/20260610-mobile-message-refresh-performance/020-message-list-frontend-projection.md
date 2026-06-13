# Message List Frontend Projection

Add an AgentApp-level parameter for optimized frontend message listing that strips known redundant fields not needed by the mobile frontend.

## Requirements checklist

- [ ] Add a parameter at the AgentApplication/AgentApp message-listing layer to request a frontend-optimized message projection.
- [ ] Expose the parameter through `GET /sessions/{session_id}/messages`.
- [ ] Preserve current full response behavior by default.
- [ ] In optimized frontend projection, strip `toolResult`.
- [ ] In optimized frontend projection, strip `content` when `metadata.display` is present.
- [ ] Update the frontend SDK/mobile message listing path to request the optimized projection where appropriate.
- [ ] Add server and SDK/mobile tests covering the optimized projection.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

## Background

The user explicitly narrowed the earlier payload work to a simple projection:

- Add a parameter to the AgentApp method.
- Optimize and strip known redundant fields that are not needed on frontend:
  - `toolResult`
  - `content` if `metadata.display` is present

Do not expand this task into broad arbitrary include/exclude metadata filtering unless needed for compatibility. The goal is a low-risk, well-scoped projection that reduces payload size while leaving stored session data and model-facing history intact.

Relevant code:

- `application/python/agent_terminal_app/server.py`
  - `list_session_messages` currently appends each message as `{"index": idx, "message": msg.to_dict()}`.
- `core/python/agent_core/types.py`
  - `Message.to_dict()` includes `metadata`, `multipartContent`, and `toolResult`.
- `packages/frontend-sdk/src/backend/restBackend.ts`
  - `RestAgentBackend.listMessages()` builds the query and parses `{ messages, cursor_event_id, active_request_id }`.
- `packages/frontend-sdk/src/types/messages.ts`
  - `ApiMessage` currently allows `content`, `multipartContent`, `toolResult`, and `metadata`.
- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
  - Mobile uses `metadata.display` preferentially through `selectDisplayContent`.

## Frontend Field Usage

The mobile renderer currently needs:

- `role`
- `content` when no `metadata.display` is present
- `multipartContent` for attachments
- `metadata.display` for tool/image/display payloads
- `metadata.tool_name` for tool labels
- `metadata.compiled_content` for expandable compiled system prompt display
- `metadata.reasoning` for assistant reasoning display
- `metadata.url_citations` and `metadata.web_search_sources`
- `metadata.tool_calls` and `metadata.tool_call_previews`
- metadata fields referenced by active message footer UI schema

This task does not need to solve arbitrary footer metadata minimization. The simplified projection only strips two known redundant fields. If a future task adds more aggressive metadata filtering, it must account for message footer UI schema paths.

## Implementation Guidance

The projection should happen on the response path only. Do not mutate stored sessions.

Suggested API shape:

- Internal method parameter: for example `frontend_optimized: bool = False` or `message_projection: Literal["full", "frontend"] = "full"`.
- HTTP query parameter: for example `projection=frontend` or `optimize_for=frontend`.

Projection rules:

- Start from `msg.to_dict()`.
- If optimized:
  - Remove `"toolResult"` if present.
  - If `metadata` is a dict and `metadata.get("display")` is present, remove `"content"`.

Mobile display already prefers `metadata.display` over `content`, so removing `content` in that case should be compatible. Confirm edit/modify flows still work when a displayed message lacks `content`; editing may require fetching the full message or disabling edit for projected messages. If this creates a UX issue, document it and prefer fetching full message on demand for edit actions.
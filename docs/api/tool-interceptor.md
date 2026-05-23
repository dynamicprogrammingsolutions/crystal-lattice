# Tool Call Interception

## Overview

Tool call interception lets a plugin pause any tool call mid-flight, present a prompt to the user (or another automated agent), collect a decision, and then resume execution with that decision. The entire flow is asynchronous — the LLM request is suspended, the server saves state to disk, and the frontend can poll or be pushed the pending prompt. Once the user responds, the backend resumes the original request with the recorded answer.

**Key capabilities:**
- Pause before a tool executes ("call-phase" interception) or after it returns ("result-phase" interception)
- Show the user a prompt with labelled buttons (e.g. Allow / Deny) and optional form fields
- Resume the suspended request transparently — the LLM sees the complete history
- Full audit trail: every interception decision is stored in `interception_phases` on the message
- Safe across provider-native history rebuilds (openai_responses, OpenRouter, etc.)

---

## Architecture

```
ToolLoopRunner._apply_tool_calls()
  ├── For each tool call from the LLM:
  │     ├── call-phase interceptors run (intercept_tool_call)
  │     │     ├── ALLOW  → continue, execute the tool
  │     │     ├── DENY   → skip the tool, inject a canned result
  │     │     └── PROMPT → suspend, emit tool_interceptor_prompt event
  │     │           └─ (execution halts until user responds)
  │     └── result-phase interceptors run (intercept_tool_result)
  │           ├── ALLOW / TRANSFORM  → pass result through
  │           └── PROMPT             → suspend, emit tool_interceptor_prompt event
  │
  └── On resume (after POST /tool-prompts/respond):
        ├── AgentApplication.submit_interceptor_prompt_answer()
        │     ├── Validates: message_index, phase, tool_call_id, prompt_id
        │     ├── Appends prompt_response entry to interception_phases
        │     └── Calls core.modify_message_metadata() → persists mutation
        └── send_request() re-runs with original config_overrides
```

---

## Message Metadata Fields

The tool loop stores interception state directly on the assistant message that triggered the tool calls. Two fields are used:

### `interception_current`

Describes the *in-progress* interception for the currently suspended tool call. Written while the request is paused. Cleared when the request resumes.

```jsonc
{
  "phase": "call",               // "call" | "result"
  "tool_call_id": "<id>",        // matches the tool call this interceptor acted on
  "tool_name": "add_numbers",
  "plugin": "my_interceptor",    // plugin that triggered the suspension
  "request_overrides": { /* original overrides to replay on resume */ },
  "pending_prompt": {
    "id": "<uuid>",              // unique per prompt — used for idempotency
    "buttons": [
      { "id": "allow", "label": "Allow" },
      { "id": "deny",  "label": "Deny"  }
    ],
    "fields": []                 // optional form fields
  }
}
```

### `interception_phases`

An append-only audit log of every interception decision made for this assistant turn. Each entry records what happened:

```jsonc
[
  // An interceptor allowed the call through without prompting
  {
    "type": "allowed",
    "phase": "call",
    "tool_call_id": "<id>",
    "tool_name": "add_numbers",
    "plugin": "my_interceptor"
  },

  // The user answered a prompt
  {
    "type": "prompt_response",
    "phase": "call",
    "tool_call_id": "<id>",
    "tool_name": "add_numbers",
    "plugin": "my_interceptor",
    "prompt": { /* the original pending_prompt object */ },
    "prompt_id": "<uuid>",
    "button_id": "allow",        // which button the user pressed
    "values": {}                 // any form field values
  },

  // An interceptor denied the tool call
  {
    "type": "denied",
    "phase": "call",
    "tool_call_id": "<id>",
    "tool_name": "add_numbers",
    "plugin": "my_interceptor"
  }
]
```

---

## Event: `tool_interceptor_prompt`

When a tool call is suspended, the tool loop emits this event into the shared event store before pausing:

```jsonc
{
  "type": "tool_interceptor_prompt",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "message_index": 3,           // index of the assistant message in session.messages
  "phase": "call",              // "call" or "result"
  "tool_call_id": "<id>",
  "tool_name": "add_numbers",
  "plugin": "my_interceptor",
  "prompt": {
    "id": "<uuid>",
    "buttons": [
      { "id": "allow", "label": "Allow" },
      { "id": "deny",  "label": "Deny"  }
    ],
    "fields": []
  }
}
```

Clients that receive this event should fetch the updated session to display the prompt UI. In the frontend SDK, `messageHistoryReducer` handles `tool_interceptor_prompt` by returning `{ kind: 'dirty' }`, which schedules an automatic session reload so the pending prompt appears in the message list.

---

## HTTP API

### `POST /sessions/{session_id}/tool-prompts/respond`

Submit a user's answer to a pending interception prompt. This endpoint:

1. Validates the request fields against the stored `interception_current`
2. Appends a `prompt_response` entry to `interception_phases`
3. Clears `pending_prompt` from `interception_current`
4. Persists the mutation via `core.modify_message_metadata()`
5. Immediately calls `send_request` to resume the suspended request

**Request body:**

```jsonc
{
  "message_index": 3,           // integer — index of the assistant message
  "phase": "call",              // "call" | "result" — must match current phase
  "tool_call_id": "<id>",       // must match interception_current.tool_call_id
  "prompt_id": "<uuid>",        // must match interception_current.pending_prompt.id
  "button_id": "allow",         // one of the button ids from the prompt
  "values": {}                  // optional form field values
}
```

**Validation errors (HTTP 400):**
- `message_index` not an integer
- `phase`, `tool_call_id`, `prompt_id`, `button_id` missing or empty string
- Phase mismatch with current interception state
- Tool call ID mismatch
- No `pending_prompt` on the target message (already answered or session stale)
- Prompt ID mismatch (double-submit guard)

**Success response (HTTP 200):**

```jsonc
{
  "status": "accepted",
  "request": { /* same shape as POST /send response */ }
}
```

After a successful submit, the backend fires a new `send_request` with the stored `request_overrides`. The resumed request continues from where it was suspended, with the `interception_phases` audit log visible to the interceptor plugin so it can read the user's decision.

---

## Writing an Interceptor Plugin

An interceptor plugin is a feature plugin that implements `intercept_tool_call` and/or `intercept_tool_result`. It returns a directive dict describing what to do.

```python
from agent_core.types import FeaturePlugin

class MyInterceptorPlugin(FeaturePlugin):
    name = "my_interceptor"

    def intercept_tool_call(
        self,
        tool_call: dict,
        session_messages: list,
        state: dict,
        *,
        context: dict | None = None,
    ) -> dict:
        """
        Called before a tool executes.

        Return one of:
          {"action": "allow"}                      # pass through
          {"action": "deny", "result": "..."}      # skip tool, inject result
          {"action": "prompt", "prompt": {...}}    # suspend and ask user
        """
        tool_name = tool_call.get("function", {}).get("name", "")

        # Example: always prompt before executing "delete_file"
        if tool_name == "delete_file":
            return {
                "action": "prompt",
                "prompt": {
                    "buttons": [
                        {"id": "allow", "label": "Allow"},
                        {"id": "deny",  "label": "Deny"},
                    ],
                    "fields": [],
                },
            }
        return {"action": "allow"}

    def materialize_interception_prompt(
        self,
        tool_call: dict,
        raw_prompt: dict,
        phases: list,
        state: dict,
        *,
        context: dict | None = None,
    ) -> dict | None:
        """
        Optional. Called to enrich the raw prompt before it is serialized
        into the event. Return a new prompt dict or None to use raw_prompt as-is.
        """
        return None

    def intercept_tool_result(
        self,
        tool_call: dict,
        tool_result: dict,
        session_messages: list,
        state: dict,
        *,
        context: dict | None = None,
    ) -> dict:
        """
        Called after a tool returns its result.

        Return one of:
          {"action": "allow"}                          # pass result through
          {"action": "transform", "result": "..."}    # replace result content
          {"action": "prompt", "prompt": {...}}        # suspend and ask user
        """
        return {"action": "allow"}
```

### Reading the user's decision on resume

When the request resumes after a `prompt` directive, the `phases` list contains the recorded `prompt_response` entry. Read it inside either `intercept_tool_call` (for call-phase prompts) or `intercept_tool_result` (for result-phase prompts) to act on the user's choice:

```python
def intercept_tool_call(self, tool_call, session_messages, state, *, context=None):
    tool_call_id = tool_call.get("id") or tool_call.get("call_id")
    phases = context.get("interception_phases") or [] if context else []

    # Look for our prior prompt response for this call
    for entry in phases:
        if (
            entry.get("type") == "prompt_response"
            and entry.get("tool_call_id") == tool_call_id
            and entry.get("phase") == "call"
        ):
            if entry.get("button_id") == "allow":
                return {"action": "allow"}
            return {"action": "deny", "result": "Denied by user."}

    # No prior answer — prompt for the first time
    return {
        "action": "prompt",
        "prompt": {
            "buttons": [
                {"id": "allow", "label": "Allow"},
                {"id": "deny",  "label": "Deny"},
            ],
        },
    }
```

---

## Native History Safety

The interception metadata (`interception_current`, `interception_phases`) is stored on assistant `Message.metadata`. With providers that use provider-native history (e.g. the `openai_responses` provider), a `_rebuild_core_from_native` pass reconstructs core messages from native items and can silently drop custom metadata fields.

Two mechanisms prevent metadata loss:

### 1. `ToolInterceptorMetadataPreserver` feature plugin

Located at `core/python/plugins/tool_interceptor_metadata_preserver.py`. This feature plugin:

- **`to_native_messages`**: copies `interception_current` and `interception_phases` from each core message's `metadata` into the corresponding native message's `_metadata` dict before the native history is serialized.
- **`from_native_messages`**: reads those fields back out of `_metadata` and merges them into the reconstructed core message metadata after a native rebuild.

Register it when using native-history providers:

```python
from core.python.plugins.tool_interceptor_metadata_preserver import ToolInterceptorMetadataPreserver
core.register_feature(ToolInterceptorMetadataPreserver)
```

### 2. Post-rebuild metadata patch in `_modify_single_message_metadata_with_native`

`core/python/agent_core/core.py` — `_modify_single_message_metadata_with_native`

When `submit_interceptor_prompt_answer` calls `core.modify_message_metadata()`, the core updates the target message's native items and then runs `_rebuild_core_from_native`. For providers like `openai_responses`, if the native segment for the target message contains only non-`message`-type items (e.g. `reasoning` + `function_call` items), the rebuilt `canonical` message starts with no metadata, which would erase all interception fields.

The core guards against this with an explicit post-rebuild overlay: after rebuilding, it iterates the new core messages and for the target index it merges every key from the intended `metadata` dict (except `native_indices`, which comes from the rebuild) back into whatever the rebuild produced. This ensures the correct `interception_phases` and `interception_current` are always present in the saved session regardless of provider-native quirks.

### 3. openai_responses provider fix

`plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` — `_build_response_segment_assistant`

When a native segment has no `message`-type item (only `reasoning` + `function_call`), the provider sets `canonical = None` and used to build metadata from scratch — discarding all `_metadata` fields stored on those items. The fix merges `internal_md` from every item in the segment into the metadata dict when `canonical is None`, so Crystal Lattice fields written by `ToolInterceptorMetadataPreserver` survive the round-trip.

---

## Frontend Integration

### Frontend SDK — `messageHistoryReducer`

`packages/frontend-sdk/src/chat/messageHistoryReducer.ts`

The reducer handles the `tool_interceptor_prompt` event type by returning `{ kind: 'dirty' }`, which schedules a session reload via `scheduleAutoReload`. This ensures the pending prompt appears in the message list as soon as it is published — without requiring the user to refresh.

```typescript
if (type === 'tool_interceptor_prompt') {
  return { kind: 'dirty', messages, reason: 'tool_interceptor_prompt: pending prompt requires reload' };
}
```

### Mobile — `SessionChatScreen`

`mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

The chat screen passes two callbacks into each message row:

- `onToolInterceptorPromptSubmit(messageIndex, phase, toolCallId, promptId, buttonId, values)` — calls `POST /tool-prompts/respond`
- `toolInterceptorPromptSubmittingKey` — tracks which prompt is currently submitting (used by `MessageBubble` to show a loading state and disable the buttons)

**Double-submit guard**: A `useRef` flag (`toolPromptSubmittingRef`) prevents sending a second request if the user taps Allow twice quickly. The ref (not state) is used because the submit callback is captured in a `useCallback` closure that would see stale state — the ref always reflects the current value.

```typescript
const toolPromptSubmittingRef = React.useRef(false);

const handleToolInterceptorPromptSubmit = useCallback(async (...) => {
  if (toolPromptSubmittingRef.current) return;
  toolPromptSubmittingRef.current = true;
  try {
    await submitToolPrompt(...);
  } finally {
    toolPromptSubmittingRef.current = false;
  }
}, [...deps]);
```

`DependencyFlatList` re-renders each message row only when its dependency array changes. `onToolInterceptorPromptSubmit` and `toolInterceptorPromptSubmittingKey` are included in `getItemDependencies` so the row receives the latest callback and submitting state when they change.

---

## End-to-End Flow

```
1. User sends message → LLM responds with a tool call
2. ToolLoopRunner: interceptor returns {"action": "prompt"}
3. pending_prompt written to message.metadata.interception_current
4. tool_interceptor_prompt event published → request suspended
5. Frontend SDK receives event → schedules reload → fetches session
6. MessageBubble renders prompt UI with Allow/Deny buttons
7. User taps Allow
8. Mobile calls POST /sessions/{id}/tool-prompts/respond
     body: { message_index, phase, tool_call_id, prompt_id, button_id }
9. Backend validates → appends prompt_response to interception_phases
10. pending_prompt removed from interception_current
11. core.modify_message_metadata() saves mutation to session file
12. send_request() re-runs with stored request_overrides
13. ToolLoopRunner: interceptor reads phases → sees button_id="allow" → returns allow
14. Tool executes normally → LLM gets the result → response continues
```

---

## Configuration Example

```jsonc
{
  "agents": {
    "default": {
      "provider": "openai_responses",
      "model": "gpt-4o",
      "plugins": [
        "path:builtin/tool-interceptor-metadata-preserver",
        "path:path/to/my-interceptor"
      ]
    }
  }
}
```

When using any provider that stores `native_messages` on session metadata (such as `openai_responses`), always include the `tool_interceptor_metadata_preserver` plugin so interception state survives native-history rebuilds.

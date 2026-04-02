# 223 - Session-Aware Application Plugin UI

Short description: Complete the session-aware application plugin UI schema implementation, enabling plugins like GeminiCompactionAppPlugin to filter UI elements based on session-specific config.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

## References

This task completes the implementation started in:
- `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`
- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md`

## Goal

Enable application plugins to generate UI elements dynamically based on the effective session config (base config + session overrides). This allows plugins like `GeminiCompactionAppPlugin` to show/hide actions based on `compaction.enabled` and `compaction.type` for the current session.

## Problem Analysis

### Current State

The protocol changes were implemented in commit `b5c9260d`:
- `ApplicationPlugin.get_ui_elements()` accepts optional `config`, `tags`, `models` parameters
- `ApplicationPluginWrapper.get_ui_elements()` passes these through
- `AgentApplication.get_application_ui_schema()` accepts these parameters

However, the server and frontend were never updated to pass these parameters:

```
Frontend (Mobile/Desktop)
    │
    ▼
PluginsRegistry.load()
    │
    ▼
backend.listApplicationUiSchema()     ← NO sessionId passed!
    │
    ▼
GET /application/ui-schema            ← NO session context!
    │
    ▼
app.get_application_ui_schema()       ← config=None, tags=None, models=None
    │
    ▼
plugin.get_ui_elements(state, None, None, None)  ← Cannot filter by config!
```

### Root Cause

1. **Server**: `/application/ui-schema` endpoint has no session context
2. **SDK**: `listApplicationUiSchema()` doesn't accept `sessionId`
3. **Frontend**: `PluginsRegistry` loads application UI without session scope

### Expected Behavior

Application plugins should receive the session's effective config (base + overrides) when queried for UI elements, just like core plugins do via `GET /sessions/{id}/ui-schema`.

## Implementation Plan

### Stage 1: Server Endpoint

Add `GET /sessions/{session_id}/application/ui-schema` to `server.py`:

1. Load session and compute effective config
2. Resolve enabled plugins and compute `tags`/`models`
3. Call `app.get_application_ui_schema(config=effective_config, tags=tags, models=models)`
4. Return elements

### Stage 2: Frontend SDK

1. Add `getSessionApplicationUiSchema(sessionId)` to `RestAgentBackend`
   - Call `/sessions/{sessionId}/application/ui-schema`

2. Create `SessionApplicationUiSchemaController` class
   - Similar to existing `SessionUiSchemaController`
   - Load session-scoped application UI on session change
   - Emit invalidation events when session overrides change

### Stage 3: Frontend SDK React Integration

Update both mobile and desktop frontends:

1. Create `useSessionApplicationUiSchemaController` hook
   - Uses `SessionApplicationUiSchemaController`
   - Subscribes to invalidation events

2. Update `SessionChatScreen` (mobile) and equivalent desktop components
   - Use session-scoped application UI instead of global
   - Merge with core UI schema elements

3. Keep global `ApplicationPluginsProvider` for session-list-level actions
   - Some actions (like "New session") don't need session context

### Stage 4: Terminal App

1. Add `session_application_ui_elements()` to `TerminalApplication`
   - Merge with existing `session_ui_elements()` from core plugins

2. **Follow-up task**: Add `/action` command for invoking application actions
   - See standalone task: `tasks/20260315-terminal-action-command.md`

## Acceptance Criteria

1. `GET /sessions/{id}/application/ui-schema` returns different elements based on session config
2. `GeminiCompactionAppPlugin.get_ui_elements()` receives session config and can filter by `compaction.enabled`
3. Mobile frontend shows compaction actions only when enabled for the session's agent
4. Desktop frontend shows compaction actions only when enabled for the session's agent
5. Terminal app can display session-aware application actions

## Task Checklist

- [x] Stage 1: Server endpoint (`server.py`)
- [x] Stage 2: Frontend SDK (`frontend-sdk`, `frontend-sdk-react`)
- [x] Stage 3: Frontend integration (mobile + desktop)
- [x] Stage 4: Terminal app (`terminal_app.py`)
- [x] Tests: Server endpoint, SDK, plugin enablement
- [x] Follow-up task created for `/action` command

## Completion Notes

### Implementation Summary

**Stage 1: Server Endpoint**
- Added `GET /sessions/{session_id}/application/ui-schema` endpoint in `server.py`
- Computes effective config from session's base config + overrides
- Passes `config`, `tags`, `models` to `AgentApplication.get_application_ui_schema()`

**Stage 2: Frontend SDK**
- Added `getSessionApplicationUiSchema(sessionId)` to `RestAgentBackend`
- Added method to `AgentBackend` interface
- Created `SessionApplicationUiSchemaController` class with caching and invalidation
- Added `useSessionApplicationUiSchemaController` hook in `frontend-sdk-react`

**Stage 3: Frontend Integration**
- Updated `SessionChatScreen.tsx` (mobile) to use **only** session-scoped application UI
- Updated `ChatPane.tsx` (desktop) to use **only** session-scoped application UI
- Removed incorrect fallback logic that would have shown disabled actions
- Kept `useApplicationPlugins()` for `actionsById` and `sessionListFields` only

**Stage 4: Terminal App**
- Added `session_application_ui_elements()` to `TerminalApplication`
- Computes effective config and passes to `get_application_ui_schema()`

**Plugin Updates**
- Updated `GeminiCompactionAppPlugin.get_ui_elements()` to filter based on config
- When config is provided and compaction is enabled, returns UI elements
- When config is provided and compaction is disabled, returns empty list
- When config is None (global endpoint), returns elements unconditionally

### Architecture: Two Separate Endpoints

| Context | Endpoint | Used For |
|---------|----------|----------|
| **Session List** (SessionsScreen/SessionsPanel) | `GET /application/ui-schema` | `session_list_actions`, `session_list_fields` (global, no config) |
| **Chat Window** (SessionChatScreen/ChatPane) | `GET /sessions/{id}/application/ui-schema` | `session_action`, `message_action` (config-aware) |

**Important**: The two results are **never combined**. Each context uses its own endpoint.

### Files Modified

| File | Change |
|------|--------|
| `application/python/agent_terminal_app/server.py` | Added session-scoped application UI endpoint |
| `application/python/agent_terminal_app/terminal_app.py` | Added `session_application_ui_elements()` method |
| `packages/frontend-sdk/src/backend/backend.ts` | Added `getSessionApplicationUiSchema` to interface |
| `packages/frontend-sdk/src/backend/restBackend.ts` | Implemented `getSessionApplicationUiSchema` |
| `packages/frontend-sdk/src/uiSchema/sessionApplicationUiSchemaController.ts` | New controller class |
| `packages/frontend-sdk/src/index.ts` | Export new controller |
| `packages/frontend-sdk-react/src/useSessionApplicationUiSchemaController.ts` | New hook |
| `packages/frontend-sdk-react/src/index.ts` | Export new hook |
| `mobile/.../SessionChatScreen.tsx` | Use session-scoped application UI only |
| `desktop/.../ChatPane.tsx` | Use session-scoped application UI only |
| `plugins/gemini-compaction-app/src/.../__init__.py` | Filter UI elements by config |
| `plugins/gemini-compaction-app/tests/...` | Updated tests |

### Follow-up Task

Created `tasks/20260315-terminal-action-command.md` for implementing `/action` slash command in the terminal app.
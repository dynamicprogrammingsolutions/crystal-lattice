# UI representation boundaries (mobile RN, desktop RN, VS Code)

This document captures **what should live in the SDK** vs **what should remain in a UI screen/component**.

Goal: enable multiple representations (mobile layout, desktop layout, editor UI) without duplicating business logic.

## Principles

- **Screens are presentation**: screens should primarily render state and dispatch user intents.
- **Controllers own workflows**: controllers own state machines, backend interaction, and cross-screen semantics.
- **UI keeps platform-specific interaction state**: anything likely to change across platforms stays in the UI layer.
- **SDK provides view-model helpers**: derived strings/fields (titles, status bars, footers) should be pure functions so different UIs can render them differently.

## What belongs in the SDK

### 1) Domain workflows (controllers)

- Chat/session lifecycle: load, send/resend/cancel, apply events, track `activeRequestId` and error state.
- Sessions list lifecycle: load, staleness policy, create/fork (where supported).
- Plugin registry loading/caching and categorization (actions and UI elements).
- Agents list loading/caching.

### 2) View-model derivation helpers (pure)

These return *presentation inputs* (strings/fields) but do not dictate layout.

- Sessions list: `deriveSessionListPresentation(session, sessionListFields)` → `{ title, subtitle, meta }`.
- Chat decorations: `deriveStatusBarParts(lastAssistantMessage, statusBarSchema)` and footer element filtering.

### 3) Application action execution semantics

UI should not re-implement “interpret plugin response and decide what to refresh.”

- Provide an SDK helper/runner that executes an application action and returns `effects` such as:
  - `navigateToSession(sessionId)`
  - `reloadSession(sessionId)`
  - `reloadSessionsList()`

Each frontend maps effects to its own navigation and refresh UI.

### 4) Data loading helpers for UI schema

- Loading/caching of per-session UI schema (`getSessionUiSchema`) should live in a headless controller.
- UI consumes `footerElements` / `statusBarElements` / raw schema and decides layout.

### 5) Reusable React glue (optional)

- Reusable hooks for controller lifecycle (`useChatController`, `useSessionsController`).
- Reusable one-shot cache hydration helper hook to avoid duplication across screens.
- Reusable hooks for agent list loading/caching and action-dialog state.

## What belongs in the UI (screen/component)

### 1) Representation state (layout and interaction)

Examples that are expected to differ between mobile/desktop/editor:

- Scroll position / auto-scroll policy.
- Inline editing state (`editingIndex`, `editingText`) and per-message render modes.
- Dialog open/close state and field values while a dialog is open.
- Search box / filtering query text.

### 2) Platform services and side effects

- Clipboard, notifications/toasts, confirmation dialogs.
- Local preference storage implementation (the SDK may define formats, but UI wires the platform store).

## Current concrete targets (mobile RN)

### `SessionChatScreen`

- **Move into SDK**: session UI schema loading; status bar/footer derivation; plugin action result interpretation; message range parsing.
- **Keep in UI**: scroll state; edit mode; message render mode; modal visibility; clipboard and alerts.

### `SessionsScreen`

- **Move into SDK**: sessions staleness policy; title/subtitle/meta derivation; plugin action result interpretation.
- **Keep in UI**: filter text; layout-specific row rendering; modal flows.

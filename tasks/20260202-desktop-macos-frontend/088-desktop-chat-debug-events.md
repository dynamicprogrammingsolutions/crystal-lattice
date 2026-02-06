# Subtask: Debug events viewer (desktop)

Add an optional debug-only events viewer for the active chat tab, similar to mobile’s debug overlay.

This is useful for validating polling, streaming rows, and reducer behavior on desktop.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/086-desktop-plugin-actions-in-chat.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- `useChatController` supports an `onEvents` listener (read 10–18 and 57–62): `packages/frontend-sdk-react/src/useChatController.ts:10`
- Mobile debug events buffer + overlay (read 205–212 and 1345–1349): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:205` and `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1345`
- Mobile debug view component (read 1–200): `mobile/crystal-lattice-control-rn/src/components/DebugEventsView.tsx:1`

## Requirements

- Capture recent events for the active tab (cap the buffer, e.g. 200).
- Provide a simple way to open/close the viewer (header action is fine).
- Viewer must not impact non-debug usage (keep it optional and lightweight).

## Deliverables

- Add a desktop debug viewer component (desktop-local; sharing not required).
- In `ChatPane`, provide a toggle action to show/hide it.
- When tab is inactive, either stop capturing events or keep capturing only if it’s inexpensive.

## Verification

- Trigger a request; verify the viewer shows `request_started`, streaming events, and `request_completed`.
- Switch tabs; verify the viewer corresponds to the active tab.

# Update SDK event types for minimal schemas

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/010-event-contract.md`

Update `@crystal-lattice/frontend-sdk` TypeScript event type definitions to reflect the new minimal event schema.

## Status

- [x] Completed

## Current state

- SDK event types are defined in `packages/frontend-sdk/src/types/events.ts:1`.
- Many server-produced event types exist but are not represented as explicit TS unions (`messages_deleted`, `message_modified`, `session_created`, etc.).
- `BaseEvent` allows extra keys; this is useful for forward compatibility, but core event types should be explicit so reducers can be well-defined.

## Work checklist

- [x] Add explicit event types:
  - [x] `SessionCreatedEvent`
  - [x] `MessageModifiedEvent`
  - [x] `MessagesDeletedEvent`
- [x] Extend existing event types:
  - [x] `MessageAppendedEvent` to include `index` and `message`
  - [x] `FinalEvent` to include `start_index` (or `indices`)
  - [x] `ToolResultsEvent` to include `start_index` (or `indices`)
- [x] Skip `event_version` (hard cutover)
- [x] Keep `BaseEvent` permissive, but ensure the exported `Event` union includes all relevant types

## Consumer update note

After types are updated, `ChatController` and the new reducer should switch to using these types directly (avoid `(ev as any)` field access where possible).

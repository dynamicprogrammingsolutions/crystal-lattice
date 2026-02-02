# Implement pure reducer for message history + dirty fallback

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/040-sdk-event-types.md`

Implement a pure reducer in `@crystal-lattice/frontend-sdk` that can consume an existing message history and a single event, and return the updated history (or mark the session dirty if the event cannot be applied safely).

## Status

- [x] Completed

## Reducer API proposal

Create a module like `packages/frontend-sdk/src/chat/messageHistoryReducer.ts`:

```ts
export type ReduceResult =
  | { kind: 'ok'; messages: IndexedMessage[] }
  | { kind: 'noop'; messages: IndexedMessage[] }
  | { kind: 'dirty'; messages: IndexedMessage[]; reason: string };

export function reduceMessageHistory(
  messages: IndexedMessage[],
  event: Event,
): ReduceResult;
```

Notes:

- Keep it fully deterministic and side-effect free.
- Prefer returning `dirty` rather than throwing for mismatches.
- `IndexedMessage.index` should be derived from array position after reducer application (or keep stable indices but ensure consistency).

## Event handling requirements

- `message_appended`: apply at `event.index` (validate it matches expectations; otherwise mark dirty)
- `message_modified`: replace message at `event.index`
- `messages_deleted`: remove listed indices (validate bounds)
- `final` / `tool_results`: insert/append at `start_index` + `messages.length`

Streaming UI state (`assistant_message` start/end, `partial`) should be handled separately (not part of message history reducer), or in a parallel reducer for `streamingRow`.

## Dirty conditions (examples)

- Index out of bounds
- Event expects append at index X but local length differs
- Unknown/unsupported event schema version
- Any event type that changes history but does not include sufficient info

## Work checklist

- [x] Create the reducer module + unit-like tests if a test framework exists for TS packages
- [x] Ensure message indices are consistent after delete operations
- [x] Document reducer semantics in-code (short docstring) and/or in a plan doc

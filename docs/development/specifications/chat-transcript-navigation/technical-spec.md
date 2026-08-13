# Chat transcript navigation technical specification

## Architecture

Transcript navigation crosses four owners:

1. The application HTTP server returns session-message slices and response
   consistency fields.
2. The frontend SDK represents indexed messages, plans ranges, and loads
   controller history.
3. The mobile application renders an inverted React Native viewport.
4. The desktop application renders a macOS viewport with native metrics and a
   scroll coordinator.

Shared code should own portable data and pure planning. Each application owns
native measurement, scrolling, and platform verification.

## Session-message HTTP contract

`GET /sessions/{session_id}/messages` accepts optional integer `start` and
`end` query parameters.

- Bounds follow Python slice semantics.
- Negative bounds are relative to the current session-history length.
- Bounds are clamped to `[0, message_count]`.
- A non-empty session returns HTTP 400 when normalized start is not less than
  normalized end.
- Results are ordered by ascending index.
- Each result contains the snapshot-relative `index` separately from the full
  message payload.
- The response includes `cursor_event_id` and applicable live-session or
  read-only snapshot fields.

An empty session returns an empty message array and consistency fields without
normalizing a range.

The TypeScript frontend contract represents an entry as:

```ts
interface IndexedMessage {
  index: number;
  message: ApiMessage;
}
```

The existing response is not a cheap session-wide message outline: obtaining
indices or roles for the whole session also obtains every full message
payload.

## Index semantics and consistency

A message index is a position in one session-history snapshot. It is not a
stable message identity:

- deleting an earlier message shifts subsequent indices;
- modifying or restoring a session can change the message at an index;
- a live session may change between two HTTP requests.

Range planning and overlap restoration may use indices when the old and new
responses are known to refer to a compatible snapshot. Navigation that spans
multiple responses must retain `cursor_event_id` or `snapshot_id` context and
must not silently target an unrelated message after a mismatch.

A future lightweight outline and direct-index navigation contract must define
one of:

- selection and range loading against the same cursor or snapshot;
- a retry protocol when the cursor changes;
- stable message identities with explicit compatibility semantics.

This baseline does not select among those future designs.

## Shared range planner

`@crystal-lattice/frontend-sdk` owns the pure contextual range planner.
Inputs contain textual range bounds, first and last loaded indices, loaded
count, page size, and maximum range size. Outputs are either:

- the exact next textual bounds; or
- no plan when the action cannot change the range.

Both frontends consume this planner. Platform components own presentation and
execution.

## Chat controller

The shared chat controller:

- parses textual Python-style bounds;
- records the selected history range;
- derives whether a range follows the tail;
- loads the exact supplied range rather than relying on asynchronous frontend
  state propagation;
- bounds in-memory tail history when a negative tail size is selected;
- avoids applying history mutations directly to explicitly bounded non-tail
  windows;
- returns or exposes response cursor and snapshot state needed by frontend
  coordination.

Changing a range begins a new controller epoch. A frontend navigation
coordinator must additionally distinguish overlapping viewport operations so
that a completed older request cannot restore an anchor after a newer user
intent.

## Range-navigation operation

The target operation for Show older and Show newer is:

```text
capture visible overlap anchor
        |
plan and request exact range
        |
replace controller messages and retain response consistency
        |
wait for target row measurement
        |
restore message index + viewport-relative offset
```

The operation record contains at least:

- unique operation identity;
- action and planned range;
- anchor message index and viewport-relative offset;
- old response consistency context;
- cancellation or supersession state;
- bounded deadline or correction count.

The frontend must check operation identity after every asynchronous boundary.
User scrolling, an explicit edge action, a later range action, session change,
or unmount cancels or supersedes the operation.

## Native viewport responsibilities

Each frontend provides:

- measured visual top and bottom gaps;
- visible-row or viewport-anchor capture;
- scroll to a message index at a requested viewport offset;
- scroll to loaded top and bottom;
- completion, failure, timeout, and user-intervention signals.

Stable row keys use the response's message index within the compatible
session-history snapshot. A frontend must not treat an array position as the
session message index.

### Mobile

Mobile maps visual bottom to inverted-list offset zero. Its current viewport
already performs bounded far-top convergence and exposes stable row test IDs.
Range preservation requires explicit operation-scoped anchor capture and
restoration; ordinary `maintainVisibleContentPosition` remains enabled for
normal list changes.

### Desktop

Desktop maps visual edges through macOS metrics and its scroll coordinator.
Its list can capture a visible message anchor and restore an item anchor with
bounded correction. Range preservation should reuse those primitives through
an operation-scoped API instead of coupling the range handler to native
details.

## Persistence

The selected textual range is stored per connection and session. Persisted
viewport state may represent pinned-bottom affinity or a detached message
anchor.

Operation-scoped anchors are transient. They must not overwrite durable
viewport state until the range operation reaches a confirmed terminal state.

## Failures

- A failed range request leaves an error visible and must not execute a stale
  anchor restoration.
- A superseded response must not take viewport ownership.
- If the target row cannot be measured within the bounded budget, the
  operation stops and records diagnostics where supported.
- Snapshot or cursor incompatibility prevents exact index restoration and
  follows the specified retry or fallback policy.
- Empty or no-overlap results use the portable fallback behavior rather than
  an accidental native-list edge.

## Verification

### Shared and server

- Pure range transitions, labels, and action availability.
- Python-style slice normalization and indexed response ordering.
- Exact controller request bounds and response consistency propagation.
- Operation supersession and cursor or snapshot mismatch handling.

### Frontend components

- Control placement, availability, disabled state, labels, and dispatch.
- Edge geometry and command mapping.
- Range persistence per connection and session.

### Native acceptance

Each frontend requires a realistic production-viewport test that:

1. starts with a variable-height transcript and a known visible anchor;
2. invokes Show older or Show newer through the production action path;
3. replaces the loaded data with an overlapping range;
4. verifies the same message index remains visible at a bounded offset;
5. verifies later navigation supersedes the pending restoration.

Method-call assertions alone do not validate viewport preservation.
# Improve chat transcript navigation

Track the cross-package transcript-navigation baseline, correction of
viewport preservation during overlapping range loads, and later semantic
navigation to a message index or adjacent user message.

## Requirements checklist

- [x] A shared specification defines portable transcript-range and loaded-edge
  navigation while preserving independent mobile and desktop implementations.
- [x] Show-older and show-newer preserve an overlapping visible message at
  approximately the same viewport-relative position on mobile and desktop.
- [ ] Users can navigate directly to a message index and to the previous or
  next user message, loading an appropriate range when necessary.
- [ ] Server, shared SDK/controller, mobile, and desktop contracts remain
  consistent and have evidence at their relevant public or native boundaries.

## Scope and workstreams

- Baseline target and current-state evidence:
  `docs/development/specifications/chat-transcript-navigation/`.
- Priority 1: correct TNAV-013 without changing existing range-planning
  semantics.
- Priority 2: add a lightweight message-navigation contract, atomic
  go-to-index operation, and previous/next user-message controls.

## Requirement questions

The TNAV-013 correction has no unresolved requirement question. Its Draft
execution plan is in the corresponding subtask.

The semantic-navigation subtask retains open questions about the lightweight
server response, the reference point for previous/next user navigation, and
the final control presentation. Those questions must be resolved before its
requirements or execution plan are finalized.

## Subtasks

- [x] `tasks/20260813-chat-transcript-navigation/010-create-baseline-specification.md`
- [x] `tasks/20260813-chat-transcript-navigation/020-preserve-range-navigation-viewport.md`
- [ ] `tasks/20260813-chat-transcript-navigation/030-add-message-and-turn-navigation.md`

## Supporting details

- The shared range planner is owned by `packages/frontend-sdk`.
- Mobile and desktop have separate native viewport implementations and should
  remain independently optimized.
- The current message API returns each index separately from its full message,
  but has no cheap session-wide index/role outline.
- Message indices are positions in a session snapshot and may shift after
  deletion, so multi-request index navigation needs cursor, snapshot, retry, or
  stable-identity semantics.
- Existing mobile native tests validate navigation within loaded messages.
  Existing desktop native tests validate persisted message anchors and
  long-distance navigation. Neither currently validates a range replacement
  followed by overlap-anchor restoration.
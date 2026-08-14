# Add direct message and adjacent user-message navigation

Add the lower-priority semantic navigation capability: cheaply discover
session message positions, atomically navigate to a target message index, and
move to the previous or next user message from both frontends.

## Requirements checklist

- [ ] A cheap server response exposes enough session-wide message navigation
  metadata to identify user-message indices without returning every full
  message payload.
- [ ] The response and subsequent range load have defined cursor or snapshot
  consistency behavior and cannot silently retarget a shifted index.
- [ ] The shared frontend API exposes one atomic go-to-message-index operation
  that selects an appropriate bounded range, loads it when necessary, and
  scrolls to the exact target message.
- [ ] Previous-user and next-user navigation resolve their target through the
  lightweight metadata and delegate to the atomic go-to-index operation.
- [ ] Mobile and desktop expose accessible controls that distinguish loaded
  transcript-edge navigation from adjacent-user-message navigation.
- [ ] Boundary, missing-target, concurrent-mutation, loading, failure, and
  supersession behavior is deterministic.
- [ ] Server, SDK/controller, mobile, and desktop automated evidence validates
  the capability at realistic boundaries.

Parent Task: `tasks/20260813-chat-transcript-navigation/000-main.md`

Depends On:

- `tasks/20260813-chat-transcript-navigation/020-preserve-range-navigation-viewport.md`

## Scope

Expected workstreams:

- application HTTP metadata contract;
- frontend SDK backend type and REST adapter;
- atomic shared chat navigation operation;
- mobile controls and native target-row navigation;
- desktop controls and native target-row navigation;
- server, SDK, component, integration, and native acceptance evidence.

This subtask may be split into ordered server-contract, controller, and
frontend subtasks after its requirement questions and design are approved.

## Requirement questions

1. What is the minimum lightweight response?
   Recommendation: ordered entries containing `index` and `role`, plus response
   `message_count`, `cursor_event_id`, and applicable `snapshot_id`. Add a
   bounded short preview only if the UI will display it; previous/next user
   navigation does not require message content.
2. What is the reference point for previous/next user navigation?
   Recommendation: use the currently anchored or most prominent visible
   message index; after an explicit semantic jump, use the last target until
   the user establishes a new visible anchor.
3. How should concurrent history mutation be handled?
   Recommendation: send expected cursor or snapshot context with the target
   range request and retry outline resolution once on a live-session mismatch.
   Do not introduce stable message IDs solely for this feature without a
   separate compatibility decision.
4. What range should surround a direct target?
   Recommendation: choose a bounded 100-message absolute range with useful
   context on both sides, clamped to history boundaries, while preserving the
   existing final-50 default outside semantic navigation.
5. What control presentation should be used?
   Recommendation: retain double chevrons for loaded top/bottom edges and add
   single chevrons for previous/next user messages, with explicit accessible
   labels. Final placement should be checked on compact mobile layouts before
   becoming normative.

## Supporting details

- The current `IndexedMessage` response already separates the index from the
  full message object but is not cheap for session-wide navigation.
- TNAV-013 supplies the target-row restoration primitive needed by an atomic
  go-to-index operation.
- Message indices are snapshot-relative and shift after deletions.
- A direct-index operation belongs in the shared chat/controller abstraction;
  the server supplies metadata and consistent range loading rather than
  storing frontend viewport state.
- No execution plan is approved for this subtask. Plan and decomposition follow
  resolution of the requirement questions.
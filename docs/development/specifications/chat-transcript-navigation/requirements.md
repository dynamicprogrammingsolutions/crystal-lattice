# Chat transcript navigation requirements

These requirements track the live implementation relative to the target
behavior. Existing tests are evidence only for the boundary they exercise.
Native or end-to-end behavior is marked unverified when only pure planning,
source inspection, or method-call assertions exist.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| TNAV-001 | Session message ranges use Python-style slice bounds and return ascending snapshot-relative message indices. | Implemented | Automated | Documented | `application/python/agent_terminal_app/server.py`; `application/python/tests/test_agent_terminal_app_server.py::test_list_session_messages_endpoint_supports_slice_bounds` |
| TNAV-002 | Message-list responses expose the cursor and live-session or read-only snapshot context associated with the returned history. | Implemented | Automated | Documented | `application/python/agent_terminal_app/server.py`; server snapshot/cursor tests; `packages/frontend-sdk/src/backend/restBackend.ts` |
| TNAV-003 | New mobile and desktop chat views default to the last 50 messages, while a persisted per-session range may override that default. | Implemented | Mobile automated; desktop unverified | Documented | `mobile/crystal-lattice-control-rn/src/transcriptRange.ts`; `mobile/crystal-lattice-control-rn/__tests__/TranscriptNavigationControls.test.tsx`; `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` |
| TNAV-004 | Older, newer, show-all, and show-last actions are presented only when applicable and at their corresponding visual transcript edges. | Implemented | Automated planning and mobile component; full-screen conformance incomplete | Documented | shared and desktop `messageRangeControls` tests; `mobile/crystal-lattice-control-rn/__tests__/TranscriptNavigationControls.test.tsx`; both chat screens |
| TNAV-005 | Ordinary range planning uses a 50-message page and a bounded 100-message loaded window before sliding. | Implemented | Automated | Documented | `packages/frontend-sdk/src/chat/messageRangeControls.ts`; shared and desktop planner tests |
| TNAV-006 | A range action reloads the exact planned range without relying on asynchronous frontend state propagation. | Implemented | Unverified at complete frontend boundary | Documented | explicit range arguments in both chat screens; prior implementation evidence in `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md` |
| TNAV-007 | Range controls do not dispatch another range load while messages are loading. | Implemented | Mobile component automated; desktop unverified | Documented | `mobile/crystal-lattice-control-rn/__tests__/TranscriptNavigationControls.test.tsx`; both chat screens |
| TNAV-008 | Arbitrary Python-style message ranges remain available alongside contextual controls. | Implemented | Unverified at frontend boundary | Documented | mobile range modal and desktop message-range popover |
| TNAV-009 | The selected message range is scoped and persisted per connection and session. | Implemented | Mobile automated; desktop unverified | Documented | shared session-scoped message cache; mobile `useMessagesCache` tests; desktop cache and tab storage |
| TNAV-010 | Scroll-to-top and scroll-to-bottom navigate only within loaded messages and appear only when the corresponding visual edge is meaningfully distant. | Implemented | Mobile unit/component/native automated; desktop partial automated | Documented | mobile inverted-scroll and Detox transcript tests; desktop scroll coordinator and native persistence tests |
| TNAV-011 | Explicit loaded-edge navigation converges on the actual oldest or newest loaded content and can be superseded by later user input. | Implemented | Mobile top/bottom native automated; desktop bottom and item-anchor native automated, exact top-button path unverified | Documented | mobile `InvertedTranscriptViewport` and Detox tests; desktop coordinator tests and macOS transcript-scroll UI tests |
| TNAV-012 | New content follows only while bottom affinity is pinned; navigating away from the bottom is not undone by unrelated streaming or geometry updates. | Implemented | Desktop automated; mobile streaming-detachment boundary unverified | Documented | desktop coordinator and macOS UI tests; mobile viewport affinity implementation |
| TNAV-013 | Show-older and show-newer range changes preserve an overlapping visible message index at approximately the same viewport-relative position. | In progress | Unverified; known nonconforming behavior | Documented | Intended by `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md`; no range-load native acceptance test; reported viewport jump |
| TNAV-014 | Show-last selects `-50:` and navigates to the newest loaded edge. | In progress | Unverified across the complete range-to-viewport flow | Documented | shared planner tests; mobile explicit post-load bottom command; desktop currently selects the range without an explicit post-load edge command |
| TNAV-015 | Transcript navigation controls expose accessible button roles and labels and stable selectors where native acceptance tests require them. | Implemented | Mobile automated; desktop source inspection only | Documented | mobile component and Detox tests; desktop accessible labels in `ChatPane.tsx` |
| TNAV-016 | A range-navigation operation has deterministic failure, no-overlap, cancellation, and supersession behavior. | Not started | Unverified | Documented | Target behavior in `frontend-behavior.md` and `technical-spec.md` |

## Baseline validation gaps

- Neither frontend has a native test that changes the loaded range and then
  verifies an overlapping message's viewport position.
- Mobile native tests validate loaded-edge navigation but not range
  replacement or streaming while detached.
- Desktop native tests validate persisted message anchors, long-distance
  bottom navigation, and far item-anchor restoration, but not the contextual
  range-button flow or exact scroll-to-top button path.
- Complete frontend tests for arbitrary range application, loading
  suppression, and range-request failure behavior were not found.
- Existing index values are snapshot-relative positions; no test or contract
  currently makes them stable across concurrent history mutation.
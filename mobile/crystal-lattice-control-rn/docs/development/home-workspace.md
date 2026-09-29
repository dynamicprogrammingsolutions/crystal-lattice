# Mobile Home, Watchlist, and notes

This page describes mobile ownership, persistence, presentation, and
interaction for Home, Watchlist, Recent Sessions, and local notes. The shared
React Native package owns portable normalization, derivation, status
presentation, and reorder geometry.

`ConnectedRoot` keeps Home, Connections, Sessions, and Messages mounted. Home
is selected after hydration. It consumes cached summaries without constructing
transports and delegates connection opening plus session/navigation selection
through one application command guarded by current user intent.

Portable Watchlist/recent selectors, note normalization, request-status
presentation, and measured reorder helpers are owned by
`@crystal-lattice/frontend-rn-components`. Mobile continues to own
AsyncStorage keys, touch responders, full-screen composition, connection
opening, and navigation. See
[Portable Home, status, and reorder contracts](../../../../packages/frontend-rn-components/docs/development/home-workspace-and-status.md).

## Local ownership

`HomeWorkspaceProvider` owns three versioned AsyncStorage records:

- `clc_home_watchlist_v1`: ordered composite
  `(connectionId, sessionId)` identities;
- `clc_session_notes_v1`: permanent note text keyed by session ID alone;
- `clc_mobile_global_preferences_v1`: the semantic Recent Sessions window.

Hydration completes before any of these stores write. Watchlist entries never
copy session summaries. Home resolves them against `sessionsCache`; unresolved
entries remain persisted but are not rendered.

Notes deliberately share across connections when session IDs match. Removing
a Watchlist entry or saved connection leaves notes intact. Only the explicit
Remove Note action deletes note text.

Sessions and Messages add shared static local action definitions to their
existing pinnable Session actions. `localWatchlist` resolves against
`HomeWorkspaceProvider` and changes only composite local membership. Its label
and icon update between Add and Remove without requiring an open backend.
Server session-pin actions remain separate plugin-owned commands.

The local actions stay disabled until Home storage hydration completes.
Pinned-action hydration also preserves an explicit user change made while an
older storage read is in flight; plugin-declared defaults are merged only
after the scoped record has loaded.

`deriveHomeSessionCollections()` preserves stored Watchlist order and derives a
separate modified-descending Recent Sessions timeline. The timeline applies
the exact `24h`, `3d`, or `1w` cutoff. Watchlist membership does not filter the
timeline because the sections answer different questions: the Watchlist is
manually curated and ordered, while Recent Sessions is complete for the
selected time window.

## Presentation

`HomeScreen` is not a variant of `SessionsScreen`:

- Watchlist uses exactly two columns of workspace tiles;
- each tile has a dedicated PanResponder drag handle and accessible Move
  Earlier/Move Later actions;
- the grid owns transient drag state, snapshots measured variable-height
  slots, renders an elevated tile plus same-size target placeholder, and
  persists only the settled move;
- release installs a keyed optimistic order until the Home workspace context
  acknowledges the same stored order, preventing the pre-move arrangement
  from rendering between local drag cleanup and context propagation;
- the responder overlay enters a non-animated settling phase at release: its
  translation snaps to the measured placeholder frame, the preview remains
  mounted, and the translation resets only after acknowledged final tiles
  replace the overlay;
- handle capture disables user scrolling only for the active drag, while
  bounded edge scrolling keeps off-screen Watchlist targets reachable;
- Recent Sessions uses a vertical activity timeline;
- Recent uses the bookmark for adding local Watchlist membership, while a
  Watchlist tile uses `x` to remove that membership;
- server session pins continue to use their existing rich application action.

Mobile owns its Watchlist and timeline presentation directly; desktop has a
separate implementation. They currently align on title, optional
subtitle/distinct preview, session ID, request status, note, and a final
connection/time metadata row, but no shared React component or spacing
contract prevents later platform-specific changes.

The mobile fallback starts with the SDK session-list presentation. It uses a
distinct preview only when no subtitle exists and never renders the same
preview as both title and secondary text. Connection is the only flexible
metadata child; relative time and action controls do not shrink. Tiles bound
title, subtitle, and note lines, consume semantic theme typography, and expose
field-level native selectors containing connection and session identity.
Timeline rail dots use `theme.textMuted`; request-status colors remain
semantic.

## Verification

Primary coverage includes:

- `src/__tests__/watchlistDrag.test.ts`
- mobile Home workspace, Home, Sessions-note, and `ConnectedRoot` component
  tests
- `src/testing/MobileHomeHarness.tsx`
- `e2e/home.e2e.test.ts`

# Desktop Home, status, panels, and tab ownership

`DesktopRoot` owns one immutable workspace state:

- ordered permanent session tabs;
- one optional preview session;
- active Home or composite session identity.

`desktopWorkspaceReducer` owns open, preview replacement, promotion, close,
connection reconciliation, presentation updates, and permanent reorder
transitions. `openTabsStorage` persists version 2 of this state and migrates
version 1 tabs as permanent.

The active session remains keyed by `(connectionId, sessionId)` through
preview promotion, so `ChatPaneTabStack` retains its existing bounded warm-pane
behavior, cached messages, drafts, and scroll state. A Chat mutation invokes
the promotion command before execution.

## Home data

`DesktopHomeWorkspaceProvider` persists:

- `clc_desktop_home_watchlist_v1`;
- `clc_desktop_session_notes_v1`.

Watchlist identity is composite. Notes are keyed by session ID alone. Portable
normalization, collection derivation, recent cutoffs, status presentation, and
reorder geometry live in `@crystal-lattice/frontend-rn-components`.

Desktop Home and History resolve local identities against `sessionsCache`.
The history range is native global state in `NSUserDefaults`, not part of the
markdown preference contract.

## Session interaction

`sessionItemInteraction` is the shared desktop interpreter for Home, History,
and Sessions rows. First click updates selection only. A second click on the
same identity inside the threshold dispatches the configured global Preview or
Open mode. Each item renders the complementary mode as its explicit button.

Selecting, opening, or restoring a session dispatches the workspace state
first, leaving cached content available, then requests connection reopening.
An open or connecting connection is reused. Repeated reopen work for the same
selection intent is suppressed.

## Panels

`DesktopShell` has three columns:

1. activity rail;
2. 340-point panel;
3. main workspace.

Connections visibility is independent. Sessions and History are mutually
exclusive lower-panel destinations. These presentation choices are local to a
main window.

## Request status

The host-neutral polling hook is owned by
`@crystal-lattice/frontend-sdk-react`. Desktop constructs one
`DesktopConnectionSessionStatusReader` and one polling consumer above all
surfaces. IDs from Home, History, Sessions, and tabs are deduplicated by
connection.

Open records use their current backend. Closed manual records use one stateless
HTTP request. Unsupported records remain quiet, and loss of authority removes
stale running state. Connection Online/Offline and request status remain
separate concepts.

## Reordering

Watchlist and tab drag hosts consume shared measured-slot geometry. The
responder-owning child remains stable while other entries render around a
same-sized placeholder. On release, the overlay snaps to the destination and
remains until the authoritative order matches. Home and preview tabs are
outside permanent-tab order.

React Native macOS touch responders do not receive AppKit mouse-pan movement
reliably. `MacDragView` is the desktop interaction adapter: an
`NSPanGestureRecognizer` emits translation events to the React hosts, while
the shared geometry and optimistic settlement remain platform-neutral.

Primary tests:

- `__tests__/desktopWorkspaceState.test.ts`
- `__tests__/DesktopHomeWorkspaceContext.test.tsx`
- `__tests__/DesktopHomeAndActivity.test.tsx`
- `__tests__/SessionTabsMenu.test.tsx`
- `__tests__/DesktopRoot.sessionReopen.test.tsx`
- `src/testing/DesktopWorkspaceHarness.tsx`
- focused methods in `ConnectionsPanelUITests` and
  `MarkdownDisplayMenuUITests`
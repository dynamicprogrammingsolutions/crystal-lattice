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

The Chat stack stays mounted when Home is selected. Home is rendered over the
inactive stack, its pointer and accessibility interaction is disabled, and
the same three-entry MRU warm set remains mounted for a later tab return.
Home itself does not count toward or reset that bound.

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

Desktop owns `DesktopSessionCollectionItem`, its display fallback,
relative-time formatting, field identifiers, and Home/History styles. Mobile
has an intentionally separate implementation. The two currently align on
field hierarchy and visual rhythm without a shared React component, display
model, or spacing contract.

Desktop starts from the SDK session-list fallback, adds a preview as secondary
text only when it differs from the title, and renders connection name and
relative time as separate metadata children. Connection is flexible and
truncating; time and actions do not shrink. Home Recent and the History panel
reuse the desktop-owned timeline variant with a `textMuted` rail, while
request status retains its shared semantic tone.

## Session interaction

`sessionItemInteraction` is the shared desktop interpreter for Home, History,
and Sessions rows. First click updates selection only. A second click on the
same identity inside the threshold dispatches the configured global Preview or
Open mode. Each item renders the complementary mode as its explicit button.

Selecting, opening, or restoring a session dispatches the workspace state
first, leaving cached content available, then requests connection reopening.
An open or connecting connection is reused. Repeated reopen work for the same
selection intent is suppressed.

Connection reopening, sidebar connection switching, and Sessions-row
following are separate effects. Reopen remains unconditional for a closed
owning connection. The native `Follow Active Tab in Sessions List` preference
defaults On when absent and is passed only to `SessionsPanel`. The native
`Switch Connection with Active Tab` preference defaults Off and is the only
tab-driven owner of `focusedConnectionId`.

`useSessionsPanelTabAutoSelect` tracks selection provenance. A manual row
selection cancels pending tab selection and survives a tab that cannot be
followed while the same connection remains focused. An automatic selection is
cleared when Home or a tab on another focused connection becomes active.
Changing the focused connection clears either source because the rendered
session-list identity changed.

Explicit item actions consult `getDesktopSessionTabKind()`. A matching preview
or permanent tab always exposes Open: permanent tabs activate in place, while
the workspace reducer promotes a matching preview through its ordinary
`openPermanent` transition.

Mobile and desktop consume the same portable local Watchlist/note action
definitions. Desktop Sessions and Chat route those definitions to
`DesktopHomeWorkspaceProvider`; Local note opens the keyed note window, and
Watchlist membership remains independent from server pin state. The actions
remain disabled until the local Home records finish hydrating, so a startup
read cannot overwrite an early mutation.

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
surfaces. IDs from active Home, visible History, the rendered Sessions window,
and all tabs are deduplicated by connection. Focusing a connection does not
register every cached session.

Open records use their current backend. Closed manual records use one stateless
HTTP path. Large groups are split below the endpoint bound, and successful
responses update only their queried IDs. A transient read failure retains a
recent Running result through retry; authoritative non-running/missing data or
bounded loss of authority removes it. Connection Online/Offline and request
status remain separate concepts.

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
The adapter normalizes AppKit Y values according to the actual view
orientation, so upward and downward pointer movement agree with React Native
layout coordinates.

Primary tests:

- `__tests__/desktopWorkspaceState.test.ts`
- `__tests__/DesktopHomeWorkspaceContext.test.tsx`
- `__tests__/DesktopHomeAndActivity.test.tsx`
- `__tests__/SessionTabsMenu.test.tsx`
- `__tests__/DesktopRoot.sessionReopen.test.tsx`
- `__tests__/desktopStatusScope.test.ts`
- `src/testing/DesktopWorkspaceHarness.tsx`
- focused methods in `ConnectionsPanelUITests` and
  `MarkdownDisplayMenuUITests`

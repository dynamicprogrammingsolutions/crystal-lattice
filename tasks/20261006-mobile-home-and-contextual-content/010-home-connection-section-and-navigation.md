# Move Connection Management onto Home

Make connection setup and switching discoverable at the top of Home, remove
the separate Connections bottom tab, and retain the existing connection and
session workflows. This is independently useful before contextual guidance
is adopted.

## Requirements checklist

- [ ] H1 — The first Home section provides connection management and state;
  the bottom navigation no longer contains Connections. Preserve the existing
  card presentation and most-recently-used ordering. Initially show up to
  three cards; a button below the cards expands all connections and collapses
  back to three. Show no toggle when there are three or fewer connections.
- [ ] H2 — Users can create, open/switch, reconnect, disconnect, and remove
  saved connections, and reach connection/server/global settings through
  Home. The existing iOS Local agent entry and available connection methods
  remain accessible. Connection setup and bridge repair appear in a modal.
  Card taps retain Sessions navigation; explicit Open stays on Home.
- [ ] H3 — Existing connection records, transport behavior, cached sessions,
  Watchlist/Recent navigation, selected sessions, and relaunch persistence
  remain compatible with the navigation change.
- [ ] H4 — Starting new connection setup keeps the current connection open.
  Cancellation or failed setup leaves it available; successful setup replaces
  it with the new connection.

Parent Task: tasks/20261006-mobile-home-and-contextual-content/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md

This dependency preserves the user's first-round priority and supplies the
approved Local agent/settings names. There is no dependency on `020`;
contextual-content adoption belongs to `030`.

## Approved UX direction

The user approved execution on 2026-10-07:

- Keep the existing cards, details, status, actions, pinning, ordering, and
  tap/Open behavior. Move Connections above Watchlist and Recent Sessions.
- Default to three visible connections. Put `Show all N connections` with a
  down chevron below the cards, changing to `Show fewer` with an up chevron
  when expanded. Keep one Home scroll area and sensible scroll positioning
  after collapse.
- Open the existing setup flow in a modal. Keep the current connection until
  the replacement succeeds; closing, cancelling, or failed setup retains it.
- Extract focused connection cards, list/collapse composition, command state,
  and wizard presentation/step components during this restructuring.

There are no remaining product questions for this delivery. Local reversible
implementation choices may be resolved during execution.

## Approved wizard presentation and follow-up

The existing connection wizard will appear in an app-owned modal opened from
Home. Preserve its existing connection methods and bridge-repair entry points.

`tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
will implement its HTTP product-mode, saved-bridge-URL, and Development
Settings follow-up after this task is complete and verified. This task owns
wizard placement/navigation and preserves current transport behavior; the
later follow-up changes bridge content and transport selection within the
delivered modal.

## Supporting facts

- `App.tsx` owns persisted connections, selection, connection wizard state,
  and creation of `Transport` and `RestAgentBackend`. That ownership need
  not move into Home.
- `ConnectedRoot.tsx` starts on Home and keeps tab contents mounted. New
  connection requests currently navigate to the Connections tab, where
  either the wizard or `ConnectionsScreen` is displayed.
- `ConnectionsScreen.tsx` already provides production connection cards and
  their action menus. It embeds its own list ScrollView, so simply nesting
  the whole screen in Home would introduce competing scroll regions.
- Home's Watchlist drag geometry depends on measured card and scroll
  positions. Adding a section above it must not assume the old vertical
  offsets.
- Existing `home.e2e.test.ts` and `connectionsSettings.e2e.test.ts` render
  production screens with deterministic native harness state. They cover UI
  interaction and geometry, not a real connection to a backend.
- `App.tsx` currently disconnects the active connection immediately when New
  connection is requested. H4 explicitly changes that setup behavior.

## Execution plan

Status: Approved

### Component and lifecycle responsibilities

Extract `ConnectionCard` presentation, a `HomeConnectionsSection` that orders
and limits the list, and a focused helper/hook for connection commands and
health-check state. Preserve connection actions, pinning, and production
entity IDs. Home receives the section as composition rather than absorbing
its command state. Keep one Home scroll owner.

Keep `App.tsx` as the connection/wizard authority. `ConnectedRoot.tsx` owns
navigation and modal coordination, passing existing lifecycle callbacks into
Home. Extract the wizard modal and focused step views from the large render
blocks in App. Move wizard presentation to the app-owned modal opened from Home
and replace references to the removed tab in placeholders, tests, and
navigation. Keep the extraction within connection behavior.

Opening/switching continues through the existing transport construction and
saved-record code. Preserve pending-navigation intent handling and cached
connection/session identities. Do not add automatic connection selection or
change reconnect/failure policies as part of moving the controls. For new
setup, retain the active transport while validating a candidate, then replace
it and disconnect the prior transport only on success. Cancellation invalidates
pending setup so a late result cannot replace the retained connection; clean
up provisional bridge connections without closing the active transport.

Provide an independently testable Home navigation slice with the existing
empty labels/actions where necessary. `030` replaces them with the shared
contextual presentation after `020`; do not create a parallel guidance
component here.

### Delivery steps

1. Update focused production shell/connection tests for the removed tab and
   new Home entry points.
2. Extract and integrate connection content, keeping lifecycle ownership and
   safe scrolling/drag behavior.
3. Extract wizard presentation, move its host, and implement candidate
   validation/handoff while retaining the active connection.
4. Update navigation references/affected native harnesses. Prove a real server
   connection and session journey, including cancellation and failed setup,
   then update current mobile navigation documentation.

### Implementation decisions and open questions

- The card presentation, three-card collapse, footer toggle, modal wizard,
  retained active connection, and focused extraction are approved above.
- Preserve saved IDs, existing transport semantics, pinning preferences, and
  connection deletion behavior. Native folders and provider settings are not
  part of this delivery.
- Shared mobile changes retain Android support. Native acceptance uses the
  iOS simulator; a physical device is not required.

### Documentation

Update `mobile/crystal-lattice-control-rn/docs/home.md` and the applicable
README/development navigation guidance to describe the new Home entry points.
Remove current instructions that direct users to the deleted tab. Keep
first-round authentication/reviewer wording owned by subtask `027`.

### Task checklist

- [x] Confirm the Home interaction/density/wizard choices and execution plan.
- [ ] Extract production connection controls into the top Home section.
- [ ] Move wizard presentation and remove Connections-tab navigation.
- [ ] Retain the current connection through pending, cancelled, or failed
  setup and clean up candidates on successful replacement or cancellation.
- [ ] Preserve saved connection/session state and Home drag behavior.
- [ ] Update affected component/native tests and pass the real connection
  journey.
- [ ] Update maintained mobile navigation documentation and requirement
  evidence.

### Requirement verification

- **H1/H2:** component and native UI checks prove section ordering, unchanged
  card presentation/actions, the three-card boundary and expansion/collapse,
  removed tab, wizard presentation/cancellation, and settings.
  Retain the existing Home and connection-action consumers as regressions.
- **H2/H3/H4 — decisive `Home connection public flow`:** add a Detox scenario
  starting a local real HTTP server with the existing
  `startBackendServer` harness. Launch the production app without substituting
  connection callbacks, use Home's manual connection wizard with that
  server's address, open the connection, create a session through the normal
  agent picker, and confirm it through `RestAgentBackend`. Relaunch and
  reopen the same saved connection/session. While connected, cancel a new
  setup and fail a request to an unavailable address, then prove the current
  connection still serves normal session operations. Successfully create a
  replacement and verify it becomes active. This crosses App transport
  creation, public backend routes, and production navigation together.
  No hosted model or production server is necessary.
- Planned decisive invocation, from the mobile package:
  `npx detox test -c ios.sim.release e2e/homeConnections.e2e.test.ts --cleanup`.
  Add the named scenario during execution; lack of an existing harness
  consumer does not waive the actual connection boundary.

### Additional implementation verification

Run the affected mobile Jest/TypeScript checks and existing Home native
geometry/Watchlist scenario. Check that new top content does not displace
drag calculations or create nested full-screen scroll owners. Native
harness-only runs are reported separately from the real HTTP scenario.
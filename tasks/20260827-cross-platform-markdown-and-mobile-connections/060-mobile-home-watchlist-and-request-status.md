# Mobile Home Watchlist, recent sessions, and derived request status

Add a mobile Home destination without replacing Connections. Home provides a
device-local, reorderable Watchlist with two-column workspace tiles and notes,
a strictly time-bounded Recent Sessions timeline across saved connections,
and lightweight request status that can be read without opening supported
connections.

## Requirements checklist

### Functional requirements

- [x] Mobile primary navigation is `Home`, `Connections`, `Sessions`, and
  `Messages`; Home is selected after local hydration and Connections remains a
  primary destination.
- [x] Home renders without an active backend and aggregates locally known
  sessions by composite `(connectionId, sessionId)` identity.
- [x] The Home header has a top-left menu that initially contains Global
  Settings and a top-right standard pinnable action bar titled `Home actions`.
- [x] Home actions initially provide Global Settings and New Connection, with
  New Session available when a focused usable backend exists; Quick Question
  is deferred until its behavior is defined.
- [x] Global Settings is reachable from Connections actions, the Home menu,
  and Home actions.
- [x] Global Settings contains a Recent Sessions selector with `Last 24
  hours`, `Last 3 days`, and `Last week`; `Last 3 days` is the default.
- [x] The `Recent Sessions` section contains only un-watched sessions whose
  `SessionSummary.modified` timestamp is inside the selected timeframe, sorted
  globally from newest to oldest.
- [x] The `Watchlist` section is separate from Recent Sessions, contains no
  default items, and may retain watched sessions after they age out of the
  recent timeframe.
- [x] Watchlist membership is device-local and does not read, write, invoke,
  or visually reuse server-side session pin metadata or pin actions.
- [x] Watchlist items render as reorderable two-column workspace tiles, and the
  stored order is restored after application reconstruction.
- [x] A session can have a permanent device-local note added, viewed, edited,
  or removed through local actions on both Home and the Sessions tab without
  changing the server session.
- [x] Watchlist tiles visibly indicate and preview an existing note without
  allowing arbitrary note length to make the grid unusable.
- [x] Recent Sessions renders as a vertical timeline feed visually distinct
  from both Watchlist tiles and the operational Sessions-tab list.
- [x] Adding a recent session to the Watchlist removes its duplicate from the
  Recent Sessions timeline; removing it returns it to Recent Sessions when it
  still falls inside the selected timeframe.
- [x] Home session items show the owning connection, session presentation,
  relative modification time, and derived request status when available.
- [x] Selecting a Home session on an open connection focuses that connection,
  selects the exact session, and navigates to Messages.
- [x] Selecting a Home session on a closed connection opens it first and
  navigates only after the current open intent succeeds; failure leaves Home
  visible with scoped recovery feedback.
- [x] Home and the mobile Sessions screen use the same request-status
  normalization and status presentation.
- [x] A bounded application endpoint requires explicit session IDs and returns
  at most one lightweight status projection for each requested existing
  session plus partial missing-ID information.
- [x] The provisional server derives only `idle`, `not_started`, `running`,
  `succeeded`, and `interrupted`: active request means `running`; no
  conversational turn means `idle`; a user tail means `not_started`; a final
  assistant tail means `succeeded`; every other non-final tail means
  `interrupted`.
- [x] A final assistant message is an assistant-role tail with no non-empty
  tool-call metadata; the provisional implementation does not emit paused,
  cancelled, or failed states.
- [x] Supported saved connections can query explicit session statuses without
  opening or focusing a runtime; legacy WebSocket-only bridges report the
  capability as unsupported.
- [x] Modern bridge records may use their authenticated HTTP proxy solely for
  this stateless status read even when their selected normal transport is
  WebSocket; this does not introduce fallback for other requests.
- [x] Closed cloud connections are queried only when the orchestrator
  guarantees that the read cannot start or wake a runtime.
- [x] The Home shell can later expose a real in-process/local App Review
  runtime without requiring a static demo screen or changing Watchlist/session
  identity.

### Non-functional requirements

- [x] Home uses a host-owned open/focus/select/navigation command and does not
  construct transports, promote runtimes, or mutate connection ownership.
- [x] Watchlist storage is versioned, hydration-safe, keyed by composite
  connection/session identity, and stores only local membership and order
  rather than duplicating session summaries.
- [x] Permanent local-note storage is versioned, hydration-safe, keyed by
  session ID alone, and resolves the same note for equal session IDs on
  different connections.
- [x] Watchlist terminology and controls use `Watchlist`, `Add to Watchlist`,
  and `Remove from Watchlist` with a bookmark metaphor; Home does not use Pin,
  Unpin, Pinned, star, or server-pin styling.
- [x] Reordering has both a touch drag interaction and accessible deterministic
  move commands; dragging cannot accidentally navigate the tile.
- [x] Two-column tiles remain usable at every maintained display typography
  preset, with bounded note preview and no title/status/control overlap.
- [x] Recent-window persistence belongs to a mobile global-preferences owner,
  not the markdown-only preference contract.
- [x] Request-status derivation is owned by a replaceable application-layer
  service; FastAPI and an eventual in-process backend are adapters.
- [x] Session-tail classifications are cached by session file-state
  fingerprint and recomputed only when the file changes, while active-request
  state is checked on every query.
- [x] The status endpoint never treats omitted IDs as all sessions, bounds and
  deduplicates input, supports partial missing sessions, and returns no message
  content, provider data, exception detail, credentials, paths, or raw
  metadata.
- [x] One stateless connection query handles all explicit IDs currently needed
  from that connection and never changes focus, navigation, repair state,
  runtime state, or `lastUsedAt`.
- [x] Polling groups displayed IDs by connection, runs only while Home or
  Sessions consumes status in the foreground, supports cancellation/backoff,
  and never opens connections.
- [x] A cached `running` result cannot remain presented as current after its
  query authority becomes unavailable.
- [x] The provisional endpoint and frontend projection can be backed later by
  persisted request-operation notifications without replacing Home or
  Sessions components.
- [x] Production controls and entities expose stable accessibility identifiers
  containing both connection and session identity, and status is not conveyed
  by color alone.
- [x] Automated application, API, SDK, component, integration, iOS, and Android
  evidence covers status derivation, stateless reads, local persistence,
  reordering, notes, timeframe filtering, and cross-connection navigation.

Parent Task:
`tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

Depends On:

- `tasks/20260827-cross-platform-markdown-and-mobile-connections/030-mobile-global-settings-and-markdown.md`
- `tasks/20260827-cross-platform-markdown-and-mobile-connections/040-mobile-connection-actions-and-layout.md`
- `tasks/20260827-cross-platform-markdown-and-mobile-connections/050-responsive-action-headers.md`

## Scope

This subtask owns the first mobile Home screen, local Home data, the
provisional derived-status query, stateless saved-connection status reads,
Home-to-session navigation, and mobile Sessions status rendering.

It coordinates with but does not execute:

- `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`;
- `tasks/20260824-operational-notifications-and-global-attention/010-persistent-request-and-action-errors.md`;
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`;
- `tasks/20260824-operational-notifications-and-global-attention/040-global-attention-frontend-integration.md`;
- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`;
- `tasks/20260820-android-google-play-github-fastlane/085-google-play-review-testable-mode.md`;
- `tasks/20260821-modular-bridge-access-platform/160-mobile-login-purchase-and-subscription-ux.md`.

This work does not implement mobile multi-open runtimes, durable operation
history, persistent request/action errors, global attention, login,
subscriptions, Quick Question, or the bundled local model/runtime.

## Resolved requirement decisions

- Each session ID has at most one permanent device-local plain-text note.
- Notes are keyed by session ID alone. Equal session IDs on different
  connections intentionally show and edit the same note.
- Notes use a separate local namespace from Watchlist membership and order, so
  removing a session from the Watchlist does not remove its note.
- Notes can be added, viewed, edited, and explicitly removed from Home and from
  the Sessions tab.
- Deleting a connection or observing a session missing on one server does not
  remove its note because another connection may use the same session ID.
- The note editor uses the established framed modal, persists a bounded value,
  and exposes a two-line preview where Home layout permits it.

## Supporting details

- Current mobile state persists session-summary caches per saved connection,
  so Home can aggregate locally known sessions before a backend opens.
- `SessionSummary.modified` is the filesystem session record's modification
  time and is the maintained source for the explicit recent cutoff.
- Current mobile owns one active backend. The Home navigation command and
  stateless status reader must therefore be abstractions that the future
  runtime map can replace.
- The existing server exposes active coordinated request IDs but no durable
  latest terminal operation. Persisted session tails are sufficient for the
  explicitly limited initial state vocabulary.
- Persisted messages do not have one universal final flag. The current tool
  loop treats an assistant tail with unresolved tool calls as pending; an
  assistant tail without tool calls is the practical provisional final-answer
  predicate.
- Modern bridge HTTP proxy requests can use a saved pairing token without
  opening a WebSocket. Older WebSocket-only bridges cannot serve the endpoint.
- Server-owned pinning already exists through `session-pinned-app`; the Home
  Watchlist deliberately does not consume that state, avoiding two controls
  that mutate one server value with different availability.
- `ActionsMenuBar`, `PanelModalFrame`, `OptionsPickerModal`, display
  typography presets, and mobile pinned-action persistence are existing
  production patterns to reuse.

## Execution plan
Status: Approved

Implement the feature in dependency order while keeping Home presentation,
connection ownership, and status authority separate.

First extend mobile navigation and global preferences. Add Home as the first of
four primary destinations while retaining the mounted Connections, Sessions,
and Messages workspaces. Introduce a versioned mobile global-preference record
for the recent window with semantic values `24h`, `3d`, and `1w`; do not add
this field to the markdown-only shared preference type. Extend the established
Global Settings modal and startup hydration boundary.

Add a versioned local Home store keyed by encoded `(connectionId, sessionId)`.
Each ordered Watchlist entry contains only that identity and no copied
`SessionSummary`. Add a separate versioned permanent-note map keyed by session
ID alone. Hydration must not overwrite stored order, membership, or notes with
empty startup state. Prune Watchlist entries for a deleted saved connection,
but retain notes until the user explicitly removes them.

Build pure Home selectors that resolve Watchlist identities against saved
connections and cached summaries, preserve explicit Watchlist order, and
produce a separate globally modified-descending Recent Sessions timeline
limited strictly by the selected window. Watched entries are excluded from the
timeline. Watchlist entries may remain visible outside the recent cutoff.

Add a replaceable `SessionRequestStatusService` at the application layer. Its
batch query requires explicit IDs, checks coordinated active requests first,
then resolves cached session-tail classification by current file-state
fingerprint. It emits only the approved provisional vocabulary and exposes a
safe projection. Add one bounded `POST /sessions/request-statuses` HTTP adapter
and an optional frontend SDK backend method.

Add a shared connection status-reader interface with injected factories for
saved records. Direct/discovery records use one `FetchTransport` request.
Modern bridge records use one authenticated HTTP proxy request without
creating a normal Bridge WebSocket runtime; capability/protocol failure maps to
unsupported and token failures map to repair or authorization state. Cloud
uses a single proxy request only under a proven no-wake contract. An open
backend and future in-process runtime return the same normalized projection.

Host one mobile status controller above Home and Sessions. Consumers register
the exact IDs they display; the controller unions and groups them by
connection, issues one cancellable request per connection, polls immediately
and every ten seconds while foreground consumers are active, and uses bounded
backoff on unavailable readers. Runtime/status results remain
connection-scoped. Polling never focuses, opens, repairs, or navigates.

Implement Home using a new design rather than adapting Sessions cards:

- a responsive header with a Settings-only left menu;
- a standard `Home actions` bar with Global Settings and New Connection
  initially pinned and conditional New Session available;
- a `Watchlist` section using exactly two columns of workspace tiles;
- a vertical chronological `Recent Sessions` timeline below it.

Watchlist tiles show session title, owning connection, status, relative
modified time, and a bounded note preview. A dedicated drag handle owns touch
reordering so tile press remains navigation. Persist order after every settled
move. The complete local action menu exposes Add/Edit/Remove Note, Remove from
Watchlist, and accessible Move Earlier/Move Later commands. Recent timeline
items expose Add to Watchlist and Add/Edit/Remove Note. Add the same local note
actions to Sessions-tab session actions. Use bookmark vocabulary and visuals
throughout; do not reuse server pin stars or copy.

Add one host-owned open-and-navigate operation carrying composite identity and
current user-intent authority. Reuse an open connection or open the closed
record through current production ownership. Select/navigate only after
current-intent success. A stale completion cannot navigate after another Home,
connection, tab, or session action.

Render the same request-status component in Home and Sessions while keeping it
separate from user-managed session workflow status, connection runtime status,
cache freshness, and frontend loading. Unknown/unsupported status is quiet
secondary state rather than a blocking alert.

Keep an App Review seam in the host: a future real local/in-process runtime can
supply summaries, derived statuses, new-session behavior, and navigation
through these interfaces. Do not add static review-only session data.

### Implementation decisions and open questions

- **Decision:** Home is added; it does not replace Connections.
- **Decision:** Primary order is Home, Connections, Sessions, Messages, with
  Home selected after hydration.
- **Decision:** Watchlist membership/order and permanent session notes are
  local-only and have no server-side default or synchronization.
- **Decision:** Watchlist uses reorderable two-column workspace tiles; Recent
  Sessions uses a vertical timeline and only the configured timeframe.
- **Decision:** Watchlist items remain separate from and may outlive the recent
  timeframe.
- **Decision:** Global Settings is available from Connections, the Home menu,
  and Home actions.
- **Decision:** Initial Home action defaults are Global Settings and New
  Connection; New Session is conditional and Quick Question is deferred.
- **Decision:** `POST` is used for explicit-ID status batches to avoid
  query-string limits.
- **Decision:** The initial server uses active-request precedence plus session
  tail inference and does not emit paused, cancelled, or failed.
- **Decision:** Stateless status reads never open/wake a runtime or change
  connection state; unsupported connections degrade honestly.
- **Decision:** one bounded plain-text note is stored per session ID in a
  namespace independent from Watchlist membership, remains after Watchlist or
  connection removal, and is editable from Home and Sessions.

### Documentation

- Update mobile current user documentation for Home, local Watchlist/order,
  local notes, Recent Sessions timeframe, status meaning, and unsupported or
  unavailable status behavior.
- Update mobile development documentation for Home ownership, global
  preferences, local store/hydration, status polling, composite navigation,
  App Review seams, and native test entry points.
- Update frontend SDK documentation for the optional status backend method and
  stateless saved-connection reader.
- Update application/terminal HTTP development documentation for the
  explicit-ID derived status service and its non-durable authority.
- Update the mobile connection-lifecycle target documentation because it
  currently specifies three primary destinations.
- Cross-link future lifecycle and notification operation contracts rather than
  duplicating their target behavior.
- Do not present derived status as durable request history in current user
  documentation.

### Task checklist

- [x] Resolve and record the note-model/removal requirement question.
- [x] Add Home to mobile navigation without replacing Connections.
- [x] Add and persist the global recent-session window.
- [x] Extend Global Settings with the recent-window selector.
- [x] Implement versioned Watchlist membership/order and permanent session-note
  storage.
- [x] Implement pure Watchlist and Recent Sessions selectors.
- [x] Implement application-layer explicit-ID status derivation and caching.
- [x] Add the bounded HTTP endpoint and frontend SDK backend method.
- [x] Add stateless status readers for supported connection kinds.
- [x] Add the scoped mobile status polling controller.
- [x] Implement Home header menu and pinnable Home actions.
- [x] Implement reorderable two-column Watchlist tiles and the shared local
  note modal/actions on Home and Sessions.
- [x] Implement the vertical Recent Sessions timeline.
- [x] Implement current-intent open-and-navigate session routing.
- [x] Add the shared Home/Sessions request-status presentation.
- [x] Add application, API, SDK, component, integration, iOS, and Android
  verification.
- [x] Update owning current user/development documentation and target
  specification.

### Requirement verification

- Navigation: production component/native tests prove all four destinations
  remain reachable, Home starts after hydration, and Home does not replace
  Connections.
- Settings/actions: tests open Global Settings from all three paths, persist
  `24h`/`3d`/`1w`, preserve Home action pins, and enforce conditional New
  Session availability.
- Watchlist/note storage: delayed-hydration/reconstruction tests prove no
  default membership, composite Watchlist identity, persisted manual order,
  session-ID note sharing across connections, permanent notes independent from
  Watchlist/connection removal, and explicit note deletion.
- Watchlist UI: component and Detox geometry verify exactly two columns,
  complete tiles at default/largest typography, bounded note previews, drag
  reorder persistence, no navigation during drag, and accessible move
  alternatives.
- Recent timeline: controlled-clock tests prove strict timeframe inclusion,
  global modified ordering, Watchlist deduplication, and immediate setting
  updates.
- Status derivation: application tests cover active `running`, empty `idle`,
  user-tail `not_started`, final assistant `succeeded`, assistant tool-call and
  tool-tail `interrupted`, file-fingerprint cache reuse/invalidation, bounded
  explicit IDs, and partial missing sessions.
- API/SDK safety: public route/backend tests prove no implicit all-session
  query, normalized projections, forward compatibility, and absence of message
  or sensitive fields.
- Stateless reads: transport tests prove one direct request, modern bridge HTTP
  side-channel behavior, legacy bridge unsupported behavior, bridge
  credential errors, cloud no-wake behavior, cancellation, and no
  runtime/focus/`lastUsedAt` mutation.
- Polling: fake-timer/controller tests prove per-connection batching,
  foreground consumer ownership, ten-second cadence, cancellation/backoff, and
  stale-running suppression.
- Navigation authority: delayed open tests prove exact composite destination,
  no wrong-connection same-ID collision, failure retention on Home, and no
  navigation from stale completion or status polling.
- App Review seam: a deterministic in-process adapter renders production Home
  and completes Home-to-session navigation without static duplicate UI.

### Additional implementation verification

- Run focused and full application Python suites affected by request
  coordination, session loading, routes, bridge/cloud adapters, and session
  listing.
- Run frontend SDK fast tests, type checking, and focused public-backend
  integration.
- Run shared React Native component tests if status/tile primitives are placed
  there.
- Run complete mobile Jest and TypeScript checks.
- Build fresh iOS and Android Detox applications and run focused Home,
  Connections/Settings, session-list, bridge transport, and navigation
  scenarios on both platforms.
- Run `git diff --check` and the relevant package documentation preparation and
  build checks.

## Implementation Notes

- The approved note model was corrected during execution: Watchlist identity
  remains `(connectionId, sessionId)`, while permanent local notes are keyed
  only by session ID and intentionally resolve across equal IDs on different
  connections.
- Home uses a new presentation rather than adapting Sessions cards:
  reorderable two-column Watchlist tiles above a chronological Recent Sessions
  timeline.
- The provisional application status service checks coordinated active
  requests before a session-tail classification cached by the store's opaque
  revision. It emits only the approved five-state vocabulary.
- Closed manual/discovery records use direct HTTP; modern bridge records use
  the authenticated HTTP proxy without opening WebSocket; closed cloud and
  unsupported legacy bridge paths degrade without opening a runtime.
- Polling uses independent cancellable per-connection timers, bounded backoff,
  and removes stale Running state. Authoritative missing IDs prune Watchlist
  entries but never remove permanent notes.
- The existing TypeScript backend integration runner's delayed `SessionStore`
  wrapper did not implement snapshot-aware `load` or current record methods.
  Completing that production test-infrastructure adapter restored its timing
  matrix and allowed the new isolated status integration to remain
  state-independent.
- Android native retries initially failed before app assertions because the
  saved Play Store launcher snapshot repeatedly entered ANR and held window
  focus. Wiping that test AVD and running cold boots with snapshot
  load/save disabled produced clean passing Home, Connections, Sessions, and
  bridge runs.
- Two desktop Xcode project files changed concurrently during this work. They
  are unrelated to mobile Home/status scope and were preserved without edits
  or inclusion in this task's evidence.

## Completion Notes

- Delivered Home as a fourth initial mobile destination while retaining
  Connections, Sessions, and Messages.
- Delivered a device-local Watchlist with no default items, exact two-column
  tiles, touch drag plus accessible reordering, persisted order, separate
  Recent Sessions timeline, and 24-hour/3-day/1-week global setting.
- Delivered permanent session-ID notes shared across connections and editable
  from Home and Sessions; Watchlist or connection removal does not delete
  notes.
- Delivered explicit-ID derived request status across `agent_app`, FastAPI,
  frontend SDK, stateless saved-connection readers, Home, and Sessions.
- Delivered current-intent closed-connection opening/navigation, standard Home
  actions, three Global Settings entry points, and local/in-process runtime
  seams for review-mode follow-up.
- Verification passed:
  - core default suite: 477 passed, 26 deselected, 1 expected xfail;
  - application default suite: 358 passed, 90 deselected;
  - frontend SDK fast suite: 316 passed;
  - frontend SDK real-backend matrix: 20 passed;
  - isolated real FastAPI/HTTP/`RestAgentBackend` status integration: 1 passed;
  - mobile Jest: 156 passed; mobile TypeScript passed;
  - fresh iOS and Android E2E builds passed;
  - Home, Connections/Settings, two-case Sessions list, and bridge native
    scenarios passed on iOS and Android;
  - Ruff, Black check, `git diff --check`, documentation preparation, and
    MkDocs build passed.
- MkDocs retained its existing generated-navigation, Griffe indentation, and
  unresolved-reference warnings; this work added no build failure.
- The provisional status source deliberately does not emit paused, cancelled,
  or failed. Closed cloud status remains unsupported unless a future
  orchestrator contract guarantees a no-wake read.

## Post-completion follow-up

Status: Approved

The user approved a focused correction to Watchlist reordering and Recent
Sessions behavior after evaluating the delivered Home screen. This follow-up
supersedes the earlier requirements and verification statements that excluded
watched sessions from Recent Sessions.

### Follow-up requirements

- [x] A drag started from a Watchlist move handle captures predominantly
  vertical as well as horizontal movement without the Home scroll view taking
  over; ordinary gestures started outside a move handle continue to scroll
  Home.
- [x] Watchlist reordering previews the prospective order during the gesture
  with a same-sized empty placeholder at the future position and persists only
  the settled order on release.
- [x] Drag target resolution uses measured tile geometry, supports
  variable-height two-column tiles, and can auto-scroll within bounded Home
  content when the pointer reaches a viewport edge.
- [x] A watched session remains in Recent Sessions whenever its modification
  timestamp is inside the selected recent window.
- [x] Removing a watched session uses a close (`x`) icon; the bookmark remains
  the Add to Watchlist metaphor in Recent Sessions.
- [x] Touch, accessibility, component, state, and native verification cover
  the corrected behavior without hardcoding typography or unrelated theme
  preset values.
- [x] Current mobile user and development documentation describes the
  inclusive Recent Sessions behavior and grid-owned drag interaction.

### Follow-up execution plan

Move transient drag ownership to the Watchlist grid while retaining one
dedicated responder handle per tile. Capture responder ownership immediately
from the handle, disable user scrolling only for the active drag, reject
responder termination, and leave ordinary Home scrolling untouched elsewhere.

Measure rendered tile slots and snapshot them when a drag starts. Resolve the
nearest target from the dragged tile center, current gesture translation, and
programmatic scroll delta. Render the dragged tile as an elevated absolute
overlay and render a same-size placeholder in a transient preview order.
Persist one final move on release; cancellation restores the original order.
Use bounded edge scrolling for Watchlists extending beyond the viewport.

Remove Watchlist identity from the Recent Sessions selector filter. Keep the
strict configured timeframe and global modified-descending order, allowing the
same session to appear in both purposefully distinct Home sections. Make the
Recent bookmark action idempotent for an already watched session and change
only the Watchlist removal icon to `x`.

Add pure geometry/preview tests, component coverage for placeholder and scroll
ownership, selector and icon regressions, and iOS/Android Home Detox coverage
for predominantly vertical drag, normal scrolling, persistence, and inclusive
Recent Sessions. Update the owning Home user/development pages and lifecycle
description.

### Follow-up task checklist

- [x] Add measured-slot drag geometry and preview helpers.
- [x] Refactor Home Watchlist drag ownership and live placeholder rendering.
- [x] Keep watched sessions in Recent Sessions and update action state.
- [x] Replace the Watchlist removal bookmark with a close icon.
- [x] Add state, component, and native regressions.
- [x] Update owning documentation and lifecycle wording.
- [x] Run mobile unit/type/native verification and record evidence.

### Follow-up implementation notes

- The first live-preview implementation rendered the dragged keyed tile after
  the preview slots. Fabric terminated the native responder when that child
  moved in the React child list, even though component simulation remained
  green. The final render-slot model keeps the responder-owning child at its
  original index, absolutely positions it as the overlay, and independently
  reorders only the non-dragged layout slots and placeholder.
- The grid snapshots measured slot frames at gesture start, adjusts the dragged
  center for programmatic scroll offset, resolves the nearest measured slot,
  and maintains only the target index in React state. Translation remains on
  `Animated.ValueXY`, avoiding a React render for every pointer update.
- Recent Sessions now applies only the selected time cutoff and modified-time
  sort. A qualifying watched session appears in both sections; its Recent
  bookmark is disabled and labeled `In Watchlist` until membership is removed.
- Detox's `longPressAndDrag` is effective only on iOS in the installed Detox
  version. The native regression therefore uses exact handle-to-handle
  vertical drag on iOS and a screen-distance vertical handle swipe on Android.
- The dedicated Android 36.1 AVD has one CPU core and 2 GB RAM and repeatedly
  raised a pre-application System UI ANR. The successful Android run used a
  cold boot with temporary four-core/4-GB runtime overrides and snapshot
  load/save disabled. No repository or permanent AVD configuration changed.

### Follow-up completion notes

- Delivered grid-owned live reordering with immediate handle capture, stable
  native responder ownership, an elevated dragged tile, a same-size target
  placeholder, measured variable-height target geometry, bounded edge scroll,
  cancellation rollback, and one settled persistence update.
- Delivered inclusive Recent Sessions semantics and an idempotent watched
  state while retaining strict `24h`, `3d`, and `1w` cutoffs.
- Replaced the Watchlist removal bookmark with a neutral close (`x`) icon;
  Recent Sessions retains the bookmark as its add metaphor.
- Verification passed:
  - mobile Jest: 40 suites and 160 tests;
  - mobile TypeScript and focused source-format checks;
  - focused measured-slot, placeholder, responder/scroll, inclusive Recent,
    action-state, and icon regressions;
  - fresh iOS and Android Detox builds;
  - the complete updated Home Detox scenario on iOS and Android, including
    predominantly vertical reorder, persisted geometry, normal timeline
    scrolling, inclusive watched recents, and Watchlist-only removal;
  - `git diff --check` and obsolete current-document wording search.
- Targeted ESLint was unavailable because this mobile package currently has no
  ESLint configuration file; TypeScript, Prettier, Jest, native builds, and
  native execution completed successfully.

### Settled-order optimism correction

Status: Complete

- [x] Releasing a successful Watchlist drag immediately renders the settled
  order and never exposes the pre-move arrangement while the workspace context
  propagates or persists the move.
- [x] The optimistic projection is keyed by session identity, reconciles with
  the current resolved tiles, clears when context acknowledges the target
  order, and yields to a competing membership or order change.
- [x] Focused projection and Home component regressions plus mobile TypeScript
  verification cover the correction.
- [x] Current Home user and development documentation describes the immediate
  settled placement.

The correction keeps a local source/target key projection when release clears
the drag overlay. `HomeScreen` applies the target keys to the latest resolved
tile objects, so note, status, membership, and cache updates remain current.
The projection is removed after context reports the target order; an order
that matches neither the source nor target is treated as newer authority and
also removes the projection.

Verification passed with the focused Home/projection regressions, the complete
mobile Jest suite (40 suites, 161 tests), mobile TypeScript, and
`git diff --check`. Native drag geometry and persistence were unchanged and
remain covered by the preceding successful iOS and Android Home runs.

### Placeholder handoff correction

Status: Complete

- [x] Releasing a moved card snaps the still-rendered drag overlay directly
  onto the measured placeholder without animation.
- [x] The overlay and preview ordering remain visible until the workspace
  context reports the final target order; only then do ordinary final tiles
  replace them.
- [x] Animated translation never resets to the source position while the
  overlay remains mounted.
- [x] Measured placeholder-offset and Home drag regressions plus mobile
  TypeScript verification cover the handoff.

The previous optimistic key projection removed the source-order context gap,
but resetting `Animated.ValueXY` during the release callback could still move
the mounted overlay back to its source for one frame. The drag now enters a
`settling` phase, snaps the overlay translation to the target slot delta, and
uses the stored source order to keep the preview composition stable even after
context receives the target order. Context acknowledgement unmounts the
overlay first; a subsequent effect then resets its translation.

Verification passed with the focused Home and measured-offset regressions, the
complete mobile Jest suite (40 suites, 162 tests), mobile TypeScript, and
`git diff --check`.

### Cross-platform Home parity and session-action follow-up

Status: Approved

This mobile-owned follow-up is coordinated by the approved execution plan in
`tasks/20260827-cross-platform-markdown-and-mobile-connections/070-desktop-home-history-status-and-preview-tabs.md`.
It reopens only the mobile Home and local-session-action behavior listed
below. Each coordinated completion chunk owns its mobile verification and
documentation.

The revised Chunk 3 presentation plan in that coordinating task is
`Approved`. Mobile and desktop keep independently owned platform layouts while
targeting the agreed current fallback and visual alignment.

#### Functional requirements

- [x] Mobile Sessions and Messages expose a local, state-aware `Add to
  Watchlist` or `Remove from Watchlist` session action. The action changes only
  device-local Watchlist membership and remains distinct from server-side
  session pinning.
- [ ] Mobile Watchlist cards and Recent Sessions timeline rows closely align
  with their desktop equivalents in current information hierarchy and visual
  rhythm: title, optional subtitle, session ID, connection name, relative
  time, request status, note, and relevant local actions. Platform-specific
  visual drift remains supported.
- [x] A message preview is rendered exactly once as the fallback when both
  title and subtitle are absent.
- [x] Long connection names and session IDs truncate without displacing the
  relative time or local actions; connection-name and time truncation are
  independent.
- [x] Timeline rail dots are neutral gray. Request-status indicators retain
  their semantic state colors.

#### Non-functional requirements

- [x] Mobile owns its Watchlist-card, timeline, display fallback,
  relative-time formatting, styles, and accessibility identifiers. It reuses
  existing shared Home data, status, theme, and reorder contracts without
  introducing shared React presentation components.
- [x] The local Watchlist action uses the existing static session-action
  extension points and pinnable action infrastructure; it does not require a
  backend, application plugin, or transport mutation.
- [x] Mobile component tests derive expected presentation from the SDK
  session-list fallback and active theme rather than duplicating mutable
  layout or typography values.
- [x] Mobile Jest and focused iOS/Android Detox scenarios verify Sessions and
  Messages Watchlist actions, long-name timestamp visibility, field fallback,
  and the mobile-owned card/timeline structure against the coordinated
  alignment fixture.

#### Follow-up task checklist

- [x] Complete the mobile portion of coordinated Chunk 2: local Watchlist
  actions in Sessions and Messages.
- [x] Complete the mobile portion of coordinated Chunk 3: independently owned
  Home presentation, field fallback, truncation, and neutral timeline dots.
- [x] Update current mobile Home/session-navigation documentation.
- [x] Record mobile component, type, iOS, and Android evidence with the owning
  completion chunk.

#### Chunk 2 mobile completion notes

- Sessions and Messages now add the same state-aware local Watchlist
  definition to their existing pinnable Session actions. The action is
  available without a backend after local hydration and remains separate from
  plugin/server pin state.
- Shared action rows now expose explicit accessibility activation. Local
  actions remain disabled during Home hydration, and pinned-action state
  preserves a user update that races an older storage read without losing
  built-in or plugin defaults.
- Verification passed with the complete mobile Jest suite (42 suites, 182
  tests), mobile TypeScript, final iOS and Android builds, the complete iOS
  Session-list and rich-session Detox suites (4 tests), and focused Android
  Sessions and Messages Detox scenarios (2 tests). Two retries of an
  unrelated Android geometry scenario were blocked by emulator
  window-focus/ANR failures before useful interaction; its iOS counterpart
  passed.
- Current mobile Home and development documentation describes the new
  Session-action entry points and hydration ownership. Chunk 3 presentation
  documentation and native evidence remain open.

#### Chunk 3 mobile implementation notes

- Mobile retains its local `WatchlistTile`, timeline markup, relative-time
  formatter, fallback helper, styles, and field identifiers. No shared React
  presentation component or display model was introduced.
- Watchlist and Recent now render title, optional subtitle or distinct
  preview, session ID, request status, note, and a final metadata row.
  Connection is the flexible one-line child; time and action controls do not
  shrink.
- Timeline status uses the inline semantic variant and its rail uses the
  mobile theme's neutral `textMuted`. Watchlist status remains a badge.
- Existing two-column measured drag, target placeholder, settling overlay,
  inclusive Recent behavior, note actions, and navigation remain owned by and
  unchanged in the mobile host.

#### Chunk 3 mobile completion notes

- Preview fallback and controlled relative-time behavior have independent
  mobile unit coverage across supplied, missing, duplicate, and
  whitespace-only title/subtitle/preview combinations.
- Mobile component coverage derives typography from the active theme and
  verifies field order, one-line truncation props, flexible connection,
  non-shrinking time/actions, neutral rail color, and preview de-duplication.
- Verification passed:
  - mobile Jest: 44 suites and 197 tests;
  - mobile TypeScript;
  - fresh iOS and Android E2E builds;
  - complete updated Home Detox scenario on iOS and Android, including
    long-name metadata geometry, preview-only behavior, both Watchlist
    columns, drag/settling, persistence, notes, settings, and navigation;
  - targeted Prettier, `git diff --check`, and documentation preparation.
- Two default-resource Android attempts lost application-window focus in the
  Android 36.1 emulator. The final scenario passed with temporary four-core,
  4-GB, no-snapshot boot arguments; no repository or permanent AVD setting
  changed.
- The Home E2E test also replaced its stale pre-existing
  `options-picker-option-24h` selector with the current production
  `options-picker-declared-24h` identifier exposed by the picker.
- Targeted mobile ESLint remains unavailable because the package has no ESLint
  configuration file.

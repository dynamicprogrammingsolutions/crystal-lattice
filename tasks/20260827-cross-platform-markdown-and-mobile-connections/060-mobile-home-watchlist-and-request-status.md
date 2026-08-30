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
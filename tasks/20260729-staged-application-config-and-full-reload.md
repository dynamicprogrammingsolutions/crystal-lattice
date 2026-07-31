# Staged Application Configuration and Full Reload

Deliver application-level configuration actions through a deliberately staged
implementation. The initial product path asks the owning runtime to reconstruct
the complete `AgentApplication` after active work drains while the surrounding
CLI/server process remains alive; narrower runtime refactoring, general
configuration writing, and live migration of active requests remain
conditional follow-up work.

## Requirements checklist

- [x] A sample application plugin contributes discoverable application actions
  for reloading the selected application and changing a provider API key.
- [x] The production application-action surface can render and execute the
  sample plugin without feature-specific frontend behavior; credential input is
  masked and is not prefilled after submission or dismissal.
- [x] The application can signal its owning process that a full reload is
  requested, and can separately signal when all active operations have drained
  and replacement is safe.
- [x] Reload actions return promptly after the request is accepted; generic
  application-level notifications communicate reload requested, completed, and
  failed states to the connected frontend without requiring a selected session.
- [x] Once reload is requested, active work may finish but new application
  operations are rejected until replacement completes.
- [x] A successful full reload reconstructs the complete `AgentApplication`
  while keeping its owning CLI/server process alive and applies arbitrary valid
  configuration changes, including plugin additions, removals, and source
  revisions supported by the plugin lifecycle contract.
- [x] Reload is coordinated across every request entry point owned by the CLI
  process so server and console behavior cannot diverge after activation.
- [x] A failed reload leaves a usable previously active application and reports
  the failure through standard application-action handling.
- [x] Restart coordination is independent of how an owning process or plugin
  persists settings, allowing desktop `.env`, JSON/overlay, and device-specific
  protected stores to supply values to a newly created `AgentApplication`.
- [x] The desktop sample plugin reads its environment-file path and explicit
  editable-key allowlist from application configuration; the expected default
  environment file is `~/.crystal/.env`.
- [ ] Before the credential-changing action is considered production-ready, it
  prevents credential disclosure and rejects execution through connection
  classes that do not satisfy the approved security policy.
- [x] Full-reload integration coverage exercises public application behavior
  with both a general configuration change and a plugin-catalog change.
- [x] Replacing the application closes the retired application's MCP registries,
  MCP server sessions/transports, runtime-store values, and other plugin-owned
  resources before reload is reported complete.
- [ ] Delivery is divided into manually approved stages; only the next stage is
  planned, and no later stage begins until the current stage passes its manual
  checkpoint.
- [ ] If completion requires a materially more complicated solution than the
  approved stage plan or crosses an approved ownership boundary—for example, a
  plugin-local feature unexpectedly requires broader platform changes—work
  stops and the user approves a revised plan before implementation continues.
- [x] The public application-level notification contract is documented,
  including event scope, payload fields, lifecycle, de-duplication, event
  polling, persistence/reconnect limits, presentation semantics, and failure
  behavior.
- [ ] Application notifications with banner presentation render in a
  connection-global banner rail within every mobile screen and desktop pane,
  with
  distinct opaque info, success, warning, and error colors and accessible
  dismissal. On mobile the rail participates in normal layout immediately
  below the screen header; on Sessions it is below the search/filter row, and
  it pushes the remaining active-screen content down instead of overlaying it.
- [x] Desktop snapshot-selection/read-only feedback composes the same shared
  banner primitive while remaining scoped to its Messages pane.
- [ ] The top of the mobile and desktop Sessions surfaces uses the reusable
  pinnable actions bar for server settings, session-list refresh, new-session
  creation, and plugin-contributed application actions.
- [ ] Desktop Sessions actions follow existing macOS conventions: the action
  menu uses the native anchored popover, server settings open in a separate
  React Native macOS window, new session uses the existing agent-picker window,
  and application-action forms use the existing desktop action-dialog
  presentation.
- [ ] Application notifications and Sessions actions remain isolated by
  backend connection, including when the desktop has multiple open
  connections.
- [x] Persistent session notifications are implemented according to the
  non-blocking Stage 1 contract in
  `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`
  through `040-stage-1-dummy-plugin-integration-tests.md`.
- [x] The display contract documents and enforces producer- and host-specific
  presentation support: application notifications support `banner` and mobile
  `modal` but reject `inline`; session notifications and direct action
  responses support `banner`, `inline`, and mobile `modal`; desktop normalizes
  notification `modal` to `inline` because React Native modal presentation is
  unsupported there.
- [ ] Desktop routes every banner presentation—application-global,
  session-scoped, or action-response—to the same connection-aware top banner
  rail.
- [x] Dedicated demonstration plugins can trigger application notifications,
  session notifications, and direct action responses for every presentation
  supported by their producer/host contract and every semantic variant without
  being enabled in production default configuration.
- [x] Notification delivery is revision-aware: dismissing one revision does
  not suppress a later update of the same lifecycle notification, resolved
  notifications are removed without redisplay, and an active session shows a
  newly persisted session notification without requiring navigation away and
  back.

Supports:
`tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`

Implements the non-blocking Stage 1 overlap from:
`tasks/20260619-generic-session-notifications/000-main.md`

## Requirement questions

- Which connection classes and authentication/provenance checks constitute the
  final approved security policy for provider credential changes?

## Approved delivery constraints

- The first demonstrable stage is intentionally a simple sample implementation:
  no general configuration-writing API and no additional credential transport
  restrictions.
- In that first stage, the desktop sample plugin may update its configured
  `.env` file directly and only for explicitly configured editable keys.
- The secret frontend field may be introduced in the first stage even though
  backend credential hardening is deferred.
- Full reload waits for active work to drain, rejects new operations after the
  reload request is registered, and reconstructs `AgentApplication` inside the
  existing owner process.
- The reload action returns an accepted result without waiting for drain. The
  owner emits generic application-level notifications for requested,
  completed, and failed reload states.
- The initial implementation borrowed only the notification envelope and
  lifecycle/display patterns. The approved checkpoint follow-up now completes
  the generic session-notification task's non-blocking Stage 1 (010–040),
  including persistent session metadata, while leaving every Stage 2
  interaction subtask out of scope.
- All application-dependent HTTP/terminal operations and background
  model/tool workers participate in drain accounting. Passive HTTP, bridge,
  and Bonjour listeners remain alive.
- Closing the old application must synchronously drain MCP registries and their
  managed sessions/transports before the owner publishes reload completion.
- If an editable dotenv key is already supplied by `os.environ`, the desktop
  plugin rejects the update as externally managed.
- Credential-action hardening is a required follow-up outcome.
- A general plugin-owned JSON configuration-writing API is optional when the
  desktop environment writer can be made production-safe and other owners can
  inject settings from platform-appropriate stores during reconstruction.
- Refactoring `AgentApplication` and changing a running request to adopt a new
  configuration are conditional. They may be postponed when complete
  application reload is functionally sufficient and further work would add
  disproportionate complexity.

## Completion constraint

During implementation or completion, stop and ask the user before proceeding
when a requirement would need a materially more complicated solution than this
approved stage plan or would cross a planned ownership/module boundary. This
includes discovering that behavior assigned to the sample plugin needs an
unplanned platform, core, server, SDK, or frontend capability. Record the
finding, return the Stage 1 plan to `Draft`, and obtain approval for the revised
scope. Do not treat an apparently useful broader refactor as implicit
authorization.

## Ground truths

- On the base `develop` implementation, `AgentApplication` resolves
  configuration, plugin catalogs, per-agent runtimes, application-plugin state,
  runtime services, and contexts during construction; it has no supported
  operation that reconstructs those fields.
- `ToolLoopRunner` is request-local, but `AgentApplication.send_request` owns
  lifecycle work around it, including application-plugin callbacks,
  configuration refresh, checkpoints, and cancellation.
- The HTTP server executes requests in background workers that retain an
  application reference. Combined server/console mode must therefore coordinate
  ownership before replacing that application.
- An application plugin cannot synchronously close and replace the application
  while its own action is executing. Full reload requires a post-action
  coordinator or another outer ownership boundary.
- Restart coordination requires two distinct owner-facing transitions:
  reload requested, followed by reload ready after operation admission is
  closed and active work reaches zero.
- Reconstructing an `AgentApplication` in the same Python process does not by
  itself unload module globals, native libraries, bound ports, or plugin-owned
  background resources. Plugins satisfying the application lifecycle contract
  are reloadable; incompatible process-global plugins may report that the
  existing manual CLI stop/start fallback is required.
- Editing `.env` does not update already-resolved configuration or arbitrary
  values already present in `os.environ`; full reload must deliberately
  re-resolve the intended environment source.
- Sessions, events, snapshots, and persisted runtime data must remain available
  across a successful full reload.
- Existing frontend event polling is session-scoped, while reload is
  application-global. A minimal global event subscription must not attach the
  reload notification to an arbitrary session or duplicate it into every
  session.
- The Stage 1 implementation currently owns global polling and rendering in
  mobile `SessionsScreen`, so notifications disappear with that screen and
  desktop does not consume them.
- Desktop already has a tested four-variant `NotificationBanner`, but it is
  desktop-local and currently used only by its notification test window.
- Mobile Sessions currently renders a separate non-pinnable application-action
  menu beside standalone server-settings, refresh, and new-session controls.
  Desktop Sessions has standalone refresh/new controls and does not yet expose
  application actions or server settings.
- Shared `ActionsMenuBar` already supports persisted pinning and the native
  macOS `NSPopover` path. Desktop's Messages pane already routes settings to a
  separate React window and application-action dialogs through the macOS
  action-dialog coordinator.
- The generic desktop `openReactWindow` API can host a server-settings window;
  this follow-up should not require a new Objective-C window-manager method.
- `mcp-runtime-app` stores its registry in the application runtime store.
  `AgentApplication.close()` closes runtime-store values, and `MCPRegistry.close`
  synchronously waits for `clear_all()` through the application's async runtime
  host. Full replacement must preserve and verify this shutdown path.
- The dependent iOS App Review runtime must expose provider-key and bundled-agent
  settings through the same application configuration/restart behavior, but it
  uses a fixed reviewed plugin set, app-sandboxed persistence, and potentially a
  device-specific protected secret store rather than desktop `.env` editing.
- The shared restart contract must therefore carry no storage-specific or raw
  secret assumptions. The owning desktop CLI or iOS runtime is responsible for
  reconstructing `AgentApplication` with its current configuration inputs.
- The broader generation-based implementation and its review follow-ups are
  preserved separately on
  `draft/application-config-runtime-reload-generations`.

## Conditional follow-up scope

- A general plugin-owned JSON configuration mutation and transaction API.
- A self-contained request execution that can continue on its original
  configuration, migrate at a safe boundary, or cancel during activation.
- A smaller request-runtime snapshot replacing whole-application generations.
- Hot configuration activation while requests remain active.
- In-process plugin revision coexistence beyond what complete application
  reconstruction can safely provide.

## Proposed stages

### Stage 1 — Full application replacement and sample environment plugin

Keep the CLI/server process alive while an owner-level coordinator closes
application-operation admission, drains active work, constructs a candidate
`AgentApplication`, atomically replaces the selected application, and reopens
admission. Add the generic application-action frontend surface, masked secret
input, and a sample plugin that can request reload or update one explicitly
allowlisted key in a configured dotenv file before requesting reload.

The action returns immediately after reload is registered. The owner publishes
application-global notification lifecycle events for reload requested,
completed, and failed. A minimal global frontend event subscriber renders the
notification on the Sessions screen or another connection-global host using
the existing action-display presentation.

Stage 1 includes realistic integration coverage for configuration changes,
plugin additions/removals, drain-and-reject behavior, candidate failure, shared
server/console ownership, and persisted session continuity. It intentionally
does not add new credential transport restrictions, protected secret storage,
or a general JSON configuration mutation API.

Completion requires a manual checkpoint. No later stage is planned until that
checkpoint is approved.

### Stage 2 — Optional general configuration mutation

Add an application-owned JSON/overlay mutation and transaction API only if the
Stage 1 checkpoint or dependent iOS design demonstrates a concrete setting that
cannot be represented by allowlisted environment values or owner-supplied
configuration inputs.

### Stage 3 — Required credential-action hardening

Make credential-changing application actions production-safe through the
approved transport/authentication policy, secret persistence and precedence
contract, response/config/log redaction, masked/no-prefill UI behavior, and
failure-safe updates. This stage remains required whether Stage 2 is performed
or skipped.

### Stage 4 — Optional self-contained request execution

Refactor the complete request lifecycle out of mutable `AgentApplication` state
only if full replacement leaves problematic request ownership or maintenance
complexity.

### Stage 5 — Optional live config-only activation

For reloads that do not change plugin topology, optionally allow active requests
to continue with their old config, adopt the new config at a safe phase
boundary, or cancel according to an explicit application policy. This remains
conditional on a demonstrated product need and the Stage 4 request boundary.

## Draft implementation reuse assessment

The preserved generation-based draft was reviewed against Stage 1.

Reusable with little or no design change:

- The SDK `application_action` element type, compound `(plugin, action)`
  identity, declaration normalization, diagnostics, and focused unit tests.
- The connection-scoped application-action registry state and React exposure.
- The shared React Native `ApplicationActionsMenu` and Sessions-header host.
- Secret/password `TextInput` masking, disabled autocapitalization/autocorrect,
  and no-prefill behavior. Only the focused lines should be ported to avoid the
  draft's unrelated whole-file formatting churn.
- The application-action menu/component and real-backend test patterns.
- The generic session-notification task's `ActionDisplayPayload`, event merge,
  and existing display-card approach. Stage 1 adapts these to an
  application-global, non-session-persistent notification rather than porting
  the full notification subsystem.
- The sample plugin package/manifest scaffold, action/UI declarations, generic
  success displays, and default-config registration after replacing its
  generation/protected-secret execution methods.
- The combined `--server --console` decision to construct one shared
  application and its lifecycle regression test.

Reusable after adaptation:

- Application-action invalidation and `reload_application_actions` UI effect.
  In Stage 1 it must run after owner-level replacement completes, not after
  generation publication.
- The sample plugin tests and application-action endpoint tests. Assertions
  must target reload requests, dotenv allowlists, full replacement, and the
  intentionally unhardened Stage 1 transport behavior.
- The production mobile integration test. It should exercise the real owner,
  backend adapter, reload action, and post-replacement action discovery without
  asserting the draft's protected-secret implementation.

Not reused for Stage 1:

- The `_ApplicationGeneration`/facade split, thread-local routing, generation
  leases, retired-generation cancellation routing, and generation tests.
- Protected secret placeholders/store, config-secret transaction journal, and
  credential precedence changes.
- Transport provenance, bridge signing, credential endpoint redaction, and
  related tests.
- Generation-aware terminal core caching, session codec changes, and HTTP
  generation reservations.
- Bash/Node generated-proxy coexistence metadata and hot-replacement policy.
- Documentation describing immutable generations or protected credentials.

## Execution plan
Status: Approved

This plan covers Stage 1 only. Execution stops at its manual checkpoint; later
stages remain unplanned.

The original Stage 1 implementation reached its manual checkpoint. Review
requested the notification-contract and cross-platform UI follow-up below.
Those changes remain part of Stage 1 and require approval before execution
resumes.

### Stage 1 approach

Introduce a small owner-level reload coordinator rather than modifying
`AgentApplication` into a proxy. The coordinator owns the current application,
an application factory, an admission state, active-operation accounting, and
the reload-requested/reload-ready transitions. Its control contract is
storage-agnostic so the desktop CLI and the dependent embedded iOS runtime can
use different configuration stores.

The application action returns a generic owner-control reload request. The
action host registers it, closes admission, publishes a reload-requested
application notification, and returns an accepted standard action result
without waiting for drain. An owner worker waits for existing operations,
constructs the candidate while the old application remains available but
quiescent, and performs replacement. On success it swaps the owner reference,
updates server and terminal consumers, closes the old application—including
waiting for MCP registry/server cleanup—reopens admission, publishes
reload-completed, and invalidates application-action discovery. On candidate or
cleanup failure it closes any partial candidate, retains the old application
where possible, reopens admission, and publishes reload-failed.

Every operation that can retain or call an application must participate in the
owner gate. HTTP request lifetime and background model/tool workers need
separate leases because the HTTP send-start response completes before its
worker. Terminal operations use the same owner. Once reload is pending, new
application-dependent operations fail with one stable reload-pending error;
passive process infrastructure such as the HTTP listener, bridge connection,
and Bonjour advertisement remains alive.

Add only the minimal application-global notification substrate needed by this
stage. Notifications reuse `ActionDisplayPayload` and created/updated lifecycle
semantics from the generic session-notification task, but are owned by the
stable application owner rather than `Session.metadata`. The stable event store
publishes application notification events across application replacement. The
SDK gains an explicitly global polling mode, notification event types and merge
helper, and a small connection-global/Sessions host. Existing session polling
semantics remain unchanged.

Combined server/console mode creates one owner and one application. The
terminal receives an explicit replacement callback or owner reference and
clears cached core/base-config/UI state after a successful swap. Server
dependency lookup resolves the current application from the owner. Existing
directly injected applications remain supported for package-local tests and
embedding.

The owner factory must recompute dotenv values on every candidate construction;
reusing startup's `config_env` would miss Stage 1 environment edits. Stable
event/snapshot services and persisted session roots are supplied to each
replacement. The desktop plugin reads a configured dotenv path and
provider-to-environment-key allowlist, updates only the selected key, and
requests reload. If the subsequent candidate fails, the plugin-owned edit is
restored before admission reopens.

Port the reviewed frontend changes selectively in the base branch's existing
format. Preserve generic compound action identity, normalize
`application_action` declarations in the connection registry, present them
once in the Sessions header, execute them through the existing generic backend
route, mask secret/password fields, return immediately after reload acceptance,
and refresh action/schema state when the reload-completed notification arrives.

Verification crosses the public boundaries involved: coordinator/application
unit tests; real HTTP action execution and admission behavior; a subprocess CLI
integration with server and console ownership; frontend SDK and component
tests; and a production `RestAgentBackend` plus Sessions-screen integration.
The full default core/application/frontend suites are rerun in proportion to
the touched boundaries.

### Manual checkpoint follow-up approach

#### 1. Formalize the application notification contract

Document and test the existing owner-scoped contract instead of treating the
current TypeScript interfaces as its specification. The proposed contract is:

- Events are `application_notification_created` and
  `application_notification_updated`.
- Events are application-global and omit `session_id`; clients poll the
  existing `/events` endpoint with a global cursor and no session filter.
- Each event carries one `notification` with stable `id` and `key`,
  `kind: "notification"`, `status: "pending" | "resolved"`,
  `severity: "info" | "success" | "warning" | "error"`, title/body,
  created/updated timestamps, source provenance,
  `model_visibility: "hidden"`, and an `ActionDisplayPayload`.
- Created and updated events upsert by notification `id`; an update replaces
  the presentation for the same lifecycle item rather than stacking another
  reload notice.
- `display.presentation: "banner"` means connection-global state rendered in
  the active screen's banner slot on mobile and the common top rail on desktop.
  `display.variant`, falling back to `severity`, selects
  info/success/warning/error colors. Other action-display presentations keep
  their documented producer/host behavior.
- Notification delivery is best-effort and cannot make reload fail.
- Stage 1 state remains process-memory/event-store scoped. It survives
  `AgentApplication` replacement because the owner and event store survive, but
  it is not durable across owner-process restart. A newly connected client
  starts from the current global event cursor and is not guaranteed historical
  banners.

Add an SDK `ApplicationNotificationsController` (or equivalently small
subscribable) that owns explicit global polling, cursor lifecycle, merge/
de-duplication, local dismissal, connection identity, and application-action
registry invalidation after reload completion/failure. This removes polling
and invalidation responsibilities from `SessionsScreen` and gives mobile and
desktop one production adapter.

Document the contract in the HTTP event API reference, application runtime
documentation, SDK exports, and plugin/action-display guidance. Cross-reference
the broader generic session-notification task and explicitly distinguish
application-global, non-durable notifications from persistent session
notifications.

#### 1a. Complete the non-blocking session-notification substrate

Implement the approved Stage 1 design in
`tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`
through `040-stage-1-dummy-plugin-integration-tests.md`:

- add application-layer create/update/update-by-key/resolve/list helpers;
- persist session notifications under
  `Session.metadata["notifications"]["items"]`;
- serialize mutation with the existing session lock;
- publish created/updated/resolved session events and checkpoints;
- cap retained items while preserving every pending item;
- expose the safe tool `notification_sink` whose failures never abort a
  request;
- add SDK types, selectors, event merge, local dismiss, and reconnect loading
  from session metadata;
- render and execute follow-up actions through the existing generic action
  runner;
- prove persistence and real-backend behavior with action-triggered demo
  notifications and the task's tool fixture.

Extend the session severity type to include `success` so it shares the complete
semantic variant set with application notifications and action displays.
Session notifications keep their persistent session metadata and session event
cursor; they do not move into the owner-memory application store.

During completion, update the generic session-notifications task and its
010–040 subtasks with requirement evidence. Mark a subtask `COMPLETED VIA
tasks/20260729-staged-application-config-and-full-reload.md` only when all of
that subtask's requirements pass; leave Stage 2 interaction subtasks unchanged.

#### 1b. Standardize display routing for every producer

Replace per-screen `presentActionDisplay` branches and the current
surface-specific suppression/coercion policy with one SDK display envelope and
presentation router. The envelope carries stable display id, source kind
(`application_notification`, `session_notification`, or `action_response`),
connection id, optional session id, action context, and
`ActionDisplayPayload`.

The routing matrix is:

| Presentation | Application notification | Session notification | Action response |
| --- | --- | --- | --- |
| `banner` | Connection-global top banner rail | Same top banner rail, tagged with its session | Same top banner rail |
| `inline` | Rejected | Active session notification region; persisted until opened | Inline region of the initiating Sessions or Messages surface |
| `modal` | Mobile global modal; desktop inline fallback | Mobile modal; desktop inline fallback when its session is presented | Mobile modal; desktop inline fallback |

Explicit presentation wins when supported by that producer and host. Existing
defaults remain compatible: action responses without presentation default to
`modal`; session notifications without presentation default to `inline`;
application notifications should declare their presentation, with reload
using `banner`. Application-notification `inline` and unknown presentation
values are rejected by normalization and surfaced through diagnostics rather
than silently dropped. Desktop notification `modal` is deliberately normalized
to `inline` because React Native modal presentation is unsupported there.

All supported presentations reuse one shared `ActionDisplayCard` body and
generic follow-up action execution. Hosts vary only placement and platform
shell. Application, session, session-list, and message action surfaces all
submit returned displays to this router; a surface may normalize a requested
presentation only through the documented platform policy.

#### 2. Add a shared global banner presentation

Move the tested desktop `NotificationBanner` visual into
`@crystal-lattice/frontend-rn-components` and retain its current visual
contract: colored accent bar, muted variant background, title/body, and dismiss
control. Use shared notification/success/warning/danger theme tokens so mobile
and desktop render the same four semantic variants without copying styles.
Refactor desktop `SnapshotReadonlyBanner` to compose the shared info banner
while preserving its selected-snapshot text, return-to-live action, disabled
state, and Messages-pane placement.

Add a shared `ApplicationNotificationBannerHost` that accepts
connection-tagged notification state and renders a bounded top stack. It
upserts lifecycle updates, supports local dismissal without backend mutation,
and uses safe-area/top inset on mobile. Mobile uses a normal-flow rail that
pushes active content down; desktop keeps its existing top-rail placement. The
host does not own network polling.

Mount one host at mobile `ConnectedRoot`, above all Connection/Sessions/
Messages tabs. Mount one at desktop `DesktopRoot`, above pane/tab content.
Every banner envelope, regardless of whether it originated from an
application notification, session notification, or action response, enters
this same host. Desktop notification state is maintained per backend
connection; banners include the connection name when multiple connections can
contribute and session-scoped entries include session identity where useful.

Change owner reload notifications to `display.presentation: "banner"` and give
the display the stable notification id. Route generic application-action
results with banner presentation through the same global host so the accepted
action response and lifecycle event do not produce duplicate screen-local
cards.

#### 3. Unify the mobile Sessions action bar

Replace the separate `ApplicationActionsMenu` plus settings/reload/new buttons
with one `ActionsMenuBar` composition. Its built-in definitions are:

- `serverSettings` — opens the existing `ServerSettingsModal`;
- `refreshSessions` — performs the existing session-list refresh;
- `newSession` — opens the existing agent picker/create flow.

Plugin `application_action` declarations become extra definitions using
compound `(plugin, element id)` keys. Selection either runs an action without a
dialog or opens the existing mobile application-action dialog. Execution keeps
`actionsByKey` input resolution, loading/disabled state, and post-reload action
registry refresh.

Persist pins by connection using a new Sessions-header storage key. Seed the
three current controls as defaults so the existing visible affordances are not
lost. Missing or removed plugin actions are ignored without deleting unrelated
pin choices.

#### 4. Implement the equivalent desktop Sessions action bar

Use the same shared definitions and compound plugin identities in desktop
`SessionsPanel`. Render `ActionsMenuBar` with `variant="dropdown"` so macOS
continues through the existing native `NSPopover` bridge. Remove the one-off
PanelHeader refresh control and standalone New button after their behavior is
represented in the action bar.

Desktop built-ins follow existing Messages-pane conventions:

- `refreshSessions` calls the existing Sessions controller.
- `newSession` opens the existing `AgentPickerWindow`.
- `serverSettings` opens a `ServerSettingsWindow` through
  `DesktopWindowManager.openReactWindow`; no new native window API is needed.
- Plugin application-action forms use `useMacOSApplicationActionDialog`,
  preserving the configured desktop popover/window presentation and secret
  field behavior.

Extract the reusable server-settings form body from mobile
`ServerSettingsModal` into the shared RN package. Mobile keeps its modal frame;
desktop adds a coordinator and `ServerSettingsWindow` wrapper, registers that
React component in the desktop entry point, clears coordinator state on native
window close, and uses the focused connection's production backend.

Persist desktop pins per connection through the existing async-storage
adapter. Keep mobile and desktop persistence implementations separate unless
backend-synchronized pins are explicitly requested.

#### 5. Add pure notification/display demonstration plugins

Add three non-default first-party demo plugins with no configuration-writing or
reload responsibilities:

- `dummy-application-notification-app` — actions create, update, and resolve
  owner-scoped application notifications.
- `dummy-session-notification-app` — session actions create, update, and
  resolve persistent session notifications and provide a generic follow-up
  action.
- `dummy-action-display-app` — actions directly return
  `ActionDisplayPayload`.

Each plugin exposes explicit action inputs or separate deterministic actions
for `banner`, `inline`, and `modal`, plus info/success/warning/error variants.
Payloads use stable display/notification ids so tests can verify replacement
instead of duplication. They may include simple `run_action`, `copy_text`, and
`dismiss` follow-ups to prove that presentation does not alter action
execution.

Keep these plugins out of the production default config. Enable them only in
example and integration-test configs, document their demonstration purpose,
and use generic names/content unrelated to reload, MCP, authentication, or
provider credentials.

#### 6. Verification

SDK tests cover global no-session polling, cursor bootstrapping/retry,
created-to-updated upsert, local dismissal, malformed events, connection
isolation, action invalidation timing, session metadata reload, session
notification lifecycle, standard presentation normalization/routing, and
notification-delivery failure containment.

Shared RN tests cover all four banner variants, title/body, accessibility,
dismissal, bounded stacking, lifecycle replacement, and pointer-event
behavior. Existing desktop snapshot-readonly tests are updated to prove that
snapshot selection uses the shared banner without becoming application-global.
Shared display-host tests run the same payload through banner, inline, and
modal routes for all three source kinds.

Mobile component tests prove the banner remains visible while switching among
Connection, Sessions, and Messages; the unified action bar contains all
built-ins and plugin actions; pin choices persist; and settings/new/refresh
retain current behavior. Update the real-backend Sessions integration to
execute reload through the unified bar and observe the global banner at
`ConnectedRoot`.

Desktop component tests prove the same action inventory and pin behavior,
native-popover coordinator data, per-connection notification isolation,
connection-labelled banners, server-settings window coordination, existing
agent-picker usage, desktop application-action dialog routing, and one common
banner location for application/session/action-response envelopes. Add a
real-backend desktop component integration for discovery, reload execution,
session notification persistence, each direct action-response presentation,
global notification update, and action refresh. Add or extend a production UI
harness/XCUITest to verify the Sessions action popover, common banner rail,
Settings window, and inline fallback for desktop modal display responses.

Rerun core/application suites because the owner notification payload changes;
all shared frontend package suites; mobile typecheck/unit/real-backend tests;
desktop TypeScript/Jest tests; focused macOS UI coverage; docs build; and
changed-file static checks. Stop again for manual verification on both mobile
and desktop before Stage 1 is completed.

#### 7. Approved manual-checkpoint notification remediation

Make notification lifecycle presentation revision-aware. The backend continues
to upsert a pending notification by stable lifecycle id/key, while clients
record local dismissal against `id + updated_at` so a later revision is
eligible for presentation. Resolved application notifications are removed
from display state and are never emitted as a fresh display.

Use controller-owned application notification state for lifecycle items and
keep the transient display bus only for immediate action responses. Keep the
display subscription stable while dismissal state changes. After a
session-scoped action mutates the current session, refresh both the parent
session-list cache and the active session-context controller so persistent
notification metadata is visible immediately even if event polling is delayed.

Enforce application-notification presentation support at both the application
contract and frontend normalization boundary. Remove `inline` from the dummy
application-notification action form. Session notifications and direct action
responses retain inline support.

On mobile, retain connection-global banner state at ConnectedRoot but render it
through reusable screen-owned slots in normal flow below each screen header;
the Sessions slot follows the search/filter row. Use opaque semantic
backgrounds. Render global application notification modals as a root-level
in-tree overlay so they remain pending while an action-form native modal
dismisses. On desktop, normalize
application and session notification modal requests to inline; do not attempt
React Native modal presentation.

Replace the simplified native banner harness with production-screen Detox
coverage around ConnectedRoot, SessionsScreen, and SessionChatScreen.
Automated geometry assertions prove that the banner bottom does not overlap
the Sessions or Messages content top. Capture named screenshots for Sessions
application banner/modal and Messages session banner/inline/modal states for
the manual visual checkpoint.

### Implementation decisions and open questions

Decided for this draft:

- Normal Stage 1 reload reconstructs `AgentApplication`; it does not restart the
  CLI process.
- The old application stays active but quiescent until the candidate is valid.
- Candidate failure preserves the old application and reopens admission.
- Plugin process-global conflicts may return a manual-process-restart-required
  result; automatic process restart is not part of Stage 1.
- One owner/application serves combined server and console mode.
- The restart/reload control contract carries no storage-specific values or raw
  secrets.
- The dotenv allowlist should map provider ids to environment keys so the UI
  does not accept arbitrary variable names.
- The reload action returns immediately after acceptance; requested/completed/
  failed state is communicated through application-global notifications.
- All application-dependent operations and background model/tool workers count
  toward drain readiness.
- An `os.environ` value makes the corresponding dotenv key externally managed
  and uneditable by the sample plugin.
- Reload completion is not published until the old application's runtime store
  and MCP registry have closed their managed resources.

Approved Stage 1 decisions:

- Keep notification state in the stable owner/event store with live global
  polling/replay only; durable reconnect semantics remain outside Stage 1.
- Do not add an automatic drain timeout or forced tool cancellation.
- Construct the candidate alongside the quiescent old application and report
  manual process restart required for exclusive process-global conflicts.
- Reject newly admitted application operations with HTTP 503 and stable
  `application_reload_pending` details, with an equivalent terminal error.

Approved checkpoint-follow-up decisions:

- Use the existing `banner` presentation value for connection-global banner
  state rendered in platform-appropriate screen/rail placement
  rather than adding another action-display enum value.
- Promote the desktop banner visual to the shared RN package.
- Keep polling/state in an SDK controller and rendering in a shared host.
- Use one shared `ActionsMenuBar` composition on each Sessions surface; do not
  create a second menu implementation.
- Use distinct labels `Refresh sessions` and `Reload application`.
- Reuse desktop `openReactWindow` and the existing action-dialog/agent-picker
  coordinators; do not add a dedicated native server-settings API.
- Pending banners remain until locally dismissed, with at most three visible
  banners per connection. Resolved notifications leave notification state
  without being redisplayed; reload completion/failure remains a distinct
  transient outcome display.
- Server settings, Refresh sessions, and New session are default-pinned;
  plugin application actions start in overflow and can be pinned.
- Pin state remains platform-local and connection-scoped rather than backend
  synchronized.
- Desktop polls each open backend connection and labels banners with the
  connection name when more than one connection is open.
- Presentation support is producer- and host-specific: application
  notifications reject inline; desktop notification modal requests fall back
  to inline; other valid explicit presentations follow the common display
  envelope/controller.
- Desktop sends every banner source to one banner rail and uses inline
  notification presentation when a notification requests modal.
- Automated implementation and verification stop before macOS
  simulator/XCUITest execution, which requires a separate user approval.
- Add mobile Detox coverage only when a required native behavior cannot be
  verified reliably through shared-component, application-component, or
  production-backend integration tests.

### Documentation

- Document the owner-level reload lifecycle and plugin action result/effect.
- Document the deliberately minimal application-global notification slice, its
  relationship to the generic session-notification task, and its live
  persistence/reconnect limits.
- Specify the application-notification event and payload contract, global
  polling rules, lifecycle/upsert semantics, banner presentation, connection
  scope, and non-durable reconnect behavior in the public event API.
- Document persistent session-notification storage/events/reconnect behavior
  and the common presentation matrix shared with application notifications and
  action responses.
- Document the pure demonstration plugins and keep their enablement confined
  to example/test configurations.
- Document the unified Sessions action-bar behavior, pin persistence, mobile
  modal conventions, and desktop popover/window conventions.
- Document the Stage 1 dotenv path and provider-to-key allowlist configuration,
  process-environment precedence, and intentionally deferred security limits.
- Document application-action declaration, discovery, compound identity,
  Sessions-header presentation, and secret field behavior.
- Document the lifecycle contract for plugins that can be reconstructed
  in-process and the manual CLI restart fallback for process-global conflicts.
- Cross-reference the iOS App Review runtime as a consumer of the
  storage-independent owner/reload contract.

### Task checklist

- [x] Resolve the four remaining Stage 1 open questions and update this plan.
- [x] Mark the Stage 1 plan `Approved`.
- [x] Add the storage-independent owner/reload control contract and coordinator.
- [x] Integrate operation admission and background-worker accounting with HTTP.
- [x] Add application-global reload notification events, owner state, SDK
  polling/merge support, and a connection-global/Sessions notification host.
- [x] Integrate the owner with console-only, server-only, and combined startup.
- [x] Make terminal application replacement explicit and clear stale caches.
- [x] Verify old-application close waits for MCP registry/server/session
  resources and does not leak subprocesses or transports.
- [x] Recompute dotenv/config inputs for every candidate construction.
- [x] Add the sample application-config plugin with configured dotenv path,
  provider/key allowlist, rollback, and reload request.
- [x] Port the generic application-action SDK, React, shared RN, and Sessions
  surface changes without unrelated formatting churn.
- [x] Port masked/no-prefill secret input behavior.
- [x] Add focused coordinator, plugin, server, terminal, SDK, React, RN, and
  mobile tests.
- [x] Add realistic public HTTP and subprocess combined-mode reload integration
  coverage.
- [x] Update Stage 1 documentation.
- [x] Run the Stage 1 automated verification and record evidence.
- [ ] Stop for the required manual checkpoint and obtain approval before
  planning any next stage.
- [x] Approve the expanded manual-checkpoint follow-up execution plan.
- [x] Add and document the application notification controller/contract.
- [x] Complete generic non-blocking session-notification subtasks 010–040 and
  record their evidence/relations in the owning task directory.
- [x] Add the producer-independent display envelope/router for banner, inline,
  and modal presentations.
- [x] Promote the four-variant notification banner and add the global shared
  host.
- [x] Move mobile notification ownership to `ConnectedRoot`.
- [x] Replace mobile Sessions header controls with one pinnable action bar.
- [x] Add desktop global notification polling/host with connection isolation.
- [x] Replace desktop Sessions controls with the equivalent native-popover
  pinnable action bar.
- [x] Extract the reusable server-settings model and add the desktop settings
  coordinator/window.
- [x] Add non-default application-notification, session-notification, and
  direct-action-display demonstration plugins.
- [x] Add SDK/shared RN/mobile/desktop unit and component coverage.
- [x] Add real-backend desktop coverage.
- [x] Run focused macOS UI verification after explicit user approval.
- [x] Update notification/action-bar documentation.
- [x] Run follow-up verification and record evidence.
- [x] Approve the manual-checkpoint notification remediation plan.
- [x] Make application and session notification delivery revision-aware and
  refresh the active session context after notification mutations.
- [x] Enforce the application-notification presentation policy and desktop
  notification modal-to-inline fallback.
- [x] Convert the mobile banner to opaque normal-flow screen slots below each
  header (below search/filter on Sessions) and add the reliable root-level
  application-notification modal overlay.
- [x] Add production-screen Detox geometry assertions and screenshots for
  notification presentation on Sessions and Messages.
- [x] Run focused remediation verification and record evidence.
- [ ] Stop for the revised mobile and desktop manual checkpoint.

### Requirement verification

- **Sample plugin and generic UI:** Discover both sample actions through the
  public backend, render them in the production Sessions header, submit masked
  credential input, and execute without feature-specific frontend code.
- **Reload request/readiness and admission:** Start a slow real request, invoke
  reload, prove the action returns accepted and a global requested notification
  appears, prove new application operations receive the stable pending
  response, let the original request finish, and prove replacement plus a
  completion notification occurs only afterward.
- **Complete replacement/config/plugin changes:** Through the public CLI/HTTP
  flow, activate a general config change and plugin addition/removal, then prove
  subsequent application discovery and requests use the replacement.
- **Shared ownership:** In combined mode, prove startup/lifecycle hooks execute
  once per application, server and console switch to the same replacement, and
  persisted sessions remain accessible.
- **Failure preservation:** Attempt an invalid candidate and an exclusive
  conflict fixture; prove the old application remains usable, admission
  reopens, plugin-owned dotenv changes roll back, and a failed notification is
  displayed.
- **MCP cleanup:** Start a fixture MCP runtime with observable managed
  resources, replace the application, and prove old registry managers,
  sessions/transports, and child processes are closed before completion is
  published.
- **Storage-independent contract/iOS support:** Exercise the coordinator with a
  non-dotenv factory/input fixture to prove reload control does not depend on
  desktop files or raw secrets.
- **Integration coverage:** Collect and pass real HTTP and subprocess tests for
  both a general configuration change and a plugin-catalog change.
- **Manual checkpoint:** The user confirms drain/reject behavior, successful
  replacement, session continuity, plugin catalog changes, dotenv key update,
  and failure recovery in the real local runtime.
- **Application notification contract:** Poll globally through the production
  backend, observe one created-to-updated lifecycle without `session_id`, and
  verify the same stable notification renders as a four-variant-capable
  connection-global banner in each mobile screen slot and the desktop rail.
- **Persistent session notifications:** Trigger a notification through a
  public session action, observe session lifecycle events, reconnect/reload the
  session from metadata, execute its follow-up action, and resolve it without
  exposing it to model history.
- **Standard presentations:** Prove application notifications accept banner
  and mobile modal but reject inline; session notifications and action
  responses retain their supported explicit presentations; desktop routes
  notification modal requests to inline and all banner payloads to one rail.
- **Notification revision reliability:** Dismiss a pending notification,
  update the same lifecycle id/key, and prove the new revision appears without
  reopening the session; resolve it and prove it disappears without redisplay.
- **Mobile notification layout:** Through production-screen Detox scenarios,
  prove the banner rail appears below the Sessions search/filter row and below
  the Messages header while pushing subsequent content down, application modal
  presentation survives action-dialog dismissal, and named screenshots record
  the rendered banner/inline/modal states.
- **Demonstration plugins:** Discover and execute each non-default demo plugin
  through the public backend while proving none is enabled by production
  default configuration.
- **Unified Sessions actions:** On mobile and desktop, discover plugin
  application actions through the real backend alongside Server settings,
  Refresh sessions, and New session; pin/unpin them; and verify each routes
  through the platform-appropriate modal, popover, or window.
- **Desktop conventions:** Through production desktop components and native UI
  verification, prove the action list uses the macOS popover and Server
  settings opens a separate React window while application forms use the
  existing desktop action-dialog path.

The final credential-security requirement remains incomplete after Stage 1 and
is accepted only as deferred Stage 3 scope. General JSON configuration writing,
request refactoring, and live active-request migration remain conditional.

### Additional implementation verification

- Candidate construction cleans up partial resources on every failure path.
- Reload notification failure does not prevent drain, replacement, rollback, or
  admission reopening.
- Repeated reloads do not duplicate application plugin startup hooks, event
  stores, background services, or terminal/server close ownership.
- Direct test injection and existing server route tests remain compatible.
- Existing session single-flight and cancellation behavior remains intact.
- Frontend action state remains isolated per backend connection and action
  definitions remain keyed by `(plugin, action)`.
- Secret/password fields clear on close/submit and never prefill from action
  defaults or context.
- Core, application, frontend SDK, React, RN component, mobile TypeScript,
  targeted mobile integration, formatting, and docs checks pass.

## Implementation Notes

- **Manual notification/display smoke guidance (July 30, 2026):** The personal
  `~/.crystal/config.json` enables the three non-default local demonstration
  packages from this checkout:
  `dummy-application-notification-app`,
  `dummy-session-notification-app`, and `dummy-action-display-app`. Request a
  configuration reload or restart the local runtime before testing. On either
  mobile or desktop, open **Sessions** and use the unified Sessions actions
  menu to run **Demo application notification** and **Demo action display**.
  Application notifications now offer `banner` and `modal` only; verify the
  mobile banner appears below the Sessions search/filter row and pushes session
  rows down, while mobile modal opens over the whole application. Direct action
  displays still exercise `banner`, `inline`, and `modal`. Open a session, run
  **Demo session notification**, verify the banner appears below the Messages
  header, inline content is in the transcript region, and modal opens globally;
  then dismiss one revision, emit an updated revision without reopening, run
  **Run follow-up**, and resolve it. On desktop, notification modal requests
  should render inline rather than opening a React Native modal/window. With
  two connections open, verify one connection's notification/action display
  does not appear in the other connection's rail or session surface. These
  packages are demonstration-only and must remain absent from production
  default configuration.
- **Notification remediation evidence (July 30, 2026):** Application
  notification creation rejects inline at the owner boundary and frontend
  normalization rejects it defensively. Mobile and desktop dismissal are keyed
  by notification revision, resolved application notifications leave
  controller-backed display state, and session action mutations refresh the
  active session context. Desktop normalizes modal notification/action
  envelopes to inline and no longer invokes the generic display window for
  those payloads.
- **Mobile visual evidence (July 30, 2026):** The production-screen iOS Detox
  suite passed five scenarios. Native frame assertions proved Sessions
  search/filter row → application banner → first session row and Messages
  header → session banner → transcript ordering. Screenshots are retained under
  `mobile/crystal-lattice-control-rn/artifacts/notification-visual/` for
  Sessions application banner/modal and Messages session banner/inline/modal.
- **Focused remediation verification (July 30, 2026):** frontend SDK
  `269 passed`; shared RN components `7 passed`; focused mobile notification
  unit tests `10 passed`; mobile TypeScript passed; real-backend mobile
  Sessions integration `2 passed`; real-backend desktop global display
  integration `1 passed`; focused Python owner/demo HTTP tests `6 passed`; iOS
  Detox notification visual suite `5 passed`; scoped `git diff --check`
  passed; `mkdocs build -f docs_site/mkdocs.yml` passed with the repository's
  pre-existing documentation warnings. Desktop TypeScript still reports the
  three pre-existing errors in `ChatPane.tsx` and
  `ActionResultInlineCard.tsx` recorded before this remediation.
- Stage 1 execution started after explicit plan approval.
- Added a small `AgentApplicationOwner`; `AgentApplication` remains the real
  application and only gains a reload-request delegation hook.
- Server HTTP lifetime and background send workers retain operation leases.
  Terminal sends use the same owner, and combined server/console mode now owns
  one application.
- Reload actions return accepted immediately. The owner publishes global
  requested/completed/failed notifications through the stable event store and
  the Sessions screen uses an explicit global polling mode.
- The desktop sample plugin writes only configured allowlisted dotenv keys,
  rejects process-environment overrides, and registers rollback on candidate
  failure.
- The draft generation implementation was not ported. Reused frontend/action
  code was applied selectively without its unrelated formatting churn.
- Focused evidence currently passing: owner/runtime tests, existing server and
  terminal tests, sample plugin tests, actual MCP registry close ordering,
  application reload HTTP tests, combined CLI subprocess plugin add/remove
  reload, frontend SDK/React/RN package tests, mobile TypeScript, Sessions unit
  tests, and the real-backend Sessions integration.
- Full default evidence: core `408 passed, 26 deselected, 1 xfailed`;
  application `313 passed, 90 deselected`; MCP runtime `21 passed`; frontend SDK
  `258 passed`; frontend React `20 passed`; shared RN components `7 passed`;
  mobile `89 passed`; mobile TypeScript passed.
- Public integration evidence: combined CLI shared lifecycle passed; combined
  CLI plugin add/remove reload passed with one unchanged process and preserved
  sessions; production `RestAgentBackend` plus Sessions-screen reload
  integration passed.
- Documentation build passed with only the repository's existing griffe and
  autoreference warnings. Ruff checks for changed Python surfaces and
  `git diff --check` passed.
- The real `~/.crystal/config.json` now includes the non-secret
  `application.application_config` dotenv path and editable provider/key
  allowlists. Exact-config preflight and one full owner reload succeeded without
  provider calls.
- Checkpoint follow-up implemented persistent session notifications, generic
  owner-memory application notifications, and one standard display envelope
  for application/session notifications and action responses.
- Mobile owns application-global display state at `ConnectedRoot`; desktop
  polls every open backend and routes all banner sources to one top rail.
- Mobile and desktop Sessions now use one pinnable action bar. Desktop Server
  settings use a separate React window; modal notification/action displays use
  the established inline fallback.
- Added non-default `dummy-application-notification-app`,
  `dummy-session-notification-app`, and `dummy-action-display-app` packages.
- Added a focused mobile Detox harness for native banner z-order/touch behavior.
  It has not been run because component/real-backend tests cover the
  non-native contract and simulator execution is deferred.
- Follow-up evidence: core `415 passed, 26 deselected, 1 xfailed`;
  application `315 passed, 90 deselected`; frontend SDK `266 passed`;
  frontend React `20 passed`; shared RN unit suite `7 passed`; mobile
  TypeScript and `97` unit/component tests passed; desktop `97` Jest tests
  passed; mobile real-backend Sessions/reload/session-notification integration
  passed; desktop real-backend global-banner integration passed; three
  demo-plugin unit tests and the public HTTP demo-plugin integration passed.
- Documentation build passed with existing griffe/autoreference warnings and
  expected nav warnings for non-default demo plugins.
- macOS simulator/XCUITest was approved and passed on July 30, 2026:
  `npm run test:macos-ui:session-filters` collected three tests covering
  native session-filter popovers, rich status-list selection and row refresh,
  the unified Sessions action popover, and the separate Server settings
  window. The two rich-list assertions now target accessibility elements that
  React Native macOS actually exposes (the close control and containing row
  label), rather than non-accessible layout/text containers.
- iOS simulator Detox was approved and passed on July 30, 2026:
  `npm run detox:build:ios` followed by
  `npm run detox:test:notification-banner:ios`. The native AppDelegate now
  selects the existing `MobileNotificationBannerHarness` when its Detox launch
  argument is supplied. The harness places its screen-changing controls below
  the visible top banner, so the test verifies the intended properties:
  banner persistence above a screen change and touch delivery to its own
  action, without requiring a visible banner to pass through touches.
- Desktop project-wide TypeScript verification still reports three pre-existing
  errors in `ChatPane.tsx` and `ActionResultInlineCard.tsx`; the new desktop
  integration directory is excluded consistently with the mobile integration
  directory, and no new source/harness TypeScript errors remain.
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

Supports:
`tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`

Uses a minimal non-blocking notification slice from:
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
- Stage 1 borrows only the notification envelope, lifecycle-event, SDK merge,
  and existing display-host patterns from the generic session-notification
  task. It does not implement session metadata persistence or interactive
  notifications and does not claim completion of that task.
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

### Documentation

- Document the owner-level reload lifecycle and plugin action result/effect.
- Document the deliberately minimal application-global notification slice, its
  relationship to the generic session-notification task, and its live
  persistence/reconnect limits.
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
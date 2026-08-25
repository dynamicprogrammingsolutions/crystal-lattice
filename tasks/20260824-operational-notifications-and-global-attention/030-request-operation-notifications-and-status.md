# Request Operation Notifications And Status

Represent model request lifecycle through persisted notification operation
records and portable status-display information while preserving streaming
events and frontend-local loading state.

## Requirements checklist

- [ ] Every coordinated model request has authoritative persisted lifecycle
  state associated with its owning session and request identity.
- [ ] Running, successful, failed, cancelled, and interrupted request outcomes
  are recoverable after navigation, reconnect, or server restart.
- [ ] Request status can carry portable display information for session/header
  or transcript-tail placement, user-facing text, semantic tone, and animated
  in-progress indication.
- [ ] A failed request uses the same lifecycle record as its persistent error
  rather than creating conflicting status and error records.
- [ ] Frontends use persisted request-operation state as recovery authority
  while continuing to process request events for streaming and immediate
  updates.
- [ ] Users can configure which request lifecycle transitions request global
  attention.
- [ ] Frontend-local network/loading indicators remain independent from
  persisted request operations.

Parent Task: `tasks/20260824-operational-notifications-and-global-attention/000-main.md`

Depends On:

- `tasks/20260824-operational-notifications-and-global-attention/010-persistent-request-and-action-errors.md`
- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`

## Supporting details

- `SessionRequestCoordinator` is the shared application-owned boundary for
  starting existing-session and append-and-send requests.
- `AgentApplication.send_request(...)` already emits request-started,
  streaming, error, completion, and cancellation-related events.
- Frontend chat state currently derives `activeRequestId` and request errors
  from event order plus checkpoint recovery.
- Event delivery is not authoritative after cursor expiry or server restart.
- The notification model already supports request IDs, revisions, lifecycle
  events, retention, terminal history, and hidden model visibility.
- Persisting one record per request requires compact session-list projection;
  generic summaries cannot carry every full historical notification.
- The OpenAI Responses background-compaction task also needs a portable
  operation/status-display shape. This task should define the generic
  contract rather than creating a request-only schema.

## Execution plan

Status: Draft

Define versioned generic operation metadata on notification records. Initial
fields should cover:

- operation type and identity;
- lifecycle state and optional phase;
- start and terminal timestamps;
- progress/elapsed information where applicable;
- cancellation capability where applicable.

Define a separate portable status-display object containing:

- placement such as session header or transcript tail;
- user-facing status text;
- semantic variant;
- a bounded indicator vocabulary such as spinner, pulse, dots, or none.

The frontend owns exact animation and layout. Unknown optional values degrade
without losing operation lifecycle state.

Create or update one request notification throughout the coordinated request:

- request admission/start creates a pending running record;
- request progress may update phase/revision without requiring persistent token
  streaming;
- success resolves the record as succeeded;
- cancellation resolves it as cancelled;
- terminal request failure updates the same record to a visible persistent
  error state;
- server/application recovery converts an orphaned running record to
  interrupted.

Notification lifecycle events remain the real-time operation-status transport.
Existing request events remain available for streaming and compatibility.
SDK selectors prefer the authoritative operation record when present and fall
back to request events/checkpoint fields during migration.

Expose compact active operation projections on session summaries so Sessions
can show request state without loading full notification history. Open Chat
hydrates full operation/notification state through dedicated notification
queries.

Add frontend settings for attention on request started, succeeded, failed, and
cancelled transitions. Preferences filter attention eligibility; they do not
prevent the authoritative operation record from being created.

### Implementation decisions and open questions

- **Decided:** Request operation state is a specialization of ordinary session
  notifications and remains hidden from model history.
- **Decided:** One request has one operation notification occurrence.
- **Decided:** Failure updates that record into the persistent error
  presentation defined by subtask 010.
- **Decided:** Request events are retained for streaming and compatibility;
  they are not the sole recovery authority.
- **Decided:** Request state, connection runtime state, cache freshness, and
  frontend-local loading are rendered as independent dimensions.
- **Recommendation:** Default attention preferences: started off; success on
  only when the owning session is not visible; failed on; cancelled off.
- **Open:** Store request-attention preferences device-locally initially or in
  application/user settings. The main-task recommendation is device-local.

### Documentation

- Update notification specifications with generic operation and
  status-display metadata and request lifecycle mapping.
- Update application/request execution documentation with operation
  publication and restart reconciliation.
- Update frontend SDK development documentation for selectors, event fallback,
  and compact session projections.
- Update mobile/desktop user documentation for delivered request status and
  preferences.
- Update the background-compaction task/documentation to consume the same
  generic operation/status-display contract when implementation begins.

### Task checklist

- [ ] Resolve attention preference persistence.
- [ ] Define and normalize operation/status-display metadata.
- [ ] Publish request operation lifecycle from coordinated request execution.
- [ ] Reuse the operation record for request failure persistence.
- [ ] Reconcile orphaned running operations after server/application restart.
- [ ] Add compact session-list operation projections.
- [ ] Add SDK operation selectors/controllers with request-event fallback.
- [ ] Add mobile and desktop request-status rendering and preference models.
- [ ] Add backend, restart, API, SDK, component, and integration tests.
- [ ] Update specifications, current docs, and requirement evidence.

### Requirement verification

- Lifecycle: controlled requests prove running, succeeded, failed, cancelled,
  and interrupted records with stable request identity.
- Recovery: reopening a session after missed events derives current/terminal
  status from persisted state.
- Streaming compatibility: partial/final/tool events continue to render while
  operation records update independently.
- Failure reuse: one failed request produces one operation/error record rather
  than duplicate records.
- Portable display: shared selectors expose placement, text, variant, and
  indicator consistently to mobile and desktop.
- Preferences: each transition can be enabled or suppressed for attention
  without changing stored operation history.

### Additional implementation verification

- A stale cached running projection is marked non-authoritative while its
  connection is offline.
- Restart reconciliation cannot mark a currently active coordinated request
  interrupted.
- High-frequency stream events do not cause high-frequency persistent
  notification writes.
- Historical operation growth respects terminal history limits.

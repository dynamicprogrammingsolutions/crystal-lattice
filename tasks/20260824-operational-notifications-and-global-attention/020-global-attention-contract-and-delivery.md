# Global Attention Contract And Delivery

Allow selected authoritative notifications to request temporary
frontend-global attention without changing their owning scope, lifecycle, or
dismissal state.

## Requirements checklist

- [ ] Notification producers can mark an important notification transition as
  eligible for frontend-global attention.
- [ ] Attention eligibility preserves the notification's real connection and
  optional session ownership.
- [ ] Frontends can receive and authoritatively rehydrate eligible application
  and session notification transitions across an open connection.
- [ ] Closing, timing out, or swiping away an attention presentation is a
  frontend-local acknowledgement and does not dismiss the notification.
- [ ] An attention presentation can offer an explicit View destination for the
  owning connection/session without navigating automatically.
- [ ] Old or already acknowledged attention transitions do not reappear after
  reconnect or host reconstruction.

Parent Task: `tasks/20260824-operational-notifications-and-global-attention/000-main.md`

Depends On:

- `tasks/20260824-operational-notifications-and-global-attention/010-persistent-request-and-action-errors.md`

## Supporting details

- Existing `display.presentation` describes placement in the notification's
  owning surface. It should not be overloaded to describe temporary
  application-global attention.
- Notification revisions may change frequently for progress. A separate
  transition token is needed so one heartbeat does not repeatedly create a
  global banner.
- Session notification events are visible through an application-scope event
  query, but events are best effort and cannot be the reconnect authority.
- Loading every session and its complete notification list is not a scalable
  cross-session hydration strategy.
- Frontend connection IDs are local identities attached by the backend/runtime
  through which a record was received. They are not server notification
  fields.
- Notification history and session caches should not require complete
  notification arrays in every generic session summary.

## Execution plan

Status: Draft

Extend the notification record with optional versioned attention metadata
separate from the ordinary display payload. The contract should include:

- one stable token per alert-worthy transition;
- an occurrence time and fresh-presentation expiry;
- priority/tone hints where needed;
- whether a standard View destination is available;
- optional producer context that remains safe and connection/session scoped.

The producer updates the attention token only when a new transition deserves
attention. Progress heartbeats that keep the same token update the owning
notification without creating another attention presentation.

Add an authoritative aggregate query per application connection that returns
eligible application notifications and session notifications with their
session IDs. Use the existing notification stores rather than creating an
attention store. Events accelerate delivery; the aggregate query handles
initial hydration, reconnect, and cursor expiry.

Add a frontend SDK attention controller that merges snapshot and event state,
filters expired transitions, and persists locally acknowledged tokens keyed by
connection, notification identity, and attention token. Acknowledgement never
calls a notification mutation endpoint.

Provide a host-neutral View destination descriptor. Frontends translate it
into their connection/session navigation model. The backend does not control
native routes or focus directly.

Keep full notification histories out of generic session-list payloads. Add
only compact notification/operation projections required by Sessions rows;
full active/terminal records remain available through dedicated notification
and future history queries.

### Implementation decisions and open questions

- **Decided:** Attention is optional metadata on an authoritative
  notification, not another notification scope or store.
- **Decided:** Attention acknowledgement is device-local presentation state
  and does not increment notification revision.
- **Decided:** The acknowledgement key includes the frontend connection ID,
  notification ID, and attention token.
- **Decided:** Events remain best-effort delivery; an aggregate query is the
  authoritative hydration path.
- **Decided:** View is explicit user intent. Receiving attention never focuses
  a connection or session.
- **Recommendation:** Frontends suppress ordinary success/start attention
  while already viewing the owning session, while high-priority failure
  policy remains configurable.

### Documentation

- Update notification product, technical, and frontend contracts with
  attention eligibility, tokens, expiry, acknowledgement, navigation, and
  aggregate hydration.
- Update frontend SDK development documentation for the attention controller
  and local acknowledgement store.
- Update plugin notification guidance with a complete important-transition
  example and a warning that producers do not own frontend navigation.
- Document compact session-summary projections separately from full
  notification history.

### Task checklist

- [ ] Define and normalize the versioned attention metadata.
- [ ] Add aggregate application/session attention query and HTTP/SDK surface.
- [ ] Add lifecycle events or event mapping needed for eligible transitions.
- [ ] Implement SDK snapshot/event merge and local acknowledgement storage.
- [ ] Exclude complete notification history from generic session summaries and
  add compact projections.
- [ ] Add backend/store/API/SDK tests for expiry, deduplication, reconnect,
  cursor expiry, and acknowledgement.
- [ ] Update notification specifications, plugin docs, SDK docs, and
  requirement evidence.

### Requirement verification

- Eligibility: creating/updating a notification with a new attention token
  yields one eligible transition without changing ownership.
- Revisions: repeated revisions with the same token do not create repeated
  attention; a later new token is eligible.
- Authority: aggregate hydration returns current eligible application/session
  records with session identity after missed events.
- Acknowledgement: local close/timeout/swipe suppresses that token without
  changing server notification status or revision.
- Expiry: stale attention is not newly presented after reconnect.
- Payload boundary: session-list responses remain compact as notification
  history grows.

### Additional implementation verification

- The same server notification ID on two frontend connections cannot share an
  acknowledgement.
- A terminal or missing notification removes obsolete local attention state.
- Malformed or unknown attention versions are ignored without hiding the
  authoritative notification in its owning surface.

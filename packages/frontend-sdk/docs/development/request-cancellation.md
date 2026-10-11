# Request cancellation

`AgentBackend` exposes two request-ID operations:

- `cancelRequest(requestId)` posts to `/requests/{requestId}/cancel` and
  requests hard cancellation;
- `softCancelRequest(requestId)` posts to
  `/requests/{requestId}/soft-cancel` and lets an active tool finish before the
  request stops.

`ChatController.cancelActiveRequest()` and
`ChatController.softCancelActiveRequest()` select the current
`activeRequestId`. Neither method clears that ID after HTTP acknowledgement.
The request remains active until the event stream delivers
`request_cancelled` or `request_completed`.

This permits escalation: after soft cancellation is acknowledged, a frontend
must keep hard cancellation available for the same active request. On mobile,
soft and hard cancellation have the same enabled state so either action
remains available while the request is active. A frontend may guard only the
brief submission itself, but must not disable soft cancellation for the rest
of an active request after acknowledgement.

The additive `request_cancelled.cancellation_mode` value is `soft` or `hard`.
Existing lifecycle reduction remains based on the event type, so older event
consumers can ignore the field.

The public `error` event represents a fatal request error. Frontend streaming
state therefore clears a matching active request when it receives `error`;
the normal later `request_completed` event is idempotent. An error for an older
request does not clear a newer active request.

## Reconciliation and acknowledgement ordering

`ChatController.recoverAfterResume()` reloads the selected history window and,
when supported, queries `getSessionRequestStatuses` for current active work.
The message-list request ID can describe an older checkpoint; the optional
status query observes the current active-request registry. Unavailable or
unsupported status reads do not establish completion.

Cursor recovery uses the same reconciliation before restarting from the latest
event. Send acknowledgement also checks current work, and completed request
IDs prevent a late acknowledgement from restoring a request that already
finished, including when a later message reload still carries that request's
checkpoint ID. Request revisions prevent an older status response from clearing
newer work. This observes current state; it does not create durable operation
history or prove whether an unacknowledged send was accepted.
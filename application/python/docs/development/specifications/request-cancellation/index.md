# Request cancellation specification

Status: Implemented

This specification defines request cancellation owned by `AgentApplication`
and consumed by providers, tools, HTTP clients, the terminal, and graphical
frontends.

## Public operations

Hard cancellation is the existing operation:

```text
AgentApplication.cancel_request(request_id)
POST /requests/{request_id}/cancel
```

It requests immediate interruption of cooperative provider work and active
foreground tools. Foreground subprocess tools terminate their isolated process
group so descendants do not survive the request.

Soft cancellation is:

```text
AgentApplication.soft_cancel_request(request_id)
POST /requests/{request_id}/soft-cancel
```

It interrupts an active provider, but an already-running foreground tool is
allowed to finish. The tool result is appended and checkpointed before the
request stops. No subsequent queued tool or provider phase starts.

Both operations are request-ID scoped and may arrive before live request
registration. Hard cancellation is stronger: a later hard request promotes a
soft cancellation and interrupts the active tool; soft cancellation never
downgrades hard cancellation.

## Internal signals

One request controller exposes three related states:

- overall stop is set by soft or hard cancellation and controls tool-loop
  checkpoints;
- provider interruption is set by soft or hard cancellation and is passed to
  provider execution;
- tool interruption is set only by hard cancellation and is passed to tool
  execution.

Tool plugins receive the hard-only signal. They do not interpret request-level
soft-cancel policy.

## Events and persistence

Cancellation terminates with the existing `request_cancelled` event. The event
includes `cancellation_mode`, whose value is `soft` or `hard`, and remains
followed by normal request completion cleanup.

A soft-cancelled tool's completed result is durable conversation history. A
hard-cancelled tool may return a cancellation result when its tool contract
supports one. Partial assistant output remains provisional under the existing
request execution rules.

Cancellation mode itself is transient request state, not durable operation
history.

## Background command boundary

Once an explicit background command has been handed off successfully, request
cancellation does not terminate it. Managed background commands remain owned
by their process-specific stop action, such as Claude `TaskStop`. This boundary
applies to both soft and hard request cancellation.

## Compatibility

- The existing `cancel_request`, `cancelRequest`, `/cancel`, and HTTP cancel
  route retain hard-cancel semantics.
- Existing event consumers may ignore the additive `cancellation_mode` field.
- `/soft-cancel` is additive and uses its own idempotency scope.
- Application shutdown and request timeout paths continue to use hard
  cancellation.

See [requirements](requirements.md) for implementation and verification state.
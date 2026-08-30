# Session request status

Backends may implement the optional
`AgentBackend.getSessionRequestStatuses(sessionIds)` operation. The operation
queries only the supplied session IDs and returns one normalized lightweight
projection per available session.

```ts
const snapshot = await backend.getSessionRequestStatuses?.([
  "session-one",
  "session-two",
]);
```

The initial states are:

- `idle`
- `not_started`
- `running`
- `succeeded`
- `interrupted`

`authority` communicates whether the source is a derived transient snapshot or
a persisted operation source. Consumers must not treat
`derived_transient` as durable request history.

Saved-connection hosts can implement `ConnectionSessionStatusReader` to query
status without opening a runtime. The result distinguishes supported data,
unsupported transports, unavailable servers, authorization failure, and
repair-required credentials.
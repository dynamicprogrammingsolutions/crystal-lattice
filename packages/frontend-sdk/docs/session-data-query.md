# Session and message data queries

`RestAgentBackend` exposes projected query methods separately from its complete
session and message methods:

```typescript
const sessions = await backend.querySessions({
  filters: {
    modified_after: "2026-09-01T00:00:00Z",
  },
  include: ["$.sessions[*].session_id"],
});

const messages = await backend.queryMessages(sessionId, {
  start: -50,
  include: [
    "$.messages[*].index",
    "$.messages[*].message.role",
    "$.messages[*].message.content",
    "$.messages[*].message.metadata.reasoning",
  ],
  exclude: ['$.messages[?(@.message.role == "tool")]'],
});
```

Selectors are encoded as repeated HTTP query parameters in their supplied
order. Filter values use the active plugin contract; arrays use CSV encoding
and `null` uses the inactive `any` spelling.

Projected calls return `SessionDataQueryResult` or `MessageDataQueryResult`.
Canonical fields are optional because strict inclusion may omit them. The SDK
does not cast projected messages to complete `IndexedMessage` values.

`listSessions()` and `listMessages()` retain their complete current types and
normalization. Projected query methods do not update the chat controller or
the persisted complete-message cache. A frontend may use projected data for a
lightweight view and later call `listMessages()` to hydrate the complete
canonical range without a partial response overwriting it.

See the application
[session and message query guide](../../../application/python/docs/session-data-query.md)
for JSONPath semantics, canonical fields, HTTP parameters, limits, and shell
examples.
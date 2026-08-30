# Provider runtime contract

## Provider role

A provider integrates one request/response protocol with AgentCore. It owns:

- provider identity;
- resolved credential consumption;
- request and client construction;
- core-to-native and native-to-core conversion;
- ordinary and streaming transport;
- raw stream parsing;
- complete native history;
- request-ID cancellation;
- raw provider error mapping;
- model discovery where supported.

Interactive login, secure credential persistence, multi-session operations,
and frontend protocol behavior do not belong in provider code.

## Configuration

Treat the resolved config mapping as immutable by convention.

- Explicit config values take precedence.
- Environment lookup may be a documented fallback.
- Runtime credentials are not copied into session history, message metadata,
  UI schema, or model descriptors.
- Provider configuration identifies the selected provider explicitly.
- A failed provider request never silently selects another provider.

## Conversion

`to_native_messages` and `from_native_messages` must handle:

- complete history;
- a single newly added message;
- internal metadata needed for reconstruction;
- provider-specific roles or content blocks;
- tool calls and tool results through the active interop contract;
- attachments supported by the active provider/profile.

Remove internal metadata before sending the wire request.

## Native history

Return a coherent full native history:

- append completed messages only;
- never append raw stream chunks;
- remove partial parsing scratch state;
- preserve opaque continuation fields;
- preserve tool IDs and result relationships;
- preserve provider-required reasoning state.

When core/native conversion is lossy, provider-native history is the
continuation source and core messages are its visible projection.

## Streaming

Each partial contains only data introduced by the current chunk. Accumulated
provider state belongs in the shared accumulator.

Use a custom stream reducer when the protocol has indexed content blocks,
multiple event types, partial tool JSON, rewinds, or provider-specific
completion rules.

Streaming and non-streaming requests produce equivalent completed native/core
messages. A prematurely ended or malformed stream fails rather than becoming a
partial final.

## Cancellation

Track active work by request ID. Cancellation:

- closes or cancels the matching transport;
- prevents retries;
- raises the portable cancellation exception;
- prevents completed-history append;
- removes active runtime state;
- is safe when repeated or requested after completion.

## Errors

Normalize provider failures into stable categories suitable for the current
application event contract. Preserve safe provider request IDs and
retryability where supported.

Do not expose:

- API keys or tokens;
- authorization headers;
- full conversation/tool payloads;
- raw sensitive provider responses;
- local credential paths unless explicitly intended for a trusted
  administrative display.

Diagnostic text is bounded and redacted.

## Model discovery

If the endpoint has an authoritative catalog:

- return descriptors with non-empty IDs;
- preserve names and capabilities when available;
- derive stable provider tags;
- return an empty list on discovery failure;
- keep manual model entry usable.

Do not make optimistic feature claims from an unknown model name when
authoritative capabilities or explicit compatibility config are absent.
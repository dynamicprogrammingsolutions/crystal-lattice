# Anthropic provider security and errors

## Credential boundary

API-key mode resolves credentials in this order:

1. non-empty `config["api_key"]`;
2. non-empty `ANTHROPIC_API_KEY` fallback;
3. authentication-required failure.

The resolved credential exists only in request/runtime state. It is not copied
to native history, core messages, session metadata, model descriptors, UI
schemas, or action results.

OAuth credentials and refresh state are outside the baseline and will be
defined by the OAuth task.

## Header and log redaction

The provider never logs:

- API keys or bearer tokens;
- authorization or `x-api-key` values;
- OAuth tokens or refresh material;
- full request payloads containing conversation or tool data;
- provider responses containing sensitive user content.

Safe diagnostics may include:

- provider and profile name;
- model ID;
- request path without query secrets;
- HTTP status;
- stable error category;
- retryability;
- provider request ID;
- bounded schema/protocol failure location.

Generic exception text is sanitized before it becomes an application event.

## Error model

The portable application-facing provider error contains:

```text
error_type
message
provider
request_id
http_status
retryable
details
```

`details` is optional, bounded, and redacted. The provider-native error type may
be retained separately when safe.

Stable categories:

| Category | Typical meaning |
|---|---|
| `validation` | Invalid request field, message ordering, tool schema, or model input |
| `authentication` | Missing or invalid credential |
| `billing` | Account credit or billing state prevents the request |
| `permission` | Credential lacks access to the requested feature/model |
| `not_found` | Requested model or resource does not exist |
| `conflict` | Provider-side state conflict |
| `request_too_large` | Byte, context, or provider request-size limit |
| `rate_limit` | Request or token rate exceeded |
| `timeout` | Connect, response, or inter-chunk timeout |
| `overloaded` | Provider capacity unavailable |
| `provider` | Provider internal/API failure |
| `transport` | Network, TLS, connection, malformed SSE, or premature stream end |
| `cancelled` | Application/user cancellation |

Unknown provider errors map to `provider` or `transport` without leaking the
raw body.

## Retryability

Authentication, billing, permission, validation, and not-found errors are not
retried automatically.

Rate-limit, timeout, overload, transport, and selected provider failures may be
retryable before visible output begins. Retry policy is bounded and respects
provider guidance when safe.

Mid-stream retries must not duplicate visible content or tool calls. Recovery
is disabled unless a feature/profile defines a tested replay policy.

## Cancellation

Cancellation is distinct from failure:

- active transport closes promptly;
- no retry begins;
- no completed assistant message is persisted;
- applications emit `request_cancelled`;
- partial display may remain transient but is not canonical history.

## Compatible endpoints

Profiles can map alternate HTTP/error envelopes into the same stable
categories. Missing provider request IDs are allowed. A compatible provider
must not be labeled as official Anthropic in diagnostics.

## Sensitive attachment behavior

Image bytes are resolved at request time from the application-owned asset
store. Base64 payloads and temporary file paths do not enter ordinary logs.
Remote Files API security is defined separately by the files task.
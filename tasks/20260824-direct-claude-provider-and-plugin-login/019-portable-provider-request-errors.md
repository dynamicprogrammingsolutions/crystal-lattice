# Portable Provider Request Errors

Define a standard structured provider request-error contract across Core, the
application tool loop, lifecycle hooks, HTTP events, terminal rendering, and
frontend SDK state.

## Requirements checklist

### Functional requirements

- [ ] Providers can raise a shared request-error type containing a stable
  category, safe message, provider identity, provider request ID, HTTP status,
  retryability, and bounded redacted details.
- [ ] The application tool loop preserves structured provider errors in the
  existing request-error event flow.
- [ ] Request-error lifecycle hooks receive the same structured error payload.
- [ ] HTTP/SSE, terminal rendering, and frontend SDK state preserve optional
  structured fields while remaining compatible with existing `detail`-only
  errors.
- [ ] Providers can retain a safe provider-native error subtype.
- [ ] Generic exceptions continue to produce the existing safe fallback event.

### Non-functional requirements

- [ ] Provider request retries remain provider-owned.
- [ ] Login, refresh, status, and logout remain auth-plugin responsibilities,
  not frontend or generic error-runner behavior.
- [ ] Frontends render or expose plugin actions but do not infer credential
  lifecycle from error strings.
- [ ] Structured details never expose credentials, authorization headers, raw
  sensitive payloads, or unbounded provider bodies.
- [ ] Existing cancellation behavior remains distinct and backward compatible.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `docs/development/specifications/portable-provider-implementation/index.md`

Primary requirement IDs:

- `PPI-008`
- `ANTH-011`

## Current behavior and problem

`ProviderRequestCancelled` is a shared typed exception, but ordinary provider
failures reach `ToolLoopRunner` as generic exceptions. The current error event
primarily preserves `detail` and `request_id`.

A provider can classify authentication, billing, permission, validation,
rate-limit, timeout, overload, transport, and internal errors locally, but the
classification, retryability, HTTP status, and provider request ID are lost at
the application boundary. Package-local exception attributes are not currently
preserved by the generic tool loop.

Without a shared contract, a provider can still:

- sanitize and raise a safe error string;
- retry eligible requests inside its transport;
- include a provider request ID in bounded text;
- keep provider-native categories for package-local diagnostics.

The frontend and lifecycle hooks cannot reliably distinguish categories
without parsing text.

## Proposed contract

The planning baseline is a shared exception similar to:

```python
class ProviderRequestError(RuntimeError):
    error_type: str
    provider: str
    request_id: str | None
    provider_request_id: str | None
    http_status: int | None
    retryable: bool
    provider_error_type: str | None
    details: dict | None
```

`ToolLoopRunner` catches it before generic `Exception` and emits the existing
error event with optional structured fields:

```json
{
  "type": "error",
  "detail": "Provider rate limit exceeded",
  "error_type": "rate_limit",
  "provider": "anthropic",
  "request_id": "application-request-id",
  "provider_request_id": "provider-request-id",
  "http_status": 429,
  "retryable": true
}
```

The same mapping enters request-error lifecycle context and passes through
HTTP/SSE and clients. Existing consumers continue to use `detail`.

## Execution plan

Status: Draft

No additional protocol research is required before planning. Revisit this task
when the standard request-error work is scheduled. At that time, confirm the
shared taxonomy, event compatibility, redaction, lifecycle payload, and
incremental provider-adoption plan.

### Implementation decisions and open questions

- Decision: retries stay in each provider.
- Decision: auth plugins own login lifecycle and actions.
- Decision: lifecycle-hook transparency is a primary reason for the contract.
- Decision: preserve the existing error event and add optional fields rather
  than requiring a new event type.
- Decision: generic exceptions remain a backward-compatible fallback.
- Open: finalize the stable error taxonomy and whether `details` needs a typed
  JSON schema.
- Open: decide whether retryability is provider-declared only or can be
  normalized from shared categories.

### Documentation

- Update Core/application event documentation, frontend SDK event types, and
  the portable provider authoring standard when implemented.
- Provider packages document native-to-portable error mappings without
  redefining the shared event.

### Task checklist

- [ ] Approve the shared taxonomy and event fields.
- [ ] Add the shared Core exception/value contract.
- [ ] Preserve structured fields in `ToolLoopRunner` and lifecycle context.
- [ ] Preserve fields through HTTP/SSE and frontend SDK state.
- [ ] Add terminal rendering and backward-compatibility behavior.
- [ ] Convert Anthropic as the first provider consumer.
- [ ] Add generic, lifecycle, HTTP, SDK, terminal, and provider mapping tests.
- [ ] Document the delivered contract and update evidence.

### Requirement verification

- A provider authentication or rate-limit error reaches lifecycle hooks and
  clients with stable fields and a safe `detail`.
- Existing detail-only error consumers continue to function.
- Provider-owned retry behavior does not move into the application layer.
- Auth-plugin actions remain the only owners of login lifecycle.

### Additional implementation verification

- Raw provider bodies and secrets remain absent from every serialized path.
- Unknown provider exceptions still produce the generic fallback event.
# Provider Request-ID Cancellation Wiring

Add provider-level cancellation using a serializable contract: request execution receives a caller-supplied `request_id`, and providers expose a separate `cancel_request(request_id)` method so the application or plugin host can cancel the correct in-flight request without passing non-serializable callbacks across the app/plugin boundary.

## Requirements checklist

- [x] Extend the provider contract to support caller-supplied `request_id` on request execution and a separate `cancel_request(request_id)` method.
- [x] Keep the provider/application interface serializable so the same design can work through a future language-neutral plugin host over stdin/stdout.
- [x] Thread request identity through `AgentApplication` -> `ToolLoopRunner` -> `AgentCore` -> provider wrapper/adapter -> concrete providers.
- [x] Ensure provider cancellation is request-scoped so one provider instance can safely handle multiple concurrent requests.
- [x] Map provider-side cancellation back to normal application cancellation flow (`request_cancelled`, not generic error).
- [x] Implement first-class provider cancellation for `openrouter` and `openai_responses`.
- [x] Add unit/integration coverage at application/core/provider levels, including real API integration tests for OpenRouter and OpenAI Responses.
- [x] Extend the same request-id cancellation support to the reference `openai_compatible` provider, with unit tests and real Ollama streaming-cancel coverage.

## Background

Current state after the shell/tool cancellation work:

- Request-level cancellation bookkeeping exists in `core/python/agent_app/application_future.py`.
- Tool-loop cancellation exists and can interrupt shell tools during tool execution.
- Provider execution is still missing live cancellation wiring for ongoing provider requests.

Current gaps:

- Providers do not receive a request identifier in `call_api` / `stream_api`.
- Providers do not expose a supported cancel method.
- The provider protocol currently assumes in-process direct calls and does not fit a future serializable plugin boundary.
- Existing server/provider tests do not cover cancelling an already-running provider request end-to-end.

Relevant code references:

- `core/python/agent_app/application_future.py`
  - Generates and owns `request_id`
  - `cancel_request(request_id)` is the app entry point
- `core/python/agent_app/tool_loop.py`
  - Orchestrates request phases
  - Needs to trigger provider cancellation while provider request is in flight
- `core/python/agent_core/core.py`
  - `send_request(...)`
  - `send_request_stream(...)`
- `core/python/agent_core/types.py`
  - Provider protocol surface
- `core/python/agent_core/plugin/provider.py`
  - Provider wrapper and adapter forwarding
- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
  - Current blocking HTTP request/stream implementation
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/openai_responses@f216464a6222b216cc91ec90c53f6043ff7f435bb1efd5ace5611b96a1d1b141/openai_responses_plugins/openai_responses_provider.py`
  - Current blocking OpenAI Responses SDK request/stream implementation

## Proposed design

### Core principle

Keep the caller/plugin contract serializable.

Instead of passing a live cancellation callback/handle into the provider API, the caller supplies a `request_id` when starting provider execution, and the provider exposes a separate:

```python
cancel_request(request_id: str) -> bool
```

The application/tool-loop can keep the actual live callback on the same in-process wrapper or plugin host object. In a future language-neutral plugin runtime, the host process can receive:

- `call_api(..., request_id="req-123")`
- `stream_api(..., request_id="req-123")`
- later: `cancel_request("req-123")`

and internally route that cancel to the correct runtime object.

### Provider protocol changes

Suggested shape:

```python
class ProviderPlugin(BasePlugin, Protocol):
    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        ...

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        ...

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        ...

    def stream_api_async(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        ...

    def cancel_request(self, request_id: str) -> bool:
        ...
```

Compatibility notes:

- `request_id` should be optional.
- Wrapper/adapter forwarding should use the existing optional-kwargs pattern so old providers still work.
- `cancel_request` should default to `False` in adapters when the provider does not implement it.

### Runtime ownership model

Do not serialize active cancel callbacks into provider state.

Serialized provider state should remain plain data. The runtime owner of the provider execution should keep a request-local in-memory registry:

```python
self._inflight_requests: dict[str, AbortHandle]
```

where `AbortHandle` is internal/runtime-specific and not part of the serializable contract.

That registry can live:

- on the Python provider instance now, or
- on a future plugin host object that wraps a language-neutral plugin process.

### Application/core wiring

1. `AgentApplication.send_request(...)` already generates/owns `request_id`.
2. `ToolLoopRunner` should pass `request_id` into provider execution through `AgentCore`.
3. `AgentCore.send_request(...)` and `send_request_stream(...)` should accept optional `request_id`.
4. During the provider phase, the tool loop should register an internal cancellation callback that calls:

```python
provider.cancel_request(request_id)
```

on the same wrapper/host object handling that request.

5. If provider execution exits because of cancellation, the application should emit `request_cancelled` rather than a generic error event.

### Provider implementation direction

#### OpenRouter

- Use request-local transport objects that can be closed on cancel.
- Prefer a transport with explicit close semantics for both streaming and non-streaming request interruption.
- Register an abort handle under `request_id` when the request starts.
- Remove it in `finally`.
- Treat transport-close during a cancelled request as cancellation rather than provider failure.

#### OpenAI Responses

- Pass caller-supplied `request_id` into provider execution.
- Register the in-flight request/stream object under `request_id`.
- On `cancel_request(request_id)`, close the matching stream/client/transport.
- Convert transport/stream-close caused by cancellation into a provider-cancelled path rather than a normal error path.

## Implementation plan

1. Extend the provider protocol in `core/python/agent_core/types.py` with optional `request_id` and `cancel_request(request_id)`.
2. Update provider adapters/wrappers in `core/python/agent_core/plugin/provider.py` and related defaults adapters to forward `request_id` optionally and expose `cancel_request`.
3. Extend `AgentCore.send_request(...)` and `AgentCore.send_request_stream(...)` to accept `request_id` and pass it through provider initialization and provider request execution.
4. Update `ToolLoopRunner` so the provider phase registers a live cancel callback that calls `provider.cancel_request(request_id)` while provider work is active, then unregisters it when provider work ends.
5. Add an internal provider-cancelled exception or equivalent normalization path so user cancellation yields `request_cancelled`.
6. Implement request-local cancellation registries for `openrouter` and `openai_responses`.
7. Add unit tests first, then application/server tests, then real API integration tests for the first two providers.

## Test plan

### 1. Core/provider contract tests

Purpose:
- Verify the framework passes the caller-supplied request id all the way to the provider.
- Verify the framework calls `provider.cancel_request(request_id)` on the correct active provider object.
- Verify request lifecycle events remain correct when provider cancellation happens.

Likely location:
- `core/python/tests`

Tests to add:

- A fake provider that records `request_id` values seen by `initialize_request`, `call_api`, and `stream_api`.
  - Assert the same `request_id` supplied by `AgentApplication.send_request(..., request_id=...)` reaches all expected provider hooks.
- A fake streaming provider that blocks until its `cancel_request(request_id)` flips an internal event.
  - Start request in a worker thread.
  - Cancel after `request_started`.
  - Assert:
    - `provider.cancel_request()` was called with the same `request_id`
    - only that request is released
    - emitted events include `request_started`, `request_cancelled`, `request_completed`
    - emitted events do not include an ordinary final assistant response
- A fake provider with two concurrent request ids.
  - Cancel only one id.
  - Assert the other request continues and completes normally.

Mocking strategy:
- No external network.
- Use deterministic fake providers defined in test fixtures.

### 2. Application-level cancellation tests

Purpose:
- Verify live cancellation works for an already-running provider request, not only pre-cancel.
- Verify app state and request bookkeeping are cleaned up afterward.

Likely location:
- `core/python/tests/test_application_layer_streaming.py`

Tests to add:

- Ongoing streaming provider request, cancel before first streamed partial.
  - Start request.
  - Wait for `request_started`.
  - Cancel immediately.
  - Assert:
    - thread/iterator exits
    - `request_cancelled` and `request_completed` are emitted
    - no normal `final` event is emitted
- Ongoing streaming provider request, cancel after first partial.
  - Start request.
  - Wait until at least one `partial` event is observed.
  - Cancel.
  - Assert:
    - stream stops promptly
    - `request_cancelled` emitted
    - no extra partials arrive after a short grace period
- Ongoing non-streaming provider request, cancel while blocked in provider call.
  - Start request with fake provider blocked inside `call_api`.
  - Cancel after `request_started`.
  - Assert the request exits promptly and is reported as cancelled.
- Follow-up request after cancellation.
  - Assert a new request on the same agent/session still completes normally.

Mocking strategy:
- Use fake providers or controlled blocking test providers.
- No external network.

### 3. HTTP/server end-to-end tests

Purpose:
- Verify `/requests/{request_id}/cancel` works for an already-active background request.
- Verify active request bookkeeping is cleared after cancellation.

Likely location:
- `application/python/tests/test_agent_terminal_app_server.py`

Tests to add:

- Start a background send request against a blocking fake provider.
- Wait until `request_started` and confirm session/messages endpoint shows the matching `active_request_id`.
- Call the server cancel endpoint while request is still active.
- Assert:
  - background worker exits
  - event store contains `request_cancelled` and `request_completed`
  - no ordinary `final` assistant response is emitted
  - a later session/messages read reports `active_request_id is None`

Mocking strategy:
- Use test app config wired to a fake blocking provider.
- No external network.

### 4. Provider-level unit tests

Purpose:
- Verify the provider’s request-local registry, cleanup, and cancel routing work correctly.

Likely locations:
- `plugins/openrouter/tests`
- provider-specific tests alongside OpenAI Responses plugin tests

Tests to add for each provider:

- Register in-flight request on start and remove on completion.
- `cancel_request` returns `False` for unknown/already-finished request id.
- `cancel_request` is idempotent for same request id.
- Two concurrent request ids do not interfere with each other.
- Cancellation-triggered transport close is normalized to cancellation, not leaked as unrelated provider exception.

Mocking strategy:
- Use fake transport/client objects for unit-level coverage.
- No real API in this layer.

### 5. Real API integration tests for OpenRouter

Purpose:
- Verify real upstream behavior with a live OpenRouter request and actual connection abort logic.

Likely location:
- `plugins/openrouter/tests`
- mark with existing integration/openrouter markers as appropriate

Required cases:

- Streaming request cancelled before first streamed token is emitted.
  - Use a real model and streaming request.
  - Start request in worker thread/process.
  - After the request is definitely sent, wait only a short interval, then call `cancel_request(request_id)`.
  - Assert:
    - local request exits promptly
    - request is reported as cancelled
    - no hang remains in the test process
- Streaming request cancelled after streaming has started.
  - Wait until the first partial token/event is observed.
  - Cancel.
  - Assert:
    - stream stops promptly
    - cancellation is surfaced instead of a generic failure
    - cleanup occurs

Optional but useful:

- Non-streaming OpenRouter request cancellation.
  - This may only guarantee local unblock, not upstream stop.
  - Assert the local app/provider exits promptly after cancellation.
  - Do not over-assert upstream billing/processing behavior.

Real API notes:

- Use explicit timeouts to avoid flaky hangs.
- Choose prompts/models likely to produce enough output for mid-stream cancellation.
- Capture timing so the test can assert cancellation latency within a reasonable bound.

### 6. Real API integration tests for OpenAI Responses

Purpose:
- Verify real cancellation behavior for normal in-flight OpenAI Responses requests by terminating the client connection/stream.

Likely location:
- tests adjacent to the OpenAI Responses provider plugin
- mark as integration

Required cases:

- Streaming request cancelled before streaming visibly starts.
  - Start real streaming request.
  - After the request is sent, cancel quickly before first partial arrives if possible.
  - Assert local request exits promptly and is treated as cancelled.
- Streaming request cancelled after first partial/output event.
  - Wait for first streamed partial.
  - Cancel.
  - Assert stream exits promptly and is treated as cancelled.

Optional but useful:

- Non-streaming request cancelled while waiting for full response.
  - Assert local request unblocks promptly.
  - Treat transport-close behavior as success for cancellation semantics, even if upstream computation may already be underway.

Real API notes:

- Keep retries low or disabled in these tests so cancellation behavior is not masked by automatic retry logic.
- Use prompts/models likely to yield multiple streamed events for the mid-stream case.

## Assertions to be careful about

Do assert:

- Cancellation is request-scoped.
- Application exits promptly after cancellation.
- Provider cleanup runs and the in-flight registry entry is removed.
- Event stream shows `request_cancelled`.
- The cancelled request does not poison subsequent requests.

Do not over-assert:

- Exact upstream billing outcome.
- Exact upstream stop timing beyond reasonable local cancellation latency.
- Exact token count or exact final transport exception class across SDK/library versions.

## Open questions during implementation

- Whether `openai_responses` can reliably unblock through SDK object close alone, or should be switched to a lower-level transport for stronger cancellation control.
- Whether `openrouter` should keep `requests` or migrate to a transport abstraction with clearer live-close semantics for both sync and streaming paths.
- Whether provider cancellation should use a dedicated internal exception type to simplify clean mapping to `request_cancelled`.

## Execution plan

Added during completion on 2026-04-04.

1. Extend the provider protocol, wrapper, and defaults adapter to accept optional `request_id` on request execution and expose `cancel_request(request_id)` with a safe fallback for legacy providers.
2. Thread `request_id` through `AgentApplication`, `ToolLoopRunner`, and `AgentCore`, and register a provider-phase cancellation callback that invokes `provider.cancel_request(request_id)` on the active wrapper.
3. Add an internal provider-cancelled exception path so provider-side cancellation becomes `request_cancelled` instead of a generic error.
4. Implement request-scoped in-flight registries for `openrouter` and `openai_responses`, using request-local abortable transports and guaranteed cleanup in `finally`.
5. Add deterministic fake-provider tests at core/application/server levels for ongoing provider cancellation, including concurrent-request isolation.
6. Add provider unit tests for registry behavior and cancellation idempotency.
7. Add real API integration tests for OpenRouter and OpenAI Responses covering:
   - cancel shortly after request send, before visible streaming output
   - cancel after the first streamed partial arrives
8. Run focused test suites first, then adjacent suites for regression coverage, and record outcomes back into this task file.

## Completion Notes

Added during completion on 2026-04-04:

- Extended the provider protocol in `core/python/agent_core/types.py` so provider request execution accepts optional `request_id`, and providers expose `cancel_request(request_id) -> bool`.
- Added `ProviderRequestCancelled` as the internal normalized cancellation exception for provider execution.
- Updated provider adapter/wrapper forwarding in:
  - `core/python/agent_core/plugin/adapters.py`
  - `core/python/agent_core/plugin/provider.py`
- Threaded provider request identity through:
  - `core/python/agent_core/core.py`
  - `core/python/agent_app/tool_loop.py`
- `ToolLoopRunner` now passes `request_id` into provider execution and supplies provider-phase live cancellation by registering an internal callback that calls `provider.cancel_request(request_id)` on the active wrapper.
- Provider-side cancellation now maps back to `request_cancelled` instead of surfacing as a generic error.
- Implemented request-scoped in-flight registries and best-effort transport shutdown in:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- Added deterministic fake-provider coverage and app/server tests in:
  - `core/python/tests/dummy_provider.py`
  - `core/python/tests/test_application_layer_streaming.py`
  - `application/python/tests/test_agent_terminal_app_server.py`
- Added provider unit coverage in:
  - `plugins/openrouter/tests/test_openrouter_provider_unit.py`
  - `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- Added real API integration cancellation coverage in:
  - `plugins/openrouter/tests/test_openrouter_basic_integration.py`
  - `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`

Verification run during completion:

- `python -m compileall core/python/agent_core/types.py core/python/agent_core/plugin/adapters.py core/python/agent_core/plugin/provider.py core/python/agent_core/core.py core/python/agent_app/tool_loop.py core/python/tests/dummy_provider.py core/python/tests/test_application_layer_streaming.py application/python/tests/test_agent_terminal_app_server.py plugins/openrouter/src/openrouter_plugins/openrouter_provider.py plugins/openrouter/tests/test_openrouter_provider_unit.py plugins/openrouter/tests/test_openrouter_basic_integration.py plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py plugins/openai_responses/tests/test_openai_responses_provider_integration.py`
- `pytest core/python/tests/test_application_layer_streaming.py application/python/tests/test_agent_terminal_app_server.py plugins/openrouter/tests/test_openrouter_provider_unit.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- `pytest core/python/tests/test_application_layer_tools.py core/python/tests/test_application_layer_streaming.py application/python/tests/test_agent_terminal_app_server.py -q`
- `pytest plugins/openrouter/tests/test_openrouter_provider_unit.py plugins/openrouter/tests/test_openrouter_provider_isolation.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py plugins/openai_responses/tests/test_openai_responses_provider_isolation.py -q`
- `pytest plugins/openrouter/tests/test_openrouter_basic_integration.py -q`
- `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`

Notes:

- The provider/application contract remains serializable: request execution takes a caller-owned `request_id`, and cancellation uses a separate `cancel_request(request_id)` method.
- Runtime-only transport handles remain internal to the provider implementation and are not stored in serialized provider state.

Added during completion on 2026-04-05:

- Extended the same request-id cancellation model to the reference `openai_compatible` provider in `core/python/plugins/openai_provider.py`.
- Added focused unit coverage in `core/python/tests/test_openai_provider_unit.py` for unknown-id, streaming, and non-streaming cancellation.
- Extended the real Ollama integration coverage in `core/python/tests/test_openai_compat_ollama.py` with:
  - cancellation shortly after request start, before visible streaming output
  - cancellation after the first streamed partial
- Extended the packaged reference provider in `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py` with the same request-id cancellation model so hosted-provider integration suites exercise live cancellation too.
- Added hosted Fireworks cancellation coverage in `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_cancellation.py` for:
  - cancellation shortly after request start
  - cancellation after the first streamed partial

Verification run for the reference provider follow-up:

- `python -m compileall core/python/plugins/openai_provider.py core/python/tests/test_openai_provider_unit.py core/python/tests/test_openai_compat_ollama.py`
- `pytest core/python/tests/test_openai_provider_unit.py -q`
- `pytest core/python/tests/test_openai_compat_ollama.py -q`
- `python -m compileall plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_cancellation.py`
- `pytest plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_cancellation.py -q`
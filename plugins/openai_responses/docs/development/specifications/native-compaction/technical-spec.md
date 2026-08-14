# Native conversation compaction technical specification

## Architecture

Native compaction has four cooperating layers:

```text
Application action and process
  admission, background lifecycle, progress, cancellation, commit

Provider extension
  visible-prefix selection, effective request initialization,
  input sanitization, result application, transcript rebuild

Compaction backend and transport
  auth-mode protocol selection, HTTP/SDK execution, V2 stream collection

OpenAI or ChatGPT backend
  V1 replacement output or V2 encrypted compaction item
```

The application process injects a cancellable async transport into the
provider-extension action. The synchronous compatibility action builds a
synchronous transport directly. Both transports implement the same logical
operation and return a compact-response-shaped mapping to the extension.

## Effective mode

The extension derives a compaction configuration before constructing a
transport:

- with `use_chatgpt_auth_for_compaction` enabled, it preserves the effective
  normal-request authentication mode;
- with the setting disabled, it forces effective API mode, selects
  `api_base_url` or the default API URL, and removes ChatGPT credentials.

The transport reads this effective mode:

- `api` selects V1;
- `chatgpt` selects V2.

There is no independent protocol-version configuration because protocol
support follows the selected upstream authentication surface.

## Input boundary

The action accepts an optional visible `end_index`. Omission means full visible
history. A valid selection:

- is greater than zero;
- does not exceed the visible message count;
- begins at native-history index zero;
- maps to a contiguous native prefix, allowing unmapped opaque compaction
  items already contained within that prefix.

Before compaction, action-request initialization runs the same feature and
extension pipeline used for ordinary requests. This supplies effective
instructions, rendered system/developer content, tool schemas, reasoning
settings, service tier, prompt-cache settings, and other request state.

Internal metadata and response-only fields are removed from compact input.
Opaque compaction items retain only their accepted wire fields.

## API/V1 protocol

API mode invokes the OpenAI SDK compact resource:

```python
client.responses.compact(
    model=model,
    input=input_items,
    instructions=instructions,
    timeout=timeout,
)
```

The response must provide a non-empty `output` list. That list becomes the
replacement for the selected native prefix after output sanitization and
leading-message restoration. The untouched native suffix is appended.

The async transport performs the same operation with `AsyncOpenAI`, allowing
the application process to cancel the active task and close the client.

## ChatGPT/V2 protocol

ChatGPT mode invokes normal streamed Responses creation:

```json
{
  "model": "<compaction model>",
  "input": [
    "... selected native prefix ...",
    {"type": "compaction_trigger"}
  ],
  "store": false,
  "stream": true
}
```

The request includes:

```text
x-codex-beta-features: remote_compaction_v2
```

The transport may also carry compatible request options:

- `include`;
- `parallel_tool_calls`;
- `prompt_cache_key`;
- `reasoning`;
- `service_tier`;
- `text`;
- `tool_choice`;
- `tools`.

Sampling-only or unrelated options are not forwarded. The transport waits for
`response.completed`, collecting `response.output_item.done` events. If item
events are absent, it may read the completed response's output list.

Success requires exactly one item with type `compaction` or
`compaction_summary`. A missing completion event, missing compaction item, or
multiple compaction items fails the operation without changing session
history.

## V2 retained history

V2 returns encrypted compaction state rather than a complete replacement
history, so the client constructs the replacement prefix.

The retained set includes:

- user messages;
- system messages;
- developer messages;
- non-final agent messages that fit the per-message budget.

Retention uses a bounded newest-first budget of approximately 64,000 tokens.
Individual agent messages above approximately 10,000 tokens are not retained.
Final-answer agent messages are excluded. Token estimates are intentionally
approximate and are used only for local retention bounds.

The single returned compaction item follows retained messages. The request's
`compaction_trigger` is never included. Output-item IDs and encrypted content
are preserved through output sanitization.

The extension then restores a separately retained leading system/developer
message when needed and appends the untouched native suffix.

## Visible transcript

After native history changes, Core rebuilds visible messages and native-index
mappings. Two projections are supported:

- expanded mode rebuilds normal visible messages and surfaces otherwise
  invisible compaction summaries as placeholders where needed;
- placeholder mode collapses each compacted native segment into one assistant
  placeholder carrying the canonical native segment in metadata.

Toggling projection does not alter canonical native history.

## Background lifecycle and concurrency

The application plugin acquires a session operation lease before starting
provider work. It captures:

- the current session;
- effective configuration and overrides;
- baseline filesystem state;
- action request context.

The process creates a persistent progress notification and runs the provider
action on a worker thread. Cancellation:

- marks the operation invalid;
- cancels the async SDK task;
- disables later commit;
- publishes a cancellation result.

Before saving, the process rechecks invalidation while holding the session
lock. Persistence reconciles against the baseline and reports concurrent
history modification as a conflict rather than silently replacing it.

## Failure behavior

Compaction does not mutate the stored session until provider output has been
validated and the commit boundary is reached.

Failures are categorized for users as:

- missing credentials or forced-API mode without an API key;
- provider or HTTP failure;
- malformed V1 output;
- incomplete or malformed V2 stream;
- cancellation or application shutdown;
- concurrent session-history conflict.

The background notification contains a retry action for provider and conflict
failures. Error text is bounded before display.

## Verification strategy

Acceptance coverage includes:

- API/V1 calls remain on the SDK compact resource;
- ChatGPT/V2 uses streamed Responses with the trigger and beta header;
- compatible request options are carried to V2;
- full and partial compaction produce reusable native history;
- saved ChatGPT login supports initial request, async V2 compaction, and a
  follow-up request through the real hosted endpoint;
- cancellation interrupts delayed V1 and V2 HTTP exchanges;
- background cancellation prevents result commit;
- concurrent history changes prevent compaction commit.

Low-level parsing and helper tests may exist without corresponding requirement
IDs when they do not define an additional user-visible contract.
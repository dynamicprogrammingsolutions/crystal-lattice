# Anthropic provider technical specification

## Package architecture

The package uses the public identity `anthropic` and the implementation module
`anthropic_plugins`.

```text
AnthropicProvider
  transport, auth consumption, model discovery, native conversion,
  streaming, cancellation, raw errors

AnthropicToolsExtension
  tool schemas, tool use/results, streamed argument reconstruction

AnthropicReasoningExtension
  thinking configuration, effort, thinking blocks, signatures

AnthropicUsageExtension
  public usage metadata, formatting, cumulative totals, cost

AnthropicPromptCachingExtension
  cache configuration, UI, request shaping, retention controls

AnthropicAttachmentsExtension
  image policy/UI/actions and compatible-endpoint gating
```

The provider remains functional without the extensions. The standard bundle
registers all five extensions, and tag/capability resolution decides which are
active for a request.

## Configuration

Provider-owned baseline keys:

| Key | Purpose |
|---|---|
| `provider` | Provider selector; value `anthropic` |
| `auth_mode` | Baseline value `api`; future values `oauth` and `auto` |
| `api_key` | Resolved API key; primary credential input |
| `base_url` | Messages API root |
| `models_url` | Optional model-discovery URL override |
| `model` | Selected discovered or explicitly entered model ID |
| `anthropic_version` | API version header value |
| `timeout` | Request timeout |
| `max_retries` | Generic pre-stream transport retry limit when supported |
| `compatibility_profile` | Named compatibility profile |
| `compatibility` | Explicit capability/auth/request overrides |
| `headers` | Non-secret additional headers permitted by policy |

Extension-owned keys are defined by their extension schemas. Request options
that do not have a provider-specific user contract may continue through the
generic request-options feature.

Config wins over direct environment lookup. A missing `api_key` may use
`ANTHROPIC_API_KEY` as a fallback only for API auth.

## Model discovery

The default model URL is `<base_url>/v1/models` unless `models_url` is set.

Official model responses are normalized into model descriptors containing:

- `id`;
- display name;
- created time when useful;
- maximum input and output tokens;
- raw capability data;
- normalized capability tags.

Published capabilities control UI and extension enablement. Unknown capability
fields are preserved in the model descriptor or ignored safely. Missing
capabilities never cause optimistic enablement.

Compatible OpenAI-style model responses containing `data[*].id` are accepted.
When no capabilities are present, the selected compatibility profile supplies
conservative defaults.

Model discovery failures return an empty model list and log a bounded,
redacted warning. They do not prevent explicit model entry.

## Provider state

Recommended request state:

```python
{
    "config": effective_config,
    "request": {
        "url": ".../v1/messages",
        "payload": {...},
        "headers": {...},
        "timeout": 300,
    },
    "accumulator": {
        "role": "assistant",
        "content": [],
    },
    "compatibility": {...},
    "raw_usage": None,
}
```

Provider and extensions share the state. Extensions merge their fields and
must not replace unknown accumulator keys.

## Request lifecycle

1. Core resolves the provider, extensions, features, tools, models, and tags.
2. The provider converts core history to Anthropic-native history.
3. The provider initializes the Messages request, auth headers, compatibility
   state, and empty accumulator.
4. Extensions add tool schemas, reasoning controls, caching, and attachment
   state.
5. Generic request options apply after provider-specific extension shaping
   according to established priority.
6. The provider performs ordinary or streaming transport.
7. The provider reduces native content-block events into complete native
   assistant history.
8. Extensions finalize tool calls, reasoning, usage, caching metadata, and
   attachment state.
9. The provider and extensions convert finals to core messages.
10. Core persists the complete provider-native history.

## Provider and extension boundary

An extension owns:

- feature configuration schema;
- UI declarations;
- tags and required tags;
- capability gating;
- normalized feature state;
- request shaping;
- public metadata;
- feature-specific tests and documentation.

The provider may own inseparable transport mechanics such as retrying a
fast-mode request, parsing a provider-native event used by an extension, or
closing the active stream. Those mechanics must consume normalized extension
state and must not independently expose feature config or UI.

## Prompt caching

Prompt caching is baseline and extension-owned.

The official profile defaults to automatic caching. Supported settings include:

- enabled/disabled;
- automatic or explicit mode;
- five-minute or one-hour retention;
- optional explicit breakpoints.

The extension writes request-only cache controls. The usage extension surfaces
cache-read and cache-creation counts. Compatible profiles that do not declare
caching support omit all cache fields.

## Attachments

The baseline supports image attachments and multimodal tool results.
`AnthropicAttachmentsExtension` owns session asset actions and UI. The provider
owns the final conversion to Anthropic image blocks and request-time asset
resolution.

PDF, document, remote Files API, and citation behavior are outside the
baseline.

## Cancellation

Each active request is registered by `request_id`. Cancellation:

- marks the runtime cancelled;
- closes the active response/client or cancels the transport task;
- causes the provider to raise `ProviderRequestCancelled`;
- removes the runtime after completion;
- never appends a partial assistant message as a completed history item.

## Follow-up feature boundary

Server web tools, fast mode/service tiers, native compaction/context editing,
Files/PDFs/citations, token counting, and advanced server tools extend this
package through separate tasks. Each must update this specification or add a
linked package refinement before implementation.
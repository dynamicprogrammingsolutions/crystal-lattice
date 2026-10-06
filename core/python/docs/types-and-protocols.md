# Core types and plugin protocols

This page is a compact map of the values and plugin relationships that make up
the Core Python SDK. Use it to understand the model without reading source
code. For complete Python signatures, use the
[generated types and protocols reference](reference/types.md);
for implementation recipes, use the
[shared plugin development documentation](../../../plugins/docs/index.md).

## Important types

| Type | Purpose |
|---|---|
| `MessageRole` | One of `system`, `user`, `assistant`, or `tool` |
| `Message` | A completed core conversation message |
| `PartialMessage` | An incremental message emitted while streaming |
| `Session` | A conversation identifier, ordered core messages, and session metadata |
| `ToolDescriptor` | Core's normalized view of one tool schema and its owning plugin |
| `ProviderRequestCancelled` | Provider cancellation signal associated with an optional request ID |

Providers also return model descriptor dictionaries from `get_models`. Each
descriptor has a non-empty string `id`; additional keys are provider-defined
metadata. This is currently a dictionary contract rather than a distinct
exported data class.

### Messages

`Message` contains:

- `role`: the core role;
- `content`: text or another provider-independent content value;
- `metadata`: optional auxiliary information such as citations or tool-call
  identifiers;
- `multipart_content`: optional structured content parts;
- `tool_result`: an optional structured tool result.

`Message.to_dict()` uses the external keys `multipartContent` and `toolResult`
for the last two fields. `Message.from_dict()` accepts those same keys.

A `PartialMessage` carries a role, an incremental content value, and optional
metadata. Each partial is new stream output; it is not necessarily the full
assistant response accumulated so far.

### Sessions and immutability

`Message`, `PartialMessage`, `ToolDescriptor`, and `Session` are frozen
dataclasses. Assigning a new value to a dataclass field is rejected. Nested
lists and dictionaries are ordinary mutable Python containers, however, so
callers must treat returned values as immutable by convention.

Use `AgentCore` operations such as `add_message`, `modify_message`,
`slice_session`, `fork_session`, and `join_sessions` to produce new sessions.
Do not mutate `session.messages`, message metadata, or session metadata in
place.

Serialization methods create dictionary representations suitable for
persistence or transport:

```python
data = session.to_dict()
restored = Session.from_dict(data)
```

## Core and provider-native messages

Core messages provide one provider-independent conversation history.
Provider-native messages retain the exact structures required by a provider,
including provider-specific tool calls, reasoning items, cache metadata, or
special roles.

```text
core Message values
        │  provider/extension/feature conversion
        ▼
provider-native history
        │  provider request and response processing
        ▼
provider/extension/feature conversion
        │
        ▼
new core Message values in a new Session
```

Core can retain provider-native history in session metadata because conversion
may be lossy. Integrity metadata ties that retained history to the visible core
messages. Session-editing operations preserve, rebuild, or discard native
history according to the operation and available provider configuration.

Provider authors should return coherent full native history, append final
assistant messages rather than raw stream chunks, and preserve provider-only
information needed on later turns. See the
[provider guide](../../../plugins/docs/provider-plugins.md#deep-dive-native-history-retention)
for detailed rules and tests.

## Plugin families

Plugins are structural Python protocols. A plugin can implement the required
attributes and methods without inheriting the protocol class, although
subclassing can improve editor and type-checker feedback.

| Kind | Primary responsibility | Request path | State ownership |
|---|---|---|---|
| Provider | Convert messages and perform model API I/O | hot and cold paths | initializes shared provider state |
| Provider extension | Add provider-language behavior such as tool calls or reasoning | hot and cold paths | reads and updates shared provider state |
| Feature | Add provider-independent cold-path behavior, actions, templates, or completions | cold path | reads and updates shared provider state |
| Tool | Expose schemas and execute model-requested operations | tool preparation/execution path | owns separate tool state |

Providers, provider extensions, and features collaborate through one explicit
state dictionary for a request. Tools are initialized independently and retain
their own state. Plugin instances are short-lived; durable state belongs in
application-managed storage rather than instance attributes.

All plugin families share identity (`name` and `version`) plus configuration
schema and UI contribution hooks. Adapters supply compatibility and default
implementations for optional hooks.

## Request flow

The exact order depends on enabled plugins and whether the provider streams,
but the main non-streaming flow is:

```text
resolve provider, models, tags, and enabled plugins
  → prepare tools and collect schemas
  → initialize provider → extensions → features
  → convert core messages to provider-native messages
  → initialize this request
  → call the provider
  → finalize provider → extensions → features
  → convert final native messages to core messages
  → return a new Session and final message dictionaries
```

During streaming:

```text
provider stream_api yields native chunks
  → provider process_chunk
  → provider extensions process the same chunk in order
  → core emits incremental partial messages
  → provider, extensions, and features finalize on the cold path
  → core emits final messages and the new Session
```

Features do not run once per provider chunk. See
[plugin execution order](../../../plugins/docs/plugin-execution-order.md) for
the complete enablement and ordering model.

## Tool-call and message-append hooks

Provider extensions and features can participate in tool-call execution and
session appends through three optional protocol hooks:
`prepare_tool_call`, `finalize_tool_call`, and `prepare_appended_message`.

```text
per tool call (AgentCore.iter_tool_messages / execute_tool_calls):
  inspect the call
    → prepare_tool_call: extensions → features (may transform the call;
      the transformed call is re-inspected before handler resolution)
    → execute the tool
    → finalize_tool_call: extensions → features, exactly once per call,
      on the single final message every call yields (synthesized error
      results included, with a tool_error context fact)

per end-append (AgentCore.add_message with a config):
  prepare_appended_message: extensions → features, before the message is
    converted to provider-native form (so stamped metadata persists into
    native _metadata)
```

The framework provides only raw facts through the context: the call
descriptor, `started_at`/`started_at_mono` and `finished_at`/
`finished_at_mono` timestamps, `session_id`/`request_id`, and `tool_error`
for synthesized results. It never computes durations or stamps messages —
plugins own any measurement derived from these facts. Shared provider state
is threaded through each chain so chained plugins can read each other's
state. The hooks dispatch only when the full plugin context resolves (a
provider is registered and selected); bare-core tool execution without a
provider keeps its current behavior.

See the [feature plugin hooks](../../../plugins/docs/feature-plugins.md)
and [provider extension hooks](../../../plugins/docs/provider-extensions.md)
for authoring guidance.

## Discovery and enablement

`AgentCore` registers providers, extensions, features, and tools as classes.
Discovery can classify structurally compatible classes by their implemented
hooks. At request time, the effective provider, model descriptors, capability
tags, required and forbidden tags, explicit enablement, and plugin-specific
`is_enabled` results determine the active set.

Use the [Core SDK guide](core-sdk.md) for registration and discovery APIs and
the [plugin overview](../../../plugins/docs/overview.md) for authoring
guidance.

## Configuration and UI contributions

Core request methods receive an application-managed configuration dictionary.
When multiple providers are registered, the effective configuration selects
one provider. Each enabled plugin reads its own keys, and configuration schema
hooks describe those keys for applications.

The canonical UI contribution hook is
`get_ui_elements(config, context=None)`. Its context includes resolved tags,
model descriptors, available tools, and effective tools. Adapters retain
compatibility with older hook signatures. Core flattens contributed
dictionaries; applications decide how each `ui_type` is rendered.

See [Application configuration](../../../application/python/docs/configuration.md),
[configuration schemas](../../../plugins/docs/config-schema.md), and
[UI elements](../../../plugins/docs/ui-elements.md) for current formats and
examples.

## Tools and interop

Tool plugins emit source schemas. Core normalizes them as `ToolDescriptor`
values, builds a request-bound interop registry, and adapts schemas into
formats accepted by the selected provider or extension.

When a model emits a tool call, interop accessors identify the tool name and
payload. Core routes that payload to an enabled tool, and the tool formats its
result for model consumption and optional richer display.

Schema, call, and result formats are deliberately not limited to one
OpenAI-compatible shape. See the
[tool plugin guide](../../../plugins/docs/tool-plugins.md) and
[tool interop flow](../../../plugins/docs/tool-interop.md).

## Actions and layered context

Provider extensions and features can expose session-scoped actions.
Application plugins can expose application-level actions that may coordinate
sessions and persistent resources. Core owns the session mutation and
provider-native history rules for Core-side actions.

Execution context is layered:

1. Core contributes the active `AgentCore`, resolved configuration, trigger,
   and session information.
2. `AgentApplication` can add application capabilities, storage, and base
   configuration.
3. Terminal or HTTP integrations can add transport-specific capabilities.

Plugins should test for a capability before using it and must not assume that
higher layers are present in a Core-only call. See
[plugin actions](../../../plugins/docs/actions.md) for the full action,
reserved-key, lifecycle, and context contracts.

## Events and examples

Core request methods return message/session values directly. `agent_app` and
the terminal application additionally expose request progress, tool,
notification, session, message, and snapshot events. See
[Application events](events.md) for ownership and transport boundaries.

Use the [tested examples](examples.md) for complete provider, extension,
feature, tool, streaming, and application flows.

## Which documentation is authoritative?

| Need | Use |
|---|---|
| Mental model and relationships | This page |
| Selected `AgentCore` workflows | [Core SDK guide](core-sdk.md) |
| Exact Python signatures and member semantics | [Generated reference](reference/types.md) |
| Plugin implementation recipes and compatibility | [Plugin development docs](../../../plugins/docs/index.md) |
| Request and lifecycle events | [Application events](events.md) |
| Executable end-to-end examples | [Tested examples](examples.md) |
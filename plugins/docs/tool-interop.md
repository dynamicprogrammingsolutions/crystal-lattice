# Tool interop flow

This page explains how tool interop works across core, providers, provider
extensions, and tool plugins.

It focuses on three related but distinct things:

- tool schema interop
- tool call interop
- tool result message flow

The short version is:

- schemas are adapted at request injection time
- tool calls are interpreted when responses are converted back into core
- tool results are not adapter-based today; they flow through normal
  core-message <-> provider-native message conversion

If you are writing a provider or provider extension, this page explains where
conversions belong and which runtime data you should use.

## Core concepts

### Schema

A tool schema is the provider-facing declaration of a tool.

Examples:

- OpenAI chat-completions function schema
- OpenAI Responses function schema
- OpenAI Responses custom/freeform schema

### Tool call

A tool call is the provider response object that says "invoke this tool with
this payload".

Examples:

- OpenAI chat `tool_calls[*]`
- OpenAI Responses `function_call`
- OpenAI Responses `custom_tool_call`

### Tool result

A tool result is the output produced by the tool after core executes it.

Today, tool results are represented as normal core `role=="tool"` messages.
There is currently no separate tool-result interop adapter registry.

That means result conversion is handled by normal provider or provider-extension
message conversion code, not by `ToolInteropRegistry`.

## Runtime ownership

Tool interop is owned by core for the active request.

Core builds the effective registry from:

1. explicit config contributions
2. provider contributions
3. provider-extension contributions
4. tool contributions
5. built-in defaults

Core also computes the accepted target schema formats for the active provider
stack from `accepted_tool_schema_formats(...)`.

Core passes both pieces of runtime data through request context:

```python
context["tool_interop"]["registry"]
context["tool_interop"]["schema_target_formats"]
```

Provider and provider-extension code should prefer those values instead of
using `DEFAULT_TOOL_INTEROP_REGISTRY`.

`DEFAULT_TOOL_INTEROP_REGISTRY` is fallback-only and should be treated as a
last resort for non-request-bound utility paths.

## End-to-end flow

### 1. Tool plugins emit source schemas

Tool plugins expose schemas via `get_tool_schemas(...)`.

Those schemas may already be in the provider's native format, or they may be in
some other supported source format.

Examples:

- a chat-function schema for OpenAI-compatible providers
- a Responses custom schema for a freeform tool
- a tool-specific custom schema format contributed by the tool plugin

At this stage, schemas are not globally rewritten by core.

Core keeps the original source schemas and records tool descriptors from them.

### 2. Core builds the effective tool interop registry

Before request execution, core composes the active registry and determines the
accepted target schema formats for the current provider and enabled extensions.

This is the source of truth for request-time adaptation.

### 3. Core passes interop runtime data into request context

During `initialize_request(...)` and `finalize(...)`, providers, provider
extensions, and features receive:

```python
context = {
    "core": ...,
    "config": ...,
    "tool_interop": {
        "registry": ...,
        "schema_target_formats": [...],
    },
    ...
}
```

Use this runtime context when adapting schemas or sanitizing calls.

## Where schema conversion happens

Schema conversion belongs in provider or provider-extension request injection.

In practice, this means `initialize_request(...)`.

That code should:

1. read the source schemas from state/config
2. fetch the active registry from `context["tool_interop"]["registry"]`
3. fetch target formats from `context["tool_interop"]["schema_target_formats"]`
4. call `registry.convert_schemas(...)`
5. inject the converted schemas into the request payload

Example pattern:

```python
from agent_core.tool_interop import (
    ToolInteropTarget,
    get_registry_from_context,
    get_schema_target_formats_from_context,
)


def initialize_request(self, native_messages, state, *, context=None):
    request = state.get("request") or {}
    payload = dict(request.get("payload") or {})
    tools = state.get("_tools") or []

    if tools and "tools" not in payload:
        registry = get_registry_from_context(context)
        target_formats = get_schema_target_formats_from_context(context)
        payload["tools"] = registry.convert_schemas(
            [tool for tool in tools if isinstance(tool, dict)],
            target=ToolInteropTarget("openai.chat_completions"),
            target_formats=target_formats,
        )
        payload["tool_choice"] = payload.get("tool_choice", "auto")

    return native_messages, {**state, "request": {**request, "payload": payload}}
```

### Why conversion happens here

This is the point where the active provider stack is known.

Only the provider and enabled extensions know:

- which request wire format is being built
- which schema formats are accepted natively
- which fallback behavior should be used when extensions are absent

Core deliberately does not pre-convert every schema into one canonical wire
format before `initialize_request(...)`.

## End-to-end example: tool schema flow

This example shows a freeform `apply_patch`-style tool whose source schema is a
Responses custom schema, while the active provider stack expects OpenAI chat
function schemas.

### Source schema emitted by the tool plugin

This is what `get_tool_schemas(...)` returns:

```json
{
  "type": "custom",
  "name": "apply_patch",
  "description": "Apply a textual patch to files in the workspace.",
  "format": {
    "type": "grammar",
    "syntax": "lark",
    "definition": "start: /.+/"
  }
}
```

### What core keeps before request injection

Core stores this original schema in the tool descriptor. It does not rewrite it
yet.

Conceptually:

```python
ToolDescriptor(
    plugin_name="apply_patch",
    tool_name="apply_patch",
    schema={
        "type": "custom",
        "name": "apply_patch",
        "description": "Apply a textual patch to files in the workspace.",
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": "start: /.+/",
        },
    },
)
```

### Runtime context passed into request injection

When the request is prepared, core passes the active registry and accepted
target formats through context:

```python
context = {
    "tool_interop": {
        "registry": registry,
        "schema_target_formats": ["openai.chat_completions.function"],
    },
    ...
}
```

### Where conversion happens

Conversion happens in provider or provider-extension `initialize_request(...)`.

Example:

```python
payload["tools"] = registry.convert_schemas(
    [source_schema],
    target=ToolInteropTarget("openai.chat_completions"),
    target_formats=["openai.chat_completions.function"],
)
```

### Converted schema sent to the provider

The converted request payload may look like:

```json
{
  "model": "gpt-4.1",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "apply_patch",
        "description": "Apply a textual patch to files in the workspace.",
        "parameters": {
          "type": "object",
          "properties": {
            "input": {
              "type": "string",
              "description": "Patch text."
            }
          },
          "required": ["input"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### What is stored after request injection

Core does not replace the tool plugin's source schema everywhere with the
converted one.

The important distinction is:

- source schema remains the tool's authored schema
- converted schema is what gets injected into the provider request

### Why this matters

This lets one tool schema source participate in multiple provider stacks:

- chat-function targets
- Responses function targets
- Responses custom/freeform targets

without forcing the tool plugin itself to guess the active wire format.

## Where tool call conversion happens

Tool call conversion happens when provider-native responses are translated back
into core messages or tool-loop inputs.

Typical places:

- provider `from_native_messages(...)`
- provider-extension `from_native_messages(...)`
- provider helpers that build assistant metadata tool-call entries

The active registry inspects or converts provider-native tool call objects so
core can work with:

- tool name
- call id
- payload
- payload kind
- payload format
- payload metadata

Examples:

- Responses `function_call` -> chat-style function tool call
- Responses `custom_tool_call` -> preserved raw-input tool call object

### Accessors vs adapters

Accessors inspect a schema or call and tell core what it means.

Adapters translate one format into another.

Use:

- `registry.inspect_schema(...)` and `registry.inspect_call(...)` when you need
  semantic information from an existing object
- `registry.convert_schemas(...)` and `registry.convert_tool_calls(...)` when
  you need a different wire format

## End-to-end example: tool call flow

This example shows a Responses function call emitted by the provider and then
converted into the core-visible tool call metadata shape.

### Provider-native tool call received from the model

The provider may receive something like:

```json
{
  "type": "function_call",
  "call_id": "call_123",
  "name": "read_file",
  "arguments": "{\"path\":\"README.md\"}"
}
```

### Where the call is interpreted

This happens in provider or provider-extension native-to-core response
conversion, typically inside `from_native_messages(...)` or a helper called by
it.

There are two common paths:

1. inspect the provider-native object and build a core tool-call object
2. convert the provider-native object into another supported wire format first

Example conversion call:

```python
chat_tool_calls = registry.convert_tool_calls(
    [native_item],
    target=ToolInteropTarget("openai.chat_completions"),
)
```

### Converted core-visible tool call

After conversion, the assistant metadata may contain:

```json
{
  "id": "call_123",
  "type": "function",
  "function": {
    "name": "read_file",
    "arguments": "{\"path\":\"README.md\"}"
  }
}
```

### What core extracts from the call

When the tool loop inspects it, the registry exposes normalized semantics:

```python
inspected = registry.inspect_call(tool_call)

assert inspected.call_id == "call_123"
assert inspected.tool_name == "read_file"
assert inspected.payload == {"path": "README.md"}
assert inspected.payload_kind == "object"
```

### What is stored in session/core messages

The tool call is stored in assistant metadata on the core message:

```json
{
  "role": "assistant",
  "content": "",
  "metadata": {
    "tool_calls": [
      {
        "id": "call_123",
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": "{\"path\":\"README.md\"}"
        }
      }
    ]
  }
}
```

### Streaming + sanitization example

If streaming delivered corrupted partial arguments:

```json
{
  "id": "call_123",
  "type": "function",
  "function": {
    "name": "read_file",
    "arguments": "{\"path\":"
  }
}
```

then provider-extension `finalize(...)` sanitizes before the call is retained in
native history:

```python
sanitized = registry.sanitize_tool_call(corrupted_call)
```

Result:

```json
{
  "id": "call_123",
  "type": "function",
  "function": {
    "name": "read_file",
    "arguments": "{}"
  }
}
```

### What is sent on the next request

When native history is replayed into the next provider request, the sanitized
version is what gets sent, not the corrupted fragment.

That is why sanitization must happen before history retention.

## Where sanitization happens

Sanitization is a tool-call concern, not a schema concern.

Provider extensions that accumulate streamed tool calls should sanitize them in
`finalize(...)` before those calls are retained in native history.

That should also use the request-owned registry from context:

```python
from agent_core.tool_interop import get_registry_from_context


def finalize(self, final_messages, native_messages, state, *, context=None):
    partial = state.get("partial")
    if isinstance(partial, dict):
        tool_calls = partial.get("tool_calls")
        if isinstance(tool_calls, list):
            registry = get_registry_from_context(context)
            partial["tool_calls"] = [
                registry.sanitize_tool_call(call)
                for call in tool_calls
                if isinstance(call, dict)
            ]
    return final_messages, native_messages, state
```

This prevents corrupted JSON argument fragments from being stored and replayed
into later API requests.

## Where core tool execution uses interop

Once tool calls are in core, the tool loop and core execution path use the
registry to interpret them in a payload-first way.

Core uses inspected call semantics to decide:

- which tool should handle the call
- what payload should be passed to the tool
- whether the payload is structured data or raw freeform input

This is the layer that lets older dict-argument tools and newer raw-input tools
coexist.

## End-to-end example: tool result flow

This example shows a `read_file` tool returning text content after execution.

### Core executes the tool

After the inspected call is routed, the tool receives normalized payload:

```python
payload = {"path": "README.md"}
result = tool.execute_tool("read_file", payload, state, context=context)
```

Assume the tool returns:

```json
{
  "path": "README.md",
  "content": "# Project title"
}
```

### Tool wrapper formats the result

`format_tool_result(...)` turns that value into the core tool message content.

For example:

```json
{
  "role": "tool",
  "content": "{\"path\":\"README.md\",\"content\":\"# Project title\"}",
  "metadata": {
    "tool_name": "read_file",
    "tool_call_id": "call_123"
  }
}
```

This is the core-side result representation that gets appended to the session.

### Where result conversion happens

There is no `ToolResultAdapter` registry today.

Instead, provider or provider-extension `to_native_messages(...)` converts that
core tool message into the provider-native wire shape.

For an OpenAI-compatible provider, the sent native message may become:

```json
{
  "role": "tool",
  "content": "{\"path\":\"README.md\",\"content\":\"# Project title\"}",
  "tool_call_id": "call_123",
  "_metadata": {
    "tool_name": "read_file"
  }
}
```

For a Responses-style provider, the sent native item may instead become:

```json
{
  "type": "function_call_output",
  "call_id": "call_123",
  "output": "{\"path\":\"README.md\",\"content\":\"# Project title\"}"
}
```

### What is stored

The core session stores the core tool message:

```json
{
  "role": "tool",
  "content": "{\"path\":\"README.md\",\"content\":\"# Project title\"}",
  "metadata": {
    "tool_call_id": "call_123",
    "tool_name": "read_file"
  }
}
```

The provider-native history stores the provider-native result message or item.

### What is sent later

If the next request reuses native history, the provider-native result message is
what gets replayed to the provider.

If native history must be rebuilt from core messages, provider or
provider-extension `to_native_messages(...)` recreates that provider-native
shape from the stored core tool message.

### Why results do not use interop adapters today

Results are part of ordinary message flow after tool execution, not part of the
provider-generated tool-call envelope.

So the conversion points are:

- schema: `initialize_request(...)`
- tool call: native response -> core metadata/tool loop input
- tool result: core tool message -> provider-native message

## General rule for tool results

Tool results do not currently go through a tool-result adapter registry.

Instead, the flow is:

1. core executes the tool
2. the tool returns a result value
3. the tool wrapper formats that result with `format_tool_result(...)`
4. core creates a normal `role=="tool"` message
5. provider or provider-extension `to_native_messages(...)` converts that core
   tool message into provider-native output form

That means:

- schema adapters are for request-time tool declarations
- call adapters/accessors are for provider response tool calls
- tool result conversion lives in provider/provider-extension message mapping

### Why results are different

Results are not provider-generated tool-call objects. They are regular message
traffic produced after tool execution.

So if you need provider-specific result handling, implement it in:

- provider `to_native_messages(...)`
- provider-extension `to_native_messages(...)`
- provider `from_native_messages(...)` if you also need rebuild symmetry

## Practical responsibilities by plugin type

### Tool plugin

Responsible for:

- emitting source schemas
- contributing extra schema/call accessors or adapters when needed
- executing calls based on normalized payload semantics
- formatting tool results

Not responsible for:

- deciding the final provider wire-format target

### Provider extension

Responsible for:

- injecting converted schemas into provider request payloads
- accumulating and sanitizing streamed tool calls
- converting provider-native tool calls into core metadata
- converting core tool-result messages into provider-native message shapes when needed

### Provider

Responsible for:

- provider-level fallback injection when no extension handles tools
- native message conversion for provider-specific result/message formats
- provider-specific helper conversions around request/response payloads

## Common mistakes

### Mistake: convert schemas in tool plugins based on guessed provider shape

Avoid hardcoding one provider target inside a tool plugin unless the tool is
explicitly provider-specific.

Prefer emitting source schemas and letting request-time injection adapt them.

### Mistake: use `DEFAULT_TOOL_INTEROP_REGISTRY` in request-bound code

That bypasses request-specific contributions and can break custom/freeform tools.

Prefer `get_registry_from_context(context)`.

### Mistake: store the registry in config or state

The active registry is runtime-only and may contain non-serializable objects.

Use request context instead.

### Mistake: expect tool results to use schema/call adapters

They do not today.

Use normal provider/provider-extension message conversion hooks for results.

## Summary

The clean mental model is:

- tool plugins emit source schemas
- core builds the request-owned interop registry and accepted target formats
- providers/extensions adapt schemas during `initialize_request(...)`
- providers/extensions inspect or convert tool calls during native-to-core response handling
- providers/extensions sanitize streamed calls during `finalize(...)`
- core executes tools using normalized payload semantics
- tool results return through normal core-message/provider-native message conversion

See also:

- [Tool plugins](tool-plugins.md)
- [Provider extensions (tools + reasoning)](provider-extensions.md)
- [Provider plugins](provider-plugins.md)
# Tool Host Protocol (NDJSON)

This is the cross-package wire contract for out-of-process tool plugins. The
Python Core client and Node.js tool host jointly implement the contract;
neither implementation is authoritative on its own.

Version 1 hosts JavaScript and TypeScript tools through the Node.js
implementation. It remains object-arguments-based even though the in-process
Python tool API also supports raw-text and other payload forms.

## Transport

- A tool host is a subprocess.
- The client writes newline-delimited JSON (NDJSON) to the host's stdin.
- The host writes NDJSON to stdout.
- Each line is one complete protocol record.
- Stdout is reserved for protocol records. Hosts and plugins write logs to
  stderr.
- Values crossing the boundary must be JSON-compatible.

## Message shapes

### Request

```json
{ "v": 1, "id": "uuid", "method": "<method>", "params": { ... } }
```

- `v`: protocol version, currently `1`.
- `id`: non-empty request identifier.
- `method`: RPC method name in snake case.
- `params`: JSON object; an omitted or non-object value is treated as `{}` by
  the Node host.

The Node host rejects unsupported versions, missing identifiers, and missing
method names with a protocol error.

### Response

```json
{ "v": 1, "id": "uuid", "ok": true, "result": { "value": <any>, "state": <object?> } }
{ "v": 1, "id": "uuid", "ok": false, "error": { "type": "Error", "detail": "...", "stack": "..." } }
```

Responses repeat the request `id`. When a request contains `params.state`, the
response includes `result.state`; `init` responses also include it. Node
plugins update state by mutating the supplied object. The Python proxy replaces
its working state with the returned object.

### Streaming events

Tool execution can emit streaming events before the final response:

```json
{ "v": 1, "id": "uuid", "event": { "type": "part", "payload": { ... } } }
```

Node tools produce events through the `emit(event)` callback. The host forwards
object-shaped events with the active request identifier.

The Python proxy maps `event.type == "part"` to:

```json
{ "part": <payload> }
```

Other event types are not emitted as tool-stream chunks by the current Python
proxy.

## Host methods

### Handshake

The host implements `handshake` without calling the plugin:

```json
{ "v": 1, "id": "uuid", "method": "handshake", "params": {} }
```

The response value reports the protocol version, host identity, Node version,
and loaded plugin name/version. The current Python proxy does not require a
handshake before ordinary calls.

### Tool lifecycle and execution

- `get_tool_schemas({"state": <object>}) -> [schema]`
- `execute_tool({"tool_name": "...", "arguments": <object>, "state": <object>}) -> result`

These correspond to `getToolSchemas(state)` and
`executeTool(toolName, arguments, state, emit)` in camel-case Node plugins.
Snake-case plugin methods are also accepted. They are the two required plugin
operations checked by the Node SDK for object exports.

`init({"config": <object>}) -> state` is supported but optional. When the
plugin does not implement it, the host returns `{"config": config}` as state.

The `execute_tool` value uses the Python tool-result shape:

```json
{ "success": true, "result": <any> }
{ "success": false, "error": "..." }
```

### Optional plugin methods

- `get_config_schema() -> object`
- `get_ui_elements() -> [object]`
- `get_tags({"config": <object>, "models": [object]}) -> [string]`
- `required_tags() -> [string]`
- `format_tool_result({"result": <object>, "state": <object>}) -> string | provider-native envelope`
- `format_tool_call_preview({"tool_name": "...", "arguments": <object>, "state": <object>}) -> string`
- `to_display_format({"text": "...", "result": <object>, "state": <object>}) -> object`

`format_tool_result` should normally return a string. A tool host may opt into
structured provider-native output by returning an explicit object with
`type: "provider_native_tool_result"` and a supported `format`, such as
`openai.chat_completions` or `openai.responses`. The Python proxy preserves
only that explicit envelope as structured model-facing content; other objects
fall back to compatibility text.

The host supplies empty-object, empty-list, empty-string, or `null` defaults
for omitted optional methods as appropriate. An unknown method without a
defined default returns a protocol error.

## Implementations and verification

- [Python proxy](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/core/python/agent_core/tool_hosts/node_tool_plugin.py)
- [Node host](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/packages/tool-host-node/host.mjs)
- [Node plugin SDK helper](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/packages/tool-host-node/sdk.mjs)
- [Cross-process tests](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/core/python/tests/test_node_tool_plugins.py)

Changes to versioning, message shapes, method names, state round-tripping,
stream events, or error behavior must be coordinated across both
implementations and this contract.
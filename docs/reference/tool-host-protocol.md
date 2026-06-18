# Tool Host Protocol (NDJSON)

This repo supports out-of-process tool plugins executed by external “tool hosts”. The first implementation is the Node.js tool host used for JavaScript/TypeScript tools.

## Transport

- A tool host is a subprocess.
- The client writes newline-delimited JSON (NDJSON) to the host’s stdin.
- The host writes NDJSON to stdout.
- Stdout is reserved for protocol messages; tool hosts/plugins should write logs to stderr.

## Message shapes

All messages include a protocol version field:

```
{ "v": 1, "id": "uuid", "method": "execute_tool", "params": { ... } }
```

### Request

```
{ "v": 1, "id": "uuid", "method": "<method>", "params": { ... } }
```

- `v`: protocol version (currently `1`).
- `id`: request id (string).
- `method`: RPC method name (snake_case).
- `params`: JSON object.

### Response

```
{ "v": 1, "id": "uuid", "ok": true, "result": { "value": <any>, "state": <object?> } }
{ "v": 1, "id": "uuid", "ok": false, "error": { "type": "Error", "detail": "...", "stack": "..." } }
```

When a request includes `params.state` (or when calling `init`), the host should also include an updated `result.state` so the client can round-trip tool state.

### Streaming events

Tool execution can emit streaming events before the final response:

```
{ "v": 1, "id": "uuid", "event": { "type": "part", "payload": { ... } } }
```

For Node.js tools, events are produced by calling the `emit(event)` callback.

The Python core maps `event.type == "part"` into partial chunks yielded as:

```
{ "part": <payload> }
```

## Required methods (v1)

- `init({"config": <object>}) -> state`
- `get_tool_schemas({"state": <object>}) -> [schema]`
- `execute_tool({"tool_name": "...", "arguments": <object>, "state": <object>}) -> result`

Note: the in-process Python tool API is now payload-first and can execute raw text / freeform tool calls. The v1 host protocol remains object-arguments-based for compatibility with existing Node-hosted tools. If host-side freeform/custom tool execution is added later, this page should be updated as part of that protocol change.

The `execute_tool` result is expected to be the same shape as a Python tool result:

```
{ "success": true, "result": <any> }
{ "success": false, "error": "..." }
```

## Optional methods

- `get_config_schema() -> object`
- `get_ui_elements() -> [object]`
- `get_tags({"config": <object>, "models": [object]}) -> [string]`
- `required_tags() -> [string]`
- `format_tool_result({"result": <object>, "state": <object>}) -> string | provider-native envelope`

`format_tool_result` should normally return a string. A tool host may opt into structured provider-native tool output by returning an explicit JSON object with `type: "provider_native_tool_result"` and a supported `format`, such as `openai.chat_completions` or `openai.responses`. The Python host preserves only that explicit envelope shape as structured model-facing content; ordinary objects are compatibility text.

- `format_tool_call_preview({"tool_name": "...", "arguments": <object>, "state": <object>}) -> string`
- `to_display_format({"text": "...", "result": <object>, "state": <object>}) -> object`

## Node.js implementation

The tool host runner lives at `packages/tool-host-node/host.mjs`. The Python proxy tool plugin lives at `core/python/agent_core/tool_hosts/node_tool_plugin.py`.

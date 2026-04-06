# Node tool plugins

Node tool plugins are out-of-process `ToolPlugin` implementations executed by a
Node.js tool host. They are a good fit when you want to author tools in
JavaScript/TypeScript, reuse npm libraries, or ship a self-contained JS tool
package without adding Python runtime code.

This page is the canonical authoring guide for `node_tool` plugins.

Runtime references (source of truth):

- Loader / plugin source: `core/python/agent_app/plugin_sources/node_tool.py`
- Python proxy plugin: `core/python/agent_core/tool_hosts/node_tool_plugin.py`
- Wire protocol: `docs/reference/tool-host-protocol.md`

Reference implementations:

- Small object export: `plugins/js-echo-tool`
- Class export: `plugins/js-class-tool`
- Multi-tool package: `plugins/js-multi-tools`
- Filesystem tools with streaming toggle: `plugins/js-fs-tools`
- Template: `plugins/template-js-multi-tools`

See also:

- [Tool plugins](tool-plugins.md)
- [Packaging & loading plugins](plugin-packaging-and-loading.md)
- [Testing & validation](testing-and-validation.md)

---

## What Node tools are for

Use a Node tool plugin when:

- your tool logic is already in JavaScript/TypeScript
- you want to use npm packages directly
- you want to ship tools as a Node package with `package.json`
- you are comfortable with a subprocess boundary

Prefer an in-process Python tool when:

- you need the newest payload-first Python tool API directly
- you need custom/freeform raw-text payload handling today
- you want simpler debugging without subprocess/protocol layers

Important current limitation:

- the in-process Python tool API is payload-first
- the v1 Node tool-host protocol still uses object-shaped `arguments`

So Node tools are best suited to classic object/function-style tool calls right
now.

---

## Development workflow

Recommended workflow:

1. start from `plugins/template-js-multi-tools`
2. implement one small tool first
3. test the JS module directly
4. test it through the Python plugin manager / `AgentCore`
5. try it from a real app config using `node_tool`

### Step 0: package layout

Typical layout:

```text
my-js-tools/
  package.json
  src/
    index.ts
    EchoTool.ts
  dist/
    index.js
```

Directory-based `node_tool` packages are discovered from `package.json#agent.tools`.

Minimal example:

```json
{
  "name": "my-js-tools",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
  },
  "agent": {
    "kinds": ["tools"],
    "tools": [
      { "id": "echo", "entry": "dist/index.js", "export": "echoTool" }
    ]
  }
}
```

The `agent.tools` entries are what the loader reads for directory-based tools.

### Step 1: implement one small tool

Minimal object-export example:

```ts
export type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolState = {
  config: Record<string, unknown>;
  calls?: number;
};

export const echoTool = {
  name: "my_js_echo_tool",
  version: "0.1.0",

  init(config: Record<string, unknown>): ToolState {
    return { config, calls: 0 };
  },

  getToolSchemas(_state: ToolState) {
    return [
      {
        type: "function",
        function: {
          name: "echo",
          description: "Echo back the provided value.",
          parameters: {
            type: "object",
            properties: {
              value: { type: "string" }
            },
            required: ["value"]
          }
        }
      }
    ];
  },

  async executeTool(
    toolName: string,
    args: Record<string, unknown>,
    state: ToolState,
    emit: ToolHostEmit
  ) {
    if (toolName !== "echo") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }

    state.calls = (state.calls ?? 0) + 1;
    emit({ type: "part", payload: { message: "working..." } });

    return {
      success: true,
      result: {
        value: String(args?.value ?? ""),
        calls: state.calls
      }
    };
  },

  formatToolResult(result: any) {
    if (!result?.success) {
      return `Error: ${String(result?.error ?? "unknown")}`;
    }
    return `Echo: ${String(result?.result?.value ?? "")}`;
  },

  toDisplayFormat(text: string, result: any) {
    const single = result?.success ? `echo ${String(result?.result?.value ?? "")}` : "echo (error)";
    return { type: "text", content: text, single_line: single };
  }
} as const;

export default echoTool;
```

Class exports are also supported:

- plain object export
- class export instantiated with `new`
- factory function returning an object

See `plugins/js-class-tool` for the class pattern.

### Step 2: build it

Typical command:

```bash
npm install
npm run build
```

If `dist/` is not checked in, the application plugin manager can install
dependencies and run the build in its cache for directory-based tools.

Relevant policy knobs:

```json
{
  "plugin_policy": {
    "node_install_deps": true,
    "node_build": true,
    "node_allow_install_scripts": false
  }
}
```

### Step 3: load it in app config

Supported config forms:

```json
{
  "plugins": [
    { "node_tool": { "path": "./plugins/my-js-tools" } }
  ]
}
```

```json
{
  "plugins": [
    { "node_tool": { "git": "https://github.com/acme/my-js-tools.git", "ref": "v0.1.0" } }
  ]
}
```

```json
{
  "plugins": [
    { "node_tool": { "file": "./tools/my_tool.js", "id": "my_tool" } }
  ]
}
```

String shortcuts:

```json
{
  "plugins": [
    "node:./plugins/my-js-tools",
    "node+git:https://github.com/acme/my-js-tools.git#v0.1.0"
  ]
}
```

---

## Runtime contract

The Python side treats a Node tool package as a proxy `ToolPlugin`. The host
protocol methods are described in more detail in
`docs/reference/tool-host-protocol.md`.

### Required methods

The v1 host expects these methods:

- `init(config) -> state`
- `getToolSchemas(state) -> schema[]`
- `executeTool(toolName, args, state, emit) -> result`

The host protocol method names are snake_case on the wire, but the JS tool
surface uses camelCase in practice.

### Optional methods

Common optional methods:

- `getConfigSchema()`
- `getUiElements()`
- `getTags(config, models)`
- `requiredTags()`
- `formatToolResult(result, state)`
- `formatToolCallPreview(toolName, args, state)`
- `toDisplayFormat(text, result, state)`

### State round-tripping

Node tools do not keep durable state in the Python process. Instead, the host
round-trips `state` through RPC calls.

Example:

```ts
type ToolState = {
  config: Record<string, unknown>;
  calls?: number;
};

init(config: Record<string, unknown>): ToolState {
  return { config, calls: 0 };
}
```

If you mutate state inside `executeTool(...)`, the updated state is sent back to
Python and reused on the next call.

### Streaming

Streaming uses the `emit(...)` callback:

```ts
emit({ type: "part", payload: { message: "starting" } });
emit({ type: "part", payload: { message: "working" } });
```

On the Python side, these become partial tool events.

Important rule:

- `stdout` is reserved for NDJSON protocol messages
- write logs/debug output to `stderr`, not `stdout`

### Tool schemas

Today, Node-hosted tools should expose classic object/function-style schemas.

Example:

```ts
getToolSchemas() {
  return [
    {
      type: "function",
      function: {
        name: "read_file",
        description: "Read a file from disk.",
        parameters: {
          type: "object",
          properties: {
            file_path: { type: "string" }
          },
          required: ["file_path"]
        }
      }
    }
  ];
}
```

Do not assume the Node host currently supports the full in-process Python
payload-first/custom-freeform tool contract.

---

## Exports and discovery

### Directory-based tools

For a package directory, the loader reads `package.json#agent.tools`.

Example:

```json
{
  "agent": {
    "tools": [
      { "id": "echo", "entry": "dist/index.js", "export": "echoTool" },
      { "id": "reverse", "entry": "dist/index.js", "export": "reverseTool" }
    ]
  }
}
```

Notes:

- `entry` is relative to the package root
- `export` is optional; without it, the default export is used
- one package can expose multiple tools

### Single-file tools

Single-file specs skip `package.json#agent.tools` and point directly to a file:

```json
{
  "plugins": [
    {
      "node_tool": {
        "file": "./plugins/js-single-file-tool/UpperTool.ts",
        "id": "js_single_file_tool"
      }
    }
  ]
}
```

### Supported export shapes

The host supports:

- plain object export
- class export
- factory function returning an object

See:

- `plugins/js-echo-tool`
- `plugins/js-class-tool`

---

## Testing Node tools

Recommended layers:

1. JS/TS unit tests for pure logic
2. build test (`npm run build`)
3. Python-side loader/integration tests
4. full app config test

### Quick local loop

```bash
npm install
npm run build
pytest core/python/tests/test_node_tool_plugins.py -q
```

Useful references:

- `core/python/tests/test_node_tool_plugins.py`
- `core/python/tests/fixtures/node_tools/`

### What to test

At minimum:

- schema discovery
- tool execution result shape
- streaming partials
- state round-tripping
- directory vs single-file loading
- class/default/named exports if relevant

If your tool uses config restrictions such as `allowed_paths`, add tests for the
failure path too.

---

## Common pitfalls

- Do not print logs to `stdout`; use `stderr`.
- Keep returned state JSON-serializable.
- Keep tool results JSON-serializable.
- Prefer small, copyable schemas and result objects.
- Remember that host protocol methods are still object-arguments-based.
- If you need raw-text/freeform payloads today, prefer a Python tool.

---

## Reference examples

- `plugins/template-js-multi-tools`
- `plugins/js-echo-tool`
- `plugins/js-class-tool`
- `plugins/js-fs-tools`
- `docs/reference/tool-host-protocol.md`
# js-multi-tools (Node.js / TypeScript)

Example multi-tool Node.js/TypeScript package.

This package demonstrates **named export selection** via `package.json#agent.tools[].export`.

- Plugin ids: `js_echo`, `js_reverse`
- Tool function(s): `echo`, `reverse`

Tool implementations live in:
- `src/EchoTool.ts`
- `src/ReverseTool.ts`

## Build

```bash
esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist
```

## Configure (local path)

Note: these examples assume you are using the application plugin manager (`AgentApplication`) and have set `plugin_cache_dir` plus `plugin_policy.base_dir` so relative paths resolve.

- Verbose form:

```json
{
  "plugins": [
    { "node_tool": { "path": "./plugins/js-multi-tools" } }
  ]
}
```

- String shortcut:

```json
{
  "plugins": [
    "node:./plugins/js-multi-tools"
  ]
}
```

### TypeScript build

```json
{
  "plugin_policy": {
    "node_build": true,
    "node_build_command": "${env:REPO_ROOT}/node_modules/.bin/esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
  }
}
```

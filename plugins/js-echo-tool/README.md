# js-echo-tool (Node.js / TypeScript)

Example JavaScript/TypeScript tool plugin for the AI Agent Platform.

- Plugin id: `js_echo_tool`
- Tool function(s): `echo`

The tool is authored in TypeScript under `src/` and built to `dist/index.js`.

## Build

This repo uses `esbuild` to compile TypeScript:

```bash
esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist
```

## Configure (local path)

Two equivalent ways to reference the plugin from an application config:

Note: these examples assume you are using the application plugin manager (`AgentApplication`) and have set `plugin_cache_dir` plus `plugin_policy.base_dir` so relative paths resolve.

- Verbose form:

```json
{
  "plugins": [
    { "node_tool": { "path": "./plugins/js-echo-tool" } }
  ]
}
```

- String shortcut:

```json
{
  "plugins": [
    "node:./plugins/js-echo-tool"
  ]
}
```

### TypeScript build options

Because `dist/` is gitignored, you typically want the application plugin manager to build in its cache:

```json
{
  "plugin_policy": {
    "node_build": true,
    "node_build_command": "${env:REPO_ROOT}/node_modules/.bin/esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
  }
}
```

Alternatively, you can build the plugin directory yourself (and ensure the plugin cache contains the built `dist/` output).

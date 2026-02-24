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

Because `dist/` is gitignored, the application plugin manager will install dependencies and run the plugin's build script in its cache automatically.

For safety/hardening, you can disable Node installs/builds globally via `plugin_policy` (applies to all Node tools):

```json
{
  "plugin_policy": {
    "node_install_deps": false,
    "node_build": false,
    "node_allow_install_scripts": false
  }
}
```

Alternatively, you can build the plugin directory yourself (and ensure the plugin cache contains the built `dist/` output).

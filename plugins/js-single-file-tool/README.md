# js-single-file-tool (Node.js / TypeScript)

Single-file TypeScript tool example.

- Tool file: `UpperTool.ts`
- Plugin id: defaults to the file stem unless overridden (`UpperTool` -> `UpperTool`).
- Tool function(s): `upper`

This example is intended for quick local development without a full package directory.

## Configure (local file)

Note: these examples assume you are using the application plugin manager (`AgentApplication`) and have set `plugin_cache_dir` plus `plugin_policy.base_dir` so relative paths resolve.

- Verbose form:

```json
{
  "plugins": [
    { "node_tool": { "file": "./plugins/js-single-file-tool/UpperTool.ts", "id": "js_single_file_tool" } }
  ]
}
```

- String shortcut:

```json
{
  "plugins": [
    "node:./plugins/js-single-file-tool/UpperTool.ts"
  ]
}
```

Note: the string shortcut cannot carry an explicit `id`; in that form the plugin id defaults to the file stem.

### TypeScript build

The application plugin manager can compile `.ts` files into a cached `dist/index.js` automatically:

```json
{
  "plugin_policy": {
    "node_build": true,
    "node_build_command": "${env:REPO_ROOT}/node_modules/.bin/esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
  }
}
```

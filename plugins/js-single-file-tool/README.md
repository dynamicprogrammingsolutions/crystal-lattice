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

The application plugin manager compiles `.ts` files by generating a tiny cached package (with `esbuild` in `devDependencies`), then running install + build in that cache.

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

## License

This directory is available under the [Apache License 2.0](../../LICENSE).

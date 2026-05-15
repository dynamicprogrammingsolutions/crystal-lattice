# js-class-tool (Node.js / TypeScript)

Example tool plugin implemented as a **TypeScript class** (instead of exporting a plain object).

- Plugin id: `js_class_tool`
- Tool function(s): `class_echo`

The Node tool host supports exporting either:
- a plain object (existing semantics), or
- a class (the host instantiates it with `new`), or
- a factory function returning an object.

## Build

```bash
esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist
```

## Configure (local path)

```json
{
  "plugins": [
    { "node_tool": { "path": "./plugins/js-class-tool" } }
  ]
}
```

Or with the string shortcut:

```json
{
  "plugins": [
    "node:./plugins/js-class-tool"
  ]
}
```

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

## License

This directory is available under the [Apache License 2.0](../../LICENSE).

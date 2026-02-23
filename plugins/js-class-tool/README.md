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

Because `dist/` is gitignored, enable build-in-cache via policy:

```json
{
  "plugin_policy": {
    "node_build": true,
    "node_build_command": "${env:REPO_ROOT}/node_modules/.bin/esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
  }
}
```

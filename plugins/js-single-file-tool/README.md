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

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

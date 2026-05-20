# js-fs-tools (Node.js / TypeScript)

Example filesystem tools implemented in Node.js/TypeScript.

- Plugin id: `js_fs_tools`
- Tool function(s): `write_file`, `read_file`

The primary implementation lives in `src/FsToolsTool.ts`.

## Security / config

This tool enforces a simple allowlist:

- `allowed_paths`: required list of directories that the tool can access.
- `working_directory`: base directory for relative paths.

It also supports a streaming toggle:

- `node_tool_stream_parts` (default `true`): when false, the tool does not emit tool-host partial events.

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
    { "node_tool": { "path": "./plugins/js-fs-tools" } }
  ]
}
```

- String shortcut:

```json
{
  "plugins": [
    "node:./plugins/js-fs-tools"
  ]
}
```

### TypeScript build

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

## Example config values

```json
{
  "allowed_paths": [".", "./tmp"],
  "working_directory": "./tmp",
  "node_tool_stream_parts": true
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

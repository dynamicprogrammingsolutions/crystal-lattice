# OpenCode Tools Wrapper Package

Create a new Node-based compatibility package that vendors selected OpenCode built-in tools and exposes them through our framework as a `node_tool` plugin, using one universal runtime object plus small per-tool adapter code.

## Task checklist

- [ ] `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/020-grep-tool.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/030-read-tool-and-media.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/040-shell-tool-runtime.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/050-write-and-edit-tools.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/055-web-fetch-and-web-search-tools.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/057-todo-tool.md`
- [ ] `tasks/20260522-opencode-tools-wrapper/060-sync-tests-and-docs.md`

## Goal

Build a new plugin package, likely `plugins/js-opencode-tools`, that:

- uses the framework's `node_tool` plugin source
- vendors selected OpenCode built-in tool code from `../opencode-app`
- exposes those tools through a universal adapter engine
- provides one universal runtime object shared by all wrapped tools
- keeps some runtime services real and some as stable no-ops
- avoids declarative manifest/profile DSLs in favor of normal programmatic adapters

This is no longer a Claude Code compatibility task. The target is an OpenCode-derived tool bundle with a maintainable sync/update path.

## Architecture decisions already made

These decisions came out of the current investigation and should be treated as the starting point unless implementation reveals a blocker:

1. The package should be Node-based, not Python-based.
   - The framework already supports out-of-process Node tool plugins.
   - References:
     - `plugins/docs/node-tool-plugins.md`
     - `core/python/agent_app/plugin_sources/node_tool.py`
     - `core/python/agent_core/tool_hosts/node_tool_plugin.py`

2. The package should vendor upstream tool code instead of reimplementing OpenCode semantics from scratch.
   - Keep copied upstream code as unchanged as practical.
   - Put adaptation pressure on the wrapper/runtime, not on the vendored files.

3. Use one universal runtime object for all wrapped tools.
   - Do not build a declarative runtime-profile system.
   - Some tools will simply not use some runtime services.

4. Do not build a declarative manifest DSL for schema/input/output transformations.
   - Prefer a tiny universal adapter kernel plus small programmatic per-tool adapters.
   - Default behavior should derive the tool name, description, schema, and result formatting from upstream when possible.

5. Start narrow.
   - Initial scope should focus on `glob`, `grep`, `read`, `shell`, `write`, and `edit`.
   - Do not start with `task`, `todo`, MCP-backed tools, or other session-orchestration-heavy tools.

## Important upstream findings

### OpenCode tools do have a shared outer shape

OpenCode built-ins are generic enough at the outer layer that a universal adapter engine is realistic:

- shared tool abstraction:
  - `../opencode-app/packages/opencode/src/tool/tool.ts`
- generic registry treatment:
  - `../opencode-app/packages/opencode/src/tool/registry.ts`

This supports a wrapper that generically:

- loads an upstream tool module
- derives `id`, `description`, and schema
- executes the tool
- normalizes the returned `{ title, output, metadata, attachments }`

### The real difficulty is the runtime dependency graph

Individual OpenCode tools depend on internal services that are not packaged as standalone reusable modules. Examples:

- `glob`:
  - `../opencode-app/packages/opencode/src/tool/glob.ts`
  - needs `InstanceState`, `AppFileSystem`, `Ripgrep`, `Reference`, permission asks, and external-directory checks
- `grep`:
  - `../opencode-app/packages/opencode/src/tool/grep.ts`
  - expands on `glob` with search result shaping and more path/file handling
- `read`:
  - `../opencode-app/packages/opencode/src/tool/read.ts`
  - adds `Instruction`, `LSP`, media/file handling, and richer output shaping
- `shell`:
  - `../opencode-app/packages/opencode/src/tool/shell.ts`
  - is significantly heavier, with parsing, config/runtime flags, shell services, child processes, and permission analysis
- `write`:
  - `../opencode-app/packages/opencode/src/tool/write.ts`
  - adds `Bus`, `Format`, `File`, `FileWatcher`, BOM handling, and diagnostics
- `edit`:
  - `../opencode-app/packages/opencode/src/tool/edit.ts`
  - further expands with locking, diff logic, `Snapshot`, formatting, diagnostics, and file lifecycle events

This means the wrapper should expect incremental runtime growth as more tools are added.

## Proposed package shape

The exact filenames can change, but the intended structure is:

```text
plugins/js-opencode-tools/
  package.json
  tsconfig.json
  README.md
  src/index.ts
  src/runtime/
    createUniversalRuntime.ts
    defaultExecute.ts
    defaultTransformResult.ts
    deriveSchemaFromUpstream.ts
    shims/
      ...
  src/adapters/
    glob.ts
    grep.ts
    read.ts
    shell.ts
    write.ts
    edit.ts
  src/vendor/opencode/
    ...
  script/sync-opencode.ts
  tests/
    ...
```

## Proposed implementation sequence

The subtasks in this task directory intentionally build upward from the smallest realistic wrapped tool:

1. Foundation plus `glob`
2. `grep`
3. `read`
4. `shell`
5. `write` and `edit`
6. `webfetch` and `websearch`
7. `todo`
8. sync script, tests, docs, and hardening

This sequence keeps the runtime expansion incremental instead of trying to solve all OpenCode internal services at once.

## Success criteria

- A new `node_tool` package exists and can be loaded by the framework.
- The package exposes at least one vendored OpenCode-derived tool through the universal adapter engine.
- Later steps add more tools without redesigning the kernel/runtime shape.
- The update path is scriptable enough that future upstream syncs are mechanical first and manual only where wrappers/shims drift.
# 010 - Foundation and First Wrapped Tool (`glob`)

Create the `opencode-tools` Node package skeleton, the universal adapter engine, the universal runtime object, and the first wrapped upstream tool using OpenCode's `glob` implementation.

## Requirements checklist

- [ ] Scaffold a new Node tool plugin package, likely `plugins/js-opencode-tools`, loadable through `node_tool`.
- [ ] Implement the universal adapter engine with code-first hooks only.
- [ ] Implement the first universal runtime object and its initial shims.
- [ ] Vendor the minimum upstream files needed for OpenCode `glob`.
- [ ] Expose a working wrapped `glob` tool through the framework.
- [ ] Add package-level tests proving the plugin loads and the wrapped tool executes.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`

## Why this is first

This subtask should establish the architecture without taking on the most complicated upstream dependencies.

`glob` is the simplest realistic first target among the OpenCode file tools:

- `../opencode-app/packages/opencode/src/tool/glob.ts:1-103`

It still exercises the important architecture pieces:

- upstream vendoring
- shared adapter engine
- shared runtime object
- permission ask plumbing
- path safety checks
- filesystem access
- ripgrep-backed file discovery

## Initial runtime services needed

The first universal runtime object should already exist here, even if many services are simple stubs for now.

At minimum, this step needs working versions of:

- `AppFileSystem`
- `InstanceState`
- permission/tool-context ask bridge
- `Reference`
- `Ripgrep`

The runtime may also include no-op placeholders for services not yet used by `glob`, so later tools can plug into the same object shape without redesign.

## Deliverables

- New package scaffold under `plugins/js-opencode-tools/`
- `src/index.ts` exporting at least the wrapped `glob` tool
- universal adapter engine and runtime construction code
- initial shims sufficient to execute `glob`
- vendored OpenCode `glob` files and their required local wrapper glue
- tests through the node tool host path

## Notes for the implementing agent

- Follow the `node_tool` package conventions documented in `plugins/docs/node-tool-plugins.md`.
- Keep adapter customization programmatic and minimal. Do not introduce a transformation DSL.
- Prefer proving the architecture with one real wrapped upstream tool over overbuilding the runtime in advance.
# 057 - Add Wrapped `todo`

Add OpenCode's `todo` tool on top of the existing universal adapter engine and runtime, making a pragmatic decision about how much task-state persistence or session integration this wrapper actually needs.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `todo`.
- [ ] Add a wrapped `todo` tool using the existing adapter engine.
- [ ] Determine which `todo`-related runtime/state behaviors are essential in this wrapper and which can be simplified.
- [ ] Add tests for the expected `todo` workflows and state transitions supported by the wrapper.
- [ ] Document any intentional divergence from full OpenCode session/task-state behavior.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Why this is separate

`todo` is not primarily a filesystem or process tool. It may introduce lightweight session/state expectations that deserve an isolated design decision instead of being mixed into the file or network tool steps.

This subtask should answer a practical question:

- what is the smallest stable `todo` behavior we can support in this wrapper package without dragging in large OpenCode session-management machinery?

## Deliverables

- vendored OpenCode `todo` files and any required nearby dependencies
- wrapped `todo` tool exported by the package
- any shared runtime/state additions needed for `todo`
- tests covering the supported behavior

## Guardrails

- Favor a pragmatic wrapper-level implementation over chasing full OpenCode session orchestration if the latter would distort the package design.
- Keep the universal runtime shape intact; do not introduce per-tool runtime selection just for `todo`.
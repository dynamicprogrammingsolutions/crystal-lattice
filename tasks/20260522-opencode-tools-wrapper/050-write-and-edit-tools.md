# 050 - Add Wrapped `write` and `edit`

Add OpenCode's `write` and `edit` tools, expanding the universal runtime to support file mutation workflows and their related side services.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `write` and `edit`.
- [ ] Add wrapped `write` and `edit` tools using the existing adapter engine.
- [ ] Expand the universal runtime for file-mutation side services used by these tools.
- [ ] Decide which mutation-adjacent services must be real and which can remain minimal placeholders.
- [ ] Add tests for file creation/editing, permission prompts, diffs/metadata, and basic diagnostic/file-event behavior.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/030-read-tool-and-media.md`

## Upstream references

- `../opencode-app/packages/opencode/src/tool/write.ts:1-104`
- `../opencode-app/packages/opencode/src/tool/edit.ts:1-211`

## Why these tools are grouped

`write` and `edit` both expand the runtime in the same general direction:

- file writes
- diff/patch metadata
- formatting hooks
- diagnostics
- file lifecycle/event-style side effects

Grouping them keeps the runtime growth coherent instead of splitting closely related mutation behavior across too many tiny tasks.

## Expected runtime additions

This step likely needs at least partial implementations for:

- `Bus`
- file event/file watcher hooks
- `Format`
- BOM/file-content helpers
- any metadata plumbing needed to preserve useful edit/write outputs

## Deliverables

- wrapped `write` and `edit` tools exported by the package
- shared runtime expanded for mutation flows
- tests covering both straightforward and failure-path mutations

## Notes

- Be pragmatic about diagnostics and watcher side effects. If full parity is too coupled to OpenCode internals, keep the wrapper behavior stable and document what is intentionally stubbed.
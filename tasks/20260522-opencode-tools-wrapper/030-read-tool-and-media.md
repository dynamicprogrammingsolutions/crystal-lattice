# 030 - Add Wrapped `read` and Media/File Handling

Add OpenCode's `read` implementation, expanding the universal runtime to support the first heavier internal-service dependencies and file attachment behavior.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `read`.
- [ ] Add a wrapped `read` tool using the shared adapter engine.
- [ ] Extend the universal runtime with the additional shared services `read` needs.
- [ ] Decide how media/file attachments from the wrapped tool map to node-tool-host outputs.
- [ ] Add tests for text reads, directories, missing files, binary/media handling, truncation, and path safety.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Upstream reference

- `../opencode-app/packages/opencode/src/tool/read.ts:1-337`
- `../opencode-app/packages/opencode/src/tool/read.txt:1-14`

## Why this is the first runtime-expansion step

`read` is where the universal runtime starts proving whether the OpenCode vendoring strategy is practical beyond simple search tools.

Compared with `glob` and `grep`, `read` adds meaningful dependencies on:

- `Instruction`
- `LSP`
- richer `AppFileSystem` behaviors
- attachment/media handling for images and PDFs
- OpenCode-style text output formatting

## Runtime expectations for this step

The universal runtime should remain a single shared object, but this step likely needs to make more of it real:

- `Instruction`: likely an initial "empty result" implementation
- `LSP`: likely still a no-op or minimal placeholder
- attachment/result normalization: shared wrapper-side logic if needed

## Deliverables

- wrapped `read` tool exported by the package
- runtime expansion needed to support it
- tests for both plain text and media-ish paths

## Notes for the implementing agent

- Keep the upstream `read` logic as intact as practical.
- If node-tool-host result shaping differs from OpenCode's native expectations, put that translation in the wrapper boundary, not inside the vendored file.
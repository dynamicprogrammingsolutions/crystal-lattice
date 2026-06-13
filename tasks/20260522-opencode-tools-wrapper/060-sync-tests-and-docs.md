# 060 - Sync Script, Hardening, Tests, and Docs

Finish the `opencode-tools` package with a maintainable upstream sync flow, better test coverage, and package documentation.

## Requirements checklist

- [ ] Add a script that copies or refreshes the selected vendored OpenCode tool files.
- [ ] Record which upstream files are intentionally vendored and how drift should be handled.
- [ ] Add end-to-end tests through the actual `node_tool` loading path.
- [ ] Add package README/docs describing the architecture and current wrapped tool set.
- [ ] Document intentional divergences, stubs, and update expectations.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Why this is last

The sync script and documentation should reflect the real package shape after several wrapped tools have landed. Doing this too early risks documenting the wrong abstraction.

## Required content to capture

The docs for this package should explicitly preserve these design decisions:

- this is a Node-based `node_tool` plugin package
- it vendors selected OpenCode built-in tools
- it uses one universal runtime object shared by all wrapped tools
- some services are real and some are universal no-ops
- per-tool customization is code-first, not declarative
- updates are expected to be script-assisted but may still require wrapper/shim adjustments

## Suggested verification

- loader-level tests similar to the framework's existing node-tool fixture/integration tests
- package-level smoke tests for the exported tools
- at least one test that catches vendored-import drift or missing shim coverage

## Deliverables

- sync/update script
- final test coverage additions
- package README and any supporting docs
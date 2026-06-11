# 055 - Add Wrapped `webfetch` and `websearch`

Add OpenCode's web retrieval tools, keeping the same universal adapter engine and runtime while expanding only the shared capabilities needed for network-backed tools.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `webfetch` and `websearch`.
- [ ] Add wrapped `webfetch` and `websearch` tools using the existing adapter engine.
- [ ] Extend the universal runtime only where these tools require new shared network/config capabilities.
- [ ] Decide how fetched content, citations, truncation, and failure paths should map through the wrapper boundary.
- [ ] Add tests for successful fetch/search flows, network failures, truncation, and any capability gating.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Why these are grouped

These two tools should expand the wrapper in a similar direction:

- network access
- request/config behavior
- response truncation/content shaping
- search/fetch specific result formatting

Grouping them keeps the runtime growth coherent instead of scattering HTTP/search concerns across multiple small tasks.

## Deliverables

- vendored OpenCode `webfetch` and `websearch` files and their required nearby dependencies
- wrapped `webfetch` and `websearch` tools exported by the package
- any shared runtime additions needed for network-backed tools
- tests covering both normal and failure-path behavior

## Implementation notes

- Keep per-tool customization programmatic and minimal.
- If these tools require capability flags or config-driven enablement, implement that in normal adapter code rather than introducing a manifest DSL.
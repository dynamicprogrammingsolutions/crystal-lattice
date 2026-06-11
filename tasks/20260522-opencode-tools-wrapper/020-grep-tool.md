# 020 - Add Wrapped `grep`

Add OpenCode's `grep` implementation on top of the foundation from `010`, reusing the same universal runtime object and expanding it only where `grep` truly needs more behavior.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `grep`.
- [ ] Add a small per-tool adapter for `grep` on top of the existing kernel.
- [ ] Reuse the universal runtime object from `010` rather than introducing per-tool runtime selection.
- [ ] Expand the runtime only if `grep` reveals missing shared capabilities.
- [ ] Add tests covering file-vs-directory handling, empty results, truncation messaging, and path safety.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Upstream reference

- `../opencode-app/packages/opencode/src/tool/grep.ts:1-156`

## Why this is second

`grep` is a good follow-up to `glob` because it should reuse most of the same runtime surface:

- `InstanceState`
- `AppFileSystem`
- `Ripgrep`
- `Reference`
- permission asks
- external-directory/path checks

Compared with `glob`, it adds:

- result grouping/formatting
- file-target vs directory-target behavior
- line truncation behavior
- partial/inaccessible-path messaging

This makes it a good validation that the universal adapter/kernel shape is actually generic and not just tailored to one tool.

## Deliverables

- vendored OpenCode `grep` files and any closely related dependencies
- a wrapped `grep` tool exported by the package
- tests for the main `grep` behaviors

## Implementation guardrails

- If a helper emerges that is useful for both `glob` and `grep`, extract it into normal shared runtime/helper code.
- Do not add generic abstraction for behavior that still exists in only one tool.
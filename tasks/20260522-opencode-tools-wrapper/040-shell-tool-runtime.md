# 040 - Add Wrapped `shell`

Add OpenCode's `shell` tool and expand the universal runtime for the first major process-heavy tool.

## Requirements checklist

- [ ] Vendor the upstream files needed for OpenCode `shell`.
- [ ] Add a wrapped `shell` tool using the existing adapter engine.
- [ ] Expand the universal runtime with the process/config services `shell` needs.
- [ ] Decide what to do about heavier shell-specific dependencies that are not worth fully reproducing.
- [ ] Add tests for execution, working directory behavior, abort/cancel behavior, and permission metadata.

Parent Task: `tasks/20260522-opencode-tools-wrapper/000-main.md`
Depends On: `tasks/20260522-opencode-tools-wrapper/010-foundation-and-glob-tool.md`

## Upstream reference

- `../opencode-app/packages/opencode/src/tool/shell.ts:1-260`
- additional neighboring modules under `../opencode-app/packages/opencode/src/tool/shell/`

## Why this is a dedicated step

`shell` is significantly more complex than the file/search tools. It introduces process spawning, shell parsing, config/runtime flag concerns, and richer permission analysis.

This step should be isolated so the runtime expansion stays deliberate rather than contaminating the earlier simpler tool work.

## Expected runtime additions

This step likely needs real implementations or thoughtful placeholders for:

- `ChildProcessSpawner`
- shell/process helpers
- config/runtime access used by the vendored shell code
- any shell-specific permission-analysis dependencies

Some services may still remain intentionally dumb if they are not critical to correct tool behavior in this wrapper package.

## Deliverables

- wrapped `shell` tool exported by the package
- universal runtime expanded as needed
- tests proving the wrapped shell path is viable through the node tool host

## Guardrails

- Do not let shell complexity force a redesign of the adapter/kernel/runtime shape unless there is a clear blocker.
- If some shell-specific behavior is too entangled with OpenCode internals, document the intentional divergence and keep moving.
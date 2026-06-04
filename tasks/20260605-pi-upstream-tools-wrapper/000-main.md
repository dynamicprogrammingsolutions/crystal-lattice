# Pi Upstream Tools Wrapper

Create a wrapper-oriented task for reusing Pi upstream tools inside our framework without mirroring Pi behavior by hand. Favor generic adapter/runtime boundaries and only use per-tool shims where the upstream contract does not line up cleanly.

## Requirements checklist

- [ ] Define a practical wrapper strategy for Pi's built-in tools that maximizes reuse of upstream code.
- [ ] Decide which Pi tools belong in the first wrapped bundle and which should stay out of scope.
- [ ] Document the runtime/context assumptions the wrapper must satisfy.

## Goal

Investigate and implement, in a future pass, a reusable tool package derived from upstream Pi tooling.

The target is not full Pi parity. The target is a stable wrapper package that:

- uses upstream Pi tool implementations as much as practical
- relies on one generic wrapper boundary where possible
- adds small per-tool adapters only where schemas, execution context, or outputs differ
- preserves a clean update path when Pi changes upstream

## Key findings from current investigation

### Pi is a strong candidate for generic wrapping

Pi's upstream tool surface is already exposed as reusable factories and tool definitions rather than being tightly embedded in one app runtime.

Relevant files:

- `../pi/packages/coding-agent/src/core/tools/index.ts`
- `../pi/packages/coding-agent/src/core/sdk.ts`
- `../pi/packages/coding-agent/src/core/tools/read.ts`
- `../pi/packages/coding-agent/src/core/tools/bash.ts`
- `../pi/packages/coding-agent/src/core/tools/find.ts`
- `../pi/packages/coding-agent/src/core/tools/grep.ts`
- `../pi/packages/coding-agent/src/core/tools/ls.ts`

### Standard Pi default tools are intentionally minimal

Pi's README says the default built-in model tools are only:

- `read`
- `write`
- `edit`
- `bash`

Reference:

- `../pi/packages/coding-agent/README.md:96`

The SDK repeats the same default assumption:

- built-in default tools are `read`, `bash`, `edit`, `write`
- they can be disabled or allowlisted through session options

Reference:

- `../pi/packages/coding-agent/src/core/sdk.ts:52-69`

### Pi upstream also ships three more built-in non-default tools

Pi's built-in tool module exports the following full built-in name set:

- `read`
- `bash`
- `edit`
- `write`
- `grep`
- `find`
- `ls`

References:

- `../pi/packages/coding-agent/src/core/tools/index.ts:81-84`
- `../pi/packages/coding-agent/src/core/tools/index.ts:138-185`

This matters because Pi is a good source not only for the default four-tool bundle, but also for a slightly broader coding/read-only bundle if we want one.

## Upstream tool shapes worth reusing

Pi tools already have clean per-tool factory boundaries.

Examples:

- `read` tool definition:
  - `../pi/packages/coding-agent/src/core/tools/read.ts:203-220`
- `bash` tool behavior and output streaming/truncation:
  - `../pi/packages/coding-agent/src/core/tools/bash.ts:350-367`
- `find` tool definition:
  - `../pi/packages/coding-agent/src/core/tools/find.ts:109-125`
- `grep` tool definition:
  - `../pi/packages/coding-agent/src/core/tools/grep.ts:123-140`
- `ls` tool definition:
  - `../pi/packages/coding-agent/src/core/tools/ls.ts:95-112`

These factories already expose:

- stable tool names
- descriptions and parameter schemas
- execution functions
- pluggable operations in several tools, which is especially helpful for adapters

## Wrapping implications

### Why Pi is easier than OpenClaw or Hermes

Compared to broader agent apps, Pi's built-in tools are:

- smaller in scope
- cleaner to instantiate directly
- less entangled with messaging, session routing, plugins, or platform services

That makes Pi a strong "foundation" candidate for a generic upstream-derived wrapper package.

### Likely wrapper shape

A future wrapper package could:

- import Pi tool factories directly
- adapt Pi `ToolDefinition` / `AgentTool` outputs into our tool host shape
- inject wrapper-provided operations or context only where necessary

Likely generic adapter concerns:

- schema translation
- tool result normalization
- context injection
- file root / cwd policy
- shell execution policy

Likely per-tool shims:

- `bash` if our runtime needs different process execution or streaming semantics
- `read` if attachment/media behavior or path policies differ
- `write` / `edit` if mutation policy differs

## Recommended initial scope

Good first-phase candidates:

- `read`
- `write`
- `edit`
- `bash`
- optionally `grep`
- optionally `find`
- optionally `ls`

This could be split into:

1. Pi default bundle:
   - `read`, `write`, `edit`, `bash`
2. Pi expanded bundle:
   - plus `grep`, `find`, `ls`

## Open questions for future implementation

- Should the wrapper expose Pi tools under the same names, or translate some names to align with our existing tool vocabulary?
- Should we treat Pi as a pure coding-tool source, or let it become the default foundation for a broader multi-source tool bundle?
- Do we want a wrapper package that directly imports Pi, or one that vendors selected Pi tool modules for tighter update control?
- Which parts of Pi's tool rendering behavior matter versus just execution/schema behavior?

## Suggested next step

Prototype one thin wrapper around Pi `read` and one around Pi `bash`.

Those two tools exercise the most important adapter concerns:

- file access and result shaping
- command execution, streaming, truncation, and policy
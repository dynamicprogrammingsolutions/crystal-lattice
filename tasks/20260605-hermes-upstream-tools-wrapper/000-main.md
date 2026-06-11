# Hermes Upstream Tools Wrapper

Create a wrapper-oriented task for reusing Hermes upstream tools inside our framework without hand-reimplementing a Hermes-like toolset. Favor a generic registry/runtime adapter first, then add per-tool shims only where Hermes assumptions leak through.

## Requirements checklist

- [ ] Define a practical wrapper strategy for Hermes built-in tools that maximizes reuse of upstream code.
- [ ] Decide which Hermes default tools belong in the first wrapped bundle and which are too runtime-coupled for phase 1.
- [ ] Document the Hermes registry, toolset, and runtime assumptions the wrapper must satisfy.

## Goal

Investigate and implement, in a future pass, a reusable tool package derived from upstream Hermes tooling.

The target is not full Hermes parity. The target is a maintainable wrapper package that:

- uses Hermes upstream tool code as much as practical
- adapts Hermes's registry-driven tool contract into our framework
- supports a broadly useful default-like tool bundle
- avoids hand-mirroring Hermes behavior unless a tool absolutely requires it

## Key findings from current investigation

### Hermes is the best candidate for a broad default-style wrapper

Hermes has a first-party tool registry and an explicit toolset model. That makes it a better source than OpenClaw for a broad upstream-derived tool bundle.

Relevant files:

- `../hermes/toolsets.py`
- `../hermes/hermes_cli/tools_config.py`
- `../hermes/tools/registry.py`
- `../hermes/tools/file_tools.py`
- `../hermes/tools/terminal_tool.py`
- `../hermes/tools/web_tools.py`
- `../hermes/tools/todo_tool.py`
- `../hermes/tools/code_execution_tool.py`

### Hermes has a shared default core tool inventory

Hermes defines `_HERMES_CORE_TOOLS` once and reuses it across default platform toolsets.

Reference:

- `../hermes/toolsets.py:29-73`

The shared core list includes:

- `web_search`
- `web_extract`
- `terminal`
- `process`
- `read_file`
- `write_file`
- `patch`
- `search_files`
- `vision_analyze`
- `image_generate`
- `skills_list`
- `skill_view`
- `skill_manage`
- `browser_navigate`
- `browser_snapshot`
- `browser_click`
- `browser_type`
- `browser_scroll`
- `browser_back`
- `browser_press`
- `browser_get_images`
- `browser_vision`
- `browser_console`
- `browser_cdp`
- `browser_dialog`
- `text_to_speech`
- `todo`
- `memory`
- `session_search`
- `clarify`
- `execute_code`
- `delegate_task`
- `cronjob`
- `send_message`
- Home Assistant tools
- Kanban tools
- `computer_use`

### Hermes default platform toolsets point back to the shared core list

Examples:

- `hermes-cli`
- `hermes-cron`
- `hermes-telegram`
- `hermes-discord`
- `hermes-whatsapp`
- `hermes-slack`

References:

- `../hermes/toolsets.py:399-469`

This makes Hermes a good source if we want a "standard broad toolset" rather than a small coding-only bundle.

### Not every Hermes toolset is enabled by default

Hermes keeps several toolsets off by default unless explicitly enabled or auto-enabled by credentials/config.

Default-off set:

- `moa`
- `homeassistant`
- `spotify`
- `discord`
- `discord_admin`
- `video`
- `video_gen`
- `x_search`

References:

- `../hermes/hermes_cli/tools_config.py:99`
- `../hermes/hermes_cli/tools_config.py:1188-1309`

This matters for wrapper design: we should distinguish between:

- standard broad Hermes defaults
- optional Hermes extras

## Upstream tool registry shape

Hermes built-ins self-register through a single registry.

Reference:

- `../hermes/tools/registry.py:57-74`

The registry model uses a shared tool entry shape that includes:

- `name`
- `toolset`
- `schema`
- `handler`
- `check_fn`
- metadata such as descriptions, async flags, and result limits

Reference:

- `../hermes/tools/registry.py:77-106`

Representative registrations:

- file tools:
  - `../hermes/tools/file_tools.py:1530-1533`
- terminal:
  - `../hermes/tools/terminal_tool.py:2589-2597`
- web tools:
  - `../hermes/tools/web_tools.py:1326-1347`
- todo:
  - `../hermes/tools/todo_tool.py:269-277`
- execute-code:
  - `../hermes/tools/code_execution_tool.py:1820-1830`

## Wrapping implications

### Why Hermes fits the generic-wrapper goal well

Hermes already has the "shared outer tool shape" that the OpenCode wrapper task wanted to exploit:

- tool discovery is centralized
- tools share one registration contract
- toolsets are already modeled separately from individual implementations

That means a future wrapper can probably operate at the registry boundary instead of adapting every tool from scratch.

### Likely wrapper shape

A future wrapper package could:

- load or import Hermes built-in tool registrations
- translate Hermes schemas into our host tool definitions
- execute upstream Hermes handlers through a runtime adapter
- normalize Hermes string/JSON tool results into our preferred result shape

Likely generic adapter concerns:

- registry import/discovery
- config and env handling
- `check_fn` availability semantics
- handler invocation and context kwargs
- result normalization

Likely per-tool shims:

- `terminal`
- `process`
- `send_message`
- `execute_code`
- `computer_use`
- browser tools

Those tools are more likely to depend on Hermes-specific runtime or operational context.

## Practical phase-1 scope recommendation

Good first-wave Hermes wrapper candidates:

- `web_search`
- `web_extract`
- `read_file`
- `write_file`
- `patch`
- `search_files`
- `todo`
- `memory`
- `session_search`

Possible second wave:

- browser tools
- `terminal`
- `process`
- `execute_code`
- `delegate_task`
- `text_to_speech`

Likely defer unless there is a strong need:

- `send_message`
- Home Assistant tools
- Kanban tools
- `computer_use`

## Important caveat

Hermes is Python-first and this repo is also Python-first at the framework/runtime level, so language mismatch is not the main concern here.

The real concern is choosing the right wrapper boundary:

- direct in-process wrapping around Hermes registry entries
- a subprocess-hosted adapter if isolation is useful
- or a bridge layer that imports Hermes tools inside a dedicated runtime and exposes them outward

## Related finding

Hermes also ships an MCP server, but it is not the same as the full local default tool catalog. It is mainly a messaging/session bridge.

Reference:

- `../hermes/mcp_serve.py:1-13`
- `../hermes/mcp_serve.py:451-859`

That MCP surface is useful for interoperability, but it should not be confused with "wrap Hermes default tools."

## Open questions for future implementation

- Should the first Hermes wrapper package target only broadly useful local tools, or should it also include selected platform/communication tools?
- Should the wrapper translate Hermes tool names into our existing naming conventions or preserve upstream names?
- Is Python runtime embedding acceptable for this package, or do we need a language-neutral host boundary?
- How much of Hermes toolset enablement logic should be preserved versus flattened into a static wrapped bundle?

## Suggested next step

Prototype a registry-level adapter that can expose a few Hermes built-in tools without hand-rewriting them.

A good minimal slice would be:

- `read_file`
- `search_files`
- `web_search`
- `todo`

That should validate whether Hermes's registry contract is stable enough for a mostly generic wrapper.
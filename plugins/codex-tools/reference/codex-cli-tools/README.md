# Codex CLI tool reference (reconstructed)

This directory documents the built-in tool surface of **Codex CLI** (the open-source `openai/codex` project), with:

- **Concrete JSON tool specs** (as serialized into the OpenAI Responses API `tools` array).
- **Handler notes** describing how the tool works, with emphasis on output formatting, truncation, and error behavior.

The intent is that you can implement compatible tool handlers (not identical, but close enough for prompts and UI integrations).

## What counts as a “tool schema” here

Codex CLI serializes tools into JSON objects with a top-level `type`:

- `{"type":"function", ...}` for normal JSON-schema function tools.
- `{"type":"custom", ...}` for “freeform” tools (Codex uses a `format` block; the backend validates input via a grammar).
- `{"type":"local_shell"}` for the special local-shell tool.
- `{"type":"web_search"}` for the OpenAI web search tool.

The schema files in each tool directory are **exactly the objects Codex CLI constructs** (modulo a couple of places where we split variants for readability, e.g. request-permissions on/off).

## Model-dependent differences

In the stock Codex CLI model catalog (`codex-rs/core/models.json` in the Codex repo), models can differ in:

- Which shell tool shape is preferred (`shell` vs `shell_command` vs `exec_command`).
- Whether `apply_patch` is offered, and whether it is **freeform** (`type: "custom"`) vs **function** (`type: "function"`).
- Whether the model supports `parallel_tool_calls` (request-level flag), which affects concurrency but not the tool schemas.

Each tool directory notes the relevant model/feature variants.

## Shared output formatting and truncation

Many tools return plain text, but shell-like tools and `apply_patch` run through common formatting code:

- Truncation policy is applied to large outputs (byte- or token-budget) and may inject a `Total output lines:` header.
- Shell and apply-patch tool outputs can be returned either as a JSON string (structured) or as a plain, sectioned text format, depending on whether the **freeform** `apply_patch` tool is present in the prompt’s tool list.

See `shared/` for those shared behaviors.

## Cookbook comparison

- `plugins/codex-tools/reference/codex-cli-tools/cookbook-comparison.md` summarizes how the cookbook’s recommended tool schemas relate to Codex CLI’s concrete tool contracts.

## Tool list covered here

- `apply_patch`
- `close_agent`
- `exec_command`
- `grep_files`
- `js_repl`
- `js_repl_reset`
- `list_dir`
- `list_mcp_resource_templates`
- `list_mcp_resources`
- `local_shell`
- `read_file`
- `read_mcp_resource`
- `report_agent_job_result`
- `request_user_input`
- `resume_agent`
- `search_tool_bm25`
- `send_input`
- `shell`
- `shell_command`
- `spawn_agent`
- `spawn_agents_on_csv`
- `test_sync_tool`
- `update_plan`
- `view_image`
- `wait`
- `web_search`
- `write_stdin`

## GPT-5 family: tools actually exposed

Codex CLI decides the tool list from:

- Model metadata (`shell_type`, `apply_patch_tool_type`, `input_modalities`, `experimental_supported_tools`).
- Feature flags (notably `unified_exec`, `apply_patch_freeform`, `apps`, `multi_agent`, `js_repl`, `request_permissions`).
- Session mode (some tools are present but will error unless you are in a specific collaboration mode).

The sections below describe what a GPT-5-family model sees in the **stock Codex CLI** configuration.

### Default on macOS/Linux (stock feature defaults)

On macOS/Linux, `unified_exec` is enabled by default, so Codex exposes PTY-backed exec tooling.

Important mapping note:

- The developer instructions often say “use the shell” in a generic sense.
- In stock macOS/Linux Codex CLI, that maps to calling `exec_command` (and optionally `write_stdin`), because the `unified_exec` feature is enabled by default and it suppresses the `shell`/`shell_command` tool specs.

Tools exposed to GPT-5-family models:

- `exec_command` and `write_stdin` (shell execution)
- `update_plan` (always present)
- `request_user_input` (present, but only usable in Plan mode)
- `view_image` (present; GPT-5 family supports image inputs)
- `apply_patch` for all GPT-5.* models **except** `gpt-5` (in the stock catalog, `gpt-5` has `apply_patch_tool_type = null`)

Tools *not* exposed by default (unless features/config enable them):

- `web_search` (requires web search mode to be enabled)
- `js_repl` / `js_repl_reset` (feature-gated)
- `spawn_agent` / multi-agent tools (feature-gated)
- `search_tool_bm25` and Apps/MCP tool discovery (feature-gated)
- `grep_files`, `read_file`, `list_dir` (require `experimental_supported_tools` per model)

### Default on Windows (stock feature defaults)

On Windows, `unified_exec` is *not* enabled by default, so Codex uses the model’s configured shell tool type.

- `gpt-5` typically exposes `shell`.
- `gpt-5.1`, `gpt-5.2`, and most `gpt-5.*-codex` models expose `shell_command`.

Additionally (same as macOS/Linux):

- `update_plan`, `request_user_input`, `view_image`
- `apply_patch` for models whose `apply_patch_tool_type` is set (all stock GPT-5.* except `gpt-5`).

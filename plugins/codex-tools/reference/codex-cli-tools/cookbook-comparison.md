# Cookbook vs Codex CLI tool surface

This document compares the tool schemas and behavior described in the OpenAI cookbook page:

- `Codex prompting guide (GPT-5)` (URL: `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/`)

to the tool surface implemented by the open-source Codex CLI (`openai/codex`).

Goal: help you build a harness that is compatible with Codex-style GPT-5 prompting while also understanding where Codex CLI’s concrete tool contracts differ.

Notes:

- Codex CLI’s “tools” are the JSON objects serialized into the Responses API `tools` array.
- Codex CLI’s effective tool list depends on platform + feature flags + model metadata. See `README.md` and `models.md`.

## High-level relationship

- The cookbook guide describes a recommended set of tools and schemas for Codex-style GPT-5 usage.
- Codex CLI is a reference implementation, but it is not a 1:1 match to the cookbook examples:
  - Some cookbook tools map to different Codex CLI tools (especially shell execution).
  - Some cookbook tools are built-in upstream tools (notably `apply_patch`) while Codex CLI provides its own.
  - Some tools the cookbook recommends (file operations) are feature/model gated in Codex CLI.

## Tool mapping (cookbook -> Codex CLI)

| Cookbook tool | Codex CLI tool(s) | Relationship |
|---|---|---|
| `shell_command` | `exec_command` + `write_stdin` (macOS/Linux default) | Same intent (run commands), different schema + output shape + interactive semantics |
| `shell_command` | `shell_command` (Windows default / unified_exec disabled) | Closest direct match; schemas still differ (permissions fields, login semantics) |
| `update_plan` | `update_plan` | Same intent; Codex CLI enforces mode gating and emits plan-update events |
| `view_image` | `view_image` | Same intent; Codex CLI checks model `input_modalities` and returns content items |
| `apply_patch` (built-in tool type) | `apply_patch` (Codex-managed tool) | Same intent, very different contract and output type |
| `read_file` / `list_dir` | `read_file` / `list_dir` | Codex CLI implements these, but they may be gated behind `experimental_supported_tools` |
| `rg` / `git` wrappers (recommended) | `grep_files` (partial) + shell tools | Codex CLI has `grep_files`; no dedicated `git_*` tool in the core set |

## Key schema differences

### 1) Shell execution: command string vs PTY sessions

Cookbook examples emphasize a `shell_command` tool where `command` is a string.

Codex CLI can expose shell execution in multiple ways:

- `exec_command` (unified exec)
  - Input: `cmd` string + PTY controls (`tty`, `yield_time_ms`, `max_output_tokens`) and optional `login`.
  - May return output incrementally by yielding early (and then continuing via `write_stdin`).

- `shell_command`
  - Input: `command` string.

- `shell`
  - Input: argv array `command: ["bash", "-lc", "..."]`.

Practical consequence:

- If you are trying to reproduce Codex CLI behavior on macOS/Linux, map “use the shell” from cookbook prompts to `exec_command` by default.

### 2) Permission/escalation fields do not match

Cookbook examples typically model escalation as a boolean + justification (for example `with_escalated_permissions`).

Codex CLI uses a more structured set of fields:

- `sandbox_permissions` (string enum-like values, e.g. `use_default` / `require_escalated`)
- `justification` (only meaningful when requesting escalation)
- `prefix_rule` (suggest a safe prefix for future approvals)
- `additional_permissions` (feature-gated; allows extra read/write paths while staying sandboxed)

If you’re implementing a compatible harness, you’ll likely need an adapter layer between the cookbook’s permission model and Codex CLI’s.

### 3) `apply_patch`: built-in tool vs Codex CLI tool

The cookbook guide uses the Responses API’s built-in patch tool type (`{"type":"apply_patch"}`), which returns structured operations.

Codex CLI does not use that built-in tool type. Instead, it exposes:

- `apply_patch` as a **freeform tool** (`type: "custom"`) with a Lark grammar, or
- `apply_patch` as a JSON-schema function tool with a single `input` string.

Codex CLI then:

- Re-parses + verifies the patch.
- Performs safety assessment (auto-approve, ask user, or reject).
- Executes patch application via a dedicated runtime.
- Returns tool output as text (stdout/stderr summary) and emits patch events for clients.

## Output formatting differences that matter

### Shell-like outputs

Cookbook snippets tend to treat shell output as plain text.

Codex CLI formats exec outputs in two different shapes:

- Structured JSON string with `metadata.exit_code`, `metadata.duration_seconds`, and an `output` string.
- Sectioned freeform text (`Exit code: ...`, `Wall time: ...`, `Output:` ...).

Codex CLI also applies truncation policies and may inject `Total output lines: <N>`.

See `shared/README.md`.

### apply_patch outputs

Cookbook `apply_patch` returns structured file edits.

Codex CLI `apply_patch` typically returns a textual summary and relies on emitted events (and turn diffs) for structured client-side rendering.

## Tools recommended by cookbook but gated in Codex CLI

The cookbook encourages dedicated filesystem tools (`read_file`, `list_dir`, glob search) and dedicated search tooling.

Codex CLI includes some of these, but availability depends on:

- `experimental_supported_tools` in model metadata (stock GPT-5 entries ship with `[]`).
- Whether `apps` / MCP is enabled (for `search_tool_bm25` and connector tools).
- Whether `js_repl` is enabled.
- Whether web search is enabled.

If your goal is “Codex CLI parity”, consider keeping the default surface minimal and gating optional tools the same way.

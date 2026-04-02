# Codex tool parity for `plugins/codex-tools` (Codex-accurate tools)

Bring the **Codex-style tool bundle** in `plugins/codex-tools` to be as close as practical to the open-source **Codex CLI** tool surface and the GPT‑5 Codex prompting guidance.

Scope: this task focuses on the *tool plugins* in `plugins/codex-tools` (Python package `codex_tools`).

Out of scope (for now): changing providers to use the Responses API; major UI work; implementing a full OS-level sandbox.

## Guiding principles

1) **No alias parameters.**
   - Do not support multiple argument names that mean the same thing.
   - Do not accept parameters that aren’t part of the Codex CLI schema.

2) **Prefer exact Codex naming and schemas.**
   - Tool *names* should match Codex CLI (`apply_patch`, `shell_command`, `exec_command`, `write_stdin`, `update_plan`, `view_image`).
   - Schema shapes and field names should match Codex CLI as closely as we can in this platform.

3) **Treat this as new major versions / new plugins.**
   - If we want to keep the current implementations around for comparison, keep them as a **separate plugin bundle** (separate plugin repo/directory + `agent_plugin.json`), not as alternate tool names.
   - Users can switch between bundles to compare performance; the model only ever sees one schema set.

4) **Platform/profile-based tool exposure is OK.**
   - Codex CLI exposes different shell tool names depending on platform/features (macOS/Linux often `exec_command` + `write_stdin`; Windows often `shell_command`).
   - In our framework, tools can hide themselves by returning `[]` from `get_tool_schemas` based on config.

## Why this task exists

Our `plugins/codex-tools` currently provides (current implementation):

- `shell` (bash -lc) via `codex_tools.shell_tool.ShellTool`
- `apply_patch` (*** Begin Patch format) via `codex_tools.apply_patch_tool.ApplyPatchTool`

Codex CLI and the Codex prompting cookbook expect a more specific tool surface (Codex-accurate):

- `apply_patch` with a particular contract (either a built-in tool type in the cookbook, or Codex CLI’s custom/function variants)
- shell tooling that may be exposed as `shell`, `shell_command`, or on macOS/Linux commonly `exec_command` + `write_stdin`
- `update_plan`
- `view_image`

Additionally, Codex CLI’s shell-like tools have stricter conventions around:

- output formatting and truncation (including explicit “total output lines” conventions)
- token-aware output caps
- permission / sandbox request signaling

## Repo investigation (current state)

### Current `plugins/codex-tools`

- Tool entrypoints are declared in `plugins/codex-tools/agent_plugin.json`:
  - `codex_tools.shell_tool.ShellTool`
  - `codex_tools.apply_patch_tool.ApplyPatchTool`

### Current behavior summaries

#### `shell`

- Schema: `{"type":"function","function":{...}}` with args: `command`, `workdir`, `timeout_seconds`, `env`.
- Execution: `subprocess.run(["bash","-lc",command])` or `Popen` for streaming.
- Truncation: line and character limits (`max_output_lines`, `max_output_chars`); not token-aware.
- Output formatting: minimal headers on failures; streaming emits stdout chunks + a `summary` part and then final result dict.

Implementation: `plugins/codex-tools/src/codex_tools/shell_tool.py`.

#### `apply_patch`

- Schema: `patch_text: string`.
- Behavior: parses `*** Begin Patch` format and applies changes with allowed path checks.
- Output formatting: returns “Patch applied successfully” + change list.

Implementation: `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`.

## Codex CLI reference points

We are using two reference sources:

1) The Codex prompting cookbook guide (GPT‑5):
   - `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/`

2) Codex CLI open-source implementation (tool contracts):
   - See `docs/codex-tools/` in this repo (reconstructed from `openai/codex`).

Important: Codex CLI uses **Responses API tool shapes** (top-level `name`), while our default provider stack currently targets **Chat Completions tool shapes** (nested `function`).

For now we will:

- Keep using Chat Completions-style envelopes (`{"type":"function","function":{...}}`) so the current providers continue to work.
- Make *the inner function schema* (name/description/parameters) match Codex CLI.
- Avoid alternate/alias params; if Codex calls it `input`, we call it `input`.

## Goals

1) Replace the current `apply_patch` with a Codex-accurate `apply_patch` (no alternate argument names).
2) Revise shell tooling in multiple rounds:
   - Round 1: schema and argument alignment (keep behavior)
   - Round 2: output formatting + truncation + token-aware limits
   - Round 3: sandboxing hooks + permission/escalation fields (initial, non-breaking)
3) Add Codex CLI-style tools as separate tool plugins:
   - `update_plan`
   - `view_image`
4) Add alternative shell tools:
   - `exec_command`
   - `write_stdin`

5) Keep the current tool bundle available as a **separate plugin bundle** so users can switch between “old” and “Codex-accurate” implementations for benchmarking.

## Task checklist

- [x] `tasks/20260225-codex-tools-parity/010-apply-patch-schema.md`
- [ ] `tasks/20260225-codex-tools-parity/011-shell-selection-parity.md`
- [ ] `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`
- [ ] `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`
- [ ] `tasks/20260225-codex-tools-parity/020-bash-tool-round-1-schema.md`
- [ ] `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`
- [ ] `tasks/20260225-codex-tools-parity/035-gpt-5-4-tool-selection-workdir-and-developer-message.md`
- [ ] `tasks/20260225-codex-tools-parity/040-bash-tool-round-3-sandboxing.md`
- [ ] `tasks/20260225-codex-tools-parity/050-update-plan-tool.md`
- [ ] `tasks/20260225-codex-tools-parity/060-view-image-tool.md`
- [ ] `tasks/20260225-codex-tools-parity/070-exec-command-and-write-stdin-tools.md`

## Deliverables

- Updated `plugins/codex-tools` Python package with the revised/added tools.
- Updated `plugins/codex-tools/agent_plugin.json` to include new tool entrypoints.
- Tests updated/added under `plugins/codex-tools/tests/`.
- Docs updates in `plugins/codex-tools/README.md` describing the supported tool surface.

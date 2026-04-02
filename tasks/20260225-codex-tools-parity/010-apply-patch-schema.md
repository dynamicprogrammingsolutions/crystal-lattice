# 010 — Apply patch parity investigation and task split

Investigate upstream Codex CLI `apply_patch` behavior, compare it with our implementation, and preserve the findings that drive the follow-up work.

## Requirements checklist

- [x] Investigate the upstream Codex CLI `apply_patch` tool definitions and model gating.
- [x] Compare the upstream behavior with `plugins/codex-tools` and our current tool interop path.
- [x] Split implementation work into dedicated follow-up subtasks instead of a standalone schema-only cleanup.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`

## Scope

This task is now a research and handoff task, not an implementation task.

Do in this task:

- Record what Codex CLI currently does for `apply_patch`.
- Record where our implementation diverges.
- Point follow-up implementation work at the right source-of-truth behavior.

Do not do in this task:

- Ship the `patch_text` -> `input` rename by itself.
- Implement freeform/custom tool support.
- Implement the final `apply_patch` parity change.

The actual implementation work is now split into:

- `tasks/20260225-codex-tools-parity/011-shell-selection-parity.md`
- `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`
- `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`

## Findings to preserve

### 1) Upstream Codex CLI exposes two `apply_patch` tool shapes

Current upstream Codex CLI defines:

- a freeform/custom `apply_patch` tool intended for GPT-5 models
- a JSON/function `apply_patch` fallback that takes a single `input` string and is explicitly commented as a `gpt-oss`-style fallback

References:

- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:288-299`
- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:302-389`

Important details from upstream:

- Freeform description: "Use the `apply_patch` tool to edit files. This is a FREEFORM tool, so do not wrap the patch in JSON."
- Function fallback parameter name: `input`
- Function fallback schema uses `required: ["input"]`
- Function fallback schema uses `additional_properties: false`
- Function fallback schema sets `strict: false`

### 2) Upstream model metadata makes freeform the normal GPT-5 path

In current upstream `models.json`, stock GPT-5-family Codex configs mostly use freeform `apply_patch`, not the JSON fallback.

Examples:

- `gpt-5.4`: `apply_patch_tool_type = "freeform"`, `shell_type = "shell_command"`
- `gpt-5.2`: `apply_patch_tool_type = "freeform"`, `shell_type = "shell_command"`
- `gpt-5.1`: `apply_patch_tool_type = "freeform"`, `shell_type = "shell_command"`
- `gpt-5`: `apply_patch_tool_type = null`, `shell_type = "default"`

References:

- `../codex/codex-rs/core/models.json:81-117`
- `../codex/codex-rs/core/models.json:359-395`
- `../codex/codex-rs/core/models.json:427-459`
- `../codex/codex-rs/core/models.json:555-591`

Tool registration is driven directly by `config.apply_patch_tool_type`:

- `../codex/codex-rs/core/src/tools/spec.rs:1914-1923`

### 3) Our current `apply_patch` tool only matches neither upstream default nor upstream fallback exactly

Our current implementation is a chat-completions function tool with a `patch_text` field wired through schema, preview, execution, and display payloads.

References:

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:501-523`
- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:535-582`
- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:613-694`

Current mismatch summary:

- Upstream JSON fallback expects `input`, not `patch_text`
- Upstream default GPT-5 path is freeform/custom, not function JSON
- Our current schema does not set `additionalProperties: false`

### 4) Core interop exists, but end-to-end source-format freedom is not there yet

The repo now has a tool interop registry with accessors and adapters, and Responses providers/extensions already use it for some conversions.

References:

- `core/python/agent_core/tool_interop.py:81-139`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:277-304`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:220-228`

But the generic tool execution and preview paths still hard-code OpenAI chat-completions function accessors:

- `core/python/agent_core/core.py:2748-2809`
- `core/python/agent_app/tool_loop.py:96-129`
- `core/python/agent_app/tool_loop.py:140-169`

And the `ToolPlugin` protocol still assumes structured dict arguments rather than raw freeform input:

- `core/python/agent_core/types.py:1119-1242`

This means non-chat or raw-input tools are not yet a complete end-to-end path in the generic core tool loop.

## Practical conclusion

The earlier idea of doing a standalone `patch_text` -> `input` rename is too narrow.

The real work breaks into three concerns:

1. model-aware shell/tool exposure parity
2. a core prerequisite for freeform/custom tool support
3. the final `apply_patch` parity implementation once the prerequisite exists

That is why this task now serves as a completed investigation and handoff, while implementation continues in `011`, `012`, and `013`.

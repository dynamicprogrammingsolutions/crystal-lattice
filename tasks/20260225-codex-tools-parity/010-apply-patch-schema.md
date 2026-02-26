# 010 — ApplyPatchTool: schema parity (no aliases)

## Problem

`plugins/codex-tools` already has a mostly working `apply_patch` implementation, but its **tool schema** differs from Codex CLI:

- Current plugin expects `{ "patch_text": "..." }`.
- Codex CLI’s function-style schema uses `{ "input": "..." }` (and the freeform/custom tool uses raw tool input).

We will **not** add aliases (`patch_text` vs `input`). The Codex-accurate tool will use **only** `input`.

This mismatch can cause:

- Prompt/harness incompatibility when reusing Codex‑style developer messages.
- Extra adapter logic in agents that assume Codex CLI conventions.

## References

- Current implementation: `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
- Codex CLI reconstructed schemas:
  - `docs/codex-tools/apply_patch/schema.function.json`
  - `docs/codex-tools/apply_patch/schema.freeform.json`

## Plan

### A) Replace the current `apply_patch` tool schema with Codex CLI

1) Update `get_tool_schemas` to match Codex CLI’s function-style schema as closely as possible:
   - single parameter: `input: string`
   - `required: ["input"]`
   - `additionalProperties: false`

2) Update `execute_tool` to accept only:
   - `arguments["input"]` as the patch text.

3) Update `format_tool_call_preview` to read from `input`.

### B) Keep the previous tool implementation as a separate plugin bundle (optional)

If we want to compare the current `apply_patch` implementation vs the Codex-accurate one:

- Keep the current tool bundle as a **separate plugin bundle** (separate directory/repo + `agent_plugin.json`).
- That bundle can continue to expose an `apply_patch` tool with the old schema.
- Users can switch which bundle is loaded to benchmark behavior.

Important:

- Do **not** ship both bundles at the same time in a single config, because tool names would collide and the model should only see one schema.

Additional schema/description alignment:

- Consider exposing `strict: false` (if the provider supports it) to align with Codex CLI.
- Update the tool description to match the Codex CLI wording where helpful:
   - emphasize relative paths only
   - emphasize the *** Begin Patch envelope format

### C) Add fixture tests

1) Add tests that call `apply_patch` with `input`.
2) If we keep the old bundle around, its tests should live alongside that bundle.

## Acceptance criteria

- The model can call `apply_patch` using `{input: "*** Begin Patch ..."}`.
- No `patch_text` alias exists on the Codex-accurate tool.
- Unit tests cover the new schema.

## Open questions / follow-ups

- Do we also want to support Codex CLI’s **freeform/custom** `apply_patch` tool shape in this repo? That likely requires provider/tooling changes (because our OpenAI-compatible provider expects `type:function`). Defer unless needed.

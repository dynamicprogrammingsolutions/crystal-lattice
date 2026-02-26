# 050 — Add `update_plan` tool plugin

## Problem

Codex CLI exposes an `update_plan` tool that lets the model maintain a structured task plan (pending / in_progress / completed). Our platform currently has no equivalent tool.

We want a Codex-accurate implementation so Codex-style prompts can be reused.

## References

- Codex CLI reconstructed schema: `docs/codex-tools/update_plan/schema.json`
- Codex prompting cookbook mentions `update_plan` as a recommended tool.

## Plan

### A) Implement `UpdatePlanTool` in `plugins/codex-tools`

1) Add a new tool plugin class:
   - File: `plugins/codex-tools/src/codex_tools/update_plan_tool.py`
   - Class: `UpdatePlanTool` (tool name: `update_plan`)

2) `get_tool_schemas` should mirror the Codex CLI schema:
   - `explanation?: string`
   - `plan: [{ step: string, status: "pending" | "in_progress" | "completed" }]`
   - enforce `additionalProperties: false` where applicable

3) `execute_tool` behavior (v1):
   - validate shape
   - enforce: at most one `in_progress`
   - return a result dict including the normalized plan

### B) Decide where the plan lives

We have two viable v1 approaches:

- **Option A (stateless tool)**: tool returns the plan but does not persist it. The model keeps the plan in context via the tool output message.
- **Option B (persist to session metadata)**: store the latest plan under a session metadata key.

Recommendation for v1: **Option A** (stateless), unless a downstream UI explicitly needs persistence.

### C) Formatting + display

1) `format_tool_result` should be concise and deterministic:
   - A short acknowledgment + a bullet list of steps and statuses.
2) `to_display_format` can include a structured payload if the UI supports it (otherwise plain text).

### D) Wire into plugin manifest

- Add `codex_tools.update_plan_tool.UpdatePlanTool` to `plugins/codex-tools/agent_plugin.json`.

### E) Tests

- Unit test: happy path with one `in_progress`.
- Unit test: reject two `in_progress`.
- Unit test: schema presence.

## Acceptance criteria

- The tool can be called with the Codex CLI schema.
- Validation rules match Codex expectations.
- The formatted tool output is stable and readable.

## Open questions / follow-ups

- If we later add a “Plan mode” to the app, we may want to persist plan state and render it in a dedicated UI.

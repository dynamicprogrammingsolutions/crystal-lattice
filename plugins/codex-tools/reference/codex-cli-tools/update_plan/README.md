# `update_plan`

`update_plan` is a todo/checklist tool used to surface a structured plan to clients.

## Handler behavior (implementation notes)

- The handler emits a plan-update event for clients to render.
- The tool returns a fixed text output: `Plan updated`.
- The handler rejects calls when Codex is in “Plan mode” (this is distinct from the todo/checklist tool; it prevents recursion/feedback loops).

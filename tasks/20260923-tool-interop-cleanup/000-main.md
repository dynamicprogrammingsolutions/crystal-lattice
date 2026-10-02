# Tool interop implementation cleanup

Short description: A task directory for reviewing and cleaning up parts of the tool interop implementation introduced in commit `dceca8dfe` ("Introduce additive tool interop registry and payload-first tool API") and related work. Subtasks address specific cleanup targets identified during review.

Scope: tool interop layer (`core/python/agent_core/tool_interop.py`), the `AgentCore` helpers added around it, the `response_finalize` lifecycle, and plugin placements that the review concludes were over-engineered or misplaced. New subtasks are added as further review identifies targets.

## Requirements checklist

- [ ] Provide a task directory that can hold related subtasks for tool interop cleanup as further review identifies them.
- [ ] First subtask replaces the `ToolCallPreviewFeature` plugin + `response_finalize` lifecycle with a tag-gated provider extension (see `010-replace-tool-call-preview-feature-with-extension.md`).

## Subtasks

- [ ] [tasks/20260923-tool-interop-cleanup/010-replace-tool-call-preview-feature-with-extension.md](tasks/20260923-tool-interop-cleanup/010-replace-tool-call-preview-feature-with-extension.md)
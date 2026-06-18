# Qwen Agent Notes

These notes are for further research or future automation work, not for direct copy-paste into final system instructions.

## Key upstream files

- `qwen-code/packages/core/src/core/prompts.ts`
- `qwen-code/packages/core/src/core/prompts.test.ts`

## What upstream actually does

1. Builds most of the default prompt as one large base string.
2. Appends sandbox guidance, git guidance, model-sensitive tool-call examples, and user-memory text.
3. Allows env-var-driven override and write-back behavior for `system.md`.
4. Switches example style based on model-name heuristics or explicit environment variables.

## Important fidelity gaps

1. The textual tool-call examples are not always appropriate when the provider already exposes native structured tool calls.
2. Absolute-path instructions depend on the actual Qwen-compatible tool surface being configured.
3. The long new-application section may conflict with existing project design systems and frontend conventions in this repo.

## Good source anchors for later work

- `getCoreSystemPrompt`
- `getToolCallExamples`
- `generalToolCallExamples`
- `qwenCoderToolCallExamples`
- `qwenVlToolCallExamples`
- `getPlanModeSystemReminder`
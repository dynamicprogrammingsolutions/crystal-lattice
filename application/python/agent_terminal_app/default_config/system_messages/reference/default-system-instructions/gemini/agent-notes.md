# Gemini Agent Notes

These notes are for further research or future automation work, not for direct copy-paste into final system instructions.

## Key upstream files

- `gemini-cli/packages/core/src/core/prompts.ts`
- `gemini-cli/packages/core/src/prompts/promptProvider.ts`
- `gemini-cli/packages/core/src/prompts/snippets.ts`
- `gemini-cli/packages/core/src/prompts/snippets.legacy.ts`
- `gemini-cli/packages/core/src/core/__snapshots__/prompts.test.ts.snap`

## What upstream actually does

1. Builds the prompt compositionally rather than from a single prompt blob.
2. Switches between modern and legacy snippet sets.
3. Selects between primary workflow and plan-mode workflow based on approval mode.
4. Injects subagent, skill, hook-context, sandbox, git, and local-context sections conditionally.
5. Appends contextual instruction content after the main body through `renderFinalShell`.

## Important fidelity gaps

1. `GEMINI.md` discovery and hierarchical precedence are host behaviors, not static prompt text.
2. Plan mode depends on real tool and policy support.
3. Skill activation and hook-context sections should only be rendered when the host supports them.
4. Tool names in upstream text should be reconciled with the actual enabled tool set in this repo.

## Good source anchors for later work

- `renderPreamble`
- `renderCoreMandates`
- `renderPrimaryWorkflows`
- `renderPlanningWorkflow`
- `renderOperationalGuidelines`
- `renderSandbox`
- `renderGitRepo`
- `renderUserMemory`
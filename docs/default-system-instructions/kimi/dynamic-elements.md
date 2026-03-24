# Kimi Dynamic Elements

## `{{INTRODUCTION}}`

- Replace with the contents of `static-introduction.md`.
- Optionally replace `{{ROLE_ADDITIONAL}}` with a short personality or role override from `agent.yaml`.
- Omit `{{ROLE_ADDITIONAL}}` entirely when no override is configured.

Example:

- `{{ROLE_ADDITIONAL}} = You specialize in careful Python maintenance work.`

## `{{PROMPT_AND_TOOL_USE}}`

- Replace with the contents of `static-prompt-and-tool-use.md`.
- Keep the parallel tool call instruction.
- Rewrite or omit the `<system-reminder>` paragraph when the host does not inject authoritative reminder tags.

Example:

- Preserve the `HIGHLY RECOMMENDED` parallel-tool guidance even when the exact tool inventory differs.

## `{{GENERAL_GUIDELINES_FOR_CODING}}`

- Replace with the contents of `static-general-guidelines-for-coding.md`.
- Keep the minimal-change and git-mutation guidance as-is unless the host has stronger local policies.

Example:

- Keep `Make MINIMAL changes to achieve the goal.` in the final prompt.

## `{{GENERAL_GUIDELINES_FOR_RESEARCH_AND_DATA_PROCESSING}}`

- Replace with the contents of `static-general-guidelines-for-research-and-data-processing.md`.
- Keep the isolated-environment guidance when package installation is possible.

Example:

- Keep the instruction to use an isolated environment for third-party packages.

## `{{WORKING_ENVIRONMENT_SECTION}}`

- Start from `working-environment-section.md`.
- Replace `${KIMI_NOW}` with the current ISO datetime.
- Replace `${KIMI_WORK_DIR}` with the current workspace root.
- Replace `${KIMI_WORK_DIR_LS}` with a directory listing captured at prompt-render time.
- Replace `${KIMI_ADDITIONAL_DIRS_BLOCK}` with either an additional-directories block or an empty string.
- Rewrite the operating-system subsection if sandbox status is unknown or the host enforces stricter path restrictions.

Examples:

- `${KIMI_NOW} = 2026-03-20T14:32:11+01:00`
- `${KIMI_WORK_DIR} = /Users/ferenci84/Dev/Mine/ai-agent-platform`
- `${KIMI_ADDITIONAL_DIRS_BLOCK} = ""`

## `{{PROJECT_INFORMATION_SECTION}}`

- Start from `project-information-section.md`.
- Replace `${KIMI_WORK_DIR}` with the workspace root.
- Replace `${KIMI_AGENTS_MD}` with the contents of the root `AGENTS.md`, or an empty string if none exists.
- If the host already injects `AGENTS.md` or similar context elsewhere, rewrite this section to avoid duplication.

Example:

- `${KIMI_AGENTS_MD}` may be the full project-level `AGENTS.md` contents.

## `{{SKILLS_SECTION}}`

- Start from `skills-section.md`.
- Replace `${KIMI_SKILLS}` with a formatted inventory of available skills.
- Omit the entire section when the host has no skill system.

Example:

- `${KIMI_SKILLS} = No skills found.`

## `{{ULTIMATE_REMINDERS}}`

- Replace with the contents of `ultimate-reminders.md`.

Example:

- Keep the final block together as the closing prompt section.
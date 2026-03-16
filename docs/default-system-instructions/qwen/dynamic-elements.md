# Qwen Dynamic Elements

## `{{INTRODUCTION_AND_CORE_MANDATES}}`

- Replace with the contents of `static-introduction-and-core-mandates.md`.

Example:

Start the final prompt with the full identity line and `# Core Mandates` block from `static-introduction-and-core-mandates.md`.

## `{{TASK_MANAGEMENT}}`

- Replace with the contents of `static-task-management.md`.
- If the host has no todo tool, rewrite `todo-writing tool` to whatever planning mechanism is actually available.

Example:

`You have access to a todo-writing tool to help you manage and plan tasks.`

## `{{PRIMARY_WORKFLOWS}}`

- Replace with the contents of `static-primary-workflows.md`.

Example:

Paste the full software-engineering workflow block directly after task management.

## `{{OPERATIONAL_GUIDELINES}}`

- Replace with the contents of `static-operational-guidelines.md`.

Example:

Keep the absolute-path and explain-before-modifying-shell-command guidance together in one block.

## `{{SANDBOX_SECTION}}`

- Omit when sandbox state is unknown or not relevant.
- Otherwise use `sandbox-section.md` and replace `{{SANDBOX_HEADING}}` and `{{SANDBOX_BODY}}`.

Examples:

- `{{SANDBOX_HEADING}} = Sandbox`
- `{{SANDBOX_BODY}} = You are running in a sandbox container with limited access to files outside the project directory or system temp directory.`

## `{{GIT_SECTION}}`

- Omit when not in a git repository.
- Otherwise use `git-section.md` as-is.

Example:

Include the git section when the working tree is tracked and normal git inspection commands are available.

## `{{MODEL_TOOL_CALL_EXAMPLES}}`

- Choose one example style based on the target provider and whether textual examples are helpful.
- Use `model-tool-call-examples.md` and replace `{{TOOL_CALL_EXAMPLE_STYLE}}`.
- In many providers in this repo, it is better to omit this entire section.

Examples:

- `{{TOOL_CALL_EXAMPLE_STYLE}} = general bracketed examples`
- `{{TOOL_CALL_EXAMPLE_STYLE}} = qwen-coder xml-style examples`
- `{{TOOL_CALL_EXAMPLE_STYLE}} = omitted because the provider already exposes native structured tool calls`

## `{{USER_MEMORY_SUFFIX}}`

- Omit when there is no appended memory or local instruction payload.
- Otherwise use `user-memory-suffix.md` and replace `{{USER_MEMORY_TEXT}}`.

Example:

```md
---

Prefer `pnpm` over `npm` in this workspace.
Run `pnpm lint` and `pnpm test` after JavaScript changes.
```

## Absolute path behavior

- Qwen's default prompt strongly assumes absolute-path file tools.
- If the configured tool family supports relative paths instead, rewrite those path rules instead of copying them literally.

Example:

- Keep: `Always use absolute paths when referring to files with tools.`
- Rewrite when needed: `Resolve user-provided relative paths against the workspace root before reading or writing files.`
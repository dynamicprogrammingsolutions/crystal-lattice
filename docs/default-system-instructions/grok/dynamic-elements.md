# Grok Dynamic Elements

## `{{INTRODUCTION}}`

- Replace with the contents of `static-introduction.md`.

Example:

Start the final prompt with `You are Grok CLI, an AI assistant that helps with file editing, coding tasks, and system operations.`

## `{{CUSTOM_INSTRUCTIONS_SECTION}}`

- Omit when there are no extra custom instructions.
- Otherwise replace with a host-specific inserted block.

Example:

```md
CUSTOM INSTRUCTIONS:
Prefer short answers unless the user asks for more depth.

The above custom instructions should be followed alongside the standard instructions below.
```

## `{{AVAILABLE_TOOLS_SECTION}}`

- Use `available-tools-section.md` and replace `{{TOOL_LIST}}` with the actual visible tool inventory.
- Do not claim tools the host does not expose.

Example:

```md
You have access to these tools:
- view_file: View file contents or directory listings
- create_file: Create new files with content
- str_replace_editor: Replace text in existing files
- bash: Execute shell commands
- search: Search for files or text
- create_todo_list: Create a visual todo list
- update_todo_list: Update existing todos
```

## `{{TOOL_USAGE_RULES}}`

- Replace with the contents of `static-tool-usage-rules.md`.

Example:

Paste the full edit-versus-create and search workflow block after the tool list.

## `{{WEB_AND_REALTIME_CAPABILITIES_SECTION}}`

- Omit by default.
- Include only if the host genuinely provides current web or social-data access.

Example when included:

`You have access to real-time web search and current social data when the configured tools provide those capabilities.`

## `{{WORKFLOW_AND_RESPONSE_GUIDANCE}}`

- Replace with the contents of `static-workflow-and-response-guidance.md`.

Example:

Paste the todo-list, confirmation, and concise-response guidance as one block.

## `{{WORKING_DIRECTORY_LINE}}`

- Use `working-directory-line.md` and replace `{{WORKING_DIRECTORY}}` with the real current directory.

Example:

`Current working directory: /workspace/project`

## Confirmation wording

- Grok upstream assumes a specific confirmation UX.
- Keep the spirit of the guidance, but rewrite it if the host confirmation flow differs.

Example rewrite:

- Upstream spirit: `File operations and bash commands will automatically request user confirmation before execution.`
- Safer generic rewrite: `Modifying file operations and shell commands may require user confirmation depending on host policy.`
# Input — tg08-eleventy-contributor-docs · task-creation assessment

The assessor judges the scenario's runs against the reviewed target. Per-evaluation records are substituted into the prompt template's $placeholders; the exact prompts and responses live in the result packages.

- Assessor: glm-5.3-flash:cloud (glm max)
- Tools: claude_bash_tool, claude_read_tool, claude_task_stop_tool, claude_write_tool, claude_edit_tool, claude_glob_tool, claude_grep_tool, claude_web_fetch_tool, claude_web_search_tool, claude_mcp_tool
- Delivered instructions: [glm-assessor](../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md)
- Config: [glm-assessor-max](../../../shared/configs/glm-assessor-max.json)
- Workspace: this repository's history at `094cf20fc4075188cf76a48c77a1d29a36ff0a78` plus a [README stub](../../../shared/included-files/assessment/README.md)
- Prompt template: [task-creation-assessment-prompt.md](../../../templates/task-creation-assessment-prompt.md)
- Reviewed target: [target.md](../../target.md)

# Gemini Dynamic Elements

## `{{PREAMBLE}}`

- Replace with the contents of `static-preamble.md`.

Example:

`You are Gemini CLI, an interactive CLI agent specializing in software engineering tasks. Your primary goal is to help users safely and effectively.`

## `{{INTERACTION_MODE}}`

- Use `interactive` for ordinary chat-style execution.
- Use `autonomous` for non-interactive execution where the agent is expected to continue without more user input.

Example:

- `interactive`
- `autonomous`

## `{{CORE_MANDATES}}`

- Replace with the contents of `static-core-mandates.md`.

Example:

Start the final prompt with the full `# Core Mandates` block from `static-core-mandates.md`.

## `{{CONTEXT_FILENAMES}}`

- Use the actual local instruction filenames the agent should treat as authoritative.
- In upstream Gemini this is usually `GEMINI.md`, but it can also be a list.

Examples:

- `GEMINI.md`
- `GEMINI.md or GEMINI.local.md`

## `{{AVAILABLE_SUBAGENTS_SECTION}}`

- Omit the whole section when the agent has no subagent support.
- Otherwise use `available-subagents-section.md` and replace `{{SUBAGENT_LIST}}`.

Example section:

```md
# Available Sub-Agents

Sub-agents are specialized expert agents. Each sub-agent is available as a tool of the same name. You MUST delegate tasks to the sub-agent with the most relevant expertise.

<available_subagents>
  <subagent>
    <name>test-fixing-agent</name>
    <description>Investigates and repairs failing tests with minimal code changes.</description>
  </subagent>
  <subagent>
    <name>license-agent</name>
    <description>Audits and updates license headers and related compliance files.</description>
  </subagent>
</available_subagents>
```

## `{{AVAILABLE_SKILLS_SECTION}}`

- Omit the whole section when the host has no activatable skills.
- Otherwise use `available-skills-section.md` and replace `{{SKILL_LIST}}`.

Example section:

```md
# Available Agent Skills

You have access to the following specialized skills. To activate a skill and receive its detailed instructions, call the activate-skill tool with the skill's name.

<available_skills>
  <skill>
    <name>large-refactor</name>
    <description>Guidance for staged refactors with intermediate verification.</description>
    <location>.agent-skills/large-refactor</location>
  </skill>
</available_skills>
```

## `{{HOOK_CONTEXT_SECTION}}`

- Omit when no hook context can be injected.
- Otherwise use `hook-context-section.md` as-is.

Example:

Include the whole hook-context section only for hosts that actually provide `<hook_context>` input.

## `{{WORKFLOW_SECTION}}`

- Use either the standard development workflow or the plan-mode workflow.
- Do not include Gemini-specific plan-mode language if the target platform lacks those controls.

Examples:

- Standard: use `workflow-section.md` with `{{WORKFLOW_MODE_NAME}}` set to `Research -> Strategy -> Execution`.
- Plan mode: replace the body with a host-specific read-only planning section.

## `{{OPERATIONAL_GUIDELINES}}`

- Replace with the contents of `static-operational-guidelines.md`.

Example:

Paste the full `# Operational Guidelines` section into the final prompt after the workflow section.

## `{{YOLO_SECTION}}`

- Omit when the host has no reduced-interruption or autonomy mode.
- Otherwise use `yolo-section.md` and keep the wording truthful.

Example:

```md
# Autonomous Mode (YOLO)

You are operating in autonomous mode. The user has requested minimal interruption.
```

## `{{SANDBOX_SECTION}}`

- Omit when sandbox state is unknown or irrelevant.
- Otherwise use `sandbox-section.md` and replace `{{SANDBOX_KIND}}` and `{{SANDBOX_EXPLANATION}}`.

Examples:

- `{{SANDBOX_KIND}} = macOS Seatbelt`
- `{{SANDBOX_EXPLANATION}} = You are running under macOS seatbelt with limited access to files outside the project directory or system temp directory.`

## `{{GIT_SECTION}}`

- Omit when the working directory is not a git repository.
- Otherwise use `git-section.md` as-is.

Example:

Include the git section when the agent is operating inside a checked-out repository with normal commit history available.

## `{{CONTEXT_FILES_SECTION}}`

- Omit when no local instruction or memory files are being loaded.
- Otherwise use `context-files-section.md` and replace `{{CONTEXT_FILE_HEADER}}` and `{{LOADED_CONTEXT}}`.

Example:

```md
# Contextual Instructions (GEMINI.md)
The following content is loaded from local and global configuration files.

<loaded_context>
Always prefer pytest over unittest in this repository.
Do not modify files under generated/ without explicit approval.
</loaded_context>
```
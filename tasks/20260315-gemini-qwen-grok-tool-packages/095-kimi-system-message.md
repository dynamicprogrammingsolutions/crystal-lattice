# 095 - Kimi Default System Message Extraction and Runtime Template

Short description: Investigate and extract the Kimi CLI default system message, classify each section as static/placeholder/omit, produce a vendor extraction set under `docs/default-system-instructions/kimi/` matching the existing Gemini/Qwen/Grok layout from task 050, then add a Kimi runtime template and agent entry in the simplified config following the 060/080 pattern.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Goal

Produce a handoff-quality extraction package for Kimi-like system messages, then integrate it into the existing vendor runtime template and simplified config infrastructure.

The purpose of this task is two-fold:

1. **Extraction**: Gather enough information from the Kimi CLI upstream source that a later agent can manually assemble equivalent system messages in this platform, with clear guidance on what to copy, what to adapt, and what to omit.
2. **Integration**: Add a Kimi runtime template under `application/python/agent_terminal_app/system_messages/kimi/` and a Kimi agent entry in the simplified config so the extracted instructions can be used immediately.

## Scope boundaries

This task is about research, extraction, documentation, and config integration. It does not require extending `feature-system-message` or implementing new runtime features — it reuses the infrastructure built in tasks 060 and 080.

## Key source references

All paths are relative to the locally cloned Kimi CLI repo at `../kimi-cli`, commit `7ba9695`.

### System prompt template and agent spec

- Default agent spec (tool list, template path, template variables):
  - `src/kimi_cli/agents/default/agent.yaml`
- System prompt Jinja2 template:
  - `src/kimi_cli/agents/default/system.md`
- Subagent spec (coder subagent):
  - `src/kimi_cli/agents/default/sub.yaml`
- Alternate agent spec (okabe personality):
  - `src/kimi_cli/agents/okabe/agent.yaml`
- Agent spec loader and inheritance:
  - `src/kimi_cli/agentspec.py`

### Runtime template rendering

- Runtime args struct (`BuiltinSystemPromptArgs` — defines all Jinja2 variables):
  - `src/kimi_cli/soul/agent.py`
- Jinja2 environment setup and template rendering (search for `JinjaEnvironment`, `StrictUndefined`, `render`, `system_prompt` in agent.py):
  - `src/kimi_cli/soul/agent.py`

### Dynamic injection system

- Dynamic injections module (plan mode and other runtime additions injected into system prompt):
  - `src/kimi_cli/soul/dynamic_injections/`
- Plan mode injection:
  - `src/kimi_cli/soul/dynamic_injections/plan_mode.py`
- KimiSoul orchestration (where injections are applied):
  - `src/kimi_cli/soul/kimisoul.py`

### Skills system

- Skill discovery and rendering:
  - `src/kimi_cli/skill/`

### Tool descriptions (Jinja2 templates)

Tool descriptions are loaded from `.md` files via `load_desc()` and may contain their own Jinja2 variables. These are tool-specific instructions that appear in the tool schema `description` field, not in the system prompt directly, but they are part of the overall instruction surface:

- `src/kimi_cli/tools/file/read.md`
- `src/kimi_cli/tools/file/write.md`
- `src/kimi_cli/tools/file/replace.md`
- `src/kimi_cli/tools/file/glob.md`
- `src/kimi_cli/tools/file/grep.md`
- `src/kimi_cli/tools/file/read_media.md`
- `src/kimi_cli/tools/shell/bash.md`
- `src/kimi_cli/tools/shell/powershell.md`
- `src/kimi_cli/tools/web/fetch.md`
- `src/kimi_cli/tools/web/search.md`
- `src/kimi_cli/tools/todo/set_todo_list.md`
- `src/kimi_cli/tools/ask_user/description.md`
- `src/kimi_cli/tools/plan/description.md`
- `src/kimi_cli/tools/plan/enter_description.md`
- `src/kimi_cli/tools/plan/enter_description_yolo.md`
- `src/kimi_cli/tools/multiagent/task.md`
- `src/kimi_cli/tools/multiagent/create.md`
- `src/kimi_cli/tools/dmail/dmail.md`
- `src/kimi_cli/tools/utils.py` (contains `load_desc` implementation)

### Context and session management

- Context persistence and system prompt storage:
  - `src/kimi_cli/soul/context.py`
- Compaction/truncation of conversation context:
  - `src/kimi_cli/soul/compaction.py`

### Existing platform documentation infrastructure

For reference on the expected output shape, see the Gemini/Qwen/Grok extractions produced by task 050:
- `docs/default-system-instructions/gemini/`
- `docs/default-system-instructions/qwen/`
- `docs/default-system-instructions/grok/`

For reference on the runtime template integration pattern, see task 060 and 080:
- `application/python/agent_terminal_app/system_messages/gemini/template.md`
- `application/python/agent_terminal_app/system_messages/qwen/template.md`
- `application/python/agent_terminal_app/system_messages/grok/template.md`
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`
- `application/python/agent_terminal_app/default_config/config.json`

## Template variables to document

The Jinja2 template at `agents/default/system.md` uses these variables:

### Defined in `BuiltinSystemPromptArgs`

| Variable | Description | Source |
|----------|-------------|--------|
| `${ROLE_ADDITIONAL}` | Optional per-agent role/personality override | `agent.yaml` `system_prompt_args.ROLE_ADDITIONAL` |
| `${KIMI_NOW}` | Current datetime in ISO format | `datetime.now().isoformat()` |
| `${KIMI_WORK_DIR}` | Absolute path of current working directory | `Config.work_dir` |
| `${KIMI_WORK_DIR_LS}` | Directory listing of working directory | `list_directory(work_dir)` |
| `${KIMI_AGENTS_MD}` | Content of project `AGENTS.md` | `load_agents_md(work_dir)` |
| `${KIMI_SKILLS}` | Formatted list of available skills | Skill discovery and rendering |
| `${KIMI_ADDITIONAL_DIRS_INFO}` | Formatted additional workspace directories | Conditional block via `{% if KIMI_ADDITIONAL_DIRS_INFO %}` |

### Dynamic injections (applied after base template)

These are not template variables but runtime string injections appended to the compiled system prompt:

- Plan mode instructions (read-only restriction, plan file path, tool restrictions)
- Other dynamic injections from `src/kimi_cli/soul/dynamic_injections/`

## Section classification guidance

The completing agent should classify each section of `system.md` as one of:

### Static reusable
Sections that can be copied near-verbatim to this platform. Most behavioral guidance sections fall here.

### Placeholder-backed
Sections that need runtime variable substitution. The extraction should preserve the section text with a placeholder like `{{KIMI_WORK_DIR}}` and the dynamic-elements guide should explain how to compute it.

### Omit/rewrite
Sections referencing Kimi-specific UX that would be misleading or unsupported on this platform:
- Kimi-specific approval/rejection flows
- Checkpoint/revert system
- `system-reminder` tag compliance (if our tool result pipeline doesn't support that pattern)
- Skill system references
- Subagent labor market references
- Plan mode enter/exit dynamic injection
- Kimi-specific session management assumptions

### Future-feature
Sections requiring capabilities this platform doesn't yet have:
- Dynamic plan mode injection (task 180)
- Skills system
- Subagent delegation (task 150)
- Ask user question structured tool (task 140)

## Kimi-specific traits to analyze

### Traits worth preserving in adapted form

1. **Parallel tool call emphasis** — Kimi strongly recommends making multiple non-interfering tool calls in a single response. This is directly portable.
2. **`<system>` tag semantics** — System information inserted within user/tool messages as supplementary context. Portable if the tool result pipeline supports it.
3. **`<system-reminder>` tag semantics** — Authoritative system directives that override normal behavior. Important for plan mode restrictions. Evaluate whether this platform's tool result pipeline can honor these.
4. **Minimal-change guidance** — "Make MINIMAL changes to achieve the goal" appears explicitly. Directly portable.
5. **Language-matching instruction** — "You MUST use the SAME language as the user." Directly portable.
6. **Working directory listing pattern** — The template includes `${KIMI_WORK_DIR_LS}` showing the top-level directory structure at system prompt time. This is a Kimi-specific pattern not present in other vendors.
7. **`AGENTS.md` reading behavior** — Kimi reads `AGENTS.md` at project root and includes it in the system prompt. Similar to Gemini's `GEMINI.md` but with different file naming. This platform already supports `AGENTS.md`.
8. **Git mutation caution** — "DO NOT run `git commit`, `git push` ... unless explicitly asked to do so. Ask for confirmation each time." Portable.
9. **Third-party package safety** — "you MUST ensure that they are installed in a virtual/isolated environment." Portable.
10. **"Ultimate Reminders" section** — Final behavioral guidance (HELPFUL, POLITE, CONCISE, ACCURATE, PATIENT, THOROUGH). Portable.
11. **Tool call self-explanation rule** — "do not provide explanations because the tool calls themselves should be self-explanatory." Portable but should be evaluated against the existing vendor instructions.

### Traits that should be adapted or conditional

1. **Tool inventory references** — The system prompt doesn't list specific tools (they come from tool schemas), but the tool list in `agent.yaml` defines the available surface. The runtime template should reflect the `kimi-tools` plugin set.
2. **`system-reminder` compliance** — Kimi uses these for plan mode restrictions. If this platform doesn't inject `system-reminder` tags into tool results, this instruction can be simplified or omitted.
3. **Skill system** — Kimi has a skill discovery and rendering system. This platform doesn't have an equivalent. The skills section should be omitted from the runtime template but documented as a future-feature candidate.

### Traits that must be omitted or rewritten

1. **Checkpoint/revert system** — Kimi's `Context` class supports checkpoints and reverting. Not present in this platform.
2. **Approval/rejection flows** — Kimi has a multi-step approval UI with `ToolRejectedError`. This platform doesn't have tool-call approval in the same form.
3. **Dynamic plan mode injection** — Kimi injects plan mode instructions dynamically. This platform's system message is static per session (unless `feature-system-message` is extended).
4. **Subagent labor market** — Kimi has `LaborMarket` for subagent management. Not present in this platform (deferred to task 150).
5. **Session persistence model** — Kimi's `Context` stores history as JSONL with special `_system_prompt` and `_checkpoint` records. Not directly portable.

## Required output shape

### 1. Documentation extraction set under `docs/default-system-instructions/kimi/`

Follow the same structure as the Gemini/Qwen/Grok directories from task 050:

- `README.md` — overview of the Kimi extraction
- `template.md` — raw system prompt text with section placeholders (not explanatory wrappers)
- Separate static section files for each reusable section (e.g., `static-prompt-and-tool-use.md`, `static-coding-guidelines.md`, etc.)
- `dynamic-elements.md` — mapping each placeholder to its computation source, with examples
- `reconstruction-notes.md` — parity notes, adaptation decisions, and future-feature candidates
- `agent-notes.md` — deeper research notes and upstream source references for future automation

### 2. Runtime template under `application/python/agent_terminal_app/system_messages/kimi/`

- `template.md` — a runtime-ready version of the system prompt using the `feature-system-message` variable syntax (`{{KIMI_WORK_DIR}}`, `{{GIT_SECTION}}`, etc.)
- Any helper files needed for dynamic sections

### 3. Config integration

- Add a Kimi agent entry to `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`
- Add a Kimi agent entry to `application/python/agent_terminal_app/default_config/config.json`
- Wire up the Kimi system-message block referencing the runtime template
- Include Kimi in the `kimi-tools` plugin package spec for the Kimi agent

### 4. Test coverage

- Extend `core/python/tests/test_default_system_instructions_docs.py` to verify the new Kimi directory structure and required artifacts exist
- Verify JSON validity of the updated config files

## Deliverables

1. A Kimi extraction set under `docs/default-system-instructions/kimi/` matching the existing vendor layout.
2. Section-by-section classification of the Kimi system prompt with parity notes.
3. A mapping from each template variable to its upstream source and recommended placeholder.
4. A Kimi runtime template and config integration in the simplified and portable configs.
5. Test coverage for the new documentation and config assets.

## Not in scope

1. Extending `feature-system-message` with new capabilities.
2. Implementing skills, subagents, plan mode, or approval flows.
3. Modifying the `kimi-tools` plugin package (task 090 is already done).
4. Implementing tool-call explanation suppression or `system-reminder` tag handling.
5. Porting Kimi's session persistence or checkpoint/revert model.

## Recommended execution direction for the completing agent

1. Read the upstream system prompt template and agent spec files.
2. Read the dynamic injection system to understand what gets appended at runtime.
3. Split the system prompt into named sections.
4. Classify each section as static reusable, placeholder-backed, omit/rewrite, or future-feature.
5. Create the extraction docs under `docs/default-system-instructions/kimi/`.
6. Create the runtime template under `application/python/agent_terminal_app/system_messages/kimi/`.
7. Add Kimi agent entries to both config files.
8. Extend the docs regression test.
9. Validate JSON configs and run tests.

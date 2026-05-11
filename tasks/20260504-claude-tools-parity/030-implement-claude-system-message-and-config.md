# Implement Claude System Message And Config

Expand Claude system-message files and default config so the `claude` agent uses Claude-compatible tools and prompt construction like the existing vendor agents.

## Requirements checklist

- [x] Replace the current minimal Claude system-message mixin with a structured `system_messages/claude` file set based on observed Claude Code request bodies.
- [x] Update `application/python/agent_terminal_app/default_config/config.json` so the `claude` agent uses `claude-tools`.
- [x] Add provider/agent config keys required by Claude web fetch/search tools.
- [x] Keep Tasks and AGENTS context integration consistent with other vendor mixins.
- [x] Update packaging metadata if new default-config files need inclusion.

## Task checklist

- [x] Investigate the Claude Code system-message request shape and save normalized fixtures for no-tools, `Read`, relative-path, and standard-tool cases.
- [x] Identify the primary missing prompt behavior for local parity: dynamic environment/path guidance, especially primary working directory handling for relative file paths.
- [x] Add structured Claude prompt files under `application/python/agent_terminal_app/default_config/system_messages/claude/`.
- [x] Update the `claude_system_message` mixin to render the structured Claude prompt plus existing `TASKS` and AGENTS context sections.
- [x] Switch the primary `claude` agent from `codex-tools` to `claude-tools`.
- [x] Add Claude web/search config keys and any required config-load or system-message rendering tests.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md
Depends On: tasks/20260504-claude-tools-parity/020-implement-claude-tools.md

## Existing State

Current default config already has a Claude mixin and agent in `application/python/agent_terminal_app/default_config/config.json`.

Current mixin:

```json
"claude_system_message": {
  "system_message_enabled": true,
  "system_message": {
    "template": "{{CLAUDE_CODE}}\n\n{{TASKS}}\n\n{{AGENTS_SECTION}}",
    "runtime_code": "${env:CONFIG_DIR}/system_messages/helpers/runtime.py",
    "variables": {
      "CLAUDE_CODE": {
        "text": "${file:${env:CONFIG_DIR}/CLAUDE_CODE_DEFAULT.md}"
      },
      "TASKS": {
        "text": "${file:${env:CONFIG_DIR}/TASKS_v6.md}",
        "runtime_code": "${env:CONFIG_DIR}/system_messages/helpers/tasks_ui.py",
        "condition": {
          "inline_code": "include_tasks()"
        }
      },
      "AGENTS_SECTION": {
        "code": "${env:CONFIG_DIR}/system_messages/helpers/render_agents_context_section.py"
      }
    }
  }
}
```

Current Claude agent:

```json
"claude": {
  "mixin_refs": ["claude_system_message"],
  "provider": "openrouter",
  "model": "anthropic/claude-haiku-4.5",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/codex-tools"
  ],
  "disabled_plugins": ["apply_patch"]
}
```

Current seed file:

```text
application/python/agent_terminal_app/default_config/CLAUDE_CODE_DEFAULT.md
```

This file is intentionally small and should be replaced or supplemented with a more faithful Claude-Code-shaped system-message structure.

## Desired Direction

Add:

```text
application/python/agent_terminal_app/default_config/system_messages/claude/
  introduction.md
  tone-and-style.md
  tool-usage.md
  workflow.md
  git-and-safety.md
  template.md
```

The exact split can change based on captured Claude Code request bodies, but keep it analogous to:

- `system_messages/gemini/*`
- `system_messages/qwen/*`
- `system_messages/kimi/*`
- `system_messages/grok/*`

Update the `claude` agent to use:

```json
"plugins": [
  "path:${env:BUILTIN_PLUGINS}/claude-tools"
]
```

Add any web config keys discovered for `WebFetch` and `WebSearch`, following patterns used by Gemini/Qwen/Kimi tools:

- `tavily_api_key`
- `web_search_enabled`
- `web_search_provider`
- fetch timeout/content-limit settings

## Test Expectations

- Config-load tests should pass for the default `claude` agent.
- The app should list Claude tools for the `claude` agent.
- System message feature tests should verify expected Claude sections render and include `TASKS` and AGENTS context when enabled.

## Execution plan

Added during completion after user approval.

Implement task `030` against the primary `claude` agent in the portable default config.

- [x] Add a structured Claude prompt under `application/python/agent_terminal_app/default_config/system_messages/claude/`.
- [x] Add a small Claude runtime/environment helper so the prompt can render the effective working directory, shell, platform, git status, and model information.
- [x] Update `claude_system_message` to use the new structured Claude prompt while preserving `TASKS` and AGENTS context integration.
- [x] Switch the primary `claude` agent from `codex-tools` to `claude-tools`, and remove the provisional `anthropic-openrouter` fallback agent.
- [x] Add Claude web/search config keys in the same style as the other vendor agents.
- [x] Update focused tests for default-config assets, Claude system-message rendering, plugin listing, and the existing OpenRouter default-config integration case for the `claude` agent.

## Progress Notes

Added during status refresh, before implementation.

Pre-implementation state captured here for handoff context:

- Claude system-message investigation fixtures and notes existed under `plugins/claude-tools/investigation/fixtures/system-message/` and `plugins/claude-tools/investigation/notes/system-message.md`.
- The investigation identified the observed Claude section structure and the need for a dynamic environment section that includes the primary working directory for relative-path resolution.
- At that point, `application/python/agent_terminal_app/default_config/config.json` still used the old minimal `claude_system_message` template and still pointed the primary `claude` agent at `codex-tools`.

## Completion Notes

Added during completion.

Implemented the Claude system-message/config slice against the primary `claude` default-config agent:

- Added structured Claude prompt assets under `application/python/agent_terminal_app/default_config/system_messages/claude/`.
- Added matching runtime-bundle copies under `application/python/agent_terminal_app/system_messages/claude/` so packaged runtime assets stay aligned with the portable default config.
- Added Claude helpers:
  - `application/python/agent_terminal_app/default_config/system_messages/helpers/claude_runtime.py`
  - `application/python/agent_terminal_app/default_config/system_messages/helpers/render_claude_environment_section.py`
  - plus matching runtime-bundle copies under `application/python/agent_terminal_app/system_messages/helpers/`
- Updated `claude_system_message` in `application/python/agent_terminal_app/default_config/config.json` to use the new template and environment helper while preserving `TASKS` and AGENTS context rendering.
- Switched the primary `claude` agent to `path:${env:BUILTIN_PLUGINS}/claude-tools`, added web-search-related config keys, and removed the provisional `anthropic-openrouter` agent.
- Updated focused tests to cover:
  - Claude runtime/environment helper rendering
  - default-config Claude system-message compilation including `TASKS` and AGENTS context when enabled
  - default-config Claude plugin listing and effective config
  - default-system-instruction asset expectations
  - the existing OpenRouter default-config integration prompt for the `claude` agent

Packaging metadata did not require code changes because the existing setuptools glob patterns already include `default_config/system_messages/**/*.md`, `default_config/system_messages/**/*.py`, `system_messages/**/*.md`, and `system_messages/**/*.py`.

Focused verification run during completion:

```bash
python -m py_compile application/python/agent_terminal_app/default_config/system_messages/helpers/claude_runtime.py application/python/agent_terminal_app/default_config/system_messages/helpers/render_claude_environment_section.py application/python/agent_terminal_app/system_messages/helpers/claude_runtime.py application/python/agent_terminal_app/system_messages/helpers/render_claude_environment_section.py application/python/tests/test_claude_system_message_helpers.py application/python/tests/test_default_config_effective_agent_configs.py application/python/tests/test_terminal_application_default_config_openrouter_integration.py core/python/tests/test_default_system_instructions_docs.py
pytest application/python/tests/test_claude_system_message_helpers.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py -q
ruff check application/python/agent_terminal_app/default_config/system_messages/helpers/claude_runtime.py application/python/agent_terminal_app/default_config/system_messages/helpers/render_claude_environment_section.py application/python/agent_terminal_app/system_messages/helpers/claude_runtime.py application/python/agent_terminal_app/system_messages/helpers/render_claude_environment_section.py application/python/tests/test_claude_system_message_helpers.py application/python/tests/test_default_config_effective_agent_configs.py application/python/tests/test_terminal_application_default_config_openrouter_integration.py core/python/tests/test_default_system_instructions_docs.py
```

Result: `14 passed` and `ruff` reported `All checks passed`.

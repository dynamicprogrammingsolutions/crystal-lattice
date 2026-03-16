# 060 - Simplified System Message Configs and Minimal Dynamics

Short description: Add a simpler multi-vendor application config that uses markdown system-message templates plus a minimal extension to `feature-system-message` for inline expressions and conditional sections, while keeping the current file-based `code` option and avoiding a larger prompt DSL.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/040-agent-and-provider-plugin-package-config.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/050-vendor-friendly-system-messages.md`

## Goal

Produce a practical, simpler runtime configuration for vendor-flavored agents that uses the existing `feature-system-message` plugin for most composition work, with only a small amount of additional dynamic behavior.

The main outcome should be a config and template setup that a human can read and modify without having to build a custom prompt-rendering framework.

## Requested outcome

1. Add a simplified example config modeled on `application/python/agent_terminal_app/config_v2_multi_family_tools.json`.
2. Use separate markdown template files for the vendor system messages instead of large inline strings.
3. Include some dynamic sections, but intentionally omit sections that are unsupported or misleading on this system.
4. Use `feature-system-message` for nearly all composition logic.
5. Extend `feature-system-message` only minimally to support small dynamic runtime facts such as current working directory and git-repository detection.

## Scope constraints

This task is intentionally smaller than a full vendor prompt-builder.

Keep the implementation focused on:

1. a cleaner config example
2. runtime markdown templates
3. a minimal amount of dynamic section logic

Do not turn `feature-system-message` into a full programming or templating system.

## Locked-in design decisions from planning

These decisions were discussed and should be treated as the target direction unless implementation reveals a concrete blocker.

### 1. Keep the existing file-based `code` behavior

The current `feature-system-message` supports:

1. `text`
2. `files`
3. `code` as a path to a Python file

That existing `code` meaning should be preserved in this subtask.

Do not repurpose `code` into inline source text.

### 2. Add `inline_code` as a separate new capability

Add a new `inline_code` value source so simple dynamic values do not require separate helper files.

Recommended semantics:

1. If `inline_code` is a single Python expression, evaluate it and use the result directly.
2. Otherwise execute it as a block and read `VALUE` from the resulting namespace.
3. If no result is produced, treat it as empty string for value rendering.

Examples:

1. Simple expression:
- `"inline_code": "cwd"`
2. Simple boolean expression:
- `"inline_code": "is_git_repo()"`
3. Multi-line block:
- `"inline_code": "if is_git_repo():\n    VALUE = '# Git Repository\\n\\n- Review changes with git status before committing.'\nelse:\n    VALUE = ''"`

### 3. Add `condition` support to variable specs

Any variable spec should be allowed to include an optional `condition`.

`condition` should support the same two lightweight code forms used for simple dynamic logic:

1. external file-backed code using the existing `code` path behavior
2. inline code using the new `inline_code`

If the condition is falsey, the variable should resolve to `""` and any `files` reads or other value work should be skipped.

### 4. Do not add standalone boolean placeholders such as `$IS_GIT_REPO`

The preferred model is that a whole section variable becomes either:

1. the full section text
2. or an empty string

Example preferred shape:

```json
{
  "GIT_SECTION": {
    "files": [
      "application/python/agent_terminal_app/system_messages/shared/git-section.md"
    ],
    "condition": {
      "inline_code": "is_git_repo()"
    }
  }
}
```

### 5. Provide a tiny helper runtime for code and inline code

Expose a very small helper context to file-based `code`, `condition.code`, `inline_code`, and `condition.inline_code`.

At minimum:

1. `cwd`
2. `is_git_repo(path: str | None = None) -> bool`
3. `git_root(path: str | None = None) -> str | None`

Optional but acceptable if implementation benefits:

1. `os`
2. `Path`

### 6. Prefer static markdown files plus small conditions

Most vendor instructions should still live in markdown files.

Use dynamic code mainly for:

1. choosing whether a section appears
2. inserting a short dynamic string like the current working directory

Avoid embedding large prompt sections directly in code unless there is no simpler option.

## What the simplified config should look like

Use `application/python/agent_terminal_app/config_v2_multi_family_tools.json` as the starting reference, but make the system-message portions simpler and more modular.

Expected direction:

1. one simplified agent per vendor family
2. system-message templates loaded from markdown files
3. variables that load markdown sections from files where possible
4. a small number of dynamic values such as:
- current working directory
- optional git section

The config should intentionally omit dynamic sections that are not truthful or not supported on this system.

Examples of sections that should usually be omitted from this simplified runtime config unless the host clearly supports them:

1. memory-specific sections
2. todo-specific sections when the selected tool family does not expose them
3. sandbox-restriction sections when sandbox status is not being modeled dynamically
4. capability claims like real-time web/X access unless actually available

## Suggested runtime template layout

Keep the runtime templates separate from the research docs in `docs/default-system-instructions/`.

Recommended location:

1. `application/python/agent_terminal_app/system_messages/`

Reasoning:

1. `docs/default-system-instructions/` is now human-oriented extraction/research material.
2. The application config should reference smaller runtime template files that are clearly intended to be loaded by config.

Possible layout:

1. `application/python/agent_terminal_app/system_messages/gemini/template.md`
2. `application/python/agent_terminal_app/system_messages/qwen/template.md`
3. `application/python/agent_terminal_app/system_messages/grok/template.md`
4. `application/python/agent_terminal_app/system_messages/shared/git-section.md`
5. `application/python/agent_terminal_app/system_messages/helpers/*.py`

The exact directory naming may be adjusted during implementation if there is a better local convention, but keep runtime templates separate from research docs.

## Current implementation references

### Existing example config

- `application/python/agent_terminal_app/config_v2_multi_family_tools.json`

This file already shows the broader multi-vendor provider/agent layout and should be used as the reference point for simplification.

### Existing system-message feature

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
- `plugins/feature-system-message/tests/test_system_message_feature.py`
- `plugins/feature-system-message/README.md`

Important current behavior to preserve or extend carefully:

1. `text`, `files`, and `code` variable sources already exist.
2. `code` currently means a path to a Python file, executed with `runpy.run_path`.
3. Placeholder substitution is intentionally simple string replacement.

### Placeholder resolution behavior

- `core/python/agent_app/config.py`
- `core/python/tests/test_application_layer_config.py`

Important note:

1. `${file:...}` is already supported in config as a whole-string placeholder.
2. `${env:...}` works inside strings.

This means runtime template config can safely reference markdown files or helper files without adding new config-resolution machinery.

### Extracted vendor instruction research

- `docs/default-system-instructions/gemini/`
- `docs/default-system-instructions/qwen/`
- `docs/default-system-instructions/grok/`

These docs are the source material for choosing which runtime sections to include, adapt, or omit.

## Expected config patterns

### Static base template from file

```json
{
  "system_message": {
    "template": "{{BASE}}\n\n{{GIT_SECTION}}\n\n{{WORKING_DIRECTORY_LINE}}",
    "variables": {
      "BASE": {
        "files": [
          "application/python/agent_terminal_app/system_messages/gemini/template.md"
        ]
      }
    }
  }
}
```

### Conditional static section

```json
{
  "GIT_SECTION": {
    "files": [
      "application/python/agent_terminal_app/system_messages/shared/git-section.md"
    ],
    "condition": {
      "inline_code": "is_git_repo()"
    }
  }
}
```

### Simple dynamic string

```json
{
  "WORKING_DIRECTORY_LINE": {
    "inline_code": "f'Current working directory: {cwd}'"
  }
}
```

### Less trivial dynamic section via helper file

```json
{
  "VENDOR_EXTRA": {
    "code": "application/python/agent_terminal_app/system_messages/helpers/render_vendor_extra.py"
  }
}
```

## Minimal feature expansion guidelines

The feature changes should remain intentionally small.

Recommended implementation shape:

1. extend variable normalization so a variable can be one of:
- string
- `{ "text": ... }`
- `{ "files": [...] }`
- `{ "code": "path/to/helper.py" }`
- `{ "inline_code": "...python..." }`
2. allow any of those variable specs to also carry:
- `{ "condition": { "code": "path/to/condition.py" } }`
- `{ "condition": { "inline_code": "is_git_repo()" } }`
3. evaluate condition first
4. if false, resolve to empty string without extra file reads or code execution for the main value
5. keep the rest of the substitution model unchanged

Avoid adding:

1. nested condition syntax in templates
2. boolean placeholders as a separate concept
3. a larger expression language beyond Python snippets
4. automatic tool-inventory rendering unless it falls out almost for free

## Testing expectations

Tests are required in the same change.

### `feature-system-message` unit tests

Add coverage for:

1. `inline_code` with a single expression returning text
2. `inline_code` block execution returning `VALUE`
3. `condition.inline_code` on a `text` variable
4. `condition.inline_code` on a `files` variable
5. `condition.code` using an external helper file
6. helper context availability:
- `cwd`
- `is_git_repo()`
- `git_root()`
7. preserving existing `code` path behavior

### Application/config-level tests

Add at least one test covering the simplified config pattern, ideally verifying that:

1. a rendered system message includes the git section when running inside a git repository
2. the same section is omitted when not in a git repository
3. the working-directory line is rendered dynamically

Use the smallest reasonable test surface. Avoid unnecessary provider integration if a local feature or application test can prove the behavior.

## Documentation expectations

Update docs in the same change.

At minimum:

1. `plugins/feature-system-message/README.md`
2. any relevant config docs, likely `docs/plugins/application-config.md`

Document:

1. `inline_code`
2. `condition`
3. the expression-versus-block behavior for `inline_code`
4. the special `VALUE` output contract for block-style inline code
5. the helper context available to code snippets
6. example config for conditional static sections such as `GIT_SECTION`

## Deliverables

1. A simplified multi-vendor example config.
2. Runtime markdown template files for vendor system messages.
3. Minimal `feature-system-message` enhancements for:
- `inline_code`
- `condition`
- helper runtime values like `cwd` and git detection
4. Tests covering the new behavior.
5. Docs explaining how to use the simplified pattern.

## Non-goals

1. Full vendor-parity prompt builders.
2. Automatic rendering of every dynamic section from the research docs.
3. Major changes to application config semantics.
4. Turning `feature-system-message` into a general-purpose scripting system.

## Approved Implementation Plan Added During Completion

Added on 2026-03-16 after user approval.

Implementation scope for this subtask:

1. Extend `plugins/feature-system-message/src/feature_system_message/system_message_feature.py` with minimal mechanics only:
- add `inline_code`
- add optional `condition` on variable specs
- expose a tiny helper runtime with `cwd`, `is_git_repo()`, and `git_root()`
- preserve existing file-based `code` behavior unchanged
- allow non-trivial dynamic sections to be rendered through `code` or `inline_code`, but do not add a larger prompt DSL or tool-aware rendering framework

2. Build the runtime templates under `application/python/agent_terminal_app/system_messages/` by copying upstream extracted wording as faithfully as possible.
- Keep static sections near-verbatim from the extracted vendor docs where they remain truthful on this platform.
- Avoid rewriting static sections just to make them cleaner.
- Omit only sections that would be misleading or unsupported.
- Use dynamic variables only for runtime facts and conditional inclusion.

3. Use `feature-system-message` composition for both simple and moderately complex dynamic sections.
- Simple examples: current working directory, git section gating.
- Acceptable richer dynamic examples through code evaluation: rendered working-directory block, optional directory listing block, other host-truthful runtime sections.
- Do not introduce features that depend on unsupported subsystems such as memory-management parity, hidden sandbox state, or tool-inventory generation unless it comes almost for free.

4. Add a simplified example config, likely `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`, modeled on the existing multi-family config.
- Simpler here means smaller and more maintainable config structure, not reduced fidelity of the instruction text.
- The config should load markdown files for the main vendor sections and use small code-backed variables for dynamic pieces.

5. Add tests in the same change.
- Feature unit tests for `inline_code`, block `VALUE`, `condition.inline_code`, `condition.code`, helper runtime, and preserved `code` semantics.
- Application-level integration test proving a markdown-template config can include or omit git content and render dynamic runtime content.

6. Update docs in:
- `plugins/feature-system-message/README.md`
- `docs/plugins/application-config.md`
- Document the new mechanics and show the intended pattern: preserve static vendor text in files, use minimal code-backed dynamic sections where needed, avoid a broader templating system.

## Completion Notes Added During Completion

Added on 2026-03-16 after implementation and verification.

What changed:

1. `feature-system-message` now supports two new lightweight config capabilities:
- `inline_code` variable sources
- optional `condition` on variable specs using either `code` or `inline_code`

2. File-backed `code` behavior was preserved while adding a tiny helper runtime for both file-backed and inline code:
- `cwd`
- `is_git_repo()`
- `git_root()`
- `Path`
- `os`

3. Runtime system-message assets were added under `application/python/agent_terminal_app/system_messages/` for:
- Gemini
- Qwen
- Grok

4. The runtime assets intentionally preserve upstream static wording as closely as practical and only omit or trim sections that would be misleading on this host, such as unsupported todo, search, subagent, skill, sandbox, memory, or web-capability claims.

5. A simplified example config was added at:
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

6. The simplified config demonstrates:
- markdown template loading from runtime files
- conditional git sections via `condition.inline_code`
- dynamic working-directory insertion via `inline_code`
- a moderately dynamic Gemini contextual-instructions block via file-backed `code`

7. Documentation was updated in:
- `plugins/feature-system-message/README.md`
- `docs/plugins/application-config.md`

8. A lightweight repository test was added to assert the runtime template assets and simplified config file exist.

Files touched:

1. Feature implementation and tests:
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
- `plugins/feature-system-message/tests/test_system_message_feature.py`
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
- `plugins/feature-system-message/README.md`

2. Runtime prompt assets and helper:
- `application/python/agent_terminal_app/system_messages/gemini/*`
- `application/python/agent_terminal_app/system_messages/qwen/*`
- `application/python/agent_terminal_app/system_messages/grok/*`
- `application/python/agent_terminal_app/system_messages/helpers/render_agents_context_section.py`
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

3. Docs and repository-level asset coverage:
- `docs/plugins/application-config.md`
- `core/python/tests/test_default_system_instructions_docs.py`

Tests run:

1. `pytest plugins/feature-system-message/tests/test_system_message_feature.py -q`
2. `pytest plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py -q`
3. `pytest plugins/feature-system-message/tests/test_system_message_integration_with_echo.py -q`
4. `pytest core/python/tests/test_default_system_instructions_docs.py -q`
5. `ruff check plugins/feature-system-message/src/feature_system_message/system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py application/python/agent_terminal_app/system_messages/helpers/render_agents_context_section.py core/python/tests/test_default_system_instructions_docs.py`
6. `python -m json.tool application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json >/dev/null`

Outcomes:

1. All targeted pytest suites passed.
2. `ruff check` passed on the edited Python files.
3. The JSON config validated successfully.
4. The `core/python/tests/test_default_system_instructions_docs.py` run emitted an existing pytest-cov warning about no coverage data for that narrow docs-only test invocation, but the test itself passed.

Open issues / intentional limitations:

1. This subtask does not attempt full vendor-parity dynamic prompt builders.
2. Unsupported upstream sections were omitted rather than simulated, especially:
- Gemini subagents, skills, hook context, sandbox, and yolo sections
- Qwen todo-tool-specific and textual tool-call-example sections
- Grok todo/search/web-capability sections
3. The Grok runtime prompt keeps only the host-truthful subset of its upstream guidance because the current simplified example does not expose Grok's deferred unified `search` tool or todo-list tools.

## Follow-up Adjustment Added During Completion

Added on 2026-03-16 after user feedback on helper-context design.

The initial implementation exposed a hard-coded helper runtime from the feature plugin itself (`cwd`, `is_git_repo`, `git_root`, `Path`, `os`). That was replaced with a config-defined model:

1. `system_message` now supports optional `runtime_code`.
2. `runtime_code` is a Python file executed once per request.
3. All exported non-underscore globals from that file become the runtime namespace for:
- `inline_code`
- `condition.inline_code`
- file-backed `code`
- `condition.code`
4. No helper names are injected by default when `runtime_code` is absent.

This keeps the feature generic and gives config authors full control over imports, subprocess use, helper functions, and convenience variables without requiring feature-level hardcoding.

Additional files/tests updated in the follow-up:

1. Added runtime helper file for the simplified example config:
- `application/python/agent_terminal_app/system_messages/helpers/runtime.py`

2. Updated the simplified config so each vendor system-message block references `runtime_code`.

3. Added and updated tests to verify:
- `runtime_code` is preserved during config normalization
- `inline_code` can use names provided by `runtime_code`
- no default helper context exists without `runtime_code`
- file-backed `code` can use names provided by `runtime_code`
- application config resolves nested `system_message` fields, including `template`, `runtime_code`, and variable values, to the expected final config values

## Approved Follow-up Plan Added During Completion

Added on 2026-03-16 after user approval.

Follow-up scope for this request:

1. Remove the deliberately empty placeholders from the runtime templates under `application/python/agent_terminal_app/system_messages/`.
2. Remove the matching empty-string variable entries from `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`.
3. Add an application-level integration test that exercises the real `AgentApplication` request path using the simplified vendor `system_message` definitions and asserts known substrings in the compiled system message for Gemini, Qwen, and Grok.
4. Keep the test deterministic by swapping in the in-process echo provider while preserving the actual simplified `system_message` config blocks and runtime assets.
5. Add focused coverage that the runtime templates and simplified config no longer keep the deliberately omitted placeholder markers.
6. Run the relevant focused pytest suites plus JSON validation and report results.

## Follow-up Completion Notes Added During Completion

Added on 2026-03-16 after implementing the approved follow-up scope.

What changed in this follow-up:

1. Removed deliberately empty placeholder markers from the runtime templates:
- `application/python/agent_terminal_app/system_messages/gemini/template.md`
- `application/python/agent_terminal_app/system_messages/qwen/template.md`
- `application/python/agent_terminal_app/system_messages/grok/template.md`

2. Removed the matching empty-string variable entries from:
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

3. Added an application-level integration test that exercises the compiled system-message path through `AgentApplication.send_request(...)` while preserving the real simplified vendor `system_message` blocks and runtime assets:
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`

4. The new integration test uses the in-process `EchoOpenAILikeProvider` so it can assert the exact compiled system text without external API calls. It verifies known substrings for:
- Gemini
- Qwen
- Grok

5. Added repository-level coverage that the runtime templates and simplified config no longer retain the deliberately omitted placeholder markers:
- `core/python/tests/test_default_system_instructions_docs.py`

Files touched in this follow-up:

1. Runtime templates and simplified config:
- `application/python/agent_terminal_app/system_messages/gemini/template.md`
- `application/python/agent_terminal_app/system_messages/qwen/template.md`
- `application/python/agent_terminal_app/system_messages/grok/template.md`
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

2. Tests:
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
- `core/python/tests/test_default_system_instructions_docs.py`

3. Task tracking:
- `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`

Tests run in this follow-up:

1. `pytest plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py -q`
2. `pytest core/python/tests/test_default_system_instructions_docs.py -q`
3. `pytest plugins/feature-system-message/tests/test_system_message_integration_with_echo.py -q`
4. `ruff check plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py core/python/tests/test_default_system_instructions_docs.py`
5. `python -m json.tool application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json >/dev/null`

Outcomes:

1. All targeted pytest suites passed.
2. `ruff check` passed on the edited test files.
3. The simplified config still validates as JSON.
4. The docs-only pytest invocation still emits the existing pytest-cov warning about no coverage data for that narrow run, but the test suite itself passed.

Open issues / intentional limitations:

1. The new compiled-system-message test is integration-style and deterministic, but it does not call a paid external API.
2. It preserves the real simplified vendor `system_message` config blocks and runtime assets, while substituting the provider with the in-process echo provider purely for assertion and test stability.

## Approved Codex Follow-up Plan Added During Completion

Added on 2026-03-16 after user approval.

Follow-up scope for this request:

1. Extend `feature-system-message` so request-time runtime evaluation gets `CONFIG` in its runtime namespace.
2. Extend `feature-system-message` so `runtime_code` can optionally export a zero-argument `get_ui_elements()` function, with `CONFIG`, `TAGS`, and `MODELS` available as runtime globals when that helper is evaluated.
3. Add a Codex helper under `application/python/agent_terminal_app/system_messages/helpers/` that:
- selects a developer message from a flat `codex_developer_messages` config list
- matches rows by `model_regex`
- optionally filters by `personality`
- exports zero-argument `get_ui_elements()` for a `codex_personality` select field
4. Add a Codex provider and `codex` agent to `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json` using OpenRouter plus `codex-tools`.
5. Store Codex instruction mappings as a flat ordered list with `model_regex`, `text`, and optional `personality`, sourcing prompt text from `docs/default-system-instructions/codex/`.
6. Keep the Codex system-message template minimal and drive message selection entirely through helper code plus config data.
7. Add tests covering:
- `CONFIG` visible to runtime code and inline/file-backed evaluation
- zero-argument `get_ui_elements()` exported from `runtime_code`
- Codex compiled system-message selection by model
- Codex compiled system-message selection by `codex_personality`
- `codex_personality` appearing in UI schema
8. Run the focused test suites, validate the simplified JSON config, and append completion notes.

## Codex Follow-up Completion Notes Added During Completion

Added on 2026-03-16 after implementing the approved Codex follow-up scope.

What changed in this follow-up:

1. Extended `feature-system-message` so runtime evaluation always receives `CONFIG` and can optionally contribute UI schema through a zero-argument `get_ui_elements()` helper in `runtime_code`.
2. Added a Codex-specific runtime helper and minimal template under `application/python/agent_terminal_app/system_messages/`.
3. Added a new simplified `openrouter_codex_tools` provider plus a `codex` agent in `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`.
4. The `codex` agent now stores `codex_personality` plus a flat `codex_developer_messages` list with `model_regex`, `text`, and optional `personality`.
5. The helper selects the developer message entirely from config data and also contributes a `codex_personality` select control to UI schema.
6. Added unit and integration tests covering `CONFIG` visibility, zero-argument runtime UI helpers, model-based Codex message routing, personality routing, and UI schema exposure.
7. Updated the feature README and application config docs to describe `CONFIG`, `TAGS`, `MODELS`, and zero-argument runtime UI helpers.

Files touched in this follow-up:

1. Feature implementation:
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`

2. Simplified config and runtime assets:
- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`
- `application/python/agent_terminal_app/system_messages/codex/template.md`
- `application/python/agent_terminal_app/system_messages/helpers/select_codex_developer_message.py`

3. Tests:
- `plugins/feature-system-message/tests/test_system_message_feature.py`
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`

4. Docs:
- `plugins/feature-system-message/README.md`
- `docs/plugins/application-config.md`

5. Task tracking:
- `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`

Tests run in this follow-up:

1. `ruff check plugins/feature-system-message/src/feature_system_message/system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
2. `pytest plugins/feature-system-message/tests/test_system_message_feature.py -q`
3. `pytest plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py -q`
4. `python -m json.tool application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json >/dev/null`
5. `pytest core/python/tests/test_default_system_instructions_docs.py -q`

Outcomes:

1. All targeted tests and lint checks passed.
2. The simplified config validates as JSON after adding the Codex provider and agent.
3. The new integration coverage verifies both model-based and personality-based Codex developer-message selection through the real application request path.
4. The docs-only pytest run still emits the existing pytest-cov no-data warning for that narrow invocation, but the test itself passed.

Open issues / intentional limitations:

1. The plugin remains generic and does not implement any Codex-specific selector type; all Codex routing policy lives in config and helper code.
2. The Codex simplified config covers extracted instruction families already present under `docs/default-system-instructions/codex/`; it does not attempt to recreate additional upstream runtime behaviors beyond developer-message selection and UI personality choice.
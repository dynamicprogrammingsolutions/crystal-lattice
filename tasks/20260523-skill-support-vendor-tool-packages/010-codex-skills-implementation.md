# Codex Skills Implementation

Implement the first production slice of skills support for Codex-family agents, including the initial shared skill library, the generic system-message-variable bridge needed by vendor features, and the Codex-owned skills behavior on top.

## Requirements checklist

- [x] Add the initial abstract shared skill package with explicit-root discovery and loading.
- [x] Extend `feature-system-message` so earlier features can contribute request-scoped template variables from shared state.
- [x] Add a Codex-owned feature plugin that computes the Codex available-skills developer block using upstream Codex wording.
- [x] Wire explicit Codex skill roots into shipped default config.
- [x] Implement manual skill activation by mention (for example `$skillname`) and inject selected `SKILL.md` content request-scoped as a synthetic user message.
- [x] Add targeted tests and docs for the Codex slice.

Parent Task: `tasks/20260523-skill-support-vendor-tool-packages/000-main.md`

## Why Codex goes first

Codex is the first requested slice, and it is the best place to land the foundational pieces because:

- it already has vendor-specific system-message runtime helpers;
- it already has detailed tool/docs parity work in this repo;
- it forces an early decision on whether skill selection is prompt-only or also tool-backed in our current Codex bundle.

## Key findings already gathered

### 1. The current Codex package is shell-heavy, not skill-aware

- `plugins/codex-tools/src/codex_tools/shell_command_tool.py:31-120`
- This bundle currently exposes Codex-style shell execution, but not a general skills subsystem.

### 2. Codex project instructions are already injected with runtime helper code

- `application/python/agent_terminal_app/system_messages/helpers/render_codex_project_instructions.py:11-49`

That makes a Codex-owned skills feature plugin a natural fit: it can compute a placeholder that the Codex template renders, instead of introducing ad hoc per-request scripts for skill discovery.

### 3. The system-message feature currently resolves variables only from config/runtime-code descriptors

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:745-780`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:937-989`

There is no existing request-state variable bridge yet. This subtask should add one generically, without baking in anything skill-specific.

### 4. Core feature hooks already support request-time state mutation before system-message rendering

- `core/python/agent_core/types.py:1042-1085`

That means a vendor feature can run before system-message rendering and stash computed placeholder values in shared state.

### 5. Repo docs already acknowledge Codex skill/file-tool surface, even if the plugin bundle is incomplete

- `docs/codex-tools/README.md:56-57`
- `docs/codex-tools/README.md:107`

This is useful because Codex's effective file-reading surface in this platform is the shell tool, which aligns with upstream Codex behavior closely enough for the first slice without adding a dedicated read-file tool here.

## Proposed Codex slice scope

### A. Add initial shared package

Create something like:

- `plugins/skill-shared/`
  - `discovery.py`
  - `models.py`
  - `parser.py`
  - `paths.py`
  - `loader.py`
  - `errors.py`

Expected responsibilities:

- discover skills from explicit `skills_roots` in listed order;
- treat config order as precedence order;
- parse `SKILL.md`;
- validate required frontmatter;
- resolve safe absolute paths;
- reject escapes and oversized skill files;
- load a named skill on demand;
- optionally sample non-`SKILL.md` sibling files.

Do not add:

- vendor-specific root defaults;
- vendor-specific rendering helpers;
- vendor-specific prompt blocks;
- vendor-specific schemas.

### B. Extend system-message feature generically

Suggested mechanism:

- earlier features write `state["system_message_variables"] = {...}`
- `feature-system-message` merges those values into template rendering

This change must remain generic and should not mention skills anywhere in its API.

### C. Add Codex-owned feature plugin

Suggested package-local artifact:

- `plugins/codex-tools/src/codex_tools/codex_skills_feature.py`

Responsibilities:

- read generic config like `skills_enabled` / `skills_roots`;
- call `skill-shared`;
- compute the Codex available-skills developer block using upstream Codex wording from `../codex/codex-rs/core/src/context/available_skills_instructions.rs`;
- store it in request state for system-message rendering;
- detect manual `$skillname` mentions in the current request and inject matching `SKILL.md` contents as request-scoped synthetic user messages, mirroring upstream Codex's `<skill>` injection shape;
- keep all Codex prompt wording local to `codex-tools`.

### D. Codex activation path for this slice

Implement the two upstream-inspired behaviors:

1. Available-skills developer block:
   - render the available-skills section into the Codex system-message template using the exact upstream wording for the instructional text.

2. Manual activation by mention:
   - detect explicit skill mentions like `$skillname` during request initialization;
   - resolve matching discovered skills;
   - read the selected `SKILL.md`;
   - inject each selected skill into the request as a synthetic user message shaped like upstream Codex `<skill>` context.

This avoids adding a dedicated skill-activation tool while still preserving the key upstream Codex activation flow.

## Suggested tests

- shared-package discovery precedence by ordered root list
- duplicate skill name resolution by root order
- symlink escape rejection
- oversized `SKILL.md` rejection
- system-message feature merges request-scoped variables from state
- Codex feature produces placeholder text from configured roots
- Codex default config exposes the expected placeholder in rendered instructions

## Files likely to change

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
- new `plugins/skill-shared/...`
- `plugins/codex-tools/src/codex_tools/...`
- Codex system-message template/default-config files under:
  - `application/python/agent_terminal_app/default_config/...`
  - `application/python/agent_terminal_app/system_messages/...`
  - possibly docs under `docs/default-system-instructions/codex/`

## Execution plan

Added during completion after user approval.

1. Add a neutral shared `skill-shared` library package with explicit-root discovery, `SKILL.md` parsing, YAML frontmatter extraction, and optional sidecar YAML loading helpers. Keep it mechanical only: no vendor-specific defaults, prompt text, or activation rules.
2. Extend `feature-system-message` with a generic request-scoped variable bridge via `state["system_message_variables"]`, merged into template variables just before render so earlier features can contribute placeholders without adding config-only descriptors.
3. Add Codex-owned skill interpretation in `plugins/codex-tools`, mapping parsed shared documents into a Codex skill model using current upstream `../codex` behavior: `name` fallback to directory name, required `description`, support for `metadata.short-description`, and fail-open optional `agents/openai.yaml`.
4. Implement `CodexSkillsFeature` as a request-time feature plugin that:
   - discovers configured skills from explicit roots;
   - renders `CODEX_SKILLS_SECTION` using the exact instructional wording from upstream `AvailableSkillsInstructions`;
   - detects manual `$skillname` mentions in request messages;
   - injects selected `SKILL.md` contents as synthetic user messages with upstream-style `<skill><name>...<path>...` wrappers, on-the-fly for the current request only.
5. Update the Codex system-message template and default config so Codex agents expose `CODEX_SKILLS_SECTION` and explicit generic `skills_*` config keys rooted at `.agents/skills`, while keeping all wording and activation behavior local to `codex-tools`.
6. Add tests for shared discovery/parsing, request-scoped system-message variable merging, Codex developer-block rendering, explicit mention activation/injection, and default-config integration. Update README/docs for `feature-system-message`, `skill-shared`, and `codex-tools`.

## Completion Notes

Added during completion.

- Implemented `plugins/skill-shared/` as a neutral discovery/parsing library using `yaml.safe_load`, explicit-root traversal, frontmatter extraction, and optional sidecar YAML mapping helpers.
- Extended `feature-system-message` so request-scoped variables supplied through `state["system_message_variables"]` override config variables for that request and existing `state["request"]["messages"]` overrides are preserved when rendering the final system message.
- Added `CodexSkillsFeature` and `codex_skill_loader.py` in `plugins/codex-tools`:
  - renders the available-skills developer block using the upstream Codex wording from `../codex/codex-rs/core/src/context/available_skills_instructions.rs`
  - supports manual `$skillname` activation
  - injects selected `SKILL.md` contents as upstream-style synthetic `<skill>` user messages
  - converts those synthetic core messages to provider-native form through a new public `AgentCore.core_messages_to_native(...)` helper, so activation is no longer tied to a specific provider message shape
  - returns updated `native_messages` from `initialize_request`, making the injected skill durable in retained native history
- Wired `CODEX_SKILLS_SECTION` into the Codex template and added generic `skills_*` config keys to the shared Codex mixin, using relative `.agents/skills` roots so resolution happens against the working directory at request time.
- Updated docs in `plugins/feature-system-message/README.md` and `plugins/codex-tools/README.md`.
- Added a real-provider application-level integration test in `application/python/tests/test_codex_skill_activation_real_api.py` that creates a temp workspace with a skill, sends a user message containing `$skillname`, and verifies both the assistant response and the retained provider-native request payload contain the injected skill text.
- Added a duplicate-injection guard so a skill already injected into retained native history is not re-activated on later request/tool-loop phases. The synthetic skill message now carries metadata (`codex_skill_injected`, `codex_skill_name`, `codex_skill_path`) and the Codex feature checks for an existing injected skill before appending another copy.
- Strengthened the real-provider integration test to force a tool-loop phase and assert that the retained native history contains exactly one injected `<skill>` message, catching the repeated-activation regression from interactive use.
- Verification run:
  - `pytest plugins/skill-shared/tests/test_skill_shared.py -q`
  - `pytest plugins/feature-system-message/tests/test_system_message_feature.py -q`
  - `pytest plugins/codex-tools/tests/test_codex_skills_feature.py plugins/codex-tools/tests/test_codex_tools_imports.py -q`
  - `pytest application/python/tests/test_codex_skill_activation_real_api.py -q -m 'integration and api and openrouter'`
  - `pytest application/python/tests/test_default_config_effective_agent_configs.py -q -m integration`
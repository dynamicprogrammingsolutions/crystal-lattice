# Codex Skills Implementation

Implement the first production slice of skills support for Codex-family agents, including the initial shared skill library, the generic system-message-variable bridge needed by vendor features, and the Codex-owned skills behavior on top.

## Requirements checklist

- [ ] Add the initial abstract shared skill package with explicit-root discovery and loading.
- [ ] Extend `feature-system-message` so earlier features can contribute request-scoped template variables from shared state.
- [ ] Add a Codex-owned feature plugin that computes the Codex skills placeholder content.
- [ ] Wire explicit Codex skill roots into shipped default config.
- [ ] Decide and implement how Codex reads selected `SKILL.md` content in this platform's current tool surface.
- [ ] Add targeted tests and docs for the Codex slice.

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

This is useful because we can either:

- add the minimum skill-reading path now, or
- explicitly document a temporary shell-based reading strategy if we do not yet want to add a full Codex `read_file` tool.

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
- compute a Codex-specific rendered placeholder string;
- store it in request state for system-message rendering;
- keep all Codex prompt wording local to `codex-tools`.

### D. Decide Codex skill activation/reading path

This subtask should choose one of these approaches and document the tradeoff:

1. Prompt-only selection in v1:
   - Codex sees available skills in the system message.
   - Codex reads the chosen `SKILL.md` using existing tools, likely `shell_command`.

2. Add a dedicated Codex read/skill path:
   - add a Codex `read_file` and/or dedicated skill tool support in our bundle.

The repo context today suggests prompt-only + existing tools may be the smallest first slice, but the task owner should decide based on fidelity and implementation cost.

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

## Completion Notes

To be added during implementation.
# Kimi Skills Implementation

Build Kimi-family skills support on top of the Codex slice: reuse the shared skill package and request-scoped system-message-variable bridge, then add Kimi-owned discovery wiring, Kimi-owned placeholder rendering, and Kimi-compatible file-access behavior for reading skills.

## Requirements checklist

- [ ] Add a Kimi-owned skills feature plugin.
- [ ] Wire explicit Kimi skill roots into shipped default config.
- [ ] Populate the Kimi skills placeholder used by the Kimi template.
- [ ] Ensure Kimi tools can actually read discovered skills from the configured skill roots.
- [ ] Add tests/docs for the Kimi slice.

Parent Task: `tasks/20260523-skill-support-vendor-tool-packages/000-main.md`

Depends On: `tasks/20260523-skill-support-vendor-tool-packages/010-codex-skills-implementation.md`

## Why Kimi goes second

Kimi already has a documented skills section in this repo's extracted prompt materials, but the current platform implementation does not yet populate it at runtime. Once the shared package and state-variable bridge exist, Kimi is the next cleanest integration.

## Key findings already gathered

### 1. Kimi's current template structure already expects a skills inventory

- `docs/default-system-instructions/kimi/skills-section.md:1-13`

The placeholder is `${KIMI_SKILLS}` in the extracted docs, and the guidance is explicitly:

- show available skills;
- read `SKILL.md` only when needed.

### 2. Kimi project-information content is already assembled through a runtime helper

- `application/python/agent_terminal_app/system_messages/helpers/render_kimi_project_information_section.py:4-43`

So a Kimi-owned skills feature plugin should fit the current vendor pattern well.

### 3. Kimi read-file behavior currently only allowlists workspace paths

- `plugins/kimi-tools/src/kimi_tools/kimi_read_file_tool.py:29-35`
- `plugins/kimi-tools/src/kimi_tools/kimi_read_file_tool.py:128-141`

That means simply telling the model about skills is not enough. This subtask must ensure the configured skill roots are also readable by the Kimi tool surface.

### 4. Kimi `ReadFile` already matches the right behavior style for reading `SKILL.md`

- `plugins/kimi-tools/src/kimi_tools/kimi_read_file_tool.py:37-95`
- `plugins/kimi-tools/src/kimi_tools/kimi_read_file_tool.py:205-220`

This is a good fit for the upstream Kimi pattern where the model chooses a skill and then reads its `SKILL.md`.

## Proposed Kimi slice scope

### A. Add Kimi-owned skills feature plugin

Suggested package-local artifact:

- `plugins/kimi-tools/src/kimi_tools/kimi_skills_feature.py`

Responsibilities:

- read generic config (`skills_enabled`, `skills_roots`, limits, etc.);
- call `skill-shared`;
- render Kimi-style inventory text for the Kimi template;
- write request-scoped placeholder values to shared state.

### B. Wire explicit Kimi roots into default config

Do not encode Kimi defaults in shared code. Put them in Kimi agent/config blocks only.

### C. Extend Kimi read/shell allowlists

At least one of the Kimi-accessible tools must be able to read the configured skill roots. The most natural path is to extend `kimi_read_file_tool` to treat configured skill roots as additional allowed read locations.

If shell access is also intended as a fallback, document that clearly, but `ReadFile` should ideally work for `SKILL.md` directly.

## Suggested tests

- Kimi feature renders `${KIMI_SKILLS}` from configured roots
- Kimi agent with configured skill roots can read a skill file through `ReadFile`
- missing/empty roots produce an omitted or empty skills section as intended
- Kimi default config includes explicit skill-root config

## Files likely to change

- `plugins/kimi-tools/src/kimi_tools/kimi_read_file_tool.py`
- new `plugins/kimi-tools/src/kimi_tools/kimi_skills_feature.py`
- Kimi system-message config/template files under:
  - `application/python/agent_terminal_app/default_config/...`
  - `application/python/agent_terminal_app/system_messages/...`
  - docs under `docs/default-system-instructions/kimi/` if wording needs updates

## Completion Notes

To be added during implementation.
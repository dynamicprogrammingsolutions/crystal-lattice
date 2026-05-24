# Gemini Skills Implementation

Add Gemini-family skills support using explicit configured roots, a Gemini-owned skills feature plugin for prompt placeholders, and a Gemini-owned activation tool that loads one selected skill for the model.

## Requirements checklist

- [ ] Add a Gemini-owned skills feature plugin for Gemini system-message placeholders.
- [ ] Add a Gemini-owned activation tool for loading a selected skill.
- [ ] Wire explicit Gemini skill roots into shipped default config.
- [ ] Add Gemini tests/docs for discovery, placeholder rendering, and activation.

Parent Task: `tasks/20260523-skill-support-vendor-tool-packages/000-main.md`

Depends On: `tasks/20260523-skill-support-vendor-tool-packages/010-codex-skills-implementation.md`

## Why Gemini comes after Codex and Kimi

Gemini has stronger upstream evidence for a dedicated activation tool, but the shared mechanics and request-scoped template-variable bridge should be proven in Codex/Kimi first.

## Key findings already gathered

### 1. The extracted Gemini docs in this repo already assume an activation tool

- `docs/default-system-instructions/gemini/available-skills-section.md:1-7`

The current wording says the model should call an activation tool to receive detailed skill instructions.

### 2. Upstream Gemini CLI docs and code references show a real skills system and activation tool

Relevant upstream research already captured during investigation:

- Gemini docs reference `.gemini/skills`, `.agents/skills`, and an activation flow.
- Upstream package references include `activate_skill` and skill reloading/management commands.

### 3. The existing repo architecture already uses shared engines plus Gemini-owned wrappers

- `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py:54-120`

This is the pattern to follow for skills:

- shared package does mechanics;
- Gemini package owns prompt/tool behavior.

## Proposed Gemini slice scope

### A. Add Gemini-owned feature plugin

Suggested artifact:

- `plugins/gemini-tools/src/gemini_tools/gemini_skills_feature.py`

Responsibilities:

- discover skills using generic config roots;
- render Gemini-specific prompt placeholder content;
- write request-scoped variables for system-message rendering.

### B. Add Gemini activation tool

Suggested artifact:

- `plugins/gemini-tools/src/gemini_tools/gemini_activate_skill_tool.py`

Responsibilities:

- expose the Gemini-facing skill activation schema/name;
- validate the requested skill name against discovered skills;
- load the selected skill via `skill-shared`;
- return Gemini-appropriate result formatting containing:
  - skill body
  - base directory
  - optional sampled file list

This tool should not reimplement discovery logic independently if the request state already has the discovered catalog.

## Suggested tests

- Gemini feature renders placeholder content from configured roots
- activation tool loads a selected skill and formats the result
- unknown-skill error wording and schema behavior
- explicit Gemini `skills_roots` wiring in default config

## Completion Notes

To be added during implementation.
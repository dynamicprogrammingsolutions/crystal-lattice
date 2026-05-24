# Skill Support For Vendor Tool Packages

Add Agent Skills support to the vendor tool packages using one abstract shared skill library plus vendor-owned LLM-facing behavior, with Codex implemented first, Kimi second, and the remaining vendors after that.

## Task checklist

- [ ] `tasks/20260523-skill-support-vendor-tool-packages/010-codex-skills-implementation.md`
- [ ] `tasks/20260523-skill-support-vendor-tool-packages/020-kimi-skills-implementation.md`
- [ ] `tasks/20260523-skill-support-vendor-tool-packages/030-gemini-skills-implementation.md`
- [ ] `tasks/20260523-skill-support-vendor-tool-packages/040-qwen-skills-implementation.md`
- [ ] `tasks/20260523-skill-support-vendor-tool-packages/050-cross-vendor-tests-docs-and-default-config.md`

## Context

We want to add skills support to the existing vendor tool/plugin packages while preserving the repo's current architecture:

- Shared packages should stay abstract and mechanical.
- Vendor packages should own all LLM-facing behavior.
- Skill roots should be explicit in config, not hidden behind vendor-specific defaults in shared code.
- Vendor system-message templates are already defined per vendor in default config, so vendor packages may add vendor-owned feature plugins that populate placeholders used by those templates.

## Agreed design constraints

1. Do not put vendor switches or vendor profiles into the shared skill package.
2. The shared package should not emit vendor-specific prompt blocks, tool schemas, or formatted tool results.
3. Vendor packages may each define their own feature plugin that computes a vendor-specific skills placeholder for that vendor's system-message template.
4. The shipped default config should explicitly set skill roots per vendor agent/config block, using generic config keys.
5. A generic default should be minimal and unsurprising, ideally using neutral `.agents/skills` conventions only if any default roots are provided at all.

## Shared-vs-vendor split to preserve

### Shared package should own

- Discovering skills from an ordered list of explicit roots.
- Parsing `SKILL.md`.
- Validating required frontmatter and name/path consistency.
- Path normalization and containment checks.
- Symlink and oversized-file safety.
- Loading one selected skill and optionally sampling sibling files.

### Vendor packages should own

- Which configured roots they pass into shared discovery.
- Whether skills are surfaced through a tool, a system-message section, or both.
- Tool names and schemas (`activate_skill`, `skill`, etc.).
- Tool result formatting.
- Exact system-message wording and placeholder names.

## Important repo references

- Feature hook ordering and request-time feature mutation points:
  - `core/python/agent_core/types.py:1042-1085`
- Existing system-message feature resolves variables from config/runtime code today:
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:745-780`
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:937-989`
- Codex project-instructions helper currently injects AGENTS content via runtime code:
  - `application/python/agent_terminal_app/system_messages/helpers/render_codex_project_instructions.py:11-49`
- Kimi project-information helper currently injects AGENTS content via runtime code:
  - `application/python/agent_terminal_app/system_messages/helpers/render_kimi_project_information_section.py:4-43`
- Existing shared-package pattern examples:
  - `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
  - `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py`

## Expected implementation direction

- Add a new shared package, likely `plugins/skill-shared/`, with no vendor-specific defaults or formatting.
- Extend `feature-system-message` in a generic way so earlier feature plugins can contribute request-scoped template variables through shared state.
- Add vendor-owned skills feature plugins in `codex-tools`, `kimi-tools`, `gemini-tools`, and `qwen-tools`.
- Wire explicit `skills_roots` (or equivalent generic keys) into vendor-specific default-config blocks.

## Suggested generic config shape

These names are suggestions, not a locked API:

- `skills_enabled`
- `skills_roots`
- `skills_max_skill_file_bytes`
- `skills_max_sampled_files`
- `skills_disabled_names`
- `skills_follow_symlinks`

The key point is that these are generic and explicit. Vendor-specific shipped config can choose different root lists without shared code knowing why.

## Completion Notes

To be added during implementation.
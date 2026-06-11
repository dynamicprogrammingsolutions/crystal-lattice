# Cross-Vendor Tests, Docs, And Default Config

Finish the skills rollout by harmonizing generic config naming, validating default-config wiring across vendor agents, and adding cross-vendor tests/docs for the final behavior after Codex, Kimi, Gemini, and Qwen implementations land.

## Requirements checklist

- [ ] Validate the final generic config shape used by all vendor packages.
- [ ] Add cross-vendor tests for explicit-root precedence and placeholder rendering.
- [ ] Update plugin and default-config docs to explain the shared-vs-vendor split.
- [ ] Ensure no vendor defaults leaked into `skill-shared`.
- [ ] Document migration/compatibility notes for any old one-off config keys such as Qwen's `user_skills_dir`.

Parent Task: `tasks/20260523-skill-support-vendor-tool-packages/000-main.md`

Depends On: `tasks/20260523-skill-support-vendor-tool-packages/010-codex-skills-implementation.md`
Depends On: `tasks/20260523-skill-support-vendor-tool-packages/020-kimi-skills-implementation.md`
Depends On: `tasks/20260523-skill-support-vendor-tool-packages/030-gemini-skills-implementation.md`
Depends On: `tasks/20260523-skill-support-vendor-tool-packages/040-qwen-skills-implementation.md`

## Goals

1. Make the final public config story explicit and easy to understand.
2. Confirm that vendor packages differ only where they should:
   - system-message wording
   - tool schema/tool name
   - tool result formatting
   - vendor-owned feature plugin behavior
3. Confirm that shared skill mechanics remain vendor-neutral.

## Cross-cutting items to verify

- All shipped vendor configs use explicit `skills_roots`-style config rather than hidden code defaults.
- `feature-system-message` request-scoped variable support remains generic and not skill-specific.
- Shared skill helpers contain no vendor prompt wording or root presets.
- Vendor docs explain how skill roots are configured and how skill activation works for that vendor.

## Useful references

- Feature hook / request initialization contract:
  - `core/python/agent_core/types.py:1042-1085`
- Current system-message variable resolution behavior:
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:745-780`
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:937-989`
- Existing vendor docs/template directories:
  - `docs/default-system-instructions/gemini/`
  - `docs/default-system-instructions/kimi/`
  - `docs/default-system-instructions/qwen/`
  - `docs/default-system-instructions/codex/`

## Completion Notes

To be added during implementation.
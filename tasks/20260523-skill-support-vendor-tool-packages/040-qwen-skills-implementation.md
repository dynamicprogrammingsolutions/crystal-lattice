# Qwen Skills Implementation

Add Qwen-family skills support using explicit configured roots, a Qwen-owned skills feature plugin where needed, and a Qwen-owned skill-loading tool with Qwen-appropriate LLM-facing schema and output behavior.

## Requirements checklist

- [ ] Add a Qwen-owned skills feature plugin if the Qwen template needs a prompt-level skills section.
- [ ] Add a Qwen-owned skill-loading tool with dynamic available-skill awareness.
- [ ] Wire explicit Qwen skill roots into shipped default config.
- [ ] Ensure Qwen file-access behavior remains compatible with configured skill roots.
- [ ] Add tests/docs for the Qwen slice.

Parent Task: `tasks/20260523-skill-support-vendor-tool-packages/000-main.md`

Depends On: `tasks/20260523-skill-support-vendor-tool-packages/010-codex-skills-implementation.md`

## Key findings already gathered

### 1. Qwen file tools already anticipate a configured user skills directory

- `plugins/qwen-tools/src/qwen_tools/qwen_read_file_tool.py:24-39`

This is important because the package is already structurally close to supporting configured skill roots. We should generalize this cleanly rather than keep a one-off `user_skills_dir`.

### 2. Qwen wrappers already follow the shared-mechanics/vendor-surface pattern

- `plugins/qwen-tools/src/qwen_tools/qwen_read_file_tool.py:20-68`

So skills should follow the same rule:

- shared discovery/loading in `skill-shared`;
- Qwen-owned schema/result formatting in `qwen-tools`.

### 3. The repo's research notes already describe Qwen as having a real skill tool/runtime path

The implementation should align with the local architectural conclusion already reached:

- use shared mechanics;
- keep Qwen tool shape and prompt behavior inside `qwen-tools`.

## Proposed Qwen slice scope

### A. Add Qwen-owned skill tool

Suggested artifact:

- `plugins/qwen-tools/src/qwen_tools/qwen_skill_tool.py`

Responsibilities:

- expose Qwen-compatible schema and tool name;
- list/select from discovered skills;
- load one selected skill via `skill-shared`;
- return Qwen-appropriate result formatting.

### B. Normalize Qwen config usage

Consider replacing the package-local `user_skills_dir` special case with generic `skills_roots` handling, while preserving backward compatibility if needed.

### C. Optional Qwen prompt placeholder feature

If Qwen's current system-message template in this repo does not need a prompt-level available-skills section, keep the feature plugin minimal or omit it. This should remain a vendor choice.

## Suggested tests

- Qwen tool loads a selected skill from configured roots
- Qwen tool rejects unknown skill names cleanly
- Qwen read access remains compatible with configured skill roots
- shipped Qwen default config contains explicit `skills_roots`

## Completion Notes

To be added during implementation.
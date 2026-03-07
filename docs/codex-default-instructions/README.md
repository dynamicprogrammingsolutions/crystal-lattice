# Codex CLI default model instructions (extracted)

This folder contains the model instruction strings bundled with the **Codex CLI** project.

Source:
- Repository: `https://github.com/openai/codex`
- File: `codex-rs/core/models.json`
- Commit: `39869f74435cb199d56ca5d53cf198f7c5332eec`

## What each file means

Each model gets its own subfolder (for example `gpt-5.2-codex/`).

- `base_instructions.md`
  - The raw `ModelInfo.base_instructions` string.
  - Used directly when `model_messages` is missing, or when the client disables personality / overrides base instructions.

- `model_messages.instructions_template.md` (only for some models)
  - The raw `ModelInfo.model_messages.instructions_template` string.
  - When present, Codex uses this template in preference to `base_instructions`.

- `model_messages.instructions_variables.json` (only for some models)
  - The raw `ModelInfo.model_messages.instructions_variables` object.
  - Contains the personality strings used to fill the template placeholder.

- `instructions_default.md`
  - The effective instructions the Codex code produces for `personality = None`.
  - If the model has a template, this equals `instructions_template` with the placeholder filled using `personality_default`.
  - If the model has no template, this equals `base_instructions`.

- `instructions_friendly.md`, `instructions_pragmatic.md` (only for templated models)
  - The effective instructions for those personality settings.

## Placeholder behavior

The only placeholder used by the bundled templates is:

- `{{ personality }}`
  - Replaced at runtime with a personality string from `model_messages.instructions_variables`.
  - Default selection uses `personality_default` when no explicit personality is set.

## Runtime selection notes

In Codex, the instructions are rendered by logic equivalent to:

- If `model_messages.instructions_template` exists: use it (with placeholder substitution).
- Otherwise: fall back to `base_instructions`.

Codex can also intentionally drop `model_messages` and use `base_instructions` if:

- A caller supplies an explicit `base_instructions` override in config.
- The personality feature is disabled.

Those behaviors are implemented in Codex CLI code (not in this repo).

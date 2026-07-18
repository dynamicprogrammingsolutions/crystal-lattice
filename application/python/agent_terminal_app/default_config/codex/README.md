# Codex Default System Instructions

This directory contains the model instruction strings bundled with the **Codex CLI** project.

It was moved from `docs/codex-default-instructions/` into the application-local
reference archive at
`application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/`.

Sources:
- Repository: `https://github.com/openai/codex`
- File (current): `codex-rs/models-manager/models.json`
- File (historical, pre-`models-manager`): `codex-rs/core/models.json`
- Commit for `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`:
  `2f7d89b1419bf7064346855b0acde23514b1ebc5` (2026-07-13)
- Commit for older models (`gpt-5` through `gpt-5.4`):
  `39869f74435cb199d56ca5d53cf198f7c5332eec`
- Commit for `gpt-5.5`: `c10f95ddac7b35095d334dece2ebcf69bcde61fc` (2026-04-24)

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

## GPT-5.6 family notes

The `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` subfolders were imported from
upstream commit `2f7d89b1419bf7064346855b0acde23514b1ebc5`.

Key differences from older templated models:

- The GPT-5.6 templates have **no `{{ personality }}` placeholder**. The personality
  text is embedded directly in the template body.
- All three `model_messages.instructions_variables` personality values
  (`personality_default`, `personality_friendly`, `personality_pragmatic`) are empty
  strings at the inspected commit.
- Because there is no placeholder to substitute and all personality variables are
  empty, `instructions_default.md` is byte-identical to
  `model_messages.instructions_template.md` and `base_instructions.md` for each
  GPT-5.6 model.
- Only `instructions_default.md` is provided per GPT-5.6 model. No
  `instructions_friendly.md` or `instructions_pragmatic.md` files are created,
  because the upstream provides no distinct friendly/pragmatic prose for these
  models. The default-config `codex_developer_messages` rows for GPT-5.6 omit the
  `personality` field, so all three personality selections (default, friendly,
  pragmatic) resolve to the same `instructions_default.md` via the fallback path
  in `select_codex_developer_message.py`.

`gpt-5.6-terra` and `gpt-5.6-luna` are byte-identical at the inspected commit
(sha256 `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec`),
but they are kept as separate directories so a future upstream divergence is
not hidden. `gpt-5.6-sol` has a distinct template
(sha256 `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9`)
with an extra paragraph in the Personality section.

The bare `gpt-5.6` alias is intentionally not mapped here. Authoritative Codex
catalog discovery publishes only the three explicit family IDs, so the bare
alias falls through to the `.*` fallback row in `codex_developer_messages`.

## Runtime selection notes

In Codex, the instructions are rendered by logic equivalent to:

- If `model_messages.instructions_template` exists: use it (with placeholder substitution).
- Otherwise: fall back to `base_instructions`.

Codex can also intentionally drop `model_messages` and use `base_instructions` if:

- A caller supplies an explicit `base_instructions` override in config.
- The personality feature is disabled.

Those behaviors are implemented in Codex CLI code (not in this repo).

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Codex Default System Instructions

This directory contains the model instruction strings bundled with the **Codex CLI** project.

It was moved from `docs/codex-default-instructions/` into the application-local
reference archive at
`application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/`.

Sources:
- Repository: `https://github.com/openai/codex`
- File (current): `codex-rs/models-manager/models.json`
- File (historical, pre-`models-manager`): `codex-rs/core/models.json`
- Commit for the `gpt-6-astra` import and the GPT-5.6 / `gpt-5.5` /
  `gpt-5.4` template refresh: `e9633d7a0226eac91c7a791dc4f92cf8f25df2ae`
  (2026-09-14)
- Commit for the original `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`
  import: `2f7d89b1419bf7064346855b0acde23514b1ebc5` (2026-07-13)
- Commit for older models (`gpt-5` through `gpt-5.4`):
  `39869f74435cb199d56ca5d53cf198f7c5332eec`
- Commit for `gpt-5.5`: `c10f95ddac7b35095d334dece2ebcf69bcde61fc` (2026-04-24)

## Date-versioned files

From 2026-09-14 onward, newly imported instruction versions are stored in
files whose names carry the date that version was introduced upstream, for
example `instructions_default.20260904.md`. The introduction date is found by
walking the upstream `models.json` git history and comparing template
hashes; see `application/python/docs/development/agent-creation.md` for the
protocol. When a newer upstream version is imported, new dated files are
added and the `codex_developer_messages` row is repointed; previous version
files remain in place. Files that predate this protocol keep their original
names.

## What each file means

Each model gets its own subfolder (for example `gpt-5.2-codex/`).

- `base_instructions.md`
  - The raw `ModelInfo.base_instructions` string.
  - Used directly when `model_messages` is missing, or when the client disables personality / overrides base instructions.
  - Upstream removed `base_instructions` from the bundled catalog on
    2026-09-07 (`8e694e955ae02ca737230a5468c55d5847074072`), so imports from
    that point on have no such file.

- `model_messages.instructions_template.md` (only for some models)
  - The raw `ModelInfo.model_messages.instructions_template` string.
  - When present, Codex uses this template in preference to `base_instructions`.

- `model_messages.instructions_variables.json` (only for some models)
  - The raw `ModelInfo.model_messages.instructions_variables` object.
  - Contains the personality strings used to fill the template placeholder.
  - Upstream removed the personality variables on 2026-09-11; newer imports
    record the remaining (empty) object.

- `instructions_default.md`
  - The effective instructions the Codex code produces for `personality = None`.
  - If the model has a template, this equals `instructions_template` with the placeholder filled using `personality_default`.
  - If the model has no template, this equals `base_instructions`.

- `instructions_friendly.md`, `instructions_pragmatic.md` (only for templated models)
  - The effective instructions for those personality settings.

- `model_messages.persistent_instructions.YYYYMMDD.md` (newer imports)
  - The raw `ModelInfo.model_messages.persistent_instructions` string, a
    Codex CLI persistent-mode instruction block.
  - Kept for provenance only; not wired into the default config.

## Placeholder behavior

The placeholders used by the bundled templates are:

- `{{ personality }}`
  - Replaced at runtime with a personality string from `model_messages.instructions_variables`.
  - Default selection uses `personality_default` when no explicit personality is set.
  - Upstream removed this placeholder from all bundled templates by 2026-09-11.

- `{{connector_id}}` (GPT-6-Astra)
  - Literal text in the `# Apps (Connectors)` section documenting the
    `[$app-name](app://{{connector_id}})` user-message syntax.
  - Upstream renders it literally (it is not a runtime substitution), so it
    is kept verbatim in the imported files.

## GPT-6-Astra notes

The `gpt-6-astra` subfolder was imported from upstream commit
`e9633d7a0226eac91c7a791dc4f92cf8f25df2ae` (2026-09-14). The template
content was introduced upstream on 2026-09-04
(`83b62a02fab5c0fc797cbc9896c332148f1fd9d0`, #42836), so the dated files
carry `20260904`:

- `instructions_default.20260904.md` — effective developer message
  (sha256 `152dfaeeb552876190962be1c12c93d426840ff12691f648261554a7675a6698`,
  21261 chars). Byte-identical to the raw template: there is no
  personality placeholder and `instructions_variables` is empty.
- `model_messages.instructions_template.20260904.md` — raw upstream template.
- `model_messages.instructions_variables.20260904.json` — empty object.
- `model_messages.persistent_instructions.20260904.md` — Codex CLI
  persistent-mode block
  (sha256 `30747e79e50efb64f91cfff3d5ef1882e347081e81448918d5f7d5358e98c523`,
  5737 chars), kept for provenance only.

The template opens with `You are Codex, an agent based on GPT-6` and adds
the `# When to ask the user for permission`, `# Autonomy and persistence`,
`# Apps (Connectors)`, and `# Plugins` sections. The `{{connector_id}}`
placeholder is literal text (see Placeholder behavior).

The default-config `codex_developer_messages` row for `gpt-6-astra` omits
the `personality` field, so all personality selections resolve to the same
dated file via the fallback path in `select_codex_developer_message.py`.
The bare `gpt-6` alias is intentionally not mapped; the authoritative Codex
catalog publishes only `gpt-6-astra`.

## GPT-5.6 family notes

The `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` subfolders were
originally imported from upstream commit
`2f7d89b1419bf7064346855b0acde23514b1ebc5` (2026-07-13; unversioned files).
On 2026-09-14 the drifted upstream templates were imported as dated files
(`instructions_default.20260718.md` and the raw template/variables files)
from commit `e9633d7a0226eac91c7a791dc4f92cf8f25df2ae`; that template
version was introduced upstream on 2026-07-18
(`d26a9bf671b1c03aabfc32e1092d137c1feb3962`, #33961).

Key differences from older templated models:

- The GPT-5.6 templates have **no `{{ personality }}` placeholder**. The personality
  text is embedded directly in the template body.
- The `model_messages.instructions_variables` personality values are empty
  strings, so `instructions_default` is byte-identical to the raw template
  for each GPT-5.6 model.
- Only `instructions_default` files are provided per GPT-5.6 model. No
  `instructions_friendly.md` or `instructions_pragmatic.md` files are created,
  because the upstream provides no distinct friendly/pragmatic prose for these
  models. The default-config `codex_developer_messages` rows for GPT-5.6 omit the
  `personality` field, so all three personality selections (default, friendly,
  pragmatic) resolve to the same file via the fallback path
  in `select_codex_developer_message.py`.

Since the 2026-07-18 upstream refresh, all three GPT-5.6 models share one
byte-identical template
(sha256 `cbefa6b0bede0e332d957fca70ccacf9f12f4c0ecdf81b819e5cbe1a3b16e265`,
17730 chars); `gpt-5.6-sol` no longer has a distinct variant. The three
directories are kept separate so a future upstream divergence is not
hidden. The 2026-07-13 import's distinct Sol template
(sha256 `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9`)
and the shared Terra/Luna template
(sha256 `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec`)
remain in the unversioned files.

The bare `gpt-5.6` alias is intentionally not mapped here. Authoritative Codex
catalog discovery publishes only the three explicit family IDs, so the bare
alias falls through to the `.*` fallback row in `codex_developer_messages`.

## GPT-5.5 and GPT-5.4 refresh notes

Upstream commit `c18277043e52ff4a81fdf2f039ddef85e3a6fd3e` (2026-09-11,
#44930 "Embed friendly instructions in bundled GPT-5.4 and GPT-5.5") removed
the `{{ personality }}` placeholder and embedded the friendly personality
directly in the `gpt-5.5` and `gpt-5.4` templates. The refreshed templates
were imported on 2026-09-14 as `instructions_default.20260911.md` (plus the
raw template/variables files) from commit
`e9633d7a0226eac91c7a791dc4f92cf8f25df2ae`.

- `gpt-5.5` refreshed template: 21459 chars, sha256
  `2351631dfc5644dc5a45eaaca4139475bd02810ee6cb792d058b551559b3242e` —
  byte-identical to the pre-existing `base_instructions.md` (the
  friendly-embedded April 2026 text).
- `gpt-5.4` refreshed template: 15296 chars, sha256
  `f8c4032f78fdb19b46f468239c5dc757f745fbb10520e64e1e4afbf747e52fb8` —
  friendly-embedded with updated file-reference rules.

The `default` personality rows now point at the dated files, so the default
instructions for these models are the friendly-embedded text, matching
upstream. The `friendly` and `pragmatic` rows keep pointing at the retained
`instructions_friendly.md` / `instructions_pragmatic.md` files, which
upstream no longer publishes updates for.

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

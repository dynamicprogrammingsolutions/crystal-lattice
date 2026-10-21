# Agent creation and model updates

This page explains the protocol for creating an agent in the bundled default
configuration, importing its developer messages, and the companion maintenance
a model update needs (model catalog, pricing, docs, tests).

The bundled default configuration lives in
`agent_terminal_app/default_config/`. `config.json` is the maintained source;
site preparation generates `/reference/default-config/` from it. Run the
documentation preparation and build after config changes when documentation
output is in scope.

## Agent entries

An agent is an entry under `agents` in `config.json`. The smallest useful
entry names a provider, a model, and the plugins that supply its tools:

```json
"codex-openai-api": {
  "mixin_refs": ["codex_developer_message", "codex_mcp_defaults"],
  "provider": "openai",
  "model": "gpt-5.4",
  "plugins": ["path:${env:BUILTIN_PLUGINS}/codex-tools"],
  "auth_mode": "api",
  "system_message_as_instructions": false
}
```

Mixin references (`mixin_refs`) pull in shared blocks from `mixins`. The
`codex_developer_message` mixin supplies the system-message template, the
developer-message selection table, and Codex personality/skills settings, so
Codex-family agents do not repeat them.

Two flags control how the compiled system message reaches the provider:

- `system_message_as_instructions: true` sends it as the top-level
  `instructions` field of a Responses request and keeps it out of session
  history;
- `false` keeps it as a persistent native system message in the session.

## System and developer messages

`feature-system-message` renders the configured `system_message` template for
each request from template variables (see
[system-message configuration](../configuration-system-messages.md) for the
general mechanism).

For Codex-family agents the flow is:

1. The mixin's template `system_messages/codex/template.md` combines
   `{{CODEX_DEVELOPER_MESSAGE}}`, `{{CODEX_PROJECT_INSTRUCTIONS}}`,
   `{{CODEX_ENVIRONMENT_CONTEXT}}`, and `{{TASKS}}`.
2. `{{CODEX_DEVELOPER_MESSAGE}}` is produced by
   `system_messages/helpers/select_codex_developer_message.py`, which selects
   a row from `codex_developer_messages` by matching `CONFIG["model"]`
   against `model_regex` (an optional `openai/` prefix is allowed) and
   `CONFIG["codex_personality"]` against the row's `personality` field.
   Rows without a `personality` field match every personality through the
   fallback path.
3. Each row's `text` loads the instruction asset with a
   `${file:${env:CONFIG_DIR}/codex/<model>/...}` placeholder.

The final `.*` row is the fallback for unknown models; add more specific rows
above it.

## Importing Codex developer messages

Instruction text for Codex-family models is imported from the upstream
`openai/codex` repository, file
`codex-rs/models-manager/models.json` (historical path:
`codex-rs/core/models.json`). Each model entry's
`model_messages.instructions_template` is the instruction source; older
entries also carried `base_instructions` and personality
`instructions_variables`, which upstream has since removed.

Assets live under `default_config/codex/<model-id>/`, with reference copies
under
`default_config/system_messages/reference/default-system-instructions/codex/<model-id>/`.
`default_config/codex/README.md` records the upstream commit for each import.

### Date-versioned developer message files

From 2026-09-14 onward, every newly imported developer-message version is
stored in files whose names carry the date that version was introduced
upstream:

- `instructions_default.YYYYMMDD.md` — the effective developer message the
  config row points at;
- `model_messages.instructions_template.YYYYMMDD.md` — the raw upstream
  template;
- `model_messages.instructions_variables.YYYYMMDD.json` — the raw variables
  object, when upstream provides one;
- `model_messages.persistent_instructions.YYYYMMDD.md` — persistent-mode
  instructions, when upstream provides them (kept for provenance; not wired
  into config).

`YYYYMMDD` is the UTC date of the earliest upstream commit whose
`codex-rs/models-manager/models.json` contains exactly this instruction
text. Find it by walking the file's git history from newest to oldest and
comparing the template's sha256 at each commit: keep walking while the hash
matches; the oldest commit in that contiguous matching run — the last one
before the content changes or the model first appears — is the introducing
commit.

When a newer upstream version is imported later, add new date-versioned
files next to the previous ones and repoint the `codex_developer_messages`
row at the new `instructions_default.YYYYMMDD.md`. Keep previous version
files in place for provenance and rollback. Existing files that predate
this protocol keep their original names; do not rename or re-date them.

Placeholders in imported text:

- `{{ personality }}` (older templates) is filled from
  `instructions_variables` per the personality rows;
- non-personality placeholders that upstream renders literally, such as
  `{{connector_id}}` in the GPT-6-Astra Apps (Connectors) syntax, are kept
  verbatim — they document user-message syntax, not a runtime substitution.

## Companion maintenance for a model update

A new or changed model needs more than instruction assets. Do each of the
following in the same change:

### Model catalog snapshot

Refresh the checked-in Codex models snapshot used for ChatGPT-mode model
discovery:

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_models.py
```

The snapshot replaces its previous content, so retired upstream models drop
out and new models appear. See
[Model discovery](../../../../plugins/openai_responses/docs/development/model-discovery.md).

Reasoning-effort gating in
`openai_responses_reasoning_extension.py` uses per-family model patterns; add
a pattern for a new model family so its real effort set is offered.

### Pricing snapshot

Refresh the checked-in pricing snapshot from the official pricing pages:

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py
```

The refresh merges page entries into the snapshot. The pricing pages label
the fast processing tier `fast`, and the snapshot keys it as `fast`; the
official API still reports the obsolete `priority` name in responses (and
the ChatGPT backend only accepts `priority` on requests), so the pricing
lookup normalizes `priority` → `fast` and Fast mode sends the wire value
the target endpoint accepts (`fast` for API auth, `priority` for ChatGPT
auth). See
[Cost estimation](../../../../plugins/openai_responses/docs/development/cost-estimation.md).

### Documentation and tests

- Update `default_config/codex/README.md` with the import commit, dates, and
  family notes.
- Run documentation preparation and the normal MkDocs build after
  `config.json` changes when generated documentation is in scope.
- Add unit tests for model selection (model regex, `openai/` prefix,
  personality fallback, content distinctions, older-model regressions) under
  `application/python/tests/`.
- Prove end-to-end delivery with a real-API test (compiled instructions reach
  the request) and, for ChatGPT auth, a `manual_integration` test using the
  saved-login recording provider.
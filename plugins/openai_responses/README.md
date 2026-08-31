# openai_responses

OpenAI Responses API bundle for the AI Agent Platform.

Use it when you want an OpenAI-backed agent with:

- plain chat over the Responses API
- OpenAI API-key auth, ChatGPT auth, or automatic fallback between them
- streaming and non-streaming replies
- direct-send image attachments
- upload-before-send image/PDF attachments
- tool calling
- reasoning controls and surfaced reasoning metadata
- usage and cost metadata in message/UI output
- verbosity controls for supported models
- flex processing controls with configurable timeout and retries
- prompt caching controls with a session-owned cache key
- native conversation compaction for longer sessions

Most users can think of this as a single plugin bundle that adds OpenAI
Responses support to the app. The package name for installation is
`openai_responses`.

It can also be paired with the `chatgpt-auth-app` application plugin so
Responses requests can use a saved ChatGPT login against the ChatGPT-hosted
endpoint.

For implementation and maintenance details — model discovery, reasoning
controls, cost estimation, bundle layout, and the native compaction
specification — see the [development documentation](docs/development/index.md).

## Install

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/openai_responses[dev]"
```

## Environment

- `OPENAI_API_KEY` is required unless you pass `api_key` directly in provider
  config and use `auth_mode: "api"`, or use `auth_mode: "auto"` with a valid
  saved ChatGPT login.
- For local use in this repo, keeping `OPENAI_API_KEY` in the repo root `.env`
  is the simplest setup.
- Do not commit real API keys into configs or docs.

The provider defaults to `OPENAI_API_KEY` automatically, so `api_key` can be
omitted from config when the env var is present.

When `auth_mode: "chatgpt"` is selected, or when `auth_mode: "auto"` resolves
to ChatGPT because a valid saved login exists, the provider reads a saved
credential file instead of requiring `OPENAI_API_KEY`.

When credentials and network access are available, API-key mode fetches the
real OpenAI model list through the OpenAI Python SDK. For ChatGPT auth, the
provider merges three Codex-backed sources for model discovery:

- checked-in manual fallback models
- a checked-in Codex models snapshot
- the latest live Codex models catalog from GitHub

If discovery is unavailable, the UI falls back to manual text entry for
`model`.

## Quickstart

This is the smallest useful terminal/app-layer config when you want basic
Responses chat with the whole `openai_responses` bundle loaded from its plugin
descriptor.

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    "path:/absolute/path/to/plugins/openai_responses"
  ],
  "providers": {
    "openai": {
      "provider": "openai_responses",
      "model": "gpt-5-mini",
      "timeout": 60
    }
  },
  "agents": {
    "default": {
      "provider": "openai"
    }
  }
}
```

Run the terminal app:

```bash
cd application/python
python -m agent_terminal_app --console --config /path/to/config_openai_responses.json
```

In config-aware UIs, the provider will try to populate the `model` selector
from the appropriate live catalog. If that lookup fails, you can still type a
model id manually.

## ChatGPT auth quickstart

This is the smallest useful config for OpenAI Responses with ChatGPT login
support.

It assumes:

- the `chatgpt-auth-app` application plugin is loaded
- the system-message feature is loaded
- top-level `instructions` should come from the system-message feature rather
  than a provider-only `instructions` config key

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:/absolute/path/to/plugins/openai_responses",
    "path:/absolute/path/to/plugins/chatgpt-auth-app",
    "path:/absolute/path/to/plugins/feature-system-message"
  ],
  "providers": {
    "openai": {
      "provider": "openai_responses",
      "model": "gpt-5",
      "auth_mode": "auto",
      "system_message_as_instructions": true,
      "strip_leading_system_or_developer_message": true,
      "system_message": "You are a precise assistant.",
      "timeout": 120
    }
  },
  "application": {
    "chatgpt_auth": {}
  },
  "agents": {
    "default": {
      "provider": "openai"
    }
  }
}
```

Then:

1. Run the app or terminal client.
2. Use the `chatgpt_auth` application actions:
   - `Sign in with ChatGPT`
   - `Show ChatGPT login status`
   - `Cancel ChatGPT login`
   - `Log out of ChatGPT`
3. After login succeeds, `auth_mode: "auto"` will use ChatGPT-backed auth when
   available and fall back to API-key mode otherwise.

## Full bundle example

Reasoning request shaping depends on the request-options feature, and tool usage
depends on loading one or more tool plugins. This example shows the intended
combination.

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    "path:/absolute/path/to/plugins/openai_responses",
    "plugins.request_options_feature.RequestOptionsFeature",
    "plugins.math_tools.MathTools"
  ],
  "providers": {
    "openai": {
      "provider": "openai_responses",
      "model": "gpt-5-mini",
      "api_key": "${env:OPENAI_API_KEY}",
      "base_url": "https://api.openai.com/v1",
      "auth_mode": "api",
      "timeout": 120,
      "enable_flex_processing": false,
      "enable_fast_mode": false,
      "flex_timeout_seconds": 300,
      "enable_flex_retries": true,
      "flex_max_retries": 2,
      "attachment_upload_mode": "upload_before_send",
      "enable_prompt_cache_key": true,
      "enable_prompt_cache_retention_24h": false,
      "reasoning_effort": "minimal",
      "reasoning_summary": "concise",
      "verbosity": "high"
    }
  },
  "agents": {
    "default": {
      "provider": "openai"
    }
  }
}
```

What this enables:

- OpenAI Responses chat
- reasoning controls and reasoning metadata on assistant messages
- tool schema injection and tool-call handling
- usage and cost metadata
- GPT-5 verbosity controls
- flex processing controls for supported OpenAI accounts
- Fast mode controls for both API-key and ChatGPT-backed requests
- prompt caching settings plus a regenerate-key session action
- a native compaction session action for longer conversations

## ChatGPT auth mode

The bundle supports three auth modes:

- `api`
  - use `api_key` or `OPENAI_API_KEY`
  - use the normal OpenAI API base URL
- `chatgpt`
  - use saved ChatGPT login credentials
  - use the ChatGPT-hosted Responses endpoint
- `auto`
  - use ChatGPT when a valid saved login exists
  - otherwise fall back to API-key mode

Relevant keys:

- `auth_mode`
- `chatgpt_credentials_path`
- `chatgpt_base_url`
- `chatgpt_account_id`
- `chatgpt_client_version`
- `strip_leading_system_or_developer_message`

ChatGPT model discovery merges checked-in manual fallback models, a
checked-in Codex snapshot, and the live Codex GitHub catalog. See
[Model discovery](docs/development/model-discovery.md) for the precedence
rules, last-resort fallback, and the bare `gpt-5.6` alias.

Defaults:

- ChatGPT base URL defaults to `https://chatgpt.com/backend-api/codex`
- saved credentials default to `CONFIG_DIR/auth/chatgpt-auth.json` when the
  auth feature can discover `CONFIG_DIR` from runtime env

### Instructions path for ChatGPT mode

For the ChatGPT endpoint, the recommended shape is:

- set `system_message_as_instructions: true` on the provider config
- let the system-message feature compile the prompt into
  `state["request"]["instructions"]`
- avoid a provider-only `instructions` config key

This mirrors how Codex-style requests send top-level `instructions`.

### Migrating older sessions

If older session histories contain a leading provider-native `system` or
`developer` message from before top-level `instructions` were used, enable:

- `strip_leading_system_or_developer_message: true`

When enabled, the provider drops the first native message only if its role is
`system` or `developer` before sending the request.

## Features

### Tools

Load one or more tool plugins, and the bundle will pass their schemas to the
Responses API and surface tool calls/results in the normal tool loop.

### Image attachments

The bundle supports two attachment paths for images:

- direct send through Responses `input_image` items
- upload-before-send through the OpenAI Files API, followed by Responses `file_id` references

Direct-send image shapes:

- `multipartContent[].content.url` with `http://` or `https://` image URLs
- `multipartContent[].content.url` with `data:image/...` URLs
- `multipartContent[].content.data_base64` plus `mime_type`, which the provider
  converts into a `data:` URL before sending

When `attachment_upload_mode: "upload_before_send"` is enabled, inline image
attachments are uploaded first and then sent as `input_image` items using
OpenAI file references.

### PDF attachments

PDF attachments are supported only when
`attachment_upload_mode: "upload_before_send"` is enabled.

Supported PDF input shapes:

- `multipartContent[].content.url` with `data:application/pdf;base64,...`
- `multipartContent[].content.data_base64` plus `mime_type: "application/pdf"`

In this mode, the provider uploads the PDF through the OpenAI Files API and
sends the Responses request using an `input_file` item with a `file_id`
reference.

Explicit upload actions are still follow-up work for Stage 3.

When the package is loaded through its plugin path, it also exposes the
`openai_responses_attachments` provider extension. That extension:

- advertises upload UI for supported attachment types
- exposes `store_attachment`, `delete_attachment`, and `download_attachment`
  actions backed by the application-owned session asset store
- lets clients upload an attachment once, send it later via `asset_ref`, and
  download the same stored asset again from message history

### Reasoning

Reasoning controls are available through:

- `reasoning_effort`
- `reasoning_summary`

To use those options, also load
`plugins.request_options_feature.RequestOptionsFeature`.

When the reasoning extension is active, it also requests
`include: ["reasoning.encrypted_content"]` so OpenAI reasoning items can be
preserved in raw metadata for future native replay.

### Usage

Usage metadata is attached to assistant messages, including formatted prompt,
completion, cached-token, and cost fields. This is useful in the terminal UI
and other clients that render message footers or status bars.

API-backed turns label monetary values as `cost`. ChatGPT-backed turns use the
same configured API pricing tables for estimation and therefore label their
message-footer values as `estimated cost` and `estimated turn`.

### Prompt caching

Prompt caching controls are available through:

- `enable_prompt_cache_key`
- `prompt_cache_key`
- `enable_prompt_cache_retention_24h`

When prompt cache key support is enabled:

- new sessions automatically receive a generated session-owned key
- older sessions missing a key are repaired on first request
- forked sessions keep the same key by default
- users can manually edit the key through normal session settings
- users can regenerate the key through the `regenerate_prompt_cache_key` session action

By default, prompt cache key support is enabled when this extension is loaded.
Set `enable_prompt_cache_key: false` if you want to turn off automatic
session-owned key generation and request injection.

When the effective auth mode selects the ChatGPT endpoint:

- `prompt_cache_key` behavior remains available
- `prompt_cache_retention: "24h"` is suppressed automatically even if
  `enable_prompt_cache_retention_24h` is `true`

### Flex processing

Flex processing controls are available through:

- `enable_flex_processing`
- `flex_timeout_seconds`
- `enable_flex_retries`
- `flex_max_retries`

When flex processing is enabled, the extension writes request overrides so the
provider can apply `service_tier: "flex"`, the configured timeout, and the
configured retry policy on both streaming and non-streaming Responses calls.

When the effective auth mode selects the ChatGPT endpoint, flex processing is
disabled automatically even if the config flags are set. The ChatGPT-hosted
endpoint does not support this OpenAI API feature.

### Verbosity

`verbosity` controls the Responses `text.verbosity` option for supported
models. In the current implementation, that is enabled for models whose id
contains `gpt-5`.

### Native compaction

The bundle includes a session action that compacts provider-native history for
future Responses turns. This is intended for context maintenance, not for
producing a human-readable summary message.

## Configuration reference

Configuration is a flat dict shared across the provider and enabled extensions.

### Provider keys

- `provider`: must be `openai_responses` in app-layer provider config
- `model`: required model id
- `auth_mode`: optional, one of `api`, `chatgpt`, `auto`; defaults to `api`
- `api_key`: optional if `OPENAI_API_KEY` is set or ChatGPT auth is used
- `base_url`: optional, defaults to `https://api.openai.com/v1`
- `api_base_url`: optional explicit base URL for API-key mode
- `chatgpt_base_url`: optional, defaults to `https://chatgpt.com/backend-api/codex`
- `chatgpt_credentials_path`: optional path to saved ChatGPT credentials
- `chatgpt_account_id`: optional explicit ChatGPT account id override
- `chatgpt_client_version`: optional, used for ChatGPT `/models` discovery
- `strip_leading_system_or_developer_message`: optional compatibility flag for migrated sessions
- `compaction_model`: optional model id for native compaction; leave empty or omit it to use `model`
- `use_chatgpt_auth_for_compaction`: optional, defaults to `true`; set to `false` to force native compaction onto the API endpoint
- `use_compaction_placeholder_transcript`: optional, defaults to `false`; set to `true` to show compacted native ranges as a single visible placeholder message instead of rebuilding the compacted native output directly
- `timeout`: optional request timeout in seconds, defaults to `60`

### Attachment keys

- `attachment_upload_mode`: `direct` or `upload_before_send`; defaults to `direct`

Use `upload_before_send` when you want the provider to upload inline image or
PDF attachment data through the OpenAI Files API before the Responses request.
PDF support is only available in this mode.

### Flex processing keys

- `enable_flex_processing`: enable `service_tier: "flex"` for Responses calls
- `flex_timeout_seconds`: per-request timeout to apply when flex is enabled; defaults to `300`
- `enable_flex_retries`: enable request-scoped retries for flex calls; defaults to `true`
- `flex_max_retries`: max retry count when flex retries are enabled; defaults to `2`

Note: flex processing is ignored automatically when the effective auth mode
selects the ChatGPT endpoint.

### Fast mode

Fast mode applies `service_tier: "priority"` to Responses calls for both
API-key and ChatGPT auth modes. The control is:

- `enable_fast_mode`: enable `service_tier: "priority"` for Responses calls
  (applies to both API-key and ChatGPT auth modes)

The usage footer renders `tier: priority` when OpenAI reports that tier, and
cost estimation uses priority-tier pricing when the checked-in or manual
pricing data defines it. The footer also renders `mode: pro` when the
response reports `reasoning.mode: "pro"` (Pro reasoning mode, see below).

Pro reasoning mode (`reasoning_mode: "pro"`) is a nested reasoning control and
is independent of Fast mode's `service_tier: "priority"`. Both can be enabled
at the same time on GPT-5.6 models with API auth; they touch different parts of
the outbound payload and neither overwrites the other. Pro mode is API-only
(see "Pro mode billing" below for the auth-mode gating).

## Benchmark script

The repo includes a benchmark helper at
`plugins/openai_responses/benchmark/run_openai_responses_tier_matrix.py`.
See `plugins/openai_responses/benchmark/README.md` for the full benchmark and
snapshot-refresh tooling guide.

Useful options:

- `--model` or `--models`
- `--repeat`
- `--execution-mode sequential|parallel`
- `--run-scope api|chatgpt|both`
- `--desired-input-tokens`
- `--desired-output-tokens`

The script saves a text artifact under `artifacts/` containing:

- the benchmark configuration
- one section per model/tier/repeat run
- actual usage and duration metrics
- aggregate summaries per model/tier row

### Reasoning keys

These require `plugins.request_options_feature.RequestOptionsFeature` to be
loaded.

- `reasoning_effort`: model-specific effort value. Current UI options are:
  - GPT-5.6 Sol and Terra: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
  - GPT-5.6 Luna: `low`, `medium`, `high`, `xhigh`, `max` (no `ultra`)
  - GPT-5.2 and GPT-5.4 models: `none`, `low`, `medium`, `high`, `xhigh`
  - GPT-5.1 models: `none`, `low`, `medium`, `high`
  - GPT-5 models: `minimal`, `low`, `medium`, `high`
  - GPT-5 pro: `high`
  - unknown models: fallback UI shows `none`, `minimal`, `low`, `medium`,
    `high`, `xhigh` (no `max` or `ultra`)
- `reasoning_summary`: one of `auto`, `concise`, `detailed`
- `reasoning_mode`: optional string enum `["pro"]`, GPT-5.6 family only
  (Sol, Terra, Luna, and the bare `gpt-5.6` alias). API-only: hidden when
  `auth_mode` is `chatgpt`.
- `reasoning_context`: optional string enum `["auto", "current_turn",
  "all_turns"]`, GPT-5.6 family only.
- `show_reasoning_context_footer`: set to `false` to keep reasoning-context
  behavior and metadata while hiding its assistant-message footer.

See [Reasoning controls](docs/development/reasoning-controls.md) for the full
shaping rules, silent-drop behavior, metadata footers, Pro mode billing, and
the `request_options.reasoning.*` expert escape hatches.

### Verbosity keys

- `verbosity`: one of `low`, `medium`, `high`
- `show_verbosity_ui`: set to `false` to hide the verbosity selector in UI

Verbosity only activates when the selected model is tagged with
`supports_verbosity`. In the current implementation, that tag is added for
models whose id contains `gpt-5`.

### Usage keys

- `pricing_snapshot_path`: optional override for the checked-in pricing snapshot
- `show_usage`: set to `false` to hide usage footer/status UI elements
- `usage_message_footer_fields`: optional list that filters message-footer
  fields while preserving plugin-defined order. Supported values are `input`,
  `cached`, `cache_write`, `estimated_cached`, `completion`, `auth`, `tier`,
  `mode`, `cost`, `turn_cost`, `turn_reasoning`, `turn_input`, `turn_cached`,
  and `turn_output`. Omitting the key preserves the complete existing footer;
  an empty list hides message-level usage while allowing the status total.
- `show_usage_status_total`: set to `false` to hide cumulative cost from the
  chat status bar while retaining selected message-footer usage
- `show_estimated_cached_tokens`: set to `true` to show ChatGPT estimated cached-token footers
- `show_openai_auth_mode`: set to `true` to show the effective auth mode (`API` or `ChatGPT`) in usage footers

ChatGPT-backed Responses usage estimates cached tokens using turn-aware
heuristics. The usage extension also surfaces `usage_reasoning_mode` metadata
and a `mode: pro` footer entry when the response reports
`reasoning.mode: "pro"`. See [Cost estimation](docs/development/cost-estimation.md)
for the pricing snapshot format, token-bucket splitting, ChatGPT cached-token
estimation, and explicit cache boundaries.

### Prompt caching keys

- `enable_prompt_cache_key`: defaults to `true`; set to `false` to disable automatic session-owned prompt cache keys
- `prompt_cache_key`: optional manual cache key override shown in normal session settings UI
- `enable_prompt_cache_retention_24h`: set to `true` to send `prompt_cache_retention: "24h"`

Note: `enable_prompt_cache_retention_24h` is ignored automatically when the
effective auth mode selects the ChatGPT endpoint.

### Tools

Tool schemas come from loaded tool plugins such as `plugins.math_tools.MathTools`.

No extra config key is required beyond loading tools in the application.

### Native compaction

The bundle exposes an application-owned session action with id
`compact_native_history`. It starts native compaction in the background and
returns promptly, rewrites provider-native history after the provider call
completes, and rebuilds the visible transcript from the compacted native
output.

Users can compact the complete visible history, provide an explicit exclusive
end index, or invoke `Compact native history up to here` from an individual
message. The message-level action includes the selected message in the
compacted prefix and uses the same background operation.

While compaction runs, a dismissible warning banner reports the current phase
and elapsed time approximately every 15 seconds and offers a `Cancel compaction`
action. Canceling stops the operation; the session is not changed.

You cannot start compaction while a request is running for the same session,
and you cannot start a request while compaction is running.

Successful completion updates the session and leaves a dismissible success
banner. Provider, output-validation, and concurrent-history failures leave a
dismissible persistent error banner with a Retry action.

A successful compaction commit creates a full session snapshot immediately
before the compacted state is saved:

```text
Before compacting conversation [:277]
```

Cancellation, provider failure, application interruption, and conflicting
commits do not retain an automatic compaction snapshot. Automatic snapshots
are enabled by default and are not pruned or limited. See the
[session snapshot guide](../../application/python/docs/session-snapshots.md)
for storage, restoration, and manual deletion.

The synchronous provider-extension compatibility action remains available as
`compact_native_history_sync`, but it has no default UI element.

If you prefer the older placeholder-style transcript behavior, enable:

- `use_compaction_placeholder_transcript: true`

When enabled, compacted native segments are shown as a single visible
placeholder message and are expanded back into native compaction artifacts on
future requests.

The bundle also exposes a session action that toggles this view mode:

- `Collapse compacted messages`
- `Expand compacted messages`

The toggle appears only after the session contains compacted history. It
changes the visible projection only. Retained native history stays canonical
and is rebuilt using the updated session override.

By default, native compaction follows the same effective auth mode as normal
Responses requests, and the selected mode selects the upstream compaction
protocol (API-key uses the dedicated compact endpoint; ChatGPT uses remote
compaction v2 over the normal Responses endpoint). See the
[native compaction specification](docs/development/specifications/native-compaction/index.md)
for the full protocol, retained-history, and compatibility contract.

Set `use_chatgpt_auth_for_compaction: false` to force a ChatGPT-authenticated
session to use the API-key mode and its dedicated compact endpoint. This
requires `config.api_key` or `OPENAI_API_KEY`.

By default, compaction uses the same `model` as normal requests. Set
`compaction_model` to use a different model for the compaction API call, for
example:

```json
{
  "model": "gpt-5.5",
  "compaction_model": "gpt-5.4-mini"
}
```

The compacted native output shape is model-dependent. Both visible-message and
opaque-artifact shapes are valid as long as future requests continue from the
compacted native history.

Maintainers can find the complete protocol, compatibility, lifecycle, and
verification contract in the
[native compaction specification](docs/development/specifications/native-compaction/index.md).

The action no longer accepts a freeform `instructions` field. When the backend
requires top-level instructions, native compaction uses the same config-driven
system-message pipeline as normal requests:

- enable `system_message_as_instructions: true`
- set `system_message` as usual
- enable `strip_leading_system_or_developer_message: true` if older sessions
  still contain a persisted leading `system` or `developer` message

When `system_message_as_instructions: false`, native compaction follows the
same request-time message-injection path as a normal request. See the
[native compaction technical specification](docs/development/specifications/native-compaction/technical-spec.md)
for the input boundary, metadata stripping, and `compaction_summary` handling
details.

### Prompt caching session action

It exposes a session action with id `regenerate_prompt_cache_key` that replaces
the current session-owned prompt cache key without changing the visible
transcript.

## Capabilities and caveats

- API-key mode supports both non-streaming and streaming Responses requests.
- ChatGPT mode is streaming-only in the current implementation. Non-streaming
  requests fail with a clear error.
- The provider retains Responses-native history (including reasoning items
  with `encrypted_content`) so future turns can replay native items rather
  than flattening everything to plain chat text. This retained native history
  is what makes `reasoning.context: "all_turns"` effective on follow-up turns.
- Reasoning requests include `reasoning.encrypted_content` so raw reasoning can
  be preserved even when the model does not expose readable reasoning text.
- Verbosity support is model-gated and currently follows the provider tag check
  for `gpt-5` models.
- ChatGPT-backed requests use top-level `instructions` and `store: false`.
- Flex processing and prompt-cache retention are automatically disabled when
  the ChatGPT endpoint is selected.
- ChatGPT `/models` discovery is a last-resort fallback. See
  [Model discovery](docs/development/model-discovery.md) for details.
- Native compaction is intentionally different from human-readable summary
  insertion. It preserves provider-native compacted artifacts for future
  Responses requests instead of replacing history with a plain assistant
  summary. See the
  [native compaction specification](docs/development/specifications/native-compaction/index.md)
  for the protocol, compatibility, and lifecycle contract.

## Bundle layout

The bundle splits responsibilities across its provider and extensions
(transport, attachments, tools, reasoning, usage, verbosity, prompt caching,
ChatGPT auth, and native compaction). See
[Bundle layout](docs/development/bundle-layout.md) for the responsibility split
and the implementation classes registered by the bundle.

## Troubleshooting

- Authentication errors:
  check `OPENAI_API_KEY` in the repo root `.env`, set `api_key` in config, or
  verify the saved ChatGPT credential file exists when using `chatgpt` / `auto`.
- ChatGPT mode says streaming is required:
  use the streaming request path, or switch `auth_mode` to `api` / `auto`.
- ChatGPT requests behave oddly on older sessions:
  enable `system_message_as_instructions: true` and
  `strip_leading_system_or_developer_message: true`.
- Reasoning controls do nothing:
  make sure `plugins.request_options_feature.RequestOptionsFeature` is loaded.
- Verbosity control does not appear or has no effect:
  verify the model is tagged with `supports_verbosity`; today that means a
  `gpt-5` model id.
- Tool calls never appear:
  load at least one tool plugin and use a model/prompt that will actually call
  tools.
- Native compaction action is missing:
  make sure the active provider is `openai_responses` and the bundle was loaded
  from `path:/absolute/path/to/plugins/openai_responses` or equivalent.

## Tests

For contributors and local validation:

Run the fast default package suite:

```bash
pytest plugins/openai_responses/tests -q
```

This package defaults to `-m 'not integration and not manual_integration'`.

Run hosted API integration tests:

```bash
pytest plugins/openai_responses/tests -m 'integration and api and not slow_integration and openai' -q
```

Run manual ChatGPT-auth integration tests separately:

```bash
pytest plugins/openai_responses/tests -m 'manual_integration' -q
```

The OpenAI Responses test suite bootstraps the repo root `.env` during local
use in this repo and does not overwrite already-exported environment variables.
Hosted API tests typically require `OPENAI_API_KEY`. Manual integration tests
also require saved ChatGPT auth state.

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

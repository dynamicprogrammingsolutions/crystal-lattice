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
- `src/openai_responses_plugins/data/openai_chatgpt_manual_models.json`
  - checked-in ChatGPT-only fallback models and estimate-only pricing
  - pricing entries may define `pricing`, `service_tiers`, or both
  - used only when a model is missing from upstream sources
- `src/openai_responses_plugins/data/openai_codex_models.json`
  - checked-in offline snapshot of the public Codex model catalog
  - refresh it with `python plugins/openai_responses/benchmark/refresh_openai_responses_models.py`
  - used when live Codex fetching fails or when you want offline coverage from a recent repo update
  - current snapshot source commit: `50b82133850d940627cf307d77e280619bfafe25` (2026-07-17); includes `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`
- `chatgpt_account_id`
- `chatgpt_client_version`
- `strip_leading_system_or_developer_message`

ChatGPT model-discovery precedence (later sources override earlier per model id):

- checked-in manual fallback models (`openai_chatgpt_manual_models.json`)
- checked-in Codex snapshot (`openai_codex_models.json`)
- live Codex GitHub catalog (`openai/codex` `main` `codex-rs/models-manager/models.json`)

The live Codex catalog is the authoritative source. The checked-in snapshot is a
pinned fallback used when live GitHub access fails. Manual models only fill gaps
that neither upstream source publishes.

Last-resort fallback: the direct ChatGPT `/models` endpoint
(`https://chatgpt.com/backend-api/codex/models?client_version=...`) is only
contacted when both the live Codex fetch fails and the checked-in snapshot is
empty. When the snapshot is available, the ChatGPT `/models` endpoint is not
called. The endpoint has been observed to return an empty `models` list even
when upstream catalogs already list GPT-5.6, so tests and callers must not rely
on it as a primary discovery source.

The bare `gpt-5.6` alias is intentionally not published in the model picker.
OpenAI examples use `gpt-5.6` as a routing alias to `gpt-5.6-sol`, but the
authoritative Codex catalog publishes only the three explicit family IDs
(`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`). Users can still type `gpt-5.6`
manually in the model field; the API will route it, but the UI will not suggest
it as an option.

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
  (Sol, Terra, Luna, and the bare `gpt-5.6` alias). Absence means standard
  mode. When set to `"pro"`, the extension injects `reasoning.mode: "pro"`
  into the outbound request. The extension never sends `"mode": "standard"`
  because omission is the standard-mode signal and `standard` is the API
  default. **API-only**: the Pro mode UI control is shown only when
  `auth_mode` is `api` or `auto` (or unset, which defaults to `api`); it is
  hidden when `auth_mode` is `chatgpt`. The extension does not inject
  `reasoning.mode` when the effective auth mode resolves to `chatgpt`,
  matching the ChatGPT backend's actual behavior (it rejects
  `reasoning.mode: "pro"`). `reasoning_effort` and `reasoning_summary` are
  unaffected by auth mode and are still injected for ChatGPT auth.
- `reasoning_context`: optional string enum `["auto", "current_turn",
  "all_turns"]`, GPT-5.6 family only (Sol, Terra, Luna, and the bare
  `gpt-5.6` alias). Controls which available reasoning items the model can
  use on supported models:
  - `auto`: uses the selected model's default. Omitting `reasoning_context`
    has the same effect as `auto`. The extension normalizes `auto` to
    omission (no `context` key is injected), matching the official
    semantics and the existing `reasoning_mode` omission precedent.
  - `current_turn`: makes reasoning from the active turn available without
    rendering earlier-turn reasoning into the next sample.
  - `all_turns`: renders available, compatible reasoning items from
    earlier turns into the next sample. Only has an effect when earlier
    response reasoning items are available (via retained native history).
  On the first request, `current_turn` and `all_turns` behave the same
  because no earlier reasoning exists. `all_turns` does not create missing
  reasoning items; it only renders existing ones. The setting is silently
  dropped for non-GPT-5.6 models, matching the existing silent-drop
  behavior for unsupported `reasoning_effort` and `reasoning_mode`. Users
  who need to force a context value on an older reasoning model can set
  `request_options.reasoning.context` directly as an expert escape hatch;
  the config-level `reasoning_context` takes precedence over the raw
  `request_options.reasoning.context` when both are present. When
  `reasoning_context` is `auto` or unset, the raw
  `request_options.reasoning.context` is preserved.

The bare `gpt-5.6` alias is not published in the model picker (per the model
catalog decision), but if a user types it manually the reasoning extension
treats it as the Sol alias and offers the Sol effort set including `ultra`,
the Pro reasoning mode control, and the reasoning context control.

`ultra` is a multi-agent coordination mode: by default it coordinates four
agents and consumes substantially more tokens than `max` or lower effort
levels. It is not an efficiency mode. Use it only when the workflow demands
it, and prefer Sol (the cheapest `ultra`-capable model) for tests and
experiments.

`reasoning.mode` and `reasoning.effort` are independent: mode selects
standard or pro execution, while `reasoning.effort` controls how much
reasoning the model applies within that mode. If `reasoning_effort` is unset,
GPT-5.6 defaults to `medium` in both modes (per the official reasoning
guide).

No default `reasoning_effort`, `reasoning_mode`, or `reasoning_context` is
inferred. If the key is unset, no `effort`, `mode`, or `context` is injected
and the OpenAI API applies its own built-in default for the selected model.
Unsupported `reasoning_effort` values for the selected model are silently
dropped (no error is raised; the value is simply not injected).
`reasoning_mode: "pro"` is silently dropped for non-GPT-5.6 models, matching
the same silent-drop behavior. `reasoning_context: "current_turn"` or
`"all_turns"` is silently dropped for non-GPT-5.6 models. Users who need to
force an unsupported effort, mode, or context for an unknown model can set
`request_options.reasoning.effort`, `request_options.reasoning.mode`, or
`request_options.reasoning.context` directly as an expert escape hatch; the
config-level `reasoning_effort`, `reasoning_mode`, and `reasoning_context`
take precedence over the raw `request_options` values when both are present.

Assistant messages always expose the frontend-friendly field
`metadata.reasoning`. OpenAI-specific raw reasoning data is preserved under
`metadata.openai_responses_reasoning`. The effective reasoning context
reported by the response (if any) is preserved as
`metadata.openai_responses_reasoning.context` (one of `current_turn` or
`all_turns`). If the response does not report an effective context, the
`context` sub-key is absent (not fabricated). The effective context is also
surfaced as a `message_footer` UI element (`context: {{data}}`) that renders
`metadata.openai_responses_reasoning.context` under each assistant message
when present. The footer is conditionally rendered — it is hidden when the
response does not report an effective context, so it does not fabricate a
value.

#### Pro mode billing

Pro reasoning mode (`reasoning_mode: "pro"`) performs more model work than
standard mode and increases token usage and cost. Pro mode bills the
aggregated model-work tokens at the selected model's standard per-token
rates. There is no separate Pro-mode pricing table and no new
`service_tier` value for Pro mode.

Pro mode is **API-only**: the UI control is hidden when `auth_mode` is
`chatgpt`, and the extension does not inject `reasoning.mode` when the
effective auth mode resolves to ChatGPT. The ChatGPT backend rejects
`reasoning.mode: "pro"` with `reasoning.mode is not supported with this
model`, so the gating matches the backend's actual behavior rather than
sending a rejected field. Fast mode (`service_tier: "priority"`) applies
to both API and ChatGPT auth modes and is independent of Pro mode.

Cost estimation in this bundle continues to use the selected model's
standard-tier pricing entry from `data/openai_model_pricing.json` (or the
manual ChatGPT fallback). Pro mode does not introduce a priority-tier or
flex-tier price lookup. Priority-tier pricing applies only when Fast mode
reports `service_tier: "priority"`; Pro mode does not change the service
tier and does not trigger priority-tier pricing.

Existing Pro model IDs (e.g. `gpt-5.5-pro`, `gpt-5.4-pro`) keep their
current behavior and pricing; they are distinct model SKUs, not a
reasoning-mode billing category. "Pro mode" the reasoning setting is
distinct from "-pro" the model SKU suffix.

### Verbosity keys

- `verbosity`: one of `low`, `medium`, `high`
- `show_verbosity_ui`: set to `false` to hide the verbosity selector in UI

Verbosity only activates when the selected model is tagged with
`supports_verbosity`. In the current implementation, that tag is added for
models whose id contains `gpt-5`.

### Usage keys

- `pricing_snapshot_path`: optional override for the checked-in pricing snapshot
- `show_usage`: set to `false` to hide usage footer/status UI elements
- `show_estimated_cached_tokens`: set to `true` to show ChatGPT estimated cached-token footers
- `show_openai_auth_mode`: set to `true` to show the effective auth mode (`API` or `ChatGPT`) in usage footers

ChatGPT-backed Responses usage currently estimates cached tokens using
turn-aware heuristics. That estimate is kept separate from the raw provider
usage payload and is used for ChatGPT-mode pricing instead of any
backend-reported cached-token field. By default it is not displayed; enable
`show_estimated_cached_tokens` if you want the footer.

The estimator considers user boundaries and usage-bearing assistant or tool-call
generations; tool results are ignored. Within one user turn, the immediately
previous generation's input is the cached-prefix candidate. If that candidate
is larger than the current input, the prefix is considered invalidated by
compaction or another history change and the estimate is `0`.

For the first generation after a user message, the estimator compares the
current input with both the first and last inputs from the preceding populated
turn:

- if current input is strictly greater than the previous turn's last input,
  reasoning is treated as preserved and that last input is the estimate
- otherwise, the previous turn's first input is used as the conservative
  interleaved-reasoning estimate when it does not exceed current input
- if even that interleaved candidate exceeds current input, the prefix is
  considered invalidated and the estimate is `0`

The estimate is an observability and pricing heuristic, not a provider-reported
or billing-grade cache measurement. It does not expose the inferred
preserved/interleaved classification as metadata.

The reasoning extension contributes its own `message_footer` element for the
effective reasoning context (`context: all_turns` / `current_turn`),
parallel to the usage footers above. It renders only when
`metadata.openai_responses_reasoning.context` is present (see Reasoning keys).

The usage extension also surfaces `usage_reasoning_mode` metadata and a
`mode: pro` footer entry when the response reports `reasoning.mode: "pro"`.
This is additive to the existing `usage_service_tier` / `tier: priority`
footer for Fast mode. Standard mode is the default and is not shown.

#### Pricing snapshot and cost estimation

The checked-in pricing snapshot at
`src/openai_responses_plugins/data/openai_model_pricing.json` is the
runtime source of truth for estimated dollar cost. It is refreshed from
the official OpenAI pricing page via
`python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py`.

Each model entry has a top-level `pricing` block (the standard-tier
projection) and a `service_tiers` mapping with per-tier rates. The
supported tiers are `standard`, `batch`, `flex`, and `priority`. Each
tier pricing block has up to four token-price columns:

- `input_per_1m`: ordinary input tokens (dollars per 1M tokens)
- `cached_input_per_1m`: cached-read tokens (cache hits)
- `cache_write_per_1m`: billable cache-write tokens (GPT-5.6+; omitted on
  legacy models)
- `output_per_1m`: output/completion tokens

The cost estimator splits `usage.input_tokens` into three mutually
exclusive input buckets so the same token is never charged twice:

```text
cached_read_tokens    = max(0, usage.input_tokens_details.cached_tokens)
cache_write_tokens    = max(0, usage.input_tokens_details.cache_write_tokens)
ordinary_input_tokens = max(0, input_tokens - cached_read_tokens - cache_write_tokens)
```

The estimated cost is:

```text
estimated = (
    ordinary_input_tokens * input_per_1m
  + cached_read_tokens   * cached_input_per_1m
  + cache_write_tokens   * cache_write_per_1m
  + output_tokens        * output_per_1m
) / 1_000_000.0
```

When `cache_write_tokens > 0` but the resolved pricing block has no
`cache_write_per_1m` (e.g., a legacy model with only three price columns),
the estimator falls back to `input_per_1m` for the cache-write bucket so
the model remains estimable.

When the reported detail counters are inconsistent (their sum exceeds
`input_tokens`), the estimator reduces the larger counter to fit and
clamps `ordinary_input_tokens` to zero. This keeps cost estimation
deterministic and non-negative without rejecting the whole payload.

GPT-5.6 implicit caching can create a billable managed cache write even
when the client does not add an explicit cache breakpoint. The estimator
uses the reported `cache_write_tokens` counter; it does not infer write
tokens from prompt shape, cache keys, or estimated cache hits.

#### ChatGPT cost estimate caveat

ChatGPT users are generally governed by subscription limits/rate limits
rather than direct API per-token billing. The dollar value produced by
this framework is an **API-equivalent estimate** useful for comparison,
not an invoice amount.

For ChatGPT-backed requests:

- Cached-read tokens are estimated using the turn-aware heuristic
  described above; the estimate replaces `cached_tokens` for pricing.
- `cache_write_tokens` is **not** synthesized from the estimate. When the
  ChatGPT backend reports `cache_write_tokens`, the estimator prices it at
  the cache-write rate. When the backend omits `cache_write_tokens`, the
  estimate cannot include cache-write cost and reports only ordinary +
  cached-read + output. The usage footer explicitly reports when the
  write counter is absent.
- `service_tier: "default"` resolves to standard pricing;
  `service_tier: "priority"` (Fast mode) resolves to priority pricing.

#### Explicit cache boundaries

Explicit cache-boundary support (`prompt_cache_options`,
`prompt_cache_breakpoint`) is intentionally unsupported for the current
use case. The framework relies on implicit caching and the
session-owned `prompt_cache_key`.

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
`compact_native_history`. It starts native compaction in the background,
returns a standard successful action result with
`operation_status: "accepted"` promptly, rewrites provider-native history
after the provider call completes, and rebuilds the visible transcript from
the compacted native output.

While compaction runs, a persistent nondismissible warning banner reports the
current phase and elapsed time approximately every 15 seconds. Its
`Cancel compaction` action cancels the async OpenAI HTTP task and revokes
commit authority. The process still checks cancellation immediately before
its reconciled session save so a late result cannot be applied.

Ordinary requests and compaction use the same session operation admission.
Starting either while the other is active is rejected before provider work.
Successful completion leaves a dismissible success banner. Provider,
output-validation, and concurrent-history failures leave a dismissible
persistent error banner with a Retry action.
The successful notification requests `ui_effects.reload_session_ids` for the
compacted session, so connected frontends refresh a mounted transcript without
opening or navigating to another session.
The invalidation remains pending for inactive or later-mounted cache consumers
until an authoritative reload succeeds. Dismissing the completion notification
does not repeat the reload.

The synchronous provider-extension compatibility action remains available as
`compact_native_history_sync`, but it has no default UI element. Both paths
share the same native compaction backend.

If you prefer the older placeholder-style transcript behavior, enable:

- `use_compaction_placeholder_transcript: true`

When enabled, compacted native segments are shown as a single visible
placeholder message and are expanded back into native compaction artifacts on
future requests.

The bundle also exposes a session action that toggles this view mode:

- `Collapse compacted messages`
- `Expand compacted messages`

The action changes the visible projection only. Retained native history stays
canonical and is rebuilt using the updated session override.

By default, native compaction follows the same effective auth mode as normal
Responses requests. The selected mode also selects the upstream compaction
protocol:

- API-key mode uses the dedicated, non-streaming
  `POST /v1/responses/compact` API.
- ChatGPT mode uses remote compaction v2 over the normal streamed
  `POST /backend-api/codex/responses` endpoint. The request appends a
  `compaction_trigger` item and expects one encrypted `compaction` output item.

Remote compaction v2 retains eligible user, system, and developer input
messages client-side before the returned encrypted compaction item. The trigger
itself is transient and is not stored in session history.

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

The compacted native output shape is model-dependent. Some models return
visible compacted assistant messages alongside opaque compaction artifacts;
others return only the retained visible user messages plus opaque compaction
state. Both shapes are valid as long as future requests continue from the
compacted native history.

Maintainers can find the complete protocol, compatibility, lifecycle, and
verification contract in the
[native compaction specification](docs/development/specifications/native-compaction/index.md).

The action no longer accepts a freeform `instructions` field. When the backend
requires top-level instructions, native compaction now uses the same
config-driven system-message pipeline as normal requests:

- enable `system_message_as_instructions: true`
- set `system_message` as usual
- enable `strip_leading_system_or_developer_message: true` if older sessions
  still contain a persisted leading `system` or `developer` message

When `system_message_as_instructions: false`, native compaction also follows
the same request-time message-injection path as a normal request:

- if `state["request"]["messages"]` is the effective outbound message set,
  compaction uses that rendered message list as its compact input
- `_metadata` is stripped from outbound compact input
- if the compacted output preserves the leading `system` or `developer`
  message, the stored native history restores the original retained version of
  that message, including template-form content and `_metadata`
- when a retained `compaction_summary` item is present, the visible rebuilt
  transcript surfaces it as a clear assistant placeholder message instead of
  letting that native item drift into unrelated later message ownership

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
  is what makes `reasoning.context: "all_turns"` effective on follow-up turns:
  the API renders the earlier reasoning items into the next sample. No second
  conversation-state mechanism is needed — the existing native replay already
  satisfies the API's "manually replaying the complete response history"
  requirement.
- Reasoning requests include `reasoning.encrypted_content` so raw reasoning can
  be preserved even when the model does not expose readable reasoning text.
- Verbosity support is model-gated and currently follows the provider tag check
  for `gpt-5` models.
- ChatGPT-backed requests use top-level `instructions` and `store: false`.
- Flex processing and prompt-cache retention are automatically disabled when
  the ChatGPT endpoint is selected.
- ChatGPT `/models` discovery is a last-resort fallback, only contacted when
  both the live Codex catalog fetch fails and the checked-in Codex snapshot is
  empty. It may still require `client_version`; if discovery is unavailable,
  pin `model` explicitly in config.
- Native compaction is intentionally different from human-readable summary
  insertion. It preserves provider-native compacted artifacts for future
  Responses requests instead of replacing history with a plain assistant
  summary.

## Native compaction behavior

Native compaction is meant for Responses-native context maintenance, not
transcript summarization.

- It can compact the full native history or a visible prefix.
- It uses the OpenAI Python SDK rather than application-layer summary logic.
- It uses `compaction_model` when configured, otherwise it uses the normal
  request `model`.
- It rebuilds visible messages after compaction directly from the compacted
  native output, whose visible assistant/user shape may vary by model.
- If `use_compaction_placeholder_transcript: true` is enabled, it instead
  shows the compacted region as a single placeholder message in the visible
  transcript while still preserving the underlying retained native compaction
  artifacts.
- Future requests continue from the compacted native history.

## Bundle layout

If you are extending or debugging the bundle, the responsibilities are split
like this:

- provider: transport, SDK calls, Responses-native conversion, and native
  history replay
- attachments: attachment upload policy/UI plus PDF composer UI
- tools: tool schema injection and tool-call reconstruction
- reasoning: reasoning request shaping and reasoning metadata
- usage: usage formatting and pricing metadata
- verbosity: `text.verbosity` request shaping
- prompt caching: `prompt_cache_key` / retention request shaping and session-key lifecycle
- ChatGPT auth feature: saved-credential loading plus `api` / `chatgpt` /
  `auto` auth-mode selection
- native compaction: shared backend, application-owned background action and
  process, plus synchronous provider-extension compatibility adapter

Implementation classes registered by the bundle:

- `openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider`
- `openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension`
- `openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature`
- `openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension`
- `openai_responses_plugins.openai_responses_fast_mode_extension.OpenAIResponsesFastModeExtension`
- `openai_responses_plugins.openai_responses_native_compaction_app.OpenAIResponsesNativeCompactionAppPlugin`
- `openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension`
- `openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension`
- `openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension`
- `openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension`
- `openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension`
- `openai_responses_plugins.openai_responses_verbosity_extension.OpenAIResponsesVerbosityExtension`

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

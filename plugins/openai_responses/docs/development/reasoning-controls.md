# Reasoning controls

This page describes how the `openai_responses` reasoning extension shapes
`reasoning.effort`, `reasoning.mode`, and `reasoning.context` in outbound
Responses requests, and how it surfaces reasoning metadata on assistant
messages.

Loading `plugins.request_options_feature.RequestOptionsFeature` is required
for the reasoning config keys to take effect.

## Config keys

- `reasoning_effort`: model-specific effort value.
- `reasoning_summary`: one of `auto`, `concise`, `detailed`.
- `reasoning_mode`: optional string enum `["pro"]`, GPT-5.6 family only.
- `reasoning_context`: optional string enum `["auto", "current_turn",
  "all_turns"]`, GPT-5.6 family only.

## Per-model effort sets

Current UI options for `reasoning_effort`:

- GPT-5.6 Sol and Terra: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
- GPT-5.6 Luna: `low`, `medium`, `high`, `xhigh`, `max` (no `ultra`)
- GPT-5.2 and GPT-5.4 models: `none`, `low`, `medium`, `high`, `xhigh`
- GPT-5.1 models: `none`, `low`, `medium`, `high`
- GPT-5 models: `minimal`, `low`, `medium`, `high`
- GPT-5 pro: `high`
- unknown models: fallback UI shows `none`, `minimal`, `low`, `medium`,
  `high`, `xhigh` (no `max` or `ultra`)

## `reasoning_mode` (Pro mode)

`reasoning_mode` accepts an optional string enum `["pro"]` and applies to the
GPT-5.6 family only (Sol, Terra, Luna, and the bare `gpt-5.6` alias). Absence
means standard mode. When set to `"pro"`, the extension injects
`reasoning.mode: "pro"` into the outbound request.

The extension never sends `"mode": "standard"` because omission is the
standard-mode signal and `standard` is the API default.

### Auth-mode gating

Pro mode is **API-only**: the UI control is shown only when `auth_mode` is
`api` or `auto` (or unset, which defaults to `api`); it is hidden when
`auth_mode` is `chatgpt`. The extension does not inject `reasoning.mode` when
the effective auth mode resolves to `chatgpt`, matching the ChatGPT backend's
actual behavior (it rejects `reasoning.mode: "pro"` with
`reasoning.mode is not supported with this model`).

`reasoning_effort` and `reasoning_summary` are unaffected by auth mode and are
still injected for ChatGPT auth.

### Relationship to `reasoning.effort`

`reasoning.mode` and `reasoning.effort` are independent: mode selects standard
or pro execution, while `reasoning.effort` controls how much reasoning the
model applies within that mode. If `reasoning_effort` is unset, GPT-5.6
defaults to `medium` in both modes (per the official reasoning guide).

## `reasoning_context`

`reasoning_context` controls which available reasoning items the model can use
on supported GPT-5.6 models:

- `auto`: uses the selected model's default. Omitting `reasoning_context` has
  the same effect as `auto`. The extension normalizes `auto` to omission (no
  `context` key is injected), matching the official semantics and the existing
  `reasoning_mode` omission precedent.
- `current_turn`: makes reasoning from the active turn available without
  rendering earlier-turn reasoning into the next sample.
- `all_turns`: renders available, compatible reasoning items from earlier
  turns into the next sample. Only has an effect when earlier response
  reasoning items are available (via retained native history).

On the first request, `current_turn` and `all_turns` behave the same because
no earlier reasoning exists. `all_turns` does not create missing reasoning
items; it only renders existing ones.

### Expert escape hatch

Users who need to force a context value on an older reasoning model can set
`request_options.reasoning.context` directly as an expert escape hatch; the
config-level `reasoning_context` takes precedence over the raw
`request_options.reasoning.context` when both are present. When
`reasoning_context` is `auto` or unset, the raw
`request_options.reasoning.context` is preserved.

The same escape hatch applies to `request_options.reasoning.effort` and
`request_options.reasoning.mode`.

## Silent drops

No default `reasoning_effort`, `reasoning_mode`, or `reasoning_context` is
inferred. If a key is unset, no `effort`, `mode`, or `context` is injected and
the OpenAI API applies its own built-in default for the selected model.

Unsupported values are silently dropped for the selected model rather than
raising an error:

- unsupported `reasoning_effort` values are not injected;
- `reasoning_mode: "pro"` is silently dropped for non-GPT-5.6 models;
- `reasoning_context: "current_turn"` or `"all_turns"` is silently dropped for
  non-GPT-5.6 models.

This matches the existing silent-drop behavior for unsupported
`reasoning_effort` values.

## `ultra` effort

`ultra` is a multi-agent coordination mode: by default it coordinates four
agents and consumes substantially more tokens than `max` or lower effort
levels. It is not an efficiency mode. Use it only when the workflow demands
it, and prefer Sol (the cheapest `ultra`-capable model) for tests and
experiments.

## Metadata and footers

Assistant messages always expose the frontend-friendly field
`metadata.reasoning`. OpenAI-specific raw reasoning data is preserved under
`metadata.openai_responses_reasoning`.

The effective reasoning context reported by the response (if any) is
preserved as `metadata.openai_responses_reasoning.context` (one of
`current_turn` or `all_turns`). If the response does not report an effective
context, the `context` sub-key is absent (not fabricated).

The reasoning extension contributes a `message_footer` element for the
effective reasoning context (`context: all_turns` / `current_turn`). It
renders only when `metadata.openai_responses_reasoning.context` is present.
The footer is conditionally rendered — it is hidden when the response does not
report an effective context, so it does not fabricate a value.

## Pro mode billing

Pro reasoning mode (`reasoning_mode: "pro"`) performs more model work than
standard mode and increases token usage and cost. Pro mode bills the
aggregated model-work tokens at the selected model's standard per-token
rates. There is no separate Pro-mode pricing table and no new `service_tier`
value for Pro mode.

Cost estimation continues to use the selected model's standard-tier pricing
entry from `data/openai_model_pricing.json` (or the manual ChatGPT fallback).
Pro mode does not introduce a fast-tier or flex-tier price lookup.
Priority-tier pricing applies only when Fast mode reports
`service_tier: "fast"`; Pro mode does not change the service tier and
does not trigger fast-tier pricing.

Fast mode (the fast processing tier; wire value `service_tier: "fast"`
for API auth and the legacy `service_tier: "priority"` name for ChatGPT
auth, whose backend rejects `"fast"`) applies to both API and ChatGPT auth
modes and is independent of Pro mode.

### Pro mode vs Pro model SKUs

Existing Pro model IDs (e.g. `gpt-5.5-pro`, `gpt-5.4-pro`) keep their current
behavior and pricing; they are distinct model SKUs, not a reasoning-mode
billing category. "Pro mode" the reasoning setting is distinct from "-pro"
the model SKU suffix.

## Reasoning metadata footers

The usage extension surfaces `usage_reasoning_mode` metadata and a
`mode: pro` footer entry when the response reports `reasoning.mode: "pro"`.
This is additive to the existing `usage_service_tier` / `tier: fast`
footer for Fast mode. Standard mode is the default and is not shown.
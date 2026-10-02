# Model discovery

This page describes how the `openai_responses` bundle discovers models for
API-key and ChatGPT auth modes, and how the model picker is populated.

## API-key mode

When credentials and network access are available, API-key mode fetches the
real OpenAI model list through the OpenAI Python SDK. If discovery is
unavailable, the UI retains the searchable dropdown with an empty catalog and
validated custom model IDs.

## ChatGPT auth mode

ChatGPT mode merges three Codex-backed sources for model discovery. Later
sources override earlier per model id:

1. checked-in manual fallback models
   (`src/openai_responses_plugins/data/openai_chatgpt_manual_models.json`);
2. checked-in Codex snapshot
   (`src/openai_responses_plugins/data/openai_codex_models.json`);
3. the latest live Codex models catalog from GitHub
   (`openai/codex` `main` `codex-rs/models-manager/models.json`).

The live Codex catalog is the authoritative source. The checked-in snapshot is
a pinned fallback used when live GitHub access fails. Manual models only fill
gaps that neither upstream source publishes.

### Refreshing the Codex snapshot

Refresh the checked-in Codex snapshot with:

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_models.py
```

The current snapshot source commit is recorded in the snapshot itself. It
includes the GPT-6 family (`gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`), the
explicit GPT-5.6 family IDs (`gpt-5.6-sol`, `gpt-5.6-terra`,
`gpt-5.6-luna`), and the hidden daybreak models
(`gpt-daybreak-blue-latest`, `gpt-daybreak-red-latest`); the retired
`gpt-5.2`, `gpt-5.4-mini`, and `gpt-5.4` entries are no longer listed.

### Last-resort fallback

The direct ChatGPT `/models` endpoint
(`https://chatgpt.com/backend-api/codex/models?client_version=...`) is only
contacted when both the live Codex fetch fails and the checked-in snapshot is
empty. When the snapshot is available, the ChatGPT `/models` endpoint is not
called.

The endpoint has been observed to return an empty `models` list even when
upstream catalogs already list GPT-5.6, so tests and callers must not rely on
it as a primary discovery source. It may still require `client_version`; if
discovery is unavailable, pin `model` explicitly in config.

## Bare `gpt-5.6` alias

The bare `gpt-5.6` alias is intentionally not published in the model picker.
OpenAI examples use `gpt-5.6` as a routing alias to `gpt-5.6-sol`, but the
authoritative Codex catalog publishes only the three explicit family IDs
(`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`).

Users can still type `gpt-5.6` manually in the model field; the API will route
it, but the UI will not suggest it as an option. When a user types it
manually, the reasoning extension treats it as the Sol alias and offers the
Sol effort set including `ultra`, the Pro reasoning mode control, and the
reasoning context control.
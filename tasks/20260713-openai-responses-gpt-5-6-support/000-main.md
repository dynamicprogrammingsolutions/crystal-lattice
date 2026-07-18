# OpenAI Responses GPT-5.6 Support

Add complete GPT-5.6 Sol, Terra, and Luna support to the OpenAI Responses provider, including model discovery, reasoning controls, pricing, and Codex-specific system instructions. Keep the six implementation areas independently completable, with documentation and API-versus-ChatGPT verification owned by each subtask.

## Task checklist

- [x] `tasks/20260713-openai-responses-gpt-5-6-support/010-refresh-model-catalog.md`
- [x] `tasks/20260713-openai-responses-gpt-5-6-support/020-add-reasoning-effort-levels.md`
- [x] `tasks/20260713-openai-responses-gpt-5-6-support/030-add-reasoning-pro-mode.md`
- [ ] `tasks/20260713-openai-responses-gpt-5-6-support/040-add-reasoning-context.md`
- [x] `tasks/20260713-openai-responses-gpt-5-6-support/050-update-pricing-and-cost-estimation.md`
- [ ] `tasks/20260713-openai-responses-gpt-5-6-support/060-add-gpt56-codex-system-instructions.md`
- [ ] `tasks/20260713-openai-responses-gpt-5-6-support/070-programmatic-tool-calling.md`

## Investigation snapshot

Research was performed on July 13, 2026.

Official and upstream sources:

- OpenAI launch page: `https://openai.com/index/gpt-5-6/`
- OpenAI reasoning guide: `https://developers.openai.com/api/docs/guides/reasoning`
- OpenAI pricing page: `https://developers.openai.com/api/docs/pricing`
- Secondary release summary supplied by the user:
  `https://www.digitalapplied.com/blog/gpt-5-6-sol-terra-luna-public-ga`
- OpenAI Codex repository: `../codex`
- Latest inspected Codex upstream commit:
  `2f7d89b1419bf7064346855b0acde23514b1ebc5`
  from `2026-07-13T05:02:52Z`

The Codex checkout had unrelated untracked files, so upstream was fetched and
inspected through `origin/main` without moving the local branch or modifying the
working tree.

Codex upstream already contains:

- `gpt-5.6-sol`
- `gpt-5.6-terra`
- `gpt-5.6-luna`

Important upstream model parameters:

| Model | Default reasoning | Supported reasoning |
| --- | --- | --- |
| `gpt-5.6-sol` | `low` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-terra` | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-luna` | `medium` | `low`, `medium`, `high`, `xhigh`, `max` |

All three Codex entries advertise a 372,000-token context window, API support,
parallel tool calls, low default verbosity, and priority/Fast service-tier
support. Sol and Terra support `ultra`; Luna does not.

## ChatGPT-path findings

The saved login requested for future implementation testing currently exists at:

`~/.crystal/auth/chatgpt-auth.json`

At investigation time it contained a usable access token and refresh token and
was valid through July 18, 2026. No token or account values were printed.

Current ChatGPT model discovery behavior:

1. `OpenAIResponsesProvider.get_models()` validates the saved ChatGPT login.
2. It then prefers the public Codex GitHub `models.json`.
3. It merges manual models, the checked-in Codex snapshot, and the live Codex
   catalog, with later sources taking precedence.
4. The ChatGPT backend `/models` endpoint is only used if the live Codex fetch
   fails and no checked-in snapshot is available.

A live diagnostic using the saved login returned nine merged models and already
included all three GPT-5.6 family IDs. The direct ChatGPT `/models` endpoint
returned an empty `models` list at the time of investigation. Therefore, GPT-5.6
is already visible in ChatGPT mode because of live Codex catalog discovery, not
because the checked-in snapshot or ChatGPT `/models` fallback is current.

Current ChatGPT pricing behavior was also checked with a real one-turn
`gpt-5.6-luna` request:

- the request completed successfully;
- usage metadata was returned;
- effective auth mode was `chatgpt`;
- reported service tier was `default`;
- estimated cached tokens were `0` on the first request;
- estimated cost was `0.0`, with no formatted cost.

The zero cost is a provider defect caused by the missing GPT-5.6 pricing entry.
ChatGPT pricing displayed by this framework is an API-equivalent token-cost
estimate, not an assertion that the user's ChatGPT subscription is billed that
dollar amount.

## Cross-cutting ChatGPT test requirements

Each subtask must add or update a dedicated ChatGPT integration test instead of
assuming API-authenticated behavior is identical.

ChatGPT tests must:

- use the existing saved-login convention with a configurable state directory;
- be runnable with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
    <other task-specific environment> \
    pytest <task-specific-test> \
      -m "manual_integration and integration and openai" -q
  ```

- resolve credentials as
  `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`;
- never print access tokens, refresh tokens, ID tokens, account IDs, or emails;
- report the exact path and reason if credentials are missing, malformed,
  expired, cannot be refreshed, or are rejected;
- treat a skipped credential-gated test as **not run**, not as successful
  verification;
- use `~/.crystal` during implementation verification as explicitly requested;
- keep API-key integration tests separate and report them independently if
  `OPENAI_API_KEY` is unavailable;
- avoid silently converting an unexpected ChatGPT rejection into a passing
  result. Use an intentional `xfail` only after confirming and documenting a
  real endpoint capability difference.

The current `~/.crystal/dev-cli-venv` has runtime dependencies but did not have
`pytest` during investigation. Implementation should use an environment with the
plugin dev dependencies installed, for example:

```bash
python -m pip install -e core/python
python -m pip install -e application/python
python -m pip install -e "plugins/openai_responses[dev]"
```

Only install the application package for subtasks that exercise default
configuration or `AgentApplication`.

## General completion rules

For every subtask:

- add regression-focused unit tests before or with implementation;
- add separate API and ChatGPT integration coverage where the feature reaches
  the wire;
- run the relevant non-integration plugin suite;
- update `plugins/openai_responses/README.md` and any feature-specific docs;
- update generated default-config documentation when default config changes;
- preserve existing behavior for older OpenAI models;
- record exact commands, pass/fail counts, and credential/API gating in
  `## Completion Notes`;
- do not count skipped gated tests as passes.

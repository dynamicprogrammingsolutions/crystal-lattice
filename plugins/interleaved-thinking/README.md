# Interleaved Thinking

Provider extension for the OpenAI-compatible provider that omits thinking
blocks from previous assistant turns when building a request.

## What it does

When enabled, every outgoing request strips prior-turn thinking in both
forms it appears in:

- `<think>...</think>` segments inside assistant message content (models
  that interleave thinking directly in content, for example through
  Ollama).
- `reasoning` / `reasoning_content` fields on assistant messages (the
  separate-field form used by Z.ai GLM and other OpenAI-compatible
  providers).

The session history itself is never modified — only the request payload.
The current turn's thinking is unaffected.

## Why it exists

"Preserve previous-turn thinking" is otherwise provider-dependent:
Ollama has no request-side setting for it, and providers differ in whether
prior thinking even round-trips. Including or excluding this plugin makes
the switch uniform:

| Plugin | Previous-turn thinking in requests |
| --- | --- |
| included | omitted, on every OpenAI-compatible provider |
| excluded | the provider's default behavior |

The task-guidance evaluation suite uses it as the preserve-thinking
switch for its producer variants.

## Usage

Add the plugin to an agent configuration that uses the
`reference_openai_compatible` provider:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/interleaved-thinking"
  ]
}
```

## Tests

```bash
python -m pip install -e "plugins/interleaved-thinking[dev]"
pytest plugins/interleaved-thinking/tests -q
```

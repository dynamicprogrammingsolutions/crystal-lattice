# OpenAI Inspection Proxy

This local development proxy forwards OpenAI-compatible or Anthropic HTTP
requests while printing their request and response bodies. It is useful for
checking the effective developer/system message, tool definitions, and request
options sent by a coding agent.

Long strings are replaced in the main JSON view with numbered
`LONG_TEXT_*` references and printed in full below the request. Repeated long
strings retain the same number.

## Install

From the repository root:

```bash
npm --prefix tools/openai-proxy ci
```

## Start the Proxy

The command accepts a target endpoint, local port, optional local base path,
and optional authentication, delay, and logging flags:

```text
node tools/openai-proxy/proxy.js <endpoint> <port> [base-path] \
  [--hide-headers] [--require-api-key-env NAME] [--delay-ms N]
```

OpenAI-compatible example:

```bash
node tools/openai-proxy/proxy.js \
  https://api.openai.com/v1 \
  3000 \
  /v1 \
  --hide-headers
```

Configure the agent to use this provider base URL:

```text
http://127.0.0.1:3000/v1
```

Anthropic example:

```bash
node tools/openai-proxy/proxy.js \
  https://api.anthropic.com \
  3000 \
  /v1 \
  --hide-headers
```

Configure the agent's Anthropic base URL as:

```text
http://127.0.0.1:3000
```

The exact environment variable or configuration field for a provider base URL
depends on the agent.

The health endpoint reports the selected target and path:

```bash
curl http://127.0.0.1:3000/health
```

## JSON-configured mode

Configured mode keeps operational values in JSON and secrets in named
environment variables:

```bash
node tools/openai-proxy/proxy.js \
  --config tools/openai-proxy/deploy/ireland/config/reviewer-proxy.json
```

JSON can configure the listener, upstream and base path, incoming and outgoing
API-key environment names, allowed models and service tiers, response status
codes, delay, logging, budget, cooldown, pricing, long-context rules, request
serialization, and persistent state. Existing positional commands remain
supported.

`models.request_overrides` applies configurable endpoint-specific top-level
request values. Endpoint keys replace `/` with `_`; for example,
`chat_completions` can set `{"reasoning_effort": "none"}` without changing
`/responses`.

Budget mode reads Responses or Chat Completions usage from JSON and streaming
SSE completions, prices ordinary input, cached input, and output separately,
and atomically persists the ledger. The threshold-crossing request completes;
later controlled requests receive `429` plus `Retry-After` until the configured
cooldown expires.

## API-Key-Protected Ollama Proxy

The embedded iOS runtime proof of concept uses the proxy as a small
OpenAI-compatible boundary in front of Ollama. Keep the client-facing key in an
environment variable and require it explicitly:

```bash
export CRYSTAL_PROXY_API_KEY="replace-with-a-random-review-key"
node tools/openai-proxy/proxy.js \
  http://127.0.0.1:11434/v1 \
  3000 \
  /v1 \
  --hide-headers \
  --require-api-key-env CRYSTAL_PROXY_API_KEY
```

Clients send:

```text
Authorization: Bearer <the configured review key>
```

When required authentication is enabled, the proxy:

- returns `401` before forwarding a missing or incorrect key;
- compares the bearer value using a timing-safe comparison;
- redacts authorization values from logs even without `--hide-headers`;
- removes the client authorization header before forwarding to Ollama.

Use `--delay-ms N` to add a bounded delay before forwarding a request when
testing mobile background behavior. The delay is test support; it does not
replace or modify model output.

The Ireland Compose example supplies self-signed TLS termination, model
filtering, separate caller/upstream credentials, cost limiting, and body/header
logging controls. Operators remain responsible for monitoring, credential
rotation, and retention.

## Inspect a Request

1. Start the proxy.
2. Point the agent's provider base URL at the local proxy.
3. Submit a prompt through the agent.
4. Find `=== Incoming Request ===` in the proxy output.
5. Inspect the JSON body and the expanded `LONG_TEXT_*` fields.

Developer/system instructions may appear in a top-level `instructions` field
or in a system/developer message, depending on the provider protocol.

The proxy forwards requests to the configured target, including streaming
requests. Stop it with <kbd>Ctrl</kbd>+<kbd>C</kbd>.

## Tests

Run the parser, logging, and local forwarding tests with:

```bash
npm --prefix tools/openai-proxy test
```

The integration cases start local target and proxy processes. They verify that
hidden mode logs only `Headers: [hidden]` while authorization and custom
headers still reach the target, and that default mode retains header logging.

## Headers, Credentials, and Private Content

Use `--hide-headers` when request headers are not needed for diagnosis. The
flag replaces all incoming request-header names and values with a fixed
`Headers: [hidden]` marker. It changes only logging: the original headers are
still forwarded to the provider.

This is a recommendation, not a security boundary. You control the process and
its output on your computer and remain responsible for:

- credentials sent through the proxy;
- the selected provider endpoint;
- access to terminal output and saved logs;
- prompts, source code, file paths, conversations, and other private content
  in request and response bodies.

Without `--hide-headers`, the proxy prints all incoming headers, which may
include authorization tokens and provider-specific API keys. Even with the
flag, bodies remain visible. Review and sanitize captured output before
sharing it.
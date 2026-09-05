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
and optional `--hide-headers` flag:

```text
node tools/openai-proxy/proxy.js <endpoint> <port> [base-path] [--hide-headers]
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
# WebFetch Tool Investigation Notes

Status: initial public-success, redirect, invalid-localhost, and timeout fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/web-fetch/success-text-file.json`
- `plugins/claude-tools/investigation/fixtures/web-fetch/success-html-page.json`
- `plugins/claude-tools/investigation/fixtures/web-fetch/success-redirect-different-host.json`
- `plugins/claude-tools/investigation/fixtures/web-fetch/error-invalid-private-url.json`
- `plugins/claude-tools/investigation/fixtures/web-fetch/error-timeout.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/web-fetch/`.

## Tool Name

Claude Code advertises the fetch tool as:

```text
WebFetch
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `WebFetch`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["url", "prompt"]`
- `additionalProperties`: `false`

## Result Formatting

Successful text fetch returns the requested prompt result directly as a plain string.

Observed text-file result:

```text
RFC 2606 reserves `.test`, `.example`, `.invalid`, and `.localhost` top-level domains for testing, documentation examples, invalid name construction, and loopback purposes respectively.
```

Observed HTML-page result:

```text
This passage depicts Perth, a grim, patient blacksmith aboard the Pequod, who lost both feet and his idyllic life due to alcoholism, now silently toiling to repair whaling equipment.
```

Redirect to a different host does not auto-follow. Claude returns a special redirect block:

```text
REDIRECT DETECTED: The URL redirects to a different host.

Original URL: https://www.iana.org/domains/example
Redirect URL: http://www.iana.org/help/example-domains
Status: 301 Moved Permanently

To complete your request, I need to fetch content from the redirected URL. Please use WebFetch again with these parameters:
- url: "http://www.iana.org/help/example-domains"
- prompt: "return a one-line summary only"
```

## Error Formatting

Invalid localhost/private-style URL:

```text
Invalid URL
```

Observed timeout:

```text
timeout of 60000ms exceeded
```

The timeout case is a real Claude harness result from a public URL (`https://example.org`), not a synthetic local failure.

## Implementation Direction

- Implement `WebFetch` as an Anthropic-native Claude tool, not an OpenAI-first function tool.
- Keep the public schema and result shape identical to Claude Code.
- Reuse the shared `web-fetch-shared` engine for HTTP fetch, extraction, truncation, and caching where possible.
- Add a Claude-specific wrapper for:
  - automatic `http://` to `https://` upgrade before fetch
  - redirect-across-host handling with the observed special message instead of auto-following
  - Claude-compatible invalid-URL and timeout result strings
  - prompt-driven summarization result as a plain string
- Treat authenticated/private URLs as unsupported in the Claude-shaped layer even if other vendor fetch tools can access localhost or private hosts directly.
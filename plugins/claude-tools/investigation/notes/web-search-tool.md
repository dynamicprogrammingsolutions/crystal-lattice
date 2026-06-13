# WebSearch Tool Investigation Notes

Status: initial real-search success, domain-filter parameter, and validation-error fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/web-search/success-basic.json`
- `plugins/claude-tools/investigation/fixtures/web-search/success-allowed-domains.json`
- `plugins/claude-tools/investigation/fixtures/web-search/success-blocked-domains.json`
- `plugins/claude-tools/investigation/fixtures/web-search/error-query-too-short.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/web-search/`.

## Tool Name

Claude Code advertises the search tool as:

```text
WebSearch
```

## Schema

The committed fixtures contain the full observed schema and description. Implementation should match:

- `name`: `WebSearch`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["query"]`
- `additionalProperties`: `false`
- optional arrays:
  - `allowed_domains`
  - `blocked_domains`

## Result Formatting

Successful search returns a single plain-text block sent back to the model. The block has three parts:

1. A header line:

```text
Web search results for query: "example domain"
```

2. A `Links:` line containing JSON-like `[{title,url}, ...]` objects.
3. A prose summary followed by:

```text
REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
```

This reminder is part of the actual tool result, not just the schema description.

## Error Formatting

Too-short query validation returns:

```text
<tool_use_error>InputValidationError: [
  {
    "origin": "string",
    "code": "too_small",
    "minimum": 2,
    "inclusive": true,
    "path": [
      "query"
    ],
    "message": "Too small: expected string to have >=2 characters"
  }
]</tool_use_error>
```

## Observed Domain-Filter Behavior

Claude Code passes `allowed_domains` and `blocked_domains` through in the tool input when explicitly instructed.

In the captured real runs for query `example domain`, the returned result set still included domains outside the requested allow/block lists. That means one of these is true:

- the Claude server-side search backend treats these filters as advisory rather than strict
- the backend has a bug or partial enforcement
- the filter semantics are broader/narrower than simple hostname equality

The fixture set records this observed behavior rather than guessing intent.

## Investigation Setup

No extra setup was required to capture real Claude `WebSearch` responses in this environment. The Claude harness produced live search results through the same local proxy/Ollama setup used for the other tool investigations.

This is different from the eventual local implementation, which will need provider credentials:

- `GEMINI_API_KEY` for Gemini-backed search
- `TAVILY_API_KEY` for Tavily-backed search

## Implementation Direction

- Keep the public `WebSearch` schema and response shape identical to Claude Code.
- Implement the backend in the shared/plugin layer using the existing structured providers from `tool_compat_shared.web_search_engine`.
- Offer at least:
  - Gemini-backed search via `GeminiApiProvider`
  - Tavily-backed search via `TavilyProvider`
- Build a Claude-specific formatter that converts provider results into the observed plain-text block:
  - header line
  - `Links:` JSON-like list
  - prose summary
  - mandatory `REMINDER:` tail
- Apply domain filters in the Claude tool layer so the shape remains Claude-compatible even if provider APIs differ.
- Decide explicitly whether to preserve Claude's apparently weak filter enforcement or tighten it. The safer product default is to enforce filters strictly in our own layer while documenting that this is a small intentional divergence from the captured server behavior.
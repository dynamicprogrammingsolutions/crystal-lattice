# 120 - Web Search Tools (All Vendors)

Short description: Add vendor-compatible web search tools to `gemini-tools`, `qwen-tools`, and `kimi-tools` (Grok has no web search tool). Gemini's tool uses the Gemini SDK with Google Search grounding and citation formatting, disabled when no API key is provided. Qwen supports configurable search providers. Kimi uses the Moonshot Search API with optional page crawling. A shared search result model and formatting helpers live in `tool-compat-shared`.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/110-web-fetch-tools.md` (shares `web-fetch-shared` for `include_content` page crawling)

## Goal

Add one tool type (web search) across three vendor packages. Each vendor exposes its own tool name, parameter names, search backend, and result formatting. The shared helpers provide a common search result data model, citation formatting, and provider abstraction.

Key requirements:
1. **Gemini `google_web_search`**: real SDK-backed implementation using Gemini API with Google Search grounding. Requires a Gemini API key; **disabled via `SkipThisTool` when no key is provided.**
2. **Kimi `SearchWeb`**: uses Moonshot Search API with optional server-side page crawling. **Disabled when no Moonshot search config is available** (raises `SkipThisTool`).
3. **Qwen `web_search`**: supports configurable search providers (Dashscope, Tavily, Google). Available when a provider is configured.

## Public package outcome

1. `plugins/gemini-tools/`
- `GeminiWebSearchTool` (tool name: `google_web_search`)
2. `plugins/qwen-tools/`
- `QwenWebSearchTool` (tool name: `web_search`)
3. `plugins/kimi-tools/`
- `KimiSearchWebTool` (tool name: `SearchWeb`)

**No changes to `plugins/grok-tools/`** — Grok CLI has no web search tool.

## Key source references

### Gemini

- Web search tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/web-search.ts:247` (`class WebSearchTool`)
  - API call: `geminiClient.generateContent({model: 'web-search'}, [{role: 'user', parts: [{text: query}]}], signal, LlmRole.UTILITY_TOOL)`.
  - Grounding metadata extraction: `response.candidates?.[0]?.groundingMetadata`.
  - Source formatting: `groundingChunks` → `[N] Title (url)` entries.
  - Citation insertion: `groundingSupports` → inline `[N]` markers at byte positions using `TextEncoder`/`TextDecoder` (UTF-8 byte offsets).
  - Result prefix: `"Web search results for \"query\":\n\n<content>\n\nSources:\n[1] ..."`.

### Qwen

- Web search base provider:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/base-provider.ts`
- Provider implementations:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/providers/dashscope-provider.ts`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/providers/tavily-provider.ts`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/providers/google-provider.ts`
- Types:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/types.ts`
- Utils:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/utils.ts`
- Main export:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-search/index.ts:281` (`class WebSearchTool`)
- Tool names:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts:25` (`WEB_SEARCH: 'web_search'`, `WebSearch: 'WebSearch'`)

### Kimi

- SearchWeb implementation:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/search.py` (`class SearchWeb`)
  - API call: `POST` to `config.services.moonshot_search.base_url` with `{"text_query": query, "limit": limit, "enable_page_crawling": include_content, "timeout_seconds": 30}`.
  - Result model: `SearchResult = {site_name, title, url, snippet, content, date, icon, mime}`.
  - Per-result formatting: `"Title: X\nDate: Y\nURL: Z\nSummary: W\n\n"` + optional `"Content: ...\n\n"` for crawled pages.
  - Results separated by `"---\n\n"`.
  - Conditional: raises `SkipThisTool` when `config.services.moonshot_search` is None.
  - Headers: `Authorization: Bearer {api_key}`, `X-Msh-Tool-Call-Id: {tool_call_id}`.
- Description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/search.md`

## Compatibility findings

### Three distinct search architectures

| Aspect | Gemini | Qwen | Kimi |
|--------|--------|------|------|
| Tool name | `google_web_search` | `web_search` | `SearchWeb` |
| Query param | `query` | `query` | `query` |
| Provider param | (none — Google only) | `provider?` (Dashscope/Tavily/Google) | (none — Moonshot only) |
| Limit param | (none) | (none) | `limit` (1-20, default 5) |
| Content crawl param | (none) | (none) | `include_content` (bool) |
| Backend | Gemini API (server-side Google Search) | Configurable HTTP provider | Moonshot Search API |
| Citation support | Yes (inline + footer) | TBD (verify) | No |
| Conditional | Requires Gemini API key | Requires provider config | Requires Moonshot config |

### Gemini `google_web_search`: real implementation with grounding

Gemini CLI's web search uses the Gemini API's Google Search grounding:

1. Calls the Gemini API with the `web-search` model alias and the user's query.
2. The API performs a Google Search server-side and returns the response with grounding metadata.
3. `groundingMetadata.groundingChunks` contains source entries: `{web: {title, uri}}`.
4. `groundingMetadata.groundingSupports` contains citation positions: `{segment: {startIndex, endIndex}, groundingChunkIndices: [N, ...]}`.
5. Citation markers `[N]` are inserted at UTF-8 byte positions in the response text.
6. A `Sources:\n[N] Title (url)\n...` footer is appended.

Our implementation must replicate this using the `google-genai` Python SDK with Google Search grounding enabled. This requires a Gemini API key.

### Kimi's `SearchWeb` has the richest schema

Kimi's search tool includes:
- `limit`: number of results (1-20, default 5).
- `include_content`: whether to crawl and include full page content (token-expensive).
- Per-result data: `title`, `date`, `url`, `snippet`, `content`, `site_name`, `icon`, `mime`.
- Distinct formatting: `"Title: ...\nDate: ...\nURL: ...\nSummary: ...\n\n"` per result, separated by `"---\n\n"`.

### Qwen has a provider abstraction

Qwen supports multiple search providers via a protocol/interface:
- `DashscopeProvider`
- `TavilyProvider`
- `GoogleProvider`

Each provider implements a `search(query) -> results` method. The tool selects the provider based on configuration.

The shared helpers should define a `SearchProvider` protocol so all three vendors can be represented as providers, and future providers can be added.

## Proposed shared internals

### In `tool-compat-shared` (lightweight — data models + formatting)

1. **Search result data model**:
   ```python
   @dataclass
   class SearchResult:
       title: str
       url: str
       snippet: str
       content: str = ""
       date: str = ""
       site_name: str = ""
   ```

2. **Citation formatting** (Gemini-specific):
   - `format_citations(text, grounding_chunks, grounding_supports) -> str`
   - Inserts inline `[N]` markers at byte positions.
   - Appends `Sources:\n[N] Title (url)` footer.

3. **Search result formatting** (per-vendor):
   - `format_gemini_search_result(query, text, sources) -> str`
   - `format_kimi_search_result(results, limit) -> dict`
   - `format_qwen_search_result(results) -> str` (verify from source during implementation)

### In `web-fetch-shared` (optional — for `include_content` crawling)

Kimi's `include_content=True` triggers server-side page crawling. Our implementation can use `web-fetch-shared`'s HTTP fetch + extraction helpers for client-side crawling when the Moonshot service is unavailable:

- `crawl_url_content(url) -> str` — fetches and extracts content from a URL.

### Search provider protocol

Define a `SearchProvider` protocol in `tool-compat-shared`:

```python
class SearchProvider(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[SearchResult]: ...
```

Each vendor's tool wraps a concrete provider:
- Gemini: `GeminiSearchProvider` (uses `google-genai` SDK with grounding).
- Qwen: `DashscopeSearchProvider`, `TavilySearchProvider`, `GoogleSearchProvider`.
- Kimi: `MoonshotSearchProvider` (uses Moonshot Search API).

## Response formatting requirement

### Gemini

- **Success**: `"Web search results for \"query\":\n\n<content with [N] citation markers>\n\nSources:\n[1] Title (url)\n[2] Title (url)\n..."`.
- **No results**: `"No search results or information found for query: \"query\""`.
- **Error**: `"Error during web search for query \"query\": ..."`.

Citation markers use UTF-8 byte positions from `groundingSupports`. This is critical for correct formatting — the insertion positions are byte offsets, not character offsets.

### Kimi

- **Per-result formatting**:
  ```
  Title: Example Page
  Date: 2024-01-15
  URL: https://example.com
  Summary: This is a brief summary of the page content.

  Content: Full page content when include_content=True...
  ```
- **Result separator**: `"---\n\n"`.
- **No results**: `"No matches found"` (from `ToolResultBuilder`).
- **Service not configured**: `"Search service is not configured. You may want to try other methods to search."`.
- **Service failure**: `"Failed to search. Status: N. This may indicates that the search service is currently unavailable."`.

### Qwen

- TBD — verify exact formatting from source during implementation.

## Behavior requirements

### Gemini (`google_web_search`)

1. Tool name: `google_web_search`. Param: `query` (required).
2. Calls Gemini API with Google Search grounding enabled.
3. Extracts grounding metadata from response.
4. Formats citations: inline `[N]` markers at UTF-8 byte positions + `Sources:` footer.
5. Result prefixed with `"Web search results for \"query\":\n\n"`.
6. **Disabled when no Gemini API key** — raises `SkipThisTool` in `init()`.

### Qwen (`web_search`)

1. Tool name: `web_search`. Params: `query` (required), `provider` (optional).
2. Uses configured search provider (Dashscope/Tavily/Google).
3. Provider selection based on config.
4. Result formatting: TBD (verify from source during implementation).

### Kimi (`SearchWeb`)

1. Tool name: `SearchWeb`. Params: `query` (required), `limit` (default 5, 1-20), `include_content` (default False).
2. Calls Moonshot Search API with `text_query`, `limit`, `enable_page_crawling`.
3. Parses response into `SearchResult` objects.
4. Formats results with Kimi-specific per-result template.
5. **Disabled when no Moonshot search config** — raises `SkipThisTool` in `init()`.
6. API key resolution supports OAuth ref.

## Test plan

### Schema tests

1. Assert exact tool names and params per vendor.
2. Gemini: `query` only.
3. Qwen: `query` + optional `provider`.
4. Kimi: `query` + `limit` + `include_content`.

### Search result formatting tests

1. Gemini: citation markers inserted at correct positions.
2. Gemini: `Sources:` footer with correct `[N] Title (url)` format.
3. Gemini: UTF-8 byte offset handling for multi-byte characters.
4. Kimi: per-result formatting matches template.
5. Kimi: result separator `"---\n\n"`.
6. Kimi: `include_content=True` includes content block.

### Conditional availability tests

1. Gemini: no API key → `SkipThisTool` raised.
2. Kimi: no Moonshot config → `SkipThisTool` raised.
3. Qwen: no provider config → verify behavior (may be always available with a default, or may raise).

### Error handling tests

1. API call failure → vendor-specific error message.
2. Empty query → validation error.
3. No results → vendor-specific no-results message.

### Integration tests

1. Each package loads through plugin manager.
2. Mock API response tests for all three vendors.
3. OpenRouter integration tests (one per vendor with cheap model, or mocked search API).

## Deliverables

1. Shared search result model and formatting helpers in `tool-compat-shared`.
2. `SearchProvider` protocol in `tool-compat-shared`.
3. Three vendor-specific web search tool classes.
4. Optional: `include_content` crawling integration with `web-fetch-shared`.
5. Package exports, manifests, and READMEs updated.
6. Tests for schema, formatting, conditional availability, and integration.

## Documentation follow-up

After implementation, update each vendor package README with:

1. Exposed web search tool name and parameters.
2. API key / configuration requirements per vendor.
3. Provider configuration for Qwen.
4. Known limitations (no browser rendering, rate limits, API quotas).

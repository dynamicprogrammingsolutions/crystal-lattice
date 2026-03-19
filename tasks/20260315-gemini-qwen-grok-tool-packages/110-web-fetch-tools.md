# 110 - Web Fetch Tools (All Vendors)

Short description: Add vendor-compatible URL content fetching tools to `gemini-tools`, `qwen-tools`, and `kimi-tools` (Grok has no web fetch tool). Gemini's tool uses the Gemini SDK with API-backed server-side fetch and grounding, disabled when no API key is provided. Qwen's and Kimi's tools use local HTTP fetching with optional LLM-based summarization. A separate `web-fetch-shared` package isolates heavy HTTP/extraction dependencies.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Goal

Add one tool type (URL content fetching) across three vendor packages (Gemini, Qwen, Kimi). Each vendor exposes its own tool name, parameter names, and fetch strategy. The shared work lives in a new `plugins/web-fetch-shared/` package to avoid adding heavy HTTP/extraction dependencies to `tool-compat-shared`.

Key requirements:
1. **Gemini web_fetch**: real SDK-backed implementation using Gemini API for server-side URL fetch with grounding. Falls back to local HTTP + LLM summarization when API fetch fails. **Disabled via `SkipThisTool` when no Gemini API key is provided.**
2. **LLM-based summarization**: both Gemini (fallback path) and Qwen use LLM calls to summarize fetched web content. This is feasible and required — the shared package must provide a summarization helper.
3. **Kimi FetchURL**: local HTTP fetch with trafilatura extraction and optional Moonshot fetch service fallback.

## Public package outcome

1. `plugins/gemini-tools/`
- `GeminiWebFetchTool` (tool name: `web_fetch`)
2. `plugins/qwen-tools/`
- `QwenWebFetchTool` (tool name: `web_fetch`)
3. `plugins/kimi-tools/`
- `KimiFetchURLTool` (tool name: `FetchURL`)

**No changes to `plugins/grok-tools/`** — Grok CLI has no web fetch tool.

## New shared package: `plugins/web-fetch-shared/`

A dedicated shared package for HTTP fetching, HTML extraction, and LLM summarization helpers. This isolates heavy dependencies (`trafilatura`, `aiohttp`) from `tool-compat-shared`.

This package is **not a public plugin package** (no `agent_plugin.json` tool entries). It is a library dependency for vendor packages that need web fetching.

**Dependencies**: `trafilatura`, `aiohttp`, and any LLM provider integration needed for summarization.

## Key source references

### Gemini

- Web fetch tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/web-fetch.ts:171` (`class WebFetchTool`)
  - Primary path: Gemini API call with URL grounding via `geminiClient.generateContent({model: 'web-fetch'}, ...)`.
  - Fallback path: local HTTP fetch + HTML→text + LLM summarization via `geminiClient.generateContent({model: 'web-fetch-fallback'}, ...)`.
  - Content type handling: text/markdown passthrough, text/html → html-to-text conversion, image/video/pdf → base64 inline data.
  - GitHub URL normalization: `convertGithubUrlToRaw()` converts `github.com/.../blob/...` to `raw.githubusercontent.com/...`.
  - Size limits: `MAX_EXPERIMENTAL_FETCH_SIZE`, `MAX_CONTENT_LENGTH`, `URL_FETCH_TIMEOUT_MS`.
  - Citation formatting: inline `[N]` markers from `groundingSupports`, `Sources:\n[N] Title (url)` footer from `groundingChunks`.
  - Rate limiting: per-host rate limit enforcement.
  - Private IP detection: falls back to local fetch for private/localhost URLs.
- Schema text:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:365` (`web_fetch` schema)

### Qwen

- Web fetch tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-fetch.ts:200` (`class WebFetchTool`)
  - Direct fetch path: HTTP GET → html-to-text conversion → LLM call with `prompt` + fetched content for summarization.
  - LLM summarization: `geminiClient.generateContent([{role: 'user', parts: [{text: fallbackPrompt}]}], {}, signal, model)` where `fallbackPrompt` includes user instructions + fetched content.
  - GitHub URL normalization: same blob → raw conversion.
  - Content limit: `MAX_CONTENT_LENGTH = 100000`.

### Kimi

- FetchURL implementation:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/fetch.py` (`class FetchURL`)
  - Primary path: Moonshot fetch service (`POST` with `{"url": url}`, returns markdown).
  - Fallback path: local HTTP GET → trafilatura extraction (`trafilatura.extract()` with `include_comments=True`, `include_tables=True`, `include_formatting=False`, `output_format="txt"`).
  - Auto-detection of text/plain vs text/markdown content types for passthrough.
  - Service configuration: `config.services.moonshot_fetch` with `base_url`, `api_key`, `oauth`, `custom_headers`.
- Description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/fetch.md`

## Compatibility findings

### Three distinct fetch strategies

| Aspect | Gemini | Qwen | Kimi |
|--------|--------|------|------|
| Tool name | `web_fetch` | `web_fetch` | `FetchURL` |
| URL param | `prompt` (URLs inline) | `url` (explicit) | `url` (explicit) |
| Instructions param | `prompt` (inline) | `prompt` (separate) | (none) |
| Primary backend | Gemini API server-side fetch | Local HTTP + LLM summarization | Moonshot fetch service |
| Fallback backend | Local HTTP + LLM summarization | (same as primary) | Local HTTP + trafilatura |
| Extraction library | `html-to-text` | `html-to-text` | `trafilatura` |
| Content limit | `MAX_CONTENT_LENGTH` (verify) | 100000 chars | `DEFAULT_MAX_CHARS` (50K from ToolResultBuilder) |
| Citation support | Yes (grounding metadata) | No | No |
| Conditional availability | Requires Gemini API key | Always | Always (Moonshot config optional) |

### Gemini web_fetch: real implementation, not a stub

Gemini CLI's `web_fetch` uses the Gemini API's built-in URL grounding capability:

1. **Primary path**: Sends the user's `prompt` (containing URLs and instructions) to the Gemini API with the `web-fetch` model alias. The API fetches URLs server-side and returns processed content with grounding metadata.
2. **Grounding metadata**: Response includes `groundingMetadata.groundingChunks` (source titles/URLs) and `groundingMetadata.groundingSupports` (citation index positions in the response text).
3. **Citation formatting**: Inline `[N]` markers are inserted at the character positions indicated by `groundingSupports`. A `Sources:\n[N] Title (url)` footer is appended.
4. **Fallback**: When primary fails (private IP, API error, no usable content), falls back to local HTTP fetch → html-to-text → LLM summarization.

Our implementation must replicate both paths using the `google-genai` Python SDK. The SDK supports grounding via `tools=[{"google_search": {}}]` or equivalent configuration. This requires a Gemini API key.

### API key gating

The Gemini web_fetch tool must check for a Gemini API key during `init()`. If no key is available (from plugin config or `GEMINI_API_KEY` environment variable), the tool should raise `SkipThisTool` to disable itself gracefully. This matches the pattern Kimi already uses for `SearchWeb` and `ReadMediaFile`.

### LLM-based summarization is required and feasible

Both Gemini (fallback) and Qwen use LLM calls to summarize fetched content:

- **Gemini fallback**: Fetches URL content locally, constructs a prompt with user instructions + raw content, calls `geminiClient.generateContent()` with the `web-fetch-fallback` model alias.
- **Qwen**: Fetches URL content locally via HTTP, converts HTML→text, constructs a prompt with user's `prompt` param + extracted content, calls the LLM.

Our shared package must provide a `summarize_fetched_content()` helper:

```python
async def summarize_fetched_content(
    content: str,
    user_prompt: str,
    *,
    provider_config: dict | None = None,
    max_summary_length: int = 100000,
) -> str:
    """Summarize fetched web content using an LLM.

    If no LLM provider is configured, returns the raw content with a prefix note.
    """
```

The provider for summarization can be configured via plugin config. If no provider is available, fall back to returning raw extracted text with a note like `"[LLM summarization unavailable; returning raw extracted content]"`.

### Kimi's trafilatura extraction is the best shared seed

Kimi's `FetchURL` uses `trafilatura.extract()` with these options:
- `include_comments=True`
- `include_tables=True`
- `include_formatting=False`
- `output_format="txt"`
- `with_metadata=True`

This produces high-quality text extraction. The shared package should use trafilatura as the primary extraction engine (rather than `html-to-text` used by Gemini/Qwen), with configuration options for extraction behavior.

## Proposed shared internals for `web-fetch-shared`

### New module: `web_fetch_engine.py`

1. **HTTP fetch**:
   - `fetch_url(url, *, timeout, headers, max_size, user_agent) -> FetchResult`
   - `FetchResult = {content: str, content_type: str, status_code: int, headers: dict}`
   - Streaming response with size limit enforcement.
   - Retry with backoff (configurable).

2. **HTML→text extraction**:
   - `extract_text(html, content_type, *, include_comments, include_tables, include_formatting) -> str`
   - Uses trafilatura for HTML, passthrough for text/plain and text/markdown.
   - Markdown content type passthrough.

3. **GitHub URL normalization**:
   - `normalize_github_url(url) -> str`
   - Converts `github.com/.../blob/...` → `raw.githubusercontent.com/...`.

4. **Private IP detection**:
   - `is_private_url(url) -> bool`
   - For deciding primary vs fallback fetch path.

5. **LLM summarization**:
   - `summarize_fetched_content(content, user_prompt, *, provider_config, max_length) -> str`
   - Constructs a summarization prompt and calls the configured LLM provider.
   - Falls back to raw content if no provider is available.

6. **Content limits and truncation**:
   - `truncate_content(content, max_chars, truncation_marker) -> str`

7. **Result formatting helpers**:
   - `format_gemini_web_fetch_result(text, sources, grounding_supports) -> str`
   - `format_qwen_web_fetch_result(summary, url) -> str`
   - `format_kimi_fetch_url_result(content, content_type) -> dict`

## Response formatting requirement

### Gemini

- **Primary path success**: Response text with inline citation markers `[N]` inserted at grounding support positions, plus `Sources:\n[1] Title (url)\n[2] ...` footer.
- **Primary path no results**: `"No search results or information found for query: \"...\""` (note: Gemini's web_fetch returns search-style results for URL prompts).
- **Fallback success**: LLM-summarized text content.
- **Fallback failure**: `"Error during fallback fetch for URL: ..."` or `"Error: ..."`.

### Qwen

- **Success**: LLM-summarized text from `prompt` + fetched content. Message: `"Content from URL processed successfully."`.
- **Failure**: `"Error during fetch for URL: ..."`.

### Kimi

- **Service fetch success**: Extracted markdown content. Message: `"The returned content is the main content extracted from the page."`.
- **Text/plain passthrough**: Raw content. Message: `"The returned content is the full content of the page."`.
- **Extraction failure**: `"Failed to extract meaningful content from the page. This may indicate the page content is not suitable for text extraction, or the page requires JavaScript to render its content."`.
- **Network error**: `"Failed to fetch URL due to network error: ..."`.

Implementation pattern: shared helpers produce vendor-neutral intermediate results; vendor wrappers apply vendor-specific formatting.

## Behavior requirements

### Gemini (`web_fetch`)

1. Tool name: `web_fetch`. Param: `prompt` (required, contains URLs + instructions, up to 20 URLs).
2. Parses URLs from `prompt` text.
3. Primary path: calls Gemini API with URL grounding enabled.
4. Formats response with inline citations and source footer.
5. Private IP URLs: falls back to local HTTP fetch.
6. Primary failure (no content, no sources): falls back to local fetch + LLM summarization.
7. GitHub URL normalization applied before fetch.
8. Content type handling: text/markdown passthrough, HTML→text conversion, image/video/pdf → base64 (if feasible in tool result).
9. Rate limiting: per-host rate limit enforcement (best-effort).
10. **Disabled when no Gemini API key** — raises `SkipThisTool` in `init()`.

### Qwen (`web_fetch`)

1. Tool name: `web_fetch`. Params: `url` (required), `prompt` (required).
2. Local HTTP fetch → HTML→text conversion → LLM call with `prompt` + content.
3. GitHub URL normalization applied.
4. Private IP handling: same behavior (direct fetch).
5. Content limit: 100000 chars after extraction.

### Kimi (`FetchURL`)

1. Tool name: `FetchURL`. Param: `url` (required).
2. Primary path: Moonshot fetch service (if configured).
3. Fallback path: local HTTP GET → trafilatura extraction.
4. Text/plain and text/markdown content types: passthrough (no extraction).
5. Other content types: trafilatura extraction with configured options.
6. No LLM summarization step (Kimi returns raw extracted text).

## Test plan

### Schema tests

1. Assert exact tool names and params per vendor.
2. Assert Gemini: `prompt` param only.
3. Assert Qwen: `url` + `prompt` params.
4. Assert Kimi: `url` param only.

### Fetch behavior tests (all vendors)

1. HTTP fetch success (mock server returning text/plain).
2. HTML fetch success → text extraction.
3. Network error (mock server returning 500 or connection refused).
4. Timeout handling.
5. Empty response body.
6. GitHub URL normalization.

### LLM summarization tests

1. Summarization with mocked LLM provider → returns summary.
2. No LLM provider available → returns raw content with note.
3. Content too large for summarization → truncation.

### Gemini-specific tests

1. API key present → tool initializes normally.
2. No API key → `SkipThisTool` raised, tool disabled.
3. Citation formatting: inline `[N]` markers and `Sources:` footer.
4. Private IP URL → fallback to local fetch.
5. Primary failure → fallback triggered.

### Kimi-specific tests

1. Moonshot service configured → service fetch attempted.
2. Moonshot service not configured → local fallback.
3. text/plain passthrough.
4. Trafilatura extraction quality (mock HTML).

### Integration tests

1. Each package loads through plugin manager.
2. Mock-server based integration tests.
3. OpenRouter integration tests (one per vendor with cheap model).

## Deliverables

1. New shared package: `plugins/web-fetch-shared/` with README, pyproject.toml.
2. Shared fetch engine: `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py`.
3. LLM summarization helper.
4. Shared tests: `plugins/web-fetch-shared/tests/test_web_fetch_engine.py`.
5. Three vendor-specific web fetch tool classes.
6. Package exports, manifests, and READMEs updated.
7. Vendor tool tests and integration tests.

## Documentation follow-up

After implementation, update each vendor package README with:

1. Exposed web fetch tool name and parameters.
2. Vendor-specific behavior notes (API key requirement for Gemini, LLM summarization for Qwen, trafilatura for Kimi).
3. Configuration reference (API key env vars, service URLs, LLM provider for summarization).
4. Known limitations (no Gemini IDE integration, no browser rendering).

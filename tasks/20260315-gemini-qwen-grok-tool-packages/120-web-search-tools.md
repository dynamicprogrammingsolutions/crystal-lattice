# 120 - Web Search Tools (All Vendors)

Short description: Add vendor-compatible web search tools to `gemini-tools`, `qwen-tools`, and `kimi-tools` (Grok has no web search tool). Gemini's tool uses the Gemini SDK with Google Search grounding and citation formatting, disabled when no API key is provided. Qwen supports configurable search providers. Kimi uses the Moonshot Search API with optional page crawling. A shared search result model and provider implementations live in `tool-compat-shared`.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/110-web-fetch-tools.md` (shares `web-fetch-shared` for HTTP utilities)

## Status: SPLIT INTO SUBTASKS

This task has been split into the following subtasks:

## Task Checklist

- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/121-web-search-shared.md`
  - Shared infrastructure: SearchResult model, SearchProvider protocol, Tavily/Google providers
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/122-gemini-web-search.md`
  - Gemini `google_web_search` tool with API grounding and UTF-8 citation formatting
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/123-qwen-web-search.md`
  - Qwen `web_search` tool with multi-provider support (Dashscope/Tavily/Google)
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/124-kimi-web-search.md`
  - Kimi `SearchWeb` tool with Moonshot API and optional page crawling

## Summary of Split

The original task has been split into four sequential subtasks:

1. **121 - Web Search Shared Package**: Create shared infrastructure in `tool-compat-shared`:
   - `SearchResult` dataclass - common result model across vendors
   - `SearchProvider` protocol - interface for provider implementations
   - `TavilyProvider` - Tavily search API client (reusable)
   - `GoogleProvider` - Google Custom Search API client (reusable)
   - No vendor-specific formatting - all formatting stays in vendor plugins

2. **122 - Gemini Web Search Tool**: Implement `GeminiWebSearchTool` in `gemini-tools`:
   - Tool name: `google_web_search` (shape matches CLI exactly)
   - Primary backend: Gemini API with `web-search` model alias + UTF-8 citation formatting
   - Alternative backends: Tavily, Google Custom Search (from shared)
   - Backend selection: config-driven (`web_search_provider`), no `provider` param in schema
   - Result format always Gemini-style regardless of backend
   - Disabled by default; errors if enabled without any configured provider

3. **123 - Qwen Web Search Tool**: Implement `QwenWebSearchTool` in `qwen-tools`:
   - Tool name: `web_search` (shape matches CLI exactly)
   - Primary backend: Dashscope (Qwen OAuth, lives in vendor plugin)
   - Alternative backends: Tavily, Google Custom Search (from shared)
   - Backend selection: `provider` param in schema (matches Qwen CLI) + config default
   - Result format always Qwen-style regardless of backend
   - Disabled by default; errors if enabled without configured provider

4. **124 - Kimi Web Search Tool**: Implement `KimiWebSearchTool` in `kimi-tools`:
   - Tool name: `SearchWeb` (PascalCase, shape matches CLI exactly)
   - Primary backend: Moonshot Search API with optional page crawling (`include_content`)
   - Alternative backends: Tavily, Google Custom Search (from shared)
   - Backend selection: config-driven (`web_search_provider`), no provider param in schema
   - Result format always Kimi-specific Title/Date/URL/Summary regardless of backend
   - Disabled by default; errors if enabled without any configured provider

## Key Architectural Decisions

1. **Engine vs Shape separation**:
   - **Shared package = Engine**: HTTP calls, API clients, data extraction, protocols
   - **Vendor plugins = Shape**: Tool name, parameters, descriptions, result formatting, error messages

2. **Provider implementations**:
   - Reusable providers (Tavily, Google) live in `tool-compat-shared` — available to all vendor tools
   - Vendor-coupled providers (Dashscope, Moonshot, Gemini API grounding) live in vendor plugins
   - Every vendor tool can use any combination of backends; shape stays vendor-specific

3. **Backend selection per vendor**:
   - **Gemini**: Config-driven (`web_search_provider`), no `provider` param in schema — preserves CLI shape
   - **Qwen**: `provider` param in schema + config default — matches Qwen CLI's multi-provider design
   - **Kimi**: Config-driven (`web_search_provider`), no provider param in schema — preserves CLI shape

4. **Tool enablement pattern**:
   - Disabled by default via config (`web_search_enabled: false`)
   - If user enables without required config, tool returns error message (not hidden)
   - No `SkipThisTool` pattern - tools are visible but indicate configuration issues

5. **Citation formatting**:
   - Gemini's `format_gemini_citations` already exists in `web-fetch-shared`
   - Shared by both web-fetch and web-search tools for Gemini
   - Only available with `gemini_api` backend (other backends use simpler Sources footer)

6. **Result formatting is backend-independent**:
   - Gemini tool always formats as `Web search results for "query":\n\n...` + Sources footer
   - Kimi tool always formats as Title/Date/URL/Summary + `---\n\n` separator
   - Qwen tool always formats as answer + Sources or top 5 summary
   - The shape doesn't change when the backend changes

## Vendor Compatibility Summary

| Aspect | Gemini | Qwen | Kimi | Grok |
|--------|--------|------|------|------|
| Tool name | `google_web_search` | `web_search` | `SearchWeb` | (none) |
| Query param | `query` | `query` | `query` | - |
| Provider param | - | `provider` (optional) | - | - |
| Limit param | - | - | `limit` (1-20) | - |
| Content crawl param | - | - | `include_content` | - |
| Primary backend | Gemini API grounding | Dashscope (Qwen OAuth) | Moonshot Search | - |
| Alt backend: Tavily | ✅ (config) | ✅ (param/config) | ✅ (config) | - |
| Alt backend: Google | ✅ (config) | ✅ (param/config) | ✅ (config) | - |
| Citation support | Yes (inline + footer, Gemini API only) | No | No | - |
| Backend selection | Config-driven | Schema param + config default | Config-driven | - |
| Default state | Disabled | Disabled | Disabled | - |

## Source References

### Gemini

- Web search tool: `../gemini-cli/packages/core/src/tools/web-search.ts`
- Tool schema: `../gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts`
- Tool name: `../gemini-cli/packages/core/src/tools/definitions/base-declarations.ts`

### Qwen

- Web search tool: `../qwen-code/packages/core/src/tools/web-search/index.ts`
- Base provider: `../qwen-code/packages/core/src/tools/web-search/base-provider.ts`
- Dashscope provider: `../qwen-code/packages/core/src/tools/web-search/providers/dashscope-provider.ts`
- Tavily provider: `../qwen-code/packages/core/src/tools/web-search/providers/tavily-provider.ts`
- Google provider: `../qwen-code/packages/core/src/tools/web-search/providers/google-provider.ts`
- Types: `../qwen-code/packages/core/src/tools/web-search/types.ts`
- Tool names: `../qwen-code/packages/core/src/tools/tool-names.ts`

### Kimi

- SearchWeb tool: `../kimi-cli/src/kimi_cli/tools/web/search.py`
- Description template: `../kimi-cli/src/kimi_cli/tools/web/search.md`
- SkipThisTool pattern: `../kimi-cli/src/kimi_cli/tools/__init__.py`

### Grok

- No web search tool - confirmed via grep search in `../grok-cli/`

## Grok

**No web search tool** - Grok CLI has no web search tool, so `plugins/grok-tools/` is not modified.

# 110 - Web Fetch Tools (All Vendors)

Short description: Add vendor-compatible URL content fetching tools to `gemini-tools`, `qwen-tools`, and `kimi-tools` (Grok has no web fetch tool). Gemini's tool uses the Gemini SDK with API-backed server-side fetch and grounding, disabled when no API key is provided. Qwen's and Kimi's tools use local HTTP fetching with optional LLM-based summarization. A separate `web-fetch-shared` package isolates heavy HTTP/extraction dependencies.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Status: SPLIT INTO SUBTASKS

This task has been split into the following subtasks:

## Task Checklist

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`
  - COMPLETED - prerequisite for tools to access LLM via context
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/112-web-fetch-shared.md`
  - COMPLETED - shared HTTP fetch and extraction library
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/113-gemini-web-fetch.md`
  - COMPLETED - Gemini web_fetch tool with API grounding
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/114-qwen-web-fetch.md`
  - COMPLETED - Qwen web_fetch tool with LLM summarization
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/115-kimi-fetch-url.md`
  - COMPLETED - Kimi FetchURL tool with trafilatura extraction

## Summary of Split

The original task has been split into five sequential subtasks:

1. **111 - Tool Plugin Context Enhancement**: Extend `ToolPlugin` protocol to accept layered context (`core`, `app`, `config`), enabling tools to make LLM calls through high-level APIs. This matches the pattern from Task 221 for feature/extension actions.

2. **112 - Web Fetch Shared Package**: Create `plugins/web-fetch-shared/` with HTTP fetching, HTML extraction, and URL normalization helpers. This isolates heavy dependencies (`trafilatura`, `aiohttp`) from vendor packages. No LLM-related code - all LLM calls happen in vendor tools via context.

3. **113 - Gemini Web Fetch Tool**: Implement `GeminiWebFetchTool` in `gemini-tools` with:
   - Primary: Gemini API server-side fetch with grounding and citations
   - Fallback: Local fetch + LLM summarization via context
   - API key gating via `is_enabled()`
   - Rate limiting per host

4. **114 - Qwen Web Fetch Tool**: Implement `QwenWebFetchTool` in `qwen-tools` with:
   - Single path: Local fetch + HTML-to-text + LLM summarization via context
   - Explicit `url` and `prompt` parameters
   - No special private IP handling

5. **115 - Kimi FetchURL Tool**: Implement `KimiFetchURLTool` in `kimi-tools` with:
   - Primary: Moonshot fetch service (optional)
   - Fallback: Local fetch + trafilatura extraction
   - No LLM summarization (returns raw extracted text)
   - PascalCase tool name: `FetchURL`

## Key Architectural Decisions

1. **Tool context access**: Tools receive the same layered context as feature/extension actions, enabling them to make LLM calls through `core.stream_request()` or `app.send_request()`.

2. **Shared package is library-only**: `web-fetch-shared` is NOT a plugin package. It's a library dependency for vendor packages.

3. **LLM calls via context**: No low-level provider access in tools. All LLM calls go through `context["core"]` or `context["app"]`.

4. **Async-first design**: All fetch operations are async, with sync wrappers in vendor tools if needed.

## Vendor Compatibility Summary

| Aspect | Gemini | Qwen | Kimi |
|--------|--------|------|------|
| Tool name | `web_fetch` | `web_fetch` | `FetchURL` |
| URL param | `prompt` (URLs inline) | `url` (explicit) | `url` (explicit) |
| Instructions param | `prompt` (inline) | `prompt` (separate) | (none) |
| Primary backend | Gemini API server-side fetch | Local HTTP + LLM summarization | Moonshot fetch service |
| Fallback backend | Local HTTP + LLM summarization | (same as primary) | Local HTTP + trafilatura |
| Extraction library | `html-to-text` (via Gemini API) | `trafilatura` | `trafilatura` |
| Content limit | 100000 chars | 100000 chars | 50000 chars |
| Citation support | Yes (grounding metadata) | No | No |
| Conditional availability | Requires Gemini API key | Always | Always (Moonshot config optional) |
| LLM summarization | Yes (fallback path) | Yes | No |

## Grok

**No web fetch tool** - Grok CLI has no web fetch tool, so `plugins/grok-tools/` is not modified.

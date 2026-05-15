# Tool Compatibility Shared Helpers

Internal helper package for the vendor-style tool bundles.

This package is intentionally not a public plugin package and does not expose
`agent_plugin.json` entries. It exists only to share filesystem, decoding,
truncation, formatting, write, literal-replacement, and web search logic across
`gemini-tools`, `qwen-tools`, `kimi-tools`, and `grok-tools`.

## Engine vs Shape Principle

This package follows the **Engine vs Shape** separation:

- **Engine (this package)**: HTTP calls, API clients, data extraction, protocol definitions, data models
- **Shape (vendor plugins)**: Tool name, parameters, descriptions, result formatting, error messages

The `web_search_engine` module returns structured data (`SearchResponse`, `SearchResult`) only.
It does NOT format results for LLM consumption. All formatting — citation markers, source footers,
truncation banners, result numbering — belongs in vendor tool plugins.

> **Note**: The existing `reader_engine.py` and `search_engine.py` modules export vendor-specific
> formatting functions (e.g., `format_gemini_*`, `format_qwen_*`). These are precedent violations
> of the Engine vs Shape principle. New modules should not follow this pattern.

## Modules

### `reader_engine.py`

File reading, encoding detection, BOM handling, path resolution, and line truncation.

### `editor_engine.py`

Literal text replacement, multi-edit application, and file writing.

### `search_engine.py`

Filesystem search: directory listing, glob search, grep search. Includes vendor-specific
formatting functions (precedent violations — see note above).

### `shell_engine.py`

Shell command execution, background process support, output truncation.

### `web_search_engine.py`

Web search infrastructure: data models, provider protocol, and reusable search provider
implementations (Tavily, Gemini API).

#### Data Models

- **`SearchResult`** — Frozen dataclass with fields: `title`, `url`, `snippet`, `content`,
  `date`, `site_name`, `score`. All optional fields have defaults.
- **`SearchResponse`** — Frozen dataclass wrapping `List[SearchResult]` plus optional
  `answer` (AI-generated, from Tavily or Gemini API), `query`, `grounding_chunks`,
  and `grounding_supports` (Gemini API citation metadata for vendor-side formatting).

#### Provider Protocol

- **`SearchProvider`** — `Protocol` with `name` (str), `is_available()` (bool),
  `async search(query, *, limit) -> SearchResponse`.

#### Provider Implementations

- **`TavilyProvider`** — POST to `api.tavily.com/search`. Config: `api_key`, `search_depth`
  (default: `"advanced"`), `include_answer` (default: `True`).
- **`GeminiApiProvider`** — Uses `google-genai` SDK with `web-search` model alias for
  server-side Google Search grounding. Config: `api_key`, `model` (default: `"web-search"`).
  Returns `answer` (response text), `results` (from grounding chunks), and raw
  `grounding_chunks`/`grounding_supports` for vendor-side citation formatting.
  Requires `google-genai>=0.3.0` (optional dependency: `pip install tool-compat-shared[gemini]`).

#### Error Handling

- **`SearchProviderError`** — Exception with `provider_name` and `original_error`.
  Message format: `[ProviderName] message`.

## Dependencies

- `aiohttp>=3.8.0` — For async HTTP in `web_search_engine.py` (lazy-imported)
- `google-genai>=0.3.0` — Optional, for `GeminiApiProvider` (install with `[gemini]` extra)

## License

This directory is available under the [Apache License 2.0](../../LICENSE).

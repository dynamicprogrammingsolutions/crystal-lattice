# 112 - Web Fetch Shared Package

Short description: Create the `web-fetch-shared` library package for HTTP fetching, HTML extraction, and URL normalization helpers. This package isolates heavy dependencies (`trafilatura`, `aiohttp`) from vendor tool packages.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`

## Goal

Create a dedicated shared package for HTTP fetching and HTML-to-text extraction used by all vendor web fetch tools. This package is a library dependency, NOT a plugin package (no `agent_plugin.json`).

## Requirements Checklist

- [x] Create package structure with pyproject.toml
- [x] Implement `fetch_url` async function
- [x] Implement `extract_text` function with trafilatura
- [x] Implement `normalize_github_url` function
- [x] Implement `is_private_url` function
- [x] Implement `truncate_content` function
- [x] Implement `format_gemini_citations` function
- [x] Implement `parse_urls_from_text` function
- [x] Create mock HTTP server fixture
- [x] Add tests for all functions
- [x] Create README.md with usage documentation

---

## Execution Plan

Added during completion.

### Phase 1: Package Skeleton
1. Create `plugins/web-fetch-shared/` directory structure
2. Create `pyproject.toml` with aiohttp/trafilatura dependencies
3. Create `README.md` with API documentation

### Phase 2: Core Implementation
1. Implement `FetchResult` frozen dataclass
2. Implement `fetch_url` with aiohttp (streaming, size limits, timeout, redirects)
3. Implement `extract_text` with trafilatura (passthrough for text/plain, text/markdown)
4. Implement `normalize_github_url` (blob → raw conversion)
5. Implement `is_private_url` (private IP detection using ipaddress stdlib)
6. Implement `truncate_content` (simple length truncation)
7. Implement `format_gemini_citations` (inline markers + source footer)
8. Implement `parse_urls_from_text` (regex extraction with validation)

### Phase 3: Tests
1. Create `conftest.py` with mock HTTP server fixture (12 endpoints)
2. Create `test_web_fetch_engine.py` with 65 tests covering:
   - HTTP fetch: 10 tests (success, errors, redirects, timeout, size limit)
   - HTML extraction: 9 tests (extraction, passthrough, options)
   - GitHub URL normalization: 6 tests
   - Private URL detection: 14 tests (all IP ranges, domains)
   - Truncation: 4 tests
   - Citation formatting: 4 tests
   - URL parsing: 7 tests
   - Constants: 5 tests
   - FetchResult dataclass: 3 tests

---

## Completion Notes

**Implementation completed successfully.**

### Files Created

| File | Purpose |
|------|---------|
| `plugins/web-fetch-shared/pyproject.toml` | Package definition with aiohttp/trafilatura deps |
| `plugins/web-fetch-shared/README.md` | Usage documentation with API reference |
| `plugins/web-fetch-shared/src/web_fetch_shared/__init__.py` | Public exports |
| `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py` | Core implementation (582 lines) |
| `plugins/web-fetch-shared/tests/__init__.py` | Test package marker |
| `plugins/web-fetch-shared/tests/conftest.py` | Mock HTTP server fixture |
| `plugins/web-fetch-shared/tests/test_web_fetch_engine.py` | 65 unit tests |

### Key Implementation Details

1. **fetch_url**: Uses aiohttp with streaming response handling, size limit enforcement during chunk reading, charset detection from Content-Type header, and automatic redirect following.

2. **extract_text**: Lazy imports trafilatura, implements passthrough for text/plain and text/markdown, uses trafilatura.extract() with configurable options (comments, tables, formatting, output format).

3. **is_private_url**: Uses Python's ipaddress stdlib for robust IP range detection, handles both IPv4 and IPv6, plus common private domain suffixes (.local, .localhost, .internal, .localdomain).

4. **format_gemini_citations**: Processes grounding metadata to insert inline [N] markers at segment positions, builds sorted source footer with unique citations.

5. **parse_urls_from_text**: Regex extraction of http/https URLs, validates hostname has TLD dot or is localhost, returns both valid URLs and error messages.

### Test Results

```
============================= 65 passed in 0.43s ==============================
```

All tests pass, covering:
- HTTP operations (success, 404/500 errors, redirects, timeout, size limit)
- HTML extraction (extraction, passthrough, empty content, options)
- GitHub URL normalization (blob→raw, edge cases)
- Private IP detection (localhost, 127.x, 10.x, 172.16-31.x, 192.168.x, link-local, IPv6 private, domain suffixes)
- Truncation (under/over limit, custom marker)
- Citation formatting (basic, no supports, no chunks, missing title)
- URL parsing (single/multiple, http/https, query strings, ports, localhost, invalid hostname)
- Constants and dataclass behavior

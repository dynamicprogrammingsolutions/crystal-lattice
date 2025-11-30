# OpenRouter Provider Implementation Plan

## Overview
Add OpenRouter provider with modular support for reasoning and tool calling, following the existing OpenAI-compatible provider structure. Use tag-based dependency management and add integration test markers.

## Research Findings

### OpenRouter API
- Base URL: `https://openrouter.ai/api/v1`
- Authentication: Bearer token via `Authorization` header
- OpenAI-compatible Chat Completions API
- Supports tool calling (standard OpenAI format)
- Supports reasoning via `reasoning_effort` parameter or model-specific parameters

### Model Names (with cheap alternatives)

- **Grok:** `x-ai/grok-4.1-fast` (cheap/free version: `x-ai/grok-4.1-fast:free`)
- **Claude:** `anthropic/claude-opus-4.5`, `anthropic/claude-sonnet-4` (cheap: `anthropic/claude-haiku-4`)
- **Gemini:** `google/gemini-3-pro-preview` (cheap: `google/gemini-2.5-flash` @ $0.30/$2.50 per M tokens, cheapest: `google/gemini-2.5-flash-lite` @ $0.10/$0.40)
- **GPT-5:** `openai/gpt-5` (cheap: `openai/gpt-5-mini` @ $0.05/$0.40 per M tokens)

---

## Implementation Structure

### 1. Core Provider Plugin (`core/python/plugins/openrouter_provider.py`)

**Features:**
- OpenAI-compatible API calls
- Base URL: `https://openrouter.ai/api/v1`
- API key authentication via `Authorization: Bearer <key>`
- Streaming and non-streaming support
- Tag: `provider:openrouter`, `supports_streaming`, `supports_tools`, `supports_reasoning`

**Config Schema:**
```python
{
    "model": {"type": "string", "required": True},
    "api_key": {"type": "string", "required": True},
    "base_url": {"type": "string", "default": "https://openrouter.ai/api/v1"},
    "timeout": {"type": "number", "default": 60},
    "site_url": {"type": "string", "required": False},  # OpenRouter-specific
    "app_name": {"type": "string", "required": False},  # OpenRouter-specific
}
```

**OpenRouter-Specific Headers:**
- `HTTP-Referer`: Optional, for ranking/tracking (from site_url)
- `X-Title`: Optional, for application identification (from app_name)

**Dependencies:** Copy structure from `openai_provider.py`, adjust for OpenRouter-specific headers

---

### 2. Reasoning Extension (`core/python/plugins/openrouter_reasoning_extension.py`)

**Features:**
- Enable reasoning via `reasoning_effort` parameter (low/medium/high)
- Extract and accumulate reasoning tokens from streaming responses
- Attach reasoning to message metadata
- Similar structure to `ollama_thinking_extension.py`

**Config Schema:**
```python
{
    "reasoning_effort": {"type": "string", "enum": ["low", "medium", "high"], "required": False},
    "enable_reasoning": {"type": "boolean", "default": False},
}
```

**Tags:**
- Provides: `ext:openrouter_reasoning`
- Requires: `supports_reasoning`

**Key Methods:**
- `initialize_request`: Add reasoning parameters to payload
- `process_delta`: Accumulate reasoning content from streaming chunks
- `finalize`: Attach accumulated reasoning to metadata
- `from_native_messages`: Extract reasoning into message metadata

---

### 3. Tool Calling Extension (`core/python/plugins/openrouter_tools_extension.py`)

**Features:**
- OpenAI-compatible tool calling format
- Tool schema injection into request payload
- Tool call accumulation during streaming
- Tool response mapping with `tool_call_id`
- Nearly identical to `openai_tools_extension.py`

**Tags:**
- Provides: `ext:openrouter_tools`
- Requires: `supports_tools`

**Key Methods:**
- `initialize_request`: Add tools array to payload
- `to_native_messages`: Map tool_call_id for tool messages
- `process_delta`: Accumulate tool_calls across chunks
- `from_native_messages`: Extract tool_calls into metadata

---

## 4. Integration Tests

### Test Files Structure

**`core/python/tests/test_openrouter_reasoning_<model>.py`** (one per model family):
- `test_openrouter_reasoning_grok_non_streaming`
- `test_openrouter_reasoning_grok_streaming`
- `test_openrouter_reasoning_claude_non_streaming`
- `test_openrouter_reasoning_claude_streaming`
- `test_openrouter_reasoning_gemini_non_streaming`
- `test_openrouter_reasoning_gemini_streaming`
- `test_openrouter_reasoning_gpt_non_streaming`
- `test_openrouter_reasoning_gpt_streaming`
- Verify reasoning content in metadata

**`core/python/tests/test_openrouter_tools_<model>.py`** (one per model family):
- `test_openrouter_tools_grok_single_tool`
- `test_openrouter_tools_grok_parallel_tools`
- `test_openrouter_tools_claude_streaming`
- `test_openrouter_tools_gemini_tool_chain`
- `test_openrouter_tools_gpt_tool_execution`
- Verify tool_calls in metadata and tool execution

### Test Configuration

```python
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Cheap model versions for testing
MODELS = {
    "grok": "x-ai/grok-4.1-fast:free",
    "claude": "anthropic/claude-haiku-4",
    "gemini": "google/gemini-2.5-flash-lite",
    "gpt": "openai/gpt-5-mini",
}
```

### Fixtures

```python
@pytest.fixture(scope="module")
def ensure_api_key():
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration tests")
```

---

## 5. Pytest Markers Configuration

### Update `core/python/pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=agent_core --cov-report=term-missing -m 'not integration'"
markers = [
    "integration: integration tests that may hit real services",
    "ollama: tests exercising local Ollama integration",
    "openrouter: tests exercising the OpenRouter provider",
]
```

### Mark existing Ollama tests

- Add `@pytest.mark.ollama` to all Ollama test files
- Remove any `@pytest.mark.integration` markers from Ollama tests so they run by default

### Mark OpenRouter tests

- Add `@pytest.mark.integration` and `@pytest.mark.openrouter` to all OpenRouter tests

### Run commands

```bash
# Run default test suite (unit + ollama; integration tests skipped)
pytest core/python/tests -q

# Run only OpenRouter tests
pytest core/python/tests -m "openrouter" -q

# Run only Ollama tests
pytest core/python/tests -m "ollama" -q

# Run all integration tests except OpenRouter
pytest core/python/tests -m "integration and not openrouter" -q
```

---

## 6. Documentation Updates

**`docs/providers/openrouter.md`:**
- Overview and setup instructions
- API key configuration
- Model selection guide
- Reasoning and tool calling examples
- Pricing and free tier information

**`EXAMPLES.md`:** Add OpenRouter examples after implementation

---

## Implementation Phases

### Phase 1: Core Provider ✅

1. Create `plugins/openrouter_provider.py`
2. Copy structure from `openai_provider.py`
3. Adjust base URL, headers, and authentication
4. Add OpenRouter-specific headers (`X-Title`, `HTTP-Referer`)
5. Write unit tests for provider initialization and message conversion
6. Test with basic model (Gemini Flash Lite)

### Phase 2: Reasoning Extension

1. Create `plugins/openrouter_reasoning_extension.py`
2. Implement reasoning parameter injection
3. Implement reasoning extraction from responses
4. Write unit tests
5. Write integration tests for Grok, Claude, Gemini, GPT-5 (with cheap models)
6. Verify reasoning in streaming and non-streaming modes

### Phase 3: Tool Calling Extension ✅

1. ✅ Create `plugins/openrouter_tools_extension.py` (v0.1.0)
2. ✅ Copy/adapt from `openai_tools_extension.py`
3. ✅ Write unit tests (9 tests in `test_openrouter_tools_extension_unit.py`)
4. ✅ Write integration tests for all 4 model families:
   - `test_openrouter_tools_reasoning_integration.py` (8 tests with reasoning_test scenario)
   - `test_openrouter_tools_comprehensive.py` (28 tests covering all scenarios)
5. ✅ Test single tool calls (8 tests: 2 scenarios × 4 models)
6. ✅ Test parallel tool calls (8 tests: 2 scenarios × 4 models)
7. ✅ Test tool chains/multiple rounds (12 tests: 3 scenarios × 4 models)
8. ✅ Create `plugins/math_tools.py` for computation testing

### Phase 4: Test Markers

1. Update `pyproject.toml` with markers
2. Mark all ollama tests with `@pytest.mark.ollama`
3. Mark all OpenRouter tests with `@pytest.mark.openrouter`
4. Update `AGENTS.md` with marker usage examples
5. Verify marker filtering works correctly

### Phase 5: Integration & Documentation

1. Run full integration test suite with API key
2. Update examples in `EXAMPLES.md`
3. Write provider documentation
4. Update `README.md` if needed
5. Final verification with all 4 model families

---

## File Structure Summary

```
core/python/
├── plugins/
│   ├── openrouter_provider.py          (new)
│   ├── openrouter_reasoning_extension.py (new)
│   └── openrouter_tools_extension.py   (new)
├── tests/
│   ├── test_openrouter_provider_unit.py (new)
│   ├── test_openrouter_reasoning_grok.py (new)
│   ├── test_openrouter_reasoning_claude.py (new)
│   ├── test_openrouter_reasoning_gemini.py (new)
│   ├── test_openrouter_reasoning_gpt.py (new)
│   ├── test_openrouter_tools_grok.py   (new)
│   ├── test_openrouter_tools_claude.py (new)
│   ├── test_openrouter_tools_gemini.py (new)
│   ├── test_openrouter_tools_gpt.py    (new)
│   └── test_ollama_*.py                (mark with @pytest.mark.ollama)
├── pyproject.toml                       (update markers)
└── ...
docs/
└── providers/
    └── openrouter.md                    (new)
```

---

## Testing Strategy

### Unit Tests
- Provider initialization and configuration
- Message conversion (to/from native)
- Request initialization
- Reasoning parameter handling
- Tool schema injection

### Integration Tests (require API key)
- Real API calls to all 4 model families
- Use cheapest/free versions to minimize cost
- Test reasoning extraction in streaming/non-streaming
- Test single/parallel tool calls
- Test tool chains (multiple rounds)
- Verify metadata structure

### Cost Optimization
- Use free models when available (Grok 4.1 Fast Free)
- Use cheapest paid models:
  - GPT-5 Mini: $0.05/$0.40 per M tokens
  - Gemini Flash Lite: $0.10/$0.40 per M tokens
- Keep test prompts minimal (< 100 tokens)
- Estimated total cost per full test run: < $0.10

---

## Success Criteria

- ✅ Provider successfully connects to OpenRouter API
- ✅ All 4 model families work (Grok, Claude, Gemini, GPT-5)
- ✅ Reasoning extension extracts reasoning content correctly
- ✅ Tool calling extension handles single/parallel/chained calls
- ✅ Streaming works for all features
- ✅ Tag-based dependency resolution works correctly
- ✅ Integration tests pass with real API
- ✅ Test markers allow selective test execution
- ✅ Documentation is complete and accurate
- ✅ No regressions in existing tests

---

## Open Questions

1. **Reasoning Format:** Need to confirm if reasoning content is in response.choices[0].message.reasoning or different field
2. **Free Tier Limits:** Need to verify rate limits for free models to avoid test failures
3. **Tool Calling Differences:** Check if OpenRouter has any non-standard behavior vs OpenAI API

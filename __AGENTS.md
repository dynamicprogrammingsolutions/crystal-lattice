# AGENTS.md

## Project Overview

The AI Agent Platform is a **modular, functional AI agent framework** built on functional programming principles. It enables developers to create conversational AI applications with any LLM provider through a plugin-based architecture.

**Core Value Propositions:**
- **Provider-agnostic**: Switch between OpenAI, Anthropic, Google, Ollama, and local models
- **Extensible**: Add features through plugins without modifying core
- **Functional design**: Immutable state, pure functions, predictable transformations
- **Streaming-first**: Real-time token-by-token response display
- **Low-level API**: Full control over conversation flow and tool execution

**Current Status:** Stage 1 MVP - Core SDK complete with working examples and tests

## Architecture at a Glance

The platform follows a **functional core, imperative shell** architecture:

```
Frontend (React/Web UI)
    ↓
Application Layer (FastAPI/Express)
    ↓
Core SDK (AgentCore) ← Pure functions, immutable state
    ↓
Plugin Wrappers
    ↓
Plugins (Provider/Extension/Feature/Tool)
```

**Key Principles:**
1. **Immutability**: All transformations return new objects
2. **Pure Functions**: Same input → same output (except I/O boundaries)
3. **Duck-Typed Plugins**: No inheritance required, just implement methods
4. **Shared State**: Provider wrapper manages state for provider + extensions + features
5. **Tool Independence**: Each tool plugin maintains its own state

For complete architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Documentation

### Documentation Files

- **[TYPES_AND_PROTOCOLS.md](TYPES_AND_PROTOCOLS.md)** - Type definitions, plugin protocols
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Roadmap, goals, success criteria
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete architecture, design principles, data flow
- **[EXAMPLES.md](EXAMPLES.md)** - Auto-generated from examples (run `scripts/generate_examples_md.py`)
- **[docs/api/core-sdk.md](docs/api/core-sdk.md)** - Core SDK API reference

## Code Entry Points

### 1. Core SDK Entry Point

**File**: `core/python/agent_core/core.py`

The `AgentCore` class is the main orchestrator providing methods for:

- Session creation and management
- Message manipulation (functional, returns new sessions)
- Request/response handling (streaming and non-streaming)
- Plugin registration (providers, features, tools)

**Start here** to understand the request/response flow.

### 2. Type Definitions

**File**: `core/python/agent_core/types.py`

Defines core data structures and plugin protocols for all plugin types.

**Start here** to understand data structures and plugin contracts.

### 3. Plugin System

**Directory**: `core/python/agent_core/plugin/`

Contains plugin wrappers (hold state, call plugin methods) and adapters (protocol bridge between core and plugins).

**Start here** to understand how plugins integrate with core.

### 4. Working Examples

**Directory**: `core/python/examples/`

All examples are tested and documented in [EXAMPLES.md](EXAMPLES.md), covering:

- Plugin implementations (providers, extensions, features, tools)
- Basic and streaming usage patterns
- Tool execution loops
- Message manipulation
- Dynamic configuration
- WebSocket applications

**Start here** for practical code patterns.

### 5. Real Provider Implementation

**File**: `core/python/plugins/openai_provider.py`

OpenAI-compatible provider (works with OpenAI, Ollama, etc.)

**Start here** to see a production-ready provider plugin.

## Development Workflow

### Setting Up Development Environment

```bash
# Install dependencies
cd core/python
pip install -e ".[dev]"

# Run tests (unit + ollama; integration skipped by default)
pytest

# Run OpenRouter integration tests
pytest core/python/tests -m openrouter -q

# Run all integration tests
pytest core/python/tests -m integration -q

# Run specific test file
pytest core/python/tests/test_core.py -v

# Run example
python core/python/examples/example5_project_plan_basic.py

# Run example test
pytest core/python/examples/tests/test_example5_project_plan_basic.py

# Typecheck
pyright

```

### Code Style

- Use type hints for all functions
- Docstrings for public APIs (Google style)
- Functional style: return new objects, never mutate
- Test coverage: minimum 80% for new code

### Updating Documentation

**After adding an example:**
```bash
python scripts/generate_examples_md.py
# Regenerates EXAMPLES.md from example files
```

**Documentation principles:**
1. Update documentation alongside implementation
2. Examples must be runnable and tested
3. Every public API needs docstrings
4. Type hints are mandatory

## Project Roadmap

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for complete roadmap, implementation stages, and success criteria.

## Getting Help

1. **Read examples first**: [EXAMPLES.md](EXAMPLES.md) has working code
2. **Check tests**: `core/python/examples/tests/` shows expected behavior
4. **Study implementations**: Real plugins in `core/python/plugins/` and `core/python/examples/`


## Quick Reference

**Core SDK**: `core/python/agent_core/core.py`  
**Types**: `core/python/agent_core/types.py`  
**Plugin Wrappers**: `core/python/agent_core/plugin/`  
**Examples**: `core/python/examples/` or [EXAMPLES.md](EXAMPLES.md)  
**Tests**: `core/python/tests/`
**Plugins**: `core/python/plugins/`

**Test Command**: `pytest core/python/tests -q` (integration tests are skipped by default; use `-m integration` or `-m openrouter` to include remote suites)
**Test Example Command**: `pytest -qs core/python/examples/tests/test_example1_echo_provider.py`  

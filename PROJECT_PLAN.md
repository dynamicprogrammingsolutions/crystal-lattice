# AI Agent Platform - Project Plan

This document outlines the project goals, roadmap, and implementation plan for the AI Agent Platform.

**For detailed architecture and design principles, see [ARCHITECTURE.md](ARCHITECTURE.md)**

**For type definitions and plugin protocols, see [TYPES_AND_PROTOCOLS.md](TYPES_AND_PROTOCOLS.md)**

## Project Overview

### Purpose

Build a **modular, functional AI agent platform** that enables developers to:
- Create conversational AI applications with any LLM provider
- Extend functionality through a plugin system
- Support both Python and JavaScript ecosystems
- Stream responses in real-time
- Add features (web search, citations, tools) without modifying core
- Build locally-first applications with optional cloud deployment

### Target Users

1. **Developers** building AI applications
2. **Plugin authors** creating provider/feature integrations
3. **End users** interacting through web/CLI interfaces

### Key Value Propositions

- **Provider agnostic**: Switch between OpenAI, Anthropic, Google, local models
- **Extensible**: Add features without touching core code
- **Cross-language**: Develop in Python or JavaScript
- **Functional design**: Predictable, testable, composable
- **Streaming-first**: Real-time response display
- **Local-first**: Run entirely on localhost, no external dependencies required

## Core Design Concepts

### 1. Functional Programming Paradigm

**Immutability:**

All transformations return new objects, never mutate. State changes are explicit and traceable.

**Pure Functions:**

Plugin methods (except I/O) are pure functions. Same input always produces same output. Easy to test, debug, and reason about.

**Composition:**

Small, focused functions compose into complex pipelines. Feature A + Feature B = Combined functionality. No hidden interactions or side effects.

### 2. Plugin Architecture

**Modularity:**

Core provides orchestration only. All provider/feature logic lives in plugins. Add/remove plugins without core changes.

**Two-Layer Plugin System:**

- Layer 1: Wrapper (holds state, same language as plugin)
- Layer 2: Adapter (protocol bridge, core language)
- Same-language = zero-overhead passthrough
- Cross-language = subprocess with JSON-RPC

**Shared Provider State:**

- The provider wrapper owns a single shared state object for each request/turn.
- Provider extensions and feature plugins receive this shared `state` and may return `new_state` which the provider wrapper propagates.
- Tools are the exception: each tool plugin maintains its own independent state.

State is an immutable dict; plugins choose whatever keys they need, and the core does not prescribe a specific layout.

Note on instance lifecycle: Plugin methods should remain stateless and operate on explicit state parameters. Plugin class instances may be constructed by wrappers for convenience, but they are short‑lived and scoped to a single request, matching the lifecycle of the shared provider state. The provider wrapper discards shared state after each request. Tool plugins should manage explicit tool state dicts and avoid persistent object state.

**Duck Typing:**

Plugin type determined by which functions it implements, not by inheritance. No required base class. Functional architecture without object-oriented constraints.

### 3. Streaming Architecture

**Dual Message Mode:**

Partial messages: streamed token-by-token during generation. Final messages: complete, with metadata (citations, etc.). Frontend shows partials, replaces with final when done. Partials are distinct `PartialMessage` objects `{role, content, metadata}`.

**Provider Extension Model:**

Extensions enhance provider streaming. They can observe and transform provider outputs per-chunk and at finalize.

**Performance Stratification:**

- Hot path (per-chunk): Must be native, same language
- Cold path (per-turn): Can be cross-language
- Streaming happens in provider's language
- Final processing can be any language

### 4. Configuration & State Management

**Unified State:**

Provider shared state is a single opaque dict owned by the provider wrapper. It is initialized via `init(config)` on the provider and then threaded through extensions/features via their `init` and `initialize_request` methods. UI-driven configuration should be resolved into the `config` dict before calling core; there is no separate `update_state` lifecycle step. The provider wrapper discards its internal shared state after each completed request.

**UI-Driven Updates:**

Frontend UI elements generated from plugin schemas. User interaction → state update → next request uses new state. Example: Toggle "Enable Web Search" → immediate effect.

**Configuration Hierarchy:**

Default provider config → Agent-specific overrides → Environment variables and file references. Application loads and resolves config, Core receives final resolved dict/object.

### 5. Cross-Language Strategy

**Native First:**

Python Core ←→ Python Plugins (default). JavaScript Core ←→ JavaScript Plugins (default). Zero serialization overhead, full language features.

**Cross-Language When Needed:**

Python Core ←→ JavaScript Plugin (via subprocess). JavaScript Core ←→ Python Plugin (via subprocess). Subprocess wrapper manages state internally. JSON-RPC over stdin/stdout.

**Performance Trade-offs:**

- Same language: ~0μs overhead per call
- Cross-language: ~1-5ms overhead per RPC
- Acceptable for cold path (once per turn)
- Not acceptable for hot path (hundreds of times per turn)

### 6. Low-Level Core API

**Separation of Concerns:**

Adding messages and sending requests are separate operations. Tool execution is application-level responsibility, not core. Messages, tool calls, and tool results are all just message types. Full control over conversation flow.

**Message Manipulation:**

Add, remove, or modify any message in conversation. Clear distinction between conversation state and API calls. Application decides when to call tools, core just handles messages.

### 7. Documentation & Testing Principles

**Documentation as Code:**

Documentation is not written after the fact—it's developed alongside the code as an integral part of development. Every function has docstrings, every plugin has a README, every API change updates the reference documentation.

**Test-Driven Development:**

Tests are written before or during implementation, not after. Each feature includes its test suite. Tests serve as living documentation of expected behavior. Code without tests is considered incomplete.

**Executable Examples:**

All examples in documentation are real, runnable code. Examples are tested as part of CI/CD to ensure they never go stale. If an example breaks, it's a bug.

**Layered Documentation:**

- **Code level**: Docstrings and type hints
- **Module level**: README explaining purpose and basic usage
- **API level**: Auto-generated reference from docstrings
- **Guide level**: Tutorials and how-tos for common tasks
- **Architecture level**: Design decisions and system overview

**Testing Strategy:**

- **Unit tests**: Pure functions, state transformations
- **Integration tests**: Plugin interactions, pipeline flows
- **End-to-end tests**: Complete request/response cycles
- **Examples as tests**: Documentation examples run in CI
- **Performance tests**: Benchmarks for critical paths

**Documentation-First Changes:**

When proposing a new feature or API change, start with documentation:
1. Write the documentation showing how it would work
2. Get feedback on the design
3. Implement to match the documentation
4. Tests verify implementation matches docs

**Quality Gates:**

Code cannot be merged without:
- Passing tests (minimum 80% coverage for new code)
- Updated documentation
- Type hints (Python) or TypeScript definitions (JavaScript)
- Docstrings for public APIs
- At least one executable example


## Architecture Summary

The platform follows these core principles:

- **Functional Core, Imperative Shell**: Pure functions for business logic, I/O at edges
- **Plugin-Based**: Provider-agnostic core with pluggable providers, features, and tools
- **Immutable State**: All transformations return new objects
- **Streaming-First**: Real-time partial messages with final consolidation
- **Low-Level API**: Application layer handles tool execution and conversation flow
- **Cross-Language Support**: Native performance with optional cross-language plugins

**See [ARCHITECTURE.md](ARCHITECTURE.md) for complete architecture details, system layers, data flow, and design principles.**

## Type System and Protocols

The platform defines clear protocols for:

- **Core Types**: Message, PartialMessage, Session, PluginState
- **Provider Plugin**: API communication and message conversion
- **Provider Extension**: Streaming enhancement (citations, reasoning)
- **Feature Plugin**: Message transformation and processing
- **Tool Plugin**: Tool definition and execution
- **Core SDK**: Application interface for agent operations

**See [TYPES_AND_PROTOCOLS.md](TYPES_AND_PROTOCOLS.md) for complete type definitions, protocols, and the latest breaking changes.**

**See [PLUGIN_EXAMPLES.md](PLUGIN_EXAMPLES.md) for complete, runnable plugin implementations.**

## Example Usage

All runnable examples have moved to `EXAMPLES.md` (contains full code, tests, and commands).




## Documentation Types

**Auto-Generated (from docstrings):**
- API Reference: Classes, functions, parameters, return types
- Tools: Sphinx (Python), TypeDoc (TypeScript), JSDoc (JavaScript)
- Format: Google-style, NumPy-style, or reStructuredText docstrings

**Manually Written:**
- Guides and tutorials
- Architecture documentation
- Examples and how-tos
- Getting started
- Design decisions

## Implementation Roadmap

> **Note:** This roadmap is a living document and will evolve during development. Timelines, features, and priorities may change based on implementation discoveries, user feedback, and technical constraints.

> **Testing & Documentation Standard:** Every item in this roadmap must include tests and documentation unless explicitly noted otherwise. This includes: unit tests for pure functions, docstrings for all public APIs, type hints/definitions, and at least one runnable example. Items marked with specific testing or documentation needs indicate additional requirements beyond the standard.

### Stage 1: Working MVP (Core + Basic UI)

**Goal:** Create a functional system we can use ourselves immediately.

**Core SDK:**
- [x] Implement basic data types
- [x] Create plugin wrapper and passthrough adapter
- [x] Build session management with low-level message API
- [x] Implement send_request, send_request_stream
- [x] Create plugin registry and discovery
- [x] Integration tests for complete request/response cycle (with dummy plugins made for testing)
- [x] API reference documentation

**Plugins**
- [x] OpenAI compatible plugin & local integration test with ollama
- [x] Thinking blocks provider extension for Ollama (should add thinking flag and process thinking blocks into final native message)
- [x] Request options feature plugin (configure request options in config via key request_options, contents will be merged and applied in initialize_request)
- [x] System message feature plugin (configure system message in config, load from specific files like AGENTS.md. Can be
  disabled via config, list of files to use should be configurable. Applied if the user didn't add a system message
  manually. If any of the dynamic elements 
  are changed, it should affect the next request.)
- [x] Develop/refine tool calling system & test with Ollama with a file reader tool plugin, supported by tool calling provider extension

**Openrouter plugins**
- [x] Openrouter provider plugin
- [x] Support for thinking and tool calling
- [ ] Web search feature plugin (basic version)
- [ ] Plugin development quick start guide (tutorial showing how to create each type)

**Application Layer:**
- [ ] Configuration loading with ${env:...} and ${file:...} resolution
- [ ] Basic FastAPI/Express server
- [ ] WebSocket handler for streaming
- [ ] Tool execution loop (application-level)
- [ ] Session management
- [ ] Integration tests for WebSocket streaming
- [ ] Configuration guide with example config files

**Frontend:**
- [ ] Basic React UI
- [ ] Message list display
- [ ] Text input for user messages
- [ ] Display streaming partials
- [ ] Replace with final message
- [ ] Show tool calls in progress
- [ ] Basic styling
- [ ] Component tests for message handling

**Configuration:**
- [ ] JSON config file support
- [ ] No UI configuration yet (manual JSON editing)
- [ ] Support multiple agent configurations
- [ ] Example config.json with inline comments

**Documentation:**
- [ ] README with setup instructions and quick start (5 minutes to working chat)
- [ ] Basic architecture diagram
- [ ] Example: basic message manipulation
- [ ] Example: streaming vs non-streaming
- [ ] Example: tool execution flow
- [ ] Troubleshooting guide

**Documentation Tooling:**
- [ ] Sphinx setup for Python (with autodoc extension)
- [ ] TypeDoc/JSDoc setup for JavaScript/TypeScript
- [ ] Auto-generated API reference published to docs site
- [ ] Docstring format guide for contributors

**Testing:**
- [ ] CI/CD pipeline setup (run on Python 3.9+, test coverage reporting)
- [ ] End-to-end test: user message → streaming → tool call → response
- [ ] Manual testing checklist

**Deliverable:** A working chat interface where we can:
- Send messages and get streaming responses
- See tool calls happen automatically
- Switch between different agent configs
- Use it for actual work
- **All features documented and tested**

### Stage 2: Production Polish (More Plugins + Features)

**Providers:**
- [ ] Anthropic provider
- [ ] Google Gemini provider
- [ ] Local model provider (Ollama)
- [ ] Provider capability detection
- [ ] Provider comparison guide

**Features:**
- [ ] Advanced web search with better citation handling
- [ ] Content filtering
- [ ] Context window management (smart trimming)
- [ ] Message transformation utilities
- [ ] Feature composition guide (using multiple features together)

**Tools:**
- [ ] Web search tool
- [ ] Code execution tool (sandboxed)
- [ ] API call tool
- [ ] Tool development guide (security considerations, best practices)

**Provider Extensions:**
- [ ] Citation extraction
- [ ] Token counter
- [ ] Reasoning trace parser

**Frontend:**
- [ ] Markdown rendering for messages
- [ ] Code syntax highlighting
- [ ] Better citation display
- [ ] Tool execution visualization
- [ ] Message editing
- [ ] Conversation branching
- [ ] Component tests with Storybook for visual documentation
- [ ] Accessibility tests
- [ ] Frontend user guide

**Configuration:**
- [ ] UI for plugin configuration (no more manual JSON)
- [ ] Live config updates
- [ ] Config presets/templates
- [ ] Tests for state update propagation
- [ ] User guide for configuration UI

**Testing:**
- [ ] Plugin test utilities and mock provider for plugin testing
- [ ] End-to-end tests for full conversation flows and multi-agent scenarios
- [ ] Performance benchmarks (baseline documented, regression tests)
- [ ] Test coverage: 90%+ for core, 80%+ for plugins

**Documentation:**
- [ ] Complete plugin development guide (step-by-step for each type, best practices, common pitfalls)
- [ ] Architecture deep-dive (design decisions, component diagrams, data flow)
- [ ] Complete API reference (examples for every public method)
- [ ] Example applications: research assistant, code review bot, customer support agent (all documented and tested)
- [ ] Video tutorials (getting started, building first plugin, advanced features)

### Stage 3: Cross-Language Support

**Core:**
- [ ] JavaScript/TypeScript Core SDK implementation
- [ ] Feature parity with Python core
- [ ] Subprocess adapter implementation
- [ ] JSON-RPC protocol
- [ ] Plugin wrapper as subprocess server
- [ ] Cross-language integration tests (Python core + JS plugin, JS core + Python plugin)
- [ ] Protocol compliance tests

**Testing:**
- [ ] Test all plugin types in both directions (Python↔JavaScript)
- [ ] Performance benchmarks: native vs cross-language overhead
- [ ] Compatibility test matrix documenting all combinations

**Documentation:**
- [ ] Cross-language plugin guide (when to use, performance considerations, debugging)
- [ ] JSON-RPC protocol specification
- [ ] Performance characteristics document with benchmarks
- [ ] Migration guides (Python plugin → JavaScript, JavaScript plugin → Python)
- [ ] Example: creating a cross-language plugin

### Stage 4: Ecosystem & Distribution

**Plugin System:**
- [ ] Plugin marketplace/registry
- [ ] Plugin discovery and installation CLI tool
- [ ] Version management with semantic versioning
- [ ] Plugin dependencies with dependency resolution
- [ ] Security scanning process
- [ ] Plugin submission guide

**Distribution:**
- [ ] PyPI package with installation guide and release checklist
- [ ] npm package with installation guide and release checklist
- [ ] Docker images with deployment guide
- [ ] Pre-built binaries
- [ ] Docker Compose examples

**Community:**
- [ ] Plugin template repositories (all types, fully documented with example tests)
- [ ] Example applications (customer support bot, research assistant, code review tool, data analysis agent, meeting summarizer)
- [ ] Tutorial series (beginner to advanced)
- [ ] Community guidelines (code of conduct, contribution guide, documentation standards, testing requirements)

**Advanced Features:**
- [ ] Multi-modal support (images, audio) with guide and examples for each modality
- [ ] Conversation persistence with serialization and database integration tests
- [ ] Cloud deployment guides (AWS, GCP, Azure, Kubernetes - all tested)
- [ ] Monitoring and observability with metrics collection and logging guide

> **Note:** Stage completion requires all tests passing with adequate coverage, all features documented, examples updated and tested, API reference current, and any migration guides written for breaking changes.

---

**Testing & Documentation Standards:**

All contributions must include:
1. **Tests**: Unit and integration tests for new functionality
2. **Documentation**: Docstrings, README updates, examples
3. **Type Hints**: Python type hints or TypeScript definitions
4. **Examples**: At least one executable example
5. **Coverage**: Minimum 80% test coverage for new code

These are not optional—they are part of the definition of "done" for any feature.

## Success Criteria

### Stage 1 Success (MVP)
- ✅ Can have a conversation with an LLM
- ✅ Streaming works and displays correctly
- ✅ Tool calls work automatically
- ✅ Can configure via JSON file
- ✅ Tests pass for Core SDK
- ✅ We use it ourselves for actual work

### Stage 2 Success (Production)
- ✅ Support 3+ providers
- ✅ 10+ plugins available
- ✅ Markdown rendering works
- ✅ Plugin configuration via UI
- ✅ Comprehensive documentation
- ✅ Others can use it without our help

### Stage 3 Success (Cross-Language)
- ✅ JavaScript core works
- ✅ Can use Python plugins from JavaScript core
- ✅ Can use JavaScript plugins from Python core
- ✅ Performance is acceptable for cross-language

### Stage 4 Success (Ecosystem)
- ✅ Plugin marketplace exists
- ✅ Available on PyPI and npm
- ✅ Community contributing plugins
- ✅ Multiple example applications
- ✅ Growing user base

---

**Living Document Notice:** This project plan represents our current understanding and intentions. As we build and learn, we will update this document to reflect new insights, changed priorities, and evolved designs. Implementation details, API designs, and architectural decisions are subject to change based on real-world usage, performance requirements, and developer feedback.

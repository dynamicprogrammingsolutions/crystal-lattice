# AGENTS.md

Guidelines for agents and contributors working in this repository. These rules apply repo-wide.

## Project Context (Essentials)
- Language targets: Python (core ready), JS planned later.
- Core SDK (Python): `core/python/agent_core` with tests in `core/python/tests`.
- Primary test runner: `pytest` with coverage.
- Architecture: Functional Core, Imperative Shell; plugins extend behavior without mutating core state.

## How To Run
```bash
# Install dev deps
cd core/python
pip install -e ".[dev]"

# Run tests (verbose + coverage in terminal)
pytest
# or generate HTML coverage
pytest --cov=agent_core --cov-report=html

# Type check, format, lint
mypy agent_core
black agent_core tests
ruff check agent_core tests
```

---

## Functional Programming Guidelines
Follow functional programming principles for all new code; refactor existing code toward this style when feasible.

- Core principles
  - Pure functions: same input → same output; avoid side effects.
  - Immutability: never mutate inputs/state; return new values.
  - First-class/composable functions: pass/return functions; prefer composition over inheritance.
- Architecture structure
  - Functional Core, Imperative Shell: keep business logic pure; isolate I/O at the boundaries.
  - Push side effects to edges: networking, filesystem, time/random live in infrastructure layers or adapters.
  - Layer separation: Presentation → Application (pure coordination) → Infrastructure (effects).
- Side-effect management
  - Isolate effects: place in dedicated modules/files; centralize invocation paths.
  - Dependency injection: pass effect handlers as parameters; avoid global singletons.
  - Effect tagging: make effectful operations explicit in names/structure.
  - Prefer central buses or interpreters to coordinate effects when needed.
- Code organization
  - Pure logic first: express rules as small pure functions; compose pipelines.
  - Prefer recursion/iterators and declarative style over raw loops and mutation where practical.
  - Separate data transformation from I/O; keep effect handlers thin and focused.
- Testing & maintenance
  - Pure core easily unit-tested; effects swappable via DI; explicit boundaries between pure and impure code.

---

## Testing Policy
High-level, maintainable testing aligned with our functional design. Do not weaken tests to accommodate bugs.

- Integrity
  - Never modify tests to mask bugs; don’t change assertions to fit incorrect behavior.
  - Don’t disable/skip tests except temporarily for valid reasons; document and re-enable promptly.
- Test-first mindset
  - Write tests before or alongside production code; tests are independent and order-agnostic.
  - Use clear, descriptive names and the Arrange–Act–Assert (AAA) pattern; one logical assertion per test.
- Coverage
  - Test public APIs, error paths, and boundaries; prioritize business logic and critical workflows.
  - Aim for meaningful tests over raw coverage metrics; minimum 80% coverage for new code.
- Design for testability
  - Prefer DI, pure functions, separation of concerns, and small units.
  - Allowed non-destructive refactors: extract methods/interfaces, inject dependencies, move config to services, split large classes, extract pure functions, use factories/builders.
- Mocking and test doubles
  - Minimize mocking; prefer real/in-memory deps and fakes/stubs.
  - Mock only external services, expensive ops, or non-determinism (time/random); mock interfaces, not concretes.
  - Verify interactions only when interaction is the behavior under test; keep mock setup simple.
- Maintainability
  - Hold test code to the same quality bar; extract fixtures/helpers; avoid duplication.
  - Use meaningful, realistic test data; employ builders/factories; mirror code structure in test layout; use setup/teardown appropriately.
- Integration & E2E
  - Validate plugin contracts and integration paths with real deps where practical; isolate and reset state.
  - Mock external HTTP only when necessary; ensure tests are deterministic and repeatable.
- Continuous improvement
  - Keep tests updated as requirements change; remove obsolete tests; monitor and optimize slow tests.
  - Ensure fast feedback, clear failure messages; fix flaky tests immediately.
- Anti-patterns to avoid
  - Don’t test implementation details or third-party libraries; don’t depend on execution order; don’t use production data.
  - Avoid overly broad integration tests when unit tests suffice; keep tests simpler than the code under test.

Repo specifics
- Use `pytest` (configured in `core/python/pyproject.toml`). Place Python tests under `core/python/tests` and name them `test_*.py`.
- Prefer unit tests for pure functions in `agent_core`; add integration tests covering plugin discovery, pipelines, streaming, and tool schemas.
- Keep examples executable and, where possible, assert on their outputs in tests.

---

## Documentation Rules
Documentation is developed alongside the code and treated as part of the deliverable.

- Documentation-as-code
  - Update docs as you implement; do not defer. Code without docs/tests is incomplete.
  - Every public function/class has docstrings and type hints.
  - Each plugin should include a concise README explaining purpose, config schema, and example usage.
- Executable examples
  - Examples must be runnable; prefer using them in tests/CI to prevent rot.
- Layered documentation (keep in sync)
  - Code level: docstrings + type hints (Python uses Google-style docstrings by default).
  - Module level: README per package/plugin with quick start and constraints.
  - API level: `docs/api/` reference kept consistent with current signatures and behavior.
  - Guide level: Tutorials/how-tos for common flows (streaming, tool loop, configuration).
  - Architecture level: High-level design and decisions; keep diagrams current with major changes.
- Documentation-first changes
  - For new features/APIs: draft usage docs first, review, then implement to match; finalize with tests ensuring behavior matches docs.
- Quality gates (definition of done)
  - Tests passing (≥80% coverage for new code), updated docs, type hints present, public APIs documented, at least one executable example.
- Style and tooling
  - Python docstrings: Google style; include Args, Returns, Raises, and clear examples where helpful.
  - Keep inline examples minimal and correct; prefer linking to tested examples when long.

## Types & Protocols Sync (Mandatory)
When you change any type or protocol definitions, you MUST update all of the following in the same change. Treat these as the authoritative documentation set for agents and contributors.

- Authoritative Spec: `TYPES_AND_PROTOCOLS.md`
  - Describes shared provider state model, plugin protocols, method signatures
  - Includes finalize tuple outputs, initialize_request return contract, and stateless transforms
  - Contains basic/streaming flow diagrams and notes on messages vs native_messages

- SDK Type Definitions: `core/python/agent_core/types.py`
  - Python Protocols for ProviderPlugin, ProviderExtensionPlugin, FeaturePlugin, ToolPlugin
  - Wrapper Protocols: ProviderWrapperProtocol, ExtensionWrapperProtocol, FeatureWrapperProtocol, ToolWrapperProtocol
  - Ensure signatures exactly match `TYPES_AND_PROTOCOLS.md` (names, params, tuple return shapes)

- Architecture Overview: `ARCHITECTURE.md`
  - Who owns state (provider wrapper), how state propagates, when it is discarded
  - Streaming vs finalize chains and where stateless transforms run
  - Updated data-flow steps with clear messages vs native_messages distinction

- API Reference: `docs/api/core-sdk.md`
  - Public `AgentCore` method signatures and behaviors
  - Plugin infrastructure descriptions reflecting shared state and finalize tuple contracts
  - Any example snippets must compile with current signatures

- Examples: `PLUGIN_EXAMPLES.md`
  - Provider: `finalize(native_messages, state) → (final_messages, native_messages, new_state)`; `call_api` returns 4‑tuple
  - Extension: shared-state lifecycle; `process_chunk(..., state, ...) → (..., new_state)`; `finalize` returns tuple; stateless `to/from_native_messages`
  - Feature: shared-state lifecycle; stateless transforms; `finalize(messages, final_messages, native_messages, state) → (final_messages, native_messages, new_state)`

- Core SDK README: `core/python/README.md`
  - Quick start and streaming examples use list of final messages, not single dict
  - Provider example reflects new signatures and tuple returns

- Project Plan: `PROJECT_PLAN.md`
  - References to spec remain accurate; any code snippets align with current contracts

- Tests and Dummies: `core/python/tests/*`
  - Dummy provider/extension/feature must compile against current Protocols

Enforcement
- Any PR that changes types or protocol definitions MUST update all files listed above and run tests.
- Keep “messages” (core) and “native_messages” (provider-native) consistent in docs and code.
- finalize MUST return a tuple everywhere; initialize_request MUST return state.
- Provider wrapper discards shared state after each completed request; apply update_state with UI settings after init on each request.

Checklist for Type/Protocol Changes
- [ ] Update `TYPES_AND_PROTOCOLS.md`
- [ ] Update `core/python/agent_core/types.py`
- [ ] Update `ARCHITECTURE.md`
- [ ] Update `docs/api/core-sdk.md`
- [ ] Update `PLUGIN_EXAMPLES.md`
- [ ] Update `core/python/README.md`
- [ ] Update references in `PROJECT_PLAN.md`
- [ ] Update dummies/tests if needed; run `pytest`

---

## Code Style & Tooling (Python)
- Python version: 3.9+.
- Formatting: `black` (line length 100).
- Linting: `ruff` (line length 100).
- Types: `mypy` with strictness appropriate to module; all public APIs typed.
- Keep functions small and composable; avoid mutable globals and side effects in core logic.

## Definition of Done (Recap)
- Functional: Pure/immutable core logic; side effects isolated.
- Tested: Unit + integration tests added/updated; fast, deterministic.
- Documented: Docstrings, READMEs, API docs, and at least one runnable example updated.
- Quality: Linted, formatted, type-checked; coverage target met.

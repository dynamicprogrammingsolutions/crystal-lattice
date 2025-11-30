# AGENTS.md

- Setup: `cd core/python && pip install -e ".[dev]"`
- Run tests (unit + ollama; integration skipped by default): `pytest core/python/tests -q`
- Run OpenRouter integration tests: `pytest core/python/tests -m openrouter -q`
- Run all integration tests: `pytest core/python/tests -m integration -q`
- Run only ollama tests: `pytest core/python/tests -m ollama -q`
- Run single test: `pytest core/python/tests/test_core.py::test_create_session -q`
- Run example tests: `pytest core/python/examples/tests -qs`
- Coverage: `pytest core/python/tests -v --cov=core/python/agent_core --cov-report=term-missing`
- Lint: `ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- Format: `black core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- Typecheck: pyright
- Python: >=3.10
- Style: functional/immutable style (no mutation)
- Tests: core/python/tests; pytest config in core/python/pyproject.toml
- After updating examples (core/python/examples): pytest core/python/examples/tests -qs; python scripts/generate_examples_md.py
- Documentation: PROJECT_PLAN.md, ARCHITECTURE.md, TYPES_AND_PROTOCOLS.md, EXAMPLES.md, docs/api/core-sdk.md
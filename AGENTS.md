# AGENTS.md

- Setup: `cd core/python && pip install -e ".[dev]"`
- Run tests: `pytest core/python/tests -q`
- Run single test: `pytest core/python/tests/test_core.py::test_create_session -q`
- Run example tests: `pytest examples/tests -qs`
- Coverage: `pytest core/python/tests -v --cov=core/python/agent_core --cov-report=term-missing`
- Lint: `ruff check core/python/agent_core tests examples`
- Format: `black core/python/agent_core core/python/tests plugins examples`
- Typecheck: pyright
- Python: >=3.9
- Style: functional/immutable style (no mutation)
- Tests: core/python/tests; pytest config in core/python/pyproject.toml
- After updating examples (./examples): pytest examples/tests -qs; scripts/generate_examples_md.py
- Documentation: PROJECT_PLAN.md, ARCHITECTURE.md, TYPES_AND_PROTOCOLS.md, EXAMPLES.md, docs/api/core-sdk.md
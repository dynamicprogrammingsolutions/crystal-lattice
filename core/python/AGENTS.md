# Core Python package guidance

This package owns the provider-agnostic conversation SDK in `agent_core`, the
application orchestration layer in `agent_app`, and older package-local plugins
kept for compatibility, tests, and a small set of Core features. The terminal
and HTTP application is owned by `application/python`.

Start with:

- `README.md` for installation, package boundaries, and first use;
- `docs/index.md` for package-user documentation;
- `docs/development/index.md` for implementation and maintainer guidance;
- `agent_core/types.py` and other source docstrings for generated Python
  reference.

Keep user-facing SDK and application-layer behavior under `docs/`. Put current
Core implementation, testing, and maintenance guidance under
`docs/development/`. Shared plugin-author documentation belongs under
`plugins/docs/`; link to it instead of creating a second protocol guide here.

Treat `Message` and `Session` as immutable values. Their dataclasses are
frozen, while nested dictionaries and lists are treated as immutable by
convention. Use `AgentCore` operations that return new values rather than
mutating nested containers directly.

Run focused checks from the repository root:

```bash
pytest core/python/tests -q -m "not integration"
pytest core/python/examples/tests -q -m "not integration"
ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins
```

Run integration, API, slow, and local-service markers deliberately, and report
gated tests as not run when their prerequisites are not enabled. When changing
an example, run its test before regenerating `docs/examples.md` with
`python scripts/generate_examples_md.py`.
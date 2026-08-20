# Application Python package guidance

This package owns the installable `crystal-lattice` terminal and HTTP
application. It combines the application layer from `agent_app` with the
terminal, FastAPI, Bonjour, bridge, runtime-layout, and distribution code under
`agent_terminal_app`.

Start with:

- `README.md` for installation, operation, connectivity, and release behavior;
- `docs/index.md` for package-user documentation;
- `docs/development/index.md` for current implementation and maintainer guides;
- `agent_terminal_app/AGENTS.md` for detailed terminal/server integration
  constraints.

Keep user-facing application behavior under `docs/` and current internals under
`docs/development/`. Cross-package contracts remain under root
`docs/development/` when no package provides the authoritative scope.

Primary verification:

```bash
pytest application/python/tests -q
```

Use focused integration, API, Docker, or provider markers when a changed claim
crosses those boundaries. Do not treat skipped gated coverage as a successful
run.
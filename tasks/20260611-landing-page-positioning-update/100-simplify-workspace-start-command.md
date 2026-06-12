# Simplify Workspace Start Command

Create a simpler CLI path for the common website demo: start Crystal Lattice in
a project folder, enable the server and terminal UI, bind for local-network
clients, and advertise with Bonjour.

## Requirements checklist

- [ ] Design a short command such as `crystal-lattice start --mobile` or `crystal-lattice workspace`.
- [ ] Preserve the explicit long-form flags for advanced users.
- [ ] Ensure the shortcut uses local config, starts server plus console, binds to a LAN-reachable host, chooses a sensible port, and enables Bonjour.
- [ ] Update docs/help text so the website can use the simplified command safely.
- [ ] Add tests for command expansion and any new CLI parsing behavior.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`

## Context

The current website demo command is accurate but long:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

The landing page would be more approachable if this had a memorable shortcut
that still maps to the same behavior.
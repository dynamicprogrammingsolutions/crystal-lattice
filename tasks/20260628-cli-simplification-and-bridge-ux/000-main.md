# CLI Simplification and Bridge UX

Simplify the Crystal Lattice CLI so that a typical local development session
only needs `crystal-lattice-cli-dev --console --server --enable-bonjour --enable-bridge`,
with automatic port selection, persistent bridge-server-id, project-name
generation, default file logging, and improved startup output. On the frontend,
make bridge URLs easy to save and reuse.

---

## Task checklist

- [x] `tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md`
- [x] `tasks/20260628-cli-simplification-and-bridge-ux/020-cli-simplification-bridge-host-logging.md`
  - DEPENDS ON `tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md`
- [x] `tasks/20260628-cli-simplification-and-bridge-ux/030-startup-output-improvements.md`
  - DEPENDS ON `tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md`
  - DEPENDS ON `tasks/20260628-cli-simplification-and-bridge-ux/020-cli-simplification-bridge-host-logging.md`
- [ ] `tasks/20260628-cli-simplification-and-bridge-ux/040-frontend-saved-bridge-urls.md`
- [ ] `tasks/20260628-cli-simplification-and-bridge-ux/050-cli-e2e-integration-tests.md`
  - DEPENDS ON `tasks/20260628-cli-simplification-and-bridge-ux/020-cli-simplification-bridge-host-logging.md`
  - DEPENDS ON `tasks/20260628-cli-simplification-and-bridge-ux/030-startup-output-improvements.md`

---

## Context

### Current pain point

A normal local development session currently requires:

```bash
cd /Users/ferenci84/Dev/Kuhar_Balint/iocharts && crystal-lattice-cli-dev \
  --host 0.0.0.0 --port 8090 \
  --bridge-url wss://crystal-bridge.dynamicprogrammingsolutions.com/ws/websocket \
  --enable-bonjour --bonjour-service-name "ioCharts" \
  --server --console --bridge-display-name "iocharts" \
  --log-level INFO --log-file ".crystal/crystal.log" \
  --fastapi-log-file "--log-file ".crystal/crystal.log" \
  --bridge-server-id="b19cb3bf-eccb-42b8-879f-ead70eaf7db9"
```

The goal is to reduce this to:

```bash
cd /Users/ferenci84/Dev/Kuhar_Balint/iocharts && crystal-lattice-cli-dev \
  --console --server --enable-bonjour --enable-bridge
```

### Key files

- **CLI entrypoint**: `application/python/agent_terminal_app/__main__.py`
  - `main()` (line ~590): arg parsing, logging config, server/console launch.
  - `_build_server_integration_config()` (line ~230): builds `ServerIntegrationRuntimeConfig` from CLI args.
  - `_configure_logging()` (line ~22): configures stdlib + structlog logging.
  - `_configure_fastapi_logging()` (line ~100): routes uvicorn logs to a file.
  - Startup prints at lines ~830-840 (bonjour/bridge enabled) and ~900 (config/sessions dir).
  - `_set_terminal_title()` (line ~190): prints "Setting terminal title to: ..." (redundant).
  - `_args()` test helper in `application/python/tests/test_cli_environment_isolation.py` (line ~17).

- **Server**: `application/python/agent_terminal_app/server.py`
  - `BonjourRuntimeConfig` (line ~63), `ServerIntegrationRuntimeConfig` (line ~69).
  - `configure_integrations()` (line ~78): sets explicit integration config.
  - `_on_startup()` (line ~405): starts bonjour + bridge client.
  - `_on_shutdown()` (line ~485): cleanup.
  - `run_api()` (line ~3462): uvicorn launch helper.

- **Bonjour**: `application/python/agent_terminal_app/bonjour.py`
  - `_get_local_ip()` (line ~52): detects non-loopback LAN IPv4 — already exists, can be reused for startup output.

- **Bridge client**: `application/python/agent_terminal_app/bridge_client.py`
  - `BridgeConfig` (line ~54): dataclass with `bridge_url`, `server_id`, `display_name`, etc.
  - `create_bridge_client_from_env()` (line ~912): env-based fallback for direct uvicorn launches.

- **Runtime layout**: `application/python/agent_terminal_app/runtime_layout.py` and `runtime_layout.json`
  - `user_paths`: `local_config` → `./.crystal/config.json`, `home_config` → `~/.crystal/config.json`, `default_sessions_dir` → `./.crystal/sessions`.

- **Application config**: `core/python/agent_app/application_future.py`
  - `AgentApplication.get_application_config()` (line ~2121): returns the `application` section of config.json — natural home for an optional `bridge_url` key.

- **Default config**: `application/python/agent_terminal_app/default_config/config.json`
  - Has an `application` section with keys like `tool_output_line_limit`, `cloud_agent`, etc.

- **Existing tests**: `application/python/tests/test_cli_environment_isolation.py`, `application/python/tests/test_bonjour_module.py`.

- **Mobile app**: `mobile/crystal-lattice-control-rn/App.tsx`
  - Bridge connection wizard: `renderBridgeConnection()` (line ~580) — manual URL entry each time.
  - `connectToBridge()` (line ~470): connects to bridge, lists servers.
  - `ConnectionsScreen.tsx`: shows saved connections (all types mixed).

- **Frontend SDK**: `packages/frontend-sdk/src/connections/`
  - `types.ts`: `ConnectionRecord` union (manual, discovery, bridge, cloud).
  - `store.ts`: `loadConnections`/`saveConnections` with `CONNECTIONS_STORAGE_KEY`.
  - `index.ts` (line ~200): exports connection types and store functions.

### Design decisions (approved)

1. **Profile file location**: `~/.crystal/projects.json` (user-level registry keyed by absolute project path) + `.crystal/profile.json` (project-local override). Both JSON, user-editable.
2. **Port auto-selection**: Bind to port 0 to let the OS assign a free port, then persist it. On next run, try the persisted port; if occupied, pick a new one and update the file.
3. **Bridge URL resolution order**: CLI `--bridge-url` > `.crystal/profile.json` > `~/.crystal/projects.json` > `application.bridge_url` in config.json > disabled.
4. **Host auto-selection**: `0.0.0.0` when bonjour is enabled and `--host` not explicitly set. `--host` always wins as the override.
5. **Default log file**: `.crystal/crystal.log` (relative to CWD). `--no-log-file` to disable. `--log-file` overrides the path. FastAPI logs go to the same file when `--fastapi-log-file` is absent.
6. **Frontend saved bridges**: Separate from connection records. A lightweight list of `{url, label?, lastUsedAt}` stored in AsyncStorage via the SDK.
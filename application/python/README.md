# crystal-lattice-cli

`crystal-lattice-cli` installs the `crystal-lattice` command. The command can
run:

- a FastAPI HTTP API for sessions, messages, requests, plugins, config, and
  application actions
- a `prompt_toolkit` terminal client with slash commands and keyboard shortcuts
- both together, sharing the same session store and in-memory event stream
- optional Bonjour/mDNS advertisement for LAN discovery
- optional bridge registration for paired mobile access across networks

The internal Python module is still `agent_terminal_app`, so
`python -m agent_terminal_app` remains useful for development and debugging.

Documentation:

- [Package documentation](docs/index.md)
- [Quickstart](docs/quickstart.md)
- [Terminal guide](docs/terminal.md)
- [Application configuration](docs/configuration.md)
- [Configuration mixins](docs/configuration-mixins.md)
- [Configuration variants](docs/configuration-variants.md)
- [Session snapshots](docs/session-snapshots.md)
- [Application runtime development](docs/development/index.md)

## Installation

### Binary Install

The bundled installer includes Python and the app runtime. It is the easiest
path for end users on macOS, Linux, or Git Bash on Windows:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

The default install locations are:

```text
~/.local/opt/crystal-lattice-cli/<asset-stem>/
~/.local/bin/crystal-lattice
```

Pinned install:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | VERSION=0.1.1 bash
```

Review-first install:

```bash
curl -fsSLO https://download.crystallattice.dev/crystal-lattice-cli/install.sh
less install.sh
bash install.sh
```

Supported shell-installer assets:

```text
darwin-amd64
darwin-arm64
linux-amd64
windows-amd64
```

On Windows, run the shell installer from Git Bash, MSYS2, or Cygwin. Native
PowerShell installation is not implemented yet; use the release `.zip` asset
directly if you do not use a Bash-compatible shell.

### Python Install

For users with Python 3.10+ available:

```bash
pipx install crystal-lattice-cli
crystal-lattice --help
```

You can also install into an active virtualenv:

```bash
pip install crystal-lattice-cli
```

### Source Install

From the repository root:

```bash
python -m pip install -e "core/python[dev]"
python -m pip install -e "application/python[dev]"
```

For local source development, install `core/python` first so
`application/python` resolves against your checkout of the core SDK. This
editable install still does not install repo-root plugin packages; install
`plugins/<plugin-name>[dev]` separately when you are actively changing one.

For binary build work:

```bash
python -m pip install -e core/python -e "application/python[binary]"
```

## Testing

For contributors and local validation:

- Fast default package run:

  ```bash
  pytest application/python/tests -q
  ```

  This package defaults to `-m 'not integration and not docker'`.

- Non-API integration:

  ```bash
  pytest application/python/tests -m 'integration and not api and not slow_integration and not docker' -q
  ```

- Hosted API integration:

  ```bash
  pytest application/python/tests -m 'integration and api and not slow_integration and not docker' -q
  ```

- Docker-only bundle validation:

  ```bash
  pytest application/python/tests -m docker -q
  ```

The application test suite bootstraps the repo root `.env` for local
real-provider tests and does not overwrite already-exported environment
variables.

## Running Crystal Lattice

### Quick Start

For a typical local development session with mobile access:

```bash
crystal-lattice --console --server --enable-bonjour --enable-bridge
```

This automatically:

- Selects a free port and persists it in `~/.crystal/projects.json` for reuse.
- Binds to `0.0.0.0` (so the server is reachable on the LAN via Bonjour).
- Generates a stable bridge-server-id and persists it.
- Uses the project directory name as the Bonjour service name and bridge display name.
- Resolves the bridge URL from `--bridge-url`, `.crystal/profile.json`, `~/.crystal/projects.json`, or `application.bridge_url` in config.json.
- Logs to `.crystal/crystal.log` by default.

All of these defaults can be overridden with explicit flags.

### Project Profiles

Per-project settings (name, port, bridge-server-id, bridge-url) are persisted
in two files:

- **`~/.crystal/projects.json`** — user-level registry keyed by absolute project path.
  Auto-generated values (port, bridge-server-id, project name) are stored here.
- **`.crystal/profile.json`** — project-local override file (same keys, higher priority).
  Any subset of keys may be present; only the keys that exist override the user-level entry.

Resolution order for each setting:

```text
CLI flag > .crystal/profile.json > ~/.crystal/projects.json > built-in default
```

`bridge_url` is never auto-generated — it must be provided by the user via CLI,
profile, or config. When `--enable-bridge` is set but no URL is found, bridge
registration is skipped with a warning.

### Server Only

With no mode flags, `crystal-lattice` runs the HTTP API server:

```bash
crystal-lattice
```

Defaults:

```text
host: 127.0.0.1
port: 8000
```

Bind to all interfaces when another device, such as a phone, needs to reach the
server:

```bash
crystal-lattice --host 0.0.0.0 --port 9000
```

### Terminal Only

Run only the terminal UI:

```bash
crystal-lattice --console
```

In this mode no HTTP server is started in the process.

### Server And Terminal Together

Run the API server in a background thread and the terminal UI in the foreground:

```bash
crystal-lattice --server --console
```

For mobile testing from a local project/work directory:

```bash
mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo
crystal-lattice --server --console --config-local --host 0.0.0.0 --port 9000
```

In combined mode, terminal and HTTP requests share an event store. Events from
requests sent through one frontend can be observed by the other when they refer
to the same session.

## Configuration

For plugin package specs, mixins, placeholders, enablement, and installation
policy, see the [application configuration guide](docs/configuration.md).

### Config Search Order

Unless `--config` or `--config-local` is supplied, the command searches for:

1. `./.crystal/config.json`
2. `~/.crystal/config.json`

If neither exists, it creates a default config at the runtime layout's
`default_config` path.

### Local Config With `--config-local`

Use `--config-local` when you want the app state to belong to the current
working directory:

```bash
crystal-lattice --config-local --server --console
```

This forces `./.crystal/config.json`, creating it from the bundled default
template when it is missing.

### Explicit Config

Use a specific config file:

```bash
crystal-lattice --config path/to/config.json --server --console
```

If the file is missing, the command creates a default config at that path.

### Sessions Directory

Set the session store explicitly:

```bash
crystal-lattice --sessions-dir ./.crystal/sessions
```

Source installs default to `./.crystal/sessions`. Bundled installs default to a
user-owned sessions directory from the bundled runtime layout, currently
`~/.crystal/sessions`.

### `.env` Files

The app loads `.env` files related to the active config path. This is the
recommended place for provider keys during local use:

```bash
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
```

### Runtime Layout

Inspect the active source or bundled layout:

```bash
crystal-lattice --runtime-layout-json
```

Runtime paths are described by `agent_terminal_app/runtime_layout.json` in
source installs. The binary build script generates a bundled manifest matching
the PyInstaller layout.

Important layout behavior:

- `CONFIG_DIR` always resolves to the directory of the active config file.
- `BUILTIN_PLUGINS` comes from the runtime layout and points at bundled plugin
  sources in binary installs.
- Config files, sessions, auth state, and plugin install caches are user-owned
  state and stay outside the bundle.

Literal values can opt out of placeholder resolution by wrapping them as
`{"$raw": "..."}` in JSON config. The wrapped value is passed through exactly
as written, including `${env:...}` or `${file:...}` text.

## Provider Credentials


The generated default config includes several real-provider agents. Useful
model requests require the corresponding credentials, for example:

```bash
export OPENAI_API_KEY=...
export OPENROUTER_API_KEY=...
export ANTHROPIC_API_KEY=...
```

The default Claude routes are provider-qualified:

- `claude-openrouter` uses Claude through OpenRouter.
- `claude-anthropic` uses the direct Anthropic API and selects model-specific
  reasoning defaults, beta, and context-management settings through
  configuration variants. The Anthropic reasoning-controls extension derives
  available mode and effort UI from model capabilities or known fallbacks. It
  defaults to Sonnet 5 and can select supported Haiku, Sonnet, Opus, Fable, and
  Mythos models from model discovery.

For no-key development from a source checkout, use the echo config:

```bash
cd application/python
mkdir -p .crystal
cp agent_terminal_app/config_echo_app.json .crystal/config.json
crystal-lattice --server --console --config-local
```

The echo provider is useful for UI, session, and connectivity checks because it
does not make network calls.

## Mobile Connectivity

The React Native app lives in
`mobile/crystal-lattice-control-rn`. See its README for platform setup and
troubleshooting.

### Direct IP

Start the server on all interfaces:

```bash
crystal-lattice --server --console --config-local --host 0.0.0.0 --port 9000
```

Find your computer's LAN IP. On macOS Wi-Fi:

```bash
ipconfig getifaddr en0
```

In the mobile app:

```text
Manual Address -> host: <computer LAN IP> -> port: 9000 -> Connect
```

### Bonjour/mDNS

Advertise the HTTP API over Bonjour:

```bash
crystal-lattice --server --console --enable-bonjour
```

This automatically binds to `0.0.0.0` and uses the project directory name as the
service name. Common options:

- `--enable-bonjour` - turn Bonjour advertisement on.
- `--bonjour-port` - override the advertised port; defaults to the server port.
- `--bonjour-service-name` - set the display name shown in discovery clients.
- `--host` - override the bind address (default: `0.0.0.0` with `--enable-bonjour`).

Verify on macOS:

```bash
dns-sd -B _http._tcp .
```

In the mobile app:

```text
Automatic Discovery -> choose the advertised server
```

### Bridge

Start a local Docker bridge from the repository root:

```bash
cd bridge-elixir
docker-compose up -d
curl http://localhost:4000/health
```

Register Crystal Lattice with the bridge:

```bash
crystal-lattice --server --console --enable-bonjour --enable-bridge \
  --bridge-url ws://localhost:4000/ws/websocket
```

Or, to avoid passing `--bridge-url` every time, add it to `.crystal/profile.json`:

```json
{"bridge_url": "ws://localhost:4000/ws/websocket"}
```

or to `config.json` under the `application` section:

```json
{"application": {"bridge_url": "ws://localhost:4000/ws/websocket"}}
```

Then simply:

```bash
crystal-lattice --server --console --enable-bonjour --enable-bridge
```

In the mobile app:

```text
Bridge Service -> ws://<bridge-host>:4000/ws/websocket -> select server -> enter pairing code
```

For a physical phone connecting to a bridge on your computer, use the
computer's LAN IP in the bridge URL, for example
`ws://192.168.1.25:4000/ws/websocket`.

Common bridge options:

- `--enable-bridge` - enable bridge registration (URL resolved from CLI, profile, or config).
- `--bridge-url` - explicitly set the bridge URL (overrides profile/config).
- `--bridge-display-name` - human-friendly server name shown to clients.
- `--bridge-location` - optional display metadata.
- `--bridge-local-http-base` - override the local server URL used by the bridge.
- `--bridge-http-base` - override the public bridge HTTP origin used by v2 body
  downloads/uploads. By default this is derived from `--bridge-url`.
- `--bridge-server-id` - provide a stable server id.
- `--bridge-exit-on-superseded` - exit if the bridge reports this server was replaced.
- `--bridge-local-guard` - opt into a local lockfile guard for the bridge server id.
- `--bridge-takeover-local` - with the local guard, try to terminate and replace
  the existing local process.

The equivalent environment override for the public HTTP origin is
`BRIDGE_HTTP_BASE_URL`. The server WebSocket remains the registration and
control channel. For HTTP/hybrid frontends, request bodies are downloaded from
the bridge and local response bodies are uploaded to it as raw HTTP byte
streams; only status, headers, paths, and short-lived transfer credentials use
the WebSocket.

Maintainers can find lifecycle, legacy/v2 forwarding, header, cancellation,
and test ownership details in
[`docs/development/bridge-server-adapter.md`](docs/development/bridge-server-adapter.md).

### Bonjour + Bridge Together

The simplest full-setup command:

```bash
crystal-lattice --console --server --enable-bonjour --enable-bridge
```

LAN clients can use Bonjour/direct HTTP. Remote or cross-network clients can use
the bridge pairing flow.

## Terminal Usage

Run the interactive client with `crystal-lattice --console`. Important commands
include `/help`, `/session`, `/agent`, `/send`, `/cancel`, `/list`,
`/tool-output`, and `/exit`.

`/tool-output one-line` keeps tool-heavy requests compact while preserving
full results for `/list <index>`. The terminal bottom toolbar reports active
request, LLM, and tool phases without adding animation frames to scrollback.
User, System, Assistant, and Tool message headers are separated by an empty
line and display their session index when the event provides one.

See the [terminal guide](docs/terminal.md) for command syntax, keyboard
shortcuts, startup help, progress behavior, tool-output configuration, session
filters, plugin controls, and non-interactive operation.

## Logging

By default, logs are written to `.crystal/crystal.log`:

```bash
crystal-lattice --console --server
# logs to .crystal/crystal.log automatically
```

Override the log file path:

```bash
crystal-lattice --log-file app.log
crystal-lattice --console --log-file console.log
crystal-lattice --server --console --log-file combined.log
```

Disable default file logging:

```bash
crystal-lattice --no-log-file
```

Set log level:

```bash
crystal-lattice --log-level DEBUG
crystal-lattice --console --log-level INFO
```

When running server and terminal together, FastAPI/uvicorn logs are routed to
the same file as the main log file by default. Use `--fastapi-log-file` to
route them separately:

```bash
crystal-lattice --server --console --fastapi-log-file fastapi.log
```

## Non-Interactive Mode (--no-tty)

When running `--console` in CI, subprocess tests, or other non-interactive
contexts where no TTY is available, use `--no-tty`:

```bash
crystal-lattice --console --server --no-tty
```

`--no-tty` runs the full console code path (session creation, event polling,
completer setup) using `prompt_toolkit`'s pipe input and dummy output. The
prompt blocks on a pipe instead of reading from stdin. SIGTERM causes a
clean exit (EOF is sent to the pipe, the prompt loop breaks, and the server
shuts down).

This is useful for:
- CI pipelines and automated testing
- Running `--console --server` in Docker containers without a TTY
- Integration tests that need to verify the console startup path

## HTTP API Overview

Important routes include:

- `GET /api/hello` - simple connectivity check used by clients.
- `GET /api/data`, `PUT /api/data` - demo endpoints used by the mobile app.

## Cloud Orchestrator

The terminal/server can be configured with a cloud orchestrator URL so an
application action can start a cloud agent for a session and return a copyable
cloud connection link.

CLI startup values are exposed to config placeholders:

```bash
crystal-lattice \
  --server \
  --cloud-orchestrator-url https://cloud.example.com \
  --cloud-orchestrator-token "$CLOUD_ORCHESTRATOR_TOKEN"
```

Quick-start config:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/cloud-agent-app"
  ],
  "application": {
    "cloud_agent": {
      "orchestrator_url": "${env:CLOUD_ORCHESTRATOR_URL}",
      "orchestrator_token": "${env:CLOUD_ORCHESTRATOR_TOKEN}",
      "workspace_dir": ".",
      "project_config_path": "${env:WORKING_DIR}/.cloud-agent/cloud-agent.json",
      "default_transfer_up_profile": "working-tree-current-state",
      "default_sync_down_profile": "working-tree-patch"
    }
  }
}
```

The default bundled profiles are selected automatically. Projects can usually
customize cloud behavior with repo-local hooks instead of inventing project-only
bundled profiles:

- `.cloud-agent/local-stage`
- `.cloud-agent/install-cloud`
- `.cloud-agent/validate-cloud`

Local hook validation does not require the orchestrator service. Run the shared
local-Docker validation flow directly from the main CLI:

```bash
crystal-lattice validate-cloud
```

Useful flags:

```bash
crystal-lattice validate-cloud --workspace-dir /path/to/project
crystal-lattice validate-cloud --keep-temp-dir
crystal-lattice validate-cloud --cache-dir /path/to/stable/cache
crystal-lattice validate-cloud --runtime-build-context /path/to/context --runtime-dockerfile /path/to/Dockerfile
```

The command runs the selected container profile. The canonical default config
declares the default Dockerfile runtime profile explicitly. Image-mode profiles
run the configured image, and Dockerfile-mode profiles stage the configured
context plus build assets, compute a digest, and build/reuse the local image.
Custom image names are treated as user-owned: validation trusts them when
present and fails clearly when they are missing unless explicit runtime build
overrides or Dockerfile profile metadata are provided.
When `--cache-dir` is provided, it is bind-mounted to `/cloud-agent/cache` so
plugin and pip caches persist across validation runs.

The default config also includes a `cloud-script-author` agent for creating
these hooks from ordinary project guidance. It uses the project's normal
`AGENTS.md`/README setup instructions and points directly at the bundled
authoring guide, which is in the agent's allowed read paths:

```text
${env:BUILTIN_PLUGINS}/cloud-agent-app/docs/cloud-script-authoring.md
```

The full cloud profile reference lives in
[`plugins/cloud-agent-app/README.md`](../../plugins/cloud-agent-app/README.md),
including:

- the `validate-cloud` command and its built-in smoke contract
- container profile image/Dockerfile modes, build assets, cache mounts, and
  runtime mounts
- the flattened `transfer_up_profiles` schema
- the bundled script tree under `default_config/cloud-agent/profiles/`
- the standard repo-local hook conventions and optional-hook behavior
- the complete config example and field-by-field reference

The authoring guide tells agents to add project container profiles only when the
runtime image must change. Project source remains a runtime workspace mount; a
Dockerfile profile may use project files only through explicit stable
`build_assets` such as package manifests or lockfiles.

`connection_key` is optional. When omitted, the cloud plugin derives an opaque
stable key from the local config/workspace context so multiple local sessions
can share one cloud connection while still running as separate cloud instances.
The orchestrator treats this key as plugin-owned opaque data.

`application.cloud_agent.disabled_plugins` is a cloud-only plugin-spec filter
applied during portable config generation. Each entry must match an exact
plugin spec string from a `plugins` list, for example
`path:${env:BUILTIN_PLUGINS}/session-asset-attachments`. Matching specs are
removed from the generated cloud runtime config from the top-level `plugins`
list and from any provider or agent `plugins` lists. This does not affect the
local runtime config.

The managed-SSH byte-transfer adapter is platform-owned. By default it runs the
packaged rsync-over-SSH adapter script against the orchestrator's restricted
transfer slot. Projects can override `managed_ssh.adapter_script` for unusual
transport needs, but workspace selection should stay in repo-local hook and
profile scripts.

For deployments where the orchestrator HTTP endpoint and managed-SSH endpoint
are different hosts, such as AWS CloudFront in front of an EC2 Docker host, the
deployed orchestrator should be configured with its own transfer public host.
The local app normally only needs `orchestrator_url` and `orchestrator_token`;
it uses the SSH endpoint returned by `POST /transfers`. Advanced/manual
deployments may still set `application.cloud_agent.transfer_public_host` to
override the orchestrator-advertised transfer host.

When a cloud agent starts, the local action generates a cloud runtime config
under `.cloud-agent/config/config.json`, removes the local
`application.cloud_agent` control-plane section, and copies the configured
`CONFIG_DIR` asset tree to `.cloud-agent/config/assets/`. The cloud runtime
sets `CONFIG_DIR` to that copied asset tree and `WORKING_DIR` to the cloud
workspace. Environment variables referenced by config placeholders are
transferred through `.cloud-agent/env/runtime.env` according to `runtime_env`.
Values are never included in action display payloads.

The default `config_assets.exclude` keeps `.env`, `.env.*`, `auth`, `state`,
logs, sessions, and plugin caches out of the copied config assets. To opt in a
specific excluded config file, use `config_assets.include_excluded`, for example
`auth/chatgpt-auth.json`. To load an env file as runtime environment variables,
prefer `runtime_env.env_files`, for example `.env.cloud`.

- `POST /sessions` - create a session.
- `GET /sessions` - list sessions.
- `POST /sessions/request-statuses` - derive lightweight status for explicitly
  supplied session IDs without listing all sessions.
- `GET /sessions/{session_id}/messages` - list session messages.
- `POST /sessions/{session_id}/messages` - append a message.
- `POST /sessions/{session_id}/send` - run the model/tool loop.
- `POST /sessions/{session_id}/send_message` - append and send in one call.
- `GET` and `POST /sessions/{session_id}/snapshots` - list or create session
  recovery points. Message deletion and successful OpenAI native compaction
  also create automatic pre-mutation snapshots; see the
  [session snapshot guide](docs/session-snapshots.md).
- `GET /events` - poll request/session events.
- `GET /application/notifications` - load the active application-notification
  snapshot; use `include_terminal=true` for terminal records.
- `POST /application/notifications/{notification_id}/dismiss` - persist
  application-notification dismissal with optional revision checking.
- `GET /sessions/{session_id}/notifications` - list active session
  notifications; use `include_terminal=true` for terminal records.
- `POST /sessions/{session_id}/notifications/{notification_id}/dismiss` -
  persist session-notification dismissal with optional revision checking.
- Application notification events are polled without a session filter. Session
  notifications use the same endpoint with `session_id` and persist in session
  metadata. Both use standard `banner`, `inline`, and `modal` display
  presentations.
- `POST /requests/{request_id}/cancel` - cancel an active request.
- `GET /agents` - list configured agents.
- `PATCH /sessions/{session_id}/agent` - change a session's agent.
- `GET /sessions/{session_id}/plugins` - list session plugins.
- `PUT /sessions/{session_id}/plugins` - update enabled session plugins.
- `GET /application/ui-schema`, `POST /actions`, and `POST /sessions/{session_id}/actions` - application UI/actions.

Request admission and execution are application-layer behavior. FastAPI and
the terminal delegate to the same `AgentApplication` session-request
coordinator:

- `start_session_request(...)` starts from existing history;
- `start_session_request_with_message(...)` atomically appends and starts;
- `run_session_request(...)` provides the synchronous equivalent;
- `get_active_session_request_id(...)` exposes the shared single-flight state.

The HTTP adapter retains payload validation, idempotency keys, status mapping,
and serialization. It does not own request worker threads, active-request
state, or event publication. Maintainers should start with
[`docs/development/request-execution.md`](docs/development/request-execution.md)
for the complete application request lifecycle.

Requests and longer-lived plugin work also share minimal active operation
registration and admission. See
[`docs/development/operations.md`](docs/development/operations.md) for session
exclusivity, lookup, managed-process ownership, plugin-owned status, and the
future extensible operations-menu direction.

Application notifications use a durable SQLite store by default. Configure its
path under `application.notifications.store`:

```json
{
  "application": {
    "notifications": {
      "store": {
        "type": "sqlite",
        "path": "${env:CONFIG_DIR}/application-notifications.sqlite3"
      }
    }
  }
}
```

Relative paths are resolved beside the active config file. The runtime opens
the store once and shares it across replacement `AgentApplication`
generations. Changing the path requires restarting the owning runtime; an
inner application reload does not switch or migrate notification databases.

The mobile and desktop Sessions headers use one pinnable action bar for Server
settings, Refresh sessions, New session, and contributed
`application_action` entries. Pin state is frontend-local and
connection-scoped. On macOS the menu uses a native popover and Server settings
opens a separate React window. Every desktop banner source uses one
connection-aware top rail; modal displays use a separate React window.

Run the command help for the complete CLI surface:

```bash
crystal-lattice --help
```

## Release And Distribution

### Making A CLI Release

The repository root `package.json` provides release scripts for the production
download domain:

1. Bump the CLI version:

   ```bash
   npm run release:cli:version:bump-patch
   ```

   This updates `application/python/pyproject.toml` and the documentation
   version references. Review the diff, then commit to `main` and push. For
   minor or major bumps, edit the version manually. The release tag must match
   `crystal-lattice-cli-v<version>`.

2. Optional preflight:

   ```bash
   npm run release:cli:plan
   npm run release:cli:gate
   ```

   `release:cli:plan` is a dry run: it prints every command without
   executing anything. `release:cli:gate` performs the full local
   validation for real — release state, release commit, download
   configuration, and the local gate (pip install and both pytest
   suites) — without creating or pushing the release tag.

3. Create the release:

   ```bash
   npm run release:cli
   ```

   This validates the local release state and download configuration, runs the
   fast test suites, pushes the release tag, and watches the GitHub Actions
   run through the platform build matrix, GitHub Release publishing, and
   download-domain publication. The command prints each phase as a numbered
   step with the executed commands and validation results.

4. Verify the public download endpoint:

   ```bash
   npm run release:cli:smoke
   ```

These commands wrap `deploy/aws-cli-downloads/release.sh` and
`deploy/aws-cli-downloads/smoke.sh` with `--profile prod`, and run them through
the repository `.venv` via `scripts/repo_run.py`, so the release local gate —
its pip install and both pytest suites — executes in the isolated environment
(the same applies after activating the `.venv` manually). They require a clean
`main` worktree whose `HEAD` matches `origin/main`, an authenticated `gh`, and
AWS credentials for read-only stack validation. For testing-domain releases,
manual republishing, promotion, and release recovery, see
`deploy/aws-cli-downloads/README.md`.

### Release Versioning

`agent-core` and `crystal-lattice-cli` version independently. The CLI package
declares the minimum compatible core version through its `agent-core>=...`
dependency. When a CLI release needs newer core behavior, bump the `agent-core`
dependency floor and release the core package first or alongside the CLI
package.

### Runtime Packages And Optimized Bundles

The general distribution format is a bundled-Python runtime package. It ships a
normal Python runtime, repo-shaped application sources, built-in plugin sources,
and launcher scripts. This is the package shape intended for desktop/local use
because arbitrary plugins and their Python dependencies install through normal
`python -m pip` behavior.

Build the current-platform bundled-Python package:

```bash
python scripts/build_crystal_lattice_python_runtime_package.py
```

The script creates a package directory under:

```text
build/crystal-lattice-python-runtime/
```

and a release archive under:

```text
dist/crystal-lattice-python-runtime/
```

Bundled-Python archive names look like:

```text
crystal-lattice-python-runtime-v0.1.1-linux-amd64.tar.gz
crystal-lattice-python-runtime-v0.1.1-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v0.1.1-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v0.1.1-windows-amd64.zip
```

From that full package, users can create optimized config-specific PyInstaller
artifacts:

```bash
crystal-lattice bundle --config path/to/config.json --output dist/
```

Optimized artifacts are runtime-only outputs. They preinstall the plugins
selected by the supplied config and do not support creating further bundles.

Maintainer builds can still call the PyInstaller builder directly:

```bash
python scripts/build_crystal_lattice_binary.py
```

That script creates a PyInstaller app directory under:

```text
application/python/dist/crystal-lattice/
```

and a release archive under:

```text
dist/crystal-lattice/
```

Bundled-Python runtime archive names look like:

```text
crystal-lattice-python-runtime-v0.1.1-linux-amd64.tar.gz
crystal-lattice-python-runtime-v0.1.1-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v0.1.1-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v0.1.1-windows-amd64.zip
```

PyInstaller does not cross-compile. Build Linux, macOS, and Windows optimized
artifacts on matching hosts or CI runners.

The bundle preinstalls default-config plugin projects and their Python
dependencies during the binary build. It still exposes lightweight metadata and
referenced resource files under `_internal/bundled_plugins`, so default config
paths such as `path:${env:BUILTIN_PLUGINS}/codex-tools` continue to resolve
without copying selected plugin source trees into that directory. User-owned
state stays outside the bundle: config files, sessions, auth state, and plugin
install caches belong under the selected `.crystal` directory.

In the bundled-Python package, built-in plugin source trees remain under
`plugins/`. The default-config plugin closure is also installed into the
packaged Python runtime and recorded in the package-owned
`preinstalled-plugins.json` manifest. Startup uses that manifest to import
default plugins without installing them into the user plugin cache, while
leaving the copied plugin source descriptors unchanged. When user config
references a built-in plugin that is not in the default closure, the app
installs it lazily into the configured plugin cache using the packaged Python
interpreter.

In optimized PyInstaller artifacts, optional built-in plugins that are not
selected by the build config remain as source trees under
`_internal/bundled_plugins`, but PyInstaller/frozen artifacts are
config-specific packages and do not support arbitrary dynamic plugin
installation by default. Dynamic plugin installation belongs to the full
bundled-Python package, where `CRYSTAL_PLUGIN_PYTHON` or
`plugin_policy.python_executable` can select the interpreter used for
`python -m pip install --target ...`.

The bundled cloud runtime Docker context uses the same selected-plugin metadata
model, but builds Linux wheels inside Docker. The installed archive carries
selected plugin source inputs under `_internal/cloud_runtime/plugin_sources`
only so the Docker builder can create runtime-compatible wheels. The final cloud
runtime image installs those wheels at image build time and sets
`BUILTIN_PLUGINS` to
`/opt/ai-agent-platform/cloud-runtime-plugin-bundle/bundled_plugins`, which
contains only preinstalled descriptors and resources. Runtime startup should not
install bundled/default plugins into `/cloud-agent/cache/plugin_cache/plugins`;
that cache remains for non-bundled or user-provided plugins.

### Local Nox Scripts

The repository root has package.json-like maintainer commands in `noxfile.py`.
`nox` is part of the `core/python[dev]` extras, so the standard development
install provides it:

```bash
python -m pip install -e "core/python[dev]"
```

The root `package.json` wraps these sessions (`npm run build:bundle`,
`npm run build:optimized`, `npm run install:prod:local`,
`npm run install:dev:local`) and runs them through the repository `.venv` via
`scripts/repo_run.py`, so no manual activation is needed.

Build the current-platform bundled-Python runtime package:

```bash
nox -s build_bundle
```

Build the current-platform optimized PyInstaller artifact directly:

```bash
nox -s build_optimized_bundle
```

Run a local production install rehearsal from the generated archive:

```bash
nox -s install_prod_local
```

`build_bundle` and `install_prod_local` intentionally follow the release
installer shape:

1. install local build dependencies
2. run `scripts/build_crystal_lattice_python_runtime_package.py`
3. smoke-test the generated release archive
4. install from the archive, not from editable source
5. link `crystal-lattice` into `~/.local/bin`

Install an editable-source dev command:

```bash
nox -s install_dev_local
```

This creates or updates `~/.crystal/dev-cli-venv`, installs the local checkout
in editable mode, and writes `~/.local/bin/crystal-lattice-cli-dev`.

### Curl Installer / Download Domain

The public shell installer downloads through the CloudFront-backed download
domain:

```text
https://download.crystallattice.dev/crystal-lattice-cli
```

Configurable installer values:

```bash
INSTALL_ROOT="$HOME/.local/opt/crystal-lattice-cli"
BIN_DIR="$HOME/.local/bin"
COMMAND_NAME="crystal-lattice"
CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="https://example.com/crystal-lattice-cli"
```

`CRYSTAL_LATTICE_DOWNLOAD_BASE_URL` is the main switch for testing another
CloudFront distribution, bucket, or local mirror. The same URL base is expected
to contain `install.sh`, `latest.txt`, and the release archives. The shell
installer downloads `.tar.gz` archives on macOS/Linux and the `.zip` archive
when it detects Git Bash/MSYS/Cygwin on Windows.

Release tag workflows publish downloads automatically after GitHub Release
publishing succeeds. The workflow assumes the OIDC role configured by:

```bash
deploy/aws-cli-downloads/configure-github-actions-vars.sh --profile prod
```

The role trust is limited to this repository's release tags matching
`refs/tags/crystal-lattice-cli-v*`, plus the explicitly configured branch used
for workflow testing. Its policy can only write to the configured downloads
bucket/prefix and invalidate the configured CloudFront distribution.

Deployment scripts and runbook live under `deploy/aws-cli-downloads/`.

Manual republish:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh \
  --profile prod \
  --assets-dir dist/crystal-lattice-python-runtime \
  --version 0.1.1
```

To change or retire the public download endpoint, use the deployment scripts in
`deploy/aws-cli-downloads/`. They manage the private S3 bucket, CloudFront
distribution, Route 53 records, installer, `latest.txt`, and GitHub Actions
publishing configuration together.

### GitHub Release Workflow

GitHub Releases are the canonical CI build output for binary archives. Public
shell installers consume copies published to the CloudFront-backed download
domain.

The release workflow lives at:

```text
.github/workflows/release-crystal-lattice-cli.yml
```

Manual dry run:

```bash
gh workflow run release-crystal-lattice-cli.yml
```

Manual runs execute tests, build every platform archive, and smoke-test the
archives. They do not store Actions artifacts or publish a GitHub Release. On a
release tag, each read-only matrix job stores its archive as a one-day Actions
artifact. One protected publish job downloads and verifies all four archives,
uploads them to the GitHub Release, and makes the release public.

Local workflow validation:

```bash
actionlint .github/workflows/release-crystal-lattice-cli.yml

act workflow_dispatch \
  -W .github/workflows/release-crystal-lattice-cli.yml \
  -j test \
  --container-architecture linux/amd64 \
  --container-daemon-socket - \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest

act workflow_dispatch \
  -W .github/workflows/release-crystal-lattice-cli.yml \
  -j build \
  --matrix target:linux-amd64 \
  --container-architecture linux/amd64 \
  --container-daemon-socket - \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

`act` can validate the Linux-shaped workflow path locally. It cannot prove the
native macOS or Windows runners or the GitHub Release upload path.

Official releases are created by pushing a tag that matches the CLI package
version:

```bash
git tag crystal-lattice-cli-v0.1.1
git push origin crystal-lattice-cli-v0.1.1
```

The tag must match `application/python/pyproject.toml`'s `project.version`.

Maintainer checklist:

1. Update `application/python/pyproject.toml` if the CLI version is changing.
2. Update release notes or user-facing docs that should ship with the tag.
3. Run local tests or a manual GitHub Actions dry run.
4. Commit and push the release commit.
5. Create and push `crystal-lattice-cli-v<version>`.
6. Verify the GitHub Release contains all four archives.
7. Verify the download-domain installer and `latest.txt` point at the expected release.

### Docker Linux Bundle Test

Linux bundling can be tested locally through pytest and Docker. The test exports
the staged Git index into a clean snapshot, builds the Linux bundle in a Python
builder container, then validates the archive in a separate Ubuntu runtime
container.

Stage the files you want included in the clean snapshot, then run:

```bash
git add <files-to-test>
pytest application/python/tests/test_binary_distribution_docker.py -q
```

This test is marked `integration` and `docker`. Docker validates Linux bundles
only; macOS and Windows bundles still need native runners.

The deeper installed-bundle E2E test runs the extracted current-platform bundle
directly, uses Ollama with Qwen 0.6B, sends a real model request, and verifies a
tool-call flow without hosted API calls:

```bash
RUN_CRYSTAL_BUNDLE_OLLAMA_E2E=1 \
CRYSTAL_LATTICE_BUNDLE_ARCHIVE=/path/to/crystal-lattice-cli-...-<platform>-<arch>.tar.gz \
pytest application/python/tests/test_binary_distribution_bundle_e2e_ollama.py -q -m "integration and ollama"
```

Use `BUNDLE_E2E_OLLAMA_MODEL` to override the default `qwen3:0.6b` model.

The real-model installed-bundle cloud-script-author validation is separately
gated because it needs a compatible bundle archive, Docker, and hosted provider
credentials. By default it uses `CHATGPT_CREDENTIALS` when set, then the saved
login at `$HOME/.crystal/auth/chatgpt-auth.json` when present, and otherwise
falls back to the normal OpenAI provider config and API-key auth. The root
`.env` is loaded by the test suite, so `OPENAI_API_KEY` can live there:

```bash
RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E=1 \
CRYSTAL_LATTICE_BUNDLE_ARCHIVE=/path/to/crystal-lattice-cli-...-<platform>-<arch>.tar.gz \
pytest application/python/tests/test_cloud_script_author_installed_bundle_real_api.py -q -m "integration and api and docker"
```

To force a specific ChatGPT login auth file for a local run, set
`CHATGPT_CREDENTIALS` explicitly. In this mode the test sends
`auth_mode: "chatgpt"` and does not fall back to API-key auth:

```bash
RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E=1 \
CHATGPT_CREDENTIALS="$HOME/.crystal/auth/chatgpt-auth.json" \
CRYSTAL_LATTICE_BUNDLE_ARCHIVE=/path/to/crystal-lattice-cli-...-<platform>-<arch>.tar.gz \
pytest application/python/tests/test_cloud_script_author_installed_bundle_real_api.py -q -m "integration and api and docker"
```

The standard authoring validation uses the default `gpt-5.4-mini` model with
high reasoning. The harder multi-repo validation defaults to `gpt-5.4`. Use
`CLOUD_SCRIPT_AUTHOR_TEST_MODEL` to override the model for local runs. The
real-model request and final `validate-cloud` subprocess both warn after a
15-minute soft timeout and fail only at the 30-minute hard timeout; soft-timeout
warnings are a signal to inspect runtime startup or model/tool-loop behavior
rather than treating the longer run as fully healthy.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

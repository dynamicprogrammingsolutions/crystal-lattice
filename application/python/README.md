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

## Installation

### Binary Install

The bundled installer includes Python and the app runtime. It is the easiest
path for end users on macOS or Linux:

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash
```

The default install locations are:

```text
~/.local/opt/crystal-lattice-cli/<asset-stem>/
~/.local/bin/crystal-lattice
```

Pinned install:

```bash
VERSION=0.1.0 \
  curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash
```

Review-first install:

```bash
curl -fsSLO https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh
less install.sh
bash install.sh
```

Supported shell-installer assets:

```text
darwin-amd64
darwin-arm64
linux-amd64
```

Windows uses the release `.zip` asset for now; a PowerShell installer can be
added separately.

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
python -m pip install -e application/python
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
```

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
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

This advertises an `_http._tcp` service named `Agent Terminal App` by default.
Common options:

- `--enable-bonjour` - turn Bonjour advertisement on.
- `--bonjour-port` - override the advertised port; defaults to `--port`.
- `--bonjour-service-name` - set the display name shown in discovery clients.

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
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url ws://localhost:4000/ws/websocket
```

In the mobile app:

```text
Bridge Service -> ws://<bridge-host>:4000/ws/websocket -> select server -> enter pairing code
```

For a physical phone connecting to a bridge on your computer, use the
computer's LAN IP in the bridge URL, for example
`ws://192.168.1.25:4000/ws/websocket`.

Common bridge options:

- `--bridge-url` - required to enable bridge registration.
- `--bridge-display-name` - human-friendly server name shown to clients.
- `--bridge-location` - optional display metadata.
- `--bridge-local-http-base` - override the local server URL used by the bridge.
- `--bridge-server-id` - provide a stable server id.
- `--bridge-exit-on-superseded` - exit if the bridge reports this server was replaced.
- `--bridge-local-guard` - opt into a local lockfile guard for the bridge server id.
- `--bridge-takeover-local` - with the local guard, try to terminate and replace
  the existing local process.

### Bonjour + Bridge Together

You can enable both:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour \
  --bridge-url ws://localhost:4000/ws/websocket \
  --bridge-display-name "My Agent Server" \
  --bridge-location "Office"
```

LAN clients can use Bonjour/direct HTTP. Remote or cross-network clients can use
the bridge pairing flow.

## Terminal Usage

Common slash commands:

- `/help` - list commands and shortcuts.
- `/new` - start a new session.
- `/session` - inspect or switch sessions.
- `/agent` - switch between configured agents.
- `/send` - send a request with current history.
- `/append` - add a message without sending.
- `/delete`, `/modify`, `/list` - manage message history.
- `/plugins` - list, enable, disable, or reset per-session plugins.
- `/set` - update config overrides from plugin UI schema entries.
- `/cancel` - cancel an active request.
- `/exit` or `/quit` - exit the terminal.

Keyboard shortcuts:

- `Ctrl-N` - new session.
- `Ctrl-Q` - exit.
- `Ctrl-X S` - send.
- `Ctrl-X A` - append.
- `Ctrl-X C` - cancel active request.

### Plugin Controls

The terminal client exposes per-session plugin control:

```text
/plugins
/plugins on <id-or-index>
/plugins off <id-or-index>
/plugins reset
```

Changes are stored on the session in `session.metadata["plugins"]`, so
subsequent requests and reloads use the updated plugin set.

### Listing Messages

The `/list` command shows compact message history, including role, content,
reasoning/thinking metadata, tool calls, and tool call ids when present.

## Logging

Mirror logs to a file:

```bash
crystal-lattice --log-file app.log
crystal-lattice --console --log-file console.log
crystal-lattice --server --console --log-file combined.log
```

Set log level:

```bash
crystal-lattice --log-level DEBUG
crystal-lattice --console --log-level INFO
```

When running server and terminal together, `--fastapi-log-file` can route
FastAPI/uvicorn logs away from terminal stdout:

```bash
crystal-lattice --server --console --fastapi-log-file fastapi.log
```

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
      "default_sync_down_profile": "working-tree-patch",
      "default_container_profile": "default-runtime"
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
```

The command runs the runtime image selected by the active
`application.cloud_agent.container_profiles` configuration. If that image is
the default `cloud-agent-runtime:latest` and it is missing locally, the command
builds it from `cloud-orchestrator/runtime/python/Dockerfile` before starting
the local validation container.
When `--cache-dir` is provided, it is bind-mounted to `/cloud-agent/cache` so
plugin and pip caches persist across validation runs.

The full cloud profile reference lives in
[`plugins/cloud-agent-app/README.md`](../../plugins/cloud-agent-app/README.md),
including:

- the `validate-cloud` command and its built-in smoke contract
- the flattened `transfer_up_profiles` schema
- the bundled script tree under `default_config/cloud-agent/profiles/`
- the standard repo-local hook conventions and optional-hook behavior
- the complete config example and field-by-field reference

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

- `POST /sessions` - create a session.
- `GET /sessions` - list sessions.
- `GET /sessions/{session_id}/messages` - list session messages.
- `POST /sessions/{session_id}/messages` - append a message.
- `POST /sessions/{session_id}/send` - run the model/tool loop.
- `POST /sessions/{session_id}/send_message` - append and send in one call.
- `GET /events` - poll request/session events.
- `POST /requests/{request_id}/cancel` - cancel an active request.
- `GET /agents` - list configured agents.
- `PATCH /sessions/{session_id}/agent` - change a session's agent.
- `GET /sessions/{session_id}/plugins` - list session plugins.
- `PUT /sessions/{session_id}/plugins` - update enabled session plugins.
- `GET /application/ui-schema`, `POST /actions`, and `POST /sessions/{session_id}/actions` - application UI/actions.

Run the command help for the complete CLI surface:

```bash
crystal-lattice --help
```

## Release And Distribution

### Release Versioning

`agent-core` and `crystal-lattice-cli` version independently. The CLI package
declares the minimum compatible core version through its `agent-core>=...`
dependency. When a CLI release needs newer core behavior, bump the `agent-core`
dependency floor and release the core package first or alongside the CLI
package.

### Binary Builds

The binary release format is a PyInstaller `--onedir` bundle. It keeps the
executable, bundled Python runtime, app assets, and built-in plugin source
projects as separate files so release artifacts are easier to inspect and
debug.

Build the current platform:

```bash
python scripts/build_crystal_lattice_binary.py
```

The script creates a PyInstaller app directory under:

```text
application/python/dist/crystal-lattice/
```

and a release archive under:

```text
dist/crystal-lattice/
```

Archive names look like:

```text
crystal-lattice-cli-v0.1.0-linux-amd64.tar.gz
crystal-lattice-cli-v0.1.0-darwin-amd64.tar.gz
crystal-lattice-cli-v0.1.0-darwin-arm64.tar.gz
crystal-lattice-cli-v0.1.0-windows-amd64.zip
```

PyInstaller does not cross-compile. Build Linux, macOS, and Windows binaries on
matching hosts or CI runners.

The bundle includes sanitized built-in plugin project directories from the
repo-root `plugins/` directory. User-owned state stays outside the bundle:
config files, sessions, auth state, and plugin install caches belong under the
selected `.crystal` directory.

### Local Nox Scripts

The repository root has package.json-like maintainer commands in `noxfile.py`.
Install `nox` once if needed:

```bash
python -m pip install nox
```

Build the current-platform bundle:

```bash
nox -s build_bundle
```

Run a local production install rehearsal from the generated archive:

```bash
nox -s install_prod_local
```

Together these commands intentionally follow the release installer shape:

1. install local build dependencies
2. run `scripts/build_crystal_lattice_binary.py`
3. smoke-test the generated release archive
4. install from the archive, not from editable source
5. link `crystal-lattice` into `~/.local/bin`

Install an editable-source dev command:

```bash
nox -s install_dev_local
```

This creates or updates `~/.crystal/dev-cli-venv`, installs the local checkout
in editable mode, and writes `~/.local/bin/crystal-lattice-cli-dev`.

### Curl Installer / S3 Downloads

The public shell installer downloads from a public S3 bucket so binary installs
can work even while the GitHub repository is private.

Configurable installer values:

```bash
INSTALL_ROOT="$HOME/.local/opt/crystal-lattice-cli"
BIN_DIR="$HOME/.local/bin"
COMMAND_NAME="crystal-lattice"
CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="https://example.com/crystal-lattice-cli"
```

`CRYSTAL_LATTICE_DOWNLOAD_BASE_URL` is the main switch for moving from direct
S3 to CloudFront, GitHub Releases, or another bucket later. The same URL base
is expected to contain `install.sh`, `latest.txt`, and the release archives.

Release tag workflows publish S3 downloads automatically after GitHub Release
publishing succeeds. The workflow assumes this OIDC role:

```text
arn:aws:iam::874087778966:role/CrystalLatticeReleaseS3Publisher
```

The role trust is limited to this repository's release tags matching
`refs/tags/crystal-lattice-cli-v*`, and its policy can only write under:

```text
s3://crystal-lattice-downloads-874087778966/crystal-lattice-cli/*
```

Manual republish:

```bash
python scripts/publish_crystal_lattice_s3.py --assets-dir dist/crystal-lattice
```

Turn off public S3 downloads quickly:

```bash
aws s3api delete-bucket-policy --bucket crystal-lattice-downloads-874087778966
aws s3api put-public-access-block \
  --bucket crystal-lattice-downloads-874087778966 \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### GitHub Release Workflow

GitHub Releases are the canonical CI build output for binary archives. While
the repository is private, public shell installers consume copies published to
S3.

The release workflow lives at:

```text
.github/workflows/release-crystal-lattice-cli.yml
```

Manual dry run:

```bash
gh workflow run release-crystal-lattice-cli.yml
```

Manual runs execute tests, build every platform archive, smoke-test the
archives, and upload workflow artifacts. They do not publish a GitHub Release.

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
native macOS or Windows runners, and `actions/upload-artifact` may require
GitHub's hosted runtime token even after the local build and smoke test pass.

Official releases are created by pushing a tag that matches the CLI package
version:

```bash
git tag crystal-lattice-cli-v0.1.0
git push origin crystal-lattice-cli-v0.1.0
```

The tag must match `application/python/pyproject.toml`'s `project.version`.

Maintainer checklist:

1. Update `application/python/pyproject.toml` if the CLI version is changing.
2. Update release notes or user-facing docs that should ship with the tag.
3. Run local tests or a manual GitHub Actions dry run.
4. Commit and push the release commit.
5. Create and push `crystal-lattice-cli-v<version>`.
6. Verify the GitHub Release contains all four archives.
7. Verify the S3 installer and `latest.txt` point at the expected release.

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

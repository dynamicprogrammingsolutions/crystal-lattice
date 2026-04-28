# README Quickstart Revision

Revise the main README and application README so first-time users see a clear app quickstart first, while release/distribution details live in the application-specific README.

## Requirements checklist

- [x] Rewrite the main README so the first major section is a user-focused Crystal Lattice app quickstart.
- [x] Include terminal/server installation and simple startup from a working directory.
- [x] Include mobile app setup and direct-IP connection as the primary happy path.
- [x] Add a "dig deeper" section for Bonjour/mDNS and bridge connectivity, including a simple Docker bridge path.
- [x] Add a plugin development quickstart with links to `plugins/docs`.
- [x] Add a core development quickstart after the user and plugin quickstarts.
- [x] Keep release and distribution details under the application README rather than the main README.
- [x] Reorganize the application README so ordinary usage, connectivity, and release/distribution details are easy to find.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/040-curl-installer.md`

## Proposed solution from conversation

### Main README goal

Make `README.md` user-first at the top, with a clean path for someone who wants to try Crystal Lattice rather than understand the whole framework immediately.

Proposed top-level structure:

```md
# Crystal Lattice / AI Agent Platform

## Quickstart: Try The App

### 1. Install The Terminal/Server App
### 2. Start Crystal Lattice In A Working Directory
### 3. Run The Mobile App
### 4. Connect Mobile To The Server By Direct IP

## Dig Deeper: Other Connection Methods

### Automatic Discovery With Bonjour/mDNS
### Bridge Connection Across Networks
### Local Docker Bridge

## Plugin Development Quickstart

### Provider Plugins
### Tool Plugins
### Feature / Extension / Application Plugins
### Plugin Docs

## Core Development Quickstart

### Install From Source
### Run Tests
### Run Examples
### Repository Map

## Architecture Overview

## Documentation Links
```

### Main README quickstart content

At the beginning, focus on the real app experience:

1. Install the terminal/server app through the S3 curl installer:

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash
```

Mention adding `~/.local/bin` to `PATH` if needed.

2. Start the terminal/server app in a project/work directory:

```bash
mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo
crystal-lattice --host 0.0.0.0 --port 9000 --console
```

Explain briefly:

- `--console` opens the terminal UI.
- The HTTP API is available to the mobile app.
- The app creates/uses `.crystal/` config/session data in the working directory or home config depending on runtime defaults.

3. Mobile app setup:

```bash
cd mobile/crystal-lattice-control-rn
npm install
cd ios && pod install && cd ..
npm run start
npx react-native run-ios
# or
npx react-native run-android
```

Then direct IP connection:

```bash
ipconfig getifaddr en0   # macOS Wi-Fi
# or use your LAN IP from system network settings
```

In the mobile app:

```text
Manual Address -> host: <computer LAN IP> -> port: 9000 -> Connect
```

Link to:

- `mobile/crystal-lattice-control-rn/README.md`
- `application/python/README.md`

### Dig deeper section

After the direct-IP happy path, add optional paths.

Bonjour/mDNS:

```bash
crystal-lattice --host 0.0.0.0 --port 9000 --enable-bonjour
```

Then mobile:

```text
Automatic Discovery -> choose discovered service
```

Bridge:

```bash
cd bridge-elixir
docker-compose up -d
```

Then server:

```bash
crystal-lattice \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url ws://localhost:4000/ws/websocket
```

Mobile:

```text
Bridge Service -> ws://<bridge-host>:4000/ws/websocket -> pair with code
```

Link to:

- `bridge-elixir/README.md`
- `application/python/README.md`

Keep this section short in the main README and let deeper docs carry the details.

### Plugin development quickstart

Add a short practical path:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "core/python[dev]"
```

Direct users to templates:

```text
plugins/template-python-provider
plugins/template-python-tools
plugins/template-bash-tool
```

And docs:

- `plugins/docs/provider-plugins.md`
- `plugins/docs/tool-plugins.md`
- `plugins/docs/feature-plugins.md`
- `plugins/docs/application-plugins.md`
- `plugins/docs/plugin-packaging-and-loading.md`

Include one tiny provider/plugin smoke-test command or example if helpful, but avoid duplicating the full plugin guide.

### Core development quickstart

Move lower-level framework details after user/plugin quickstarts:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
```

Link to:

- `ARCHITECTURE.md`
- `DEVELOPMENT.md`
- `docs/api/core-sdk.md`
- `TYPES_AND_PROTOCOLS.md`

### Application README goal

Keep `application/python/README.md` as the authoritative app-specific doc.

Suggested structure:

```md
# crystal-lattice-cli

## What This App Provides
## End-User Installation
## Running The Terminal And HTTP Server
## Configuration And Runtime Layout
## Mobile Connectivity
### Direct IP
### Bonjour/mDNS
### Bridge
## Release And Distribution
### Binary Builds
### Local Prod/Dev Install Scripts
### Curl Installer / S3 Downloads
### GitHub Release Workflow
### Docker Bundle Test
## API Server Reference
## Terminal Commands
```

The app README should own details like:

- PyInstaller build command
- S3 bucket / OIDC role / publishing
- GitHub Actions release process
- local `nox -s install_prod_local`
- curl installer internals
- Docker packaging test
- runtime layout manifest behavior

### Small cleanup option

The mobile README title still says:

```md
# Bonjour Service Discovery - React Native
```

Consider renaming it in a separate cleanup to:

```md
# Crystal Lattice Control React Native App
```

If this task is scoped only to the main README and application README, avoid editing the mobile README and just link to it.

## Implementation approach

1. Rewrite the top third of the main README around the user quickstart.
2. Move or compress existing low-level examples so they appear after plugin/core development sections.
3. Keep release/distribution material out of the main README except a one-line user install command.
4. Reorganize the app README so release details are easier to find and clearly separated from ordinary usage.
5. Preserve existing useful details rather than deleting them, but reduce duplication between the two READMEs.
6. Run markdown sanity checks by reviewing headings/links with `rg` and `sed`; no code tests needed unless commands are changed.

## Execution plan

Added during completion.

1. Rewrite `README.md` so the first path is: install terminal/server app, start server plus terminal in a local working directory, run the React Native app, and connect by direct IP.
2. Add concise main README sections for Bonjour/mDNS and bridge connectivity, with a Docker bridge command and links to deeper docs.
3. Move plugin development before core development in the main README, linking to `plugins/docs` and the template plugin directories.
4. Keep core SDK examples and architecture in the main README, but compress them into later "developer" sections.
5. Reorganize `application/python/README.md` so installation, running modes, configuration, credentials, mobile connectivity, terminal/API usage, and release/distribution are clearly separated.
6. Keep detailed release, S3, GitHub Actions, binary build, and Docker bundle-test instructions only in the application README.
7. Verify markdown headings and changed command references with shell checks; no runtime tests are expected for documentation-only changes.

## Completion Notes

Added during completion.

- Rewrote `README.md` so it now starts with an end-user Crystal Lattice quickstart: bundled install, `--server --console --config-local`, LAN IP lookup, React Native mobile startup, and direct-IP connection.
- Added concise main README sections for Bonjour/mDNS and bridge usage, including a local Docker bridge flow and links to the application, mobile, and bridge READMEs.
- Moved plugin development before core development in the main README and linked to the current plugin docs and templates.
- Compressed main README architecture/core examples into later developer-facing sections.
- Reorganized `application/python/README.md` around installation, running modes, config/runtime layout, credentials, mobile connectivity, terminal/API usage, and release/distribution.
- Kept detailed binary build, nox, curl installer, S3, GitHub Release, and Docker bundle-test documentation in `application/python/README.md`.
- Verified changed docs with heading/link path checks and `git diff --check`.
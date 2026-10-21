# Crystal Lattice / AI Agent Platform

Crystal Lattice is a local terminal, HTTP, and mobile-friendly agent application
built on a modular Python agent framework. It gives you:

- `crystal-lattice`, a terminal and FastAPI server for local agent sessions.
- Crystal Lattice Control, a React Native app that connects to the local server.
- A plugin system for providers, tools, features, and UI-aware extensions.
- A small Elixir/Phoenix bridge service for pairing mobile clients across networks.
- `agent_core` and `agent_app`, the Python SDK layers underneath the app.

This README starts with the user path for trying the app. Developer and SDK
material follows after that.

## Project Status

Crystal Lattice is in active early development. The terminal/server, mobile
connection, SDK, and plugin-authoring workflows are available for evaluation
and development, but public APIs, configuration, plugin contracts, packaging,
and deployment procedures may change as the project incorporates early-adopter
feedback.

The bridge and cloud-orchestrator components are optional self-hosted software.
Dynamic Programming Solutions Kft. does not currently operate a public
production bridge or cloud-agent service. The project does not promise a
support SLA or a fixed compatibility window at this stage.

## Quickstart: Try Crystal Lattice

### 1. Install The Terminal/Server App

On macOS or Linux:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

On Windows x64 or ARM64, run from PowerShell:

```powershell
irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex
```

Both installers include Python and verify that `crystal-lattice` is available
by name. No provider credentials are required for startup.

The Python packages are not currently published to PyPI. For development from
a source checkout, use the editable-install instructions later in this README.

For PATH behavior, review-first installation, manual archives, updates, and
removal, see the
[installation guide](application/python/docs/installation.md).

### 2. Start The Server And Terminal

Create a working directory and start both the HTTP server and terminal UI:

```bash
mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo
crystal-lattice --server --console --config-local --host 0.0.0.0 --port 9000
```

What those flags do:

- `--server --console` runs the FastAPI server in the background and the
  terminal UI in the foreground.
- `--config-local` creates or uses `./.crystal/config.json` in this directory.
- `--host 0.0.0.0` makes the server reachable from another device on your LAN.
- `--port 9000` is the port you will enter in the mobile app.

The mobile app can connect and verify the server without a model key. To send
real model requests, configure a provider credential such as `OPENAI_API_KEY`,
`OPENROUTER_API_KEY`, or a local provider in `./.crystal/config.json`.

### 3. Find Your Computer's LAN IP

On macOS Wi-Fi:

```bash
ipconfig getifaddr en0
```

On Linux, use your network manager or:

```bash
hostname -I
```

Use the LAN address that your phone or simulator can reach, for example
`192.168.1.25`.

### 4. Run The Mobile App

From a source checkout:

```bash
cd mobile/crystal-lattice-control-rn
npm install
npm run pod-install    # iOS only
npm run start
```

In another terminal:

```bash
npm run ios
```

Or run Android:

```bash
npm run android
```

React Native setup details, physical-device notes, and troubleshooting live in
[mobile/crystal-lattice-control-rn/README.md](mobile/crystal-lattice-control-rn/README.md).

### 5. Connect By Direct IP

In the mobile app:

```text
Manual Address -> host: <your computer LAN IP> -> port: 9000 -> Connect
```

After connecting, the app can show connection status, sessions, messages,
settings, plugins, and streamed responses from the local server.

## Dig Deeper: Other Connection Methods

### Automatic Discovery With Bonjour/mDNS

On the same LAN, the server can advertise itself for discovery:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

In the mobile app:

```text
Automatic Discovery -> choose the advertised server
```

You can inspect advertisements on macOS with:

```bash
dns-sd -B _http._tcp .
```

### Bridge Connection Across Networks

The bridge lets a mobile app pair with a local server through WebSockets. For a
local Docker bridge:

```bash
cd bridge-elixir
docker-compose up -d
curl http://localhost:4000/health
```

Start Crystal Lattice and register it with the bridge:

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

For a physical device testing against a bridge on your computer, use your
computer's LAN IP in the bridge URL, not `localhost`.

More detail:

- [application/python/README.md](application/python/README.md) - CLI/server modes, config, mobile connectivity, and release process.
- [mobile/crystal-lattice-control-rn/README.md](mobile/crystal-lattice-control-rn/README.md) - React Native setup and connection screens.
- [bridge-elixir/README.md](bridge-elixir/README.md) - bridge service, Docker cluster, protocol, and deployment notes.

## External Services Deployment

### Combined Bridge And Cloud Orchestrator

For the cheapest single-user or testing setup, deploy both services to one EC2
Docker host:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-combined \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-combined \
  --region us-east-1
```

This creates one EC2 Docker host and generated CloudFront endpoints for both
the bridge and cloud orchestrator. See
[deploy/aws-ec2/README.md](deploy/aws-ec2/README.md) for build/up/down and
smoke-test flows.

### Bridge

Deploy only the external bridge:

```bash
cd bridge-elixir
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

This creates a low-cost EC2 Docker host + CloudFront bridge and prints a stable
`wss://<cloudfront-domain>/ws/websocket` URL. See
[bridge-elixir/deploy/aws-ec2/README.md](bridge-elixir/deploy/aws-ec2/README.md)
for build/up/down and AWS smoke-test flows. The existing Fargate deployment
remains available under [bridge-elixir/deploy/aws-fargate/README.md](bridge-elixir/deploy/aws-fargate/README.md).

### Cloud Orchestrator

Deploy only the cloud orchestrator:

```bash
cd cloud-orchestrator
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-cloud-orchestrator \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-cloud-orchestrator \
  --region us-east-1
```

This creates a low-cost EC2 Docker host + CloudFront orchestrator and prints a
stable `https://<cloudfront-domain>` URL plus a control token. See
[cloud-orchestrator/deploy/aws-ec2/README.md](cloud-orchestrator/deploy/aws-ec2/README.md)
for build/up/down and AWS E2E flows.

## Plugin Development Quickstart

Plugins are plain classes or tool packages loaded by the app configuration.
They can add providers, provider extensions, features, tools, UI controls,
message actions, and application-level actions.

### Start From A Template

Current templates:

- `plugins/template-python-provider`
- `plugins/template-python-tools`
- `plugins/template-bash-tool`
- `plugins/template-js-multi-tools`

Set up a development environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "core/python[dev]"
```

Add the terminal/server app when the plugin work needs app-level integration:

```bash
python -m pip install -e application/python
```

Install each repo-root plugin package separately when you are actively changing it:

```bash
python -m pip install -e "plugins/template-python-provider[dev]"
pytest plugins/template-python-provider/tests -q
```

Load local or packaged plugins through app config entries such as dotted class
paths, `path:` descriptors, or Git descriptors. See the packaging guide for the
supported forms.

### Plugin Docs

- [plugins/docs/index.md](plugins/docs/index.md)
- [plugins/docs/provider-plugins.md](plugins/docs/provider-plugins.md)
- [plugins/docs/tool-plugins.md](plugins/docs/tool-plugins.md)
- [plugins/docs/node-tool-plugins.md](plugins/docs/node-tool-plugins.md)
- [plugins/docs/bash-tool-plugins.md](plugins/docs/bash-tool-plugins.md)
- [plugins/docs/feature-plugins.md](plugins/docs/feature-plugins.md)
- [plugins/docs/provider-extensions.md](plugins/docs/provider-extensions.md)
- [plugins/docs/application-plugins.md](plugins/docs/application-plugins.md)
- [plugins/docs/plugin-packaging-and-loading.md](plugins/docs/plugin-packaging-and-loading.md)
- [plugins/docs/testing-and-validation.md](plugins/docs/testing-and-validation.md)
- [plugins/docs/ui-elements.md](plugins/docs/ui-elements.md)
- [plugins/docs/overview.md](plugins/docs/overview.md) - general plugin-system overview

## Core Development Quickstart

Use this path when you want to work on the framework itself.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

`core/python[dev]` installs the core SDK development environment from this
repo checkout. It does not install repo-root plugin packages, so install
`plugins/<plugin-name>[dev]` separately when you are changing a plugin.

The root `package.json` scripts run Python tooling through
`scripts/repo_run.py`, which resolves the repository `.venv` automatically, so
they work without activating the virtualenv:

```bash
npm run install:venv
npm run install:all
npm run test:core:unit
```

Application-owned CLI build, install, release-maintenance, and distribution
smoke entry points live under `application/python/scripts/`. Root `scripts/`
retains repository-wide utilities and the cross-runtime packaging primitives
used by shipped archives and cloud-orchestrator builds.

Install the plugin-suite packages into the same `.venv` when working on the
kimi-tools, claude-tools, web-fetch-shared, tool-compat-shared, or
openai_responses plugins:

```bash
npm run install:plugins
npm run test:plugins:kimi
```

The CLI release npm scripts run the release local gate — its pip install and
both pytest suites — inside the same `.venv`. `release:cli:gate` runs the full
local validation without creating or pushing the release tag.

On Windows, install Python 3.10+ and make sure `python` is on `PATH`; the
same npm scripts run from cmd.exe and PowerShell. The `deploy:*`, `ssh:*`,
`server:cloud-test`, and `release:cli*` scripts are macOS/Linux only.

Run the common fast test sets:

```bash
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
pytest core/python/examples/tests -qs
```

Lint and type-check commands:

```bash
ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins
black core/python/agent_core core/python/tests core/python/examples core/python/plugins
pyright
```

Contributor references:

- [Application and terminal feature development](application/python/docs/development/terminal-and-http-features.md)
- [Core Python documentation](core/python/docs/index.md)
- [Core SDK guide](core/python/docs/core-sdk.md)
- [Core types and plugin protocols](core/python/docs/types-and-protocols.md)
- [Application events](core/python/docs/events.md)
- [Tested Core examples](core/python/docs/examples.md)

## Architecture Overview

The repository is organized around a small set of layers.

### Core SDK

`core/python/agent_core` provides the provider-agnostic conversation engine:

- immutable `Session` and `Message` flows
- provider, extension, feature, and tool registration
- sync, streaming, and async streaming request APIs
- provider-native history retention
- tool schema discovery and tool-call execution helpers

### Application Layer

`core/python/agent_app` builds an application runtime on top of the core:

- JSON config loading and placeholder resolution with `${env:...}` and
  `${file:...}`
- agent/provider/plugin wiring
- filesystem session persistence
- event storage for server and terminal clients
- the model plus tool loop used by the terminal and HTTP app

### Terminal And HTTP App

`application/python/agent_terminal_app` provides the user-facing CLI/server:

- `crystal-lattice`, the installed command
- FastAPI routes for sessions, messages, events, agents, plugins, config, and
  application actions
- a `prompt_toolkit` terminal UI with slash commands
- Bonjour/mDNS advertising
- bridge registration and pairing support

### Mobile App

`mobile/crystal-lattice-control-rn` is a React Native app that connects to the
server through direct HTTP, Bonjour discovery, or the bridge. It includes
connection management, session lists, chat, message actions, plugin controls,
attachments, and streaming message views.

### Bridge Service

`bridge-elixir` is an Elixir/Phoenix WebSocket bridge. Local servers register as
server clients, mobile apps connect as app clients, and a 6-digit pairing flow
authorizes proxied HTTP requests.

## Repository Layout

- `core/python/agent_core` - core SDK.
- `core/python/agent_app` - app runtime, config, sessions, events, tool loop.
- `core/python/plugins` - core-packaged Python plugins kept mainly for tests, compatibility, and some package-local/core features.
- `core/python/examples` - runnable examples used as executable docs.
- `core/python/tests` - core, app-layer, and plugin tests.
- `application/python/agent_terminal_app` - CLI, terminal, FastAPI server, mobile glue.
- `application/python/tests` - terminal/server tests.
- `mobile/crystal-lattice-control-rn` - React Native app.
- `bridge-elixir` - bridge service and Docker/HAProxy setup.
- `plugins` - built-in plugin projects for the current runtime layout, plus templates and shared plugin docs.
- `docs` - MkDocs/API reference docs.
- `test` - repository-level shared test support and cross-cutting test areas.
- `archive` - historical conversations, plans, notes, and diagnostics; not current guidance.

## Core SDK Examples

### Basic Synchronous Chat

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
}

session = core.create_session()
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

session, finals = core.send_request(session, config)
print(finals[-1]["content"])
```

### Streaming

```python
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        session = chunk["session"]
        print("\n[Done]")
```

### Echo Provider With No API Key

```python
from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

core = AgentCore()
core.register_provider(EchoOpenAILikeProvider)

session = core.create_session()
session = core.add_message(session, "user", "Hello from the echo provider!")

session, replies = core.send_request(
    session,
    {"provider": "echo_openai_like", "model": "echo-test-1", "timeout": 60},
)
print(replies[-1]["content"])
```

## Examples And Recipes

Examples live under `core/python/examples` and are catalogued in
[the generated examples guide](core/python/docs/examples.md). Highlights include echo providers, provider
extensions, feature plugins, file tools, streaming, app-layer flows, and
OpenRouter/Ollama examples.

Run the examples as tests:

```bash
pytest core/python/examples/tests -qs
```

## Documentation

Browse the MkDocs site locally:

```bash
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs serve -a 127.0.0.1:8001)
```

Key docs:

- [Development documentation](docs/development/index.md)
- [Documentation and specification guide](docs/development/documentation.md)
- [Crystal Lattice documentation conventions](docs/development/crystal-lattice-documentation.md)
- [Core Python documentation](core/python/docs/index.md)
- [Core SDK guide](core/python/docs/core-sdk.md)
- [Application events](core/python/docs/events.md)
- [plugins/docs/index.md](plugins/docs/index.md)
- [plugins/docs/overview.md](plugins/docs/overview.md) - general plugin-system overview
- [Generated AgentCore reference](https://docs.crystallattice.dev/packages/core-python/reference/core/)
- [application/python/README.md](application/python/README.md)
- [mobile/crystal-lattice-control-rn/README.md](mobile/crystal-lattice-control-rn/README.md)
- [bridge-elixir/README.md](bridge-elixir/README.md)

Build the prepared site without starting a server:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

See [docs_site/README.md](docs_site/README.md) for reference-source ownership,
the full build, and the deployment workflow.

When changing examples:

```bash
pytest core/python/examples/tests -qs
python scripts/generate_examples_md.py
```

## Community And Support

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing or submitting a
  change.
- Use [SUPPORT.md](SUPPORT.md) to route usage questions, reproducible bugs, and
  feature requests.
- Use the
  [GitHub issue chooser](https://github.com/dynamicprogrammingsolutions/crystal-lattice/issues/new/choose)
  for non-sensitive bugs and feature proposals.
- Read [SECURITY.md](SECURITY.md) and report suspected vulnerabilities
  privately. Do not disclose security-sensitive details in a public issue.
- Product and mobile-app support information is also available at
  [crystallattice.dev/support](https://crystallattice.dev/support).

## Status And Version

- Core package: `agent-core` 0.3.0
- Terminal CLI package: `crystal-lattice-cli` 0.2.2 (`crystal-lattice` command)

See `core/python/pyproject.toml`, `application/python/pyproject.toml`, and the
source files for the most up-to-date behavior.

## License

Unless otherwise noted, original source code and other original materials in
this repository are licensed under the Apache License, Version 2.0.

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this material except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Some subdirectories may include their own `LICENSE` files, file-level license
headers, `NOTICE` files, or other rights notices. Those more specific notices
apply within their respective files or subtrees.

Independently authored compatibility implementations and generated normalized
behavior fixtures may be Apache-2.0 licensed where the applicable project or
subtree says so. Actual third-party source or adapted material remains subject
to its applicable upstream notices and terms.

See [LICENSE](LICENSE) and [LICENSING.md](LICENSING.md) for the repository-wide
licensing rule.
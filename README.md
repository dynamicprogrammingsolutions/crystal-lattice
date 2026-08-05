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

## Quickstart: Try Crystal Lattice

### 1. Install The Terminal/Server App

On macOS, Linux, or Git Bash on Windows, install the bundled CLI:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

The installer links the command as `~/.local/bin/crystal-lattice`. If that
directory is not on your `PATH`, add it or call the command by its full path.

Users who prefer Python packaging can use:

```bash
pipx install crystal-lattice-cli
```

More installation details are in [application/python/README.md](application/python/README.md).

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
- [docs/plugins/development.md](docs/plugins/development.md) - older/general plugin overview

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

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [docs/api/core-sdk.md](docs/api/core-sdk.md)
- [TYPES_AND_PROTOCOLS.md](TYPES_AND_PROTOCOLS.md)
- [EXAMPLES.md](EXAMPLES.md)

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
[EXAMPLES.md](EXAMPLES.md). Highlights include echo providers, provider
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
- [Reusable development standards](docs/development/standards/index.md)
- [Crystal Lattice repository policy](docs/development/repository/index.md)
- [docs/api/core-sdk.md](docs/api/core-sdk.md)
- [plugins/docs/index.md](plugins/docs/index.md)
- [docs/plugins/development.md](docs/plugins/development.md) - older/general plugin overview
- [docs/reference/agent_core](docs/reference/agent_core)
- [application/python/README.md](application/python/README.md)
- [mobile/crystal-lattice-control-rn/README.md](mobile/crystal-lattice-control-rn/README.md)
- [bridge-elixir/README.md](bridge-elixir/README.md)

Build the prepared site without starting a server:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

See [docs_site/README.md](docs_site/README.md) for the full build, generated
reference snapshot, and deployment workflow.

When changing examples:

```bash
pytest core/python/examples/tests -qs
python scripts/generate_examples_md.py
```

## Status And Version

- Core package: `agent-core` 0.3.0
- Terminal CLI package: `crystal-lattice-cli` 0.1.0 (`crystal-lattice` command)

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

Some compatibility-oriented materials in this repository are derived from or
adapted from third-party systems and are not necessarily licensed by us under
Apache-2.0. Rights for those materials should be determined from the
applicable file-level notices, subtree-specific notices, and upstream terms.

See [LICENSE](LICENSE) and [LICENSING.md](LICENSING.md) for the repository-wide
licensing rule.
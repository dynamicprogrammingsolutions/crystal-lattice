# Crystal Lattice Core Python

The `agent-core` Python distribution provides the provider-agnostic
conversation SDK and application orchestration layer used by Crystal Lattice.
It supports immutable conversation values, provider and plugin composition,
synchronous and streaming requests, tool interoperability, application-managed
sessions, and event storage.

## Package contents

- `agent_core`: conversations, providers, extensions, features, tools,
  streaming, provider-native history, and session operations.
- `agent_app`: configuration, application plugin orchestration, session and
  event stores, and the model/tool loop.
- `plugins`: older package-local plugins retained for compatibility, tests,
  and a small set of Core features.

The installable terminal and HTTP application lives separately under
`application/python`. Current first-party provider and plugin packages live
under the repository-root `plugins/` directory.

## Install

From a source checkout:

```bash
python -m pip install -e "core/python"
```

For development:

```bash
python -m pip install -e "core/python[dev]"
```

Python 3.10 or newer is required.

## First request

The package includes a deterministic echo provider for an offline first
request:

```python
from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

core = AgentCore()
core.register_provider(EchoOpenAILikeProvider)

session = core.create_session("readme")
session = core.add_message(session, "user", "Hello!")
session, replies = core.send_request(
    session,
    {"provider": "echo_openai_like", "model": "echo-test-1"},
)

print(replies[-1]["content"])
```

This prints:

```text
SYS= | USER=Hello!
```

For installation explanation, expected state, and next steps, use the
[Core Python quickstart](docs/quickstart.md).

## Documentation

- [Core Python documentation](docs/index.md)
- [Core SDK guide](docs/core-sdk.md)
- [Core types and plugin protocols](docs/types-and-protocols.md)
- [Application events](docs/events.md)
- [Tested examples](docs/examples.md)
- [Core development documentation](docs/development/index.md)
- [Shared plugin development documentation](../../plugins/docs/index.md)

Generated API reference is published through the repository documentation
site from maintained Python docstrings.

## Development

From the repository root:

```bash
pytest core/python/tests -q -m "not integration"
pytest core/python/examples/tests -q -m "not integration"
ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins
```

Integration, hosted API, slow, and local-service test markers must be enabled
deliberately. See [Core package guidance](AGENTS.md) for ownership and
verification boundaries.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0. See
<https://www.apache.org/licenses/LICENSE-2.0>.

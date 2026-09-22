# Core Python quickstart

This quickstart installs the Core Python distribution and completes one
request without provider credentials, a network connection, or a local model.

## Install from a source checkout

From the repository root:

```bash
python -m pip install -e "core/python"
```

Install development and test dependencies with:

```bash
python -m pip install -e "core/python[dev]"
```

## Send a deterministic request

The package includes an OpenAI-shaped echo provider used for offline examples
and verification.

<!-- quickstart-example-start -->
```python
from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

core = AgentCore()
core.register_provider(EchoOpenAILikeProvider)

session = core.create_session("quickstart")
session = core.add_message(
    session,
    "user",
    "Hello from the echo provider!",
)

session, replies = core.send_request(
    session,
    {
        "provider": "echo_openai_like",
        "model": "echo-test-1",
    },
)

print(replies[-1]["content"])
```
<!-- quickstart-example-end -->

The result is:

```text
SYS= | USER=Hello from the echo provider!
```

`send_request` returns a new `Session` and the final core-message dictionaries
produced for the request. The input session is not mutated; the returned
session contains both the user message and the assistant reply.

## Continue

- Read the [Core SDK guide](core-sdk.md) for session and request operations.
- Read [Core types and plugin protocols](types-and-protocols.md) for the data,
  state, and request-flow model.
- Browse the [tested examples](examples.md) for providers, extensions,
  features, tools, streaming, and application-layer flows.
- Use the [shared plugin development documentation](../../../plugins/docs/index.md)
  when implementing a plugin package.
# Core Python documentation

The `agent-core` distribution contains the provider-agnostic `agent_core` SDK,
the `agent_app` application orchestration layer, and a small collection of
package-local compatibility plugins.

The SDK manages immutable conversation values, provider and plugin
orchestration, synchronous and streaming requests, provider-native history,
tool interoperability, and session operations. Applications remain
responsible for choosing configuration and persisting sessions.

## Start here

- [Quickstart](quickstart.md): install from a source checkout and complete a
  deterministic request without credentials or network access.
- [Core SDK guide](core-sdk.md): use selected session, request, streaming,
  tool, action, import, and export APIs.
- [Core types and plugin protocols](types-and-protocols.md): understand the
  important values, plugin families, state ownership, request flow, and
  native-history model.
- [Application events](events.md): event storage, request/tool events,
  notification events, terminal additions, and transport boundaries.
- [Tested examples](examples.md): generated catalog of runnable providers,
  extensions, features, tools, application flows, and integrations.
- [Package README](../README.md): package boundaries, installation, tests, and
  project metadata.

## Related documentation

- [Generated AgentCore reference](reference/core.md)
- [Generated types and protocols reference](reference/types.md)
- [Generated provider-wrapper reference](reference/plugin/provider.md)
- [Cross-package tool-host protocol](../../../docs/reference/tool-host-protocol.md)
- [Shared plugin development documentation](../../../plugins/docs/index.md)
- [Application and terminal documentation](../../../application/python/docs/index.md)

## Development

- [Core Python development](development/index.md): implementation,
  configuration-composition, notification, logging, and maintainer guidance.
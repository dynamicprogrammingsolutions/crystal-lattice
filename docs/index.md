# Crystal Lattice Docs

Crystal Lattice is a plugin-driven AI agent platform for running local-first,
provider-agnostic agent workflows across your computer, phone, and custom
automation.

The platform includes a Python SDK, a terminal and HTTP runtime, mobile and
desktop clients, provider integrations, and a first-party plugin system for
tools, features, provider behavior, application actions, and model-family
harnesses.

## Start Here

- [Application configuration](plugins/application-config.md): configure agents,
  providers, plugins, tools, placeholders, and runtime policy.
- [Current plugin docs](plugin-development/index.md): build provider, feature,
  application, and tool plugins using the current plugin documentation set.
- [Built-in plugins](built-in-plugins/index.md): browse generated reference
  pages for bundled plugin packages.
- [Default configuration](reference/default-config.md): inspect the generated
  default application configuration.
- [Event stream types](api/events.md): understand application events exposed by
  HTTP polling and bridge streaming.

## Developer Reference

- [AgentCore API](reference/agent_core/core.md): core session, message, request,
  streaming, and tool orchestration APIs.
- [Core SDK guide](api/core-sdk.md): hand-written overview of the functional SDK
  surface.
- [Types and protocols](reference/agent_core/types.md): immutable core types and
  plugin protocols.
- [Provider wrapper](reference/agent_core/plugin/provider.md): provider adapter
  API reference.
- [OpenAI-compatible provider](reference/providers/openai_provider.md): reference
  provider implementation details.
- [Tool host protocol](reference/tool-host-protocol.md): protocol reference for
  external tool hosts.

## Project Links

- [Crystal Lattice website](https://crystallattice.dev.dynamicprogrammingsolutions.com/)
- [GitHub repository](https://github.com/dynamicprogrammingsolutions/crystal-lattice)

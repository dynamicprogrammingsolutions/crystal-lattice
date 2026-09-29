# Crystal Lattice Docs

Crystal Lattice is a plugin-driven AI agent platform for running local-first,
provider-agnostic agent workflows across your computer, phone, and custom
automation.

The platform includes a Python SDK, a terminal and HTTP runtime, mobile and
desktop clients, provider integrations, and a first-party plugin system for
tools, features, provider behavior, application actions, and model-family
harnesses.

## Start Here

- [Package documentation](packages/index.md): choose the SDK, application,
  component, or service that owns the part of Crystal Lattice you want to use.
- [Application configuration](packages/application-python/configuration.md): configure agents,
  providers, plugins, tools, placeholders, and runtime policy.
- [Current plugin docs](plugin-development/index.md): build provider, feature,
  application, and tool plugins using the current plugin documentation set.
- [Built-in plugins](built-in-plugins/index.md): browse generated reference
  pages for bundled plugin packages.
- [Default configuration](reference/default-config.md): inspect the generated
  default application configuration.
- [Event stream types](packages/core-python/events.md): understand application
  events exposed by HTTP polling and bridge streaming.
- [Development documentation](development/index.md): reusable standards,
  Crystal Lattice repository policy, and cross-package target specifications.

## Developer Reference

- [Documentation and specification guide](development/documentation.md):
  structure, file roles, writing, requirements, testing, and verification.
- [Crystal Lattice documentation conventions](development/crystal-lattice-documentation.md):
  package paths, plugin guidance, tasks, publication, and migration.
- [AgentCore API](reference/agent_core/core.md): core session, message, request,
  streaming, and tool orchestration APIs.
- [Core SDK guide](packages/core-python/core-sdk.md): hand-written guide to
  selected SDK surface.
- [Core types and plugin protocols](packages/core-python/types-and-protocols.md):
  conceptual map of important values, plugin responsibilities, state, and
  request flow.
- [Types and protocols](reference/agent_core/types.md): immutable core types and
  exact Python plugin protocol reference generated from docstrings.
- [Provider wrapper](reference/agent_core/plugin/provider.md): provider adapter
  API reference.
- [OpenAI-compatible provider](reference/providers/openai_provider.md): reference
  provider implementation details.
- [Tool host protocol](reference/tool-host-protocol.md): protocol reference for
  external tool hosts.

## Project Links

- Use the **Website Home** menu item to return to the Crystal Lattice website.
- [GitHub repository](https://github.com/dynamicprogrammingsolutions/crystal-lattice)

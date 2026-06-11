---
eyebrow: Features
title: Full control, zero compromises
body: >-
  Persistent sessions, configurable agents, tool calling, streaming, mobile
  access, and a developer SDK. Defaults you can replace when your workflow needs
  something different.
---

## Runs from your computer

<!-- icon: lock -->

Your sessions and history are stored in the working directory you choose. Model
requests go to the provider or local model you configure, and bridge traffic only
exists when you choose to connect across networks.

## Provider and model-family plugins

<!-- icon: provider -->

Providers, model-family harnesses, tools, prompts, and request behavior are
plugin-driven. Different providers and models expose different capabilities, so
Crystal Lattice lets the harness change with the agent you are running.

## Streaming-first

<!-- icon: stream -->

Responses stream token-by-token from the model to your terminal or phone.
Partial messages display as they arrive. Final messages can include metadata
such as tool call results, reasoning traces, and token counts when the configured
provider and plugins supply them.

## Persistent sessions

<!-- icon: file -->

Sessions are stored on the filesystem. Restart Crystal Lattice and your
conversations are still there. Multiple simultaneous sessions can each keep their
own agent config, message history, and state. List and resume sessions from the
app UI.

## Automatic tool calling

<!-- icon: tool -->

When tools are configured, agents can use them in a multi-step loop. The model
requests a tool call, Crystal Lattice executes it, the result feeds back into the
conversation, and the model continues.

## Deep plugin system

<!-- icon: plugin -->

Extend every layer: add providers, tools, features, UI controls, and application
actions with Python or JavaScript plugins. Write a plugin, point your config at
it, and use it without waiting for the core project to accept a new capability.

---
eyebrow: Features
title: Full control, zero compromises
body: >-
  Persistent sessions, multi-agent configs, tool calling, streaming, mobile
  access, and a developer SDK. Full control, no vendor lock-in.
---

## Local-first & private

<!-- icon: lock -->

Your conversations, sessions, and history live on your own machine. No data is
sent anywhere except to whichever AI provider you choose. Run completely offline
with local models via Ollama: no API key, no internet, no data leaving your
device.

## Provider agnostic

<!-- icon: provider -->

Crystal Lattice doesn't lock you into any one AI provider or model. The
terminal, mobile app, and SDK all work identically regardless of which provider
is configured. Switching providers is a one-line config change.

## Streaming-first

<!-- icon: stream -->

Responses stream token-by-token from the model, through the server, to your
terminal or phone. Partial messages display as they arrive. Final messages
replace them with full metadata: tool call results, reasoning traces, and token
counts.

## Persistent sessions

<!-- icon: file -->

Sessions are stored on the filesystem. Restart the server and your conversations
are still there. Multiple simultaneous sessions, each with their own agent
config, message history, and state. List and resume any session from the mobile
app.

## Automatic tool calling

<!-- icon: tool -->

Agents call tools (file reads, web search, code execution, or custom tools you
define) in an automatic multi-step loop. The model requests a tool call, the app
executes it, the result feeds back into the conversation, and the model
continues.

## Deep plugin system

<!-- icon: plugin -->

Extend every layer: add providers, tools, features, UI controls, and application
actions with Python or JavaScript plugins. You never need to modify the core to
add a capability. Write a plugin, point your config at it, and it loads.

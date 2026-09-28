# Embedded Python runtime proof of concept

This mobile-owned specification defines the first working iOS embedding of the
Crystal Lattice Python runtime. It covers one fixed OpenAI-compatible agent,
an API-key-protected Ollama proxy, general workspace-restricted `Read` and
`Write` tools, and bounded foreground/background execution through the real
mobile application.

Active work:

- [Embedded runtime, proxy, and file tools](../../../../../../tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md)

Related broader target:

- [App Review local runtime](../../../../../../tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md)

## Ownership

The mobile package owns:

- the iOS CPython bundle and native runtime host;
- the React Native bridge and local `AgentBackend`;
- app-owned runtime/config/session/workspace paths;
- iOS foreground/background integration and native verification;
- the first-run proof-of-concept settings surface.

The Core and application packages retain ownership of `AgentCore`,
`AgentApplication`, session/message/tool semantics, plugin protocols, and
complete application reload. The existing proxy package retains ownership of
OpenAI-compatible forwarding behavior extended for this proof of concept.

## Target

A release-like simulator or device build can:

1. Start the bundled Python runtime without a desktop process.
2. Expose one fixed agent through the production Sessions and Messages UI.
3. Call an API-key-protected OpenAI-compatible proxy backed by Ollama.
4. Execute a real multi-round `Read`/`Write` tool sequence under one app-owned
   workspace.
5. Persist the session and workspace across runtime reconstruction.
6. Continue for bounded background time or return to a visible recoverable
   interruption state.

Exact model prose and broad model capability are not part of acceptance.

## Explicit exclusions

This specification does not define:

- Tavily web search;
- restricted Python execution;
- ChatGPT authorization;
- an on-device model;
- email or personal-data tools;
- arbitrary user-selected workspace roots;
- production reviewer-service deployment;
- complete production credential security or polished onboarding;
- general dynamic plugin installation on iOS.

Those exclusions may be addressed by later tasks without changing this
proof-of-concept target.

## Specification documents

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)
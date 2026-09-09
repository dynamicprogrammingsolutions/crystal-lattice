# Embedded Python runtime proof-of-concept requirements

These requirements track the live implementation of the
[embedded Python runtime proof of concept](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
| --- | --- | --- | --- | --- | --- |
| IPR-001 | A release-like iOS application bundle contains and starts the fixed CPython/Crystal Lattice closure without a desktop process, loopback application server, runtime download, or dynamic plugin installation. | Not started | Unverified | Pending | Active task `tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md` |
| IPR-002 | The mobile application exposes the embedded runtime through a production `inProcess` `AgentBackend` that supports the fixed agent, sessions, messages, request events, cancellation, and the proof-of-concept configuration action. | Not started | Unverified | Pending | Active task |
| IPR-003 | One fixed agent uses the reference OpenAI-compatible provider through an API-key-protected proxy backed by Ollama and completes a real multi-round request. | Not started | Unverified | Pending | Active task |
| IPR-004 | The proxy rejects missing or incorrect bearer credentials, accepts the configured key, preserves required OpenAI-compatible streaming/non-streaming behavior, and does not log the credential. | Not started | Unverified | Pending | Active task |
| IPR-005 | The app accepts a masked proof-of-concept API key, supplies it through an app-owned configuration overlay, and reconstructs the complete `AgentApplication` without exposing the key in prompts, events, tools, logs, or committed configuration. | Not started | Unverified | Pending | Active task |
| IPR-006 | General text `Read` and `Write` tools operate only on logical paths under one canonical app-owned workspace and reject absolute paths, traversal, and symlink escape. | Not started | Unverified | Pending | Active task |
| IPR-007 | Session and workspace state survive navigation, runtime reconstruction, and process relaunch for the proof-of-concept flow. | Not started | Unverified | Pending | Active task |
| IPR-008 | An active request receives bounded iOS background handling, durable lifecycle timestamps/state, and visible completion or recoverable interruption without automatic duplicate provider execution. | Not started | Unverified | Pending | Active task |
| IPR-009 | Focused automated simulator coverage exercises production screens and adapters, while physical-device evidence records runtime startup and actual background behavior. | Not started | Unverified | Pending | Active task |
| IPR-010 | The proof of concept remains limited to one agent/provider, workspace `Read`/`Write`, basic credentials, and lifecycle evidence; Tavily search, restricted Python, ChatGPT authorization, local models, and broader production hardening are not falsely presented as delivered. | Not started | Unverified | Pending | Active task and specification exclusions |
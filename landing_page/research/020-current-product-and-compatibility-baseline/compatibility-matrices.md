# Product Compatibility Matrices

Status: Accepted

These matrices describe Crystal Lattice product behavior. Compatibility
profiles are Crystal Lattice configurations, not official upstream
applications, accounts, or sessions.

## Status legend

| Status | Meaning |
|---|---|
| `supported` | Implemented for this row without an additional feature gate beyond ordinary configuration. |
| `conditional` | Implemented, but availability depends on model capability, provider response, account mode, explicit enablement, or another prerequisite. |
| `planned` | Not implemented in the current row, but explicitly owned by a maintained future requirement or task. |
| `unsupported` | Not implemented for this row and not represented as current support. |
| `not_applicable` | The feature does not meaningfully apply to this row. |
| `unknown` | Evidence is insufficient to classify the cell. |

## Feature catalog

| Plugin | Kinds | Lifecycle | Capability | Default | Description |
|---|---|---|---|---:|---|
| `anthropic-compatible` | extensions, providers | `default_selected` | `partial` | yes | Direct Anthropic API and Anthropic-compatible Messages provider for the AI Agent Platform. |
| `application-config-app` | application | `default_selected` | `current` | yes | Provides application-level actions to request a complete application reload and to update explicitly allowlisted provider keys in a configured dotenv file. |
| `bash-read-line-range` | tools | `example` | `internal` | no | A minimal bash tool plugin that reads a line range from a file using `sed`, with optional line numbers via `nl`. |
| `bash-send-kindle-icloud` | tools | `optional` | `optional` | no | Bash tool plugin that exposes three small tools: `build_epub_from_markdown`; `send_to_kindle`; `send_markdown_to_kindle`. |
| `chatgpt-auth-app` | application | `default_selected` | `partial` | yes | Minimal application plugin implementing a device-code login flow for ChatGPT-style auth. |
| `claude-tools` | features, tools | `default_selected` | `current` | yes | Claude Code-compatible tool plugin bundle for Crystal Lattice. |
| `cloud-agent-app` | application | `default_selected` | `partial` | yes | Cloud agent application plugin and managed SSH transfer adapter. |
| `codex-tools` | features, tools | `default_selected` | `current` | yes | Codex CLI-compatible tool plugin bundle. Provides shell tools and apply-patch with schemas, parameter names, output formatting, and behavioral semantics matching OpenAI's Codex CLI. |
| `cost-tracking` | application, extensions | `default_selected` | `current` | yes | Generic, provider-agnostic cost tracking plugin for the Crystal Lattice platform. |
| `dummy-action-display-app` | application | `development_fixture` | `internal` | no | Non-production demonstration plugin for direct banner, inline, and modal action responses. It is intentionally absent from the default runtime configuration. |
| `dummy-action-display-form-app` | application | `development_fixture` | `internal` | no | Demo application plugin for manually testing generic action display embedded forms. |
| `dummy-application-notification-app` | application | `development_fixture` | `internal` | no | Non-production demonstration plugin for creating, updating, and resolving owner-memory application notifications. It is intentionally absent from the default runtime configuration. |
| `dummy-mcp-auth-server` | support/other | `development_fixture` | `internal` | no | Local streamable HTTP MCP server for manually testing MCP OAuth login from Crystal Lattice. |
| `dummy-mcp-output-server` | support/other | `development_fixture` | `internal` | no | Local MCP server for investigating and testing large MCP tool outputs. |
| `dummy-rich-config-ui` | feature | `development_fixture` | `internal` | no | Opt-in feature plugin for manually and automatically testing portable rich configuration controls on mobile and desktop. |
| `dummy-session-notification-app` | application | `development_fixture` | `internal` | no | Non-production demonstration plugin for persistent session notifications and follow-up actions. It is enabled only by examples and integration tests. |
| `dummy-settings-app` | application | `development_fixture` | `internal` | no | Demo application plugin for manually testing server-scoped settings. |
| `duration-tracking` | application, features | `optional` | `optional` | no | Generic, provider-agnostic duration tracking plugin for the Crystal Lattice platform. |
| `embedded-claude-tools` | tools | `distribution_specific` | `optional` | no | Claude-like, iOS-safe workspace tools for the embedded Crystal Lattice runtime. |
| `embedded-codex-tools` | tools | `distribution_specific` | `optional` | no | Codex-like, iOS-safe command tools for the embedded Crystal Lattice runtime. |
| `embedded-tools-shared` | support/other | `support_library` | `internal` | no | Pure-Python engines shared by the embedded Claude-like and Codex-like tool plugins. |
| `feature-file-context` | features | `default_selected` | `current` | yes | Feature plugin providing `@file:` marker expansion and file completions. |
| `feature-request-options` | features | `default_selected` | `partial` | yes | Feature plugin that merges `request_options` from config into the provider payload, with support for declarative UI configuration using flat override keys. |
| `feature-system-message` | features | `default_selected` | `current` | yes | Feature plugin providing configurable system-message templating for request-time prompt composition. |
| `feature-web-context` | features | `default_selected` | `partial` | yes | Feature plugin providing `@web:` marker expansion and URL completions. |
| `gemini-compaction-app` | application | `optional` | `optional` | no | Gemini-style context compaction application plugin for the AI Agent Platform. |
| `gemini-compaction-feature` | feature | `optional` | `optional` | no | A Feature-level plugin that provides Gemini-style context compaction using the layered context approach. |
| `gemini-tools` | tools | `default_selected` | `current` | yes | Compatibility-oriented Gemini-style filesystem tools for the AI Agent Platform. |
| `generate-title-app` | application | `default_selected` | `partial` | yes | Application-level plugin for generating session titles (and descriptions). |
| `generic-callback-app` | application | `development_fixture` | `internal` | no | Demo application plugin for testing generic external callback deep links. |
| `grok-tools` | tools | `default_selected` | `current` | yes | Compatibility-oriented Grok-style filesystem tools for the AI Agent Platform. |
| `js-class-tool` | tools | `example` | `internal` | no | Example tool plugin implemented as a **TypeScript class** (instead of exporting a plain object). |
| `js-echo-tool` | tools | `example` | `internal` | no | Example JavaScript/TypeScript tool plugin for the AI Agent Platform. |
| `js-fs-tools` | tools | `example` | `internal` | no | Example filesystem tools implemented in Node.js/TypeScript. |
| `js-multi-tools` | tools | `example` | `internal` | no | Example multi-tool Node.js/TypeScript package. |
| `js-single-file-tool` | support/other | `example` | `internal` | no | Single-file TypeScript tool example. |
| `kimi-tools` | features, tools | `default_selected` | `current` | yes | Kimi CLI-compatible plugin bundle. It provides manual conversation compaction and file, search, web, media, and shell tools with model-facing behavior based on MoonshotAI's `kimi-cli`. |
| `mcp-runtime-app` | application | `default_selected` | `optional` | yes | Application-level observability plugin for MCP runtimes. |
| `mcp-shared` | support/other | `support_library` | `internal` | no | Internal helper package for MCP-backed tool wrappers. |
| `message-export-actions` | application | `optional` | `optional` | no | Optional application actions for exporting messages or sessions as Markdown, PDF, EPUB/Kindle-compatible files, and generated session assets. |
| `openai_responses` | application, extensions, features, providers | `default_selected` | `partial` | yes | OpenAI Responses API bundle for the AI Agent Platform. |
| `openrouter` | extensions, providers | `default_selected` | `partial` | yes | OpenRouter Chat Completions and image-generation providers with capability-gated tools, reasoning, verbosity, web search, caching, attachments, usage, and image output extensions. |
| `openrouter_responses` | extensions, providers | `optional` | `optional` | no | Plugin bundle containing an OpenRouter provider that targets the `/responses` endpoint, plus `/responses`-compatible extensions. |
| `qwen-tools` | tools | `default_selected` | `current` | yes | Compatibility-oriented Qwen-style filesystem tools for the AI Agent Platform. |
| `rebuild-native-app` | application | `default_selected` | `current` | yes | Application-level plugin to rebuild provider-native history from core messages. |
| `reference-openai-compatible-provider` | extensions, providers | `default_selected` | `partial` | yes | Generic OpenAI-compatible Chat Completions provider package for the AI Agent Platform. |
| `session-actions-app` | application | `default_selected` | `current` | yes | Application-level plugin providing copy/fork/delete session actions. |
| `session-archive-app` | application | `default_selected` | `current` | yes | Application-level plugin that archives and restores sessions. |
| `session-asset-attachments` | application | `default_selected` | `partial` | yes | Generic application-level actions for downloading session-owned attachment assets. |
| `session-main-search-app` | application | `default_selected` | `current` | yes | Application plugin that contributes the ordinary declarative main search and focused text filters for session lists. |
| `session-message-count-meta-app` | application | `default_selected` | `current` | yes | Application-level plugin that computes message-count fields for sessions. |
| `session-ordering-buckets-app` | application | `default_selected` | `current` | yes | Application-level plugin defining bucketed ordering for session lists. |
| `session-pinned-app` | application | `default_selected` | `current` | yes | Application-level plugin that toggles and filters pinned state on sessions. |
| `session-status-app` | application | `default_selected` | `current` | yes | Application-level plugin for assigning and filtering session workflow status. |
| `session-timestamp-meta-app` | application | `default_selected` | `current` | yes | Application-level plugin that computes timestamp-derived fields for sessions and contributes the `modified_after` timezone-aware session-list filter. |
| `session-title-app` | application | `default_selected` | `current` | yes | Application-level plugin providing actions and UI schema for editing session titles. |
| `skill-shared` | support/other | `support_library` | `internal` | no | Shared discovery and parsing helpers for vendor-owned skill integrations. |
| `sleep-prevention-app` | application | `optional` | `optional` | no | Application plugin that exposes a live server setting for keeping the local server process awake. |
| `summarize-range-app` | application | `default_selected` | `partial` | yes | Application-level plugin providing summarize-range session actions. |
| `template-bash-tool` | tools | `template` | `internal` | no | Template plugin repo for **bash tool plugins**. |
| `template-js-multi-tools` | tools | `template` | `internal` | no | Template plugin repo for **Node.js / TypeScript tool plugins**. |
| `template-python-provider` | extensions, features, providers | `template` | `internal` | no | Template plugin repo for **Python provider plugins** (provider + provider extension + feature). |
| `template-python-tools` | tools | `template` | `internal` | no | Template plugin repo for **Python tool plugins**. |
| `timestamp-extension` | features | `default_selected` | `current` | yes | Timing-related feature plugins. |
| `tool-compat-shared` | support/other | `support_library` | `internal` | no | Internal helper package for the vendor-style tool bundles. |
| `web-fetch-shared` | support/other | `support_library` | `internal` | no | Shared HTTP fetch and HTML extraction helpers for vendor web fetch tools. |

## Provider support

### OpenAI Responses — API key

- Implementation: `openai_responses`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `not_applicable` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `supported` |  |
| Native reasoning controls and metadata | `supported` |  |
| Native verbosity control | `conditional` | Shown for supported model families, currently GPT-5-class models. |
| Usage and token metadata | `supported` |  |
| Cost reporting or estimation | `supported` | Locally estimated from response usage and maintained pricing data. |
| Native prompt caching | `supported` |  |
| Native provider web search | `supported` |  |
| Native provider compaction | `supported` |  |
| Flex processing | `supported` |  |
| Fast or priority processing tier | `supported` |  |
| Image input | `supported` |  |
| PDF or file input | `conditional` | Requires upload-before-send through the Files API. |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `supported` |  |

### OpenAI Responses — saved ChatGPT account

- Implementation: `openai_responses`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `not_applicable` |  |
| Subscription-account authentication | `supported` |  |
| Model discovery | `conditional` | Uses saved-account model discovery with maintained fallbacks. |
| Streaming responses | `supported` | Current ChatGPT route is streaming-only. |
| Native tool calling | `supported` |  |
| Native reasoning controls and metadata | `supported` |  |
| Native verbosity control | `conditional` | Model-gated. |
| Usage and token metadata | `supported` |  |
| Cost reporting or estimation | `conditional` | API-equivalent local estimate, not subscription billing. |
| Native prompt caching | `conditional` | Session cache keys are supported; 24-hour retention is suppressed. |
| Native provider web search | `supported` |  |
| Native provider compaction | `supported` |  |
| Flex processing | `unsupported` | The ChatGPT-hosted endpoint does not support flex processing. |
| Fast or priority processing tier | `supported` | Uses the ChatGPT backend's priority-tier wire name. |
| Image input | `supported` |  |
| PDF or file input | `conditional` | Requires provider upload/file support. |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `supported` |  |

### OpenRouter Chat Completions

- Implementation: `openrouter`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `unsupported` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` | Selected-model capability discovery must report tools support. |
| Native reasoning controls and metadata | `conditional` | Selected-model capability discovery must report reasoning support. |
| Native verbosity control | `conditional` | Selected-model capability discovery must report verbosity support. |
| Usage and token metadata | `conditional` | Requires usage data in the provider response. |
| Cost reporting or estimation | `conditional` | Uses provider-returned cost metadata when present. |
| Native prompt caching | `conditional` | Claude-style cache controls apply to compatible Anthropic model routes. |
| Native provider web search | `supported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` | Image attachments depend on model/provider acceptance. |
| PDF or file input | `unsupported` |  |
| Image generation | `conditional` | Implemented through the separate OpenRouter image-generation route. |
| Provider routing controls | `supported` |  |
| Retry and rate-limit policy | `supported` |  |

### OpenRouter Responses

- Implementation: `openrouter_responses`
- Availability: `optional`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `unsupported` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` |  |
| Native reasoning controls and metadata | `conditional` |  |
| Native verbosity control | `conditional` |  |
| Usage and token metadata | `conditional` |  |
| Cost reporting or estimation | `conditional` |  |
| Native prompt caching | `conditional` | Claude-style cache behavior for compatible routes. |
| Native provider web search | `supported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` |  |
| PDF or file input | `unknown` |  |
| Image generation | `unsupported` |  |
| Provider routing controls | `unknown` |  |
| Retry and rate-limit policy | `conditional` |  |

### Anthropic Messages

- Implementation: `anthropic-compatible`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `planned` | OAuth is owned by a separate maintained provider task. |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `supported` |  |
| Native reasoning controls and metadata | `supported` |  |
| Native verbosity control | `unsupported` |  |
| Usage and token metadata | `supported` |  |
| Cost reporting or estimation | `planned` | Maintained pricing-based cost estimation requirement is not started. |
| Native prompt caching | `supported` |  |
| Native provider web search | `planned` | Server web tools are deferred to a maintained provider subtask. |
| Native provider compaction | `planned` | Native compaction/context editing is deferred to a maintained provider subtask. |
| Flex processing | `not_applicable` |  |
| Fast or priority processing tier | `planned` | Fast mode and service tiers are deferred provider work. |
| Image input | `planned` | Image attachments are deferred provider work. |
| PDF or file input | `planned` | Files/PDF/document support is deferred provider work. |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `supported` |  |

### Ollama-compatible local route

- Implementation: `reference-openai-compatible-provider`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `not_applicable` | The checked-in route has no API-key field. |
| Subscription-account authentication | `unknown` | Cloud-named model identifiers may impose external account requirements. |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` |  |
| Native reasoning controls and metadata | `conditional` |  |
| Native verbosity control | `unknown` |  |
| Usage and token metadata | `conditional` |  |
| Cost reporting or estimation | `conditional` |  |
| Native prompt caching | `unsupported` |  |
| Native provider web search | `unsupported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` |  |
| PDF or file input | `unsupported` |  |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `conditional` |  |

### Fireworks OpenAI-compatible route

- Implementation: `reference-openai-compatible-provider`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `unsupported` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` |  |
| Native reasoning controls and metadata | `conditional` |  |
| Native verbosity control | `unknown` |  |
| Usage and token metadata | `conditional` |  |
| Cost reporting or estimation | `conditional` |  |
| Native prompt caching | `unsupported` |  |
| Native provider web search | `unsupported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` |  |
| PDF or file input | `unsupported` |  |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `supported` |  |

### Z.ai OpenAI-compatible route

- Implementation: `reference-openai-compatible-provider`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `unsupported` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` |  |
| Native reasoning controls and metadata | `conditional` |  |
| Native verbosity control | `unknown` |  |
| Usage and token metadata | `conditional` |  |
| Cost reporting or estimation | `conditional` |  |
| Native prompt caching | `unsupported` |  |
| Native provider web search | `unsupported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` |  |
| PDF or file input | `unsupported` |  |
| Image generation | `unsupported` |  |
| Provider routing controls | `supported` | Checked-in General and Coding endpoint choices. |
| Retry and rate-limit policy | `supported` |  |

### Custom OpenAI-compatible endpoint

- Implementation: `reference-openai-compatible-provider`
- Availability: `optional`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `conditional` |  |
| Subscription-account authentication | `unknown` |  |
| Model discovery | `supported` |  |
| Streaming responses | `supported` |  |
| Native tool calling | `conditional` |  |
| Native reasoning controls and metadata | `conditional` |  |
| Native verbosity control | `unknown` |  |
| Usage and token metadata | `conditional` |  |
| Cost reporting or estimation | `conditional` |  |
| Native prompt caching | `unsupported` |  |
| Native provider web search | `unsupported` |  |
| Native provider compaction | `unsupported` |  |
| Flex processing | `unsupported` |  |
| Fast or priority processing tier | `unsupported` |  |
| Image input | `conditional` |  |
| PDF or file input | `unsupported` |  |
| Image generation | `unsupported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `conditional` |  |

### OpenRouter image generation

- Implementation: `openrouter`
- Availability: `default_configured`

| Native/provider feature | Status | Notes |
|---|---|---|
| API-key authentication | `supported` |  |
| Subscription-account authentication | `unsupported` |  |
| Model discovery | `conditional` |  |
| Streaming responses | `unsupported` |  |
| Native tool calling | `not_applicable` |  |
| Native reasoning controls and metadata | `not_applicable` |  |
| Native verbosity control | `not_applicable` |  |
| Usage and token metadata | `unknown` |  |
| Cost reporting or estimation | `unknown` |  |
| Native prompt caching | `not_applicable` |  |
| Native provider web search | `not_applicable` |  |
| Native provider compaction | `not_applicable` |  |
| Flex processing | `not_applicable` |  |
| Fast or priority processing tier | `not_applicable` |  |
| Image input | `supported` |  |
| PDF or file input | `unsupported` |  |
| Image generation | `supported` |  |
| Provider routing controls | `not_applicable` |  |
| Retry and rate-limit policy | `unknown` |  |

## Model-family-specific features

### Codex-oriented GPT-5.4-mini shell-command profiles

- Profiles: `cloud-script-author`, `codex-openai`, `codex-openrouter`
- Provider routes: `openai`, `openrouter`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` | Uses shell_command for the checked-in GPT-5.4 and GPT-5.4-mini models. |
| Read files | `conditional` | Available through shell commands rather than a dedicated file-read tool. |
| Write files | `conditional` | Available through shell commands rather than a dedicated file-write tool. |
| Edit files | `conditional` | Available through shell commands and patching. |
| Glob or list files | `conditional` | Available through shell commands. |
| Search file contents | `conditional` | Available through shell commands. |
| Apply patch | `supported` |  |
| Read images or media | `supported` |  |
| Non-native web fetch | `conditional` | No dedicated fetch tool; shell network tools may be used within policy. |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `conditional` | Depends on the selected OpenAI or OpenRouter provider route and session setting. |
| MCP tools | `conditional` | Implemented but disabled by the common default mixin. |
| Skills | `supported` |  |
| Background shell tasks | `unknown` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `conditional` | Available only on the OpenAI Responses route. |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` | The selected generic GPT-5 prompt promises update_plan, but no selected tool implements it. |
| Persistent subagents | `unsupported` |  |

### Codex-oriented GPT-5.4 API profile

- Profiles: `codex-openai-api`
- Provider routes: `openai`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` | Uses shell_command for the checked-in GPT-5.4 model. |
| Read files | `conditional` | Available through shell commands rather than a dedicated file-read tool. |
| Write files | `conditional` | Available through shell commands rather than a dedicated file-write tool. |
| Edit files | `conditional` | Available through shell commands and patching. |
| Glob or list files | `conditional` | Available through shell commands. |
| Search file contents | `conditional` | Available through shell commands. |
| Apply patch | `supported` |  |
| Read images or media | `supported` |  |
| Non-native web fetch | `conditional` | No dedicated fetch tool; shell network tools may be used within policy. |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `supported` |  |
| MCP tools | `conditional` | Implemented but disabled by the common default mixin. |
| Skills | `supported` |  |
| Background shell tasks | `unknown` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `supported` |  |
| Reasoning controls | `supported` |  |
| Provider attachments | `supported` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` | No selected todo/plan tool is registered; the distinct GPT-5.4 prompt was not part of the generic GPT-5 update_plan mismatch. |
| Persistent subagents | `unsupported` |  |

### GPT-5 Codex-oriented shell-array profiles

- Profiles: `gpt-5-openai`, `gpt-5-openrouter`
- Provider routes: `openai`, `openrouter`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` | Uses the array-form shell tool. |
| Read files | `conditional` |  |
| Write files | `conditional` |  |
| Edit files | `conditional` |  |
| Glob or list files | `conditional` |  |
| Search file contents | `conditional` |  |
| Apply patch | `supported` | Dedicated plugin is disabled, but shell interception routes apply_patch invocations. |
| Read images or media | `supported` |  |
| Non-native web fetch | `conditional` |  |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `conditional` |  |
| MCP tools | `conditional` | Implemented but disabled by default. |
| Skills | `supported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `conditional` | OpenAI Responses route only. |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` | The selected prompt promises update_plan, but no selected tool implements it. |
| Persistent subagents | `unsupported` |  |

### Claude-compatible tool profiles

- Profiles: `claude-anthropic`, `claude-openrouter`, `glm-ollama`, `deepseek-ollama`, `zai`
- Provider routes: `anthropic`, `openrouter`, `ollama`, `zai`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` |  |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `supported` | Read handles images and PDF rendering subject to local dependencies and provider interop. |
| Non-native web fetch | `supported` |  |
| Non-native web search | `conditional` | Enabled for the direct Anthropic and OpenRouter Claude profiles; requires Gemini or Tavily credentials. |
| Provider-native web search | `conditional` | Provider-specific and not equivalent to the Claude WebSearch tool. |
| MCP tools | `conditional` | Implemented but disabled by the common default mixin. |
| Skills | `unsupported` |  |
| Background shell tasks | `supported` |  |
| Profile-level compaction | `supported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` | OpenRouter route supports images; direct Anthropic package does not currently implement attachments. |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Qwen-style profile

- Profiles: `qwen`
- Provider routes: `openrouter`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` |  |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `conditional` |  |
| Non-native web fetch | `supported` |  |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `conditional` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Gemini-style and GLM-with-Gemini-tools profiles

- Profiles: `gemini`, `glm`
- Provider routes: `openrouter`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` |  |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `conditional` |  |
| Non-native web fetch | `supported` |  |
| Non-native web search | `supported` | Enabled in the checked-in profiles; requires Gemini or Tavily credentials. |
| Provider-native web search | `conditional` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `conditional` | Gemini compaction plugins exist but are optional and not selected by the default profiles. |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Grok-style profile with Qwen composition

- Profiles: `grok`
- Provider routes: `openrouter`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` | Current source declares bash; two stale tests omit it. |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` | Provided by the residual Qwen package surface. |
| Search file contents | `supported` | Provided by the residual Qwen package surface. |
| Apply patch | `unsupported` |  |
| Read images or media | `unsupported` |  |
| Non-native web fetch | `supported` | Provided by the residual Qwen package surface. |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `conditional` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Kimi-style profiles

- Profiles: `kimi`, `kimi-ollama`
- Provider routes: `openrouter`, `ollama`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `supported` |  |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `conditional` | ReadMediaFile is capability-gated; image input is the default package capability. |
| Non-native web fetch | `supported` |  |
| Non-native web search | `conditional` | Enabled for the OpenRouter Kimi profile; requires a configured search provider. |
| Provider-native web search | `conditional` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `supported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Provider-only generic profiles

- Profiles: `ollama`, `fireworks`
- Provider routes: `ollama`, `fireworks`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `unsupported` |  |
| Read files | `unsupported` |  |
| Write files | `unsupported` |  |
| Edit files | `unsupported` |  |
| Glob or list files | `unsupported` |  |
| Search file contents | `unsupported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `unsupported` |  |
| Non-native web fetch | `unsupported` |  |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `unsupported` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `conditional` |  |
| Provider attachments | `conditional` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### OpenRouter image-generation profile

- Profiles: `openrouter-image`
- Provider routes: `openrouter_image_generation`
- Availability: `default_configured`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `not_applicable` |  |
| Read files | `not_applicable` |  |
| Write files | `not_applicable` |  |
| Edit files | `not_applicable` |  |
| Glob or list files | `not_applicable` |  |
| Search file contents | `not_applicable` |  |
| Apply patch | `not_applicable` |  |
| Read images or media | `not_applicable` |  |
| Non-native web fetch | `not_applicable` |  |
| Non-native web search | `not_applicable` |  |
| Provider-native web search | `not_applicable` |  |
| MCP tools | `not_applicable` |  |
| Skills | `not_applicable` |  |
| Background shell tasks | `not_applicable` |  |
| Profile-level compaction | `not_applicable` |  |
| Provider-native compaction | `not_applicable` |  |
| Reasoning controls | `not_applicable` |  |
| Provider attachments | `supported` |  |
| Provider image generation | `supported` |  |
| Todo or plan tool | `not_applicable` |  |
| Persistent subagents | `not_applicable` |  |

### Embedded Codex-like tools

- Profiles: distribution-specific; no default profile ID
- Provider routes: `embedded runtime`
- Availability: `distribution_specific`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `conditional` | Pure-Python sed, rg, find, and bounded curl emulation; no arbitrary shell. |
| Read files | `supported` |  |
| Write files | `conditional` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `supported` |  |
| Read images or media | `unsupported` |  |
| Non-native web fetch | `supported` |  |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `unsupported` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `unsupported` |  |
| Provider attachments | `unsupported` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

### Embedded Claude-like tools

- Profiles: distribution-specific; no default profile ID
- Provider routes: `embedded runtime`
- Availability: `distribution_specific`

| Feature | Status | Notes |
|---|---|---|
| Shell execution | `unsupported` |  |
| Read files | `supported` |  |
| Write files | `supported` |  |
| Edit files | `supported` |  |
| Glob or list files | `supported` |  |
| Search file contents | `supported` |  |
| Apply patch | `unsupported` |  |
| Read images or media | `unsupported` |  |
| Non-native web fetch | `supported` |  |
| Non-native web search | `unsupported` |  |
| Provider-native web search | `unsupported` |  |
| MCP tools | `unsupported` |  |
| Skills | `unsupported` |  |
| Background shell tasks | `unsupported` |  |
| Profile-level compaction | `unsupported` |  |
| Provider-native compaction | `unsupported` |  |
| Reasoning controls | `unsupported` |  |
| Provider attachments | `unsupported` |  |
| Provider image generation | `unsupported` |  |
| Todo or plan tool | `unsupported` |  |
| Persistent subagents | `unsupported` |  |

## Interpretation boundaries

- Default selection is not the same as successful clean-runtime loading.
- Conditional provider cells require the stated model, account, route,
  capability discovery, or explicit setting.
- Provider-native web search is separate from model-family tools backed
  by Gemini, Tavily, or local URL fetching.
- Profile-level compaction is separate from provider-native compaction.
- Cost values may be provider-reported or locally estimated and are not
  automatically billing or invoice truth.
- Planned cells are not current support.

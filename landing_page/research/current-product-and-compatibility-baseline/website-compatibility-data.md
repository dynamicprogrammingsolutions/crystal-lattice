# Website Compatibility Data

Review state: `accepted`
Maturity: `draft`

Compatibility profiles and tool bundles are Crystal Lattice implementations, not official upstream applications or sessions.

Downstream website work may refine selection, wording, grouping, and presentation while preserving accepted compatibility boundaries and source traceability.

## Product features

Complete per-plugin application and session feature rows that are not repeated in the provider or model-family tool tables. Publication work may later shorten descriptions or hide review-only columns.

| Plugin | Path | Status | Description | Limitations |
|---|---|---|---|---|
| `application-config-app` | `plugins/application-config-app` | Available | Provides application-level actions to request a complete application reload and to update explicitly allowlisted provider keys in a configured dotenv file. | Process environment is externally managed; secret input does not prove exhaustive log/cache/history redaction. |
| `cloud-agent-app` | `plugins/cloud-agent-app` | Conditional | Cloud agent application plugin and managed SSH transfer adapter. | No Docker, orchestrator, SSH, transfer, cloud link, deployment, or produced runtime executed. |
| `cost-tracking` | `plugins/cost-tracking` | Available | Generic, provider-agnostic cost tracking plugin for the Crystal Lattice platform. | Provider-reported or locally estimated values are not invoices; availability differs by route. |
| `duration-tracking` | `plugins/duration-tracking` | Optional | Generic, provider-agnostic duration tracking plugin for the Crystal Lattice platform. | Not selected in checked-in default; distinct from selected timestamp message-duration metadata. |
| `feature-file-context` | `plugins/feature-file-context` | Available | Feature plugin providing `@file:` marker expansion and file completions. | No dedicated mobile/desktop completion UI established; inserted content has ordinary prompt/history privacy risk. |
| `feature-request-options` | `plugins/feature-request-options` | Conditional | Feature plugin that merges `request_options` from config into the provider payload, with support for declarative UI configuration using flat override keys. | Schema exposure does not prove upstream provider accepts every option or model is available. |
| `feature-system-message` | `plugins/feature-system-message` | Available | Feature plugin providing configurable system-message templating for request-time prompt composition. | Interactive terminal and standalone CLI/Python have no generic session-action executor; terminal request composition/history rendering still applies. Compiled text can contain sensitive project context. |
| `feature-web-context` | `plugins/feature-web-context` | Conditional | Feature plugin providing `@web:` marker expansion and URL completions. | No remote fetch was run; URL safety, reachability, and extraction success are unverified. |
| `generate-title-app` | `plugins/generate-title-app` | Conditional | Application-level plugin for generating session titles (and descriptions). | Default model override availability/entitlement unknown; generation can race with message changes. |
| `message-export-actions` | `plugins/message-export-actions` | Optional | Optional application actions for exporting messages or sessions as Markdown, PDF, EPUB/Kindle-compatible files, and generated session assets. | Not selected by default; no generic terminal action execution; conversion/browser/pandoc/SMTP/Keychain/native-share workflows not completed. |
| `rebuild-native-app` | `plugins/rebuild-native-app` | Available | Application-level plugin to rebuild provider-native history from core messages. | No automatic snapshot policy in this action; provider-native representation remains provider-specific. |
| `session-actions-app` | `plugins/session-actions-app` | Available | Application-level plugin providing copy/fork/delete session actions. | No generic terminal action runner established; unknown-agent deletion and concurrency edges need resolution. |
| `session-archive-app` | `plugins/session-archive-app` | Available | Application-level plugin that archives and restores sessions. | Default filter changes visible membership; generic client support is not native UI verification. |
| `session-asset-attachments` | `plugins/session-asset-attachments` | Conditional | Generic application-level actions for downloading session-owned attachment assets. | Generic storage/download does not mean every provider accepts attachments; terminal/headless workflow not established. |
| `session-main-search-app` | `plugins/session-main-search-app` | Available | Application plugin that contributes the ordinary declarative main search and focused text filters for session lists. | Does not search all messages or assistant/tool content; client fallback omits first_user_message; no server full-text endpoint. |
| `session-message-count-meta-app` | `plugins/session-message-count-meta-app` | Available | Application-level plugin that computes message-count fields for sessions. | Derived count, not separately persisted; generic client metadata rendering is source/test bounded. |
| `session-ordering-buckets-app` | `plugins/session-ordering-buckets-app` | Available | Application-level plugin defining bucketed ordering for session lists. | Ordering is time-sensitive and plugin-derived; no arbitrary user sort control established. |
| `session-pinned-app` | `plugins/session-pinned-app` | Available | Application-level plugin that toggles and filters pinned state on sessions. | No generic terminal action execution; native UI suites not run. |
| `session-status-app` | `plugins/session-status-app` | Available | Application-level plugin for assigning and filtering session workflow status. | Application adds public order metadata that one plugin test does not expect; workflow status is distinct from request execution status. |
| `session-timestamp-meta-app` | `plugins/session-timestamp-meta-app` | Available | Application-level plugin that computes timestamp-derived fields for sessions and contributes the `modified_after` timezone-aware session-list filter. | Derived projection; fallback/time-bound behavior can change without metadata mutation. |
| `session-title-app` | `plugins/session-title-app` | Available | Application-level plugin providing actions and UI schema for editing session titles. | Event-store test drift is not title behavior proof; generic terminal action execution unknown. |
| `sleep-prevention-app` | `plugins/sleep-prevention-app` | Optional | Application plugin that exposes a live server setting for keeping the local server process awake. | Not selected by default; no real OS hold or native client workflow run. |
| `summarize-range-app` | `plugins/summarize-range-app` | Conditional | Application-level plugin providing summarize-range session actions. | No hosted summarization result; action does not itself establish a recovery snapshot. |
| `timestamp-extension` | `plugins/timestamp-extension` | Available | Timing-related feature plugins. | Distinct from optional duration-tracking reports and human-time telemetry. |

### Represented in the other matrices

- **Provider Support:** `anthropic-compatible`, `chatgpt-auth-app`, `openai_responses`, `openrouter`, `reference-openai-compatible-provider`
- **Model Family Features:** `gemini-compaction-app`, `gemini-compaction-feature`, `mcp-runtime-app`
- **Internal Infrastructure:** `plugins-tool-gating-feature-toolgatingfeature`

## Provider support

Complete provider-grouped feature rows for every retained provider route. Unsupported and not-applicable capabilities are omitted rather than rendered as generic negative cells.

### OpenAI Responses — API key

Access: API key

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Native verbosity control | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_verbosity` | Passes a provider-native response verbosity control for model families that support it. Shown for supported model families, currently GPT-5-class models. |
| Usage and token metadata | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. Locally estimated from response usage and maintained pricing data. |
| Native prompt caching | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_prompt_caching` | Configures and reports the provider's native prompt-caching behavior. |
| Native provider web search | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_websearch` | Enables the provider's own hosted web-search capability rather than a model-family search tool. |
| Native provider compaction | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_native_compaction` | Uses provider-native context compaction while preserving continuation state. |
| Flex processing | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_flex_processing` | Selects the provider's lower-priority flex processing mode. |
| Fast or priority processing tier | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_fast_mode` | Selects the provider's fast, priority, or equivalent processing tier. |
| Image input | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_attachments` | Maps image attachments into the provider request format. |
| PDF or file input | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_attachments` | Maps PDF or file attachments into the provider request or upload flow. Requires upload-before-send through the Files API. |
| Retry and rate-limit policy | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Applies route-specific retry, throttling, and rate-limit handling. |

### OpenAI Responses — saved ChatGPT account

Access: Saved ChatGPT account

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Subscription-account authentication | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_chatgpt_auth` | Authenticates through a saved subscription-account session rather than a direct API key. |
| Model discovery | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Discovers available models through the provider route and applies maintained fallbacks where documented. Uses saved-account model discovery with maintained fallbacks. |
| Streaming responses | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Streams provider response events into the Crystal Lattice request pipeline. Current ChatGPT route is streaming-only. |
| Native tool calling | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Native verbosity control | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_verbosity` | Passes a provider-native response verbosity control for model families that support it. Model-gated. |
| Usage and token metadata | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. API-equivalent local estimate, not subscription billing. |
| Native prompt caching | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_prompt_caching` | Configures and reports the provider's native prompt-caching behavior. Session cache keys are supported; 24-hour retention is suppressed. |
| Native provider web search | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_websearch` | Enables the provider's own hosted web-search capability rather than a model-family search tool. |
| Native provider compaction | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_native_compaction` | Uses provider-native context compaction while preserving continuation state. |
| Fast or priority processing tier | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_fast_mode` | Selects the provider's fast, priority, or equivalent processing tier. Uses the ChatGPT backend's priority-tier wire name. |
| Image input | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_attachments` | Maps image attachments into the provider request format. |
| PDF or file input | Conditional | `openai_responses`<br>`plugins/openai_responses` | `openai_responses_attachments` | Maps PDF or file attachments into the provider request or upload flow. Requires provider upload/file support. |
| Retry and rate-limit policy | Available | `openai_responses`<br>`plugins/openai_responses` | `openai_responses` | Applies route-specific retry, throttling, and rate-limit handling. |

### OpenRouter Chat Completions

Access: API key

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `openrouter`<br>`plugins/openrouter` | `openrouter` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `openrouter`<br>`plugins/openrouter` | `openrouter` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `openrouter`<br>`plugins/openrouter` | `openrouter` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. Selected-model capability discovery must report tools support. |
| Native reasoning controls and metadata | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. Selected-model capability discovery must report reasoning support. |
| Native verbosity control | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_verbosity` | Passes a provider-native response verbosity control for model families that support it. Selected-model capability discovery must report verbosity support. |
| Usage and token metadata | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_usage` | Normalizes provider usage and token metadata for the application. Requires usage data in the provider response. |
| Cost reporting or estimation | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. Uses provider-returned cost metadata when present. |
| Native prompt caching | Conditional | `openrouter`<br>`plugins/openrouter` | `claude_caching_extension` | Configures and reports the provider's native prompt-caching behavior. Claude-style cache controls apply to compatible Anthropic model routes. |
| Native provider web search | Available | `openrouter`<br>`plugins/openrouter` | `openrouter_websearch` | Enables the provider's own hosted web-search capability rather than a model-family search tool. |
| Image input | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_attachments` | Maps image attachments into the provider request format. Image attachments depend on model/provider acceptance. |
| Image generation | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_image_generation` | Uses the provider route to generate image output. Implemented through the separate OpenRouter image-generation route. |
| Provider routing controls | Available | `openrouter`<br>`plugins/openrouter` | `openrouter` | Passes provider or endpoint routing controls owned by this route. |
| Retry and rate-limit policy | Available | `openrouter`<br>`plugins/openrouter` | `openrouter` | Applies route-specific retry, throttling, and rate-limit handling. |

### OpenRouter Responses

Access: API key; optional Responses route

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Native verbosity control | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_verbosity` | Passes a provider-native response verbosity control for model families that support it. |
| Usage and token metadata | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. |
| Native prompt caching | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_claude_caching` | Configures and reports the provider's native prompt-caching behavior. Claude-style cache behavior for compatible routes. |
| Native provider web search | Available | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses_websearch` | Enables the provider's own hosted web-search capability rather than a model-family search tool. |
| Image input | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses` | Maps image attachments into the provider request format. |
| Retry and rate-limit policy | Conditional | `openrouter_responses`<br>`plugins/openrouter_responses` | `openrouter_responses` | Applies route-specific retry, throttling, and rate-limit handling. |

### Anthropic Messages

Access: API key

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic` | Authenticates requests with the API key configured for this provider route. |
| Subscription-account authentication | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_oauth` | Planned: authenticates through a saved subscription-account session rather than a direct API key. OAuth is owned by a separate maintained provider task. |
| Model discovery | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_reasoning`<br>`anthropic_reasoning_controls` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Usage and token metadata | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_cost_estimation` | Planned: supplies provider-reported cost data or a clearly identified local estimate derived from usage. Maintained pricing-based cost estimation requirement is not started. |
| Native prompt caching | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_prompt_caching` | Configures and reports the provider's native prompt-caching behavior. |
| Native provider web search | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_server_web_tools` | Planned: enables the provider's own hosted web-search capability rather than a model-family search tool. Server web tools are deferred to a maintained provider subtask. |
| Native provider compaction | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_compaction`<br>`anthropic_context_editing` | Planned: uses provider-native context compaction while preserving continuation state. Native compaction/context editing is deferred to a maintained provider subtask. |
| Fast or priority processing tier | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_fast_mode` | Planned: selects the provider's fast, priority, or equivalent processing tier. Fast mode and service tiers are deferred provider work. |
| Image input | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_attachments` | Planned: maps image attachments into the provider request format. Image attachments are deferred provider work. |
| PDF or file input | Planned | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic_files` | Planned: maps PDF or file attachments into the provider request or upload flow. Files/PDF/document support is deferred provider work. |
| Retry and rate-limit policy | Available | `anthropic-compatible`<br>`plugins/anthropic-compatible` | `anthropic` | Applies route-specific retry, throttling, and rate-limit handling. |

### Ollama-compatible local route

Access: Local endpoint; cloud-named models may have external account requirements

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Model discovery | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Usage and token metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. |
| Image input | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible_attachments` | Maps image attachments into the provider request format. |
| Retry and rate-limit policy | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Applies route-specific retry, throttling, and rate-limit handling. |

### Fireworks OpenAI-compatible route

Access: API key

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Usage and token metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. |
| Image input | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible_attachments` | Maps image attachments into the provider request format. |
| Retry and rate-limit policy | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Applies route-specific retry, throttling, and rate-limit handling. |

### Z.ai OpenAI-compatible route

Access: API key; Coding or General endpoint

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Usage and token metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. |
| Image input | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible_attachments` | Maps image attachments into the provider request format. |
| Provider routing controls | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Passes provider or endpoint routing controls owned by this route. Checked-in General and Coding endpoint choices. |
| Retry and rate-limit policy | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Applies route-specific retry, throttling, and rate-limit handling. |

### Custom OpenAI-compatible endpoint

Access: Endpoint-specific

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Streaming responses | Available | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Streams provider response events into the Crystal Lattice request pipeline. |
| Native tool calling | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_tools` | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. |
| Native reasoning controls and metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_reasoning` | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. |
| Usage and token metadata | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Normalizes provider usage and token metadata for the application. |
| Cost reporting or estimation | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_usage` | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. |
| Image input | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible_attachments` | Maps image attachments into the provider request format. |
| Retry and rate-limit policy | Conditional | `reference-openai-compatible-provider`<br>`plugins/reference-openai-compatible-provider` | `reference_openai_compatible` | Applies route-specific retry, throttling, and rate-limit handling. |

### OpenRouter image generation

Access: API key

| Feature | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| API-key authentication | Available | `openrouter`<br>`plugins/openrouter` | `openrouter_image_generation` | Authenticates requests with the API key configured for this provider route. |
| Model discovery | Conditional | `openrouter`<br>`plugins/openrouter` | `openrouter_image_generation` | Discovers available models through the provider route and applies maintained fallbacks where documented. |
| Image input | Available | `openrouter`<br>`plugins/openrouter` | `openrouter_image_generation_attachments` | Maps image attachments into the provider request format. |
| Image generation | Available | `openrouter`<br>`plugins/openrouter` | `openrouter_image_generation` | Uses the provider route to generate image output. |


## Model-family tool bundles

Crystal Lattice compatibility tool bundles. These are independent implementations, not the official upstream applications.

### Codex-oriented

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Shell | Available | `codex-tools`<br>`plugins/codex-tools` | `shell`<br>`shell_command` | Run commands using the model-appropriate array or shell-command schema. |
| Apply patch | Available | `codex-tools`<br>`plugins/codex-tools` | `apply_patch` | Apply structured multi-file patches with Codex-compatible patch syntax. |
| View image | Available | `codex-tools`<br>`plugins/codex-tools` | `view_image` | Load a local image into model-visible input. |
| MCP tools | Optional | `codex-tools`<br>`plugins/codex-tools` | `codex_mcp_tool` | Discover and call configured MCP-server tools. |
| Skills | Available | `codex-tools`<br>`plugins/codex-tools` | `codex_skills` | Discover configured skills and expose their instructions to the agent. |
| Update plan | Planned | `codex-tools`<br>`plugins/codex-tools` | `update_plan` | Maintain a structured pending, active, and completed task plan. |
| Exec command | Planned | `codex-tools`<br>`plugins/codex-tools` | `exec_command` | Start an interactive or long-running command with a persistent process handle. |
| Write stdin | Planned | `codex-tools`<br>`plugins/codex-tools` | `write_stdin` | Send input to a command started through Exec command. |
| Request user input | Planned | `codex-tools`<br>`plugins/codex-tools` | `request_user_input` | Ask a non-blocking question and continue from the user's follow-up answer. |
| Spawn subagent | Planned | `codex-tools`<br>`plugins/codex-tools` | `spawn_subagent` | Start a configured agent in a persistent child session. |
| Wait for subagent | Planned | `codex-tools`<br>`plugins/codex-tools` | `wait_for_subagent` | Wait for one or more child-agent runs to make progress or finish. |
| Send subagent input | Planned | `codex-tools`<br>`plugins/codex-tools` | `send_subagent_input` | Continue an existing child session with persistent follow-up input. |
| List subagents | Planned | `codex-tools`<br>`plugins/codex-tools` | `list_subagents` | List persistent child sessions and their current status. |
| Close subagent | Planned | `codex-tools`<br>`plugins/codex-tools` | `close_subagent` | Close or cancel a persistent child-agent run. |

### Claude-compatible

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Bash | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_bash_tool` | Run foreground or background shell commands with persistent working-directory behavior. |
| Read | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_read_tool` | Read text, images, PDFs, and supported notebook content. |
| Write | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_write_tool` | Create or replace files with read-before-write protection. |
| Edit | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_edit_tool` | Perform exact text replacements with read-before-edit protection. |
| Glob | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_glob_tool` | Find files by path pattern. |
| Grep | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_grep_tool` | Search file contents with multiple result modes. |
| Web fetch | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_web_fetch_tool` | Fetch and analyze a specific URL. |
| Web search | Conditional | `claude-tools`<br>`plugins/claude-tools` | `claude_web_search_tool` | Search through configured Gemini or Tavily backends. |
| Task stop | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_task_stop_tool` | Stop a background Bash task. |
| MCP tools | Optional | `claude-tools`<br>`plugins/claude-tools` | `claude_mcp_tool` | Discover and call configured MCP-server tools with Claude-style names and results. |
| Compact conversation | Available | `claude-tools`<br>`plugins/claude-tools` | `claude_compaction` | Summarize and rewrite selected history using the Claude-compatible compaction flow. |

### Gemini-style

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Read file | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_read_file_tool` | Read text or supported media content from a file. |
| List directory | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_list_directory_tool` | List directory entries. |
| Grep search | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_grep_search_tool` | Search file contents. |
| Glob | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_glob_tool` | Find files by path pattern. |
| Write file | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_write_file_tool` | Create or replace file content. |
| Replace | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_replace_tool` | Replace exact text in a file. |
| Run shell command | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_shell_tool` | Run a shell command with bounded output. |
| Web fetch | Available | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_web_fetch_tool` | Fetch content from a specific URL. |
| Google web search | Conditional | `gemini-tools`<br>`plugins/gemini-tools` | `gemini_web_search_tool` | Search through a configured Gemini or Tavily backend. |
| Write todos | Planned | `gemini-tools`<br>`plugins/gemini-tools` | `write_todos` | Replace the Gemini-style task list and track task status. |
| MCP tools | Planned | `gemini-tools`<br>`plugins/gemini-tools` | `mcp` | Expose configured MCP-server tools with Gemini-compatible naming and results. |
| Activate skill | Planned | `gemini-tools`<br>`plugins/gemini-tools` | `activate_skill` | Load one selected skill and return its instructions and supporting files. |
| Specialist-agent tools | Planned | `gemini-tools`<br>`plugins/gemini-tools` | `specialist_agents` | Expose configured specialist agents as separate blocking tools backed by persistent child sessions. |

### Qwen-style

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Read file | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_read_file_tool` | Read file content with bounded output. |
| List directory | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_list_directory_tool` | List directory entries. |
| Grep search | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_grep_search_tool` | Search file contents. |
| Glob | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_glob_tool` | Find files by path pattern. |
| Write file | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_write_file_tool` | Create or replace file content. |
| Edit | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_edit_tool` | Apply exact file edits. |
| Bash | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_shell_tool` | Run shell commands with bounded output. |
| Web fetch | Available | `qwen-tools`<br>`plugins/qwen-tools` | `qwen_web_fetch_tool` | Fetch content from a specific URL. |
| Web search | Planned | `qwen-tools`<br>`plugins/qwen-tools` | `web_search` | Search through Dashscope, Tavily, or Google backends. |
| Todo write | Planned | `qwen-tools`<br>`plugins/qwen-tools` | `todo_write` | Replace a Qwen-style todo list with stable item IDs. |
| Skills | Planned | `qwen-tools`<br>`plugins/qwen-tools` | `skills` | Discover and load a selected skill through a Qwen-compatible tool. |
| Compaction | Planned | `qwen-tools`<br>`plugins/qwen-tools` | `compaction` | Compact conversation history and preserve Qwen-style checkpoint replay. |

### Grok-style

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| View file | Available | `grok-tools`<br>`plugins/grok-tools` | `grok_view_file_tool` | Read file content. |
| Create file | Available | `grok-tools`<br>`plugins/grok-tools` | `grok_create_file_tool` | Create a new file. |
| String-replace editor | Available | `grok-tools`<br>`plugins/grok-tools` | `grok_str_replace_editor_tool` | Edit file content through exact string replacement. |
| Bash | Available | `grok-tools`<br>`plugins/grok-tools` | `grok_shell_tool` | Run shell commands. |
| Create todo list | Planned | `grok-tools`<br>`plugins/grok-tools` | `create_todo_list` | Replace a prioritized Grok-style todo list. |
| Update todo list | Planned | `grok-tools`<br>`plugins/grok-tools` | `update_todo_list` | Patch individual todo items by ID. |
| Unified search | Planned | `grok-tools`<br>`plugins/grok-tools` | `search` | Search file names and content through one Grok-style interface. |

### Kimi-style

| Tool | Status | Plugin bundle | Plugin name | Description |
|---|---|---|---|---|
| Read file | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_read_file_tool` | Read text content with line-numbered output. |
| Read media file | Conditional | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_read_media_file_tool` | Read image or supported media content for a capable model. |
| Write file | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_write_file_tool` | Create, replace, or append file content. |
| String-replace file | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_str_replace_file_tool` | Apply one or more exact text replacements. |
| Glob | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_glob_tool` | Find files by path pattern. |
| Grep | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_grep_tool` | Search file contents. |
| Shell | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_shell_tool` | Run shell commands with a clean-environment option. |
| Fetch URL | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_fetch_url_tool` | Fetch content from a specific URL. |
| Search web | Conditional | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_web_search_tool` | Search through a configured web-search backend. |
| Compact conversation | Available | `kimi-tools`<br>`plugins/kimi-tools` | `kimi_compaction` | Compact earlier history while preserving a recent message tail. |
| Set todo list | Planned | `kimi-tools`<br>`plugins/kimi-tools` | `set_todo_list` | Replace a Kimi-style task list with pending, active, and done states. |
| MCP tools | Planned | `kimi-tools`<br>`plugins/kimi-tools` | `mcp` | Expose configured MCP-server tools with Kimi-compatible names and results. |
| Skills | Planned | `kimi-tools`<br>`plugins/kimi-tools` | `skills` | Discover configured skills and make their instructions readable to Kimi tools. |
| Task | Planned | `kimi-tools`<br>`plugins/kimi-tools` | `task` | Run a blocking task in a persisted child-agent session and return its final answer. |

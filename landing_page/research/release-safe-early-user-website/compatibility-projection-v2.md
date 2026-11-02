# Compatibility Projection V2

Review state: `focused_refresh_accepted`
Maturity: `internal_evidence`
Observed: `2026-10-24`

Configured agents and harnesses are Crystal Lattice configurations and implementations, not official upstream applications, accounts, or sessions.

Public presentation may change grouping, wording, and progressive disclosure while preserving accepted or explicitly refreshed identity, status, limitation, and source boundaries.

## Projection summary

- Configured agents: 20
- Harness families with capability detail: 6
- Provider/account routes: 10
- Plugin projects: 69

## Included configured agents

### Codex-oriented

Codex-oriented command, patch, image, skill, and optional MCP behavior implemented by Crystal Lattice.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Cloud Script Author<br><code>cloud-script-author</code> | openai-chatgpt, openai-api | codex-tools; exec_command; write_stdin; apply_patch; image; skills; MCP default-off | Included | Authors project hooks; does not provide cloud infrastructure, orchestrator availability, or official Codex parity. Its selected GPT-5 fallback prompt promises update_plan without a selected implementation. |
| Codex · OpenAI<br><code>codex-openai</code> | openai-chatgpt, openai-api | codex-tools; exec_command; write_stdin; apply_patch; image; skills; MCP default-off | Included | Auto auth changes route; mini model falls back to GPT-5 prompt; prompt references update_plan without a selected implementation; not official Codex. |
| Codex · OpenRouter<br><code>codex-openrouter</code> | openrouter-chat | codex-tools; exec_command; write_stdin; apply_patch; image; skills; MCP default-off | Included | Mini model uses generic GPT-5 prompt; live tools/reasoning depend on discovery; no official Codex/account/session parity. |
| Codex · OpenAI API<br><code>codex-openai-api</code> | openai-api | codex-tools; exec_command; write_stdin; apply_patch; image; skills; MCP default-off | Included | Forces API route and keeps native system/developer history; no dated hosted result; not official Codex. |
| GPT-5 · OpenAI<br><code>gpt-5-openai</code> | openai-chatgpt, openai-api | codex-tools; exec_command; write_stdin; apply_patch plugin disabled; image; skills; MCP default-off | Included | Tool shape differs from shell_command configurations; auto auth changes account route; no dated hosted result. |
| GPT-5 · OpenRouter<br><code>gpt-5-openrouter</code> | openrouter-chat | codex-tools; exec_command; write_stdin; apply_patch plugin disabled; image; skills; MCP default-off | Included | Tool shape differs from shell_command configurations; live capabilities depend on discovery; no dated hosted result. |

<details>
<summary>Technical configured-agent defaults</summary>

- `cloud-script-author` — model `gpt-5.4-mini`; agent plugin packages: codex-tools
- `codex-openai` — model `gpt-5.4-mini`; agent plugin packages: codex-tools
- `codex-openrouter` — model `openai/gpt-5.4-mini`; agent plugin packages: codex-tools
- `codex-openai-api` — model `gpt-5.4`; agent plugin packages: codex-tools
- `gpt-5-openai` — model `gpt-5`; agent plugin packages: codex-tools
- `gpt-5-openrouter` — model `openai/gpt-5`; agent plugin packages: codex-tools

</details>

### Claude-compatible

Claude-compatible file, search, shell, web, MCP, background-task, and compaction behavior implemented by Crystal Lattice.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Claude · Anthropic<br><code>claude-anthropic</code> | anthropic | claude-tools; direct Anthropic extensions | Included | Independent Crystal Lattice implementation, not official Claude Code. Native compaction and context editing are capability-gated; image/file input and hosted-provider verification remain unavailable. |
| Claude · OpenRouter<br><code>claude-openrouter</code> | openrouter-chat | claude-tools; OpenRouter capability-gated tools/reasoning/cache/attachments | Included | Requests Anthropic ordering/no fallback but does not prove fulfillment; tools/reasoning depend on live discovery; not official Claude Code. |
| GLM · Ollama<br><code>glm-ollama</code> | ollama | claude-tools through reference-compatible provider | Included | Cloud-named model identifier still uses localhost route; no live model/account/tool evidence. |
| DeepSeek · Ollama<br><code>deepseek-ollama</code> | ollama | claude-tools through reference-compatible provider | Included | Cloud-named model identifier still uses localhost route; no account, model availability, or live tool acceptance evidence. |
| Z.ai<br><code>zai</code> | zai | claude-tools through reference-compatible provider | Included | Configured request options and retries do not establish endpoint acceptance, usage/cost, tools, reasoning, or account state. |

<details>
<summary>Technical configured-agent defaults</summary>

- `claude-anthropic` — model `claude-sonnet-5`; agent plugin packages: claude-tools
- `claude-openrouter` — model `anthropic/claude-haiku-4.5`; agent plugin packages: claude-tools
- `glm-ollama` — model `glm-5.2:cloud`; agent plugin packages: claude-tools
- `deepseek-ollama` — model `deepseek-v4-pro:cloud`; agent plugin packages: claude-tools
- `zai` — model `glm-5.3-flash`; agent plugin packages: claude-tools

</details>

### Gemini-oriented

Gemini-oriented file, shell, search, and web behavior, also used by selected GLM configurations.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Gemini<br><code>gemini</code> | openrouter-chat | gemini-tools; web/search conditional; apply_patch not supplied | Included | Selected declarations do not prove live tool/search/reasoning acceptance or official Gemini parity. |
| GLM · OpenRouter<br><code>glm</code> | openrouter-chat | gemini-tools; max configured reasoning input; web/search conditional | Included | Uses Gemini prompt/tools rather than GLM-native product behavior; provider order/no fallback is request intent only. |

<details>
<summary>Technical configured-agent defaults</summary>

- `gemini` — model `google/gemini-2.5-flash-lite`; agent plugin packages: gemini-tools
- `glm` — model `z-ai/glm-5.2`; agent plugin packages: gemini-tools

</details>

### Qwen-oriented

Qwen-oriented file, shell, search, and fetch behavior implemented by Crystal Lattice.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Qwen<br><code>qwen</code> | openrouter-chat | qwen-tools; local file/shell/fetch candidates; apply_patch not supplied | Included | Descriptor surface is not live model capability or official Qwen parity. |

<details>
<summary>Technical configured-agent defaults</summary>

- `qwen` — model `qwen/qwen3.5-flash-02-23`; agent plugin packages: qwen-tools

</details>

### Grok-oriented

Grok-oriented file and shell behavior composed with selected Qwen tool implementations.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Grok<br><code>grok</code> | openrouter-chat | grok-tools plus residual Qwen tools; Qwen read/write/edit disabled | Included | Duplicate bash/tool resolution and live model acceptance are unresolved; not official Grok product parity. |

<details>
<summary>Technical configured-agent defaults</summary>

- `grok` — model `x-ai/grok-4.1-fast`; agent plugin packages: grok-tools, qwen-tools

</details>

### Kimi-oriented

Kimi-oriented file, shell, web, media, and compaction behavior implemented by Crystal Lattice.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Kimi<br><code>kimi</code> | openrouter-chat | kimi-tools and Kimi compaction descriptor; search/media conditional | Included | Search/media and shell behavior are conditional/incompletely verified; not official Kimi parity. |
| Kimi · Ollama<br><code>kimi-ollama</code> | ollama | kimi-tools and configured Kimi compaction | Included | Cloud-named model uses localhost route; no live compaction/model/account evidence. |

<details>
<summary>Technical configured-agent defaults</summary>

- `kimi` — model `moonshotai/kimi-k2.5`; agent plugin packages: kimi-tools
- `kimi-ollama` — model `kimi-k2.6:cloud`; agent plugin packages: kimi-tools

</details>

### Provider-only configurations

Configured provider routes without a model-family-specific coding tool bundle.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Ollama · Local<br><code>ollama</code> | ollama | no configured-agent-specific coding-agent tool package | Included | Config does not prove daemon health, downloaded weights, model discovery, inference, or auth policy. |
| Fireworks<br><code>fireworks</code> | fireworks | no configured-agent-specific coding-agent tool package | Included | Configured endpoint/options do not establish hosted acceptance, usage, cost, reasoning, tools, or image capability. |

<details>
<summary>Technical configured-agent defaults</summary>

- `ollama` — model `qwen3:0.6b`; agent plugin packages: none
- `fireworks` — model `fireworks/gpt-oss-20b`; agent plugin packages: none

</details>

### Image-generation configuration

A specialist non-streaming image-generation configuration through OpenRouter.

| Agent | Provider route | Tool/harness summary | Status | Limitations |
|---|---|---|---|---|
| Image Generation · OpenRouter<br><code>openrouter-image</code> | openrouter-image | non-streaming image request; generic asset-backed output/attachments | Included | No hosted image request, result, cost, or entitlement evidence; terminal attachment/image workflow not established. |

<details>
<summary>Technical configured-agent defaults</summary>

- `openrouter-image` — model `black-forest-labs/flux.2-klein-4b`; agent plugin packages: none

</details>

## Harness capabilities

### Codex-oriented

Codex-oriented command, patch, image, skill, and optional MCP behavior implemented by Crystal Lattice.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| Legacy shell modes | Available | optional | Select the retained array or string-command shell surface explicitly; unified exec is the default. | refreshed |
| Apply patch | Available | included | Apply structured multi-file patches with Codex-compatible patch syntax. | accepted |
| View image | Available | included | Load a local image into model-visible input. | accepted |
| MCP tools | Available | optional | Discover and call configured MCP-server tools. | accepted |
| Skills | Available | included | Discover configured skills and expose their instructions to the agent. | accepted |
| Update plan | Planned | planned | Maintain a structured pending, active, and completed task plan. | accepted |
| Exec command | Available | included | Start an interactive or long-running command with a persistent process handle. | refreshed |
| Write stdin | Available | included | Send input to a command started through Exec command. | refreshed |
| Request user input | Planned | planned | Ask a non-blocking question and continue from the user's follow-up answer. | accepted |
| Spawn subagent | Planned | planned | Start a configured agent in a persistent child session. | accepted |
| Wait for subagent | Planned | planned | Wait for one or more child-agent runs to make progress or finish. | accepted |
| Send subagent input | Planned | planned | Continue an existing child session with persistent follow-up input. | accepted |
| List subagents | Planned | planned | List persistent child sessions and their current status. | accepted |
| Close subagent | Planned | planned | Close or cancel a persistent child-agent run. | accepted |

### Claude-compatible

Claude-compatible file, search, shell, web, MCP, background-task, and compaction behavior implemented by Crystal Lattice.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| Bash | Available | included | Run foreground or background shell commands with persistent working-directory behavior. | accepted |
| Read | Available | included | Read text, images, PDFs, and supported notebook content. | accepted |
| Write | Available | included | Create or replace files with read-before-write protection. | accepted |
| Edit | Available | included | Perform exact text replacements with read-before-edit protection. | accepted |
| Glob | Available | included | Find files by path pattern. | accepted |
| Grep | Available | included | Search file contents with multiple result modes. | accepted |
| Web fetch | Available | included | Fetch and analyze a specific URL. | accepted |
| Web search | Conditional | included | Search through configured Gemini or Tavily backends. | accepted |
| Task stop | Available | included | Stop a background Bash task. | accepted |
| MCP tools | Available | optional | Discover and call configured MCP-server tools with Claude-style names and results. | accepted |
| Compact conversation | Available | included | Run manual or background Claude-compatible compaction for full history, a prefix, or a selected range with snapshots, notifications, cancellation, and retry support. | refreshed |

### Gemini-oriented

Gemini-oriented file, shell, search, and web behavior, also used by selected GLM configurations.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| Read file | Available | included | Read text or supported media content from a file. | accepted |
| List directory | Available | included | List directory entries. | accepted |
| Grep search | Available | included | Search file contents. | accepted |
| Glob | Available | included | Find files by path pattern. | accepted |
| Write file | Available | included | Create or replace file content. | accepted |
| Replace | Available | included | Replace exact text in a file. | accepted |
| Run shell command | Available | included | Run a shell command with bounded output. | accepted |
| Web fetch | Available | included | Fetch content from a specific URL. | accepted |
| Google web search | Conditional | included | Search through a configured Gemini or Tavily backend. | accepted |
| Write todos | Planned | planned | Replace the Gemini-style task list and track task status. | accepted |
| MCP tools | Planned | planned | Expose configured MCP-server tools with Gemini-compatible naming and results. | accepted |
| Activate skill | Planned | planned | Load one selected skill and return its instructions and supporting files. | accepted |
| Specialist-agent tools | Planned | planned | Expose configured specialist agents as separate blocking tools backed by persistent child sessions. | accepted |

### Qwen-oriented

Qwen-oriented file, shell, search, and fetch behavior implemented by Crystal Lattice.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| Read file | Available | included | Read file content with bounded output. | accepted |
| List directory | Available | included | List directory entries. | accepted |
| Grep search | Available | included | Search file contents. | accepted |
| Glob | Available | included | Find files by path pattern. | accepted |
| Write file | Available | included | Create or replace file content. | accepted |
| Edit | Available | included | Apply exact file edits. | accepted |
| Bash | Available | included | Run shell commands with bounded output. | accepted |
| Web fetch | Available | included | Fetch content from a specific URL. | accepted |
| Web search | Planned | planned | Search through Dashscope, Tavily, or Google backends. | accepted |
| Todo write | Planned | planned | Replace a Qwen-style todo list with stable item IDs. | accepted |
| Skills | Planned | planned | Discover and load a selected skill through a Qwen-compatible tool. | accepted |
| Compaction | Planned | planned | Compact conversation history and preserve Qwen-style checkpoint replay. | accepted |

### Grok-oriented

Grok-oriented file and shell behavior composed with selected Qwen tool implementations.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| View file | Available | included | Read file content. | accepted |
| Create file | Available | included | Create a new file. | accepted |
| String-replace editor | Available | included | Edit file content through exact string replacement. | accepted |
| Bash | Available | included | Run shell commands. | accepted |
| Create todo list | Planned | planned | Replace a prioritized Grok-style todo list. | accepted |
| Update todo list | Planned | planned | Patch individual todo items by ID. | accepted |
| Unified search | Planned | planned | Search file names and content through one Grok-style interface. | accepted |

### Kimi-oriented

Kimi-oriented file, shell, web, media, and compaction behavior implemented by Crystal Lattice.

| Capability | Status | Availability | Description | Source state |
|---|---|---|---|---|
| Read file | Available | included | Read text content with line-numbered output. | accepted |
| Read media file | Conditional | included | Read image or supported media content for a capable model. | accepted |
| Write file | Available | included | Create, replace, or append file content. | accepted |
| String-replace file | Available | included | Apply one or more exact text replacements. | accepted |
| Glob | Available | included | Find files by path pattern. | accepted |
| Grep | Available | included | Search file contents. | accepted |
| Shell | Available | included | Run shell commands with a clean-environment option. | accepted |
| Fetch URL | Available | included | Fetch content from a specific URL. | accepted |
| Search web | Conditional | included | Search through a configured web-search backend. | accepted |
| Compact conversation | Available | included | Compact earlier history while preserving a recent message tail. | accepted |
| Set todo list | Planned | planned | Replace a Kimi-style task list with pending, active, and done states. | accepted |
| MCP tools | Planned | planned | Expose configured MCP-server tools with Kimi-compatible names and results. | accepted |
| Skills | Planned | planned | Discover configured skills and make their instructions readable to Kimi tools. | accepted |
| Task | Planned | planned | Run a blocking task in a persisted child-agent session and return its final answer. | accepted |

## Provider support

### OpenAI Responses — API key

Access: API key

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Not applicable | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Available | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Available | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Conditional | Passes a provider-native response verbosity control for model families that support it. Shown for supported model families, currently GPT-5-class models. | accepted |
| Usage and token metadata | Available | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Available | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. Locally estimated from response usage and maintained pricing data. | accepted |
| Native prompt caching | Available | Configures and reports the provider's native prompt-caching behavior. | accepted |
| Native provider web search | Available | Enables the provider's own hosted web-search capability rather than a model-family search tool. | accepted |
| Native provider compaction | Available | Uses provider-native context compaction while preserving continuation state. | accepted |
| Flex processing | Available | Selects the provider's lower-priority flex processing mode. | accepted |
| Fast or priority processing tier | Available | Selects the provider's fast, priority, or equivalent processing tier. | accepted |
| Image input | Available | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Conditional | Maps PDF or file attachments into the provider request or upload flow. Requires upload-before-send through the Files API. | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: Auto route depends on saved token presence; API and ChatGPT endpoints differ; no dated hosted result.

### OpenAI Responses — saved ChatGPT account

Access: Saved ChatGPT account

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Not applicable | API-key authentication | accepted |
| Subscription-account authentication | Available | Authenticates through a saved subscription-account session rather than a direct API key. | accepted |
| Model discovery | Conditional | Discovers available models through the provider route and applies maintained fallbacks where documented. Uses saved-account model discovery with maintained fallbacks. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. Current ChatGPT route is streaming-only. | accepted |
| Native tool calling | Available | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Available | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Conditional | Passes a provider-native response verbosity control for model families that support it. Model-gated. | accepted |
| Usage and token metadata | Available | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. API-equivalent local estimate, not subscription billing. | accepted |
| Native prompt caching | Conditional | Configures and reports the provider's native prompt-caching behavior. Session cache keys are supported; 24-hour retention is suppressed. | accepted |
| Native provider web search | Available | Enables the provider's own hosted web-search capability rather than a model-family search tool. | accepted |
| Native provider compaction | Available | Uses provider-native context compaction while preserving continuation state. | accepted |
| Flex processing | Unsupported | The ChatGPT-hosted endpoint does not support flex processing. | accepted |
| Fast or priority processing tier | Available | Selects the provider's fast, priority, or equivalent processing tier. Uses the ChatGPT backend's priority-tier wire name. | accepted |
| Image input | Available | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Conditional | Maps PDF or file attachments into the provider request or upload flow. Requires provider upload/file support. | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: Auto route depends on saved token presence; API and ChatGPT endpoints differ; no dated hosted result.

### OpenRouter Chat Completions

Access: API key

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Unsupported | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. Selected-model capability discovery must report tools support. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. Selected-model capability discovery must report reasoning support. | accepted |
| Native verbosity control | Conditional | Passes a provider-native response verbosity control for model families that support it. Selected-model capability discovery must report verbosity support. | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. Requires usage data in the provider response. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. Uses provider-returned cost metadata when present. | accepted |
| Native prompt caching | Conditional | Configures and reports the provider's native prompt-caching behavior. Claude-style cache controls apply to compatible Anthropic model routes. | accepted |
| Native provider web search | Available | Enables the provider's own hosted web-search capability rather than a model-family search tool. | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. Image attachments depend on model/provider acceptance. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Conditional | Uses the provider route to generate image output. Implemented through the separate OpenRouter image-generation route. | accepted |
| Provider routing controls | Available | Passes provider or endpoint routing controls owned by this route. | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: No live catalog, routing fulfillment, account entitlement, or billed-cost evidence.

### OpenRouter Responses

Access: API key; optional Responses route

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Unsupported | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Conditional | Passes a provider-native response verbosity control for model families that support it. | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. | accepted |
| Native prompt caching | Conditional | Configures and reports the provider's native prompt-caching behavior. Claude-style cache behavior for compatible routes. | accepted |
| Native provider web search | Available | Enables the provider's own hosted web-search capability rather than a model-family search tool. | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Not verified | PDF or file input | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not verified | Provider routing controls | accepted |
| Retry and rate-limit policy | Conditional | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

### Anthropic Messages

Access: API key

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Planned | Planned: authenticates through a saved subscription-account session rather than a direct API key. OAuth is owned by a separate maintained provider task. | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Available | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Available | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Unsupported | Native verbosity control | accepted |
| Usage and token metadata | Available | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Planned | Planned: supplies provider-reported cost data or a clearly identified local estimate derived from usage. Maintained pricing-based cost estimation requirement is not started. | accepted |
| Native prompt caching | Available | Configures and reports the provider's native prompt-caching behavior. | accepted |
| Native provider web search | Planned | Planned: enables the provider's own hosted web-search capability rather than a model-family search tool. Server web tools are deferred to a maintained provider subtask. | accepted |
| Native provider compaction | Conditional | Uses Anthropic automatic request-time compaction and preserves complete provider-native continuation blocks for later requests. | refreshed |
| Flex processing | Not applicable | Flex processing | accepted |
| Fast or priority processing tier | Planned | Planned: selects the provider's fast, priority, or equivalent processing tier. Fast mode and service tiers are deferred provider work. | accepted |
| Image input | Planned | Planned: maps image attachments into the provider request format. Image attachments are deferred provider work. | accepted |
| PDF or file input | Planned | Planned: maps PDF or file attachments into the provider request or upload flow. Files/PDF/document support is deferred provider work. | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |
| Native context editing | Conditional | Applies Anthropic-native thinking-retention and old tool-use clearing policies without deleting the local visible transcript. | refreshed |

Limitations: No hosted auth, model, compaction, or context-editing request was run for this refresh. Image/file input, subscription-account authentication, and cost estimation remain unavailable or separately planned.

### Ollama-compatible local route

Access: Local endpoint; cloud-named models may have external account requirements

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Not applicable | The checked-in route has no API-key field. | accepted |
| Subscription-account authentication | Not verified | Cloud-named model identifiers may impose external account requirements. | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Not verified | Native verbosity control | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. | accepted |
| Native prompt caching | Unsupported | Native prompt caching | accepted |
| Native provider web search | Unsupported | Native provider web search | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Conditional | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: No daemon/model/auth/inference evidence; :cloud suffix does not prove hosted account or remote execution.

### Fireworks OpenAI-compatible route

Access: API key

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Unsupported | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Not verified | Native verbosity control | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. | accepted |
| Native prompt caching | Unsupported | Native prompt caching | accepted |
| Native provider web search | Unsupported | Native provider web search | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: No hosted discovery/auth/request/retry/cost verification.

### Z.ai OpenAI-compatible route

Access: API key; Coding or General endpoint

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Unsupported | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Not verified | Native verbosity control | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. | accepted |
| Native prompt caching | Unsupported | Native prompt caching | accepted |
| Native provider web search | Unsupported | Native provider web search | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Available | Passes provider or endpoint routing controls owned by this route. Checked-in General and Coding endpoint choices. | accepted |
| Retry and rate-limit policy | Available | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

Limitations: No hosted discovery/auth/request/retry/cost verification.

### Custom OpenAI-compatible endpoint

Access: Endpoint-specific

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Conditional | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Not verified | Subscription-account authentication | accepted |
| Model discovery | Available | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Available | Streams provider response events into the Crystal Lattice request pipeline. | accepted |
| Native tool calling | Conditional | Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format. | accepted |
| Native reasoning controls and metadata | Conditional | Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model. | accepted |
| Native verbosity control | Not verified | Native verbosity control | accepted |
| Usage and token metadata | Conditional | Normalizes provider usage and token metadata for the application. | accepted |
| Cost reporting or estimation | Conditional | Supplies provider-reported cost data or a clearly identified local estimate derived from usage. | accepted |
| Native prompt caching | Unsupported | Native prompt caching | accepted |
| Native provider web search | Unsupported | Native provider web search | accepted |
| Native provider compaction | Unsupported | Native provider compaction | accepted |
| Flex processing | Unsupported | Flex processing | accepted |
| Fast or priority processing tier | Unsupported | Fast or priority processing tier | accepted |
| Image input | Conditional | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Unsupported | Image generation | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Conditional | Applies route-specific retry, throttling, and rate-limit handling. | accepted |

### OpenRouter image generation

Access: API key

| Capability | Status | Description / condition | Source state |
|---|---|---|---|
| API-key authentication | Available | Authenticates requests with the API key configured for this provider route. | accepted |
| Subscription-account authentication | Unsupported | Subscription-account authentication | accepted |
| Model discovery | Conditional | Discovers available models through the provider route and applies maintained fallbacks where documented. | accepted |
| Streaming responses | Unsupported | Streaming responses | accepted |
| Native tool calling | Not applicable | Native tool calling | accepted |
| Native reasoning controls and metadata | Not applicable | Native reasoning controls and metadata | accepted |
| Native verbosity control | Not applicable | Native verbosity control | accepted |
| Usage and token metadata | Not verified | Usage and token metadata | accepted |
| Cost reporting or estimation | Not verified | Cost reporting or estimation | accepted |
| Native prompt caching | Not applicable | Native prompt caching | accepted |
| Native provider web search | Not applicable | Native provider web search | accepted |
| Native provider compaction | Not applicable | Native provider compaction | accepted |
| Flex processing | Not applicable | Flex processing | accepted |
| Fast or priority processing tier | Not applicable | Fast or priority processing tier | accepted |
| Image input | Available | Maps image attachments into the provider request format. | accepted |
| PDF or file input | Unsupported | PDF or file input | accepted |
| Image generation | Available | Uses the provider route to generate image output. | accepted |
| Provider routing controls | Not applicable | Provider routing controls | accepted |
| Retry and rate-limit policy | Not verified | Retry and rate-limit policy | accepted |

Limitations: No hosted image response, entitlement, price, or native-client completion.

## Plugins and application features

### Included by default

| Plugin | Status | Lifecycle | Kinds | Description | Verification | Limitations |
|---|---|---|---|---|---|---|
| `anthropic-compatible` | Conditional | `default_selected` | extensions, providers | Direct Anthropic Messages provider and extensions for tools, reasoning, prompt caching, usage, native compaction, and native context editing. | `passed` | No hosted result was run for this refresh; image/file input, subscription-account authentication, and cost estimation remain unavailable or separately planned. |
| `application-config-app` | Included | `default_selected` | application | Provides application-level actions to request a complete application reload and to update explicitly allowlisted provider keys in a configured dotenv file. | `passed` | Process environment is externally managed; secret input does not prove exhaustive log/cache/history redaction. |
| `chatgpt-auth-app` | Conditional | `default_selected` | application | Minimal application plugin implementing a device-code login flow for ChatGPT-style auth. | `incomplete` | No credential read, device flow, entitlement, or hosted login verified. |
| `claude-tools` | Included | `default_selected` | features, tools | Claude-compatible file, search, shell, web, MCP, background task, and manual/background compaction bundle. | `unknown` |  |
| `cloud-agent-app` | Conditional | `default_selected` | application | Cloud agent application plugin and managed SSH transfer adapter. | `passed` | No Docker, orchestrator, SSH, transfer, cloud link, deployment, or produced runtime executed. |
| `codex-tools` | Included | `default_selected` | features, tools | Codex-oriented unified exec, patch, image, MCP, skills, and legacy shell-mode bundle. | `unknown` |  |
| `cost-tracking` | Included | `default_selected` | application, extensions | Generic, provider-agnostic cost tracking plugin for the Crystal Lattice platform. | `passed` | Provider-reported or locally estimated values are not invoices; availability differs by route. |
| `feature-file-context` | Included | `default_selected` | features | Feature plugin providing `@file:` marker expansion and file completions. | `passed` | No dedicated mobile/desktop completion UI established; inserted content has ordinary prompt/history privacy risk. |
| `feature-request-options` | Conditional | `default_selected` | features | Feature plugin that merges `request_options` from config into the provider payload, with support for declarative UI configuration using flat override keys. | `passed` | Schema exposure does not prove upstream provider accepts every option or model is available. |
| `feature-system-message` | Included | `default_selected` | features | Feature plugin providing configurable system-message templating for request-time prompt composition. | `passed` | Interactive terminal and standalone CLI/Python have no generic session-action executor; terminal request composition/history rendering still applies. Compiled text can contain sensitive project context. |
| `feature-web-context` | Conditional | `default_selected` | features | Feature plugin providing `@web:` marker expansion and URL completions. | `passed` | No remote fetch was run; URL safety, reachability, and extraction success are unverified. |
| `gemini-tools` | Included | `default_selected` | tools | Compatibility-oriented Gemini-style filesystem tools for the Crystal Lattice. | `unknown` |  |
| `generate-title-app` | Conditional | `default_selected` | application | Application-level plugin for generating session titles (and descriptions). | `passed` | Default model override availability/entitlement unknown; generation can race with message changes. |
| `grok-tools` | Included | `default_selected` | tools | Compatibility-oriented Grok-style filesystem tools for the Crystal Lattice. | `unknown` |  |
| `kimi-tools` | Included | `default_selected` | features, tools | Kimi CLI-compatible plugin bundle. It provides manual conversation compaction and file, search, web, media, and shell tools with model-facing behavior based on MoonshotAI's `kimi-cli`. | `unknown` |  |
| `mcp-runtime-app` | Conditional | `default_selected` | application | Application-level observability plugin for MCP runtimes. | `passed` | Package is selected but common Codex/Claude defaults disable MCP and sample filesystem server; no server/OAuth flow started. |
| `openai_responses` | Conditional | `default_selected` | application, extensions, features, providers | OpenAI Responses API bundle for the Crystal Lattice. | `passed` | API and ChatGPT routes differ; costs can be estimates; native compaction/attachments depend on auth/model/provider state. |
| `openrouter` | Conditional | `default_selected` | extensions, providers | OpenRouter Chat Completions and image-generation providers with capability-gated tools, reasoning, verbosity, web search, caching, attachments, usage, and image output extensions. | `passed` | Extensions have separate predicates; model names and descriptors do not prove live capability, routing, or billed cost. |
| `qwen-tools` | Included | `default_selected` | tools | Compatibility-oriented Qwen-style filesystem tools for the Crystal Lattice. | `unknown` |  |
| `rebuild-native-app` | Included | `default_selected` | application | Application-level plugin to rebuild provider-native history from core messages. | `passed` | No automatic snapshot policy in this action; provider-native representation remains provider-specific. |
| `reference-openai-compatible-provider` | Conditional | `default_selected` | extensions, providers | Generic OpenAI-compatible Chat Completions provider package for the Crystal Lattice. | `passed` | Generic implementation/tag/UI availability is not endpoint capability, account, pricing, or client-brand parity. |
| `session-actions-app` | Included | `default_selected` | application | Application-level plugin providing copy/fork/delete session actions. | `incomplete` | No generic terminal action runner established; unknown-agent deletion and concurrency edges need resolution. |
| `session-archive-app` | Included | `default_selected` | application | Application-level plugin that archives and restores sessions. | `passed` | Default filter changes visible membership; generic client support is not native UI verification. |
| `session-asset-attachments` | Conditional | `default_selected` | application | Generic application-level actions for downloading session-owned attachment assets. | `passed` | Generic storage/download does not mean every provider accepts attachments; terminal/headless workflow not established. |
| `session-main-search-app` | Included | `default_selected` | application | Application plugin that contributes the ordinary declarative main search and focused text filters for session lists. | `passed` | Does not search all messages or assistant/tool content; client fallback omits first_user_message; no server full-text endpoint. |
| `session-message-count-meta-app` | Included | `default_selected` | application | Application-level plugin that computes message-count fields for sessions. | `passed` | Derived count, not separately persisted; generic client metadata rendering is source/test bounded. |
| `session-ordering-buckets-app` | Included | `default_selected` | application | Application-level plugin defining bucketed ordering for session lists. | `passed` | Ordering is time-sensitive and plugin-derived; no arbitrary user sort control established. |
| `session-pinned-app` | Included | `default_selected` | application | Application-level plugin that toggles and filters pinned state on sessions. | `passed` | No generic terminal action execution; native UI suites not run. |
| `session-status-app` | Included | `default_selected` | application | Application-level plugin for assigning and filtering session workflow status. | `incomplete` | Application adds public order metadata that one plugin test does not expect; workflow status is distinct from request execution status. |
| `session-timestamp-meta-app` | Included | `default_selected` | application | Application-level plugin that computes timestamp-derived fields for sessions and contributes the `modified_after` timezone-aware session-list filter. | `passed` | Derived projection; fallback/time-bound behavior can change without metadata mutation. |
| `session-title-app` | Included | `default_selected` | application | Application-level plugin providing actions and UI schema for editing session titles. | `incomplete` | Event-store test drift is not title behavior proof; generic terminal action execution unknown. |
| `summarize-range-app` | Conditional | `default_selected` | application | Application-level plugin providing summarize-range session actions. | `passed` | No hosted summarization result; action does not itself establish a recovery snapshot. |
| `timestamp-extension` | Included | `default_selected` | features | Timing-related feature plugins. | `passed` | Distinct from optional duration-tracking reports and human-time telemetry. |

### Available optional plugins

| Plugin | Status | Lifecycle | Kinds | Description | Verification | Limitations |
|---|---|---|---|---|---|---|
| `bash-send-kindle-icloud` | Available | `optional` | tools | Bash tool plugin that exposes three small tools: `build_epub_from_markdown`; `send_to_kindle`; `send_markdown_to_kindle`. | `unknown` |  |
| `duration-tracking` | Available | `optional` | application, features | Generic, provider-agnostic duration tracking plugin for the Crystal Lattice platform. | `passed` | Not selected in checked-in default; distinct from selected timestamp message-duration metadata. |
| `gemini-compaction-app` | Available | `optional` | application | Gemini-style context compaction application plugin for the Crystal Lattice. | `passed` | Not selected in checked-in default; default Gemini configuration does not enable it; no hosted compaction run. |
| `gemini-compaction-feature` | Available | `optional` | feature | A Feature-level plugin that provides Gemini-style context compaction using the layered context approach. | `passed` | Not selected by default and does not own application persistence/locking. |
| `interleaved-thinking` | Available | `optional` | extensions | Optional provider extension that omits previous-turn thinking blocks from outgoing OpenAI-compatible requests without changing stored session history. | `passed` | It affects request construction only and does not establish provider support for reasoning or thinking fields. |
| `message-export-actions` | Available | `optional` | application | Optional application actions for exporting messages or sessions as Markdown, PDF, EPUB/Kindle-compatible files, and generated session assets. | `incomplete` | Not selected by default; no generic terminal action execution; conversion/browser/pandoc/SMTP/Keychain/native-share workflows not completed. |
| `openrouter_responses` | Available | `optional` | extensions, providers | Plugin bundle containing an OpenRouter provider that targets the `/responses` endpoint, plus `/responses`-compatible extensions. | `unknown` |  |
| `shell-tool-settings` | Available | `optional` | features | Optional session setting that selects the Codex shell-tool surface used for later requests. | `passed` | The plugin exposes configuration only; codex-tools owns the actual command implementations. |
| `sleep-prevention-app` | Available | `optional` | application | Application plugin that exposes a live server setting for keeping the local server process awake. | `passed` | Not selected by default; no real OS hold or native client workflow run. |

### Distribution-specific plugins

| Plugin | Status | Lifecycle | Kinds | Description | Verification | Limitations |
|---|---|---|---|---|---|---|
| `embedded-claude-tools` | Conditional | `distribution_specific` | tools | Claude-like, iOS-safe workspace tools for the embedded Crystal Lattice runtime. | `unknown` |  |
| `embedded-codex-tools` | Conditional | `distribution_specific` | tools | Codex-like, iOS-safe command tools for the embedded Crystal Lattice runtime. | `unknown` |  |
| `embedded-workspace-settings` | Conditional | `distribution_specific` | application, features | Embedded-runtime workspace selection and containment-aware per-session working-directory controls. | `passed` | Applies to the embedded mobile runtime; it does not provide arbitrary filesystem paths, directory creation, or iOS Files/iCloud access. |

### Developer examples, templates, support, and fixtures

| Plugin | Status | Lifecycle | Kinds | Description | Verification | Limitations |
|---|---|---|---|---|---|---|
| `bash-read-line-range` | Developer/internal | `example` | tools | A minimal bash tool plugin that reads a line range from a file using `sed`, with optional line numbers via `nl`. | `unknown` |  |
| `dummy-action-display-app` | Developer/internal | `development_fixture` | application | Non-production demonstration plugin for direct banner, inline, and modal action responses. It is intentionally absent from the default runtime configuration. | `unknown` |  |
| `dummy-action-display-form-app` | Developer/internal | `development_fixture` | application | Demo application plugin for manually testing generic action display embedded forms. | `unknown` |  |
| `dummy-application-notification-app` | Developer/internal | `development_fixture` | application | Non-production demonstration plugin for creating, updating, and resolving owner-memory application notifications. It is intentionally absent from the default runtime configuration. | `unknown` |  |
| `dummy-mcp-auth-server` | Developer/internal | `development_fixture` |  | Local streamable HTTP MCP server for manually testing MCP OAuth login from Crystal Lattice. | `unknown` |  |
| `dummy-mcp-output-server` | Developer/internal | `development_fixture` |  | Local MCP server for investigating and testing large MCP tool outputs. | `unknown` |  |
| `dummy-rich-config-ui` | Developer/internal | `development_fixture` | feature | Opt-in feature plugin for manually and automatically testing portable rich configuration controls on mobile and desktop. | `unknown` |  |
| `dummy-session-notification-app` | Developer/internal | `development_fixture` | application | Non-production demonstration plugin for persistent session notifications and follow-up actions. It is enabled only by examples and integration tests. | `unknown` |  |
| `dummy-settings-app` | Developer/internal | `development_fixture` | application | Demo application plugin for manually testing server-scoped settings. | `unknown` |  |
| `embedded-tools-shared` | Developer/internal | `support_library` |  | Pure-Python engines shared by the embedded Claude-like and Codex-like tool plugins. | `unknown` |  |
| `generic-callback-app` | Developer/internal | `development_fixture` | application | Demo application plugin for testing generic external callback deep links. | `unknown` |  |
| `js-class-tool` | Developer/internal | `example` | tools | Example tool plugin implemented as a **TypeScript class** (instead of exporting a plain object). | `unknown` |  |
| `js-echo-tool` | Developer/internal | `example` | tools | Example JavaScript/TypeScript tool plugin for the Crystal Lattice. | `unknown` |  |
| `js-fs-tools` | Developer/internal | `example` | tools | Example filesystem tools implemented in Node.js/TypeScript. | `unknown` |  |
| `js-multi-tools` | Developer/internal | `example` | tools | Example multi-tool Node.js/TypeScript package. | `unknown` |  |
| `js-single-file-tool` | Developer/internal | `example` |  | Single-file TypeScript tool example. | `unknown` |  |
| `mcp-shared` | Developer/internal | `support_library` |  | Internal helper package for MCP-backed tool wrappers. | `unknown` |  |
| `skill-shared` | Developer/internal | `support_library` |  | Shared discovery and parsing helpers for vendor-owned skill integrations. | `unknown` |  |
| `template-bash-tool` | Developer/internal | `template` | tools | Template plugin repo for **bash tool plugins**. | `unknown` |  |
| `template-js-multi-tools` | Developer/internal | `template` | tools | Template plugin repo for **Node.js / TypeScript tool plugins**. | `unknown` |  |
| `template-python-provider` | Developer/internal | `template` | extensions, features, providers | Template plugin repo for **Python provider plugins** (provider + provider extension + feature). | `unknown` |  |
| `template-python-tools` | Developer/internal | `template` | tools | Template plugin repo for **Python tool plugins**. | `unknown` |  |
| `tool-compat-shared` | Developer/internal | `support_library` |  | Internal helper package for the vendor-style tool bundles. | `unknown` |  |
| `web-fetch-shared` | Developer/internal | `support_library` |  | Shared HTTP fetch and HTML extraction helpers for vendor web fetch tools. | `unknown` |  |

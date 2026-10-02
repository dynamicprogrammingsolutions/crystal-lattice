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

Selected provider-native capabilities that materially change the user experience. General streaming and ordinary tool calling are omitted.

| Provider | Reasoning | Prompt cache | Native web | Native compact | Processing tiers | Files and media |
|---|---|---|---|---|---|---|
| OpenAI API<br><small>API key</small> | Yes | Yes | Yes | Yes | Fast + Flex | Images + PDF |
| ChatGPT account<br><small>Saved account login</small> | Yes | Session key | Yes | Yes | Fast only | Images; PDF varies |
| OpenRouter<br><small>API key</small> | By model | Anthropic routes | Yes | No | No | Images by model |
| Anthropic<br><small>API key</small> | Yes | Yes | Planned | Planned | Fast planned | Images/PDF planned |
| Ollama<br><small>Local endpoint; model access varies</small> | By model/server | No | No | No | No | Images by model |
| Fireworks<br><small>API key</small> | By model | No | No | No | No | Images by model |
| Z.ai<br><small>API key; Coding or General endpoint</small> | By model | No | No | No | No | Images by model |
| Other OpenAI-compatible<br><small>Endpoint-specific</small> | By endpoint | No | No | No | No | Images by endpoint |
| OpenRouter image generation<br><small>API key</small> | — | — | — | — | — | Image input + output |

## Model-family tool bundles

Crystal Lattice compatibility tool bundles. These are independent implementations, not the official upstream applications.

### Codex-oriented

| Tool | Status | Description |
|---|---|---|
| Shell | Available | Run commands using the model-appropriate array or shell-command schema. |
| Apply patch | Available | Apply structured multi-file patches with Codex-compatible patch syntax. |
| View image | Available | Load a local image into model-visible input. |
| MCP tools | Optional | Discover and call configured MCP-server tools. |
| Skills | Available | Discover configured skills and expose their instructions to the agent. |
| Update plan | Planned | Maintain a structured pending, active, and completed task plan. |
| Exec command | Planned | Start an interactive or long-running command with a persistent process handle. |
| Write stdin | Planned | Send input to a command started through Exec command. |
| Request user input | Planned | Ask a non-blocking question and continue from the user's follow-up answer. |
| Spawn subagent | Planned | Start a configured agent in a persistent child session. |
| Wait for subagent | Planned | Wait for one or more child-agent runs to make progress or finish. |
| Send subagent input | Planned | Continue an existing child session with persistent follow-up input. |
| List subagents | Planned | List persistent child sessions and their current status. |
| Close subagent | Planned | Close or cancel a persistent child-agent run. |

### Claude-compatible

| Tool | Status | Description |
|---|---|---|
| Bash | Available | Run foreground or background shell commands with persistent working-directory behavior. |
| Read | Available | Read text, images, PDFs, and supported notebook content. |
| Write | Available | Create or replace files with read-before-write protection. |
| Edit | Available | Perform exact text replacements with read-before-edit protection. |
| Glob | Available | Find files by path pattern. |
| Grep | Available | Search file contents with multiple result modes. |
| Web fetch | Available | Fetch and analyze a specific URL. |
| Web search | Conditional | Search through configured Gemini or Tavily backends. |
| Task stop | Available | Stop a background Bash task. |
| MCP tools | Optional | Discover and call configured MCP-server tools with Claude-style names and results. |
| Compact conversation | Available | Summarize and rewrite selected history using the Claude-compatible compaction flow. |

### Gemini-style

| Tool | Status | Description |
|---|---|---|
| Read file | Available | Read text or supported media content from a file. |
| List directory | Available | List directory entries. |
| Grep search | Available | Search file contents. |
| Glob | Available | Find files by path pattern. |
| Write file | Available | Create or replace file content. |
| Replace | Available | Replace exact text in a file. |
| Run shell command | Available | Run a shell command with bounded output. |
| Web fetch | Available | Fetch content from a specific URL. |
| Google web search | Conditional | Search through a configured Gemini or Tavily backend. |
| Write todos | Planned | Replace the Gemini-style task list and track task status. |
| MCP tools | Planned | Expose configured MCP-server tools with Gemini-compatible naming and results. |
| Activate skill | Planned | Load one selected skill and return its instructions and supporting files. |
| Specialist-agent tools | Planned | Expose configured specialist agents as separate blocking tools backed by persistent child sessions. |

### Qwen-style

| Tool | Status | Description |
|---|---|---|
| Read file | Available | Read file content with bounded output. |
| List directory | Available | List directory entries. |
| Grep search | Available | Search file contents. |
| Glob | Available | Find files by path pattern. |
| Write file | Available | Create or replace file content. |
| Edit | Available | Apply exact file edits. |
| Bash | Available | Run shell commands with bounded output. |
| Web fetch | Available | Fetch content from a specific URL. |
| Web search | Planned | Search through Dashscope, Tavily, or Google backends. |
| Todo write | Planned | Replace a Qwen-style todo list with stable item IDs. |
| Skills | Planned | Discover and load a selected skill through a Qwen-compatible tool. |
| Compaction | Planned | Compact conversation history and preserve Qwen-style checkpoint replay. |

### Grok-style

| Tool | Status | Description |
|---|---|---|
| View file | Available | Read file content. |
| Create file | Available | Create a new file. |
| String-replace editor | Available | Edit file content through exact string replacement. |
| Bash | Available | Run shell commands. |
| Create todo list | Planned | Replace a prioritized Grok-style todo list. |
| Update todo list | Planned | Patch individual todo items by ID. |
| Unified search | Planned | Search file names and content through one Grok-style interface. |

### Kimi-style

| Tool | Status | Description |
|---|---|---|
| Read file | Available | Read text content with line-numbered output. |
| Read media file | Conditional | Read image or supported media content for a capable model. |
| Write file | Available | Create, replace, or append file content. |
| String-replace file | Available | Apply one or more exact text replacements. |
| Glob | Available | Find files by path pattern. |
| Grep | Available | Search file contents. |
| Shell | Available | Run shell commands with a clean-environment option. |
| Fetch URL | Available | Fetch content from a specific URL. |
| Search web | Conditional | Search through a configured web-search backend. |
| Compact conversation | Available | Compact earlier history while preserving a recent message tail. |
| Set todo list | Planned | Replace a Kimi-style task list with pending, active, and done states. |
| MCP tools | Planned | Expose configured MCP-server tools with Kimi-compatible names and results. |
| Skills | Planned | Discover configured skills and make their instructions readable to Kimi tools. |
| Task | Planned | Run a blocking task in a persisted child-agent session and return its final answer. |

# Website Compatibility Data

Review state: `accepted`
Maturity: `draft`

Compatibility profiles and tool bundles are Crystal Lattice implementations, not official upstream applications or sessions.

Downstream website work may refine selection, wording, grouping, and presentation while preserving accepted compatibility boundaries and source traceability.

## Product features

Current application and session capabilities that are not repeated in the provider or model-family tool tables.

| Feature | Status | Description |
|---|---|---|
| Session organization | Available | Search and filter sessions, edit titles, pin important work, archive sessions, assign workflow status, and keep useful ordering. |
| Session actions | Available | Copy, fork, and delete sessions through application-owned actions. |
| Generated titles | Conditional | Generate a session title and description with a configured model. |
| Range summaries | Conditional | Summarize a selected range of conversation history without replacing provider-native compaction. |
| Snapshots and recovery | Available | Create and restore recovery points around destructive history changes and compaction workflows. |
| File and URL context | Conditional | Insert local file content or fetched web-page context through composer markers. |
| Configuration and prompt control | Available | Inspect and adjust provider options, system messages, session settings, and plugin-contributed controls. |
| Usage, cost, and timing | Conditional | Show provider usage, locally estimated or provider-reported cost, timestamps, and optional duration information when available. |
| Message and session export | Optional | Export selected content as Markdown, PDF, or EPUB/Kindle-compatible files. |

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

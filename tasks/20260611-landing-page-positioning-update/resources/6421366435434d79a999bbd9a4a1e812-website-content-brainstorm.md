# fbf52334-fcd5-4494-8e25-ed69e4c5698d - Website content brainstorm

## User message 1

I would like to create a webpage for this software. Help me brainstorm about the value proposition. Basically we need to determine some of the unique selling point we can advertise.
Here are few similar projects:
https://pi.dev
https://opencode.ai
https://openclaw.ai

Also most popular ones are codex and claude code if we look at coding agents.

Please look into thos projects and also look into ours and see what unique features are in this project that makes it unique over others. Give me ideas first. Do not just look at the readme, look into the code and structure as well.


## Assistant message 2

I’ll do a proper product-discovery pass: first inspect this repo’s shape and docs/code paths, then look up the comparison projects so we’re not guessing from memory. I’ll keep this at ideas/positioning only for now, no webpage implementation.


## Assistant message 6

The comparison set is already giving a useful contour: Pi is selling “minimal, hackable harness”; OpenCode is selling “open-source coding agent everywhere, with LSP/multi-session/model choice”; OpenClaw is selling “personal AI assistant reachable from chat apps, proactive and always-on.” I’m now looking through your actual modules/plugins to find the sharp edges that are yours, not just brochure overlap.


## Assistant message 30

There’s one detail worth noting from the competitor pass: Pi’s current homepage is very strong and quite close to what you’re asking for, so the positioning cannot just be “extensible terminal coding agent.” Your project seems much more like a local-first agent operating system with mobile/desktop clients, bridge, cloud runtime handoff, and UI-aware plugins.


## Assistant message 95

I looked through the comparison projects and then dug through this repo’s structure, server routes, frontend SDK, plugins, bridge, and cloud orchestrator. My strongest read: **Crystal Lattice should not be positioned as “another terminal coding agent.”** That lane is crowded by Codex, Claude Code, OpenCode, and Pi. Your sharper lane is:

**Crystal Lattice is a local-first agent control plane: run coding agents locally, control them from terminal, desktop, or phone, extend them with UI-aware plugins, and hand sessions off to cloud runtimes when needed.**

**Competitive Shape**
Pi is selling a minimal, hackable terminal coding harness with model switching, tree history, context engineering, skills, steering, modes, and TypeScript extensions. OpenCode is selling a polished open-source coding agent across terminal, desktop, IDE, with LSP, multi-session, share links, and many providers. OpenClaw is selling a personal AI assistant that acts through chat apps and handles day-to-day tasks. Claude Code and Codex are selling first-party coding-agent excellence, tight model integration, and broad official surfaces.

So I would avoid leading with “open-source coding agent,” “any model,” or “extensible terminal agent.” Those are valuable, but they are not the most differentiated.

**Best USP Candidates**

1. **Your Agent, Reachable From Anywhere**
The repo has a real local server plus terminal, mobile, desktop, direct IP, Bonjour/mDNS, and bridge transports. That is unusual. The product can say: “Start an agent on your workstation, then monitor and steer it from your phone, desktop, or terminal.” Evidence: local terminal/server/mobile stack in [README.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/README.md:3), mobile connection methods in [mobile README](/Users/ferenci84/Dev/Mine/ai-agent-platform/mobile/crystal-lattice-control-rn/README.md:5), bridge architecture in [bridge-elixir/README.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/bridge-elixir/README.md:7).

2. **A Control Plane, Not Just A CLI**
The HTTP API exposes sessions, messages, config, plugins, actions, UI schema, snapshots, and events. The frontend SDK has `FetchTransport`, `BridgeTransport`, and `CloudTransport`. This lets you build actual products around agent sessions, not just wrap a terminal. Positioning line: “The missing backend and frontend SDK for agent apps.” Evidence: server UI schema endpoints in [server.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/application/python/agent_terminal_app/server.py:1189), frontend cloud transport in [cloudTransport.ts](/Users/ferenci84/Dev/Mine/ai-agent-platform/packages/frontend-sdk/src/transport/cloudTransport.ts:9), bridge transport in [bridgeTransport.ts](/Users/ferenci84/Dev/Mine/ai-agent-platform/packages/frontend-sdk/src/transport/bridgeTransport.ts:38).

3. **UI-Aware Plugins**
This is a genuinely interesting differentiator. Plugins do not only add tools or provider behavior; they can contribute config controls, status bars, message footers, session actions, message actions, and app-level UI effects. That means a plugin can ship behavior plus its own cross-platform interface. Positioning line: “Plugins that change the agent and the app around it.” Evidence: application plugin capabilities in [application-plugins.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/docs/application-plugins.md:18), UI element system in [ui-elements.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/docs/ui-elements.md:50).

4. **Local To Cloud Session Handoff**
This is probably your boldest “enterprise/developer power user” differentiator. The cloud orchestrator can start cloud runtimes, transfer workspace/session state, proxy requests, and sync changes back down. That is much more than “remote execution.” Positioning line: “Start local. Burst to cloud. Sync back safely.” Evidence: orchestrator lifecycle and runtime transfer in [cloud-orchestrator/README.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/cloud-orchestrator/README.md:3), cloud connection link and sync flow in [cloud-orchestrator/README.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/cloud-orchestrator/README.md:50).

5. **Provider-Agnostic Codex-Style Workflows**
The `codex-tools` plugin gives Codex-compatible shell, shell_command, apply_patch, view_image, MCP tools, and skill behavior, while the default config includes OpenAI, OpenRouter, Qwen, Gemini, Grok, Kimi, Claude, Ollama, Fireworks, Z.ai, and image generation paths. This suggests a good claim: “Codex-like tool semantics across models and providers.” Evidence: [codex-tools README](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/codex-tools/README.md:1), default agents in [config.json](/Users/ferenci84/Dev/Mine/ai-agent-platform/application/python/agent_terminal_app/default_config/config.json:620).

6. **Session Workbench**
Snapshots, read-only snapshot selection, restore, session forking/copying/deleting, pinned sessions, titles, message counts, ordering buckets, attachments, and summarize/export actions make this feel like a workbench for long-running agent work. Positioning line: “Treat agent conversations as durable work artifacts.” Evidence: snapshot API in [server.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/application/python/agent_terminal_app/server.py:2461), snapshot logic in [application_future.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_app/application_future.py:2351).

7. **Polyglot Tool Plugin System**
Python plugins are expected, but Node and Bash tool plugins are also supported. That gives a practical “bring your existing scripts/packages” story. Positioning line: “Turn Python packages, npm packages, or shell scripts into agent capabilities.” Evidence: [node-tool-plugins.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/docs/node-tool-plugins.md:3), [bash-tool-plugins.md](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/docs/bash-tool-plugins.md:3).

**Homepage Angles I’d Test**

**Angle A: The Agent Control Plane**
Headline: “Run coding agents from your workstation. Control them from anywhere.”
Subhead: “Crystal Lattice gives local agents a server, mobile and desktop clients, plugin-powered UI, bridge pairing, and cloud handoff.”

This is my favorite. It is clearest and most differentiated.

**Angle B: The Open Framework For Agent Apps**
Headline: “Build agent apps, not just agent prompts.”
Subhead: “A modular Python agent core, FastAPI application layer, React Native clients, and UI-aware plugins for sessions, tools, providers, and workflows.”

This is better for developers building on the platform.

**Angle C: Local-First, Cloud-Ready Coding Agents**
Headline: “Keep the agent near your code. Move the work when you need to.”
Subhead: “Run locally for privacy and control, connect securely from mobile, then launch cloud runtimes and sync results back.”

This is strongest if cloud orchestration is ready enough to advertise.

**What I Would Put Above The Fold**

“Crystal Lattice is a local-first control plane for coding agents.”

Then three proof points:

- “Terminal, HTTP, desktop, and mobile clients over the same session store.”
- “Bridge pairing lets your phone reach your workstation without exposing a raw local server.”
- “Plugins can add tools, providers, lifecycle actions, settings, status UI, and session actions.”

**What To Be Careful With**

Do not over-index on “any model.” OpenCode and Pi both say that well already. Do not lead with “terminal agent,” because that makes you look smaller than Codex/Claude/OpenCode/Pi. Also be cautious with cloud claims if the UX is still developer-heavy; it is a huge differentiator, but only homepage-ready if the happy path is reliable.

Sources used for competitor positioning: [Pi](https://pi.dev/), [OpenCode](https://opencode.ai/), [OpenCode docs](https://opencode.ai/docs/), [OpenClaw](https://openclaw.ai/), [Claude Code overview](https://docs.anthropic.com/en/docs/claude-code/overview), [OpenAI Codex docs](https://developers.openai.com/codex/).


## User message 96

The strongest USP candidates are in my opinion:
- agent reachable from anywhere. Our terminal applicatipn is quite minimal and unpolished. The strongest point is other UIs.
- The plugin system: it's very flexible, it's not always possible to switch providers in-session, but the system allows to develop plugins at the lowest-level provider support: it stores provider-native messages that makes a better base for native feature support. And yes, it's possible to add provider-native features directly to UI.
- you noticed that we developed codex-like tool semantics, but we also developed several others: gemini, kimi, qwen, grok, claude. All of them has the specific system message, tool schema, etc that those model families are optimized to. This is where we make customization seriously. We don't assume that a standard tool set and a standard system prompt will serve all models well. These default agents with plugin packages are done in a way that models do not even notice they are working outside the harness they are optimized to.

Several other things you mentioned are appropriate as feature blocks:
- "Session Workbench" all these operations are plugin driven.
- Polyglot plugin system
- A strong feature is that every part of the system can be replaced. The UI is fully driven by plugins, providers are also plugins. The user don't need to submit pull request and have it approved to change something. They can just change the plugin and use that plugin in the config.
- The core: The plugin system makes the harness available as an SDK (this is the python SDK) as a high level access to rich capabilities. This part could show a code sample, for example a bulk API.


## Assistant message 97

Yes, this sharpens the story a lot. I’d frame Crystal Lattice less as “a better coding agent” and more as:

**Crystal Lattice is a model-native, plugin-driven agent platform for building your own agent surfaces.**

Or, more product-y:

**The agent platform for people who want control over the harness, not just the prompt.**

The three strongest pillars now feel like these:

**1. Reach Your Agent From Any Interface**
This is the user-facing hook. The terminal is not the hero; the terminal is one surface among others.

Possible copy:
> Start an agent on your machine and control it from the interfaces that fit your day: desktop, mobile, HTTP, or terminal. Crystal Lattice turns a local agent runtime into a reachable, multi-client workspace.

Feature ideas underneath:
- Local FastAPI server as the stable runtime
- React Native mobile client
- React Native macOS desktop client
- Direct LAN, Bonjour/mDNS, and bridge pairing
- Same sessions, messages, plugins, and streamed events across clients

This differentiates from terminal-first tools because the runtime is not trapped inside the TUI.

**2. Model-Native Agents, Not One Prompt For Everything**
This is probably the most technically distinct USP. You’re not just routing requests to different providers; you’re tailoring the harness to model families.

Possible copy:
> Different models are trained inside different harnesses. Crystal Lattice treats that as a first-class design constraint. Codex, Claude, Gemini, Qwen, Kimi, Grok, and other agents can each get their own system message, tool schemas, tool semantics, provider features, and UI controls.

Another sharper version:
> Don’t make every model pretend it is the same agent.

Feature ideas underneath:
- Codex-style tools and system behavior for Codex/GPT families
- Gemini/Kimi/Qwen/Grok/Claude-specific tool packages and system messages
- Provider-native message storage for better native feature support
- Provider-native features can surface directly into the UI
- Model-family-specific defaults instead of lowest-common-denominator abstractions

This is the place to explain the “models do not even notice they are outside their native harness” idea. That sentence is strong, but I’d polish it:

> The goal is for each model family to feel like it is still inside the harness it was optimized for.

**3. Replace The Harness Without Forking The Product**
This is the hacker/developer/business moat. The platform is configurable at every layer.

Possible copy:
> In most agent tools, changing the harness means waiting for upstream. In Crystal Lattice, providers, tools, features, UI actions, session behavior, and application workflows are plugins. Replace the part you disagree with, point config at your plugin, and keep moving.

Feature ideas underneath:
- Providers are plugins
- Tools are plugins
- Features and provider extensions are plugins
- Application/session actions are plugins
- UI schema is plugin-driven
- Config can load local, git, Python, Node, and Bash plugin packages
- No pull request required to customize local behavior

This is a very good “so what?”:
> Your workflow does not need to be accepted upstream to exist.

**Feature Blocks**
These fit nicely below the core pillars:

**Session Workbench**
> Agent conversations are working state, not disposable chat logs.

Bullets:
- Plugin-driven session actions
- Fork, copy, delete, summarize, title, pin, order, and export sessions
- Message-level actions
- Snapshots and restore
- Attachments and generated assets
- Mobile/desktop UI can expose these actions automatically from plugin metadata

**Polyglot Plugin Runtime**
> Write extensions in the language that fits the job.

Bullets:
- Python plugins for deep provider/app behavior
- Node tools for npm ecosystem integration
- Bash tools for shell-native workflows
- Local path and git-loaded plugin packages
- Plugin cache and install policy controls

**Python SDK / Agent Core**
This is where the code sample belongs. The pitch is not “we have an SDK” but:

> The same rich harness used by the app is available as a Python SDK.

A homepage code sample could show bulk processing or scripted session orchestration:

```python
from agent_app import AgentApplication

app = AgentApplication.from_config("./.crystal/config.json")

for task in tasks:
    session = app.create_session(agent_id="codex-openrouter")
    session = app.add_message(session.session_id, "user", task)

    for event in app.send_request(session.session_id, stream=True):
        if event["type"] == "final":
            print(event["message"]["content"])
```

Or more product-specific:

```python
app = AgentApplication.from_config("./.crystal/config.json")

for path in changed_files:
    session = app.create_session(agent_id="qwen")
    app.add_message(
        session.session_id,
        "user",
        f"Review this file and suggest a minimal patch: {path}",
    )
    app.send_request(session.session_id)
```

The exact API names may need adjustment, but the idea is right: show that the platform is scriptable, not only interactive.

**Potential Homepage Narrative**
I’d structure the page like this:

1. Hero:
   > **Model-native agents, reachable from anywhere.**
   >
   > Crystal Lattice is a plugin-driven agent platform for running local coding agents through desktop, mobile, HTTP, and terminal interfaces, with model-specific harnesses for Codex, Claude, Gemini, Qwen, Kimi, Grok, and more.

2. First section: “Your agent is not trapped in a terminal”
   Show desktop/mobile/server connection story.

3. Second section: “Each model gets the harness it expects”
   Explain model-family customization, native messages, provider features, tool schemas.

4. Third section: “Everything is replaceable”
   Explain plugins across providers/tools/features/UI/actions.

5. Fourth section: “A workbench for long-running agent work”
   Sessions, snapshots, actions, attachments.

6. Fifth section: “Use it as an SDK”
   Code sample for bulk/headless workflows.

7. Closing CTA:
   Install CLI, run server, connect client, or build a plugin.

**Some Tagline Options**
- “Model-native agents, reachable from anywhere.”
- “An agent platform where the harness is yours.”
- “Build agent workflows without waiting for upstream.”
- “One runtime. Many interfaces. Native harnesses for every model family.”
- “The local-first control plane for customizable coding agents.”
- “Stop forcing every model through the same prompt.”

My favorite combo:

Headline:
> **Model-native agents, reachable from anywhere.**

Subhead:
> Crystal Lattice is a local-first, plugin-driven agent platform. Run agents on your machine, control them from desktop or mobile, and customize the provider, tools, system messages, UI, and session workflow for each model family.


## User message 98

I like fhese sections. I would like you to elaborate. Also I am thinking that each section could have an simple action, like if the marketing page was a documentation: installing a CLI and start in server mode, installing the mobile application (link to appstore/google play) and connecting via bonjour discovery (local network). Deploying a bridge via aws (bridge service coming soon), and connecting over the bridge. Plugin section could show a simple prompt that is a starting conversation to develop a plugin, askikng the agent to find the documentation and plan the plugin. This is an idea and possible direction.


## Assistant message 99

Yes. I really like this direction: **a marketing page that behaves like executable documentation**.

That fits Crystal Lattice unusually well because the product is not just a static value prop. Its value appears when someone realizes: “Oh, this is a runtime I can connect to, replace, script, and extend.” So each section can pair a claim with a small concrete action.

The page should feel less like “trust us” and more like:

> Here is the capability. Here is the command or flow that proves it.

**Page Thesis**
A strong organizing sentence:

> Crystal Lattice is a local-first agent platform: run model-native agents on your machine, reach them from any interface, and replace every layer of the harness with plugins.

That gives us four big ideas:

1. Reachable from anywhere
2. Model-native harnesses
3. Everything is replaceable
4. Programmable SDK / workbench

Then each section can have a “Try this” strip.

**Hero**
Headline:

> **Model-native agents, reachable from anywhere.**

Subhead:

> Crystal Lattice runs agent sessions locally, exposes them through HTTP, desktop, mobile, and terminal clients, and lets every model family use the harness it was optimized for: system messages, tool schemas, provider-native features, and UI actions included.

Primary CTA:
`Install CLI`

Secondary CTA:
`View Plugin Docs` or `Run Mobile Client`

Hero action block:

```bash
curl -fsSL https://.../install.sh | bash

mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo

crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000
```

Small caption:

> Starts the local runtime, HTTP API, and terminal client. Other clients can connect to the same sessions.

This immediately proves that the “runtime” is real.

**Section 1: Your Agent Is Not Trapped In A Terminal**
Core message:

> Terminal agents are powerful, but the terminal should not be the only control surface. Crystal Lattice runs the agent as a local service, so desktop, mobile, scripts, and future UIs can all talk to the same session store.

Supporting bullets:
- Start once, connect from multiple clients
- Mobile and desktop clients use the same backend API
- Sessions, streamed events, settings, plugins, and actions are exposed over HTTP
- Direct LAN, Bonjour/mDNS, and bridge transports support different network shapes

Action block title:

> Connect from your phone on the local network

Steps:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

Then UI steps:

```text
Open Crystal Lattice Control
Choose Automatic Discovery
Select your computer
Open a session
Send a message
```

For App Store / Google Play:

Use buttons, but if not available yet:

- `Download for iOS` with “Coming soon”
- `Download for Android` with “Coming soon”
- `Run from source` as the active link

This avoids pretending distribution is finished.

Possible visual:
A simple diagram:

```text
Mac / Linux Runtime
  ├─ Terminal
  ├─ Desktop App
  ├─ Mobile App
  └─ HTTP / SDK
```

**Section 2: Local First, Bridge Ready**
This should be separate from local mobile connection. It explains the next network step.

Core message:

> Local-first should not mean desk-bound. The bridge lets a phone or remote client pair with a local Crystal Lattice server through a relay without exposing the server directly to the internet.

Supporting bullets:
- Server registers with the bridge
- App discovers available servers
- Pairing uses short-lived codes
- Requests proxy over WebSockets
- Same frontend backend interface after pairing

Since you said “bridge service coming soon,” I’d frame it as:

> Bridge service is available for self-hosted/developer deployments. Hosted bridge coming soon.

Action block title:

> Self-host the bridge

Local/dev version:

```bash
cd bridge-elixir
docker compose up -d

crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url ws://localhost:4000/ws/websocket
```

AWS coming-soon/deployment preview:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --stack-name crystal-lattice-bridge \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

Then:

```text
Open Crystal Lattice Control
Choose Bridge Service
Enter the bridge URL
Select your server
Enter the pairing code
```

Marketing copy:

> The bridge does not replace local-first. It extends it.

**Section 3: Each Model Gets The Harness It Expects**
This is the differentiator that deserves careful explanation.

Core message:

> Most multi-model agents treat providers as interchangeable text endpoints. Crystal Lattice does not. Each model family can have its own provider plugin, tool schema, system message, reasoning support, message conversion, and UI controls.

Supporting bullets:
- Codex-style tools and apply-patch semantics for Codex/GPT agents
- Gemini, Claude, Qwen, Kimi, Grok, and others can ship their own optimized tool packages
- Provider-native messages can be retained across turns
- Native provider features can surface directly in the UI
- Defaults are model-family-aware, not lowest-common-denominator

This phrase is excellent and should appear:

> The goal is for the model not to notice it is outside the harness it was optimized for.

Action block title:

> Start with a model-native default agent

Maybe:

```json
{
  "agents": {
    "codex-openrouter": {
      "provider": "openrouter",
      "model": "openai/gpt-5.4-mini",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/codex-tools"
      ]
    },
    "claude": {
      "provider": "openrouter",
      "model": "anthropic/claude-haiku-4.5",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/claude-tools"
      ]
    },
    "gemini": {
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/gemini-tools"
      ]
    }
  }
}
```

CTA:
`Browse Default Agents`

Visual idea:
A comparison table:

| Generic Agent | Crystal Lattice |
|---|---|
| One prompt | Model-family system messages |
| One tool schema | Model-native tool packages |
| Provider abstraction only | Provider-native history and features |
| UI hardcoded in app | UI contributed by plugins |

**Section 4: Everything Is Replaceable**
Core message:

> Crystal Lattice is built around plugins because serious users eventually disagree with the harness. You should not need a merged pull request to change how your agent works.

Supporting bullets:
- Providers are plugins
- Tools are plugins
- Model-family features are plugins
- Application actions are plugins
- Session workbench actions are plugins
- UI controls and menus are plugin-provided
- Local path, git, Python, Node, and Bash plugin options

Strong line:

> If your workflow is local, your customization can be local too.

Action block title:

> Ask the agent to plan a plugin

This is a really good idea. It makes the plugin section approachable.

Prompt block:

```text
I want to build a Crystal Lattice plugin.

Please inspect the plugin documentation in this repository, especially:
- plugins/docs/index.md
- plugins/docs/tool-plugins.md
- plugins/docs/application-plugins.md
- plugins/docs/ui-elements.md
- plugins/docs/plugin-packaging-and-loading.md

Goal:
Create a plugin that [describe what I want].

Please:
1. Identify which plugin type fits best.
2. Find the closest existing plugin to copy from.
3. Propose the file layout.
4. Draft an implementation plan.
5. Tell me what tests should be added before coding.
```

Then show a minimal config:

```json
{
  "plugins": [
    "path:./plugins/my-custom-plugin"
  ]
}
```

Section close:

> Change the harness by changing config.

**Section 5: Session Workbench**
This should feel like a practical product feature, not a core architecture claim.

Core message:

> Long-running agent work creates state: decisions, failed paths, generated files, summaries, forks, and checkpoints. Crystal Lattice treats sessions as durable work artifacts.

Supporting bullets:
- Pin, title, order, and organize sessions
- Fork from a message
- Delete or modify messages
- Summarize ranges
- Attach files and generated assets
- Create, view, restore, and delete snapshots
- Expose all of this through plugin-driven UI actions

Action block title:

> Snapshot before a risky turn

Could show API:

```bash
curl -X POST http://localhost:9000/sessions/$SESSION_ID/snapshots \
  -H "Content-Type: application/json" \
  -d '{"reason":"before dependency upgrade"}'
```

Then restore:

```bash
curl -X POST \
  http://localhost:9000/sessions/$SESSION_ID/snapshots/$SNAPSHOT_ID/restore
```

Or UI action:

```text
Open session menu
Create snapshot
Ask the agent to attempt the risky change
Restore if needed
```

This also reinforces that desktop/mobile are serious clients, not demos.

**Section 6: Use The Harness As An SDK**
Core message:

> The same system behind the app is available programmatically. Use Crystal Lattice as a Python SDK when you want bulk runs, internal tools, evaluations, repo workflows, or custom agent products.

Supporting bullets:
- Create sessions programmatically
- Select configured agents
- Stream events
- Reuse provider/tool/plugin configuration
- Run the same model-native harness outside the UI

Code sample idea:

```python
from agent_app import AgentApplication

app = AgentApplication.from_config("./.crystal/config.json")

reviews = [
    "Review the authentication flow.",
    "Find risky database migrations.",
    "Check whether the mobile client handles reconnects cleanly.",
]

for prompt in reviews:
    session = app.create_session(agent_id="codex-openrouter")
    app.add_message(session.session_id, "user", prompt)

    for event in app.send_request(session.session_id, stream=True):
        if event["type"] == "partial":
            print(event["content"], end="", flush=True)
        elif event["type"] == "final":
            print("\n--- done ---")
```

We should verify exact SDK API before putting final code on a real webpage, but as a marketing concept this section is right.

Alternative API block via HTTP, which is safer for a public page:

```bash
SESSION_ID="$(
  curl -s -X POST http://localhost:9000/sessions \
    -H "Content-Type: application/json" \
    -d '{"agent_id":"codex-openrouter"}' |
  jq -r '.session.session_id'
)"

curl -X POST "http://localhost:9000/sessions/$SESSION_ID/send_message" \
  -H "Content-Type: application/json" \
  -d '{"message":"Review this repository and identify the riskiest module."}'
```

**Section 7: Cloud Handoff**
This can be later in the page because it is advanced but powerful.

Core message:

> Some agent work belongs on your workstation. Some work should continue in a cloud runtime. Crystal Lattice is designed for both, with explicit transfer and sync profiles.

Supporting bullets:
- Start a cloud runtime from a local session
- Transfer workspace and session state
- Connect to cloud runtime from frontend clients
- Sync changes back down
- Customize transfer/install/validation hooks per project

Action block title:

> Validate a project for cloud runtime

```bash
crystal-lattice validate-cloud --workspace-dir .
```

Then advanced:

```text
Start Cloud Agent
Open returned crystal-lattice-cloud:// link
Continue from mobile or desktop
Sync down when complete
```

This should maybe be labeled:

> Advanced / coming soon for hosted deployments

Depending on how public-ready you want to be.

**Overall Page Flow**
I’d order it like this:

1. Hero: Model-native agents, reachable from anywhere
2. Install and start local runtime
3. Connect mobile/desktop on local network
4. Model-native harnesses
5. Everything is replaceable with plugins
6. Session workbench
7. SDK/API automation
8. Bridge and cloud handoff
9. Final CTA

Reason: lead with something a user can feel quickly, then deepen into architecture.

**A Nice Pattern For Every Section**
Each section can repeat a small structure:

- Claim: one sentence
- Why it matters: one short paragraph
- What makes it possible: 3-5 bullets
- Try it: command / prompt / UI flow
- Link: docs or source

That “Try it” pattern makes the page distinctive. It becomes a landing page for builders, not a vague product brochure.

**Best Final Positioning**
I’d use this as the core webpage copy direction:

> Crystal Lattice is for developers who want the power of modern coding agents without giving up control of the harness. Run agents locally, reach them from mobile or desktop, use model-native defaults for Codex, Claude, Gemini, Qwen, Kimi, Grok, and more, then replace any layer with plugins when your workflow needs something different.

That captures the magic without overclaiming.

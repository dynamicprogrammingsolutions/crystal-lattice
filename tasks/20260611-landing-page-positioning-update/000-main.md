# Landing Page Positioning Update

Refine the landing page so it better reflects Crystal Lattice's strongest current value proposition: start agent work on the user's computer, continue from phone or app UI, and customize the harness through plugins without making misleading claims.

## Task checklist

- [x] `tasks/20260611-landing-page-positioning-update/010-claim-safety-and-current-state-audit.md`
- [x] `tasks/20260611-landing-page-positioning-update/020-homepage-structure-and-copy.md`
- [ ] `tasks/20260611-landing-page-positioning-update/030-mobile-connectivity-and-store-links.md`
- [ ] `tasks/20260611-landing-page-positioning-update/040-plugin-control-and-sdk-action-blocks.md`
- [ ] `tasks/20260611-landing-page-positioning-update/050-implementation-and-verification.md`

## Context

The landing page worktree is checked out at:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
```

The Astro landing page is content-driven. Current key files:

- `landing_page/src/content/pages/home.yaml`
- `landing_page/src/content/pages/mobile.yaml`
- `landing_page/src/content/markdown/home-features.md`
- `landing_page/src/components/Nav.astro`
- `landing_page/src/components/Footer.astro`
- `landing_page/src/components/Quickstart.astro`
- `landing_page/src/components/mobile/Download.astro`

Current build was checked during planning:

```bash
yarn build
```

It passed before these task files were created.

## Product Direction

Avoid leading with jargon such as "HTTP client", "local-first", "Bonjour", "bridge", or "model-native" before explaining the idea in plain language.

Preferred high-level message:

```text
Own the harness.
Use the agent anywhere.
```

Expanded:

```text
Crystal Lattice is a plugin-driven platform for running AI agents your way:
from your computer, from your phone, and through custom tools, prompts,
settings, and model-family harnesses you can replace.
```

Important corrections from product discussion:

- HTTP is not a client. It is an API/transport used by apps, scripts, and SDKs.
- Desktop should not be described as a separate device. The desktop app is a UI on the user's own computer.
- Do not over-emphasize "local-first" as a standalone USP. Many agent harnesses also start locally. Combine it with "start on your computer, continue on your phone."
- The bridge should be described as a way to connect from outside the local network, not as "avoiding exposing a server."
- AWS bridge deployment is working, not a preview.
- Do not show localhost as the public bridge example.
- Mobile App Store and Google Play links should be "Coming soon" for now. "Run from source" can be a fallback.
- Avoid provider/model-family disambiguation in main marketing copy. Talk about model families and the harnesses they work best with.
- Explain model-family harnesses plainly: GPT-5.5 works well with Codex-style tools; Claude Opus works well with Claude Code-style behavior; Crystal Lattice provides simplified plugin-driven tool/prompt sets that make those model families feel familiar.
- The plugin system should become the main high-level principle: control with no compromises, serious users can replace the harness rather than waiting for upstream.
- Session workbench should be described as plugin-driven and probably appear before or alongside the plugin section.
- For session workbench, prefer screenshot/UI examples rather than HTTP snippets.
- For SDK/API, use actual simplified Python code. A useful real-world example is CSV processing that generates personalized first LinkedIn messages.

## Proposed Page Structure

This is an intermediate version, not the final website. Use this primary order:

1. Hero: "Own the harness. Use the agent anywhere."
2. Start and continue: install CLI, start Crystal Lattice on the user's computer, then open the same work from the phone on the local network.
3. Connect outside the local network: AWS bridge deployment and pairing flow.
4. Control with no compromises: config-driven options exposed by replaceable plugins.
5. Harnesses that fit each model family: Codex-like, Claude-like, Gemini/Qwen/Kimi/Grok-like tool and prompt packages.
6. Session workbench: sessions as durable workspaces, plugin-driven operations.
7. Build or replace a plugin: prompt for the agent to inspect docs and plan a plugin.
8. Automate the same harness with Python: CSV batch personalization example.
9. CTA: install CLI, mobile app coming soon, run from source fallback.

## Draft Hero Copy

```text
Own the harness.
Use the agent anywhere.

Crystal Lattice is a plugin-driven platform for running AI agents your way: from your computer, from your phone, and through custom tools, prompts, settings, and model-family harnesses you can replace.
```

Short supporting bullets:

```text
- One running agent workspace, multiple human interfaces.
- Mobile app links are coming soon; source builds are available today.
- Every serious workflow can replace the plugin that controls it.
```

## Draft Section Texts

### Start And Continue

```text
Install the CLI, choose a project folder, and start Crystal Lattice. The terminal UI can stay open, but the work is not trapped there. On the same Wi-Fi, the mobile app can find your computer automatically. Open Crystal Lattice Control, choose Automatic Discovery, select your computer, and continue the session from your phone.
```

Action:

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash

mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo

crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

Clarification:

```text
Automatic discovery uses the local network. If your phone is away from that network, use the bridge section below.
```

### Connect Outside The Local Network

```text
When your phone is not on the same network as your computer, deploy the bridge and pair through it. The bridge gives Crystal Lattice clients a way to reconnect from outside the local network.
```

AWS action:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

Then:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url wss://<your-cloudfront-domain>/ws/websocket
```

### Control With No Compromises

```text
Serious users eventually disagree with the defaults. Crystal Lattice is built so the defaults are not a wall. Request options, UI controls, tools, providers, and session actions can be supplied by plugins and selected in config.
```

Illustration target:

```text
Show a config snippet and screenshot for a plugin-exposed setting, such as temperature, from the user's HOME/.crystal config. Explain that the UI control exists because a plugin exposes it and can be replaced.
```

### Harnesses That Fit Each Model Family

```text
Different model families are optimized around different coding harnesses. GPT-5.5 works well with Codex-style tools. Claude Opus works well with Claude Code-style behavior. Gemini, Qwen, Kimi, and Grok each have their own expectations.

Crystal Lattice uses plugins to provide simplified tool sets, system messages, and request behavior that feel familiar to those models.
```

### Session Workbench

```text
Agent work is more than a chat transcript. Crystal Lattice treats sessions as durable workspaces: title them, pin them, summarize ranges, fork from a message, attach assets, restore snapshots, and add custom session actions.

These operations are plugin-driven, so the workbench can change with your workflow.
```

Visual target:

```text
Use a screenshot of the mobile or desktop session UI showing session actions, pinned/title state, snapshots, or settings. Avoid an API snippet in this section.
```

### Build Or Replace A Plugin

```text
Your workflow does not need to be accepted upstream to exist. Ask an agent to inspect the plugin docs, choose the right plugin type, and draft a plan.
```

Prompt:

```text
I want to build a Crystal Lattice plugin.

Please inspect the plugin documentation in this repository, especially:
- plugins/docs/index.md
- plugins/docs/tool-plugins.md
- plugins/docs/application-plugins.md
- plugins/docs/provider-plugins.md
- plugins/docs/provider-extensions.md
- plugins/docs/ui-elements.md
- plugins/docs/plugin-packaging-and-loading.md

Goal:
Create a plugin that [describe what I want].

Please:
1. Identify whether this should be a provider, provider extension, feature, tool, or application plugin.
2. Find the closest existing plugin to copy from.
3. Explain what UI, if any, the plugin should expose.
4. Propose the file layout.
5. Draft an implementation plan.
6. Tell me what tests should be added before coding.
```

### Automate With Python

```text
The app UI is not the only way to use the harness. Use Python for repeatable workflows, bulk jobs, internal tools, and evaluations.
```

Example target:

```text
Read a CSV of LinkedIn leads and generate a personalized first message for each person using a configured agent. Use actual simplified Python code after checking the current AgentApplication API.
```

# Homepage Structure And Copy

Rewrite the homepage content so the page leads with the human workflow and gradually introduces the plugin-driven architecture.

## Requirements checklist

- [x] Keep the hero centered on "Own the harness. Use the agent anywhere."
- [x] Replace generic provider-agnostic/open-source positioning with human-centered control and customization.
- [x] Rework the feature grid to introduce the key concepts in plain language.
- [x] Put session workbench before or near the plugin/control section so plugin-driven session operations are easy to understand.
- [x] Avoid saying desktop is a separate device; describe desktop as another UI on the user's computer.
- [x] Avoid saying HTTP is a client; if mentioned, call it an API/transport for apps/scripts.
- [x] Keep the result as an intermediate base, not a final exhaustive website.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`
Depends On: `tasks/20260611-landing-page-positioning-update/010-claim-safety-and-current-state-audit.md`

## Files To Change

- `landing_page/src/content/pages/home.yaml`
- `landing_page/src/content/markdown/home-features.md`
- Potentially `landing_page/src/components/Providers.astro` only if the strip needs a different label/layout.

## Proposed Homepage Structure

Use this primary order for the intermediate page:

1. Hero: Own the harness. Use the agent anywhere.
2. Start and continue: install CLI, start Crystal Lattice, then open the same work from the phone on the local network.
3. Connect outside the local network: AWS bridge and pairing flow.
4. Control with no compromises: settings and UI controls exposed by replaceable plugins.
5. Harnesses that fit each model family: simplified Codex/Claude/Gemini/Qwen/Kimi/Grok-style tools and instructions.
6. Session workbench: sessions as durable workspaces with plugin-driven actions.
7. Build or replace a plugin: prompt for planning plugin work.
8. Automate the same harness with Python: real-world CSV personalization example.
9. CTA: install CLI, mobile apps coming soon, run from source fallback.

## Draft Hero

Use this as the target tone:

```yaml
titleHtml: 'Own the harness.<br /><span class="highlight">Use the agent anywhere.</span>'
subtitle: >-
  Crystal Lattice is a plugin-driven platform for running AI agents your way:
  from your computer, from your phone, and through custom tools, prompts,
  settings, and model-family harnesses you can replace.
```

Badge options:

```text
Plugin-driven agent workspace
```

or:

```text
Your interfaces. Your harness. Your workflow.
```

Avoid:

```text
Open Source · Apache 2.0
```

unless licensing is reviewed and scoped correctly.

## Draft Feature Grid

Replace `home-features.md` with cards close to these:

### Start And Continue

```text
Install the CLI, choose a project folder, and start Crystal Lattice. The terminal UI can stay open, but the work is not trapped there. On the same Wi-Fi, the mobile app can find your computer automatically so you can continue the same session from your phone.
```

### Connect Outside The Local Network

```text
When your phone is not on the same network as your computer, deploy the bridge and pair through it. The bridge gives Crystal Lattice clients a way to reconnect from outside the local network.
```

### Control With No Compromises

```text
Serious users eventually disagree with the defaults. Crystal Lattice lets plugins expose settings, tools, request behavior, and session actions that you can replace in config.
```

### Familiar Harnesses For Each Model Family

```text
GPT-5.5 works well with Codex-style tools. Claude Opus works well with Claude Code-style behavior. Crystal Lattice uses plugins to provide simplified harnesses that feel familiar to different model families.
```

### Sessions Become Workspaces

```text
Agent work is more than a chat transcript. Title sessions, pin important work, summarize ranges, fork from a message, attach assets, and restore snapshots.
```

### Automate The Same Harness

```text
Use Python for repeatable workflows, bulk jobs, internal tools, and evaluations while keeping the same configured agents and plugins.
```

## Copy Notes

- Do not over-index on "local-first" as a standalone benefit.
- Do not claim the mobile app can do everything the terminal can do.
- Do not claim all provider switching is seamless.
- Do not frame desktop as a second device. If desktop is mentioned, say "desktop UI" or "app UI."
- Use "plugin-driven" only after showing what plugins change.

## Execution plan

Added during completion after maintainer approval.

1. Update `landing_page/src/content/pages/home.yaml`.
   - Keep the selected hero direction: "Own the harness. Use the agent anywhere."
   - Retitle the provider strip so it does not collapse providers and model-family harnesses into a single provider claim.
   - Rework quickstart around the first concrete workflow: start Crystal Lattice on the user's computer, then continue from the phone on the same Wi-Fi.
   - Lead phone setup with automatic discovery and keep manual IP as a fallback.
   - Update CTA copy to reinforce harness ownership and replaceable plugins.

2. Update `landing_page/src/content/markdown/home-features.md`.
   - Replace the generic six-card feature grid with a narrative grid in the agreed order:
     start and continue, connect beyond the local network, control with no compromises, harnesses for model families, sessions as workspaces, and automation.
   - Keep the wording plain and careful; avoid reintroducing the overclaims fixed in task `010`.
   - Use existing feature-grid icons and avoid new component work in this task.

3. Do not modify components unless current content cannot be represented with existing sections.
   - `Features.astro`, `Quickstart.astro`, `Providers.astro`, and `CTA.astro` should remain unchanged if possible.
   - Bridge deployment commands, plugin-planning prompt blocks, screenshots, and Python code samples belong to later subtasks.

4. Verify.
   - Run `yarn build` from `landing_page`.
   - Re-run the task `010` risky-phrase/link scan.
   - Update this task's checklist and completion notes.
   - Mark task `020` complete in `tasks/20260611-landing-page-positioning-update/000-main.md` after verification.

## Completion Notes

Added during completion.

Implemented the homepage structure and copy pass as an intermediate base using
the existing page sections.

Changed content:

- `landing_page/src/content/pages/home.yaml`
  - Kept the selected hero direction: "Own the harness. Use the agent anywhere."
  - Changed the provider strip from a generic provider list to "Built for" chips
    that include model-family harnesses and integrations.
  - Reworked quickstart around the concrete workflow: install the CLI, start
    Crystal Lattice in a project folder with local network discovery enabled,
    then connect from the phone.
  - Led phone connection with Automatic Discovery and left manual address as a
    fallback.
  - Updated the CTA to reinforce harness ownership and replaceable plugins.

- `landing_page/src/content/markdown/home-features.md`
  - Replaced the generic feature grid with the agreed narrative order:
    start and continue, bridge access beyond the local network, control with no
    compromises, model-family harnesses, sessions as workspaces, and automation.
  - Kept bridge and automation at a high-level copy layer; deployment commands,
    plugin prompts, screenshots, and Python code remain for later subtasks.

Verification:

- Re-ran the task `010` risky-phrase/link scan; no matches were found.
- Ran `yarn build` from `landing_page`; build passed.
- Build still reports an Astro duplicate-id warning for `home-features.md`.
  This warning existed before this task family and is outside this task's scope.

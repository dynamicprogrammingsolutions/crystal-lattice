# Homepage Positioning And Visual Decisions

This page preserves the homepage positioning, copy, download presentation, and
proof-visual decisions that are likely to be revisited. It records selected
directions alongside viable alternatives so later redesigns can reuse the
reasoning instead of reconstructing it from task history.

The maintained implementation plan is tracked under
`tasks/20260930-homepage-getting-started-and-waitlist/`. Public website copy
must not present target-only visuals or product improvements as available until
they are implemented and verified.

## Baseline Before Copy Revision

Commit `89883b92` (`Build homepage structure`) is the durable baseline before
the current copy and platform-download revisions.

Its feature titles were:

1. One workspace for every model family.
2. Replace the parts you disagree with.
3. See what the agent is actually using.
4. Start at your desk. Continue wherever you are.
5. Shape it around your workflow.
6. Sessions become durable workspaces.

Its platform presentation used one generic download-icon macOS control,
generic Desktop icons for unavailable platforms, and generic mobile-device
icons for iOS and Android. That implementation established structure but did
not match the selected logo-led download convention.

## Copy-Orientation Theory

### Statement-oriented titles

Statement-oriented titles name the capability or value directly.

Examples:

- One workspace for every model family.
- Everything is a plugin.
- Transparency by design.
- Work from anywhere.
- Sessions become workspaces.
- You are in control.

They are easy to scan, reduce dependence on body copy, and usually sound more
credible than abstract marketing language. Their risk is repetition: six
declarative headings can feel static.

### Action-oriented titles

Action-oriented titles emphasize what the reader can do.

Examples:

- Replace the parts you disagree with.
- See what the agent is actually using.
- Start at your desk. Continue wherever you are.
- Shape it around your workflow.
- Vibe code—or vibe anything.

They create momentum and make technical capabilities feel relevant. Their risk
is that the underlying value can become unclear when the title is read without
its body.

### Selected principle

Do not force all highlights into one grammatical style. Select the clearest
title for each value, then evaluate the rhythm of the complete grid.

The current mix intentionally combines direct value statements with
action-oriented user outcomes.

## Selected Feature Order And Copy

### 1. One workspace for every model family

Selected title:

> One workspace for every model family.

Selected body:

> Use Codex-, Claude-, Gemini-, Qwen-, Kimi-, and Grok-oriented profiles
> without switching between separate model-specific clients. Each profile
> keeps its model-family instructions, tools, and request behavior inside the
> same workspace.

Why selected:

- “Workspace” covers sessions, apps, tools, and configuration better than
  “app.”
- “Model family” avoids an unsupported claim about every possible model.
- The statement directly communicates the value.

Viable alternatives:

- One app for every model.
- Every model. One workspace.
- Stop switching between model-specific apps.
- Model-native agents, together in one workspace.

Planned proof:

- Add config/API/UI metadata for stable ID, user-facing title, description,
  and order.
- Capture an ordered agent picker.
- Capture Codex selected beside Codex-specific tools such as apply patch,
  shell, and image viewing.
- Capture Claude selected beside Claude-specific tools.

### 2. Replace the parts you disagree with

Selected title:

> Replace the parts you disagree with.

Selected body:

> Providers, tools, model defaults, actions, settings, and UI elements are
> plugin surfaces. Keep the built-in experience where it works and replace
> only the layers your workflow disagrees with.

Why selected:

- It gives the plugin architecture a practical user benefit.
- It communicates selective replacement instead of requiring users to build
  the whole system.
- Its action-oriented voice balances the statement-oriented first title.

Viable alternatives:

- Everything is a plugin.
- Everything is replaceable.
- A plugin for every layer.
- The whole harness is yours to change.
- Your agent. Your rules.

Planned proof:

- Provider-specific settings showing authentication mode and flex processing.
- Separate plugins/features window showing independently selectable features.

### 3. Transparency by design

Selected title:

> Transparency by design.

Selected body:

> Framework and plugin boundaries make instructions, configuration, tools,
> state, and provider metadata visible and user-modifiable. Usage, cache,
> duration, and cost remain visible when the provider supplies them. Open
> source adds full source-level transparency.

Why selected:

- It states the value without implying open source is the mechanism that makes
  runtime behavior inspectable.
- Inspectability comes from explicit framework/plugin boundaries and
  user-modifiable plugins.
- Open source is an additional source-level transparency benefit.

Viable alternatives:

- See what the agent is actually using.
- Full transparency, from prompt to cost.
- See the entire agent stack.
- Nothing important is hidden.
- Inspect every layer.
- You can see what the agent sees.

Planned proof:

- Compiled system/developer instructions and enabled plugin context.
- Completed response metadata showing usage, cache, duration, reasoning tokens,
  and cost when available.

### 4. Work from anywhere

Selected title:

> Work from anywhere.

Selected body:

> Start in the terminal or Desktop app and continue the same session from your
> phone. Connect on the same network or through a self-hosted bridge when you
> are away.

Why selected:

- It states the original value directly.
- The body explains the actual local-network and bridge mechanisms.

Viable alternatives:

- Start at your desk. Continue wherever you are.
- Your workspace, wherever you are.
- One session across every screen.
- Start at your desk. Continue anywhere.
- The same work, on every device.

Planned proof:

- The same reviewed session open in Desktop and mobile.
- Matching session title, latest user/assistant content, and status.

### 5. Vibe code—or vibe anything

Selected title:

> Vibe code—or vibe anything.

Selected body:

> Turn the same agent platform toward software work, research, operations,
> content, evaluations, internal automation, or a workflow built from your own
> tools and plugins.

Why selected:

- It preserves the recognizable “vibe code” idea while intentionally extending
  the platform beyond software development.
- The em dash makes the coined phrase read as a deliberate contrast.
- The body immediately explains the real general-purpose-agent value.

Viable alternatives:

- Vibe code. Then go beyond code.
- From vibe coding to general-purpose agents.
- A general-purpose agent—not just a coding agent.
- Shape it around your workflow.
- More than a coding harness.
- Vibe code—or build any workflow.
- From vibe coding to anything.

Planned proof:

- System message at the top.
- Non-development user prompt below it.
- Initial agent reasoning that implies tool-heavy work.
- Crop before tool calls appear.

### 6. Sessions become workspaces

Selected title:

> Sessions become workspaces.

Selected body:

> Titles, subtitles, status, pinned state, snapshots, attachments, and actions
> turn conversations into durable workspaces. These behaviors are
> plugin-driven: keep them, disable them, replace them, or refine them for your
> workflow.

Why selected:

- It states the durable-session value directly.
- The body distinguishes the plugin-driven implementation from hardcoded
  product behavior.

Viable alternatives:

- Sessions become durable workspaces.
- Durable workspaces, not disposable chats.
- Work that persists.
- Keep the work, not just the transcript.
- Experiment without losing the thread.

Planned proof:

- Session list with `todo`, `in-progress`, and `done`.
- Pinned and unpinned sessions.
- Descriptive titles and subtitles.
- Plugin-provided controls or configuration that own those fields.

## Overlapping Theme: You Are In Control

“You are in control.” remains a viable umbrella value, but it overlaps:

- model choice;
- plugin replacement;
- transparency and modification;
- runtime/connectivity ownership;
- workflow adaptation.

Preserved options:

1. Standalone highlight: strongest wording, highest duplication risk.
2. Hero support line: can tie model choice, replaceability, and transparency
   together, but may compete with the one-size-fits-all positioning.
3. Transparency variation: “You are in control—and nothing is hidden,” but
   this weakens the shorter selected transparency title.
4. Plugin-section outcome: keep “Replace the parts you disagree with” and use
   control as the concluding benefit.

Current recommendation: use control as an outcome in the plugin/body language,
not as a seventh highlight.

## Platform Download Presentation

Reviewed references:

- `https://zcode.z.ai/en/docs/install`
- `https://opencode.ai/download`
- `https://toggl.com/apps/mobile/ios`
- `https://toggl.com/apps/mobile/android`

### Selected Desktop layout: current platform first

```text
Download Crystal Lattice Desktop

[Apple logo] macOS
Universal DMG · Apple silicon + Intel · macOS 14+
[Download for macOS]

All platforms
[Windows logo] Windows — Coming soon
[Linux logo]   Linux — Coming soon
```

Why selected:

- gives the only real download clear priority;
- keeps version/architecture details subordinate;
- makes unavailable platforms discoverable without presenting false actions;
- can activate Windows/Linux later without replacing the section.

Viable alternative: three-column platform matrix.

```text
[Apple logo]        [Windows logo]      [Linux logo]
macOS               Windows             Linux
Universal DMG       Coming soon         Coming soon
[Download]          [disabled]          [disabled]
```

The matrix is symmetrical and easy to extend but gives unavailable platforms
more visual weight.

### Selected mobile availability layout

```text
[Apple logo] iOS             [Android logo] Android
Coming soon                   Coming soon

[email address]
[Join the mobile release waitlist]
```

Until the store listings exist:

- both platform controls are grayed;
- both say **Coming soon**;
- neither is interactive;
- visible text conveys all logo meaning.

Official store badges replace these states only after real listings exist.

## Screenshot-Specific Product Decisions

Some planned proof may require hiding or reordering settings/plugin rows.
Classify each need before implementation:

1. Real product improvement when ordinary users benefit from the behavior.
2. Maintained capture-only UI plugin/fixture when it truthfully demonstrates
   plugin extensibility without changing production defaults.
3. One-off candidate aid only for exploration; never promote it as reviewed
   proof.

The agent picker metadata change is a real product improvement because the
current backend/SDK/Desktop path exposes and renders bare agent IDs.

Selected implementation:

- agent config accepts optional `display.title`, `display.description`, and
  finite `display.order`;
- stable config keys remain agent IDs;
- the existing `/agents` string list and SDK `listAgents()` remain compatible;
- `/agents` adds ordered `agent_descriptors`;
- the SDK adds optional `listAgentDescriptors()` and controller descriptor
  caching;
- Desktop renders descriptor title/description/order and submits the stable ID;
- display metadata is stripped before provider request configuration is built.

Capture-specific ordering/hiding does not add production controls solely for
screenshots. Deterministic fixtures select the relevant rows. Session-workspace
proof reuses the existing `session-status-app`, `session-pinned-app`, and
`session-title-app` contracts, including `todo`, `in_progress`, and `done`
values.

The detailed implementation and verification plan lives in
`tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`.

## Revision Procedure

When a section does not work in context:

1. Start with the alternatives preserved here.
2. State whether the problem is value clarity, title rhythm, body accuracy,
   proof composition, or responsive layout.
3. Compare at least the selected version and one viable alternative in the
   real page.
4. Record the new decision and rationale here.
5. Preserve the replaced version when it remains credible enough to test
   later.
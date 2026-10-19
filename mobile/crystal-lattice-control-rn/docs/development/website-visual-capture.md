# Website visual capture

`MobileWebsiteVisualHarness` renders deterministic production components for
homepage proof candidates. Detox launches the ordinary app target with
`clcWebsiteVisualHarness`, selects a named fixture state, drives the real
control needed to expose that state, and stores ignored PNG candidates under
`artifacts/website-visual/`.

For a dedicated existing simulator, set `DETOX_IOS_DEVICE_ID` to its UDID.
This takes precedence over the device-type selector and avoids capture runs
being allocated to another simulator with the same model.

## Real action displays

The compiled-system-message and cost-report captures do not invent modal
content in TypeScript. Refresh their fixture with:

```bash
python scripts/generate_website_action_fixtures.py
```

The generator:

1. creates a real `AgentApplication`;
2. loads the production system-message and cost-tracking plugins;
3. creates a persisted session;
4. executes `show_compiled_system_message` through the feature-action path;
5. seeds generic deterministic records through the real SQLite cost store;
6. executes `show_cost_report` through the application-action path;
7. writes sanitized UI elements, action definitions, and response envelopes
   to `src/testing/fixtures/websiteActionDisplays.json`.

The captured app still opens the production session actions menu and sends the
selected element through `runApplicationAction`. The fixture backend returns
the generated real response envelope, and the production action-display modal
renders it.

Cost values are illustrative. Project/session names are generic, and the
fixture is checked for local paths and credential-like fields.

## Revised proof states

- `compiled`: real **Show compiled system message** action and modal.
- `cost`: provider usage footer behind the real **Cost report** action modal.
- `vibe`: the configured `zai` profile, identified as GLM-5.3 Flash through
  Z.ai, with attached source files and expanded pre-execution reasoning.
- `workspaces`: production session list with `todo`, `in_progress`, and
  `done`, header pin state, a fresh pinned-action preference namespace, and
  the default-pinned status rich list open. The first row reuses the Starlette
  compatibility title/subtitle from the conversation fixture, and its
  descriptive slug avoids exposing a raw session UUID.
- `message-actions`: the terminal Starlette/Codex assistant message with the
  production Message actions menu open. The capture scrolls to the bottom and
  targets the terminal message's action trigger in the native accessibility
  order.
- `composer-active`: active request with the production Composer actions menu,
  model/reasoning/web-search controls, hard cancel, and soft cancel.
- `system-template`: authored System-role instruction template with unresolved
  placeholders followed by its user request.
- `home`: production Home screen with deterministic local Watchlist, notes,
  recent sessions, saved connections, and request states.
- `connections`: the ordinary pre-connection application screen, captured
  without the website harness so the real Manual Address, Automatic
  Discovery, Bridge Service, and Cloud Agent Link choices remain visible.

The `workspaces` capture now also supplies deterministic transient request
states. Its `workspaces-list-<theme>.png` source is taken before the status
selection modal opens; `workspaces-<theme>.png` retains the modal state.

Select a bounded subset without changing the capture test:

```bash
CLC_WEBSITE_VISUAL_KINDS=composer-active,message-actions,workspaces,system-template,home,connections \
  npm run detox:capture:website-visual:ios
```

Do not promote these captures directly. Homepage composition, annotations,
device frames, review, source promotion, optimization, and binding are owned
by the landing-page visual asset workflow.
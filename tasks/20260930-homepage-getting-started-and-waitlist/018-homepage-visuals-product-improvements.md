# Produce Homepage Proof Visuals And Supporting Product Improvements

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`

After the selected homepage copy and download layout are approved in context,
make the real product improvements and reviewed capture fixtures needed to
produce truthful proof for all six highlights. Keep screenshot-specific
ordering or hiding separate from durable product behavior until its ownership
is explicitly decided.

## Requirements checklist

- [x] Configured agents support a user-facing title, description, and explicit
      order in addition to the stable agent ID, and that metadata reaches the
      public backend/SDK/Desktop picker without breaking existing string-ID
      consumers.
- [x] The agent picker presents ordered title/description rows while retaining
      stable IDs for submission, session metadata, APIs, and compatibility.
- [ ] Desktop agent selection is a real consolidated two-pane window: the
      ordered agent list remains on the left and the selected agent's effective
      default provider/extensions/features/tools appear on the right before a
      session is created or switched.
- [ ] A read-only public backend/SDK contract supplies effective agent-profile
      plugin entries without creating a temporary session, exposing secrets,
      or changing stable agent/session IDs.
- [ ] Highlight 1 has two reviewed captures from the real consolidated window:
      Codex with apply patch, shell, and image viewing; and Claude with
      read/write/edit/glob/grep/bash-style tools.
- [ ] Highlight 2 uses two reviewed relationship compositions. Each contains a
      sanitized real JSON configuration snippet, the corresponding production
      plugin row, and the production UI it contributes, connected by a red
      annotated line plus non-color labels: provider settings in one image and
      session actions in the other.
- [ ] Highlight 3 uses the real **Show compiled system message** session action
      and the real **Show cost report** action contract. It combines compiled
      instructions, provider usage metadata, and deterministic synthetic cost
      records using the established magnification/callout treatment without
      implying uniform provider metadata or real company spending.
- [ ] Highlight 4 is one reviewed composite image—not two independent images—
      with a recognizable Desktop frame and a phone frame. Both clients show
      the same title, subtitle/status/agent, latest prompt, and answer so
      continuity is immediately visible.
- [ ] The light-theme user-message foreground is corrected as a product fix:
      dark text is used on the light blue user bubble while dark-theme contrast
      remains light-on-dark across both maintained Markdown renderers, raw
      message text, and applicable attachment/message affordances.
- [ ] Highlight 5 identifies the selected agent as GLM-5.3 through Z.ai, shows
      expanded reasoning, and uses a non-development request that naturally
      requires file/web/tool work. The screenshot stops before tool calls and
      neither the prompt nor reasoning uses the phrase **tool-heavy**.
- [ ] The session-pinned plugin keeps the star in the header but changes its
      action-bar `default_pinned` value to `false`; the session-status plugin
      changes its rich status action defaults to pinned. Existing stored user
      preferences remain authoritative and are not force-migrated.
- [ ] Highlight 6 shows the corrected production defaults with exact
      session-status, session-pinned, and session-title plugin contracts:
      `todo`, `in_progress`, and `done`; pinned and unpinned sessions;
      descriptive titles/subtitles; one visible pin star per row; and the
      status action present in the default action bar.
- [ ] Published Desktop captures use a deterministic standard blue accent
      similar to mobile, not the operator's personal macOS accent color.
- [x] Website claims and captions are reconciled with the accepted draft
      compatibility baseline now maintained under
      `landing_page/research/current-product-and-compatibility-baseline/`,
      preserving Available, Conditional, Optional, and Planned distinctions
      and the non-upstream compatibility disclaimer.
- [x] Every screenshot-specific hide/reorder behavior is explicitly classified
      as a real product improvement, a maintained capture fixture/plugin, or a
      one-off candidate aid before implementation.
- [x] Capture-only behavior does not silently alter production defaults or
      misrepresent unavailable product capability.
- [ ] Light/dark proof variants, alt text, dimensions, compression, content
      bindings, and freshness triggers are maintained through the visual asset
      framework.
- [ ] Final proof assets and their claims receive human visual approval before
      the website or waitlist work advances.

## Prior approved decisions

### Agent metadata contract

Current fact: `/agents` and `frontend-sdk.listAgents()` expose string IDs, and
the Desktop picker renders those strings. Title, description, and order require
a public compatibility design.

Recommendation:

- preserve `listAgents(): string[]` temporarily for compatibility;
- add an agent-descriptor endpoint/method returning
  `{id, title, description, order}`;
- let new clients prefer descriptors and fall back to string IDs;
- keep IDs authoritative for session creation/switching and persistence.

This contract was approved and implemented before the October 2 visual review.

### Screenshot-specific row selection and ordering

Options:

1. **Real product improvement**
   - Add user-facing hide/order controls for settings or plugin rows.
   - Best when ordinary users need the capability.
   - Highest API, persistence, UX, and testing cost.
2. **Maintained capture-only UI plugin/fixture**
   - A deterministic plugin contributes or orders only the rows required by the
     reviewed screenshot fixture.
   - Truthful when the screenshot demonstrates real plugin extensibility.
   - Must remain clearly test-owned and not change production defaults.
3. **One-off candidate aid**
   - Temporary local-only code or data used to explore composition.
   - Cannot be promoted as reviewed proof unless replaced by a reproducible
     maintained source.

The approved rule remains: prefer real product improvements when ordinary
users benefit; otherwise use a maintained capture-only plugin/fixture. Do not
promote one-off candidate aids.

## Planned visual set

### 1. One workspace for every model family

- Replace the current artificial side-by-side harness with a real two-pane
  Desktop agent selection window.
- The left pane owns ordered agent title/description/ID selection.
- The right pane loads the selected agent's effective default plugins through
  a read-only agent-profile endpoint and groups provider, extensions, features,
  and tools. The screenshot opens the **Tools** group.
- Capture A selects Codex and shows apply patch, shell, and image viewing.
- Capture B selects Claude and shows read, write, edit, glob, grep, and bash.
- The window must be useful in the real new-session and switch-agent flows,
  not a capture-only shell.

### 2. Replace the parts you disagree with

- Capture A uses a sanitized maintained JSON snippet that loads the OpenAI
  Responses package, the relevant production plugin rows, and the real session
  settings containing authentication mode and flex processing.
- Capture B uses a sanitized maintained JSON snippet that loads application
  plugins such as session status/title/actions, the matching plugin rows, and
  the real session-actions surface they contribute.
- Red connector lines show `config -> plugin -> contributed UI`; numbered or
  textual endpoint labels carry the same meaning without relying on color.
- The red line is an illustrative asset annotation and must not be made to look
  like application UI.

### 3. Transparency by design

- Capture A executes the real `show_compiled_system_message` action through the
  production session-action path and displays its real action modal. A focused
  callout magnifies the relevant compiled instruction excerpt.
- Capture B combines a real provider usage footer with the production Cost
  report action window. The report is generated from deterministic synthetic
  records through the actual cost-tracking plugin contract, then uses the same
  focus/magnification treatment as the existing usage-and-cost asset.
- Synthetic project/session names are generic and the caption makes clear that
  the values are illustrative. No private cost records or company totals are
  used.

### 4. Work from anywhere

- Produce one image with a Desktop frame and a phone frame.
- Desktop and mobile show the exact same session title, subtitle/status, agent,
  latest user prompt, and assistant answer.
- Add restrained **Desktop** and **Mobile** labels and matching session-title
  emphasis so continuity is recognizable at homepage display size.
- Use real client captures inside the frames. Device chrome and annotations are
  illustrative composition, not simulated product controls.

### 5. Vibe code—or vibe anything

- The capture identifies GLM-5.3 through Z.ai as the active agent/model.
- A non-development system message appears first.
- The user asks for a research/operations result that naturally requires
  inspecting files or attached data, checking external sources, comparing
  evidence, and producing a structured recommendation.
- Expanded initial reasoning describes those concrete inspection and research
  steps without using the phrase **tool-heavy**.
- Tool calls remain outside the crop because the capture represents the
  reasoning-before-execution state.
- The corrected light-theme user message uses dark foreground text on its
  light blue bubble.

### 6. Sessions become workspaces

- Session list includes `todo`, `in_progress`, and `done`.
- Includes pinned and unpinned sessions with descriptive title/subtitle fields.
- The pin star occupies the `header_trailing` placement only by default and is
  not duplicated in the action bar.
- The status action is default-pinned and its real rich list is open in the
  reviewed composition, matching the supplied reference.
- The fresh capture preference namespace proves product defaults; separate
  tests prove stored user preferences still override changed defaults.
- Supporting copy states these statuses/fields/actions are plugin-driven and
  can be turned off, replaced, or refined.

## October 2, 2026 visual review outcome

The first candidate set is retained as design history but is not approved for
promotion or homepage binding.

Review findings:

1. The agent/tool content was useful, but the side-by-side window did not exist
   in the product. Replace it with a real consolidated Desktop window.
2. Replace standalone settings/plugins screenshots with annotated
   configuration-to-plugin-to-UI relationship proof, including a session
   actions example.
3. Replace the direct system-message bubble with the real session action and
   add real Cost report action proof plus magnification.
4. Replace independent Desktop/mobile images with one framed composite whose
   shared session is unmistakable.
5. Correct user-bubble contrast, use GLM-5.3 through Z.ai, expand reasoning,
   and revise the prompt/reasoning language.
6. Correct pin/status default-pinned behavior and recapture the real plugin
   state.

The operator's pink macOS accent is personal configuration and is not part of
the product identity. Published Desktop captures use deterministic blue.

Compatibility source reviewed during planning and reconciled after the branch
merge:

- historical review branch: `develop`;
- historical review commit:
  `c52db305e0a815da5831d462a495df68ec4f2eb7`;
- canonical package:
  `landing_page/research/current-product-and-compatibility-baseline/`;
- canonical website projection:
  `landing_page/research/current-product-and-compatibility-baseline/website-compatibility-data.md`;
- accepted product source revision:
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`;
- transformation version: `compatibility-baseline-v2`;
- review state: accepted;
- maturity: draft.

The canonical package supersedes the historical numbered location and is more
complete than the earlier projection, so the historical file is not copied
into a duplicate directory. The accepted website projection verifies against
its maintained generator. Current extraction also detects later Anthropic
context-editing and compaction additions; under the package's source-revision
policy, that drift requires a separate re-audit and does not silently alter
the accepted classifications used by this website task.

## Execution plan

Status: Approved

The October 2 review materially changes user-visible Desktop behavior, the
shared theme contract, application-plugin defaults, capture sources, and four
of the six visual compositions. The earlier approval no longer authorizes
execution beyond the already-completed agent descriptor work and unpromoted
candidate infrastructure.

### Design

#### Consolidated Desktop agent selection

Extend the real `AgentPickerWindow` into a two-pane selector rather than adding
a screenshot-only shell.

The left pane retains ordered agent descriptors and stable-ID selection. The
right pane presents selected-agent details and grouped effective default
plugins. New-session mode describes these as **Agent defaults** because no
session exists yet. Switch-agent mode previews the selected target agent rather
than the current session's overrides.

Add an additive read-only endpoint:

```text
GET /agents/{agent_id}/plugins
```

Recommended response:

```json
{
  "plugins": [
    {
      "id": "codex_shell_tool",
      "kind": "tools",
      "class_path": "...",
      "enabled": true,
      "active": true,
      "source": "agent"
    }
  ]
}
```

The server derives this from the existing per-agent plugin runtime,
`list_plugins_for_agent()`, `get_agent_plugins()`, and the agent's effective
base config. It returns plugin identity/state only—never config values,
credentials, environment values, or provider tokens.

The SDK adds optional `listAgentPlugins(agentId)` and a small selected-agent
cache. The Desktop window fetches on selection, handles loading/error/empty
states, groups provider/extensions/features/tools, and keeps submission
semantics unchanged.

#### Plugin default corrections

Change the real plugin declarations:

- `session-pinned-app`: `default_pinned: false`; retain
  `header_trailing` and `actions_bar` placements so the star remains in the
  header and can still be user-pinned deliberately.
- `session-status-app`: `default_pinned: true` for both the session-list and
  session-view rich status actions.

Do not migrate or overwrite saved connection-scoped preferences. Defaults apply
only when a preference has not been stored.

#### User-message contrast

Add a dedicated `bubbleUserText` field to the shared React Native `Theme`
contract:

- light theme: dark text on the translucent light-blue bubble;
- dark theme: light text on the dark-blue bubble;
- dynamic Desktop theme: derive a readable foreground for the effective user
  bubble rather than reuse `textOnPrimary`.

Use the token consistently in both Markdown renderers, raw user text, inline
code, links/lists, and relevant user-bubble attachment labels. Keep
`textOnPrimary` for genuinely solid primary buttons and controls.

#### Capture truth and compatibility

Use the reconciled accepted compatibility package at
`landing_page/research/current-product-and-compatibility-baseline/` as the
claim source. Its accepted projection remains pinned to source revision
`add5f5e71de3bb1676851bb840dfd77620f63ddb`; later product drift requires a
separate re-audit rather than an automatic regeneration inside this task.
Reconciliation is content provenance work, not permission to advertise
Planned rows as current.

Use:

- Available capabilities as direct current claims;
- Conditional/Optional capabilities with explicit qualifiers;
- Planned capabilities only as future-looking material outside current proof;
- the compatibility disclaimer for all model-family tool bundles.

### Ordered execution

1. Reconcile the compatibility baseline and record its source revision and
   canonical package provenance in the durable homepage decision document.
2. Implement the read-only agent-profile plugins endpoint, SDK method/cache,
   and consolidated two-pane Desktop picker with backend/SDK/Desktop tests.
3. Correct pin/status plugin defaults, docs, fixtures, unit tests, real
   application integration, and saved-preference regression coverage.
4. Add `bubbleUserText`, update both mobile Markdown renderers and Desktop
   message rendering, audit user-bubble affordances, and add light/dark
   component regressions.
5. Make Desktop capture theme injection deterministic blue while ordinary
   application windows continue to follow user/system accent settings.
6. Build real action-display fixtures:
   - execute `show_compiled_system_message` through its production action path;
   - seed generic deterministic records through the real cost-tracking store
     and execute `show_cost_report`;
   - retain provider usage metadata only where the fixture provider supplies
     it.
7. Build revised capture fixtures:
   - actual consolidated Codex and Claude picker states;
   - provider-config/plugin/settings and application-config/plugin/actions
     relationships;
   - GLM-5.3/Z.ai system/prompt/expanded-reasoning state;
   - corrected session-list defaults;
   - exact same-session Desktop/mobile state.
8. Add specialized asset composition:
   - red relationship connectors with accessible labels;
   - established focus/magnification callouts;
   - one Desktop/phone framed continuity composite;
   - deterministic blue Desktop frames and no personal accent data.
9. Produce light/dark candidates and a LAN gallery. Stop for explicit human
   approval before promotion.
10. After approval, promote reviewed masters, generate optimized derivatives,
    bind primary/secondary media, run complete responsive/browser/catalog
    verification, and update durable rationale.

### Implementation decisions and open questions

- Approved and implemented: preserve string IDs and `listAgents()` while
  adding ordered `{id, title, description, order}` descriptors.
- Decision: stable agent IDs remain authoritative for creation, switching, and
  persistence.
- User decision: the consolidated agent/plugins view becomes real Desktop
  product behavior, not a visual-only harness.
- Recommendation requiring plan approval: use additive
  `GET /agents/{agent_id}/plugins` plus optional SDK
  `listAgentPlugins(agentId)`.
- Recommendation requiring plan approval: show all plugin groups in the right
  pane and keep **Tools** expanded in the reviewed Codex/Claude captures.
- User decision: use real JSON snippets and production plugin/settings/actions
  surfaces with red relationship connectors.
- User decision: use the real compiled-system-message action and cost-report
  action.
- Decision: Cost report values are synthetic and generated through the actual
  plugin/store contract.
- User decision: continuity is one framed composite with recognizable matching
  session state.
- User decision: GLM-5.3 through Z.ai, expanded reasoning, and no
  **tool-heavy** wording.
- Recommendation requiring plan approval: add shared `bubbleUserText` rather
  than branching on light/dark inside individual renderers.
- User decision: pin is not default-pinned; status is default-pinned.
- Interpretation to confirm with plan approval: status defaults to pinned on
  both session-list and session-view surfaces. Saved user choices remain
  authoritative.
- Decision: published Desktop screenshots use deterministic blue; production
  UI still honors the user's accent.
- Decision: no current website claim promotes Planned compatibility rows as
  available.

### Documentation

- Maintain the accepted website projection at
  `landing_page/research/current-product-and-compatibility-baseline/website-compatibility-data.md`
  and preserve its source revision, transformation version, historical review
  commit, and later-drift boundary.
- Update application HTTP/configuration and frontend SDK docs for the read-only
  agent-profile plugins contract.
- Update Desktop user/development documentation for the consolidated agent
  selection window and selected-agent plugin preview.
- Update `session-pinned-app` and `session-status-app` READMEs/docs for the new
  default-pinned behavior and saved-preference rule.
- Update mobile/Desktop theme documentation for `bubbleUserText` and why
  `textOnPrimary` is not valid on translucent user bubbles.
- Document the deterministic blue capture theme, real action-display fixtures,
  synthetic cost data generator, and relationship annotation pipeline.
- Update the durable homepage positioning/visual-decision record with:
  - the rejected first candidate set and review rationale;
  - the revised product decisions;
  - compatibility-baseline provenance;
  - final screenshots and reasons selected;
  - retained alternatives worth retrying.
- Update visual asset catalog metadata, provenance, alt text, dimensions,
  byte budgets, bindings, and freshness triggers.

### Task checklist

- [x] **HUMAN JUDGMENT:** Approve the agent metadata compatibility contract.
- [x] **HUMAN JUDGMENT:** Classify each hide/reorder need as product or
      capture-only behavior.
- [x] **AGENT:** Implement and verify approved product improvements.
- [x] **AGENT:** Implement deterministic reviewed fixtures/plugins.
- [x] **AGENT:** Capture the first six visual concepts for review.
- [x] **HUMAN JUDGMENT:** Review and reject/revise the first candidate set.
- [x] **HUMAN JUDGMENT:** Approve this revised Draft execution plan, including
      the agent-profile endpoint, shared bubble foreground token, and status
      default pinned on both list and session-view surfaces.
- [x] **AGENT:** Import/reconcile the accepted compatibility baseline.
- [ ] **AGENT:** Implement the consolidated Desktop agent/plugins selector.
- [ ] **AGENT:** Correct pin/status plugin defaults and saved-preference
      coverage.
- [ ] **AGENT:** Correct user-bubble foreground contrast across renderers.
- [ ] **AGENT:** Implement the real compiled-system and synthetic Cost report
      action-display fixtures.
- [ ] **AGENT:** Implement revised relationship, continuity, GLM/Z.ai, and
      workspace capture compositions.
- [ ] **AGENT:** Capture and review all revised visual concepts.
- [ ] **AGENT:** Promote approved source masters and generate public assets.
- [ ] **AGENT:** Bind proof to homepage content and run complete verification.
- [ ] **HUMAN JUDGMENT:** Approve every final visual composition.

### Requirement verification

- Agent metadata: public backend + production frontend integration verifies
  ordered title/description rendering while session creation still submits the
  stable ID; legacy string-list behavior remains covered if preserved.
- Agent-profile plugin proof: a real FastAPI → HTTP transport → SDK → Desktop
  integration returns the selected agent's effective default plugins; a
  Desktop component/native check proves the two-pane window renders and still
  submits the stable ID.
- Consolidated-window compatibility: new-session and switch-agent flows remain
  functional when the optional plugin-preview API is unavailable, empty, slow,
  or returns an error.
- Plugin-default proof: owning plugin unit/integration tests assert pin
  `default_pinned: false` and status `default_pinned: true`; frontend tests
  prove a stored explicit preference wins over changed defaults.
- User-bubble contrast: both maintained Markdown renderers and raw text use the
  dedicated user-bubble foreground in light/dark themes; component tests assert
  dark-on-light-blue and light-on-dark-blue behavior.
- Relationship proof: config snippets are parsed from maintained sanitized
  fixtures, plugin IDs match production registry entries, and the linked
  setting/action exists in real UI schema. Connectors include non-color labels.
- Action-display proof: compiled-system output crosses the existing real
  backend action integration; Cost report fixture generation seeds and invokes
  the actual cost-tracking plugin/store before frontend capture.
- Cross-device proof: one fixture/session identity appears in both production
  Desktop and mobile clients; automated fixture assertions require exact
  matching title, subtitle/status, agent, prompt, and answer before composition.
- GLM/Z.ai proof: fixture labels match default config/provider data and
  compatibility qualifiers; expanded reasoning is visible and no tool call is
  inside the crop.
- Session-list proof: production list components render exact plugin-provided
  status, title, subtitle, and pin state with one default pin placement and a
  default-pinned status action.
- Capture-only boundary: repository inspection and tests prove fixtures,
  synthetic costs, annotations, and blue capture theme do not alter production
  defaults beyond the separately approved product fixes.
- Compatibility-claim proof: current copy maps only Available features to
  unqualified current claims; Conditional/Optional claims keep qualifiers and
  Planned rows are not presented as shipped.
- Asset proof: catalog check, source provenance, theme variants, dimensions,
  compression, alt text, and browser loading all pass.

### Additional implementation verification

- Verify configuration ordering is deterministic across Python parsing, HTTP,
  SDK caching, and Desktop rendering.
- Verify agent metadata does not change persisted session IDs or switch-agent
  semantics.
- Verify agent-profile plugin responses contain no config values, credentials,
  environment values, account identifiers, or provider tokens.
- Verify provider settings and session actions remain usable independently of
  the annotated website composition.
- Verify synthetic Cost report records use generic project/session names and
  are excluded from normal runtime state.
- Verify ordinary Desktop windows still honor system/user accent settings while
  capture harnesses use deterministic blue.
- Verify the pin/status default change does not overwrite existing persisted
  pinned-action preferences.
- Verify screenshot fixtures contain no credentials, private prompts, customer
  data, or misleading unavailable controls.
- Verify all images remain legible at actual website display sizes.

## Implementation Notes

- 2026-10-02: The user approved the descriptor compatibility recommendation,
  capture-specific configuration/plugin approach, and this execution plan.
- 2026-10-02: Existing session-status, session-pinned, and title/subtitle
  application plugin contracts are authoritative for Highlight 6. Capture
  fixtures must use them directly or mirror them exactly.
- 2026-10-02: Added optional `agents.<id>.display` configuration with title,
  description, and finite order. The application exposes ordered descriptors
  in `GET /agents` while preserving the legacy sorted string list. Display
  metadata is removed before provider request configuration is built.
- 2026-10-02: Added SDK `AgentDescriptor`,
  `listAgentDescriptors()`, descriptor-aware controller caching, and
  `ensureDescriptorsLoaded()`. Desktop renders ordered title/description rows,
  shows the stable ID as secondary metadata, and still submits only the ID.
- 2026-10-02: Product verification passed: 76 focused core/application tests,
  all 352 frontend SDK tests, Desktop TypeScript checking, and focused picker
  and Sessions-panel component tests.
- 2026-10-02: Added a maintained Desktop website-visual harness using the
  production agent picker and production session-plugins window. The
  harness-owned AppKit content-view export avoids screen-recording permission.
  It generated Codex and Claude light/dark candidates successfully.
- 2026-10-02: Added deterministic mobile capture kinds for provider
  authentication/flex settings, feature plugins, compiled instructions,
  non-development reasoning, and plugin-driven session workspaces. The session
  workspace fixture uses the existing session-status, session-pinned, and
  session-title plugin IDs, values, and UI contracts.
- 2026-10-02: The expanded iOS Detox capture is running in the background
  after its first foreground build exceeded ten minutes. Candidate review and
  promotion remain pending.
- 2026-10-02: The complete 20-state iOS Detox website-visual loop passed in
  one run after replacing brittle readiness text with stable production
  identifiers. It generated light/dark candidates for provider settings,
  feature plugins, compiled instructions, usage/cost, mobile continuity,
  general-purpose reasoning, and plugin-driven workspaces.
- 2026-10-02: Added a Desktop same-session continuity state using the same
  session ID, title, latest prompt/answer, and agent as the mobile fixture. The
  incremental macOS producer generated its light/dark candidates together with
  the Codex and Claude picker/tool candidates.
- 2026-10-02: Added paired-proof support to the homepage media contract without
  changing the approved editorial/card structure. No candidate is bound yet.
- 2026-10-02: A LAN review gallery groups all ten light and ten dark candidates
  by the six feature highlights. Human approval is now the gate before source
  promotion, WebP generation, homepage binding, and final responsive review.
- 2026-10-02: Human review did not approve the first candidate set. The task
  returned from Approved to Draft because the revision adds a real
  consolidated Desktop selector, a public read-only agent-profile plugin
  contract, a shared theme token, plugin default changes, real action-display
  fixtures, and materially different compositions.
- 2026-10-02: The consolidated selector is feasible. Existing
  `list_plugins_for_agent()` and per-agent plugin runtime state provide the
  backend source, but no public agent-profile plugin endpoint currently exists.
  The session-plugin endpoint cannot cover new-session selection because no
  session exists yet.
- 2026-10-02: Confirmed the light-theme color defect: the classic Markdown
  renderer uses `textOnPrimary` for user messages even though
  `bubbleUserBg` is a translucent 12% blue. Raw text already uses normal dark
  text, and the selectable Markdown renderer currently ignores the user
  variant. A dedicated user-bubble foreground token is the coherent fix.
- 2026-10-02: Confirmed real action contracts:
  `show_compiled_system_message` returns a modal text action display, and
  `show_cost_report` returns a modal Markdown report with totals, daily
  project/bucket tables, and top sessions/projects.
- 2026-10-02: Confirmed current plugin defaults are the reverse of the reviewed
  target: pin is `default_pinned: true`; status list and session actions are
  `default_pinned: false`. Stored frontend preferences already override plugin
  defaults and must not be migrated.
- 2026-10-02: Reviewed the accepted draft compatibility data from `develop`
  commit `c52db305e0a815da5831d462a495df68ec4f2eb7`. It is absent on current
  `main`, so the revised plan imports/reconciles it before publishing claims.
  Available, Conditional, Optional, and Planned states remain distinct, and
  model-family bundles remain Crystal Lattice compatibility implementations,
  not official upstream applications.
- 2026-10-02: This was a planning-only pass. No product, plugin, capture, or
  website source was modified beyond this task-plan revision.
- 2026-10-02: The user approved the revised plan, including the additive
  agent-profile plugin endpoint, all plugin groups in the consolidated picker,
  the shared `bubbleUserText` contract, status default-pinned on both list and
  session-view surfaces, compatibility-baseline reconciliation, and execution
  of the revised product/capture work. Planned asset promotion remains gated by
  a later human visual confirmation.
- 2026-10-04: Reconciled the historical numbered compatibility reference with
  the canonical accepted package at
  `landing_page/research/current-product-and-compatibility-baseline/`. The
  accepted website projection is pinned to source revision
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`, uses transformation
  `compatibility-baseline-v2`, and passes its maintained website-data
  generator check. Current extraction detects later Anthropic
  context-editing/compaction additions; the package explicitly requires a
  separate re-audit for post-source drift, so this task does not regenerate
  or silently reclassify accepted claims.

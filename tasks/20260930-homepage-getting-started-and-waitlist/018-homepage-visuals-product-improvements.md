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

- [ ] Configured agents support a user-facing title, description, and explicit
      order in addition to the stable agent ID, and that metadata reaches the
      public backend/SDK/Desktop picker without breaking existing string-ID
      consumers.
- [ ] The agent picker presents ordered title/description rows while retaining
      stable IDs for submission, session metadata, APIs, and compatibility.
- [ ] Highlight 1 has two reviewed captures: a Codex-oriented agent with
      Codex-specific tools such as apply patch, shell, and image viewing; and a
      Claude-oriented agent with Claude-specific tools.
- [ ] Highlight 2 clearly proves provider-specific settings such as
      authentication mode and flex processing, plus a separate plugin/features
      view.
- [ ] Highlight 3 combines compiled instructions with provider usage/cost
      metadata without implying every provider supplies identical metadata.
- [ ] Highlight 4 shows the same reviewed session in Desktop and mobile with
      matching identity and content.
- [ ] Highlight 5 shows a system message, a non-development user prompt, and
      initial agent reasoning that implies tool-heavy work without exposing
      tool calls in the frame.
- [ ] Highlight 6 shows a session list containing plugin-driven status values
      (`todo`, `in-progress`, `done`), pinned and unpinned rows, descriptive
      titles, and subtitles; public copy states that these fields/actions can
      be disabled, replaced, or refined through plugins.
- [ ] Every screenshot-specific hide/reorder behavior is explicitly classified
      as a real product improvement, a maintained capture fixture/plugin, or a
      one-off candidate aid before implementation.
- [ ] Capture-only behavior does not silently alter production defaults or
      misrepresent unavailable product capability.
- [ ] Light/dark proof variants, alt text, dimensions, compression, content
      bindings, and freshness triggers are maintained through the visual asset
      framework.
- [ ] Final proof assets and their claims receive human visual approval before
      the website or waitlist work advances.

## Material implementation decisions still required

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

This is a material public interface decision and requires approval before
implementation.

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

Recommendation: prefer real product improvements when the behavior has user
value; otherwise use a maintained capture-only plugin/fixture. Do not promote
one-off candidate aids.

## Planned visual set

### 1. One workspace for every model family

- Improve config and API/UI metadata with ID, title, description, and order.
- Capture A: Codex profile selected; adjacent session settings/plugins tools
  section shows apply patch, shell, and image-viewing capabilities.
- Capture B: Claude profile selected; adjacent tools section shows
  Claude-specific read/write/edit/glob/grep/bash-style capabilities.
- Both captures should make one shared workspace visible.

### 2. Replace the parts you disagree with

- Capture A: provider settings emphasizing authentication mode and flex
  processing.
- Capture B: plugins/features window showing independently selectable
  provider extensions or features.
- The composition must prove both provider-native settings and replaceable
  plugin surfaces.

### 3. Transparency by design

- Capture A: compiled system/developer instructions and enabled plugin/tool
  context.
- Capture B: completed response footer with usage, cache, duration, reasoning
  tokens, and cost where supplied.

### 4. Work from anywhere

- Desktop and mobile show the same session title, latest user/assistant content,
  and status.
- Connection context should be visible enough to establish continuity without
  overwhelming the session proof.

### 5. Vibe code—or vibe anything

- System message appears first.
- A non-development user prompt appears beneath it.
- Initial reasoning is visible and suggests a tool-heavy plan.
- Tool calls themselves remain outside the crop.
- Candidate workflow: research/operations brief with several expected source
  and transformation steps.

### 6. Sessions become workspaces

- Session list includes `todo`, `in-progress`, and `done`.
- Includes pinned and unpinned sessions.
- Rows use descriptive title and subtitle fields.
- Supporting copy states these statuses/fields/actions are plugin-driven and
  can be turned off, replaced, or refined.

## Execution plan

Status: Draft

First approve the agent metadata compatibility contract and classify each
screenshot-specific hide/reorder need. Implement and test any selected product
improvements through the backend, public SDK, and real Desktop consumer before
using them as proof.

Then add deterministic visual fixtures and, where approved, maintained
capture-only plugins. Produce candidate captures from the real product paths,
review composition and truthfulness, promote accepted source masters, and
generate bounded public derivatives.

Finally bind each asset to the selected homepage claim, run visual catalog and
browser verification, and obtain explicit human approval of every light/dark
composition.

### Implementation decisions and open questions

- Open material decision: exact backward-compatible agent descriptor contract.
- Open material decision: which row-order/hide needs are product features
  versus maintained capture-only plugins.
- Open product decision: whether session status/title/subtitle presentation
  needs additional plugin contract work or only a deterministic existing
  plugin fixture.
- Decision: stable agent IDs remain authoritative even after display metadata
  is added.
- Decision: no screenshot may imply tool calls are absent merely because they
  are cropped; the copy should describe initial reasoning, not execution
  completion.

### Documentation

- Update owning backend/SDK/Desktop docs for any public agent metadata change.
- Document maintained capture-only plugins/fixtures and their exclusion from
  production defaults.
- Update the durable homepage positioning/visual-decision record with final
  screenshots, product changes, and capture-only decisions.
- Update visual asset catalog metadata, provenance, and freshness triggers.

### Task checklist

- [ ] **HUMAN JUDGMENT:** Approve the agent metadata compatibility contract.
- [ ] **HUMAN JUDGMENT:** Classify each hide/reorder need as product or
      capture-only behavior.
- [ ] **AGENT:** Implement and verify approved product improvements.
- [ ] **AGENT:** Implement deterministic reviewed fixtures/plugins.
- [ ] **AGENT:** Capture and review all six visual concepts.
- [ ] **AGENT:** Promote approved source masters and generate public assets.
- [ ] **AGENT:** Bind proof to homepage content and run complete verification.
- [ ] **HUMAN JUDGMENT:** Approve every final visual composition.

### Requirement verification

- Agent metadata: public backend + production frontend integration verifies
  ordered title/description rendering while session creation still submits the
  stable ID; legacy string-list behavior remains covered if preserved.
- Provider/plugin proof: real session settings and plugins surfaces display the
  selected provider-specific and feature rows.
- Cross-device proof: one reviewed fixture/session identity appears in both
  production Desktop and mobile clients.
- Session-list proof: production list components render plugin-provided status,
  title, subtitle, and pinned state from a deterministic backend.
- Capture-only boundary: repository inspection and tests prove fixture plugins
  do not alter production defaults.
- Asset proof: catalog check, source provenance, theme variants, dimensions,
  compression, alt text, and browser loading all pass.

### Additional implementation verification

- Verify configuration ordering is deterministic across Python parsing, HTTP,
  SDK caching, and Desktop rendering.
- Verify agent metadata does not change persisted session IDs or switch-agent
  semantics.
- Verify screenshot fixtures contain no credentials, private prompts, customer
  data, or misleading unavailable controls.
- Verify all images remain legible at actual website display sizes.
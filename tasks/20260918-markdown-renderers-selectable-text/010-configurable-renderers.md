# Configurable Markdown and Code Renderers

Replace the mobile chat's hard-coded renderer choices with persisted settings
next to the existing font and heading controls, while keeping deterministic
platform fallbacks and a stable RNMD default.

## Requirements checklist

- [x] Mobile settings provide a markdown renderer selector and a code renderer
      selector alongside base font size and markdown header size.
- [x] `react-native-markdown-display` is the default markdown renderer.
- [x] The currently active `react-native-enriched-markdown` choice is secondary
      and its visible label contains `(experimental)`.
- [x] Renderer preferences survive relaunch and older persisted typography-only
      values migrate without losing the user's font/header choices.
- [x] Every in-scope markdown surface uses the selected renderer and selected
      code implementation, subject to an explicit platform capability fallback.
- [x] The selectable native code renderer is the effective default on every
      platform where it has passed native verification.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Resolved requirement questions

1. Desktop does not show renderer selectors in this subtask. Desktop behavior
   remains fixed and supplies only the in-memory fields required by the shared
   type.
2. The user-visible code choices are selectable native and syntax highlighter.
   The enriched built-in path is renderer-specific and would create unsupported
   or confusing cross-renderer combinations.
3. Action-display markdown obeys the same preference as chat markdown.
4. A known unavailable renderer remains the requested persisted value while
   platform capabilities derive an effective fallback. Settings shows fallback
   status only when requested and effective values differ.

## Current implementation map

- Shared contract:
  `packages/frontend-rn-components/src/markdownDisplayPreferences.tsx`
  currently stores only `baseFontSize` and `headerSize`.
- Mobile persistence:
  `mobile/crystal-lattice-control-rn/src/useMarkdownDisplayPreferences.ts`
  stores normalized JSON under `clc_markdown_display_preferences_v1`.
- Mobile settings:
  `mobile/crystal-lattice-control-rn/src/components/GlobalSettingsModal.tsx`.
- Mobile chat:
  `MessageBubble.tsx` directly imports
  `SelectableMarkdownMessageContent`, so enriched markdown is fixed for user
  and assistant markdown.
- Mobile action displays:
  `ActionDisplayCard.tsx` directly imports the RNMD-backed
  `MarkdownMessageContent`, producing an existing inconsistency.
- Enriched code:
  `SelectableMarkdownMessageContent.tsx` has a local
  `CodeBlockRenderingMode` union with `syntax-highlighter`,
  `enriched-markdown`, and `selectable-code-block`, but returns the
  hard-coded selectable value.
- Desktop:
  `DesktopGlobalSettings`, `GlobalSettingsWindow`, `DesktopRoot`,
  `AppDelegate.mm`, and `DesktopWindowManager.mm` own the persisted native
  settings/event path. RNMD is the only desktop markdown renderer.

## Feasibility assessment

High. The preference provider already surrounds both applications and has
normalization, option lists, tests, and platform-owned persistence. The main
design work is separating a persisted requested renderer from the effective
platform renderer and routing every markdown consumer through one dispatcher.

A recommended shared shape is conceptually:

```ts
type MarkdownRendererId =
  | 'react-native-markdown-display'
  | 'react-native-enriched-markdown';

type CodeBlockRendererId =
  | 'selectable-native'
  | 'syntax-highlighter';
```

This draft intentionally omits the enriched renderer's built-in code path as a
user-facing choice; open question 2 can change that decision before approval.
Defaults should be RNMD and selectable-native. Normalization should
independently default missing or unknown fields so the existing storage key can
be migrated in place.

The renderer dispatcher should receive `text` and `variant` and choose the
markdown component. Both markdown implementations should receive the effective
code renderer rather than maintaining separate hidden constants.

## Capability model

| Platform | RNMD | Enriched markdown | Selectable native code |
| --- | --- | --- | --- |
| iOS | Present | Present | Implemented and reported verified |
| Android | Present | Present | Implemented, but Detox verification fails in native Fabric measurement when the optional false `wrapLines` prop is absent |
| macOS | Present | Not integrated | Not implemented until subtask 040 |

Do not silently attempt to mount an unavailable native component. A pure
capability resolver should select the stable fallback and be unit-tested
without native modules.

## Execution plan

Status: Approved

Implement the change in six bounded workstreams.

1. Extend the shared preference contract.

   Add exported renderer ID types, options, labels, defaults, and independent
   normalization for:

   ```ts
   type MarkdownRendererId =
     | 'react-native-markdown-display'
     | 'react-native-enriched-markdown';

   type CodeBlockRendererId =
     | 'selectable-native'
     | 'syntax-highlighter';
   ```

   Add the two required fields to `MarkdownDisplayPreferences`, with RNMD and
   selectable-native as defaults. Keep typography derivation independent from
   renderer IDs. Update provider memoization dependencies, public exports, and
   shared tests.

   Introduce a pure resolver that accepts requested preferences and explicit
   platform capabilities and returns effective renderer IDs plus any fallback
   reason. Unknown persisted IDs normalize to defaults; known but temporarily
   unavailable IDs remain requested while the resolver selects a fallback.

   Because desktop consumes the same shared type, update its state and
   deterministic harness/test values with fixed RNMD/syntax-highlighter
   defaults. Do not add desktop UI, native persistence, or desktop renderer
   switching in this subtask.

2. Migrate mobile persistence and settings.

   Keep the current AsyncStorage key so existing font/header preferences remain
   intact. Normalization will add missing renderer fields and write the
   normalized object back once during hydration.

   Add Markdown renderer and Code renderer rows to the existing Global Settings
   modal and options picker. Use explicit labels:

   - `React Native Markdown Display`
   - `Enriched Markdown (experimental)`
   - `Selectable native code`
   - `Syntax highlighter`

   Settings continue to apply immediately. If requested and effective values
   ever differ on mobile, show concise fallback status without overwriting the
   requested value.

3. Create one mobile markdown dispatcher.

   Add a small production component that reads the preference context, resolves
   mobile capabilities, and chooses the RNMD-backed or enriched implementation.
   Give each implementation a stable test identifier so component and native
   tests can prove which renderer is active without relying on visual
   differences.

   Route user/assistant chat markdown and markdown action-display bodies through
   this dispatcher. Raw message mode and text-format action displays remain
   unchanged. System/tool plain-text rendering remains out of scope.

4. Make code rendering portable across both markdown implementations.

   Extract the syntax-highlighter code-block presentation from the enriched
   renderer into a reusable component. Add a configured code-block dispatcher
   that chooses this component or the existing `SelectableCodeBlock`.

   RNMD `fence` and `code_block` rules use the configured code-block dispatcher.
   The enriched renderer continues using markdown segmentation and sends every
   fenced/indented code segment to the same dispatcher. Remove the hidden
   hard-coded code mode from the production path; do not expose the enriched
   renderer's internal code block as a third user option in this plan.

   Inline code remains owned by each markdown renderer because it participates
   in the renderer's prose layout rather than the block-code implementation
   choice.

5. Add regression coverage at each ownership boundary.

   - Shared unit tests cover defaults, labels, independent normalization,
     typography-only migration, known-unavailable fallback, and provider
     updates.
   - Mobile persistence tests cover old JSON, new defaults, explicit choices,
     invalid fields, normalized write-back, and relaunch hydration.
   - Settings component tests select all four renderer options and verify the
     controlled preference value.
   - Dispatcher tests cover the two markdown renderers and the full two-by-two
     markdown/code combination matrix.
   - Message and action-display tests verify they use the configured dispatcher
     while raw/text paths remain unchanged.
   - The production connections/settings harness uses the dispatcher rather
     than importing the enriched renderer directly. Its iOS and Android Detox
     scenario verifies defaults, switching, persistence across relaunch, and
     active renderer identifiers. Existing dedicated side-by-side renderer
     harnesses may remain for implementation regression testing.
   - Desktop shared-type consumers and markdown geometry tests are updated only
     as needed to preserve their fixed behavior.

6. Update maintained documentation.

   Update the shared preference development page so it no longer describes the
   contract as renderer-neutral. Document mobile labels, defaults, persistence
   migration, in-scope surfaces, and fallback semantics in the owning mobile
   development guidance. Desktop documentation changes only if a visible
   desktop behavior changes unexpectedly during implementation.

### Implementation decisions and open questions

- Approved decision: renderer selectors are mobile-only in
  subtask 010. Desktop receives compile-time/default values but no settings or
  persistence changes.
- Approved decision: expose exactly two code implementations,
  selectable-native and syntax-highlighter.
- Approved decision: markdown action displays follow the same
  markdown/code preferences as chat messages.
- Approved decision: preserve a known requested renderer when
  unavailable and derive an effective fallback; unknown IDs normalize to
  defaults.
- Decided by existing requirements: default to RNMD and selectable-native, and
  visibly label enriched markdown `(experimental)`.
- Recommended effective fallbacks: RNMD for markdown and syntax-highlighter for
  code.
- Selectable-native remains the requested default on Android, but
  syntax-highlighter is the effective fallback until subtask 040 corrects the
  native `wrapLines` measurement crash and Android passes verification.

### Documentation

- Update
  `packages/frontend-rn-components/docs/development/markdown-display-preferences.md`.
- Update the owning mobile development guidance for renderer ownership,
  defaults, labels, persistence, surfaces, and fallbacks.
- Do not document desktop selection controls unless that scope is separately
  approved and implemented.

### Task checklist

- [x] Obtain approval for the four plan assumptions.
- [x] Add shared renderer IDs, options, defaults, normalizers, and capability
      resolution.
- [x] Update fixed desktop shared-type consumers without changing desktop
      behavior.
- [x] Migrate mobile persistence and add both settings selectors.
- [x] Add the mobile markdown dispatcher and route chat/action markdown.
- [x] Add the shared block-code dispatcher and connect both markdown
      implementations.
- [x] Add shared, mobile, desktop-compatibility, and native settings coverage.
- [x] Update documentation.

### Requirement verification

- Load a typography-only saved value and verify font/header values survive,
  RNMD/selectable-native defaults are added, and normalized storage is written.
- Select every exposed markdown and code renderer, close/reopen settings and
  relaunch the app, and verify the same requested values and effective
  implementations.
- Verify the enriched option visibly includes `(experimental)` and is not the
  default.
- Render representative prose and fenced code through all four supported
  markdown/code pairings and verify both selected implementations are used.
- Verify chat markdown and markdown action displays switch together while raw
  messages and text-format action displays do not.
- Force an unsupported capability in a unit test and verify the documented
  fallback, preserved requested value, and absence of a native-component crash.
- Verify desktop retains its existing RNMD behavior and passes type/component
  coverage despite the expanded shared preference shape.

### Additional implementation verification

- Shared package: `npm --workspace @crystal-lattice/frontend-rn-components test`.
- Mobile: focused Jest suites followed by the full Jest suite and
  `npm run tsc`.
- Native mobile: focused iOS and Android connections/settings Detox scenarios;
  run the selectable-code harness if code-dispatch changes expose native layout
  regressions.
- Desktop compatibility: focused settings/markdown Jest coverage and
  TypeScript validation. Native macOS UI tests are not required unless visible
  desktop behavior changes.

## Implementation Notes

- The approved assumptions were applied: mobile-only selectors, two exposed
  code renderers, shared chat/action-display preferences, and preserved
  requested values with effective fallbacks.
- The shared preference record now includes renderer IDs. Desktop supplies
  fixed RNMD/syntax-highlighter values but does not expose or persist renderer
  settings.
- Mobile production rendering now enters through one markdown dispatcher and
  one block-code dispatcher. Direct implementation components retain their
  prior isolated defaults for focused regression harnesses.
- Detox exposed an Android native crash in the existing selectable-code package:
  `SelectableCodeBlockViewManager.measure` calls
  `props.getBoolean("wrapLines")` even when Fabric omits the optional false
  value. Android is therefore capability-disabled in subtask 010 and uses the
  approved syntax-highlighter fallback while preserving the requested
  selectable-native preference. Fixing and re-enabling that backend remains in
  subtask 040.
- The mobile Jest setup intentionally replaces RNMD with a lightweight mock
  that does not parse markdown. RNMD code-selection coverage therefore asserts
  its production rule adapter directly, while enriched-renderer coverage
  observes the rendered native/syntax leaf. Detox remains the real parser and
  native-renderer boundary.
- Shared package tests, focused mobile Jest tests, mobile TypeScript, and the
  focused desktop markdown Jest suite pass.
- A desktop-wide `tsc --noEmit` run still reports unrelated pre-existing errors
  in frontend SDK URL typing, `ChatPane`, and `ActionResultInlineCard`. The one
  task-related markdown preference error was corrected. Per user direction, no
  desktop XCTest run has been started.

## Completion Notes

Completed on September 19, 2026.

The shared markdown preference record now persists requested markdown and
block-code renderer IDs alongside typography. Mobile Global Settings exposes
the approved two markdown and two code choices. RNMD is the stable default,
enriched markdown is visibly marked `(experimental)`, and chat plus markdown
action displays use one configured markdown dispatcher and one configured
block-code dispatcher.

Older typography-only AsyncStorage records retain their font/header values and
gain RNMD/selectable-native defaults. Known unavailable requests are preserved
while capability resolution chooses RNMD or syntax-highlighter and Settings
shows the effective fallback.

Native verification established the final capability matrix:

- iOS uses selectable-native code by default and passed the complete settings,
  renderer-switching, geometry, persistence, and relaunch Detox scenario.
- Android's existing selectable-code backend crashes in Fabric measurement
  because an absent optional false `wrapLines` prop is read without `hasKey`.
  Android therefore preserves selectable-native as the requested default but
  uses syntax-highlighter effectively and shows a fallback notice. The rebuilt
  Android app passed the same Detox scenario with this behavior. The native
  fix and capability re-enable are recorded in subtask 040.
- Desktop behavior remains fixed to RNMD and syntax-highlighter; only shared
  type compatibility changed. No desktop XCTest was started, as requested.

Verification completed:

- `npm --workspace @crystal-lattice/frontend-rn-components test`: 73 tests
  passed.
- Mobile `npm test -- --runInBand`: 46 suites and 206 tests passed.
- Mobile `npm run tsc`: passed.
- Focused desktop Jest coverage for global settings, markdown rendering, and
  message typography: 10 tests passed.
- `npm run detox:build:ios`: passed.
- `npm run detox:test:connections-settings:ios`: passed against the final iOS
  bundle.
- `npm run detox:build:android`: passed.
- Android Detox passed with the documented local verification invocation using
  Detox's forced ADB installer and a 4 GB emulator:
  `npx detox test -c android.emu.e2e --cleanup --force-adb-install
  --device-boot-args="-memory 4096" e2e/connectionsSettings.e2e.test.ts`.
- `git diff --check`: passed.

The default Android alternate installer froze before application launch in this
local environment; the forced ADB installer completed and exercised the real
application. A full desktop TypeScript run remains blocked by unrelated
pre-existing errors listed in the implementation notes. The mobile package has
no discoverable ESLint configuration, so a focused ESLint command could not be
run.
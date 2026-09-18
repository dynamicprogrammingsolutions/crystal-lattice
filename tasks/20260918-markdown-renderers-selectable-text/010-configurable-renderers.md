# Configurable Markdown and Code Renderers

Replace the mobile chat's hard-coded renderer choices with persisted settings
next to the existing font and heading controls, while keeping deterministic
platform fallbacks and a stable RNMD default.

## Requirements checklist

- [ ] Mobile settings provide a markdown renderer selector and a code renderer
      selector alongside base font size and markdown header size.
- [ ] `react-native-markdown-display` is the default markdown renderer.
- [ ] The currently active `react-native-enriched-markdown` choice is secondary
      and its visible label contains `(experimental)`.
- [ ] Renderer preferences survive relaunch and older persisted typography-only
      values migrate without losing the user's font/header choices.
- [ ] Every in-scope markdown surface uses the selected renderer and selected
      code implementation, subject to an explicit platform capability fallback.
- [ ] The selectable native code renderer is the effective default on every
      platform where it has passed native verification.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Open requirement questions

1. Should desktop show renderer selectors even while it has only one markdown
   choice?
2. Which code choices should be user-visible: selectable native and syntax
   highlighter only, or the enriched renderer's built-in code rendering too?
3. Should action-display markdown obey the same preference as chat markdown?
   Recommendation: yes.
4. If a persisted renderer becomes unavailable, should settings continue to
   show the desired value with a fallback notice, or normalize storage to the
   fallback? Recommendation: preserve the desired value and derive an effective
   renderer from platform capabilities.

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
  | 'syntax-highlighter'
  | 'renderer-native';
```

The exact third code value depends on open question 2. Defaults should be RNMD
and selectable-native. Normalization should independently default missing or
unknown fields so the existing storage key can be migrated in place.

The renderer dispatcher should receive `text` and `variant` and choose the
markdown component. Both markdown implementations should receive the effective
code renderer rather than maintaining separate hidden constants.

## Capability model

| Platform | RNMD | Enriched markdown | Selectable native code |
| --- | --- | --- | --- |
| iOS | Present | Present | Implemented and reported verified |
| Android | Present | Present | Implemented and compiled; native interaction still needs verification |
| macOS | Present | Not integrated | Not implemented until subtask 040 |

Do not silently attempt to mount an unavailable native component. A pure
capability resolver should select the stable fallback and be unit-tested
without native modules.

## Execution plan

Status: Draft

Extend the shared preference types, defaults, option metadata, and
normalization with renderer IDs. Keep typography derivation independent from
renderer selection. Add mobile controls and migration coverage, then introduce
a single mobile markdown dispatcher used by chat and action displays.

Make code rendering an explicit prop/adapter in both markdown implementations.
For RNMD, route `fence` and `code_block` rules to the selected implementation.
For enriched markdown, retain segmentation only when an external code renderer
is selected; allow the whole document through when its built-in implementation
is selected.

Add a capability resolver with stable fallback behavior. Add desktop
persistence/UI only if question 1 resolves in favor of exposing the setting
there; otherwise keep desktop on fixed RNMD while consuming the shared code
renderer once macOS support lands.

### Implementation decisions and open questions

- Recommended defaults: `react-native-markdown-display` and
  `selectable-native`.
- Required label: `Enriched markdown (experimental)` or an equally explicit
  label containing `(experimental)`.
- Recommended fallback: syntax-highlighter for code and RNMD for markdown.
- Keep requested and effective values separate so adding a platform backend
  later automatically activates the user's original preference.
- Questions 1–4 above require confirmation before finalizing the exposed
  option set and desktop persistence surface.

### Documentation

- Update
  `packages/frontend-rn-components/docs/development/markdown-display-preferences.md`.
- Update mobile development guidance for renderer ownership, defaults, labels,
  and fallbacks.
- If desktop settings change, update
  `desktop/crystal-lattice-control-desktop-rn/docs/development/markdown-display-preferences.md`.

### Task checklist

- [ ] Resolve the exposed option set and in-scope surfaces.
- [ ] Add shared renderer IDs, defaults, labels, normalizers, and capability
      resolution.
- [ ] Migrate mobile persistence and add both settings controls.
- [ ] Introduce the markdown dispatcher and route all approved mobile surfaces.
- [ ] Make code rendering explicit in both mobile markdown implementations.
- [ ] Add desktop setting/persistence support if approved.
- [ ] Add unit, component, persistence, and native settings coverage.
- [ ] Update documentation.

### Requirement verification

- Load a typography-only saved value and verify its font/header values survive
  while both renderer fields receive defaults.
- Select each exposed renderer, close/reopen settings, relaunch the app, and
  verify the same visible value and rendered implementation.
- Verify the enriched option visibly includes `(experimental)` and is not the
  default.
- Render the same fenced code through every supported markdown/code pairing and
  verify the selected code implementation is used.
- Force an unsupported capability in a unit test and verify the documented
  stable fallback without a native-component crash.

### Additional implementation verification

- Shared package: `npm --workspace @crystal-lattice/frontend-rn-components test`.
- Mobile: focused settings/preference/message tests, `npm run tsc`, and the
  iOS/Android settings Detox scenario.
- Desktop if changed: focused global-settings and renderer tests plus the
  markdown settings XCUITest.
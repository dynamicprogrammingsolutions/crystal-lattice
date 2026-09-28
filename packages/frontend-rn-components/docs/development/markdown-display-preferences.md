# Markdown display preferences

The shared React Native component package defines normalized markdown display
preferences used by the desktop and mobile applications. The contract combines
typography choices with requested markdown and block-code renderer IDs while
leaving renderer implementation and platform persistence to each application.

The maintained API provides:

- supported 14, 15, 16, and 17 base font sizes and header profiles;
- RNMD and enriched-markdown renderer IDs, with RNMD as the default and the
  enriched option labeled `(experimental)`;
- selectable-native and syntax-highlighter code renderer IDs, with
  selectable-native as the requested default;
- the 15-point/Normal typography default;
- normalization of values received from platform persistence, including
  migration from legacy 13 to 14, 19 to 17, and typography-only records to the
  renderer defaults;
- immutable font-size and line-height presets for tiny, small, secondary,
  normal, message, large, and code text;
- explicit semantic body and H1–H6 font-size/line-height derivation;
- a pure helper that overlays a selected typography preset on a
  platform-owned color theme;
- a pure renderer capability resolver that keeps requested preferences
  separate from effective fallbacks;
- a controlled React provider and hook.

Applications own persistence and presentation. Desktop maps the preferences to
native View-menu typography values and fixed
`react-native-markdown-display`/syntax-highlighter rendering. Mobile maps the
complete record to AsyncStorage, its Global Settings modal, and a renderer
dispatcher shared by chat and markdown action displays. The shared package does
not read platform storage or depend on a markdown renderer.

`resolveMarkdownRendererPreferences` treats RNMD and syntax-highlighter as the
stable fallbacks. A known requested enriched or selectable-native renderer
remains in persisted preferences when its platform capability is absent; only
the returned effective ID changes. Unknown IDs normalize to defaults.

`DISPLAY_TYPOGRAPHY_PRESETS` is the maintained source of truth for exact
metrics. Individual roles may be tuned independently after visual review.
Tests should compare consumers with the selected preset and assert structural
relationships rather than duplicating its numeric table. Title, screen-title,
and display roles stay fixed. Normal markdown headings use explicit
hierarchical presets; Small H1-H6 use the selected base size and the message
line-height token.

Maintainer entry points:

- `src/markdownDisplayPreferences.tsx`
- `src/markdownDisplayPreferences.test.ts`
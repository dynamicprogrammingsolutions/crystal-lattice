# Markdown display preferences

The shared React Native component package defines renderer-neutral display
preferences used by the desktop and mobile applications.

The maintained API provides:

- supported 14, 15, 16, and 17 base font sizes and header profiles;
- the 15-point/Normal default;
- normalization of values received from platform persistence, including
  migration from legacy 13 to 14 and 19 to 17;
- immutable font-size and line-height presets for tiny, small, secondary,
  normal, message, large, and code text;
- explicit semantic body and H1–H6 font-size/line-height derivation;
- a pure helper that overlays a selected typography preset on a
  platform-owned color theme;
- a controlled React provider and hook.

Applications own persistence and presentation. Desktop maps the preferences to
native View-menu values and `react-native-markdown-display` styles. Mobile maps
them to AsyncStorage, its Global Settings modal, and enriched-markdown styles.
The shared package does not read platform storage or depend on either markdown
renderer.

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
# Markdown display preferences

The desktop application exposes Font Size and Markdown Headers submenus in the
native macOS View menu. Font Size offers 14, 15 (Default), 16, and 17.

`AppDelegate.mm` validates and persists the selected values in
`NSUserDefaults`, supplies them as initial properties to every main window,
and posts native change notifications. `DesktopWindowManager.mm` forwards
those notifications to each observing React root. `DesktopRoot.tsx` owns the
current in-memory values and supplies them through the shared display
preference provider. A nested theme provider overlays the selected responsive
font-size and line-height preset on the macOS semantic color theme.

`MarkdownMessageContent.tsx` maps the shared semantic body and H1–H6 metrics to
`react-native-markdown-display`. Base prose metrics belong on the renderer's
`body` style; the generic `text` style must remain color-only because the
library applies it after inherited heading styles. Putting body font metrics
on `text` makes every heading body-sized. Desktop-specific colors, spacing,
error fallback, inline code, and syntax-highlighted fenced code remain owned
by the desktop renderer.

User-message prose and inline code use `bubbleUserText`, not
`textOnPrimary`. The macOS theme builder derives the token from the accent
composited over the effective window background, preserving dark-on-light and
light-on-dark contrast even when the operator uses a custom accent. Plain user
text plus bubble-owned header/footer copy use the same token.

Message, chat, composer, attachment, and metadata styles use responsive theme
tokens. Icons, spacing, and hit targets remain fixed. Desktop panel headers,
connection/session rows, session tabs, and the chat header also consume
semantic typography and color tokens, so the selected display preset and
macOS appearance propagate through the main workspace. Session rows use
`normal` titles, `secondary` subtitles/previews, `small` IDs, and `tiny`
metadata with matching line heights. Legacy persisted 13 and 19 values migrate
to 14 and 17.

Fenced code passes the semantic `code` font size and line height plus the macOS
`Menlo` family directly to `react-native-syntax-highlighter`; placing those
values only in its `customStyle` does not affect token text. The application
uses the `feature/native-line-height` branch of
`ferenci84/react-native-syntax-highlighter`, whose lockfile entry pins the
reviewable fork commit. Raw and otherwise non-markdown message bodies consume
the semantic `message` font size and line height.

The raw assistant message uses the repository's native `MacTextView` in
read-only auto-grow mode. Read-only native instances forward wheel events to
their parent, reset their clip origin to the top, disable spelling, grammar,
replacement, data-detection, and undo services, and expose only Copy in the
context menu. The raw renderer passes its Menlo family, semantic message font
size and line height, and zero text-container inset. A production `ChatPane`
XCUITest proves that the same wheel gesture moves the transcript over both an
ordinary message and the tall raw assistant block.

The chat header session ID uses `Text selectable`. Human verification
confirmed selection works; AppKit also exposes spelling and grammar menu
items, which is accepted for this field. Clickable Sessions and home
collection rows retain their separate human gate before any selection change.

Expanded reasoning, tool results, and tool-call arguments use read-only
auto-growing `MacTextView` instances inside their existing bounded
`ScrollView`s. Wheel input therefore reaches the intentional bounded parent
instead of creating another hidden native scroll offset. Markdown fenced and
indented code retain syntax highlighting but have no nested `ScrollView`.
Long code wraps to the available message width and the block expands to its
complete content height. Its syntax highlighter uses a selectable root
`Text`, and wheel input over the block moves the transcript.

Native verification launches `DesktopMarkdownGeometryHarness` through the
application's harness initial property. The harness uses the production
markdown renderer and reports React `onLayout` measurements through
`DesktopWindowManager` because React Native macOS accessibility descendants
are not available to XCTest in this application. `MarkdownDisplayMenuUITests`
verifies persisted menu values across relaunch, actual Normal/Small heading
geometry, body geometry, and responsive footer geometry.

The Connections panel is expanded by default and its header disclosure
collapses or restores the saved-record list. Up to three records use a
natural-height non-scroll container. Larger sets use a theme-derived
three-row viewport. A non-interactive bottom fade indicates remaining content
and disappears at the real bottom. `DesktopConnectionsPanelHarness` and
`ConnectionsPanelUITests` verify natural versus bounded geometry and native
scrolling. Typography and geometry expectations are derived from the active
preset rather than copied point values.

Maintainer entry points:

- `macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`
- `macos/CrystalLatticeControlDesktopRN-macOS/DesktopMenuNotifications.h`
- `macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`
- `src/DesktopRoot.tsx`
- `src/chat/MarkdownMessageContent.tsx`
- `src/testing/DesktopMarkdownGeometryHarness.tsx`
- `src/testing/DesktopConnectionsPanelHarness.tsx`
- `src/panels/ConnectionsPanel.tsx`
- `__tests__/MarkdownMessageContent.test.tsx`
- `__tests__/DesktopMessageBubbleTypography.test.ts`
- `macos/CrystalLatticeControlDesktopRN-macOSUITests/MarkdownDisplayMenuUITests.swift`
- `macos/CrystalLatticeControlDesktopRN-macOSUITests/ConnectionsPanelUITests.swift`
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

Message, chat, composer, attachment, and metadata styles use responsive theme
tokens. Explicit panel/card titles, icons, spacing, and hit targets remain
fixed. Legacy persisted 13 and 19 values migrate to 14 and 17.

Native verification launches `DesktopMarkdownGeometryHarness` through the
application's harness initial property. The harness uses the production
markdown renderer and reports React `onLayout` measurements through
`DesktopWindowManager` because React Native macOS accessibility descendants
are not available to XCTest in this application. `MarkdownDisplayMenuUITests`
verifies persisted menu values across relaunch, actual Normal/Small heading
geometry, body geometry, and responsive footer geometry.

Maintainer entry points:

- `macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`
- `macos/CrystalLatticeControlDesktopRN-macOS/DesktopMenuNotifications.h`
- `macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`
- `src/DesktopRoot.tsx`
- `src/chat/MarkdownMessageContent.tsx`
- `src/testing/DesktopMarkdownGeometryHarness.tsx`
- `__tests__/MarkdownMessageContent.test.tsx`
- `__tests__/DesktopMessageBubbleTypography.test.ts`
- `macos/CrystalLatticeControlDesktopRN-macOSUITests/MarkdownDisplayMenuUITests.swift`
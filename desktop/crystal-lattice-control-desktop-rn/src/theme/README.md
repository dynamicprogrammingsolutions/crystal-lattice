# Desktop theming notes (macOS)

This directory builds the desktop app `Theme` (from `@crystal-lattice/frontend-rn-components`) from macOS system/semantic colors.

The intent is:

- Use native macOS semantic colors for background/text so the UI matches the user’s appearance (light/dark, high contrast, etc.).
- Use the user’s accent color as `primary`.
- Keep the shared `Theme` *interface* stable so shared RN components can be reused.

## Data sources

Native module: `DesktopWindowManager` (macOS) exposes:

- `getSystemTheme()` → returns semantic colors as strings.
- `systemThemeChanged` event → emitted when appearance or system colors change.

Implementation: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`.

Notifications observed (best-effort across SDK versions):

- `NSApplicationDidChangeEffectiveAppearanceNotification` (light/dark)
- `NSSystemColorsDidChangeNotification` (accent / system colors)
- `AppleInterfaceThemeChangedNotification` via `NSDistributedNotificationCenter` (reliable light/dark changes)

## Common macOS semantic colors

These are the usual building blocks for desktop UI. We map them into the shared `Theme` fields.

- Window background: `NSColor.windowBackgroundColor`
- Control background: `NSColor.controlBackgroundColor`
- Separator lines: `NSColor.separatorColor`
- Primary text: `NSColor.labelColor`
- Secondary text: `NSColor.secondaryLabelColor`
- Tertiary/muted text: `NSColor.tertiaryLabelColor`
- Accent: `NSColor.controlAccentColor`
- Semantic status:
  - Danger: `NSColor.systemRedColor`
  - Success: `NSColor.systemGreenColor`

If we need “material” surfaces later, consider also:

- `NSColor.textBackgroundColor`
- `NSColor.underPageBackgroundColor`
- `NSColor.controlColor`

And for strokes/fills:

- `NSColor.quaternaryLabelColor` (very subtle text)
- `NSColor.unemphasizedSelectedContentBackgroundColor` (selection backgrounds)
- `NSColor.selectedContentBackgroundColor` (selection backgrounds)
- `NSColor.keyboardFocusIndicatorColor` (focus ring)

## Shared Theme mapping (current)

Built in `buildDesktopTheme()` (`desktop/crystal-lattice-control-desktop-rn/src/theme/buildDesktopTheme.ts`).

- `theme.background` ← window background
- `theme.surface` ← control background
- `theme.border`/`theme.divider`/`theme.navBarBorder` ← separator (slightly boosted for contrast)
- `theme.primary`/`theme.navIconActive` ← accent
- `theme.primaryMuted` ← accent with alpha
- `theme.text`/`theme.textSecondary`/`theme.textMuted` ← semantic label colors

Derived values:

- `textOnPrimary` picks black/white based on accent luminance.
- `bubbleUserBg` composites the accent at a low alpha over the window
  background.
- `bubbleUserText` picks black/white against that effective composited
  background; it is intentionally independent from `textOnPrimary`.
- Other bubble backgrounds and code backgrounds are derived from accent/text
  with alpha.

Website capture roots deliberately use `buildDesktopCaptureTheme()` for a
deterministic standard-blue light/dark palette. That function is capture-only;
ordinary product roots continue to call `useDesktopTheme()` and honor the
operator's macOS accent.

## macOS sizing defaults (desktop UI)

RN macOS often renders `StyleSheet.hairlineWidth` too subtly. For desktop separators/borders we generally prefer:

- Separator/border width: `1`
- Border radius:
  - Cards/panels: `12`
  - Buttons/inputs: `8–10`
- Row padding:
  - Horizontal: `10–12`
  - Vertical: `8–10`
- Font sizes:
  - Titles: `13–14`
  - Body: `12–13`
  - Meta/secondary: `10–12`

Other useful macOS-ish sizing heuristics:

- Toolbar/tab-strip height: `44–52`
- Standard button height: `28–32`
- Compact icon button hit-target: `24–28`

These are not “final design tokens”, just pragmatic defaults for legibility.

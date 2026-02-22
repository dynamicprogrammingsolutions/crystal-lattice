# Desktop theming: separate palettes + macOS semantic colors

Desktop and mobile currently share the same concrete color palette via `@crystal-lattice/frontend-rn-components`. This task decouples the *palette* (app-owned) from the *theming interface* (shared), and upgrades the desktop app to use macOS semantic system colors (including dynamic light/dark switching and accent color).

Parent Task: tasks/20260202-desktop-macos-frontend/000-main.md

## Goals

- Keep a shared theming interface (`Theme`, `ThemeProvider`, `useTheme`) so shared RN components can style consistently.
- Allow mobile and desktop to use different palettes.
- Desktop uses macOS semantic colors for background/text/separators and uses the user accent color for `primary`.
- Theme updates while the app is running when:
  - macOS light/dark mode changes.
  - macOS accent color changes.
- Improve desktop contrast (borders/separators).

## Current state

- Shared palette and `useSystemTheme()` live in `packages/frontend-rn-components/src/theme.ts`.
- Desktop uses it directly in `desktop/crystal-lattice-control-desktop-rn/App.tsx`.
- Some desktop separators/borders use `StyleSheet.hairlineWidth` and appear too low-contrast.

## Plan

### 1) Make palettes app-owned

- Refactor `@crystal-lattice/frontend-rn-components` to export only:
  - `type Theme`
  - `ThemeProvider`
  - `useTheme`
- Move the iOS-inspired `lightTheme`/`darkTheme` definitions into the mobile app:
  - `mobile/crystal-lattice-control-rn/src/theme.ts`
- Replace desktop’s use of shared `useSystemTheme()` with a desktop-only theme hook.

### 2) Desktop: macOS semantic colors + accent color (native)

Implement a native API on macOS (can be added to the existing `DesktopWindowManager` event emitter to avoid Xcode project churn):

- JS-callable: `getSystemTheme(): Promise<SystemThemePayload>`
- JS event: `systemThemeChanged` with the same payload

Payload should include (as sRGB strings like `#RRGGBB` or `rgba(...)`):

- `appearance`: `"light" | "dark"`
- `accent`: `NSColor.controlAccentColor`
- `windowBackground`: `NSColor.windowBackgroundColor`
- `controlBackground`: `NSColor.controlBackgroundColor` (or `textBackgroundColor` if preferred)
- `separator`: `NSColor.separatorColor`
- `text`: `NSColor.labelColor`
- `textSecondary`: `NSColor.secondaryLabelColor`
- `textMuted`: `NSColor.tertiaryLabelColor`
- `danger`: `NSColor.systemRedColor`
- `success`: `NSColor.systemGreenColor`

Listen for system changes and emit `systemThemeChanged`.

In practice, these were the only notifications that reliably fired under RN macOS in this app:

- `AppleInterfaceThemeChangedNotification` (via `NSDistributedNotificationCenter`) for light/dark.
- `NSSystemColorsDidChangeNotification` for accent + other system color updates.

### 3) Desktop: build a `Theme` from semantic colors

- Add `desktop/crystal-lattice-control-desktop-rn/src/theme/useDesktopTheme.ts`:
  - Calls native `getSystemTheme()` on mount.
  - Subscribes to `systemThemeChanged` and updates state.
  - Returns a fully built `Theme` object.

- Add `desktop/crystal-lattice-control-desktop-rn/src/theme/buildDesktopTheme.ts`:
  - Maps semantic colors into existing `Theme` fields.
  - Derives `primaryMuted`, bubble backgrounds, etc. from the accent color.
  - Chooses `textOnPrimary` (black/white) based on accent luminance.
  - Boosts `border/divider` slightly (mix with `text`) if macOS separator is too subtle.

Update desktop entry points to use the new theme:

- `desktop/crystal-lattice-control-desktop-rn/App.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/windows/ConnectionEditorWindow.tsx`

### 4) Improve desktop separator visibility

- For desktop-only UI, use `1` instead of `StyleSheet.hairlineWidth` for borders on macOS.
- Apply to high-visibility separators:
  - `desktop/crystal-lattice-control-desktop-rn/src/ui/PanelHeader.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/SessionTabs.tsx`
  - Panels that render list rows / input borders.

### 5) Tests / mocks

- Update `desktop/crystal-lattice-control-desktop-rn/jest.setup.js` mocks:
  - Stop mocking `useSystemTheme()`.
  - If needed, mock `DesktopWindowManager.getSystemTheme()`.

## Acceptance checklist

- Desktop uses macOS background/text/separator colors (looks native).
- Changing macOS appearance (light/dark) while the app is open updates desktop colors.
- Changing macOS accent color while the app is open updates `primary`-colored elements.
- Desktop separators and borders are visibly higher contrast.

## References

- Desktop theming notes: `desktop/crystal-lattice-control-desktop-rn/src/theme/README.md`

## Implementation notes (done)

- Shared theme interface stays in `packages/frontend-rn-components/src/theme.ts` (no concrete palettes exported).
- Mobile owns its own palettes + `useSystemTheme()` in `mobile/crystal-lattice-control-rn/src/theme.ts`.
- Desktop theme comes from macOS semantic colors via `DesktopWindowManager.getSystemTheme()` and `systemThemeChanged`.
- Final/native event sources:
  - Light/dark: `AppleInterfaceThemeChangedNotification` (distributed)
  - Accent/system colors: `NSSystemColorsDidChangeNotification`
- Semantic colors are resolved as sRGB strings under an explicit `NSAppearance` created from `AppleInterfaceStyle` using `performAsCurrentDrawingAppearance:`.
- Removed experimental/unused appearance observers (app/window effective appearance) once it was clear they didn’t fire in this setup.

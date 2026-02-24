# Subtask: Desktop tab strip styles + View menu toggle

Add a user-selectable tab strip style on macOS (two variants) and a native “View” menu item to switch between them.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/050-desktop-shell-layout.md`
- `tasks/20260202-desktop-macos-frontend/060-desktop-connections-panel.md`

## Status

- [x] Done

Implemented in:

- Tab strip variants: `desktop/crystal-lattice-control-desktop-rn/src/tabs/SessionTabs.tsx:1`
- Variant type + parsing: `desktop/crystal-lattice-control-desktop-rn/src/tabs/tabStripStyle.ts:1`
- Root state + event subscription: `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`
- Initial props plumbing: `desktop/crystal-lattice-control-desktop-rn/App.tsx:1`
- Native View menu + persistence + event emission: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm:1`

## Background

The current tab strip is implemented in JS as a custom component:

- `desktop/crystal-lattice-control-desktop-rn/src/tabs/SessionTabs.tsx:1`

We want to keep this implementation (no native `NSTabViewController` yet), but restyle it to look more desktop-native and make the style switchable via the macOS menubar.

## Requirements

### 1) Two tab strip visual styles

Implement selectable designs:

1) **Toolbar Tabs (Option A)**
   - Looks like a macOS toolbar tab strip (Finder/Xcode-ish).
   - Active tab feels “raised” (lighter surface + subtle shadow).
   - Inactive tabs are flatter; hover is subtle.
   - Close button is only visible when the tab is active or hovered.

2) **Code Tabs (Option C)**
   - Looks like a VS Code / editor tab strip.
   - Rectangular tabs, dense spacing, separators between tabs.
   - Active tab uses stronger background; optional top accent.
   - Close button is always visible (but low-contrast until hover).

3) **Underline Tabs (Option B)**
   - Minimal tab strip with an underline indicator for the active tab.
   - No pill borders; low visual weight.
   - Close button appears only when the tab is active or hovered.

4) **Rounded Pills (Option D)**
   - Modern pill-style tabs with subtle borders.
   - Active tab uses a stronger outline and/or fill.
   - Close button appears only when the tab is active or hovered.



### 2) Toggle via native View menu

Add a menubar item:

- `View` → `Tab Strip Style` →
  - `Toolbar Tabs`
  - `Code Tabs`
  - `Underline Tabs`
  - `Rounded Pills`

The two items behave like a radio group:

- Exactly one is checked at a time.
- Selecting an item immediately updates the JS-rendered tab strip.

This is the “custom menu item” integration for Phase 5: a non-system `NSMenuItem` whose action is handled by app code and forwarded into React Native.

### 3) Persist selection

- Selected style persists across app restarts.
- Default on first run: `Toolbar Tabs`.

### 4) Non-goals

- No switch to a native `NSTabViewController` implementation in this subtask.
- No rework of tab semantics (open/close behavior, mounted-but-hidden panes). Styling only.

## Implementation plan

### 1) Define a tab strip style enum + default

- Add a desktop-local type:
  - `type TabStripStyle = 'toolbarTabs' | 'codeTabs'`
- Default: `'toolbarTabs'`.

Recommended placement:

- `desktop/crystal-lattice-control-desktop-rn/src/tabs/tabStripStyle.ts:1` (or similar).

### 2) Update `SessionTabs` to support both variants

- Extend `SessionTabsProps` with a `styleVariant: TabStripStyle` prop.
- Make `createStyles(theme, styleVariant)` return variant-specific styles.
- Variant-specific behaviors:
  - Option A: close button opacity/visibility rules (active/hover only).
  - Option C: separators, denser paddings, always-visible close.

Target file:

- `desktop/crystal-lattice-control-desktop-rn/src/tabs/SessionTabs.tsx:1`

### 3) Store and drive style selection from `DesktopRoot`

- Add `tabStripStyle` state to `DesktopRoot`.
- Pass `tabStripStyle` down to `SessionTabs`.
- Initialize from native-provided initial props (preferred) or a JS storage fallback.

Target file:

- `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`

### 4) Implement a native View menu submenu + actions

We already have a macOS storyboard defining the app menu:

- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/Base.lproj/Main.storyboard:1`

Add the new View submenu items either:

- **A) Programmatically** in `AppDelegate` by locating the `View` menu and inserting a `Tab Strip Style` submenu (preferred: less storyboard XML churn), or
- **B) In storyboard** and connect the menu items’ actions to the `AppDelegate`.

Native responsibilities:

- Create two menu items that call app-defined selectors.
- Maintain checkmarks (radio behavior).
- Persist selection in `NSUserDefaults`.
- Provide initial selection to JS at startup.

Target file:

- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm:1`

### 5) Forward native menu selection into React Native

Implement a small native bridge so the menu selection updates JS state.

Recommended approach (works with the current app setup and New Architecture builds):

- Create an `RCTEventEmitter` module (e.g. `DesktopMenuEvents`) that emits:
  - `tabStripStyleChanged` with `{ style: 'toolbarTabs' | 'codeTabs' }`
- In `AppDelegate`, when a menu item is selected:
  - Update `NSUserDefaults`
  - Update menu checkmarks
  - Emit `tabStripStyleChanged` to JS
- Also, on startup:
  - Read persisted style from `NSUserDefaults`
  - Include it in `self.initialProps` (e.g. `{ initialTabStripStyle: 'toolbarTabs' }`)

JS responsibilities:

- Read `initialTabStripStyle` from root component props and seed `DesktopRoot` state.
- Subscribe to `DesktopMenuEvents` via `NativeEventEmitter` to update state.

Native files (proposed):

- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopMenuEvents.h:1` (new)
- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopMenuEvents.mm:1` (new)

JS files (proposed):

- `desktop/crystal-lattice-control-desktop-rn/App.tsx:1` (accept initial props + pass down)
- `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1` (event subscription)

### 6) Manual verification checklist

- Launch app → default style is Toolbar Tabs.
- `View → Tab Strip Style → Code Tabs` updates the strip immediately.
- Checkmark switches correctly.
- Relaunch app → previously selected style restores.
- Tab selection/close behavior still works.

## Notes / pitfalls

- Keep menu integration macOS-only.
- Ensure the menu event emission works when the RN bridge isn’t ready yet:
  - Emitting should be a no-op until the event emitter module is initialized.
  - Initial style should come from `initialProps` so the first render matches the menu checkmark.

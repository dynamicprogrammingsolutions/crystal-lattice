# Native elements notes (RN macOS)

This file records *hints* and research notes about which “native-ish” UI elements are available when building a desktop app with React Native macOS.

These are not final decisions; they’re intended to reduce rediscovery and keep options open.

## Likely available in RN macOS (JS-accessible)

RN macOS adds macOS-specific props/events to core primitives (notably `View`) that can help the desktop app feel more native without adopting an external UI toolkit.

Examples of capabilities to explore/validate in the chosen RN macOS version:

- Focus ring / focus behaviors (`focusable`, `enableFocusRing`)
- Keyboard shortcut handling via `keyDownEvents` / `keyUpEvents` (opt-in list)
- Mouse affordances: hover enter/leave, double click
- Tooltips (`tooltip`)
- Cursor control (`cursor`)
- Drag and drop (types + handlers)
- Vibrancy / blending with macOS materials (`allowsVibrancy`)

Potential usage in this project:

- Session tabs:
  - hover affordances (close button reveal)
  - keyboard navigation
  - tooltips for long session titles
- Menus:
  - hover highlight
  - keyboard-driven selection

## Menus / popovers (native AppKit)

macOS has native menu/popover primitives (`NSMenu`, `NSPopover`). RN macOS does not appear to expose these as first-class declarative JSX primitives.

Implications / design guidance:

- Prefer a pluggable abstraction for “menu surface” in shared components.
  - Phase 5 can use a JS overlay-based dropdown.
  - A future macOS-specific implementation could use a native module for `NSMenu`/`NSPopover`.

There are libraries and experiments in the ecosystem, but stability/maintenance varies; treat as optional.

## “Native selects” for settings

If the desktop UI needs a native-ish select control, investigate `@react-native-picker/picker` support for macOS.

Design guidance:

- Share *settings model* and field descriptors.
- Keep the field renderer swappable:
  - mobile: switch/inputs and modal panels
  - desktop: picker/menus and dropdown panels
  - future: a truly native preferences window (likely AppKit)

## Preferences / Settings window

macOS has strong conventions for “Preferences…” UI, and many apps implement it as a separate window.

Guidance:

- Avoid hard-coding “settings == modal” in shared components.
- Prefer:
  - shared: load/patch/revert logic
  - platform: window/panel/presentation

## Web search note

RN macOS docs evolve; version compatibility details (especially init/scaffolding) should be verified when implementing `tasks/20260202-desktop-macos-frontend/020-rn-macos-scaffold-and-version.md`.

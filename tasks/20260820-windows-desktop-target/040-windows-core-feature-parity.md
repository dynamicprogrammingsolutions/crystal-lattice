# Complete Core Single-Window Windows Feature Parity

Make the primary Windows window usable for normal Crystal Lattice work before
native secondary-window and transient-host parity.

## Requirements checklist

- [ ] Connections, sessions, chat, streaming, cancellation, settings, plugins, actions, notifications, persistence, caches, and reconnection work in the Windows main window.
- [ ] Windows attachment selection works through a maintained native or supported platform adapter.
- [ ] Composer and message text behavior provide the required focus, programmatic text, selection, sizing, copy, and keyboard behavior without importing the macOS text-view package.
- [ ] Transcript scrolling, range navigation, bottom-follow behavior, restoration, and metrics work reliably on Windows.
- [ ] Menus, dropdowns, action dialogs, and transient surfaces have accessible functional single-window implementations.
- [ ] Theme, high contrast, text scaling, keyboard navigation, focus visibility, shortcuts, and accessibility roles are Windows-appropriate.
- [ ] Dependency platform support is verified through actual Windows builds and behavior.
- [ ] Shared and macOS behavior remain green.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/030-bootstrap-react-native-windows-host.md

## Research-derived implementation guidance

- Reuse the existing checkbox fallback when it meets Windows accessibility.
- Replace the current non-macOS select text-only fallback with an interactive Windows implementation.
- Start `DesktopTextView.windows.tsx` with core `TextInput`; add a Fabric component only for behavior proven unavailable.
- Prefer scroll-event/layout-derived metrics where reliable; add a Windows native metrics module for the existing transcript invariants when necessary.
- Use shared React overlays/modals for the first transient UI implementation because current RNW New Architecture does not expose the old Windows `Flyout`/`Popup` components.

## Execution plan
Status: Draft

Audit each user workflow and dependency on Windows. Implement platform adapters
and functional in-window presentation, adding native TurboModules/components
only where required by verified behavior. Extend shared tests with Windows
contract cases and add deterministic Windows integration harnesses for text,
scroll, transient UI, attachments, persistence, and backend communication.

### Implementation decisions and open questions

- Functional parity precedes native visual parity.
- Do not weaken transcript invariants to avoid a Windows native metrics implementation.
- Preserve Windows conventions for keyboard, menus, focus and high contrast rather than cloning macOS appearance.
- Treat unsupported third-party packages as replacement decisions, not permanent test mocks.

### Documentation

- Document current Windows-supported workflows and limitations in Windows user docs.
- Document adapter ownership, dependency support, text/scroll implementation, and diagnostics in Windows/shared development docs.

### Task checklist

- [ ] Audit and classify every desktop dependency on Windows.
- [ ] Implement file picker, theme, text-view, select/checkbox, and scroll adapters.
- [ ] Implement functional in-window menus, dialogs, and transient surfaces.
- [ ] Complete connection/session/chat/settings/plugins/actions/notification workflows.
- [ ] Add keyboard, high-contrast, text-scale, and accessibility behavior.
- [ ] Add deterministic integration harnesses and production selectors.
- [ ] Run Windows and macOS regression suites.

### Requirement verification

- Complete a realistic user flow from connection creation through streamed response, settings/actions, attachments, and relaunch.
- Verify composer and transcript behavior with long sessions and keyboard-only input.
- Verify high contrast, 200% scaling, accessibility tree, and focus order.
- Verify no shared Windows path imports macOS-only native packages.

### Additional implementation verification

- Test network loss/reconnect, sleep/resume, clipboard, Unicode, large attachments, and slow streaming.
- Compare Windows behavior with macOS requirements while documenting intentional platform differences.
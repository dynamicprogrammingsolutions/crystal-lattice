# Implement Windows Native Window, Menu, And Transient-Host Parity

Implement the Windows-native host capabilities needed for secondary React
windows, multiple main windows, application commands, anchored transient
surfaces, lifecycle, theme, and event parity.

## Requirements checklist

- [ ] A supported Windows App SDK/C++ host can create, focus, reuse, close, and release secondary windows containing registered React roots.
- [ ] Existing secondary surfaces such as connection editor, agent picker, settings, plugins, snapshots, attachment metadata, server settings, and application-action dialogs have approved Windows presentations.
- [ ] Multiple main-window behavior, application activation/reopen, shutdown, focus, and window restoration are defined and verified.
- [ ] Windows application menus/command surfaces and keyboard shortcuts expose the required production commands.
- [ ] Popover/transient behavior has Windows-appropriate anchoring, dismissal, focus, cancellation, and accessibility semantics.
- [ ] Native-to-React events preserve submit/cancel/theme/menu/window lifecycle contracts without duplicate or missing events.
- [ ] The implementation uses supported RNW New Architecture mechanisms and does not depend on Paper, unsupported RNW 0.81, or a private framework fork without approval.
- [ ] Functional fallback presentation remains available when a native transient surface is not technically maintainable.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/040-windows-core-feature-parity.md

## Highest-risk spike

Before implementing the generic manager, prove this minimal flow:

```text
Open Connection Editor
→ create a separate Windows App SDK window
→ mount the registered ConnectionEditorWindow React root
→ pass initial props
→ submit or cancel
→ emit exactly one event
→ close and release the root/window
```

If supported public RNW APIs cannot implement this reliably, stop and present
the evidence plus recommended fallback architecture before proceeding.

## Execution plan
Status: Draft

Define platform-neutral window/transient/menu contracts from the existing
semantic behavior, then implement the Windows host in C++/WinRT using current
public RNW/Windows App SDK APIs. Complete the single-window secondary-root spike
first. Generalize only after lifecycle, theme, event, and teardown tests pass.
Use in-window React overlays for surfaces where current RNW native composition
cannot provide a maintainable anchored host.

### Implementation decisions and open questions

- Do not mechanically reproduce `NSWindow` and `NSPopover`; preserve user outcome using Windows conventions.
- Determine whether all secondary surfaces need real windows or whether some should remain accessible main-window dialogs.
- Keep native root/window registration deterministic and centralized.
- Avoid arbitrary XAML-in-Fabric integration unless current official support has become production-ready and the spike proves it.
- Ask before adopting a custom RNW fork, unsupported API, or process-per-window design.

### Documentation

- Document the current Windows host architecture, root/window registry, lifecycle, events, menus, fallback rules, and debugging in Windows development docs.
- Update shared platform-contract docs when native findings refine cross-host semantics.
- User docs should describe Windows behavior directly without comparing implementation internals to macOS.

### Task checklist

- [ ] Write semantic parity matrix for each current macOS window/menu/popover behavior.
- [ ] Complete and verify the Connection Editor secondary-window spike.
- [ ] Implement generic secondary React-window hosting.
- [ ] Port or adapt all approved secondary surfaces.
- [ ] Implement multiple-main-window lifecycle if retained.
- [ ] Implement Windows command/menu/shortcut surfaces.
- [ ] Implement native or approved fallback transient surfaces.
- [ ] Verify event, focus, dismissal, theme, teardown, and memory behavior.
- [ ] Run Windows core and macOS regression tests.

### Requirement verification

- Exercise every secondary surface through production user actions.
- Verify repeated open/focus/close cycles do not duplicate React roots/events or leak windows.
- Verify keyboard, accessibility, multi-monitor, DPI, theme, application hide/minimize, and shutdown behavior.
- Verify approved fallbacks are functional and documented rather than silent.

### Additional implementation verification

- Stress open/close and multiwindow operation while streaming messages.
- Verify window placement on changed monitor topology and scaling.
- Inspect native diagnostics for leaked host objects or roots after teardown.
# Window and popover conventions

Current macOS conventions:

| Interaction | Convention |
|---|---|
| Anchored transient menu | Native `NSPopover` |
| Server or session settings | Separate React window |
| Direct action modal response | Separate React action-display window |
| Notification modal request | Inline fallback in message/detail rail |
| Connection/application banner | Message/detail-area rail |
| Session inline/banner/modal | Active ChatPane rail |

Do not introduce React Native `Modal` for desktop notification flows; the
current macOS runtime does not provide a reliable implementation. Direct action
modal responses use `ActionDisplayWindow`, opened through the generic
`DesktopWindowManager.openReactWindow()` path. Its body is bounded and
scrollable for lengthy content.
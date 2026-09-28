# Window and popover conventions

Current macOS conventions:

| Interaction | Convention |
|---|---|
| Anchored transient menu | Native `NSPopover` |
| Server or session settings | Separate React window |
| Direct action modal response | Separate React action-display window |
| Notification modal request | Inline fallback in message/detail rail |
| Global application settings | Separate keyed React window opened from the application menu |
| Permanent local session note | Separate keyed React window |
| Connection/application banner | Message/detail-area rail |
| Session inline/banner/modal | Active ChatPane rail |
| Compact config dropdown or rich session-action list | Native `NSPopover` |

Do not introduce React Native `Modal` for desktop notification flows; the
current macOS runtime does not provide a reliable implementation. Direct action
modal responses use `ActionDisplayWindow`, opened through the generic
`DesktopWindowManager.openReactWindow()` path. Its body is bounded and
scrollable for lengthy content.

Global Settings and the View-menu `Follow Active Tab in Sessions List` and
`Switch Connection with Active Tab` items read and write their respective
native preferences. Notifications update every open main root and the
Settings root. Missing values default to Follow On and Switch Connection Off;
explicitly stored Follow values are retained.
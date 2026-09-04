# Window and popover conventions

Current macOS conventions:

| Interaction | Convention |
|---|---|
| Anchored transient menu | Native `NSPopover` |
| Server or session settings | Separate React window |
| Global application settings | Separate keyed React window opened from the application menu |
| Permanent local session note | Separate keyed React window |
| Notification/action modal request | Inline fallback in message/detail rail |
| Connection/application banner | Message/detail-area rail |
| Session inline/banner/modal | Active ChatPane rail |
| Compact config dropdown or rich session-action list | Native `NSPopover` |

Do not introduce React Native `Modal` for desktop notification flows; the
current macOS runtime does not provide a reliable implementation.
# Sessions-actions technical specification

The Sessions action surface contains:

- Server settings;
- Refresh sessions;
- New session;
- Notifications, when notification history is supported on the surface;
- plugin-contributed application actions.

Complete-menu and pinned representations invoke the same stable action
identity. Pin state is frontend-local and connection-scoped.

Plugin dialogs use the common action parameter and form model. Returned
displays use the action-display contract. Platforms may use native anchored
menus or other standard transient controls while retaining the same action
model and accessibility semantics.

Session actions are mutating by default. An action may declare
`mutates_session: false` when it only inspects effective state or returns a
transient display. A non-mutating action:

- may return a display-only result without native messages or session metadata;
- receives the same resolved session configuration and request-initialization
  context as a mutating action;
- cannot return session-mutation fields;
- does not require a writable snapshot selection;
- does not rebuild, persist, touch the modified time, or report the session as
  updated.

Existing actions that omit the declaration retain their rebuild, persistence,
conflict, and refresh behavior.

The Notifications action opens the scope-appropriate compact history surface
and may expose an active or waiting-for-input count badge.
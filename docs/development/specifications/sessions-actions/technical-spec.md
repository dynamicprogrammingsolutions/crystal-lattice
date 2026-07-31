# Sessions-actions technical specification

The Sessions action surface contains:

- Server settings;
- Refresh sessions;
- New session;
- plugin-contributed application actions.

Complete-menu and pinned representations invoke the same stable action
identity. Pin state is frontend-local and connection-scoped.

Plugin dialogs use the common action parameter and form model. Returned
displays use the action-display contract. Platforms may use native anchored
menus or other standard transient controls while retaining the same action
model and accessibility semantics.
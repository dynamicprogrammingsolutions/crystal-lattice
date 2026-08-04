# session-archive-app

Application-level plugin that archives and restores sessions.

The plugin stores state under `metadata.archived` by default. Set
`application.session_archived_metadata_key` to use another metadata key. The
same configured key drives its immutable mutation, rich ordinary row action,
and `archive_state` Boolean filter.

It contributes:

- `toggle_session_archived`, an application action and ordinary
  `session_list_action`;
- a rich `toggle` presentation with primary active and muted inactive tones;
- `archive_state`, a Boolean `session_list_filter` defaulting to `false`.

Consequently, archived sessions are hidden by default when the plugin is
enabled. Choose **Any** in the filter to show every session, or **Archived** to
show only archived sessions. Sessions with no stored archive metadata behave as
not archived.

When `session-ordering-buckets-app` is also enabled, archived sessions updated
within the last 60 days sort below non-archived sessions. It reads this
plugin's same `application.session_archived_metadata_key`; archived sessions
older than 60 days retain ordinary recency/pin ordering.

Like all rich session-list actions, frontends that do not implement the rich
toggle still execute the ordinary action (`dialog.kind: "none"`).

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
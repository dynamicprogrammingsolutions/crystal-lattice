# session-status-app

Application-level plugin for assigning and filtering session workflow status.

The plugin stores status under `metadata.status` by default. Set
`application.session_status_metadata_key` to use a different metadata key.
The same resolved key drives the action form, mutation, event, filter, and
session-list footer label.

Built-in statuses are:

| Value | Label | Tone |
| --- | --- | --- |
| `todo` | To do | `muted` |
| `in_progress` | In progress | `primary` |
| `blocked` | Blocked | `danger` |
| `done` | Done | `success` |

It contributes:

- `set_session_status`, an application action;
- an ordinary `session_list_action` select form using that action;
- `session_status`, a multi-select `session_list_filter`;
- a session-list trigger that derives a human-readable
  `session_status_label`;
- `session_status_meta`, a `session_list_field` rendered at the end of
  `presentation.meta`.

Missing status behaves as `todo` without writing metadata. The filter defaults
to Any (`[]`), so enabling the plugin does not hide existing sessions. The
footer therefore renders `Status: To do` for an older session without stored
status. Its order is `100`, after the built-in Updated, Created, and message
count fields.

The footer is enabled by default. Set the application-level default at startup:

```json
{
  "application": {
    "session_status_show_in_session_list_footer": false
  }
}
```

The plugin exposes a server-scoped checkbox with the same key. A persisted
server setting overrides the application default; deleting the server setting
returns to that configured default.

The ordinary form is the compatibility presentation. A later rich-action
extension can enhance the same stable action with immediate list selection
without changing the action or filter IDs.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
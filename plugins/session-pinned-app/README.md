# session-pinned-app

Application-level plugin that toggles and filters pinned state on sessions.

The plugin stores the state under `metadata.pinned` by default. Set
`application.session_pinned_metadata_key` to use another metadata key. The
same resolved key drives the mutation, rich ordinary row action state, and
the declarative filter.

It contributes:

- `toggle_session_pinned`, an application action and ordinary
  `session_list_action` with a rich toggle presentation;
- `pinned_state`, a Boolean `session_list_filter` with `missing_value: false`;
- Not pinned and Pinned choices with muted and yellow `highlight` semantic
  tones.

The rich toggle declares both `header_trailing` and `actions_bar` placements:
it restores the title-corner pin control while still allowing the user to
choose whether it appears in their action bar. The rich toggle is initially
pinned when the user has no saved action-bar preference. An existing saved
preference, including an intentionally empty one, remains authoritative.
Frontends without rich-toggle or header-placement support still retain the
ordinary action-menu behavior and run the action immediately through its
ordinary `dialog.kind: "none"` behavior.

The filter defaults to Any (`null`), so merely enabling this plugin does not
change the visible session list. Sessions without pin metadata behave as not
pinned.

Consumers should treat `pinned_state` as the stable filter ID and
`toggle_session_pinned` as the stable action and UI-element ID.

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

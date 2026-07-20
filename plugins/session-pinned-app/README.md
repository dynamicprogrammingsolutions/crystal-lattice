# session-pinned-app

Application-level plugin that toggles and filters pinned state on sessions.

The plugin stores the state under `metadata.pinned` by default. Set
`application.session_pinned_metadata_key` to use another metadata key. The
same resolved key drives both the mutation and the declarative filter.

It contributes:

- `toggle_session_pinned`, the existing application action and legacy
  session-row pin control;
- `pinned_state`, a Boolean `session_list_filter` with `missing_value: false`;
- Not pinned and Pinned choices with muted and warning semantic tones.

The filter defaults to Any (`null`), so merely enabling this plugin does not
change the visible session list. Sessions without pin metadata behave as not
pinned.

The legacy pin-specific row control remains until the rich ordinary-action
presentation is introduced. Consumers should treat `pinned_state` as the
stable filter ID.

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

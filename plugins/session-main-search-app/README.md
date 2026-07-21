# session-main-search-app

Application plugin that contributes the ordinary declarative main search and
focused text filters for session lists.

The plugin does not implement matching itself. Python and TypeScript consumers
interpret the shared `session_list_filter` contract.

It contributes one main search:

```python
{
    "ui_type": "session_list_filter",
    "id": "session_search",
    "label": "Search",
    "icon": "search",
    "order": 0,
    "type": "text",
    "match": "contains",
    "data": [
        "session_id",
        "preview",
        "first_user_message",
        "presentation.title",
        "presentation.subtitle",
        "presentation.meta",
    ],
    "case_sensitive": False,
    "default": "",
    "main_search": True,
}
```

It also contributes two ordinary filters:

- `session_title_search`, over displayed `presentation.title` and
  `presentation.subtitle`;
- `session_first_message_search`, over the complete first non-empty user
  message.

The complete first message is exposed as a `first_user_message` summary field
by the plugin's deterministic `trigger: "session_list"` action. This avoids the
80-character list-preview limit while keeping the existing preview path in the
broad main search for compatibility. System messages are skipped, whitespace
is normalized, and sessions without a user message contribute an empty value.

Python terminal queries and TypeScript clients interpret the shared filter
contract. Terminal free-text search requires one valid plugin-declared main
search. Mobile and desktop use this declaration when available and retain a
small local fallback search when no unambiguous declaration is available.

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
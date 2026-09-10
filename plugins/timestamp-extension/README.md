# timestamp-extension

Timing-related feature plugins.

## TimestampExtension

- Adds a footer timestamp derived from `metadata.timestamp`.
- Timestamps are allocated when:
  - A new user/system message is appended to the session (`to_native_messages`).
  - An assistant message is received from the provider (`finalize`).

### Known limitation: tool-result timestamps

Tool results receive timestamps **only after the session is persisted and reloaded**, not inside the live `tool_results` event stream. This happens because `to_native_messages` runs inside `add_message`, and tool-result messages are added to the session after the `tool_results` event has already been emitted. All providers are affected equally.

## DurationExtension

- Adds per-request `duration` (start/end timestamps + elapsed time).
- Adds per-turn cumulative `turn duration` similar to OpenRouter usage turn totals.
- Adds cumulative `total duration` for all LLM/provider requests retained in
  the session history. This total excludes tool execution, human activity, and
  the wall-clock age of the session.
- Exposes the formatted total in the chat status bar. Set
  `duration_extension_show_status_total` to `false` to hide the status total
  independently from the message footers controlled by
  `duration_extension_show_duration`.

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

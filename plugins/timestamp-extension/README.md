# timestamp-extension

Timing-related feature plugins.

## TimestampExtension

- Adds a footer timestamp derived from `metadata.timestamp`.
- Timestamps are allocated when:
  - A new message is appended to the session
    (`prepare_appended_message`, dispatched by `AgentCore.add_message`
    before the message is converted to provider-native form — so the
    timestamp persists into native `_metadata` and survives
    native-history rebuilds). Existing timestamps are never overwritten.
  - An assistant message is received from the provider (`finalize`).

### Known limitation: tool-result timestamps in the event stream

Tool results are timestamped when they are appended to the session, so the
live `session_checkpoint` and the persisted session carry the timestamp.
The `tool_results` event payload is built from the tool message before
`add_message` runs, so that event stream still predates the stamp. All
providers are affected equally.

## DurationExtension

- Adds per-request `duration` (start/end timestamps + elapsed time) on
  assistant messages.
- Adds per-turn cumulative `turn duration` similar to OpenRouter usage
  turn totals.
- Adds per-tool-call `duration` on tool-result messages, measured in
  `finalize_tool_call` from the framework-provided context facts
  (`started_at`/`finished_at`, wall and monotonic). The framework provides
  only raw timestamps; this plugin owns the measurement.
- Adds per-turn cumulative `tool turn` duration: the sum of tool-result
  durations since the last turn separator (a user/system message or an
  assistant message without tool calls) plus the current call, scanned from
  the session history available in the tool-call context. Assistant LLM
  durations never leak into the tool turn.
- Message footers (`duration:`, `turn duration:`, `turn TPS:`,
  `tool turn:`) are gated by the `duration_extension_show_duration`
  config flag.

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

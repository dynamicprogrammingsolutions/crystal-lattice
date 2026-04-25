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

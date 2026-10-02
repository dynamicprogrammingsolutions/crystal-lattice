# Chat history range loading

`ChatController` loads message history windows from
`GET /sessions/{id}/messages` using Python-style slice bounds. Frontends
express the window as range text (`startText`/`endText`, e.g. `-50:` for the
last 50 messages) and translate it with `parseIndexRangeText`; suffix
windows follow the session tail (`followTail`) and keep only the requested
number of messages in memory (`maxMessages`).

## Default-range fallback

Sessions can be rewritten underneath a client — most commonly by
compaction, which replaces a large message range with a summary. An
absolute range such as `100:150` can then start past the end of the
rewritten history; the server clamps both bounds to the message count and
rejects the request with HTTP 400 `range selects no messages`.

When a load for any range other than the default fails with that error,
`ChatController` automatically retries once with the default suffix window
(`DEFAULT_HISTORY_RANGE`, the last 50 messages, `-50:`). The fallback:

- retries exactly once per load call (the default window itself never
  falls back),
- updates the controller's `historyRange` to the default window, and
- notifies the consumer via the `onRangeFallback` option or
  `setRangeFallbackListener`, passing the effective range.

`isRangeSelectsNoMessagesError(err)` performs the error detection: it
matches the server detail substring on the transport's `HTTP 400 ...`
message, so both the fetch and bridge transports are covered.

Consumers must sync their own range state when notified. The desktop
`ChatPane` updates its range texts (the messages-cache persist effect then
stores them), and the mobile `SessionChatScreen` updates its texts and
calls its history-range save, so the recovered window survives reloads and
restarts instead of reapplying the invalid range.

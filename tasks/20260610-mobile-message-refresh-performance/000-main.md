# Mobile Message Refresh Performance

Break the mobile message refresh slowdown into separable fixes. The first priority is bridge request head-of-line blocking; later work should reduce redundant payload fields and make UI schema/settings freshness event-driven rather than tied to every message reload.

## Task checklist

- [x] `tasks/20260610-mobile-message-refresh-performance/010-bridge-concurrent-proxied-requests.md`
- [ ] `tasks/20260610-mobile-message-refresh-performance/020-message-list-frontend-projection.md`
- [ ] `tasks/20260610-mobile-message-refresh-performance/030-session-metadata-ui-schema-invalidation-events.md`
- [ ] `tasks/20260610-mobile-message-refresh-performance/040-frontend-refresh-orchestration.md`
- [ ] `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`

## Background

Manual message reload in the React Native mobile app can become slow for large sessions due to an accumulation of smaller issues:

- The bridge currently serializes proxied HTTP requests on one app channel. In a diagnostic burst, six schema/settings requests were processed before the `/messages` request, delaying the start of the message response by about 2 seconds.
- The message list endpoint currently returns full `Message.to_dict()` payloads, including full `metadata`, `toolResult`, and `content`. For mobile display, known redundant fields can be stripped in an optimized frontend projection.
- UI schema/settings refreshes were added to message reload because session metadata can change on the server in the background, including from server-side plugins. That freshness requirement is real and must be preserved by explicit invalidation events before removing broad refreshes.

Known diagnostic results from the investigation:

- Largest local sessions over 300 messages live under `.crystal/sessions`; 17 sessions had more than 300 messages.
- For session `1f9778bb-d219-4139-87de-7809a47f254e` with 538 messages, standalone direct `/sessions/{id}/messages` returned about 4.77 MB in about 0.10-0.16s locally.
- The same full message request over the bridge took about 0.32s alone, chunked into 6 WebSocket chunks.
- A bridge burst matching mobile reload behavior delayed the message response start by about 2.09s, with replies ordered as all schema/settings requests first, then messages.
- Payload analysis for that 538-message session showed significant redundant or frontend-unneeded data:
  - `metadata`: about 2.94 MB
  - `toolResult`: about 834 KB
  - duplicated tool text in both `content` and `toolResult`: about 791 KB
  - repeated `tool_schema`: about 187 KB
  - provider/internal reasoning and phase metadata dominate much of the rest

## Scope Notes

The plain HTTP bridge path for large payloads, gzip/HTTP2, and server-to-bridge HTTP response upload are included as a later-stage subtask. Do the immediate bridge concurrency and payload projection work first, then treat the HTTP bridge path as a broader transport architecture improvement.
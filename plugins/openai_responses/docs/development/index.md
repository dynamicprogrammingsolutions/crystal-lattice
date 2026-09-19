# OpenAI Responses development documentation

This documentation covers implementation and maintenance of the
`openai_responses` plugin package.

## Implementation guides

- [Model discovery](model-discovery.md): API-key and ChatGPT model discovery
  precedence, Codex snapshot, last-resort fallback, and the bare `gpt-5.6`
  alias.
- [Reasoning controls](reasoning-controls.md): `reasoning.effort`,
  `reasoning.mode` (Pro mode), and `reasoning.context` shaping, per-model
  effort sets, silent drops, metadata footers, and Pro mode billing.
- [Cost estimation](cost-estimation.md): pricing snapshot format, token-bucket
  splitting, ChatGPT cached-token estimation, and explicit cache boundaries.
- [Usage journal](usage-journal.md): append-only ChatGPT usage journal record
  format, write path, reset markers, date-based inspection, and CSV export.
- [Usage persistence sanitization](usage-sanitization.md): supported persisted
  usage field paths and the dry-run/apply maintenance command for older
  sessions.
- [Bundle layout](bundle-layout.md): responsibility split across provider and
  extensions, implementation classes, and background compaction notification
  handling.

## Specifications

- [Native conversation compaction](specifications/native-compaction/index.md):
  target behavior, API and ChatGPT protocols, compatibility, and live
  requirements.

## Current implementation

Native compaction is implemented by:

- `openai_responses_native_compaction.py` for API and ChatGPT transports;
- `openai_responses_native_compaction_extension.py` for session-history
  selection, compaction application, and transcript rebuilding;
- `openai_responses_native_compaction_app.py` and
  `openai_responses_native_compaction_process.py` for the background action,
  cancellation, notifications, and reconciled persistence.

Package tests under `tests/` cover transport contracts, session-history
behavior, application-owned background execution, and hosted integration.
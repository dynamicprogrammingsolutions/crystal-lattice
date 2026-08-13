# OpenAI Responses development documentation

This documentation covers implementation and maintenance of the
`openai_responses` plugin package.

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
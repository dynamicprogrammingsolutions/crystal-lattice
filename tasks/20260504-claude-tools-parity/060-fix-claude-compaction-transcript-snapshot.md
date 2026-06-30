# Fix Claude Compaction Transcript Snapshot

Save a pre-compaction transcript snapshot in Claude Code's JSONL format before applying compaction, so the transcript path reference in the summary footer points to a valid file containing the original conversation.

## Requirements checklist

- [x] Investigate Claude Code's transcript JSONL format (entry schema, fields, metadata).
- [x] Implement a transcript snapshot writer that saves the pre-compaction conversation as a JSONL file matching Claude Code's format.
- [x] Wire the snapshot writer into the compaction action so it runs before the session is modified.
- [x] Update `_session_transcript_path` to return the snapshot file path (not the live session file path).
- [x] Update `build_compact_summary_text` to reference the snapshot path in the footer.
- [x] Add unit tests for the snapshot writer (JSONL format, entry schema, metadata fields).
- [x] Add integration-style test verifying the transcript path references a file containing the original conversation.
- [x] Update existing Claude compaction tests to account for the snapshot file.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/040-investigate-and-implement-claude-compaction.md

## Problem

The Claude compaction plugin's `_SUMMARY_FOOTER` tells the model:

```
If you need specific details from before compaction (like exact code snippets,
error messages, or content you generated), read the full transcript at: {transcript_path}
```

But `_session_transcript_path` returns the path to the **live session file** (`{root_dir}/{session_id}.json`). After compaction is applied via `_apply_session_action_result`, that file is overwritten with the compacted conversation — the original pre-compaction messages are gone. So the transcript path reference is broken: the model would try to read the file expecting the original conversation, but only find the compacted summary.

This was identified during the kimi compaction parity work (the kimi compaction had the same bug and was fixed by removing the reference). For Claude compaction, the user chose Option 2: save a pre-compaction transcript snapshot that matches Claude Code's own format.

## Claude Code Transcript Format

Claude Code saves its project transcript as a JSONL file at:
```
~/.claude/projects/<project-path-slug>/<session-id>.jsonl
```

Each line is a JSON object. Observed entry types and fields:

### Message entries (`type: "user"` or `type: "assistant"`)

```json
{
  "parentUuid": "b7cde546-cd46-428d-b0dd-6bda98d5ea30",
  "isSidechain": false,
  "promptId": "10059338-5bed-4c79-a5bf-5196a0bb43ab",
  "type": "user",
  "message": {
    "role": "user",
    "content": "Answer exactly ONE."
  },
  "uuid": "fa3c170b-934f-4b53-9bed-434b060ffee6",
  "timestamp": "2026-05-28T20:44:37.128Z",
  "sessionId": "a047d763-7d7f-4323-9de5-1c1a03118d2f",
  "userType": "external",
  "entrypoint": "...",
  "cwd": "...",
  "version": "2.1.126",
  "gitBranch": "...",
  "slug": "..."
}
```

### Compact summary entries

Same as message entries but with additional fields:
```json
{
  "isCompactSummary": true,
  "isVisibleInTranscriptOnly": true,
  ...
}
```

### Other entry types

- `type: "queue-operation"` — queue enqueue/dequeue events
- `type: "last-prompt"` — last prompt tracking

### Key observations

1. The transcript is **append-only** — Claude Code never overwrites entries, it appends new ones. This is why the original conversation is preserved after compaction.
2. Each entry has a `uuid` and `parentUuid` for threading.
3. The compact summary entry is marked with `isCompactSummary: true` and `isVisibleInTranscriptOnly: true`.
4. The transcript path in the summary footer references this JSONL file.

## Implementation Direction

### Snapshot writer

Create a function `write_pre_compaction_transcript` that:
1. Takes the session and a target directory (e.g., `{session_root}/transcripts/`)
2. Writes a JSONL file at `{target_dir}/{session_id}_pre_compaction_{timestamp}.jsonl`
3. Each line is a JSON object matching Claude Code's entry schema:
   - `type`: "user" or "assistant" (based on message role)
   - `message`: `{role, content}`
   - `uuid`: generated UUID
   - `parentUuid`: previous message's UUID (or null for first)
   - `timestamp`: ISO timestamp
   - `sessionId`: session ID
   - `isSidechain`: false
   - `isCompactSummary`: false (these are original messages)
   - `isVisibleInTranscriptOnly`: false
4. Returns the path to the written file

### Integration point

In `build_compacted_session` (or `execute_action`), before calling `core.slice_session` / `core.add_message`:
1. Call `write_pre_compaction_transcript` to save the original conversation
2. Use the returned path as the `transcript_path` in `build_compact_summary_text`
3. The summary footer then references a valid file containing the original conversation

### Path resolution

Update `_session_transcript_path` to:
1. Determine the transcript snapshot directory (e.g., `{session_root}/transcripts/` or a configurable path)
2. Generate a unique filename: `{session_id}_pre_compaction_{timestamp}.jsonl`
3. Return the full path

The snapshot directory should be derived from the session store's root directory (via `context["app"]._session_store._root_dir`) or a configurable compaction transcript path.

### What stays the same

- `_SUMMARY_HEADER` and `_SUMMARY_FOOTER` format (matches Claude Code)
- `_LOCAL_COMMAND_ARTIFACT` and `_NO_RESPONSE_REQUESTED` injection (matches Claude Code)
- The 3-message injection pattern (summary + local-command + no-response)
- The compaction prompt and `<analysis>/<summary>` output format
- The `claude_compaction` metadata key

## Execution plan

Added during completion after user approval.

Stage 1: Investigation and design
- [x] Confirm the Claude Code JSONL entry schema by examining captured transcripts
- [x] Decide snapshot file naming and directory layout
- [x] Decide whether to store transcripts alongside sessions or in a separate directory
- [x] Present design for approval

Stage 2: Implementation
- [x] Implement `write_pre_compaction_transcript` function
- [x] Add JSONL entry schema matching Claude Code's format
- [x] Wire snapshot writing into `execute_action`
- [x] Update `_session_transcript_path` to return snapshot path
- [x] Update `build_compact_summary_text` to use snapshot path

Stage 3: Tests
- [x] Unit tests for `write_pre_compaction_transcript` (JSONL format, entry schema, UUID threading)
- [x] Unit test verifying snapshot contains original pre-compaction messages
- [x] Integration-style test verifying transcript path references a valid file
- [x] Update existing tests that assert on transcript path

## Investigation Notes

Captured Claude Code transcript files examined:

- `~/.claude/projects/.../a047d763-7d7f-4323-9de5-1c1a03118d2f.jsonl` — success-basic compaction
- `~/.claude/projects/.../757f4aae-9c7a-4612-b885-5d81daa6f417.jsonl` — success-prior-summary compaction

Key fields in compact summary entry:
- `isCompactSummary: true`
- `isVisibleInTranscriptOnly: true`
- `type: "user"`
- `message.content` starts with `_SUMMARY_HEADER`
- `uuid` and `parentUuid` for threading

The transcript is append-only, so the original conversation is preserved alongside the compact summary entry. This is fundamentally different from the ai-agent-platform's session store, which overwrites the session file on compaction.

## Completion Notes

Added during completion after implementation and verification.

- Investigation fixture generation now captures normalized Claude Code project transcript shape:
  - `project_transcript_type_counts`
  - `project_transcript_pre_compaction_message_events`
  - `project_transcript_compact_boundary_event`
  - `project_transcript_compact_summary_event`
  - `project_transcript_local_command_events`
  - `project_transcript_no_response_event`
- Implemented `write_pre_compaction_transcript` in `plugins/claude-tools/src/claude_tools/claude_compaction_feature.py`.
- Snapshot files are written under the app session root:
  - `claude-compaction-transcripts/<session_id>_pre_compaction_<stamp>.jsonl`
- The summary footer now references the snapshot JSONL path instead of the live session JSON file.
- Snapshot writing is intentionally wired in `execute_action`, not `build_compacted_session`, because it is a filesystem side effect requiring application/session-store context.
- Snapshot entries serialize the pre-compaction user/assistant visible conversation in Claude project-transcript style and skip provider-injected system prompt internals.
- Focused verification completed:
  - `python -m py_compile plugins/claude-tools/src/claude_tools/claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature.py application/python/tests/test_claude_compaction_feature_action.py`
  - `pytest plugins/claude-tools/tests/test_claude_compaction_feature.py -q`
  - `pytest application/python/tests/test_claude_compaction_feature_action.py -q`
  - `ruff check plugins/claude-tools/src/claude_tools/claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature.py application/python/tests/test_claude_compaction_feature_action.py application/python/tests/test_claude_default_config_compaction_integration.py`
  - `black --check plugins/claude-tools/src/claude_tools/claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature.py application/python/tests/test_claude_compaction_feature_action.py application/python/tests/test_claude_default_config_compaction_integration.py`
- Hosted default-config verification command was attempted:
  - `pytest -m 'integration and api and openrouter' application/python/tests/test_claude_default_config_compaction_integration.py -q`
  - Result: skipped in this environment because the hosted API gate was not available.
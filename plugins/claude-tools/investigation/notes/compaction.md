# Claude Compaction Investigation

Manual compaction is available as the slash command `/compact`, and it works in `claude -p --output-format stream-json` mode when the session is persisted and resumed with `-c`.

## Observed behavior

- Claude advertises `compact` in the `slash_commands` list of the `system/init` event.
- The exact outgoing compaction request body was captured through `../openai-proxy` in raw artifact:
  - `plugins/claude-tools/investigation/raw/compaction/20260529-110802-success-basic/proxy.log`
- `/compact` with no prior messages returns a synthetic assistant message:
  - `Error: No messages to compact`
- `/compact` after only one normal turn returns:
  - `system/status: compacting`
  - `system/status: compact_result=failed`
  - synthetic assistant text: `Not enough messages to compact.`
- Successful `/compact` returns:
  - `system/status: compacting`
  - `system/status: compact_result=success`
  - `system/compact_boundary` with `compact_metadata`
  - a synthetic user summary message injected into the persisted project transcript
  - a replayed local command stdout message: `<local-command-stdout>Compacted </local-command-stdout>`

## Summary injection shape

On success, Claude inserts a synthetic user message whose content starts with:

```text
This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.
```

Then it writes a dense markdown-like summary, typically with numbered sections such as:

```text
1. Primary Request and Intent:
2. Key Technical Concepts:
3. Files and Code Sections:
4. Errors and fixes:
5. Problem Solving:
6. All user messages:
7. Pending Tasks:
8. Current Work:
9. Optional Next Step:
```

The injected summary message is marked in the project transcript with:

- `isCompactSummary: true`
- `isVisibleInTranscriptOnly: true`

The summary also ends with resume instructions similar to:

```text
If you need specific details from before compaction ..., read the full transcript at: <PROJECT_TRANSCRIPT>
Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.
```

## Tool history handling

In the `success-tool-history` case:

- Claude included the `Read` action in the summary.
- It preserved the absolute file path.
- It inlined the file content that had been read.
- It also kept a transcript attachment entry for the read file after compaction.

This means Claude compaction is not merely abstract; it tries to preserve concrete tool-derived artifacts and file content.

## Prior-summary handling

In the `success-prior-summary` case:

- A second `/compact` succeeded after a prior compaction plus a few more turns.
- The second summary rolled forward the compacted state instead of re-expanding original history.
- The transcript shows the prior compaction as a local command/system operation, including:
  - `<local-command-caveat>`
  - `<command-name>/compact</command-name>`
  - `<local-command-stdout>Compacted </local-command-stdout>`

There was also a synthetic assistant message of `No response requested.` inserted between the first compaction and the next real user prompt in the persisted transcript. That appears to be a local bookkeeping artifact rather than model-facing content to emulate directly.

## Debug-log findings

Claude writes these useful internal breadcrumbs to the debug log during successful compaction:

- `[API REQUEST] /api/v1/messages source=compact`
- `Forked agent [reactive-compact] received message: type=assistant`
- `Forked agent [reactive-compact] finished: 1 messages, types=[assistant], ...`

These strongly suggest compaction is performed by a dedicated internal summarizer path, but the exact prompt body was not recovered from the proxy in this investigation.

Update: the prompt body was later recovered from the proxy.

## Captured outgoing compaction prompt

The successful `/compact` request is a normal outgoing `POST /api/v1/messages?beta=true` request that still includes:

- the standard Claude system prompt
- the standard tool list for the session
- the actual prior conversation messages

The compaction-specific behavior is injected as the **last user message**, not as a special replacement system prompt.

In the captured `success-basic` request:

- `messages[0..3]` contained the actual prior conversation turns
- `messages[4]` contained:
  - `content[0]`: the user's latest raw message text (`Answer exactly THREE.` in the probe)
  - `content[1]`: a long compaction instruction block beginning with:

```text
CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.
```

That long block instructs the model to produce:

- an `<analysis>` block
- a `<summary>` block
- a detailed summary with sections such as:
  - `Primary Request and Intent`
  - `Key Technical Concepts`
  - `Files and Code Sections`
  - `Errors and fixes`
  - `Problem Solving`
  - `All user messages`
  - `Pending Tasks`
  - `Current Work`
  - `Optional Next Step`

It also explicitly says:

- do not use tools
- preserve security-relevant constraints verbatim
- pay special attention to recent work and user feedback
- follow any additional summary instructions present in context

This means Claude compaction is effectively driven by an appended summarization task prompt over the live conversation, not by a hidden compact-only system prompt format like Gemini's XML snapshot pattern.

## Output format conclusions

- Claude compaction is not Gemini-style XML.
- No verification/self-critique second pass was observed.
- There is no assistant acknowledgement equivalent to Gemini's `Got it. Thanks for the additional context!`.
- The durable history shape is fundamentally:
  - synthetic compact summary user message
  - local command caveat / command / stdout records
  - preserved tail message(s)
- The summarizer request still carries the normal system prompt and available tools, but the appended compaction instruction strongly tells the model not to use tools and to answer in plain text only.

## Implementation recommendation

Recommendation: implement Claude compaction separately inside `plugins/claude-tools` as a Claude-specific feature plugin.

Why:

- The captured Claude compaction prompt and history-injection behavior are materially different from Gemini's XML snapshot flow.
- The current task direction is to keep Gemini compaction separate and use it only as a reference for plugin shape, not as a shared abstraction target.
- Investigation fixtures now provide a Claude-specific contract we can implement directly without inventing cross-vendor compaction abstractions.

Practical direction:

- Keep the implementation self-contained in `plugins/claude-tools/src/claude_tools/`.
- Match the captured Claude compaction request and injected-summary behavior directly.
- Defer any shared compaction abstraction until there are at least two implemented vendor-specific compaction paths that clearly want the same seam.
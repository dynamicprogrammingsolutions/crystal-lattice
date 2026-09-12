# Usage persistence sanitization

OpenAI Responses usage metadata persists token and cost information used by
message footers, status totals, ChatGPT cached-token estimation, and later
native-history reconstruction. Persisted usage retains only the supported
OpenAI root fields documented in
[Cost estimation](cost-estimation.md#persisted-usage-boundary). Other root
fields are processed only as part of the current response and are not
persisted.

Older monolithic JSON sessions may still contain unsupported usage root fields
in:

- assistant message metadata;
- nested phase-message metadata;
- retained provider-native metadata;
- stale private raw-usage metadata.

The package provides a maintenance command that removes unsupported usage root
members while retaining supported roots, their nested detail mappings, and all
derived usage metadata. The scan includes canonical live sessions and
immutable snapshots under `<session-root>/.snapshots`.

## Dry run

Dry run is the default:

```bash
plugins/openai_responses/scripts/sanitize_session_usage.py \
  --session-root ~/.crystal/sessions \
  --report-path /tmp/openai-usage-sanitizer-dry-run.json
```

Select individual sessions by repeating `--session-id`:

```bash
plugins/openai_responses/scripts/sanitize_session_usage.py \
  --session-root ~/.crystal/sessions \
  --session-id <session-id> \
  --report-path /tmp/openai-usage-sanitizer-session.json
```

The JSON report contains affected occurrence counts, removed root-key counts
grouped by persisted path, and projected byte savings. It does not include
message content.

## Apply

Stop or otherwise prevent writers from changing the selected session files
before applying the migration. The current application does not participate in
the maintenance command's file coordination, so a file-state recheck cannot
replace a no-writer window.

Apply mode requires a recovery-backup directory outside the live session root:

```bash
plugins/openai_responses/scripts/sanitize_session_usage.py \
  --session-root ~/.crystal/sessions \
  --apply \
  --backup-dir ~/.crystal/session-migration-backups/openai-usage-<run-id> \
  --report-path /tmp/openai-usage-sanitizer-apply.json
```

For every affected canonical live session, the command:

1. validates the original session;
2. creates and validates a temporary sanitized replacement;
3. rechecks the source content before publication;
4. writes a gzip recovery copy;
5. atomically replaces the source;
6. validates the published session.

The command skips top-level conflict-backup filename patterns and snapshot
selection records ending in `.selected.json`. It stores live-session and
snapshot recovery copies in separate `sessions/` and `snapshots/` directories
under the selected backup root and refuses to overwrite an existing recovery
backup.

Run dry mode again after apply. A completed migration reports zero files that
would change.

## Recovery

Each changed session has a corresponding `<session-id>.json.gz` file in the
selected backup directory. To recover, keep the application stopped, decompress
the required file to a temporary path, validate that its embedded session ID
matches the destination filename, and atomically replace the live session file.
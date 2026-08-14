# Claude Tools Investigation

This directory contains AI-assisted, behavior-driven investigation assets for
matching Claude Code's publicly visible standard-tool behavior.

Raw logs are written to `raw/` and ignored by git. Generated,
implementation-relevant fixtures are normalized to remove credentials,
user-home paths, volatile IDs, temporary paths, and other run-specific data
before they are committed under `fixtures/`. Human-readable implementation
directions live under `notes/`.

The normalized fixtures, investigation scripts, and notes are Crystal Lattice
project materials licensed under Apache-2.0. They are not raw Claude Code logs.
See the package [provenance statement](../PROVENANCE.md) for the full
compatibility and non-affiliation boundary.

## Harness Setup

The current harness assumes:

- Claude Code is installed locally and available as `claude`
- Ollama is running on `http://localhost:11434`
- the sibling proxy repo exists at `../openai-proxy`

Known-good proxy startup:

```bash
cd ../openai-proxy
node proxy.js http://localhost:11434/v1 9018
```

Known-good Claude environment shape:

```bash
ANTHROPIC_BASE_URL=http://localhost:9018/api
ANTHROPIC_API_KEY=ollama
ANTHROPIC_AUTH_TOKEN=ollama
ANTHROPIC_SMALL_FAST_MODEL=qwen3-coder-next:cloud
ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3-coder-next:cloud
```

## Important Caveats

- Use `--setting-sources project` plus explicit `--settings` in scripts so user-level `~/.claude/settings.json` does not override the investigation environment.
- Use `--tools <ToolName>` to restrict the tool schemas sent to the model. `--allowedTools` is not sufficient for schema isolation.
- `--output-format stream-json` requires `--verbose` in Claude Code `2.1.126`.
- Pin both `ANTHROPIC_SMALL_FAST_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL`. Claude otherwise emits auxiliary requests using a default Haiku model that Ollama usually does not provide.
- Claude Code may still attempt first-party bootstrap or telemetry calls and log 401s. Those do not necessarily mean the proxied tool investigation failed.
- The normalization scripts intentionally replace volatile ids, temp paths, and other run-specific data so the committed fixtures stay stable.
- Never commit raw logs, authentication material, local settings, or real
  user-home paths. Add normalization coverage before retaining a new kind of
  captured path or identifier.

Run the first investigation script with:

```bash
python plugins/claude-tools/investigation/scripts/investigate_read_tool.py --case success-small-file
```

Run the web investigations with:

```bash
python plugins/claude-tools/investigation/scripts/investigate_web_fetch_tool.py --case all
python plugins/claude-tools/investigation/scripts/investigate_web_search_tool.py --case all
```

Run the system-message investigation with:

```bash
python plugins/claude-tools/investigation/scripts/investigate_system_message.py --case all
```

# Claude Tools Investigation

This directory contains behavior-driven investigation assets for matching Claude Code's standard tools.

Raw logs are written to `raw/` and ignored by git. Normalized, implementation-relevant fixtures are committed under `fixtures/`. Human-readable implementation directions live under `notes/`.

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

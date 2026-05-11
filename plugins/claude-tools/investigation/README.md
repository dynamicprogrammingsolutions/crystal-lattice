# Claude Tools Investigation

This directory contains behavior-driven investigation assets for matching Claude Code's standard tools.

Raw logs are written to `raw/` and ignored by git. Normalized, implementation-relevant fixtures are committed under `fixtures/`. Human-readable implementation directions live under `notes/`.

Run the first investigation script with:

```bash
python plugins/claude-tools/investigation/scripts/investigate_read_tool.py --case success-small-file
```

Run the system-message investigation with:

```bash
python plugins/claude-tools/investigation/scripts/investigate_system_message.py --case all
```

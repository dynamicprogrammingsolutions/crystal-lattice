# codex-tools

Plugin bundle containing local developer tools:

- `ShellTool` (`shell`): run shell commands in a controlled working directory.
- `ApplyPatchTool` (`apply_patch`): apply unified diffs to files.

This repository is intended to be loaded by the AI Agent Platform application layer via a LocalPath spec (development) or via a Git install (distribution).

## Development

- Install (editable): `pip install -e ".[dev]"`
- Run tests: `pytest`

The Python package name is `codex_tools` and uses a `src/` layout.

Plugin metadata lives at `agent_plugin.json` in the repo root.

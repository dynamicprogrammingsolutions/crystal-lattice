# Roadmap development

This directory documents roadmap internals, maintenance, and implemented
specifications. The package entry point remains
[`roadmaps/README.md`](../../README.md).

## Current implementation

The current implementation consists of:

- [`generate.py`](../../generate.py): CSV validation, deterministic display
  IDs, and Markdown generation;
- [`roadmap_config.py`](../../roadmap_config.py): self-contained named roadmap,
  dotenv, and MCP configuration loading;
- [`sync.py`](../../sync.py): dry-run-first Google Sheets synchronization;
- [`config.json`](../../config.json): named roadmap destinations;
- [`tests/`](../../tests/): generator, configuration, and synchronization
  coverage.

The current CSV contract is documented in the package README. It uses `task` as
authored identity, optional external IDs, generated internal IDs, and canonical
internal-ID dependency references.

## Implemented specification

- [Task identity and synchronization](specifications/task-identity-and-synchronization/index.md):
  task identity, optional external IDs, generated internal IDs, canonical
  dependency references, and normalization across CSV, Markdown, and Google
  Sheets.
- [Requirements](specifications/task-identity-and-synchronization/requirements.md):
  live implementation and verification state for the implemented contract.

The specification owns required behavior. The requirements record owns
implementation, verification, documentation, and evidence state.
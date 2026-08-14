"""RepoQA evaluation code.

Two variants share the common scorer in ``common.py``:

- ``benchmark_prompted`` / ``logic_prompted``: single-prompt, no-tools mode
  registered as ``repoqa-prompted``.
- ``benchmark_agentic`` / ``logic_agentic``: workspace-and-tools mode
  registered as ``repoqa``.
"""
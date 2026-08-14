# RepoQA Agentic

Workspace-and-tools RepoQA benchmark mode.

This benchmark keeps the original custom agentic execution style:

- materialize repository workspace
- allow tools
- expect normalized JSON answer

Benchmark-specific configs and profiles should live under this benchmark directory rather than under one shared `evaluations/config/` area.

Preferred local setup:

```bash
pip install -e core/python
pip install -e evaluations
```

Then run through:

```bash
agent-evaluations ...
```
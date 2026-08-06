# Agent Evaluation

`agent_eval` is a programmatic evaluation library for maintainers. Its generic
kernel owns run identity, workspaces, compatible state reuse, artifacts, and
errors. A replaceable `RunEnvironment` owns execution-specific context,
snapshots, and observations.

The package currently includes:

- the generic `AgentEval` kernel;
- arbitrary Python evaluation programs and return values;
- cached runs and clean continuations;
- existing-path and pinned Git workspaces;
- compact canonical and separate raw artifacts;
- a complete `CrystalLatticeEnvironment`;
- production `AgentApplication` request and tool-loop execution;
- custom request drivers, observers, stopping, snapshots, evaluation, and
  presentation.

## Installation

From the repository root:

```bash
python -m pip install -e "maintainer/agent-evaluation[crystal-lattice,dev]"
```

## First evaluation

```python
from pathlib import Path

from agent_eval import AgentEval
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
)


environment = CrystalLatticeEnvironment.from_config(
    Path("/path/to/config.json"),
)

with AgentEval(
    default_environment=environment,
    artifact_root=Path("tmp/agent-evaluation"),
    cache_root=Path("tmp/agent-evaluation/cache"),
) as evaluation:
    def exercise(context: CrystalLatticeContext) -> str:
        context.start("your-agent-id")
        context.add_message("user", "Explain the current package.")
        context.request()
        return context.final_response()

    run = evaluation.run("explain-package", exercise)
    run.raise_for_error()
    print(run.value)
    print(run.artifact_dir)
```

## Documentation

- [Documentation index](docs/index.md)
- [Quickstart](docs/quickstart.md)
- [Environments and customization](docs/environments.md)
- [Continuation and cache](docs/continuation-and-cache.md)
- [Artifacts and evidence](docs/artifacts-and-evidence.md)
- [Development](docs/development/index.md)

Target behavior and live status:

- [Specification](../specifications/agent-evaluation-framework/index.md)
- [Implementation task](../../tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md)

## Verification

Run the deterministic package tests:

```bash
pytest maintainer/agent-evaluation/tests -q
```

Real-agent suites use the `agent_eval` marker and remain excluded from the
package's default pytest configuration.
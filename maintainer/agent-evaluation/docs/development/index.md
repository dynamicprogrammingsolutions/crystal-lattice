# Agent Evaluation Development

## Package boundaries

```text
src/agent_eval/
├── eval.py              generic run lifecycle
├── environment.py       generic RunEnvironment protocol
├── result.py            Run and structured errors
├── services.py          evidence and artifact services
├── workspace.py         workspace preparation and Git helper
├── cache.py             locked atomic local cache
├── artifacts.py         canonical/raw rendering
└── crystal_lattice/
    ├── environment.py   AgentApplication lifecycle
    ├── context.py       evaluation-author context
    ├── requests.py      request driver and normalized outcomes
    └── snapshots.py     JSON session continuation
```

The generic modules must remain importable without importing Crystal Lattice.
The subprocess import test enforces this.

The root `evaluations/` package is a benchmark/CLI/scheduler system and has a
different owner and purpose.

## Lifecycle

For an uncached run, the kernel:

1. Creates the artifact directory.
2. Prepares the workspace.
3. fingerprints the selected environment.
4. Validates parent compatibility.
5. Checks the explicit cache.
6. Opens the environment.
7. Runs arbitrary program code.
8. Requests snapshot and normalized observation.
9. Captures workspace state and artifacts.
10. Publishes a complete cache entry.
11. Returns `Run[T]`.

The Crystal Lattice environment opens an isolated `AgentApplication`, restores
or creates a session, and closes all application resources before its runtime
directory is removed.

## Testing boundaries

The fast package suite covers:

- arbitrary program values and failures;
- alternate environments;
- custom snapshot codecs;
- parent continuation;
- cache locking, corruption, and workspace restoration;
- artifact safety and evidence projection;
- real `AgentApplication` and `AgentCore` construction;
- real dotted plugin loading;
- production request and streaming event paths;
- a production application tool loop;
- custom driver bypass;
- request observers, stopping, and mutation classification;
- Crystal Lattice cache and continuation;
- workspace path rebasing;
- application cleanup.

Run:

```bash
ruff check maintainer/agent-evaluation/src maintainer/agent-evaluation/tests
mypy maintainer/agent-evaluation/src maintainer/agent-evaluation/tests --ignore-missing-imports
pytest maintainer/agent-evaluation/tests -q
```

Real-model tests use the `agent_eval` marker and are excluded by default.
Checkpoint 3 owns the first documentation-standard consumers.

## Extension guidance

- Add optional helpers only after repeated consumers justify them.
- Keep custom drivers and environments ordinary callables/classes.
- Preserve direct access to production application/core/session objects.
- Prefer public Core/Application APIs.
- If realistic integration exposes a product issue, fix the product or report
  the limitation; do not replace the test with a mock-only path.
- Keep canonical output concise and inspect raw evidence only for diagnosis.
- Update the live `AEVAL-*` ledger with implementation, verification, and
  documentation evidence.

## Specifications and task

- Target:
  `maintainer/specifications/agent-evaluation-framework/`
- Execution:
  `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
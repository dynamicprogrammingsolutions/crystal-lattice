# Agent Evaluation Development Guidance

This package owns the maintainer-facing `agent_eval` library. It is distinct
from the repository's benchmark and scheduler package under `evaluations/`.

Start with:

- `README.md` for installation and first use;
- `docs/index.md` for user documentation;
- `docs/development/index.md` for implementation and test boundaries;
- `docs/development/specifications/framework/index.md` for generic target behavior;
- `docs/development/specifications/crystal-lattice-environment/index.md`
  for the bundled environment;
- `../../tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
  for approved execution and current progress.

Keep these boundaries:

- The generic `agent_eval` import must not import `agent_core` or `agent_app`.
- Crystal Lattice integration belongs under
  `src/agent_eval/crystal_lattice/`.
- Programs remain arbitrary Python; do not add required case, suite, reviewer,
  score, prompt, or policy abstractions.
- `RunEnvironment` remains the broad replacement seam.
- Crystal Lattice request drivers, stop conditions, observers, snapshots,
  projections, evaluations, and presentations remain optional.
- Use production `AgentApplication` and `AgentCore` paths in integration tests.
- Do not weaken a realistic integration test to accommodate an implementation
  defect.
- Keep real-model tests explicitly marked and outside default test runs.
- Canonical artifacts should remain compact; complete evidence belongs under
  `raw/`.
- Do not copy credentials or authentication state into artifacts.

Run before handing off package changes:

```bash
ruff check maintainer/agent-evaluation/src maintainer/agent-evaluation/tests
mypy maintainer/agent-evaluation/src maintainer/agent-evaluation/tests --ignore-missing-imports
pytest maintainer/agent-evaluation/tests -q
```
# Maintainer documentation ownership

`maintainer/` is a maintenance audience and publication boundary. It is not a
single document type.

| Content | Owner |
|---|---|
| Cross-cutting instruction concepts, workflows, current status, and interpreted results | `maintainer/docs/` |
| Cross-cutting maintainer architecture and guidance specifications | `maintainer/docs/development/` |
| Generic evaluation kernel and Crystal Lattice environment | `maintainer/agent-evaluation/` |
| Documentation-guidance scenarios, targets, procedures, and frozen records | `maintainer/agent-evaluation/suites/documentation_standard/` |
| Guidance compiler, bundles, candidates, and targets | `maintainer/guidance/` |
| Approval and execution | `tasks/` |
| Historical one-off review material | `archive/` |

Specifications describe intended contracts. Requirements track live state and
link evidence. Dated evaluation reports explain observed results. Scenario
files define test inputs. Frozen JSON preserves machine-readable evidence.
These roles should link to one another without becoming interchangeable.

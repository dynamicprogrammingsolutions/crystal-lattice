# Evaluation result packages

This specification defines optional reusable support for preserving completed
evaluations as compact result packages for human and machine review.

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)

Result packages consume completed evaluation records. They do not change the
[generic evaluation kernel](../framework/index.md) or define sessions,
messages, requests, tools, models, or suite semantics.

Runtime-specific review data belongs to the relevant environment. Crystal
Lattice review projections are specified by the
[Crystal Lattice evaluation environment](../crystal-lattice-environment/index.md).
Each consuming suite owns its scenarios, stages, outputs, assessments, and
human interpretation.

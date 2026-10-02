# Documentation and specification guidance testing strategy

The reusable guidance is verified through several evidence types:

- static checks for project-neutral wording, structure, links, and word budgets;
- deterministic behavior checks for placement, audience, generated-output, and
  task boundaries;
- diverse small-project requirement and testing scenarios;
- model and effort comparisons when wording changes could affect scope;
- semantic and pairwise review as supporting evidence;
- focused human review before acceptance.

A concrete repository may provide the runtime, models, fixtures, and publication
checks. Those tests validate this product but do not become package-neutral
product requirements. Reports must record source and delivery separately and
must not count missing files, evaluator failures, or process exits as valid
semantic evidence.

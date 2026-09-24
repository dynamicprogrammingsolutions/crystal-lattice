# Documentation and specification guidance testing strategy

The reusable guidance is verified through several evidence types:

- static checks for project-neutral wording, structure, links, and word budgets;
- deterministic behavior checks for placement, audience, generated-output, and
  task boundaries;
- diverse small-project requirement and testing scenarios;
- separate destination-terminology scenarios for preventing new labels and
  requesting authority before removing existing wording;
- model and effort comparisons when wording changes could affect scope;
- semantic and pairwise review as supporting evidence;
- focused human review before acceptance.

A concrete repository may provide the runtime, models, fixtures, and publication
checks. Those tests validate this product but do not become package-neutral
product requirements. Reports must record source and delivery separately and
must not count missing files, evaluator failures, or process exits as valid
semantic evidence.

Terminology scenarios use examples and prompts different from the guidance
examples. Mechanical token checks are secondary to complete-file, response,
mutation, provenance, semantic, and human review. A scenario that begins with
existing wording does not share the same acceptance contract as a scenario
that tests whether new wording is introduced.

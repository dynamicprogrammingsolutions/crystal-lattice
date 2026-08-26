# Establish Website Documentation and Content Specification

Create package-local ownership for the website content system, copy-focused
content target, supporting research knowledge, retained evidence, and
disposable output.

## Requirements checklist

- [x] The landing website has concise package and development indexes plus
      website-specific agent guidance.
- [x] Current YAML, Markdown, Astro, section, asset, and rendering behavior is
      documented in one development page without creating an unnecessary
      technical specification.
- [x] A package-owned copywriting-focused product website content
      specification and live requirements file exist.
- [x] Durable research knowledge, retained normalized evidence, current public
      content, and disposable output have distinct documented locations.
- [x] The existing package README and ignore rules route maintainers to the new
      sources without duplicating their content.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

## Scope decisions

- `content-system.md` is current implementation documentation.
- The content specification is
  `docs/development/specifications/product-website-content/`.
- The content specification initially uses `index.md`, `content-spec.md`, and
  `requirements.md`; no technical-spec page is required.
- A future content-system specification is created only if formal YAML,
  rendering, asset, generation, or compatibility behavior becomes complex
  enough to justify one.
- Task files remain in root `tasks/`.
- The package is not added to the generated documentation-site package
  registry in this subtask.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, questions, approved structure, facts, handoff rules,
   common references, output rules, and boundaries.
2. `docs/development/repository/index.md:1-16` — repository documentation and
   specification-policy router; follow its directly relevant pages.
3. `docs/development/standards/documentation.md:1-205` — documentation
   authority, audience, package profiles, ownership, duplication, and
   discoverability.
4. `docs/development/repository/documentation.md:1-255` — Crystal Lattice
   package paths, audience/reference boundaries, source-of-truth, publication,
   and discoverability.
5. `docs/development/standards/specifications.md:1-215` and
   `docs/development/repository/specifications.md:1-180` — proportional
   specification, requirements, task, and current-documentation rules.
6. `landing_page/README.md:1-144` and
   `landing_page/src/content/pageTypes.ts:1-220` — current package entry point
   and content shapes used to bound the initial documentation.

## Known facts and supporting details

- The landing package had no local AGENTS file or docs tree before this
  subtask.
- The existing README already provided build, preview, deployment, and URL
  configuration, so a placeholder quickstart was not justified.
- The current content system can be explained as one implementation page.
- The approved product-content specification is copywriting-focused and does
  not justify a technical-spec page at this stage.
- Research knowledge may be public repository material, but private
  interviews, full source content, credentials, and raw browser/API output
  require minimized or ignored storage.

## Expected outputs

- `landing_page/AGENTS.md`
- `landing_page/docs/index.md`
- `landing_page/docs/development/index.md`
- `landing_page/docs/development/content-system.md`
- `landing_page/docs/development/specifications/product-website-content/index.md`
- `landing_page/docs/development/specifications/product-website-content/content-spec.md`
- `landing_page/docs/development/specifications/product-website-content/requirements.md`
- `landing_page/docs/development/research/index.md`
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
- `landing_page/docs/development/research/research-method.md`
- `landing_page/docs/development/research/evidence-index.md`
- `landing_page/research/README.md`
- Updates to `landing_page/README.md` and `.gitignore`.

## Scope boundaries

- Do not create empty findings, decision, evidence, dataset, review, or
  artifacts directories.
- Do not register `landing_page/` in `docs_site/packages.toml`.
- Do not rewrite current public website copy.
- Do not create a content-system specification or a technical-spec page for
  the product-content specification.

## Execution plan

Status: Approved

Create only pages with substantive current or target content. Route the
package through a local AGENTS file and short indexes. Document current
implementation separately from the product communication target. Preserve
research hypotheses as supporting knowledge and define a minimized retained
evidence area plus an ignored disposable-output area.

Update the package README and root ignore rules, then validate links, task
references, authored Markdown structure, and the landing build.

### Implementation decisions and open questions

- Decision: use the exact ownership and file set approved by the user.
- Decision: do not create empty findings, decision, dataset, or evidence
  directories.
- Decision: defer docs-site registry publication.
- No material open question remains for this subtask.

### Documentation

- Create the approved package-local documentation and specification files.
- Current implementation claims must be verified against the repository.
- Research pages label facts, observations, hypotheses, recommendations,
  decisions, and questions where the distinction matters.

### Task checklist

- [x] Add `landing_page/AGENTS.md`.
- [x] Add package and development indexes.
- [x] Document the current content system.
- [x] Add the product website content specification and requirements.
- [x] Add the research index, baseline, method, and evidence index.
- [x] Add the retained research evidence README.
- [x] Update the package README.
- [x] Ignore `landing_page/artifacts/`.
- [x] Validate the authored files and references.

### Requirement verification

- Package routing: inspect README, AGENTS, and both indexes.
- Current implementation: compare `content-system.md` with the current loader,
  preparation, registry, page, component, content, and build paths.
- Specification: inspect scope boundaries and verify no unnecessary
  technical-spec page exists.
- Research/evidence boundaries: inspect research docs, evidence README, and
  `.gitignore`.
- Validation: task-reference, Markdown/link, diff, and landing build checks
  pass.

## Implementation Notes

- Created the approved package-local documentation, content specification,
  research knowledge, evidence boundary, and ignored disposable-output
  structure.
- Kept current rendering documentation and copywriting-focused target behavior
  separate.
- Did not register the landing package in `docs_site/packages.toml`.

## Completion Notes

- Outcome: the website package now has a durable, discoverable ownership model
  for current content mechanics, target product communication, supporting
  research, retained normalized evidence, and disposable output.
- The content specification is proportional: `index.md`, `content-spec.md`,
  and `requirements.md`; no technical-spec page or empty decision directory
  was created.
- Verification:
  - `yarn build` in `landing_page/`: passed; five static routes built.
  - Task-reference validation: all referenced task files exist and all 18
    subtasks are listed by the main task.
  - Package Markdown link validation: passed.
  - Task title, requirements, execution-plan, parent-link, and ignore-boundary
    checks: passed.
  - `git diff --check`: passed.
  - No absolute developer-home paths remain in the new package documentation,
    research, or task files.
- No later research or website-rewrite subtask was executed.

## Post-completion follow-up

- On August 25, 2026, the task handoff was strengthened with bounded ordered
  references, known facts, exact outputs, and scope boundaries before the
  replaceable execution plan. The completed documentation-foundation outcome
  and requirement evidence were not reopened.

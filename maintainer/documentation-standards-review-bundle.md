# Documentation guidance review bundle

Use the focused bundle for ordinary human review. Join maintained Markdown
sources directly; do not substitute prepared or generated copies.

## Focused human review

Include, in order:

1. a short cover explaining what changed and which objective checks passed
2. the exact `AGENTS.md` documentation section
3. `docs/development/index.md`
4. `docs/development/documentation.md`
5. `docs/development/crystal-lattice-documentation.md`

Do not append compatibility pages, requirements tables, task history, complete
behavior-test definitions, model transcripts, generated-site output, or
maintainer specifications unless the reviewer asks for them.

The agent completes link, structure, duplication, terminology, and
guidance-behavior checks before sending the bundle. Human review concentrates
on clarity, coherence, length, scannability, examples, and whether the guidance
would be pleasant to use.

## Complete maintenance review

When source-level design or evaluation detail is explicitly needed, append:

Include each specification in index, product, technical, requirements order:

1. `maintainer/specifications/documentation-and-specification-standard/`
2. `maintainer/specifications/agent-evaluation-framework/`

Then append the relevant files from
`maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/`
and the corresponding evaluation results. Do not include the entire directory
when a smaller requirement- or scenario-focused selection answers the review
question.

Keep this page synchronized when a public guidance page, governing
specification, seed, or consumer scenario is added, removed, or renamed.